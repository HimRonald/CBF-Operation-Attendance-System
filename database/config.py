import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://cbf:cbf2024@68.183.186.239:5432/cbf2024'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Use an environment variable for the secret key
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'