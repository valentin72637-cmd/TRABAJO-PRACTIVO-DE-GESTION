# backend/schemas.py

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


# ============================================================
# TIPOS PERMITIDOS
# ============================================================

RolUsuario = Literal[
    "admin",
    "cliente"
]

TipoPoliza = Literal[
    "Auto",
    "Hogar",
    "Vida",
    "Salud"
]

EstadoPoliza = Literal[
    "Vigente",
    "Por vencer",
    "Vencida"
]


# ============================================================
# USUARIOS
# ============================================================

class UsuarioBase(BaseModel):

    # Elimina espacios al principio/final de strings
    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    nombre: str = Field(
        min_length=1,
        max_length=100
    )

    email: EmailStr

    role: RolUsuario


class UsuarioCreate(UsuarioBase):

    model_config = ConfigDict(str_strip_whitespace=False)
    tipo_poliza: Optional[TipoPoliza] = None

    @field_validator("password")
    @classmethod
    def clave_no_publicada(cls, value):
        if value in {"Admin123!", "Cliente123!"}:
            raise ValueError("Elegí una contraseña nueva; las claves demo están bloqueadas")
        return value

    @model_validator(mode="after")
    def validar_poliza_inicial(self):
        if self.tipo_poliza and self.role != "cliente":
            raise ValueError("Solo los clientes pueden tener póliza inicial")
        return self

    password: str = Field(
        min_length=8,
        max_length=128
    )


class UsuarioUpdate(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=False
    )

    nombre: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    email: Optional[EmailStr] = None

    role: Optional[RolUsuario] = None

    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=128
    )

    @field_validator("password")
    @classmethod
    def clave_no_publicada(cls, value):
        if value in {"Admin123!", "Cliente123!"}:
            raise ValueError("Elegí una contraseña nueva; las claves demo están bloqueadas")
        return value


class UsuarioOut(BaseModel):

    id: int

    nombre: str

    email: EmailStr

    role: RolUsuario

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# PÓLIZAS
# ============================================================

class PolizaBase(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    numero: str = Field(
        min_length=1,
        max_length=50
    )

    tipo: TipoPoliza

    inicio: date

    vencimiento: date

    estado: EstadoPoliza

    mensaje: Optional[str] = Field(
        default=None,
        max_length=500
    )

    cliente_id: int = Field(
        gt=0
    )


class PolizaCreate(PolizaBase):
    pass


class PolizaUpdate(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    numero: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    tipo: Optional[TipoPoliza] = None

    inicio: Optional[date] = None

    vencimiento: Optional[date] = None

    estado: Optional[EstadoPoliza] = None

    mensaje: Optional[str] = Field(
        default=None,
        max_length=500
    )

    cliente_id: Optional[int] = Field(
        default=None,
        gt=0
    )


class PolizaOut(BaseModel):

    @model_validator(mode="after")
    def estado_actual(self):
        from backend.policy_rules import calcular_estado
        self.estado = calcular_estado(self.vencimiento)
        return self

    id: int

    numero: str

    tipo: TipoPoliza

    inicio: date

    vencimiento: date

    estado: EstadoPoliza

    mensaje: Optional[str] = None

    cliente_id: int

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# LOGIN / AUTH
# ============================================================

class LoginData(BaseModel):

    email: EmailStr

    password: str = Field(min_length=1, max_length=128)


class Token(BaseModel):

    access_token: str

    token_type: str = "bearer"


class TokenData(BaseModel):

    id: Optional[int] = None

    role: Optional[RolUsuario] = None
# ============================================================
# INFORMES DE PÓLIZAS
# ============================================================

class InformePolizaItem(BaseModel):
    id: int
    numero: str
    tipo: TipoPoliza
    inicio: date
    vencimiento: date
    estado: str
    mensaje: Optional[str] = None
    cliente_id: int
    cliente_nombre: Optional[str] = None


class PaginacionOut(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
