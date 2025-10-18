import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///local.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTH_BEARER_TOKEN = os.getenv("AUTH_BEARER_TOKEN", "CHANGE_ME_IN_PROD")
    JSON_SORT_KEYS = False
