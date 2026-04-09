import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# ─── Chargement des données ───────────────────────────────────────────────────
print("⏳ Chargement des données synthétiques...")
df = pd.read_csv(os.path.join(os.path.dirname(__file__), "sinistres_synthetiques.csv"))
print(f"✅ {len(df)} dossiers chargés.")

# ─── Feature Engineering ──────────────────────────────────────────────────────
print("⏳ Préparation des features...")

# Encodage des variables catégorielles
le_acte        = LabelEncoder()
le_prescripteur = LabelEncoder()
le_assure      = LabelEncoder()

df["code_acte_enc"]       = le_acte.fit_transform(df["code_acte"].astype(str))
df["prescripteur_enc"]    = le_prescripteur.fit_transform(df["prescripteur_id"].astype(str))
df["assure_enc"]          = le_assure.fit_transform(df["assure_id"].astype(str))

# Calcul du ratio montant / plafond
df["ratio_montant"] = df.apply(
    lambda r: r["montant_reclame"] / r["plafond_acte"] if r["plafond_acte"] > 0 else 0,
    axis=1
)

# Conversion des dates
df["date_soin"]  = pd.to_datetime(df["date_soin"])
df["date_depot"] = pd.to_datetime(df["date_depot"])
df["date_adhesion"] = pd.to_datetime(df["date_adhesion"])

# Délai entre soin et dépôt (en jours)
df["delai_depot"] = (df["date_depot"] - df["date_soin"]).dt.days

# Antériorité du soin par rapport à l'adhésion (en jours, négatif = avant adhésion)
df["anteriorite"] = (df["date_soin"] - df["date_adhesion"]).dt.days

# Fréquence de l'assuré (nb de dossiers par assuré)
freq = df.groupby("assure_id")["reference"].count().reset_index()
freq.columns = ["assure_id", "freq_assure"]
df = df.merge(freq, on="assure_id", how="left")

# ─── Sélection des features ───────────────────────────────────────────────────
FEATURES = [
    "montant_reclame",
    "plafond_acte",
    "ratio_montant",
    "delai_depot",
    "anteriorite",
    "freq_assure",
    "code_acte_enc",
    "prescripteur_enc",
    "assure_enc",
]

X = df[FEATURES].fillna(0)

# ─── Entraînement du modèle ───────────────────────────────────────────────────
print("⏳ Entraînement du modèle Isolation Forest...")

model = IsolationForest(
    n_estimators=200,
    contamination=0.20,   # 20% d'anomalies attendues
    random_state=42,
    max_samples="auto"
)
model.fit(X)

# Scores de décision (plus négatif = plus anormal)
df["score_if"]    = model.decision_function(X)
df["prediction"]  = model.predict(X)   # -1 = anomalie, 1 = normal

# Normalisation du score entre 0 et 1 (1 = très anormal)
score_min = df["score_if"].min()
score_max = df["score_if"].max()
df["score_normalise"] = 1 - (df["score_if"] - score_min) / (score_max - score_min)

# ─── Évaluation rapide ────────────────────────────────────────────────────────
print("\n📊 Évaluation du modèle :")
vrais_positifs  = ((df["prediction"] == -1) & (df["anomalie"] == 1)).sum()
faux_positifs   = ((df["prediction"] == -1) & (df["anomalie"] == 0)).sum()
faux_negatifs   = ((df["prediction"] == 1)  & (df["anomalie"] == 1)).sum()
vrais_negatifs  = ((df["prediction"] == 1)  & (df["anomalie"] == 0)).sum()

precision = vrais_positifs / (vrais_positifs + faux_positifs) if (vrais_positifs + faux_positifs) > 0 else 0
rappel    = vrais_positifs / (vrais_positifs + faux_negatifs) if (vrais_positifs + faux_negatifs) > 0 else 0
f1        = 2 * precision * rappel / (precision + rappel) if (precision + rappel) > 0 else 0

print(f"  Vrais positifs  : {vrais_positifs}")
print(f"  Faux positifs   : {faux_positifs}")
print(f"  Faux négatifs   : {faux_negatifs}")
print(f"  Vrais négatifs  : {vrais_negatifs}")
print(f"  Précision       : {precision:.2%}")
print(f"  Rappel          : {rappel:.2%}")
print(f"  F1-score        : {f1:.2%}")

# ─── Sauvegarde du modèle et des encodeurs ────────────────────────────────────
output_dir = os.path.dirname(__file__)

joblib.dump(model,          os.path.join(output_dir, "isolation_forest.pkl"))
joblib.dump(le_acte,        os.path.join(output_dir, "le_acte.pkl"))
joblib.dump(le_prescripteur, os.path.join(output_dir, "le_prescripteur.pkl"))
joblib.dump(le_assure,      os.path.join(output_dir, "le_assure.pkl"))
joblib.dump(FEATURES,       os.path.join(output_dir, "features.pkl"))

print("\n✅ Modèle sauvegardé dans data/")
print("   → isolation_forest.pkl")
print("   → le_acte.pkl")
print("   → le_prescripteur.pkl")
print("   → le_assure.pkl")
print("   → features.pkl")