"""Contraseñas y sesiones revocables; se invalidan los JWT anteriores."""
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Sesion, Usuario

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
if not SECRET_KEY:
    raise RuntimeError("No se encontro SECRET_KEY en .env")
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"],
                          deprecated=["bcrypt"], pbkdf2_sha256__rounds=600000)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        scheme = pwd_context.identify(hashed_password)
        if scheme == "bcrypt" and len(plain_password.encode("utf-8")) > 72:
            return False  # La contraseña antigua ambigua requiere restablecimiento.
        if scheme:
            return pwd_context.verify(plain_password, hashed_password)
        if hashed_password.startswith("$"):
            return False
        # Migración de texto plano antiguo, también Unicode.
        return bool(hashed_password) and hmac.compare_digest(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def needs_password_update(stored: str) -> bool:
    return pwd_context.identify(stored) != "pbkdf2_sha256"


def is_published_demo_password(password: str) -> bool:
    return password in {"Admin123!", "Cliente123!"}


def create_access_token(data: dict, expires_delta=None) -> str:
    payload = dict(data)
    payload["exp"] = datetime.now(timezone.utc) + (
        expires_delta if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def issue_session(db: Session, user: Usuario) -> str:
    now = datetime.now(timezone.utc)
    db.query(Sesion).filter(Sesion.vence <= now.replace(tzinfo=None)).delete()
    session_id = secrets.token_urlsafe(32)
    expires = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    db.add(Sesion(id=session_id, usuario_id=user.id, vence=expires.replace(tzinfo=None)))
    token = create_access_token({"sub": str(user.id), "jti": session_id})
    db.commit()
    return token


def revoke_sessions(db: Session, user_id: int):
    db.query(Sesion).filter(Sesion.usuario_id == user_id).delete(synchronize_session=False)


def decode_session(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],
                             options={"require_exp": True, "require_sub": True})
        if not isinstance(payload.get("jti"), str) or not payload["jti"]:
            raise ValueError("Missing session")
        return int(payload["sub"]), payload["jti"]
    except (JWTError, ValueError, TypeError, KeyError):
        raise HTTPException(401, "Token inválido o expirado",
                            headers={"WWW-Authenticate": "Bearer"}) from None


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)) -> Usuario:
    user_id, session_id = decode_session(token)
    session = db.get(Sesion, session_id)
    if (session is None or session.usuario_id != user_id
            or session.vence <= datetime.now(timezone.utc).replace(tzinfo=None)):
        raise HTTPException(401, "Sesión inválida o expirada",
                            headers={"WWW-Authenticate": "Bearer"})
    user = db.get(Usuario, user_id)
    if user is None:
        raise HTTPException(401, "Usuario no disponible")
    return user


def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.role != "admin":
        raise HTTPException(403, "Solo administradores pueden realizar esta acción")
    return current_user
