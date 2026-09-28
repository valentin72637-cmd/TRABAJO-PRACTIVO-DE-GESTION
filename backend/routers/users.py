# backend/routers/users.py

from typing import List
from uuid import uuid4
from backend.policy_rules import business_today, calcular_estado

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth_utils import (
    get_password_hash,
    require_admin,
    get_current_user,
    revoke_sessions
)
from backend.database import get_db
from backend.models import Usuario, Poliza
from backend.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate


router = APIRouter(
    prefix="/users",
    tags=["Usuarios"]
)


# ============================================================
# LISTAR USUARIOS
# Solo administrador
# ============================================================

@router.get(
    "/",
    response_model=List[UsuarioOut]
)
def list_users(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin)
):

    return db.query(Usuario).all()

# ============================================================
# LISTAR ASESORES
# Usuario autenticado
# ============================================================

@router.get(
    "/asesores",
    response_model=List[UsuarioOut]
)
def list_asesores(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return (
        db.query(Usuario)
        .filter(Usuario.role == "admin")
        .all()
    )

# ============================================================
# CREAR USUARIO
# Solo administrador
# ============================================================

@router.post(
    "/",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    data: UsuarioCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin)
):
    # --------------------------------------------------------
    # VALIDAR ROL
    # --------------------------------------------------------

    if data.role not in ("admin", "cliente"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol debe ser 'admin' o 'cliente'"
        )


    # --------------------------------------------------------
    # VALIDAR CONTRASEÑA
    # --------------------------------------------------------

    if len(data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "La contraseña debe tener "
                "al menos 8 caracteres"
            )
        )


    # --------------------------------------------------------
    # VALIDAR NOMBRE
    # --------------------------------------------------------

    if not data.nombre.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre es obligatorio"
        )
    
    # Comprobar email duplicado
    existing = (
        db.query(Usuario)
        .filter(Usuario.email == data.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # Guardar contraseña utilizando bcrypt
    hashed_password = get_password_hash(
        data.password
    )

    user = Usuario(
        nombre=data.nombre.strip(),
        email=data.email,
        password=hashed_password,
        role=data.role
    )

    db.add(user)
    if data.tipo_poliza:
        db.flush()
        inicio = business_today()
        try:
            vencimiento = inicio.replace(year=inicio.year + 1)
        except ValueError:
            vencimiento = inicio.replace(year=inicio.year + 1, day=28)
        db.add(Poliza(numero=f"POL-{uuid4().hex}", tipo=data.tipo_poliza,
                      inicio=inicio, vencimiento=vencimiento,
                      estado=calcular_estado(vencimiento),
                      mensaje=f"Póliza {data.tipo_poliza} activa", cliente_id=user.id))
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# ACTUALIZAR USUARIO
# Solo administrador
# ============================================================

@router.put(
    "/{user_id}",
    response_model=UsuarioOut
)
def update_user(
    user_id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin)
):

    # --------------------------------------------------------
    # 1. BUSCAR USUARIO
    # --------------------------------------------------------

    user = (
        db.query(Usuario)
        .filter(Usuario.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )


    # --------------------------------------------------------
    # 2. VALIDAR ROL
    # --------------------------------------------------------

    if (
        data.role is not None
        and data.role not in ("admin", "cliente")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol debe ser 'admin' o 'cliente'"
        )


    # --------------------------------------------------------
    # 3. IMPEDIR QUE EL ADMIN CAMBIE SU PROPIO ROL
    # --------------------------------------------------------

    if (
        user.id == admin.id
        and data.role is not None
        and data.role != admin.role
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No puedes cambiar tu propio rol "
                "mientras tienes la sesión iniciada"
            )
        )


    # --------------------------------------------------------
    # 4. PROTEGER AL ÚLTIMO ADMINISTRADOR
    # --------------------------------------------------------

    if (
        user.role == "admin"
        and data.role is not None
        and data.role != "admin"
    ):

        cantidad_admins = (
            db.query(Usuario)
            .filter(Usuario.role == "admin")
            .count()
        )

        if cantidad_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se puede cambiar el rol del último "
                    "administrador del sistema"
                )
            )


    # --------------------------------------------------------
    # PROTEGER CLIENTE CON PÓLIZAS
    # --------------------------------------------------------

    if (
        user.role == "cliente"
        and data.role is not None
        and data.role == "admin"
    ):

        cantidad_polizas = (
            db.query(Poliza)
            .filter(
                Poliza.cliente_id == user.id
            )
            .count()
        )

        if cantidad_polizas > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se puede convertir este cliente "
                    "en administrador mientras tenga "
                    "pólizas asignadas"
                )
            )

        
    # --------------------------------------------------------
    # 5. NOMBRE
    # --------------------------------------------------------

    if data.nombre is not None:

        nombre_limpio = data.nombre.strip()

        if not nombre_limpio:
            raise HTTPException(400, "El nombre es obligatorio")
        user.nombre = nombre_limpio


    # --------------------------------------------------------
    # 6. EMAIL
    # --------------------------------------------------------

    if data.email is not None:

        existing_email = (
            db.query(Usuario)
            .filter(
                Usuario.email == data.email,
                Usuario.id != user_id
            )
            .first()
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )

        user.email = data.email


    # --------------------------------------------------------
    # 7. ROL
    # --------------------------------------------------------

    if data.role is not None:
        if data.role != user.role:
            revoke_sessions(db, user.id)
        user.role = data.role


    # --------------------------------------------------------
    # 8. CONTRASEÑA
    # --------------------------------------------------------

    if data.password is not None:
        revoke_sessions(db, user.id)

        if len(data.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "La contraseña debe tener "
                    "al menos 8 caracteres"
                )
            )

        user.password = get_password_hash(
            data.password
        )


    # --------------------------------------------------------
    # 9. GUARDAR
    # --------------------------------------------------------

    db.commit()
    db.refresh(user)

    return user


# ============================================================
# ELIMINAR USUARIO
# Solo administradores
# ============================================================

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin)
):

    # --------------------------------------------------------
    # 1. BUSCAR USUARIO
    # --------------------------------------------------------

    user = (
        db.query(Usuario)
        .filter(Usuario.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )


    # --------------------------------------------------------
    # 2. IMPEDIR QUE EL ADMIN SE ELIMINE A SÍ MISMO
    # --------------------------------------------------------

    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No puedes eliminar tu propio usuario "
                "mientras tienes la sesión iniciada"
            )
        )


    # --------------------------------------------------------
    # 3. PROTEGER AL ÚLTIMO ADMINISTRADOR
    # --------------------------------------------------------

    if user.role == "admin":

        cantidad_admins = (
            db.query(Usuario)
            .filter(Usuario.role == "admin")
            .count()
        )

        if cantidad_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se puede eliminar el último "
                    "administrador del sistema"
                )
            )


    # --------------------------------------------------------
    # 4. ELIMINAR
    # --------------------------------------------------------

    db.delete(user)
    db.commit()

    return None
