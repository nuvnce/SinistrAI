from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Dossier, Document, ResultatAnalyse
from app.services.ocr_service import analyser_document
from app.services.rules_engine import verifier_regles
from datetime import datetime
import random
import string
import json
import os

bp = Blueprint('dossiers', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


def generer_reference():
    annee   = datetime.now().year
    suffixe = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SIN-{annee}-{suffixe}"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    dossier         = Dossier.query.get_or_404(id)
    nouveau_statut  = request.form.get('statut')
    statuts_valides = ['EN_ATTENTE', 'VALIDE', 'ANOMALIE', 'REJETE']
    if nouveau_statut in statuts_valides:
        dossier.statut           = nouveau_statut
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
    ref     = dossier.reference
    db.session.delete(dossier)
    db.session.commit()
    flash(f'Dossier {ref} supprimé.', 'warning')
    return redirect(url_for('dossiers.index'))


@bp.route('/dossiers/<int:id>/upload', methods=['POST'])
@login_required
def upload_document(id):
    dossier = Dossier.query.get_or_404(id)

    if 'fichier' not in request.files:
        flash('Aucun fichier sélectionné.', 'danger')
        return redirect(url_for('dossiers.detail', id=id))

    fichier = request.files['fichier']
    if fichier.filename == '' or not allowed_file(fichier.filename):
        flash('Fichier invalide. Formats acceptés : PDF, PNG, JPG.', 'danger')
        return redirect(url_for('dossiers.detail', id=id))

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(fichier.filename)
    chemin   = os.path.join(upload_folder, filename)
    fichier.save(chemin)

    flash('⏳ Analyse OCR en cours...', 'info')
    resultat = analyser_document(chemin)

    doc = Document(
        dossier_id=dossier.id,
        chemin_fichier=chemin,
        ocr_data=json.dumps(resultat["champs"], ensure_ascii=False)
    )
    db.session.add(doc)
    db.session.commit()

    if resultat["succes"]:
        flash('✅ Document analysé avec succès.', 'success')
    else:
        flash(f'⚠️ OCR partiel : {resultat.get("erreur", "erreur inconnue")}', 'warning')

    return redirect(url_for('dossiers.detail', id=id))


@bp.route('/dossiers/<int:id>/analyser', methods=['POST'])
@login_required
def analyser(id):
    dossier = Dossier.query.get_or_404(id)

    if not dossier.documents:
        flash('Veuillez d\'abord importer un document.', 'warning')
        return redirect(url_for('dossiers.detail', id=id))

    dernier_doc = dossier.documents[-1]
    ocr_data    = json.loads(dernier_doc.ocr_data) if dernier_doc.ocr_data else {}
    resultat    = verifier_regles(ocr_data, dossier.id)

    analyse = ResultatAnalyse(
        dossier_id=dossier.id,
        regles_violees=json.dumps(resultat, ensure_ascii=False)
    )
    db.session.add(analyse)
    dossier.statut           = resultat["statut"]
    dossier.date_mise_a_jour = datetime.utcnow()
    db.session.commit()

    if resultat["regles_violees"]:
        flash(
            f'⚠️ {resultat["nb_violations"]} règle(s) violée(s) : '
            f'{", ".join(resultat["regles_violees"])}',
            'danger'
        )
    else:
        flash('✅ Dossier conforme — aucune anomalie détectée.', 'success')

    return redirect(url_for('dossiers.detail', id=id))