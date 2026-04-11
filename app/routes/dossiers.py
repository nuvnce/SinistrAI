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
from app.services.anomaly_detector import scorer_dossier
from app.services.logger import log_action

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

    # ── Statistiques générales ────────────────────────────────────────────────
    total      = Dossier.query.filter_by(created_by=current_user.id).count()
    en_attente = Dossier.query.filter_by(created_by=current_user.id, statut='EN_ATTENTE').count()
    valide     = Dossier.query.filter_by(created_by=current_user.id, statut='VALIDE').count()
    anomalie   = Dossier.query.filter_by(created_by=current_user.id, statut='ANOMALIE').count()
    rejete     = Dossier.query.filter_by(created_by=current_user.id, statut='REJETE').count()

    stats = {
        'total': total, 'en_attente': en_attente,
        'valide': valide, 'anomalie': anomalie, 'rejete': rejete,
        'taux_anomalie': round(anomalie / total * 100, 1) if total > 0 else 0,
    }

    # ── Données pour graphiques ───────────────────────────────────────────────
    # Évolution des dossiers par mois
    from sqlalchemy import func, extract
    evolution = db.session.query(
        extract('month', Dossier.date_creation).label('mois'),
        func.count(Dossier.id).label('nb')
    ).filter_by(created_by=current_user.id)\
     .group_by('mois').order_by('mois').all()

    mois_labels = ['Jan','Fév','Mar','Avr','Mai','Jun',
                   'Jul','Aoû','Sep','Oct','Nov','Déc']
    evolution_data = [0] * 12
    for row in evolution:
        evolution_data[int(row.mois) - 1] = row.nb

    # Scores d'anomalie des 10 derniers dossiers analysés
    derniers = Dossier.query.filter(
        Dossier.created_by == current_user.id,
        Dossier.score_anomalie != None
    ).order_by(Dossier.date_creation.desc()).limit(10).all()

    scores_labels = [d.reference for d in reversed(derniers)]
    scores_data   = [round(d.score_anomalie, 2) for d in reversed(derniers)]

    # ── Métriques de performance OCR ─────────────────────────────────────────
    tous_docs = Document.query.join(Dossier)\
                .filter(Dossier.created_by == current_user.id).all()

    nb_docs        = len(tous_docs)
    nb_montant_ok  = 0
    nb_date_ok     = 0
    nb_benef_ok    = 0

    for doc in tous_docs:
        if doc.ocr_data:
            try:
                data = json.loads(doc.ocr_data)
                if data.get("montant"):    nb_montant_ok += 1
                if data.get("date"):       nb_date_ok    += 1
                if data.get("beneficiaire"): nb_benef_ok += 1
            except Exception:
                pass

    perf_ocr = {
        'nb_docs':    nb_docs,
        'montant':    round(nb_montant_ok / nb_docs * 100, 1) if nb_docs > 0 else 0,
        'date':       round(nb_date_ok    / nb_docs * 100, 1) if nb_docs > 0 else 0,
        'beneficiaire': round(nb_benef_ok / nb_docs * 100, 1) if nb_docs > 0 else 0,
    }

    return render_template(
        'dashboard.html',
        dossiers=dossiers,
        stats=stats,
        evolution_labels=mois_labels,
        evolution_data=evolution_data,
        scores_labels=scores_labels,
        scores_data=scores_data,
        perf_ocr=perf_ocr,
    )


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
        log_action("CREATION_DOSSIER", f"Dossier {dossier.reference} créé", user_id=current_user.id)
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
        log_action("MAJ_STATUT", f"Dossier #{id} → {nouveau_statut}", user_id=current_user.id)
        flash('Statut mis à jour avec succès.', 'success')
    else:
        flash('Statut invalide.', 'danger')
    return redirect(url_for('dossiers.detail', id=id))


