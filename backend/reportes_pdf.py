"""Generación del informe PDF de pólizas."""
import html
import io
from collections import Counter
from datetime import datetime
from backend.policy_rules import ARGENTINA
from math import ceil
from pathlib import Path
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

LOGO_PATH = Path(__file__).resolve().parent.parent / "login" / "app" / "assets" / "logo.png"


def grafico_barras(titulo, categorias, valores, color):
    dibujo = Drawing(500, 165)
    dibujo.add(String(250, 153, titulo, textAnchor="middle", fontName="Helvetica-Bold", fontSize=10, fillColor=colors.HexColor("#212529")))
    grafico = VerticalBarChart()
    grafico.x, grafico.y, grafico.width, grafico.height = 45, 36, 425, 100
    grafico.data = [valores]
    grafico.categoryAxis.categoryNames = categorias
    grafico.categoryAxis.labels.fontName = "Helvetica"
    grafico.categoryAxis.labels.fontSize = 7
    grafico.categoryAxis.labels.dy = -8
    grafico.valueAxis.valueMin = 0
    maximo = max(valores) if valores else 0
    grafico.valueAxis.valueMax = max(1, maximo + 1)
    grafico.valueAxis.valueStep = max(1, ceil(max(1, maximo) / 4))
    grafico.valueAxis.labels.fontSize = 7
    grafico.bars[0].fillColor = colors.HexColor(color)
    grafico.bars[0].strokeColor = colors.HexColor(color)
    grafico.barLabelFormat = "%d"
    grafico.barLabels.fontName = "Helvetica-Bold"
    grafico.barLabels.fontSize = 8
    grafico.barLabels.fillColor = colors.HexColor("#212529")
    grafico.barLabels.nudge = 7
    dibujo.add(grafico)
    return dibujo


def resumen_categorias(categorias, cantidades):
    maximo = max((cantidades[x] for x in categorias), default=0)
    if maximo == 0:
        return "No hay pólizas para comparar con estos filtros."
    mayores = [x for x in categorias if cantidades[x] == maximo]
    if len(mayores) > 1:
        return f"Empatan {', '.join(mayores)}, con {maximo} póliza(s) cada categoría."
    return f"{mayores[0]} tiene la mayor cantidad: {maximo} póliza(s)."


