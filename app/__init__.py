from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
import json

db           = SQLAlchemy()
login_manager = LoginManager()
mail          = Mail()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    app.jinja_env.filters['fromjson'] = json.loads

    from app.routes import auth, dossiers, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(dossiers.bp)
    app.register_blueprint(admin.bp)

    return app