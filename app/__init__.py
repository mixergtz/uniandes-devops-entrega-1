import os
import newrelic.agent

# Initialize New Relic agent
newrelic.agent.initialize()

from flask import Flask, jsonify
from .config import Config, db
from .routes import api_bp
from .models import BlacklistEntry

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init DB
    db.init_app(app)

    # Health check (for Beanstalk/ELB)
    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    # Blueprints (API)
    app.register_blueprint(api_bp)

    # Simple auto-migration (create_all) if enabled
    # Useful for delivery (do not use in real production).
    run_migs = os.getenv("RUN_DB_MIGRATIONS", "0")
    if run_migs == "1":
        with app.app_context():
            db.create_all()

    return app

# Beanstalk looks for 'application' in wsgi.py, but we also expose it here just in case
application = create_app()
