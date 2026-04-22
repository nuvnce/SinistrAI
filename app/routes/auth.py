from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Utilisateur
from app.services.logger import log_action
import bcrypt

bp = Blueprint('auth', __name__)


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        user     = Utilisateur.query.filter_by(email=email).first()

        hash_bytes = user.password_hash if isinstance(user.password_hash, bytes) else user.password_hash.encode('utf-8')
        if user and bcrypt.checkpw(password.encode('utf-8'), hash_bytes):
            login_user(user)
            log_action("CONNEXION", "Connexion réussie", user_id=user.id)
            return redirect(url_for('auth.splash'))
        else:
            flash('Email ou mot de passe incorrect.', 'danger')

    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    log_action("DECONNEXION", "Déconnexion", user_id=current_user.id)
    logout_user()
    return redirect(url_for('auth.login'))


@bp.route('/splash')
@login_required
def splash():
    return render_template('splash.html', user=current_user)