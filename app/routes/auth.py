from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app import db
from app.models import Utilisateur
import bcrypt
from app.services.logger import log_action

bp = Blueprint('auth', __name__)


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Utilisateur.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
            login_user(user)
            log_action("CONNEXION", f"Connexion réussie", user_id=user.id)
            return redirect(url_for('dossiers.index'))
        else:
            flash('Email ou mot de passe incorrect.', 'danger')

    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    from flask_login import current_user
    log_action("DECONNEXION", "Déconnexion", user_id=current_user.id)
    logout_user()
    return redirect(url_for('auth.login'))


@bp.route('/init-admin')
def init_admin():
    """Route temporaire pour créer le compte admin de test."""
    if Utilisateur.query.filter_by(email='admin@sinistrai.com').first():
        return "Compte admin déjà existant."

    password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
    admin = Utilisateur(
        nom='Administrateur',
        email='admin@sinistrai.com',
        password_hash=password_hash,
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()
    return "✅ Compte admin créé : admin@sinistrai.com / admin123"