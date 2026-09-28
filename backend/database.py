# backend/database.py

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker


# ============================================================
# RUTA ABSOLUTA DE LA BASE DE DATOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "segurar.db"

SQLALCHEMY_DATABASE_URL = (
    f"sqlite:///{DB_PATH.as_posix()}"
)


# ============================================================
# ENGINE
# ============================================================

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


# ============================================================
# FOREIGN KEYS SQLITE
# ============================================================

@event.listens_for(engine, "connect")
def activar_foreign_keys(
    dbapi_connection,
    connection_record
):

    cursor = dbapi_connection.cursor()

    cursor.execute(
        "PRAGMA foreign_keys=ON"
    )

    cursor.close()


# ============================================================
# SESIONES
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


# ============================================================
# DEPENDENCIA FASTAPI
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
