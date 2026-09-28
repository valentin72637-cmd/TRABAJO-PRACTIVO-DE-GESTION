# backend/models.py
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)   # hash
    role = Column(String, nullable=False)       # "admin" | "cliente"

    polizas = relationship("Poliza", back_populates="cliente", cascade="all, delete")
    sesiones = relationship("Sesion", cascade="all, delete-orphan")


class Sesion(Base):
    __tablename__ = "sesiones"

    id = Column(String, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    vence = Column(DateTime, nullable=False)


class Poliza(Base):
    __tablename__ = "polizas"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, unique=True, index=True, nullable=False)
    tipo = Column(String, nullable=False)       # Auto, Hogar, Vida, Salud
    inicio = Column(Date, nullable=False)
    vencimiento = Column(Date, nullable=False)
    estado = Column(String, nullable=False)     # Vigente, Vencida, Por vencer
    mensaje = Column(String, nullable=True)
    
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    cliente = relationship("Usuario", back_populates="polizas")