def crear_pdf_polizas(filas, hoy, usuario, filtros, calcular_estado):
    salida = io.BytesIO()
    pagina = A4
    documento = SimpleDocTemplate(salida, pagesize=pagina, rightMargin=14*mm, leftMargin=14*mm, topMargin=12*mm, bottomMargin=15*mm, title="Informe de pólizas - SegurAR", author="SegurAR")
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("Titulo", parent=estilos["Title"], textColor=colors.HexColor("#0056B3"), fontSize=19, leading=22, alignment=TA_CENTER)
    seccion = ParagraphStyle("Seccion", parent=estilos["Heading2"], textColor=colors.HexColor("#0056B3"), fontSize=13, leading=16, spaceBefore=7, spaceAfter=5)
    celda = ParagraphStyle("Celda", parent=estilos["BodyText"], fontSize=7.2, leading=8.6)
    pequeno = ParagraphStyle("Pequeno", parent=estilos["BodyText"], fontSize=8.5, leading=11, textColor=colors.HexColor("#495057"))
    resumen = ParagraphStyle("Resumen", parent=pequeno, alignment=TA_CENTER, fontSize=8)
    cabecera_texto = [Paragraph("SegurAR - Informe de pólizas", titulo), Paragraph(f"Generado el {datetime.now(ARGENTINA).strftime('%d/%m/%Y %H:%M')} (Argentina)<br/>Usuario: {html.escape(usuario.nombre)} ({html.escape(usuario.role)})", pequeno)]
    if usuario.role == "cliente":
        cabecera_texto.append(Paragraph(f"Cliente: {html.escape(usuario.nombre)} | Email: {html.escape(usuario.email)}", pequeno))
    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH), width=30*mm, height=22*mm, kind="proportional")
        cabecera = Table([[logo, cabecera_texto]], colWidths=[34*mm, 148*mm])
        cabecera.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"), ("ALIGN",(0,0),(0,0),"CENTER")]))
        elementos = [cabecera, Spacer(1, 3*mm)]
    else:
        elementos = cabecera_texto + [Spacer(1, 3*mm)]
    detalle = [f"Estado: {filtros['estado'] or 'Todos'}", f"Tipo: {filtros['tipo'] or 'Todos'}", f"Vence desde: {filtros['desde'] or 'Sin límite'}", f"Vence hasta: {filtros['hasta'] or 'Sin límite'}"]
    if usuario.role == "admin": detalle.insert(0, f"Cliente ID: {filtros['cliente_id'] or 'Todos'}")
    elementos.extend([Paragraph(" | ".join(detalle), pequeno), Paragraph(f"Total exportado: {len(filas)} póliza(s)", pequeno), Spacer(1, 4*mm), Paragraph("Listado de pólizas", seccion)])
    encabezados = ["N°", "Tipo", "Inicio", "Vencimiento", "Estado", "Mensaje"]
    if usuario.role == "admin": encabezados.insert(1, "Cliente / email")
    datos = [encabezados]
    estados, tipos, tramos = Counter(), Counter(), Counter()
    for poliza, cliente_nombre, cliente_email in filas:
        estado = calcular_estado(poliza.vencimiento, hoy)
        estados[estado] += 1
        tipos[poliza.tipo] += 1
        dias = (poliza.vencimiento - hoy).days
        if dias < 0: tramos["Vencidas"] += 1
        elif dias <= 7: tramos["0-7"] += 1
        elif dias <= 30: tramos["8-30"] += 1
        elif dias <= 60: tramos["31-60"] += 1
        else: tramos["60+"] += 1
        fila = [Paragraph(html.escape(poliza.numero), celda), Paragraph(html.escape(poliza.tipo), celda), Paragraph(poliza.inicio.strftime("%d/%m/%Y"), celda), Paragraph(poliza.vencimiento.strftime("%d/%m/%Y"), celda), Paragraph(html.escape(estado), celda), Paragraph(html.escape(poliza.mensaje or "-"), celda)]
        if usuario.role == "admin":
            fila.insert(1, Paragraph(f"{html.escape(cliente_nombre)}<br/><font color='#6C757D'>{html.escape(cliente_email)}</font>", celda))
        datos.append(fila)
    if len(datos) == 1: datos.append(["No hay resultados"] + [""]*(len(encabezados)-1))
    anchos = [18*mm,30*mm,18*mm,23*mm,25*mm,25*mm,43*mm] if usuario.role == "admin" else [24*mm,24*mm,25*mm,27*mm,28*mm,54*mm]
    tabla = Table(datos, colWidths=anchos, repeatRows=1, hAlign="CENTER")
    tabla.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0D6EFD")), ("TEXTCOLOR",(0,0),(-1,0),colors.white), ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,0),8), ("ALIGN",(0,0),(-1,0),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"), ("GRID",(0,0),(-1,-1),.35,colors.HexColor("#CED4DA")), ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F3F6FA")]),
        ("LEFTPADDING",(0,0),(-1,-1),4), ("RIGHTPADDING",(0,0),(-1,-1),4), ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    elementos.extend([tabla, Spacer(1, 7*mm), Paragraph("Resumen gráfico", seccion)])
    categorias_estado = ["Vigente", "Por vencer", "Vencida"]
    categorias_tipo = ["Auto", "Hogar", "Vida", "Salud"]
    categorias_tramo = ["Vencidas", "0-7", "8-30", "31-60", "60+"]
    dibujos = [
        grafico_barras("Pólizas por estado", categorias_estado, [estados[x] for x in categorias_estado], "#0D6EFD"),
        grafico_barras("Pólizas por tipo", categorias_tipo, [tipos[x] for x in categorias_tipo], "#198754"),
        grafico_barras("Cercanía del vencimiento", categorias_tramo, [tramos[x] for x in categorias_tramo], "#FD7E14"),
    ]
    textos = [
        Paragraph(resumen_categorias(categorias_estado, estados), resumen),
        Paragraph(resumen_categorias(categorias_tipo, tipos), resumen),
        Paragraph(f"{estados['Por vencer']} póliza(s) vencen dentro de los próximos 30 días.", resumen),
    ]
    for dibujo, texto_resumen in zip(dibujos, textos):
        bloque = Table([[dibujo], [texto_resumen]], colWidths=[180*mm], hAlign="CENTER")
        bloque.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("BOTTOMPADDING",(0,1),(-1,1),8),
        ]))
        elementos.append(KeepTogether([bloque, Spacer(1, 4*mm)]))
    def pie(canvas, doc):
        canvas.saveState(); canvas.setFont("Helvetica",8); canvas.setFillColor(colors.HexColor("#6C757D")); canvas.drawString(14*mm,8*mm,"SegurAR - Informe confidencial"); canvas.drawRightString(pagina[0]-14*mm,8*mm,f"Página {doc.page}"); canvas.restoreState()
    documento.build(elementos, onFirstPage=pie, onLaterPages=pie)
    return salida.getvalue()
