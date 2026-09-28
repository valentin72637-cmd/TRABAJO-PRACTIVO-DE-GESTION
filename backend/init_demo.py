"""Carga demo explícita con claves elegidas localmente; nunca se ejecuta al iniciar la API."""
from datetime import timedelta
from getpass import getpass
from backend.auth_utils import get_password_hash, is_published_demo_password
from backend.database import Base, engine, SessionLocal
from backend.models import Usuario, Poliza
from backend.policy_rules import business_today, calcular_estado


def init_demo(admin_password, cliente_password):
    for password in (admin_password, cliente_password):
        if not 8 <= len(password) <= 128 or is_published_demo_password(password):
            raise ValueError("Usa claves nuevas de 8 a 128 caracteres; las claves publicadas no se permiten.")
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for email, nombre, role, password in [
            ("admin@demo.com", "Administrador Demo", "admin", admin_password),
            ("cliente@demo.com", "Cliente Demo", "cliente", cliente_password),
        ]:
            user = db.query(Usuario).filter(Usuario.email == email).first()
            if user is None:
                db.add(Usuario(email=email, nombre=nombre, role=role,
                               password=get_password_hash(password)))
        db.flush()
        cliente = db.query(Usuario).filter(Usuario.email == "cliente@demo.com").one()
        if cliente.role != "cliente":
            raise ValueError("El email del cliente demo pertenece a un administrador.")
        hoy = business_today()
        for numero, tipo in [("POL-1001", "Auto"), ("POL-2001", "Hogar")]:
            if not db.query(Poliza).filter(Poliza.numero == numero).first():
                vence = hoy + timedelta(days=365)
                db.add(Poliza(numero=numero, tipo=tipo, inicio=hoy, vencimiento=vence,
                              estado=calcular_estado(vence), mensaje=f"Poliza {tipo} activa",
                              cliente_id=cliente.id))
        db.commit()
    print("Datos demo creados. Las cuentas y polizas existentes se conservaron.")


if __name__ == "__main__":
    init_demo(getpass("Nueva clave admin demo: "), getpass("Nueva clave cliente demo: "))
