"""Informes de pólizas protegidos por JWT."""
import io
from datetime import date, timedelta
from math import ceil
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from backend.auth_utils import get_current_user
from backend.database import get_db
from backend.models import Poliza, Usuario
from backend.reportes_pdf import crear_pdf_polizas
from backend.policy_rules import business_today, calcular_estado, estado_sql

router = APIRouter(prefix="/informes", tags=["Informes"])
DIAS_PROXIMO_VENCIMIENTO = 30
TIPOS = ("Auto", "Hogar", "Vida", "Salud")
ESTADOS = ("Vigente", "Por vencer", "Vencida")

def consulta(db, user, cliente_id, estado, tipo, desde, hasta):
    if desde and hasta and desde > hasta:
        raise HTTPException(400, "La fecha desde no puede ser posterior a la fecha hasta")
    if user.role == "cliente":
        if cliente_id is not None and cliente_id != user.id:
            raise HTTPException(403, "No puedes consultar pólizas de otro cliente")
        cliente_id = user.id
    elif user.role != "admin":
        raise HTTPException(403, "No tienes permisos para consultar informes")
    hoy = business_today()
    estado_expr = estado_sql(hoy)
    q = db.query(Poliza, Usuario.nombre.label("cliente_nombre"), Usuario.email.label("cliente_email")).join(Usuario, Usuario.id == Poliza.cliente_id)
    if cliente_id is not None: q = q.filter(Poliza.cliente_id == cliente_id)
    if estado is not None: q = q.filter(estado_expr == estado)
    if tipo is not None: q = q.filter(Poliza.tipo == tipo)
    if desde is not None: q = q.filter(Poliza.vencimiento >= desde)
    if hasta is not None: q = q.filter(Poliza.vencimiento <= hasta)
    return q, hoy, estado_expr, cliente_id

def args(cliente_id: Optional[int] = Query(None, gt=0), estado: Optional[Literal["Vigente", "Por vencer", "Vencida"]] = None, tipo: Optional[Literal["Auto", "Hogar", "Vida", "Salud"]] = None, vencimiento_desde: Optional[date] = None, vencimiento_hasta: Optional[date] = None):
    return cliente_id, estado, tipo, vencimiento_desde, vencimiento_hasta

@router.get("/polizas/resumen")
def resumen(cliente_id: Optional[int] = Query(None, gt=0), estado: Optional[Literal["Vigente", "Por vencer", "Vencida"]] = None, tipo: Optional[Literal["Auto", "Hogar", "Vida", "Salud"]] = None, vencimiento_desde: Optional[date] = None, vencimiento_hasta: Optional[date] = None, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    q, hoy, estado_expr, cliente_final = consulta(db, current_user, cliente_id, estado, tipo, vencimiento_desde, vencimiento_hasta)
    base = q.with_entities(Poliza.id, Poliza.tipo, Poliza.vencimiento, estado_expr.label("estado")).subquery()
    por_estado = dict(db.query(base.c.estado, func.count()).group_by(base.c.estado).all())
    por_tipo = dict(db.query(base.c.tipo, func.count()).group_by(base.c.tipo).all())
    tr = case((base.c.vencimiento < hoy, "Vencida"), (base.c.vencimiento <= hoy + timedelta(days=7), "0–7 días"), (base.c.vencimiento <= hoy + timedelta(days=30), "8–30 días"), (base.c.vencimiento <= hoy + timedelta(days=60), "31–60 días"), else_="Más de 60 días")
    por_tramo = dict(db.query(tr, func.count()).group_by(tr).all())
    proximas = por_estado.get("Por vencer", 0)
    return {"filtros_aplicados":{"cliente_id":cliente_final,"estado":estado,"tipo":tipo,"vencimiento_desde":vencimiento_desde,"vencimiento_hasta":vencimiento_hasta},"fecha_referencia":hoy,"dias_proximo_vencimiento":30,"indicadores":{"total_polizas":sum(por_estado.values()),"vigentes":por_estado.get("Vigente",0),"proximas_a_vencer":proximas,"vencidas":por_estado.get("Vencida",0)},"por_estado":[{"categoria":x,"cantidad":por_estado.get(x,0)} for x in ESTADOS],"por_tipo":[{"categoria":x,"cantidad":por_tipo.get(x,0)} for x in TIPOS],"vencimientos_por_tramo":[{"tramo":x,"cantidad":por_tramo.get(x,0)} for x in ("Vencida","0–7 días","8–30 días","31–60 días","Más de 60 días")],"resumen_textual":f"{proximas} póliza(s) vencen dentro de los próximos 30 días."}

@router.get("/polizas/listado")
def listado(cliente_id: Optional[int] = Query(None, gt=0), estado: Optional[Literal["Vigente", "Por vencer", "Vencida"]] = None, tipo: Optional[Literal["Auto", "Hogar", "Vida", "Salud"]] = None, vencimiento_desde: Optional[date] = None, vencimiento_hasta: Optional[date] = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    q, hoy, _, _ = consulta(db, current_user, cliente_id, estado, tipo, vencimiento_desde, vencimiento_hasta)
    total=q.count(); rows=q.order_by(Poliza.vencimiento.asc(), Poliza.id.asc()).offset((page-1)*page_size).limit(page_size).all(); items=[]
    for p,nombre,_ in rows:
        efectivo = calcular_estado(p.vencimiento, hoy)
        items.append({"id":p.id,"numero":p.numero,"tipo":p.tipo,"inicio":p.inicio,"vencimiento":p.vencimiento,"estado":efectivo,"mensaje":p.mensaje,"cliente_id":p.cliente_id,"cliente_nombre":nombre if current_user.role=="admin" else None})
    return {"items":items,"pagination":{"page":page,"page_size":page_size,"total_items":total,"total_pages":ceil(total/page_size) if total else 0}}

@router.get("/polizas/exportar.pdf")
def exportar_pdf(
    cliente_id: Optional[int] = Query(None, gt=0),
    estado: Optional[Literal["Vigente", "Por vencer", "Vencida"]] = None,
    tipo: Optional[Literal["Auto", "Hogar", "Vida", "Salud"]] = None,
    vencimiento_desde: Optional[date] = None,
    vencimiento_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    q, hoy, _, cliente_final = consulta(
        db, current_user, cliente_id, estado, tipo,
        vencimiento_desde, vencimiento_hasta,
    )
    filas = q.order_by(Poliza.vencimiento.asc(), Poliza.id.asc()).all()
    contenido = crear_pdf_polizas(
        filas,
        hoy,
        current_user,
        {
            "cliente_id": cliente_final,
            "estado": estado,
            "tipo": tipo,
            "desde": vencimiento_desde,
            "hasta": vencimiento_hasta,
        },
        calcular_estado,
    )
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="informe_polizas_segurar.pdf"'
        },
    )
