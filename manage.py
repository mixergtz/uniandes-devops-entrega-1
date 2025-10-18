"""
Comandos utilitarios locales para inicializar DB en RDS.
Uso:
  export DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:5432/DB
  python manage.py init-db
"""
import sys
from app import create_app
from app.config import db

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()
    print("DB schema created (create_all).")

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "init-db":
        init_db()
    else:
        print("Usage: python manage.py init-db")
