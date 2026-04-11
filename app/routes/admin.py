from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Utilisateur
from app.services.logger import log_action
import bcrypt

bp = Blueprint('admin', __name__)


def admin_required(f):
    """Décorateur qui vérifie que l'utilisateur est admin."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('dossiers.index'))
        return f(*args, **kwargs)
    return decorated


@bp.route('/admin/utilisateurs')
@login_required
@admin_required
def utilisateurs():
    users = Utilisateur.query.order_by(Utilisateur.date_creation.desc()).all()
    return render_template('admin/utilisateurs.html', users=users)


@bp.route('/admin/utilisateurs/creer', methods=['POST'])
@login_required
@admin_required
def creer_utilisateur():
    nom      = request.form.get('nom', '').strip()
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    role     = request.form.get('role', 'gestionnaire')

    if not nom or not email or not password:
        flash('Tous les champs sont obligatoires.', 'danger')
        return redirect(url_for('admin.utilisateurs'))

    if Utilisateur.query.filter_by(email=email).first():
        flash('Un compte avec cet email existe déjà.', 'danger')
        return redirect(url_for('admin.utilisateurs'))

    if len(password) < 6:
        flash('Le mot de passe doit contenir au moins 6 caractères.', 'danger')
        return redirect(url_for('admin.utilisateurs'))

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = Utilisateur(nom=nom, email=email, password_hash=password_hash, role=role)
    db.session.add(user)
    db.session.commit()

    log_action("CREATION_UTILISATEUR", f"Compte créé : {email} ({role})", user_id=current_user.id)
    flash(f'Compte de {nom} créé avec succès.', 'success')
    return redirect(url_for('admin.utilisateurs'))


@bp.route('/admin/utilisateurs/<int:id>/modifier', methods=['POST'])
@login_required
@admin_required
def modifier_utilisateur(id):
    user     = Utilisateur.query.get_or_404(id)
    nom      = request.form.get('nom', '').strip()
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    role     = request.form.get('role', 'gestionnaire')

    if not nom or not email:
        flash('Le nom et l\'email sont obligatoires.', 'danger')
        return redirect(url_for('admin.utilisateurs'))

    # Vérifier doublon email
    existant = Utilisateur.query.filter_by(email=email).first()
    if existant and existant.id != id:
        flash('Cet email est déjà utilisé par un autre compte.', 'danger')
        return redirect(url_for('admin.utilisateurs'))

    user.nom   = nom
    user.email = email
    user.role  = role

    if password:
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'danger')
            return redirect(url_for('admin.utilisateurs'))
        user.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    db.session.commit()
    log_action("MODIFICATION_UTILISATEUR", f"Compte modifié : {email}", user_id=current_user.id)
    flash(f'Compte de {nom} mis à jour.', 'success')
    return redirect(url_for('admin.utilisateurs'))


@bp.route('/admin/utilisateurs/<int:id>/supprimer', methods=['POST'])
@login_required
@admin_required
def supprimer_utilisateur(id):
    user = Utilisateur.query.get_or_404(id)

    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('admin.utilisateurs'))

    nom = user.nom
    db.session.delete(user)
    db.session.commit()

    log_action("SUPPRESSION_UTILISATEUR", f"Compte supprimé : {user.email}", user_id=current_user.id)
    flash(f'Compte de {nom} supprimé.', 'warning')
    return redirect(url_for('admin.utilisateurs'))