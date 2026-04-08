import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# ─── Configuration ────────────────────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

NB_DOSSIERS    = 500
TAUX_ANOMALIES = 0.20   # 20% de dossiers anormaux

# ─── Référentiels simulés ─────────────────────────────────────────────────────
ACTES_MEDICAUX = {
    "CONS001": {"libelle": "Consultation généraliste",  "plafond": 15000},
    "CONS002": {"libelle": "Consultation spécialiste",  "plafond": 25000},
    "RADIO001": {"libelle": "Radiographie",             "plafond": 30000},
    "LABO001": {"libelle": "Analyse biologique",        "plafond": 20000},
    "CHIR001": {"libelle": "Chirurgie mineure",         "plafond": 150000},
    "HOSP001": {"libelle": "Hospitalisation",           "plafond": 300000},
    "PHARMA001": {"libelle": "Médicaments ordonnance",  "plafond": 10000},
    "KINE001": {"libelle": "Kinésithérapie",            "plafond": 12000},
}

ACTE_NON_COUVERT = "DENT001"   # acte absent du référentiel

PRESCRIPTEURS = [f"MED{str(i).zfill(4)}" for i in range(1, 51)]

ASSURES = [
    {"id": f"ASS{str(i).zfill(4)}",
     "nom": f"Assuré_{i}",
     "date_adhesion": datetime(2022, 1, 1) + timedelta(days=random.randint(0, 365))}
    for i in range(1, 101)
]


# ─── Fonctions utilitaires ────────────────────────────────────────────────────

def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def generer_reference(index):
    return f"SIN-2024-{str(index).zfill(4)}"


# ─── Générateurs de dossiers ──────────────────────────────────────────────────

def dossier_normal(index):
    """Génère un dossier sans anomalie."""
    assure      = random.choice(ASSURES)
    code_acte   = random.choice(list(ACTES_MEDICAUX.keys()))
    acte        = ACTES_MEDICAUX[code_acte]
    date_soin   = random_date(datetime(2024, 1, 1), datetime(2024, 11, 30))
    date_depot  = date_soin + timedelta(days=random.randint(1, 30))
    montant     = round(random.uniform(acte["plafond"] * 0.3, acte["plafond"] * 0.9), 2)
    prescripteur = random.choice(PRESCRIPTEURS)

    return {
        "reference":        generer_reference(index),
        "assure_id":        assure["id"],
        "assure_nom":       assure["nom"],
        "date_adhesion":    assure["date_adhesion"].strftime("%Y-%m-%d"),
        "code_acte":        code_acte,
        "libelle_acte":     acte["libelle"],
        "plafond_acte":     acte["plafond"],
        "montant_reclame":  montant,
        "date_soin":        date_soin.strftime("%Y-%m-%d"),
        "date_depot":       date_depot.strftime("%Y-%m-%d"),
        "prescripteur_id":  prescripteur,
        "anomalie":         0,
        "type_anomalie":    "NORMAL",
    }


def scenario_A(index):
    """Surfacturation : montant > plafond."""
    assure      = random.choice(ASSURES)
    code_acte   = random.choice(list(ACTES_MEDICAUX.keys()))
    acte        = ACTES_MEDICAUX[code_acte]
    date_soin   = random_date(datetime(2024, 1, 1), datetime(2024, 11, 30))
    date_depot  = date_soin + timedelta(days=random.randint(1, 15))
    montant     = round(acte["plafond"] * random.uniform(1.3, 2.5), 2)

    return {
        "reference":        generer_reference(index),
        "assure_id":        assure["id"],
        "assure_nom":       assure["nom"],
        "date_adhesion":    assure["date_adhesion"].strftime("%Y-%m-%d"),
        "code_acte":        code_acte,
        "libelle_acte":     acte["libelle"],
        "plafond_acte":     acte["plafond"],
        "montant_reclame":  montant,
        "date_soin":        date_soin.strftime("%Y-%m-%d"),
        "date_depot":       date_depot.strftime("%Y-%m-%d"),
        "prescripteur_id":  random.choice(PRESCRIPTEURS),
        "anomalie":         1,
        "type_anomalie":    "SURFACTURATION",
    }


def scenario_B(index, dossier_original):
    """Doublon : même assuré, même acte, même date, nom légèrement différent."""
    d = dossier_original.copy()
    d["reference"]    = generer_reference(index)
    d["assure_nom"]   = d["assure_nom"] + "_bis"
    d["date_depot"]   = (
        datetime.strptime(d["date_depot"], "%Y-%m-%d") + timedelta(days=random.randint(1, 3))
    ).strftime("%Y-%m-%d")
    d["anomalie"]     = 1
    d["type_anomalie"] = "DOUBLON"
    return d