@bp.route('/dossiers/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer(id):
    dossier = Dossier.query.get_or_404(id)
    ref     = dossier.reference
    log_action("SUPPRESSION_DOSSIER", f"Dossier {ref} supprimé", user_id=current_user.id)
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
    log_action("UPLOAD_DOCUMENT", f"Document uploadé sur dossier {dossier.reference}", user_id=current_user.id)

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
    resultat = verifier_regles(ocr_data, dossier.id)

    # ── Score Isolation Forest ────────────────────────────────────────────────────
    scoring = scorer_dossier(ocr_data)
    score_if = scoring["score"]

    analyse = ResultatAnalyse(
        dossier_id=dossier.id,
        regles_violees=json.dumps(resultat, ensure_ascii=False),
        score_if=score_if
    )
    db.session.add(analyse)
    dossier.statut = resultat["statut"]
    dossier.score_anomalie = score_if
    dossier.date_mise_a_jour = datetime.utcnow()
    db.session.commit()
    log_action(
        "ANALYSE_DOSSIER",
        f"Dossier {dossier.reference} analysé — statut={resultat['statut']} score={round(score_if, 2)}",
        user_id=current_user.id
    )

    if resultat["regles_violees"]:
        flash(
            f'⚠️ {resultat["nb_violations"]} règle(s) violée(s) : '
            f'{", ".join(resultat["regles_violees"])}',
            'danger'
        )
    else:
        flash('✅ Dossier conforme — aucune anomalie détectée.', 'success')

    return redirect(url_for('dossiers.detail', id=id))

@bp.route('/dossiers')
@login_required
def liste():
    dossiers = Dossier.query.filter_by(created_by=current_user.id)\
                            .order_by(Dossier.date_creation.desc()).all()
    stats = {
        'total':      Dossier.query.filter_by(created_by=current_user.id).count(),
        'en_attente': Dossier.query.filter_by(created_by=current_user.id, statut='EN_ATTENTE').count(),
        'valide':     Dossier.query.filter_by(created_by=current_user.id, statut='VALIDE').count(),
        'anomalie':   Dossier.query.filter_by(created_by=current_user.id, statut='ANOMALIE').count(),
    }
    return render_template('dossiers/liste.html', dossiers=dossiers, stats=stats)


@bp.route('/analytics')
@login_required
def analytics():
    from sqlalchemy import func, extract
    total      = Dossier.query.filter_by(created_by=current_user.id).count()
    en_attente = Dossier.query.filter_by(created_by=current_user.id, statut='EN_ATTENTE').count()
    valide     = Dossier.query.filter_by(created_by=current_user.id, statut='VALIDE').count()
    anomalie   = Dossier.query.filter_by(created_by=current_user.id, statut='ANOMALIE').count()
    rejete     = Dossier.query.filter_by(created_by=current_user.id, statut='REJETE').count()

    stats = {
        'total': total, 'en_attente': en_attente,
        'valide': valide, 'anomalie': anomalie, 'rejete': rejete,
        'taux_anomalie': round(anomalie / total * 100, 1) if total > 0 else 0,
    }

    evolution = db.session.query(
        extract('month', Dossier.date_creation).label('mois'),
        func.count(Dossier.id).label('nb')
    ).filter_by(created_by=current_user.id)\
     .group_by('mois').order_by('mois').all()

    mois_labels    = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc']
    evolution_data = [0] * 12
    for row in evolution:
        evolution_data[int(row.mois) - 1] = row.nb

    derniers = Dossier.query.filter(
        Dossier.created_by == current_user.id,
        Dossier.score_anomalie != None
    ).order_by(Dossier.date_creation.desc()).limit(10).all()

    scores_labels = [d.reference for d in reversed(derniers)]
    scores_data   = [round(d.score_anomalie, 2) for d in reversed(derniers)]

    tous_docs = Document.query.join(Dossier)\
                .filter(Dossier.created_by == current_user.id).all()
    nb_docs       = len(tous_docs)
    nb_montant_ok = nb_date_ok = nb_benef_ok = 0
    for doc in tous_docs:
        if doc.ocr_data:
            try:
                data = json.loads(doc.ocr_data)
                if data.get("montant"):      nb_montant_ok += 1
                if data.get("date"):         nb_date_ok    += 1
                if data.get("beneficiaire"): nb_benef_ok   += 1
            except Exception:
                pass

    perf_ocr = {
        'nb_docs':      nb_docs,
        'montant':      round(nb_montant_ok / nb_docs * 100, 1) if nb_docs > 0 else 0,
        'date':         round(nb_date_ok    / nb_docs * 100, 1) if nb_docs > 0 else 0,
        'beneficiaire': round(nb_benef_ok   / nb_docs * 100, 1) if nb_docs > 0 else 0,
    }

    return render_template('analytics.html',
        stats=stats,
        evolution_labels=mois_labels,
        evolution_data=evolution_data,
        scores_labels=scores_labels,
        scores_data=scores_data,
        perf_ocr=perf_ocr,
    )


@bp.route('/apropos')
@login_required
def apropos():
    return render_template('apropos.html')