from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Dossier
from datetime import datetime
import random
import string

bp = Blueprint('dossiers', __name__)


def generer_reference():
    """Génère une référence unique de dossier."""
    annee = datetime.now().year
    suffixe = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SIN-{annee}-{suffixe}"


@bp.route('/dashboard')
@login_required
def index():
    dossiers = Dossier.query.filter_by(created_by=current_user.id)\
                            .order_by(Dossier.date_creation.desc()).all()
    stats = {
        'total':      Dossier.query.filter_by(created_by=current_user.id).count(),
        'en_attente': Dossier.query.filter_by(created_by=current_user.id, statut='EN_ATTENTE').count(),
        'valide':     Dossier.query.filter_by(created_by=current_user.id, statut='VALIDE').count(),
        'anomalie':   Dossier.query.filter_by(created_by=current_user.id, statut='ANOMALIE').count(),
    }
    return render_template('dashboard.html', dossiers=dossiers, stats=stats)


@bp.route('/dossiers/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau():
    if request.method == 'POST':
        dossier = Dossier(
            reference=generer_reference(),
            statut='EN_ATTENTE',
            created_by=current_user.id
        )
        db.session.add(dossier)
        db.session.commit()
        flash(f'Dossier {dossier.reference} créé avec succès.', 'success')
        return redirect(url_for('dossiers.detail', id=dossier.id))

    return render_template('dossiers/nouveau.html')


@bp.route('/dossiers/<int:id>')
@login_required
def detail(id):
    dossier = Dossier.query.get_or_404(id)
    return render_template('dossiers/detail.html', dossier=dossier)


@bp.route('/dossiers/<int:id>/statut', methods=['POST'])
@login_required
def update_statut(id):
    dossier = Dossier.query.get_or_404(id)
    nouveau_statut = request.form.get('statut')
    statuts_valides = ['EN_ATTENTE', 'VALIDE', 'ANOMALIE', 'REJETE']

    if nouveau_statut in statuts_valides:
        dossier.statut = nouveau_statut
        dossier.date_mise_a_jour = datetime.utcnow()
        db.session.commit()
        flash('Statut mis à jour avec succès.', 'success')
    else:
        flash('Statut invalide.', 'danger')

    return redirect(url_for('dossiers.detail', id=id))


@bp.route('/dossiers/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer(id):
    dossier = Dossier.query.get_or_404(id)
    db.session.delete(dossier)
    db.session.commit()
    flash(f'Dossier {dossier.reference} supprimé.', 'warning')
    return redirect(url_for('dossiers.index'))