import joblib
import os
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

# Chargement du modèle et des encodeurs au démarrage
model          = joblib.load(os.path.join(DATA_DIR, 'isolation_forest.pkl'))
le_acte        = joblib.load(os.path.join(DATA_DIR, 'le_acte.pkl'))
le_prescripteur = joblib.load(os.path.join(DATA_DIR, 'le_prescripteur.pkl'))
le_assure      = joblib.load(os.path.join(DATA_DIR, 'le_assure.pkl'))
FEATURES       = joblib.load(os.path.join(DATA_DIR, 'features.pkl'))

ACTES_PLAFONDS = {
    "CONS001": 15000,  "CONS002": 25000,  "RADIO001": 30000,
    "LABO001": 20000,  "CHIR001": 150000, "HOSP001": 300000,
    "PHARMA001": 10000, "KINE001": 12000,
}


def encoder_valeur(encodeur, valeur):
    """Encode une valeur en gérant les catégories inconnues."""
    try:
        return encodeur.transform([str(valeur)])[0]
    except ValueError:
        return -1


def scorer_dossier(ocr_data: dict, freq_assure: int = 1) -> dict:
    """
    Calcule le score d'anomalie d'un dossier à partir des données OCR.
    Retourne un score normalisé entre 0 et 1 (1 = très anormal).
    """
    try:
        montant      = float(ocr_data.get("montant") or 0)
        code_acte    = str(ocr_data.get("code_acte") or "INCONNU")
        prescripteur = str(ocr_data.get("prescripteur_id") or "INCONNU")
        assure_id    = str(ocr_data.get("assure_id") or "INCONNU")
        date_str     = ocr_data.get("date") or ""
        date_adhesion = ocr_data.get("date_adhesion") or ""

        plafond      = ACTES_PLAFONDS.get(code_acte, 0)
        ratio_montant = montant / plafond if plafond > 0 else 0

        # Calcul des délais
        delai_depot  = 7    # valeur par défaut
        anteriorite  = 365  # valeur par défaut

        if date_str:
            from datetime import datetime
            try:
                date_soin = datetime.strptime(date_str, "%Y-%m-%d")
                delai_depot = (datetime.utcnow() - date_soin).days
                if date_adhesion:
                    d_adh = datetime.strptime(date_adhesion, "%Y-%m-%d")
                    anteriorite = (date_soin - d_adh).days
            except ValueError:
                pass

        # Encodage
        code_acte_enc    = encoder_valeur(le_acte, code_acte)
        prescripteur_enc = encoder_valeur(le_prescripteur, prescripteur)
        assure_enc       = encoder_valeur(le_assure, assure_id)

        # Construction du vecteur de features
        X = [[
            montant,
            plafond,
            ratio_montant,
            delai_depot,
            anteriorite,
            freq_assure,
            code_acte_enc,
            prescripteur_enc,
            assure_enc,
        ]]

        # Score brut du modèle
        score_brut = model.decision_function(X)[0]
        prediction = model.predict(X)[0]   # -1 = anomalie, 1 = normal

        # Normalisation approximative entre 0 et 1
        score_normalise = max(0.0, min(1.0, 0.5 - score_brut))

        return {
            "score":      round(score_normalise, 4),
            "prediction": "ANOMALIE" if prediction == -1 else "NORMAL",
            "succes":     True
        }

    except Exception as e:
        return {"score": 0.0, "prediction": "INCONNU", "succes": False, "erreur": str(e)}