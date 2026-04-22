import os

class Config:
    SECRET_KEY        = os.environ.get('SECRET_KEY') or 'sinistrai-dev-key-2025'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///sinistrai.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER     = os.path.join(os.path.dirname(__file__), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # ── Configuration email ──────────────────────────────────────────────
    MAIL_SERVER   = 'smtp.gmail.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('SinistrAI', os.environ.get('MAIL_USERNAME'))
