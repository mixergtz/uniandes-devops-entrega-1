import re
import uuid
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from .config import db
from .models import BlacklistEntry
from .schemas import BlacklistCreateSchema, BlacklistGetSchema

api_bp = Blueprint("api", __name__)

create_schema = BlacklistCreateSchema()
get_schema = BlacklistGetSchema()

def require_bearer_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    token = auth.split(" ", 1)[1].strip()
    return token == current_app.config["AUTH_BEARER_TOKEN"]

def client_ip():
    # Beanstalk/ELB suele pasar X-Forwarded-For
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "0.0.0.0"

def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except Exception:
        return False

@api_bp.post("/blacklists")
def add_to_blacklist():
    if not require_bearer_token():
        return jsonify(error="Unauthorized"), 401

    payload = request.get_json(silent=True) or {}
    errors = create_schema.validate(payload)
    if errors:
        return jsonify(error="ValidationError", details=errors), 400

    email = payload["email"].lower().strip()
    app_uuid = payload["app_uuid"].strip()
    blocked_reason = (payload.get("blocked_reason") or "").strip()

    if len(blocked_reason) > 255:
        return jsonify(error="blocked_reason must be ≤ 255 chars"), 400

    if not is_valid_uuid(app_uuid):
        return jsonify(error="app_uuid must be a valid UUID string"), 400

    entry = BlacklistEntry(
        email=email,
        app_uuid=app_uuid,
        blocked_reason=blocked_reason or None,
        ip_address=client_ip(),
    )

    db.session.add(entry)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Ya existe: se permite idempotencia (no es un error funcional)
        return jsonify(message="Email ya estaba en la lista negra"), 200

    return jsonify(message="Email agregado a la lista negra global"), 201

@api_bp.get("/blacklists/<string:email>")
def check_blacklist(email: str):
    if not require_bearer_token():
        return jsonify(error="Unauthorized"), 401

    e = email.lower().strip()
    entry = BlacklistEntry.query.filter_by(email=e).first()
    if not entry:
        data = {"blocked": False, "email": e, "blocked_reason": None, "created_at": None}
        return jsonify(get_schema.dump(data)), 200

    data = {
        "blocked": True,
        "email": entry.email,
        "blocked_reason": entry.blocked_reason,
        "created_at": entry.created_at,
    }
    return jsonify(get_schema.dump(data)), 200
