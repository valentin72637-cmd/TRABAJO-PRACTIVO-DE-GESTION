# backend/routers/polizas.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Poliza, Usuario
from backend.schemas import PolizaCreate, PolizaOut, PolizaUpdate
from backend.auth_utils import get_current_user, require_admin
from backend.policy_rules import calcular_estado


router = APIRouter(
    prefix="/polizas",
    tags=["Pólizas"]
)


# ============================================================
# VALORES PERMITIDOS
# ============================================================

TIPOS_VALIDOS = {
    "Auto",
    "Hogar",
    "Vida",
    "Salud"
}

ESTADOS_VALIDOS = {
    "Vigente",
    "Por vencer",
    "Vencida"
}


# ============================================================
# VALIDAR CLIENTE
# ============================================================

def validar_cliente(
    db: Session,
    cliente_id: int
) -> Usuario:

    cliente = (
        db.query(Usuario)
        .filter(Usuario.id == cliente_id)
        .first()
    )

    # Cliente inexistente
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El cliente con ID {cliente_id} "
                "no existe"
            )
        )

    # Un administrador no puede recibir pólizas
    if cliente.role != "cliente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "La póliza solo puede asignarse "
                "a un usuario con rol cliente"
            )
        )

    return cliente


# ============================================================
# VALIDAR NÚMERO DE PÓLIZA ÚNICO
# ============================================================

def validar_numero_unico(
    db: Session,
    numero: str,
    poliza_id: int | None = None
):

    consulta = (
        db.query(Poliza)
        .filter(Poliza.numero == numero)
    )

    # Cuando estamos editando,
    # excluimos la póliza actual.
    if poliza_id is not None:
        consulta = consulta.filter(
            Poliza.id != poliza_id
        )

    existente = consulta.first()

    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Ya existe una póliza con "
                f"el número {numero}"
            )
        )


# ============================================================
# VALIDAR TIPO, ESTADO Y FECHAS
# ============================================================

def validar_datos_poliza(
    tipo: str,
    estado: str,
    inicio,
    vencimiento
):

    # --------------------------------------------------------
    # TIPO
    # --------------------------------------------------------

    if tipo not in TIPOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Tipo de póliza inválido. "
                "Debe ser Auto, Hogar, Vida o Salud"
            )
        )


    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    if estado not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Estado inválido. "
                "Debe ser Vigente, Por vencer o Vencida"
            )
        )


    # --------------------------------------------------------
    # FECHAS
    # --------------------------------------------------------

    if vencimiento < inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "La fecha de vencimiento no puede "
                "ser anterior a la fecha de inicio"
            )
        )


# ============================================================
# LISTAR TODAS LAS PÓLIZAS
# Solo administrador
# ============================================================

@router.get(
    "/",
    response_model=List[PolizaOut]
)
def list_polizas(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin)
):

    return (
        db.query(Poliza)
        .order_by(Poliza.id.asc())
        .all()
    )


# ============================================================
# CREAR PÓLIZA
# Solo administrador
# ============================================================

@router.post(
    "/",
    response_model=PolizaOut,
    status_code=status.HTTP_201_CREATED
)
def create_poliza(
    data: PolizaCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin)
):

    # --------------------------------------------------------
    # 1. CONVERTIR PYDANTIC → DICCIONARIO
    # --------------------------------------------------------

    datos = data.model_dump()


    # --------------------------------------------------------
    # 2. VALIDAR NÚMERO
    # --------------------------------------------------------

    validar_numero_unico(
        db,
        datos["numero"]
    )


    # --------------------------------------------------------
    # 3. VALIDAR CLIENTE
    # --------------------------------------------------------

    validar_cliente(
        db,
        datos["cliente_id"]
    )


    # --------------------------------------------------------
    # 4. VALIDAR DATOS
    # --------------------------------------------------------

    validar_datos_poliza(
        tipo=datos["tipo"],
        estado=datos["estado"],
        inicio=datos["inicio"],
        vencimiento=datos["vencimiento"]
    )


    # --------------------------------------------------------
    # 5. CREAR
    # --------------------------------------------------------

    datos["estado"] = calcular_estado(datos["vencimiento"])
    poliza = Poliza(
        **datos
    )

    db.add(poliza)
    db.commit()
    db.refresh(poliza)

    return poliza


