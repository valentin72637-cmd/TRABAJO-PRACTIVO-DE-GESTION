"""Recuperación local con entrada oculta y respaldo previo a cualquier cambio."""
import argparse
import sqlite3
import warnings
from contextlib import closing
from datetime import datetime
from getpass import GetPassWarning, getpass
from pathlib import Path
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError

from backend.auth_utils import get_password_hash, is_published_demo_password, revoke_sessions
from backend.database import Base, DB_PATH, engine, SessionLocal
from backend.models import Usuario


def password_problem(password):
    if len(password) < 8:
        return "La clave tiene menos de 8 caracteres. No se guardo ningun cambio."
    if len(password) > 128:
        return "La clave supera 128 caracteres. No se guardo ningun cambio."
    if is_published_demo_password(password):
        return "Esa clave demo fue publicada y esta bloqueada. Elegi una clave diferente."
    return None


def ask_new_password():
    print("La escritura es oculta: no apareceran letras ni asteriscos.")
    print("Usa una clave personal de 8 a 128 caracteres, distinta de las antiguas claves demo.")
    while True:
        # Nunca permitir la alternativa de getpass que imprime la clave por falta de TTY.
        with warnings.catch_warnings():
            warnings.simplefilter("error", GetPassWarning)
            password = getpass("Nueva clave: ")
            problem = password_problem(password)
            if problem:
                print(problem)
                continue
            confirmation = getpass("Repetir nueva clave: ")
        if password != confirmation:
            print("Las claves no coinciden. Volve a intentarlo; no se guardo ningun cambio.")
            continue
        return password


def backup_database(source_path):
    source_path = Path(source_path).resolve(strict=True)
    directory = source_path.parent / "backups"
    directory.mkdir(exist_ok=True)
    target = directory / (
        "segurar-antes-recuperacion-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        + "-" + uuid4().hex + ".sqlite3")
    # API de backup SQLite: consistente incluso cuando el servidor tiene la BD abierta.
    with closing(sqlite3.connect(source_path.as_uri() + "?mode=ro", uri=True, timeout=10)) as source:
        with closing(sqlite3.connect(target)) as destination:
            source.backup(destination)
            if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("El respaldo no supero la verificacion de integridad.")
            if destination.execute("PRAGMA foreign_key_check").fetchall():
                raise RuntimeError("Hay relaciones inconsistentes. Se cancelo el restablecimiento.")
    return target


def inspect_account(source_path, email):
    # mode=ro evita crear silenciosamente otra base vacía.
    source_path = Path(source_path).resolve(strict=True)
    with closing(sqlite3.connect(source_path.as_uri() + "?mode=ro", uri=True, timeout=10)) as db:
        return db.execute("SELECT id, role FROM usuarios WHERE email=?", (email,)).fetchone()


def reset_existing_password(db, email, password):
    problem = password_problem(password)
    if problem:
        raise ValueError(problem)
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user is None:
        raise ValueError("El usuario no existe. No se crearon cuentas ni se borraron registros.")
    user.password = get_password_hash(password)
    revoke_sessions(db, user.id)
    db.commit()


def main():
    parser = argparse.ArgumentParser(description="Recuperacion local de acceso a SegurAR")
    parser.add_argument("action", choices=["reset-password", "create-admin"])
    parser.add_argument("email")
    parser.add_argument("--nombre", default="Administrador")
    args = parser.parse_args()
    email = args.email.strip()
    print("Base de datos: " + str(DB_PATH.resolve()))
    try:
        if args.action == "reset-password":
            if not DB_PATH.is_file():
                parser.error("No existe la base configurada. No se creo una base nueva.")
            account = inspect_account(DB_PATH, email)
            if account is None:
                parser.error("No existe ese email en esta base. No se modifico ningun dato.")
            print(f"Cuenta encontrada: {email} | ID {account[0]} | rol {account[1]}")
        elif DB_PATH.is_file() and inspect_account(DB_PATH, email):
            parser.error("El email ya existe. Usa reset-password para conservar esa cuenta.")

        # El usuario define la clave en su terminal; no se acepta como argumento ni variable.
        password = ask_new_password()
        if DB_PATH.is_file():
            backup = backup_database(DB_PATH)
            print("Respaldo verificado: " + str(backup))
        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            if args.action == "reset-password":
                reset_existing_password(db, email, password)
            else:
                from backend.schemas import UsuarioCreate
                data = UsuarioCreate(nombre=args.nombre, email=email, role="admin", password=password)
                if db.query(Usuario).filter(Usuario.email == str(data.email)).first():
                    raise ValueError("El email ya existe. No se sobrescribio la cuenta.")
                db.add(Usuario(nombre=data.nombre.strip(), email=str(data.email), role="admin",
                               password=get_password_hash(password)))
                db.commit()
        print("Credencial guardada. Usuarios y polizas conservados.")
        print("Inicia sesion con el mismo email y la NUEVA clave. No uses la guardada por el navegador.")
    except (EOFError, KeyboardInterrupt, GetPassWarning):
        print("\nEntrada cancelada o terminal sin escritura oculta. No se cambio la clave.")
        raise SystemExit(1)
    except (OSError, sqlite3.Error, SQLAlchemyError, ValueError, RuntimeError):
        # No mostrar contraseñas, SQL, parámetros ni trazas con material sensible.
        print("No se pudo completar la operacion. Verifica los datos y el acceso a la base.")
        print("No se imprimen detalles internos para proteger las credenciales.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
