"""Punto de entrada sin cambios de datos al importar el módulo."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from backend.database import Base, engine
from backend.routers import auth, users, polizas, informes


@asynccontextmanager
async def lifespan(app):
    # Migración aditiva: crea sesiones; no modifica usuarios ni pólizas.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="SegurAR API", version="3.1", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in os.getenv(
        "CORS_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500").split(",") if x.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, error: IntegrityError):
    return JSONResponse(status_code=409, content={
        "detail": "No se pudo guardar: el registro está duplicado o cambió una relación. Actualizá e intentá nuevamente."})


for router in (auth.router, users.router, polizas.router, informes.router):
    app.include_router(router)


@app.get("/")
def root():
    return {"status": "ok", "msg": "API SegurAR funcionando"}
