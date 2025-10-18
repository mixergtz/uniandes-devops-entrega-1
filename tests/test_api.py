import os
import uuid
import json
import pathlib
import pytest

# 1) Definir variables de entorno ANTES de importar la app
TEST_DB_FILE = pathlib.Path("test_api.sqlite")
# Limpieza preventiva por si quedó de una corrida anterior
if TEST_DB_FILE.exists():
    TEST_DB_FILE.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"
os.environ["AUTH_BEARER_TOKEN"] = "testtoken"
# Desactivamos la automigración para controlar el schema manualmente en cada test
os.environ["RUN_DB_MIGRATIONS"] = "0"

# 2) Ahora sí importamos la app y la DB (Config ya leerá las env vars correctas)
from app import create_app
from app.config import db


def auth_headers(token="testtoken"):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session", autouse=True)
def clean_sqlite_file():
    """Limpia el archivo SQLite al final de toda la sesión de tests."""
    yield
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()


@pytest.fixture()
def client():
    """
    Crea la app y reinicia el esquema (drop_all/create_all) ANTES de cada test.
    Retorna un test client listo para usar.
    """
    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        db.drop_all()
        db.create_all()

        with app.test_client() as c:
            yield c


def test_add_to_blacklist_success(client):
    email = f"user-{uuid.uuid4().hex[:8]}@test.com"
    payload = {
        "email": email,
        "app_uuid": str(uuid.uuid4()),
        "blocked_reason": "spam detected",
    }
    resp = client.post("/blacklists", data=json.dumps(payload), headers=auth_headers())
    assert resp.status_code == 201, resp.get_data(as_text=True)
    body = resp.get_json()
    assert body["message"] == "Email agregado a la lista negra global"


def test_add_to_blacklist_is_idempotent_on_duplicate(client):
    email = f"dup-{uuid.uuid4().hex[:8]}@test.com"
    payload = {"email": email, "app_uuid": str(uuid.uuid4()), "blocked_reason": "test"}

    r1 = client.post("/blacklists", data=json.dumps(payload), headers=auth_headers())
    assert r1.status_code == 201, r1.get_data(as_text=True)

    # Mismo email → respuesta idempotente (200)
    r2 = client.post("/blacklists", data=json.dumps(payload), headers=auth_headers())
    assert r2.status_code == 200, r2.get_data(as_text=True)
    assert r2.get_json()["message"] == "Email ya estaba en la lista negra"


def test_check_blacklist_true_after_post(client):
    email = f"blocked-{uuid.uuid4().hex[:8]}@test.com"
    payload = {"email": email, "app_uuid": str(uuid.uuid4())}

    r1 = client.post("/blacklists", data=json.dumps(payload), headers=auth_headers())
    assert r1.status_code == 201, r1.get_data(as_text=True)

    r2 = client.get(f"/blacklists/{email}", headers=auth_headers())
    assert r2.status_code == 200
    body = r2.get_json()
    assert body["blocked"] is True
    assert body["email"] == email
    assert "blocked_reason" in body
    assert "created_at" in body


def test_check_blacklist_false_for_unknown_email(client):
    email = f"unknown-{uuid.uuid4().hex[:8]}@test.com"
    r = client.get(f"/blacklists/{email}", headers=auth_headers())
    assert r.status_code == 200
    body = r.get_json()
    assert body["blocked"] is False
    assert body["blocked_reason"] is None
    assert body["created_at"] is None


def test_unauthorized_without_bearer_token(client):
    payload = {
        "email": f"noauth-{uuid.uuid4().hex[:8]}@test.com",
        "app_uuid": str(uuid.uuid4()),
        "blocked_reason": "nope",
    }
    r = client.post("/blacklists", data=json.dumps(payload), headers={"Content-Type": "application/json"})
    assert r.status_code == 401
    assert r.get_json()["error"] == "Unauthorized"


def test_validation_errors(client):
    payload = {
        "email": f"bad-{uuid.uuid4().hex[:8]}@test.com",
        "app_uuid": "not-a-uuid",          # UUID inválido
        "blocked_reason": "x" * 256,       # demasiado largo (>255)
    }
    r = client.post("/blacklists", data=json.dumps(payload), headers=auth_headers())
    # La vista puede fallar por reason largo o por UUID inválido, ambas son 400
    assert r.status_code == 400
