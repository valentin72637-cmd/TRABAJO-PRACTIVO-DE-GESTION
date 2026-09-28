"""Servidor UI de prueba: python -B -m tests.serve_tab_fixture (SQLite solo en memoria)."""
from datetime import timedelta, datetime
from pathlib import Path
from urllib.parse import quote
import asyncio
from fastapi import FastAPI, Depends, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base, get_db, engine as real_engine
from backend.models import Usuario, Poliza, Sesion
from backend.auth_utils import get_password_hash, get_current_user, oauth2_scheme, decode_session
from backend.policy_rules import business_today
from backend.routers import auth, users, polizas, informes


def prohibit_real_database(*args):
    raise RuntimeError("El servidor de prueba no puede abrir la base real")


event.listen(real_engine, "connect", prohibit_real_database)
fixture_engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread":False})
event.listen(fixture_engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
Base.metadata.create_all(fixture_engine)
sessions = sessionmaker(fixture_engine)
with sessions() as db:
    # Cuentas exclusivamente ficticias; no se crean en segurar.db.
    password = get_password_hash("SoloPruebaLocal-2026!")
    db.add_all([
        Usuario(id=1,nombre="QA Administrador",email="qa.admin@example.com",password=password,role="admin"),
        Usuario(id=2,nombre="QA Cliente A",email="qa.cliente@example.com",password=password,role="cliente"),
        Usuario(id=3,nombre="QA Cliente B",email="qa.otro@example.com",password=password,role="cliente")])
    db.flush()
    for uid, number in [(2,"QA-AUTO-A"),(3,"QA-HOGAR-B")]:
        db.add(Poliza(numero=number,tipo="Auto" if uid==2 else "Hogar",inicio=business_today(),
                      vencimiento=business_today()+timedelta(days=90),estado="Vigente",
                      cliente_id=uid,mensaje="Poliza ficticia de prueba"))
    db.commit()

app = FastAPI(title="SegurAR QA - base efimera")


class SerializeMemoryConnection:
    # StaticPool comparte una conexión: serializar solicitudes evita rollback
    # cruzado entre sesiones ORM concurrentes en este servidor ficticio.
    def __init__(self, app):
        self.app = app
        self.lock = asyncio.Lock()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            async with self.lock:
                await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)


app.add_middleware(SerializeMemoryConnection)
def fixture_db():
    with sessions() as db:
        try: yield db
        except Exception:
            db.rollback()
            raise
app.dependency_overrides[get_db] = fixture_db
for router in (auth.router, users.router, polizas.router, informes.router):
    app.include_router(router)


@app.post("/qa/expire-current", status_code=204)
def expire_current(token=Depends(oauth2_scheme), user=Depends(get_current_user), db=Depends(get_db)):
    _, sid = decode_session(token)
    db.get(Sesion,sid).vence = datetime(2000,1,1)
    db.commit()
    return Response(status_code=204)


class FixtureFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if isinstance(getattr(response, "path", None), (str,Path)) and str(response.path).endswith(".html"):
            text = Path(response.path).read_text(encoding="utf-8")
            text = text.replace("</head>", "<script>window.SEGURAR_API_URL=location.origin;</script></head>")
            banner = ('<aside style="background:#ffed99;color:#111;padding:8px">QA: datos ficticios. '
                      '<a href="/'+quote((path or "index.html").replace(chr(92),"/"))+'" target="_blank" rel="opener">Abrir copia con opener</a> '
                      '<button onclick="SegurAR.request(\'/qa/expire-current\',{method:\'POST\'}).then(()=>location.reload())">'
                      'Invalidar esta sesion de prueba</button></aside>')
            # Banner fuera del contenido protegido, solo en este servidor de pruebas.
            banner += """<p id="qa-runtime" role="status">QA: esperando inicializacion de pestaña</p>
            <script>
            SegurAR.tabReady.then(ok=>document.getElementById('qa-runtime').textContent='QA: pestaña lista='+ok);
            document.getElementById('loginForm')?.addEventListener('submit', event=>{
                document.getElementById('qa-runtime').textContent='QA: submit recibido; formulario valido='+event.target.checkValidity();
            });
            </script>"""
            text = text.replace("</body>", banner+"</body>")
            return HTMLResponse(text,headers={"Cache-Control":"no-store"})
        return response


app.mount("/", FixtureFiles(directory=Path(__file__).resolve().parents[1]/"login",html=True), name="frontend")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="127.0.0.1",port=8765,access_log=False)
