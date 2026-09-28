"""Regresiones aisladas: python -B -m unittest discover -s tests -v."""
import asyncio
import json
import unittest
from collections import Counter
from datetime import timedelta
from unittest.mock import patch

from sqlalchemy import create_engine, event, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base, engine as production_engine, get_db
from backend.main import app
from backend.models import Usuario, Poliza, Sesion
from backend.auth_utils import get_password_hash, create_access_token, verify_password
from backend.policy_rules import business_today, calcular_estado
from backend.reportes_pdf import resumen_categorias


def reject_production_connection(*args):
    raise AssertionError("Las pruebas no pueden conectarse a la base real")


event.listen(production_engine, "connect", reject_production_connection)


async def asgi_request(method, path, token=None, data=None):
    route, _, query = path.partition("?")
    headers = [(b"content-type", b"application/json")]
    if token:
        headers.append((b"authorization", ("Bearer " + token).encode()))
    messages = []
    scope = {"type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"},
             "http_version": "1.1", "method": method, "scheme": "http",
             "path": route, "raw_path": route.encode(), "query_string": query.encode(),
             "root_path": "", "headers": headers,
             "server": ("test", 80), "client": ("127.0.0.1", 12345)}
    async def receive():
        return {"type": "http.request", "body": json.dumps(data).encode() if data is not None else b"",
                "more_body": False}
    async def send(message):
        messages.append(message)
    await app(scope, receive, send)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    try:
        value = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        value = body
    return status, value


class SecurityRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = "Clave privada 2026!"
        cls.password_hash = get_password_hash(cls.password)

    def setUp(self):
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        event.listen(self.engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(self.engine)
        def isolated_db():
            with self.sessions() as db:
                try:
                    yield db
                except Exception:
                    db.rollback()
                    raise
        app.dependency_overrides[get_db] = isolated_db
        with self.sessions() as db:
            for name, role in [("admin", "admin"), ("cliente", "cliente"), ("otro", "cliente")]:
                db.add(Usuario(nombre=name, email=name + "@example.com", role=role,
                               password=self.password_hash))
            db.commit()
        self.admin = self.login("admin")
        self.client = self.login("cliente")

    def tearDown(self):
        app.dependency_overrides.clear()
        self.engine.dispose()

    def request(self, method, path, token=None, data=None):
        return asyncio.run(asgi_request(method, path, token, data))

    def login(self, name, password=None):
        status, body = self.request("POST", "/auth/login",
                                   data={"email": name + "@example.com", "password": password or self.password})
        self.assertEqual(status, 200, body)
        return body["access_token"]

    def policy(self, number="P-1", days=10, client=2, **extra):
        today = business_today()
        data = {"numero": number, "tipo": "Auto", "inicio": str(today - timedelta(days=100)),
                "vencimiento": str(today + timedelta(days=days)), "estado": "Vigente",
                "cliente_id": client, "mensaje": "<img src=x onerror=alert(1)>"}
        data.update(extra)
        status, body = self.request("POST", "/polizas/", self.admin, data)
        self.assertEqual(status, 201, body)
        return body

    def test_old_token_cannot_inherit_reused_id(self):
        old = self.login("otro")
        self.assertEqual(self.request("DELETE", "/users/3", self.admin)[0], 204)
        status, new = self.request("POST", "/users/", self.admin,
                                  {"nombre": "nuevo", "email": "nuevo@example.com",
                                   "role": "admin", "password": self.password})
        self.assertEqual(status, 201)
        self.assertEqual(new["id"], 3)  # SQLite reutiliza el ID: aun así, JWT inválido.
        self.assertEqual(self.request("GET", "/users/", old)[0], 401)

    def test_legacy_unsigned_session_token_rejected(self):
        token = create_access_token({"sub": "1", "role": "admin"})
        self.assertEqual(self.request("GET", "/auth/me", token)[0], 401)

    def test_password_change_revokes_sessions_and_partial_update_works(self):
        other = self.login("cliente")
        status, data = self.request("PUT", "/users/2", self.admin, {"password": "Otra clave segura!"})
        self.assertEqual(status, 200, data)
        for token in [other, self.client]:
            self.assertEqual(self.request("GET", "/auth/me", token)[0], 401)
        self.login("cliente", "Otra clave segura!")

    def test_partial_email_edit_and_empty_update(self):
        self.assertEqual(self.request("PUT", "/users/2", self.admin, {"email": "nuevo@example.com"})[0], 200)
        self.assertEqual(self.request("PUT", "/users/2", self.admin, {})[0], 200)
        self.assertEqual(self.request("PUT", "/users/2", self.admin, {"nombre": "  "})[0], 400)

    def test_logout_revokes_only_current_session(self):
        other = self.login("cliente")
        self.assertEqual(self.request("POST", "/auth/logout", self.client)[0], 204)
        self.assertEqual(self.request("GET", "/auth/me", self.client)[0], 401)
        self.assertEqual(self.request("GET", "/auth/me", other)[0], 200)

    def test_role_change_revokes_sessions(self):
        self.assertEqual(self.request("PUT", "/users/2", self.admin, {"role": "admin"})[0], 200)
        self.assertEqual(self.request("GET", "/users/", self.client)[0], 401)

    def test_long_password_and_whitespace_preserved(self):
        password = " " + "a" * 72 + "UNO "
        status, _ = self.request("POST", "/users/", self.admin,
                                {"nombre": "largo", "email": "largo@example.com",
                                 "role": "cliente", "password": password})
        self.assertEqual(status, 201)
        self.login("largo", password)
        for wrong in [password.strip(), " " + "a" * 72 + "DOS "]:
            self.assertEqual(self.request("POST", "/auth/login", data={
                "email": "largo@example.com", "password": wrong})[0], 401)

    def test_published_password_cannot_authenticate_or_be_created(self):
        with self.sessions() as db:
            db.get(Usuario, 2).password = get_password_hash("Cliente123!")
            db.commit()
        self.assertEqual(self.request("POST", "/auth/login", data={
            "email": "cliente@example.com", "password": "Cliente123!"})[0], 401)
        self.assertEqual(self.request("PUT", "/users/2", self.admin, {"password": "Admin123!"})[0], 422)

    def test_legacy_unicode_migrates(self):
        with self.sessions() as db:
            db.get(Usuario, 2).password = "Contraseña ñ segura"
            db.commit()
        self.login("cliente", "Contraseña ñ segura")
        with self.sessions() as db:
            self.assertTrue(db.get(Usuario, 2).password.startswith("$pbkdf2-sha256$"))

    def test_bcrypt_legacy_migrates_and_refuses_truncation(self):
        import bcrypt
        stored = bcrypt.hashpw(self.password.encode(), bcrypt.gensalt(rounds=4)).decode()
        with self.sessions() as db:
            db.get(Usuario, 2).password = stored
            db.commit()
        self.login("cliente")
        self.assertFalse(verify_password("a" * 72 + "otra", bcrypt.hashpw(b"a"*72, bcrypt.gensalt(rounds=4)).decode()))

    def test_permissions_and_ownership(self):
        self.policy(client=2)
        self.policy("P-otro", client=3)
        self.assertEqual(self.request("GET", "/users/", self.client)[0], 403)
        self.assertEqual(self.request("GET", "/polizas/")[0], 401)
        self.assertEqual(len(self.request("GET", "/polizas/mias", self.client)[1]), 1)
        for endpoint in ["listado", "resumen", "exportar.pdf"]:
            self.assertEqual(self.request("GET", "/informes/polizas/" + endpoint + "?cliente_id=3", self.client)[0], 403)
        for method, path, body in [("DELETE", "/users/1", None), ("PUT", "/users/1", {"role":"cliente"})]:
            self.assertEqual(self.request(method, path, self.admin, body)[0], 400)

    def test_dates_states_and_aggregates_match(self):
        for index, days in enumerate([-1, 0, 7, 8, 30, 31, 60, 61]):
            result = self.policy("P-" + str(index), days)
            self.assertEqual(result["estado"], calcular_estado(business_today()+timedelta(days=days)))
        _, summary = self.request("GET", "/informes/polizas/resumen", self.client)
        _, listing = self.request("GET", "/informes/polizas/listado?page_size=3", self.client)
        self.assertEqual(summary["indicadores"], {"total_polizas":8, "vigentes":3, "proximas_a_vencer":4, "vencidas":1})
        self.assertEqual(listing["pagination"]["total_items"], 8)
        self.assertEqual(sum(row["cantidad"] for row in summary["vencimientos_por_tramo"]), 8)
        for state in ["Vigente", "Por vencer", "Vencida"]:
            from urllib.parse import urlencode
            query = "?" + urlencode({"estado":state})
            s = self.request("GET", "/informes/polizas/resumen"+query, self.client)[1]
            l = self.request("GET", "/informes/polizas/listado"+query, self.client)[1]
            self.assertEqual(s["indicadores"]["total_polizas"], len(l["items"]))

    def test_state_recomputed_for_old_stored_values(self):
        self.policy(days=-1)
        with self.sessions() as db:
            db.query(Poliza).update({"estado":"Vigente"})
            db.commit()
        self.assertEqual(self.request("GET", "/polizas/mias", self.client)[1][0]["estado"], "Vencida")

    def test_invalid_dates_and_pagination(self):
        self.assertEqual(self.request("GET", "/informes/polizas/listado?page=0", self.client)[0], 422)
        self.assertEqual(self.request("GET", "/informes/polizas/listado?page_size=101", self.client)[0], 422)
        self.assertEqual(self.request("GET", "/informes/polizas/resumen?vencimiento_desde=2026-12-31&vencimiento_hasta=2026-01-01", self.client)[0], 400)

    def test_atomic_client_policy_success(self):
        status, user = self.request("POST", "/users/", self.admin,
                                   {"nombre":"joint", "email":"joint@example.com", "password":self.password,
                                    "role":"cliente", "tipo_poliza":"Hogar"})
        self.assertEqual(status, 201, user)
        with self.sessions() as db:
            self.assertEqual(db.query(Poliza).filter(Poliza.cliente_id == user["id"]).count(), 1)

    def test_atomic_client_policy_rollback(self):
        def fail_insert(*args):
            raise IntegrityError("test collision", {}, Exception("forced"))
        event.listen(Poliza, "before_insert", fail_insert)
        try:
            status, _ = self.request("POST", "/users/", self.admin,
                                    {"nombre":"rollback", "email":"rollback@example.com", "password":self.password,
                                     "role":"cliente", "tipo_poliza":"Auto"})
            self.assertEqual(status, 409)
        finally:
            event.remove(Poliza, "before_insert", fail_insert)
        with self.sessions() as db:
            self.assertEqual(db.query(Usuario).filter_by(email="rollback@example.com").count(), 0)

    def test_pdf_receives_every_filtered_row_over_10000(self):
        today = business_today()
        with self.sessions() as db:
            db.bulk_insert_mappings(Poliza, [
                {"numero":"B-"+str(i), "tipo":"Auto", "inicio":today, "vencimiento":today,
                 "estado":"Vigente", "cliente_id":2} for i in range(10001)])
            db.commit()
        with patch("backend.routers.informes.crear_pdf_polizas", return_value=b"%PDF-test") as render:
            self.assertEqual(self.request("GET", "/informes/polizas/exportar.pdf", self.client)[0], 200)
            self.assertEqual(len(render.call_args.args[0]), 10001)

    def test_pdf_real_export_and_empty_export(self):
        for create in [False, True]:
            if create:
                self.policy()
            status, pdf = self.request("GET", "/informes/polizas/exportar.pdf", self.client)
            self.assertEqual(status, 200)
            self.assertTrue(pdf.startswith(b"%PDF-"))

    def test_pdf_ties_and_empty_summaries(self):
        self.assertIn("Empatan", resumen_categorias(["Auto", "Vida"], Counter(Auto=2, Vida=2)))
        self.assertIn("No hay", resumen_categorias(["Auto", "Vida"], Counter()))

    def test_invalid_data_and_duplicate_email(self):
        self.assertEqual(self.request("POST", "/users/", self.admin, {
            "nombre":"x", "email":"admin@example.com", "role":"cliente", "password":self.password})[0], 400)
        self.assertEqual(self.request("POST", "/users/", self.admin, {
            "nombre":"x", "email":"x@example.com", "role":"admin", "password":self.password,
            "tipo_poliza":"Auto"})[0], 422)

    def test_independent_admin_client_logins_both_orders(self):
        for order in [("admin", "cliente"), ("cliente", "admin")]:
            first, second = [self.login(name) for name in order]
            for token, role in [(first,order[0]),(second,order[1])]:
                status, me = self.request("GET", "/auth/me", token)
                self.assertEqual(status, 200)
                self.assertEqual(me["role"], role)
            self.assertEqual(self.request("POST", "/auth/logout", first)[0], 204)
            self.assertEqual(self.request("GET", "/auth/me", first)[0], 401)
            self.assertEqual(self.request("GET", "/auth/me", second)[0], 200)

    def test_expired_session_does_not_affect_other_user(self):
        from backend.auth_utils import decode_session
        from datetime import datetime
        _, sid = decode_session(self.admin)
        with self.sessions() as db:
            db.get(Sesion, sid).vence = datetime(2000, 1, 1)
            db.commit()
        self.assertEqual(self.request("GET", "/auth/me", self.admin)[0], 401)
        self.assertEqual(self.request("GET", "/auth/me", self.client)[0], 200)

    def test_policy_crud_and_filter_remain_available(self):
        policy = self.policy("CRUD-TABS")
        status, updated = self.request("PUT", "/polizas/"+str(policy["id"]), self.admin,
                                      {"tipo":"Hogar", "mensaje":"Mensaje actualizado"})
        self.assertEqual(status, 200)
        self.assertEqual(updated["tipo"], "Hogar")
        filtered = self.request("GET", "/informes/polizas/listado?tipo=Hogar", self.client)[1]
        self.assertEqual(filtered["items"][0]["numero"], "CRUD-TABS")
        self.assertEqual(self.request("DELETE", "/polizas/"+str(policy["id"]), self.client)[0], 403)
        self.assertEqual(self.request("DELETE", "/polizas/"+str(policy["id"]), self.admin)[0], 204)
        self.assertEqual(self.request("GET", "/polizas/mias", self.client)[1], [])


if __name__ == "__main__":
    unittest.main()
