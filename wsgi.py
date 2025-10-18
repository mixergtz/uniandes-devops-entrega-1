from app import create_app

# Beanstalk looks for 'application'
application = create_app()

# To run locally: `gunicorn wsgi:application -b 0.0.0.0:8000`