# ============================================================
# ACTUALIZAR PÓLIZA
# Solo administrador
# ============================================================

@router.put(
    "/{poliza_id}",
    response_model=PolizaOut
)
def update_poliza(
    poliza_id: int,
    data: PolizaUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin)
):

    # --------------------------------------------------------
    # 1. BUSCAR PÓLIZA
    # --------------------------------------------------------

    poliza = (
        db.query(Poliza)
        .filter(Poliza.id == poliza_id)
        .first()
    )

    if poliza is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Póliza no encontrada"
        )


    # --------------------------------------------------------
    # 2. CAMPOS QUE SE QUIEREN MODIFICAR
    # --------------------------------------------------------

    cambios = data.model_dump(
        exclude_unset=True
    )


    # --------------------------------------------------------
    # 3. CALCULAR VALORES FINALES
    # --------------------------------------------------------

    numero_final = cambios.get(
        "numero",
        poliza.numero
    )

    tipo_final = cambios.get(
        "tipo",
        poliza.tipo
    )

    inicio_final = cambios.get(
        "inicio",
        poliza.inicio
    )

    vencimiento_final = cambios.get(
        "vencimiento",
        poliza.vencimiento
    )

    estado_final = cambios.get(
        "estado",
        poliza.estado
    )

    cliente_id_final = cambios.get(
        "cliente_id",
        poliza.cliente_id
    )


    # --------------------------------------------------------
    # 4. EVITAR VALORES NULOS OBLIGATORIOS
    # --------------------------------------------------------

    if numero_final is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de póliza es obligatorio"
        )

    if tipo_final is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tipo de póliza es obligatorio"
        )

    if inicio_final is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de inicio es obligatoria"
        )

    if vencimiento_final is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de vencimiento es obligatoria"
        )

    if estado_final is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estado es obligatorio"
        )

    if cliente_id_final is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cliente es obligatorio"
        )


    # --------------------------------------------------------
    # 5. VALIDAR NÚMERO
    # --------------------------------------------------------

    validar_numero_unico(
        db,
        numero_final,
        poliza_id=poliza.id
    )


    # --------------------------------------------------------
    # 6. VALIDAR CLIENTE
    # --------------------------------------------------------

    validar_cliente(
        db,
        cliente_id_final
    )


    # --------------------------------------------------------
    # 7. VALIDAR TIPO / ESTADO / FECHAS
    # --------------------------------------------------------

    validar_datos_poliza(
        tipo=tipo_final,
        estado=estado_final,
        inicio=inicio_final,
        vencimiento=vencimiento_final
    )


    # --------------------------------------------------------
    # 8. APLICAR CAMBIOS
    # --------------------------------------------------------

    cambios["estado"] = calcular_estado(vencimiento_final)
    for campo, valor in cambios.items():
        setattr(
            poliza,
            campo,
            valor
        )


    # --------------------------------------------------------
    # 9. GUARDAR
    # --------------------------------------------------------

    db.commit()
    db.refresh(poliza)

    return poliza


# ============================================================
# ELIMINAR PÓLIZA
# Solo administrador
# ============================================================

@router.delete(
    "/{poliza_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_poliza(
    poliza_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin)
):

    poliza = (
        db.query(Poliza)
        .filter(Poliza.id == poliza_id)
        .first()
    )

    if poliza is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Póliza no encontrada"
        )

    db.delete(poliza)
    db.commit()

    return None


# ============================================================
# VER MIS PÓLIZAS
# Solo cliente autenticado
# ============================================================

@router.get(
    "/mias",
    response_model=List[PolizaOut]
)
def mis_polizas(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # PROTEGER ENDPOINT
    # --------------------------------------------------------

    if current_user.role != "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Solo los clientes pueden consultar "
                "sus pólizas"
            )
        )


    return (
        db.query(Poliza)
        .filter(
            Poliza.cliente_id ==
            current_user.id
        )
        .order_by(Poliza.id.asc())
        .all()
    )
