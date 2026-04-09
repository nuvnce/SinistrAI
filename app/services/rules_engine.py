from datetime import datetime, timedelta
from app.models import Dossier, Document, ResultatAnalyse
import json

# ─── Référentiel des actes médicaux couverts ─────────────────────────────────
ACTES_COUVERTS = {
    "CONS001": {"libelle": "Consultation généraliste",  "plafond": 15000},
    "CONS002": {"libelle": "Consultation spécialiste",  "plafond": 25000},
    "RADIO001": {"libelle": "Radiographie",             "plafond": 30000},
    "LABO001":  {"libelle": "Analyse biologique",       "plafond": 20000},
    "CHIR001":  {"libelle": "Chirurgie mineure",        "plafond": 150000},
    "HOSP001":  {"libelle": "Hospitalisation",          "plafond": 300000},
    "PHARMA001":{"libelle": "Médicaments ordonnance",   "plafond": 10000},
    "KINE001":  {"libelle": "Kinésithérapie",           "plafond": 12000},
}

PRESCRIPTEURS_VALIDES = [f"MED{str(i).zfill(4)}" for i in range(1, 51)]


def verifier_regles(ocr_data: dict, dossier_id: int) -> dict:
    """
    Applique les 5 règles métiers sur les données OCR d'un dossier.
    Retourne un dictionnaire avec les règles violées et le statut final.
    """
    regles_violees = []
    details        = {}

    montant       = ocr_data.get("montant")
    date_str      = ocr_data.get("date")
    code_acte     = ocr_data.get("code_acte")
    prescripteur  = ocr_data.get("prescripteur_id")
    assure_id     = ocr_data.get("assure_id")
    date_adhesion = ocr_data.get("date_adhesion")

    # ── R01 : Plafond de remboursement ────────────────────────────────────────
    if montant and code_acte and code_acte in ACTES_COUVERTS:
        plafond = ACTES_COUVERTS[code_acte]["plafond"]
        if float(montant) > plafond:
            regles_violees.append("R01")
            details["R01"] = (
                f"Montant réclamé ({montant} FCFA) "
                f"dépasse le plafond autorisé ({plafond} FCFA) "
                f"pour l'acte {code_acte}."
            )

    # ── R02 : Cohérence des dates ─────────────────────────────────────────────
    if date_str:
        try:
            date_soin  = datetime.strptime(date_str, "%Y-%m-%d")
            date_depot = datetime.utcnow()
            if date_soin > date_depot:
                regles_violees.append("R02")
                details["R02"] = (
                    f"La date de soin ({date_str}) "
                    f"est postérieure à la date de dépôt du dossier."
                )
        except ValueError:
            pass

    # ── R02b : Date de soin avant date d'adhésion ─────────────────────────────
    if date_str and date_adhesion:
        try:
            date_soin = datetime.strptime(date_str, "%Y-%m-%d")
            d_adhesion = datetime.strptime(date_adhesion, "%Y-%m-%d")
            if date_soin < d_adhesion:
                if "R02" not in regles_violees:
                    regles_violees.append("R02")
                details["R02"] = (
                    f"La date de soin ({date_str}) est antérieure "
                    f"à la date d'adhésion ({date_adhesion})."
                )
        except ValueError:
            pass

    # ── R03 : Doublon de dossier ──────────────────────────────────────────────
    if assure_id and date_str and code_acte:
        from app import db
        # Cherche un dossier similaire (même assuré, même acte, même date)
        # dans les documents déjà en base, hors dossier courant
        docs_existants = Document.query.filter(
            Document.dossier_id != dossier_id
        ).all()

        for doc in docs_existants:
            if doc.ocr_data:
                try:
                    data = json.loads(doc.ocr_data)
                    if (data.get("assure_id") == assure_id and
                            data.get("code_acte") == code_acte and
                            data.get("date") == date_str):
                        regles_violees.append("R03")
                        details["R03"] = (
                            f"Dossier potentiellement en doublon avec "
                            f"le document #{doc.id} "
                            f"(même assuré, même acte, même date)."
                        )
                        break
                except (json.JSONDecodeError, AttributeError):
                    continue

    # ── R04 : Fréquence anormale ──────────────────────────────────────────────
    if assure_id and date_str:
        try:
            date_soin   = datetime.strptime(date_str, "%Y-%m-%d")
            debut_periode = date_soin - timedelta(days=30)
            docs_periode  = Document.query.filter(
                Document.dossier_id != dossier_id
            ).all()

            count = 0
            for doc in docs_periode:
                if doc.ocr_data:
                    try:
                        data = json.loads(doc.ocr_data)
                        if data.get("assure_id") == assure_id and data.get("date"):
                            d = datetime.strptime(data["date"], "%Y-%m-%d")
                            if debut_periode <= d <= date_soin:
                                count += 1
                    except (ValueError, json.JSONDecodeError):
                        continue

            if count >= 5:
                regles_violees.append("R04")
                details["R04"] = (
                    f"L'assuré {assure_id} a soumis {count} dossiers "
                    f"dans les 30 derniers jours (seuil : 5)."
                )
        except ValueError:
            pass

    # ── R05 : Acte non couvert ────────────────────────────────────────────────
    if code_acte and code_acte not in ACTES_COUVERTS:
        regles_violees.append("R05")
        details["R05"] = (
            f"L'acte médical '{code_acte}' "
            f"est absent du référentiel des actes couverts."
        )

    # ── Détermination du statut final ─────────────────────────────────────────
    if regles_violees:
        statut = "ANOMALIE"
    else:
        statut = "VALIDE"

    return {
        "regles_violees": regles_violees,
        "details":        details,
        "statut":         statut,
        "nb_violations":  len(regles_violees),
    }