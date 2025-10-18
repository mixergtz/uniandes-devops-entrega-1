from .config import db
from datetime import datetime

class BlacklistEntry(db.Model):
    __tablename__ = "blacklist"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), nullable=False, unique=True, index=True)  # RFC 3696-ish
    app_uuid = db.Column(db.String(36), nullable=False, index=True)  # UUID string
    blocked_reason = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<BlacklistEntry {self.email}>"
