import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sinistrai-secret-key-2025'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///sinistrai.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max par fichier