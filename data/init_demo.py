"""
Script de peuplement de la base de données pour la démonstration.
Lance ce script avant la soutenance pour avoir des dossiers prêts.

Usage : python data/init_demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Utilisateur, Dossier, Document, ResultatAnalyse, Log
from app.services.rules_engine import verifier_regles
from app.services.anomaly_detector import scorer_dossier
from datetime import datetime
import bcrypt
import json

app = create_app()

# ─── Dossiers de démonstration ────────────────────────────────────────────────
DOSSIERS_DEMO = [
    {
        "reference": "DEMO-2026-001",
        "label":     "Dossier normal — Consultation généraliste",
        "ocr_data": {
            "montant":        8500.0,
            "date":           "2026-01-15",
            "beneficiaire":   "Jean Dupont",
            "code_acte":      "CONS001",
            "plafond_acte":   15000,
            "assure_id":      "ASS0001",
            "date_adhesion":  "2023-01-01",
            "prescripteur_id": "MED0001",
            "texte_brut":     "Consultation généraliste — Patient : Jean Dupont — Montant : 8500 FCFA — Date : 15/01/2026"
        }
    },
    {
        "reference": "DEMO-2026-002",
        "label":     "Anomalie R01 — Surfacturation chirurgie",
        "ocr_data": {
            "montant":        280000.0,
            "date":           "2026-02-10",
            "beneficiaire":   "Marie Koné",
            "code_acte":      "CHIR001",
            "plafond_acte":   150000,
            "assure_id":      "ASS0002",
            "date_adhesion":  "2022-06-01",
            "prescripteur_id": "MED0012",
            "texte_brut":     "Chirurgie mineure — Patient : Marie Koné — Montant : 280000 FCFA — Date : 10/02/2026"
        }
    },
    {
        "reference": "DEMO-2026-003",
        "label":     "Anomalie R02 — Soin avant adhésion",
        "ocr_data": {
            "montant":        12000.0,
            "date":           "2021-03-05",
            "beneficiaire":   "Kofi Mensah",
            "code_acte":      "LABO001",
            "plafond_acte":   20000,
            "assure_id":      "ASS0003",
            "date_adhesion":  "2022-01-01",
            "prescripteur_id": "MED0007",
            "texte_brut":     "Analyse biologique — Patient : Kofi Mensah — Montant : 12000 FCFA — Date : 05/03/2021"
        }
    },
    {
        "reference": "DEMO-2026-004",
        "label":     "Anomalie R05 — Acte non couvert",
        "ocr_data": {
            "montant":        35000.0,
            "date":           "2026-03-20",
            "beneficiaire":   "Ama Sow",
            "code_acte":      "DENT001",
            "plafond_acte":   0,
            "assure_id":      "ASS0004",
            "date_adhesion":  "2021-09-15",
            "prescripteur_id": "FANTOME_999",
            "texte_brut":     "Soins dentaires — Patient : Ama Sow — Montant : 35000 FCFA — Date : 20/03/2026"
        }
    },
    {
        "reference": "DEMO-2026-005",
        "label":     "Dossier limite — Score IF élevé",
        "ocr_data": {
            "montant":        22000.0,
            "date":           "2026-04-01",
            "beneficiaire":   "Paul Diallo",
            "code_acte":      "CONS002",
            "plafond_acte":   25000,
            "assure_id":      "ASS0005",
            "date_adhesion":  "2020-03-10",
            "prescripteur_id": "MED0033",
            "texte_brut":     "Consultation spécialiste — Patient : Paul Diallo — Montant : 22000 FCFA — Date : 01/04/2026"
        }
    },
]


def peupler_demo():
    with app.app_context():
        print("⏳ Initialisation de la démo SinistrAI...\n")

        # Récupère l'admin
        admin = Utilisateur.query.filter_by(email='admin@sinistrai.com').first()
        if not admin:
            print("❌ Compte admin introuvable. Lancez d'abord python run.py")
            return

        # Supprime les anciens dossiers demo
        for ref in [d["reference"] for d in DOSSIERS_DEMO]:
            existant = Dossier.query.filter_by(reference=ref).first()
            if existant:
                db.session.delete(existant)
        db.session.commit()

        # Crée les dossiers demo
        for d in DOSSIERS_DEMO:
            print(f"  📁 Création : {d['reference']} — {d['label']}")

            # Dossier
            dossier = Dossier(
                reference=d["reference"],
                statut='EN_ATTENTE',
                created_by=admin.id
            )
            db.session.add(dossier)
            db.session.flush()  # Pour obtenir l'id avant le commit

            # Document simulé
            doc = Document(
                dossier_id=dossier.id,
                chemin_fichier=f"demo/{d['reference']}.pdf",
                ocr_data=json.dumps(d["ocr_data"], ensure_ascii=False)
            )
            db.session.add(doc)
            db.session.flush()

            # Analyse règles métiers
            resultat = verifier_regles(d["ocr_data"], dossier.id)

            # Score Isolation Forest
            scoring  = scorer_dossier(d["ocr_data"])
            score_if = scoring["score"]

            # Résultat d'analyse
            analyse = ResultatAnalyse(
                dossier_id=dossier.id,
                regles_violees=json.dumps(resultat, ensure_ascii=False),
                score_if=score_if
            )
            db.session.add(analyse)

            # Mise à jour du dossier
            dossier.statut         = resultat["statut"]
            dossier.score_anomalie = float(score_if)
            dossier.date_mise_a_jour = datetime.utcnow()

            regles = resultat["regles_violees"]
            print(f"     Statut  : {dossier.statut}")
            print(f"     Score IF: {round(score_if, 2)}")
            print(f"     Règles  : {regles if regles else 'Aucune violation'}\n")

        db.session.commit()
        print("✅ Base de démo initialisée avec succès !")
        print("   Connectez-vous sur http://127.0.0.1:5000/login")
        print("   Email    : admin@sinistrai.com")
        print("   Password : admin123")


if __name__ == "__main__":
    peupler_demo()