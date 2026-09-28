"""Autenticación compartida por formulario y Swagger."""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Usuario, Sesion
from backend.schemas import LoginData
from backend.auth_utils import (
    decode_session, get_current_user, get_password_hash, is_published_demo_password,
    issue_session, needs_password_update, oauth2_scheme, verify_password,
)
router = APIRouter(prefix="/auth", tags=["Auth"])


def authenticate(db, email, password):
    user = db.query(Usuario).filter(Usuario.email == email.strip()).first()
    if (is_published_demo_password(password) or user is None
            or not verify_password(password, user.password)):
        raise HTTPException(401, "Email o contraseña incorrectos",
                            headers={"WWW-Authenticate": "Bearer"})
    if needs_password_update(user.password):
        user.password = get_password_hash(password)
    return user


@router.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    user = authenticate(db, str(data.email), data.password)
    token = issue_session(db, user)
    return {"access_token": token, "token_type": "bearer",
            "id": user.id, "nombre": user.nombre, "email": user.email, "role": user.role}


@router.post("/token")
def login_swagger(form_data: OAuth2PasswordRequestForm = Depends(),
                  db: Session = Depends(get_db)):
    user = authenticate(db, form_data.username, form_data.password)
    return {"access_token": issue_session(db, user), "token_type": "bearer"}


@router.get("/me")
def get_me(current_user: Usuario = Depends(get_current_user)):
    return {"id": current_user.id, "nombre": current_user.nombre,
            "email": current_user.email, "role": current_user.role}


@router.post("/logout", status_code=204)
def logout(token: str = Depends(oauth2_scheme),
           current_user: Usuario = Depends(get_current_user),
           db: Session = Depends(get_db)):
    _, session_id = decode_session(token)
    db.query(Sesion).filter(Sesion.id == session_id,
                           Sesion.usuario_id == current_user.id).delete()
    db.commit()
    return Response(status_code=204)
