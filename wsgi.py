from app import create_app

# Beanstalk busca 'application'
application = create_app()

# Para correr local: `gunicorn wsgi:application -b 0.0.0.0:8000`
