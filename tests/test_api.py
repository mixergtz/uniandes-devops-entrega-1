import os
import uuid
import json
import pathlib
import pytest

# 1) Define environment variables BEFORE importing the app
TEST_DB_FILE = pathlib.Path("test_api.sqlite")
# Preventive cleanup in case it was left from a previous run
if TEST_DB_FILE.exists():
    TEST_DB_FILE.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"
os.environ["AUTH_BEARER_TOKEN"] = "testtoken"
# We disable auto-migration to control the schema manually in each test
os.environ["RUN_DB_MIGRATIONS"] = "0"

# 2) Now we import the app and the DB (Config will already read the correct env vars)
from app import create_app
from app.config import db


def auth_headers(token="testtoken"):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session", autouse=True)
def clean_sqlite_file():
    """Cleans up the SQLite file at the end of the entire test session."""
    yield
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()


@pytest.fixture()
def client():
    """
    Creates the app and resets the schema (drop_all/create_all) BEFORE each test.
    Returns a test client ready to use.
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
    assert body["message"] == "Email added to global blacklist"


def test_add_to_blacklist_is_idempotent_on_duplicate(client):
    email = f"dup-{uuid.uuid4().hex[:8]}@test.com"
    payload = {"email": email, "app_uuid": str(uuid.uuid4()), "blocked_reason": "test"}

    r1 = client.post("/blacklists", data=json.dumps(payload), headers=auth_headers())
    assert r1.status_code == 201, r1.get_data(as_text=True)

    # Same email → idempotent response (200)
    r2 = client.post("/blacklists", data=json.dumps(payload), headers=auth_headers())
    assert r2.status_code == 200, r2.get_data(as_text=True)
    assert r2.get_json()["message"] == "Email was already on the blacklist"


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
        "app_uuid": "not-a-uuid",          # Invalid UUID
        "blocked_reason": "x" * 256,       # Too long (>255)
    }
    r = client.post("/blacklists", data=json.dumps(payload), headers=auth_headers())
    # The view can fail due to long reason or invalid UUID, both are 400
    assert r.status_code == 400