def scenario_C(index, assure):
    """Cumul suspect : même assuré, plus de 5 actes sur 30 jours."""
    code_acte  = random.choice(list(ACTES_MEDICAUX.keys()))
    acte       = ACTES_MEDICAUX[code_acte]
    date_soin  = random_date(datetime(2024, 3, 1), datetime(2024, 10, 1))
    date_depot = date_soin + timedelta(days=random.randint(1, 5))
    montant    = round(random.uniform(acte["plafond"] * 0.4, acte["plafond"] * 0.8), 2)

    return {
        "reference":        generer_reference(index),
        "assure_id":        assure["id"],
        "assure_nom":       assure["nom"],
        "date_adhesion":    assure["date_adhesion"].strftime("%Y-%m-%d"),
        "code_acte":        code_acte,
        "libelle_acte":     acte["libelle"],
        "plafond_acte":     acte["plafond"],
        "montant_reclame":  montant,
        "date_soin":        date_soin.strftime("%Y-%m-%d"),
        "date_depot":       date_depot.strftime("%Y-%m-%d"),
        "prescripteur_id":  random.choice(PRESCRIPTEURS),
        "anomalie":         1,
        "type_anomalie":    "CUMUL_SUSPECT",
    }


def scenario_D(index):
    """Incohérence temporelle : date de soin avant date d'adhésion."""
    assure      = random.choice(ASSURES)
    code_acte   = random.choice(list(ACTES_MEDICAUX.keys()))
    acte        = ACTES_MEDICAUX[code_acte]
    date_soin   = assure["date_adhesion"] - timedelta(days=random.randint(10, 180))
    date_depot  = datetime(2024, 6, 1) + timedelta(days=random.randint(0, 90))
    montant     = round(random.uniform(acte["plafond"] * 0.3, acte["plafond"] * 0.8), 2)

    return {
        "reference":        generer_reference(index),
        "assure_id":        assure["id"],
        "assure_nom":       assure["nom"],
        "date_adhesion":    assure["date_adhesion"].strftime("%Y-%m-%d"),
        "code_acte":        code_acte,
        "libelle_acte":     acte["libelle"],
        "plafond_acte":     acte["plafond"],
        "montant_reclame":  montant,
        "date_soin":        date_soin.strftime("%Y-%m-%d"),
        "date_depot":       date_depot.strftime("%Y-%m-%d"),
        "prescripteur_id":  random.choice(PRESCRIPTEURS),
        "anomalie":         1,
        "type_anomalie":    "INCOHERENCE_TEMPORELLE",
    }


def scenario_E(index):
    """Prescripteur fantôme : ID absent du registre."""
    assure      = random.choice(ASSURES)
    code_acte   = random.choice(list(ACTES_MEDICAUX.keys()))
    acte        = ACTES_MEDICAUX[code_acte]
    date_soin   = random_date(datetime(2024, 1, 1), datetime(2024, 11, 30))
    date_depot  = date_soin + timedelta(days=random.randint(1, 20))
    montant     = round(random.uniform(acte["plafond"] * 0.3, acte["plafond"] * 0.85), 2)

    return {
        "reference":        generer_reference(index),
        "assure_id":        assure["id"],
        "assure_nom":       assure["nom"],
        "date_adhesion":    assure["date_adhesion"].strftime("%Y-%m-%d"),
        "code_acte":        ACTE_NON_COUVERT,
        "libelle_acte":     "Acte non référencé",
        "plafond_acte":     0,
        "montant_reclame":  montant,
        "date_soin":        date_soin.strftime("%Y-%m-%d"),
        "date_depot":       date_depot.strftime("%Y-%m-%d"),
        "prescripteur_id":  f"FANTOME_{random.randint(100, 999)}",
        "anomalie":         1,
        "type_anomalie":    "PRESCRIPTEUR_FANTOME",
    }


# ─── Génération principale ────────────────────────────────────────────────────

def generer_dataset():
    dossiers = []
    index    = 1

    nb_anomalies = int(NB_DOSSIERS * TAUX_ANOMALIES)  # 100 anomalies
    nb_normaux   = NB_DOSSIERS - nb_anomalies          # 400 normaux

    # 400 dossiers normaux
    for _ in range(nb_normaux):
        dossiers.append(dossier_normal(index))
        index += 1

    # 20 doublons (scénario B) — on clone 20 dossiers normaux existants
    bases_doublon = random.sample(dossiers[:nb_normaux], 20)
    for base in bases_doublon:
        dossiers.append(scenario_B(index, base))
        index += 1

    # 20 surfacturations (scénario A)
    for _ in range(20):
        dossiers.append(scenario_A(index))
        index += 1

    # 20 cumuls suspects (scénario C) — 4 assurés × 5 dossiers rapprochés
    assures_suspects = random.sample(ASSURES, 4)
    for assure in assures_suspects:
        for _ in range(5):
            dossiers.append(scenario_C(index, assure))
            index += 1

    # 20 incohérences temporelles (scénario D)
    for _ in range(20):
        dossiers.append(scenario_D(index))
        index += 1

    # 20 prescripteurs fantômes (scénario E)
    for _ in range(20):
        dossiers.append(scenario_E(index))
        index += 1

    # Mélanger pour ne pas avoir les anomalies regroupées à la fin
    random.shuffle(dossiers)

    return dossiers


# ─── Export CSV ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("⏳ Génération des données synthétiques...")
    dossiers = generer_dataset()
    df = pd.DataFrame(dossiers)

    output_path = os.path.join(os.path.dirname(__file__), "sinistres_synthetiques.csv")
    df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"✅ {len(df)} dossiers générés → {output_path}")
    print(f"\n📊 Répartition :")
    print(df["type_anomalie"].value_counts().to_string())
    print(f"\nTaux d'anomalies : {df['anomalie'].mean() * 100:.1f}%")