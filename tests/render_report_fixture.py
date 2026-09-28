"""Genera un PDF ficticio para inspección visual; nunca conecta a SQLite."""
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from backend.reportes_pdf import crear_pdf_polizas
from backend.policy_rules import calcular_estado

if __name__ == "__main__":
    today = date(2026, 9, 27)
    rows = []
    for i, (kind, days) in enumerate([("Auto", -1), ("Vida", 0), ("Auto", 30), ("Vida", 61)]):
        policy = SimpleNamespace(
            numero="POL-PRUEBA-" + str(i), tipo=kind,
            inicio=today-timedelta(days=90), vencimiento=today+timedelta(days=days),
            mensaje=("Mensaje extenso de prueba. " * 20)[:500] if i == 0 else "Texto de prueba <sin HTML activo>.",
        )
        rows.append((policy, "Cliente de prueba con nombre extenso",
                     "correo.extenso.de.prueba@example.com"))
    output = Path(__file__).resolve().parents[1] / "tmp" / "pdfs" / "qa-correcciones.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(crear_pdf_polizas(
        rows, today, SimpleNamespace(nombre="Administrador de prueba", role="admin"),
        {"cliente_id":None,"estado":None,"tipo":None,"desde":None,"hasta":None},
        calcular_estado))
    print(str(output))
