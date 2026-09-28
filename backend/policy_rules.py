"""Regla vigente: vencida antes de hoy; próxima entre hoy y +30 inclusive."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import case

# SegurAR opera con fecha civil argentina (UTC-03:00), no con la fecha UTC.
ARGENTINA = timezone(timedelta(hours=-3))


def business_today():
    return datetime.now(ARGENTINA).date()


def calcular_estado(vencimiento, hoy=None):
    hoy = hoy if hoy is not None else business_today()
    if vencimiento < hoy:
        return "Vencida"
    return "Por vencer" if vencimiento <= hoy + timedelta(days=30) else "Vigente"


def estado_sql(hoy):
    from backend.models import Poliza
    return case((Poliza.vencimiento < hoy, "Vencida"),
                (Poliza.vencimiento <= hoy + timedelta(days=30), "Por vencer"),
                else_="Vigente")
