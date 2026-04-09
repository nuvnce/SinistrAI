from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return Utilisateur.query.get(int(user_id))


class Utilisateur(UserMixin, db.Model):
    __tablename__ = 'utilisateurs'
    id            = db.Column(db.Integer, primary_key=True)
    nom           = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), default='gestionnaire')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    dossiers      = db.relationship('Dossier', backref='createur', lazy=True)

    def __repr__(self):
        return f'<Utilisateur {self.email}>'


class Dossier(db.Model):
    __tablename__ = 'dossiers'
    id             = db.Column(db.Integer, primary_key=True)
    reference      = db.Column(db.String(20), unique=True, nullable=False)
    statut         = db.Column(db.String(30), default='EN_ATTENTE')
    score_anomalie = db.Column(db.Float, nullable=True)
    date_creation  = db.Column(db.DateTime, default=datetime.utcnow)
    date_mise_a_jour = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by     = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    documents = db.relationship('Document', backref='dossier', lazy=True, cascade='all, delete-orphan')
    resultats = db.relationship('ResultatAnalyse', backref='dossier', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Dossier {self.reference}>'


class Document(db.Model):
    __tablename__ = 'documents'
    id            = db.Column(db.Integer, primary_key=True)
    dossier_id    = db.Column(db.Integer, db.ForeignKey('dossiers.id'), nullable=False)
    chemin_fichier = db.Column(db.String(255), nullable=False)
    ocr_data      = db.Column(db.Text, nullable=True)   # JSON stocké en texte
    date_upload   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Document {self.id} — Dossier {self.dossier_id}>'


class ResultatAnalyse(db.Model):
    __tablename__ = 'resultats_analyse'
    id              = db.Column(db.Integer, primary_key=True)
    dossier_id      = db.Column(db.Integer, db.ForeignKey('dossiers.id'), nullable=False)
    regles_violees  = db.Column(db.Text, nullable=True)   # JSON stocké en texte
    score_if        = db.Column(db.Float, nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ResultatAnalyse dossier={self.dossier_id}>'

class Log(db.Model):
    __tablename__ = 'logs'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=True)
    action      = db.Column(db.String(100), nullable=False)
    details     = db.Column(db.Text, nullable=True)
    ip_address  = db.Column(db.String(45), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Log {self.action} — user={self.user_id}>'