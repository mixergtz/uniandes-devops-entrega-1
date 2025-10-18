from flask import Flask, jsonify
from .config import Config, db
from .routes import api_bp
from .models import BlacklistEntry
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init DB
    db.init_app(app)

    # Health check (para Beanstalk/ELB)
    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    # Blueprints (API)
    app.register_blueprint(api_bp)

    # Auto-migración simple (create_all) si está habilitado
    # Útil para la entrega (no usar en prod real).
    run_migs = os.getenv("RUN_DB_MIGRATIONS", "0")
    if run_migs == "1":
        with app.app_context():
            db.create_all()

    return app

# Beanstalk busca 'application' en wsgi.py, pero también lo exponemos aquí por si acaso
application = create_app()
