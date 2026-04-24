"""
Génération de documents médicaux synthétiques pour tester le pipeline OCR.
Les documents sont des images PNG simulant des ordonnances/factures médicales.
"""

from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "documents_test")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Essai de chargement d'une police lisible
def get_font(size=16):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        try:
            return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
        except:
            return ImageFont.load_default()

def creer_document(nom_fichier, lignes, titre, couleur_titre="#1F4E79"):
    """Génère une image PNG simulant un document médical."""
    largeur, hauteur = 800, 600
    img  = Image.new("RGB", (largeur, hauteur), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # En-tête
    draw.rectangle([0, 0, largeur, 80], fill=couleur_titre)
    draw.text((20, 15), "🏥 CLINIQUE SAINT-JOSEPH", font=get_font(20), fill="white")
    draw.text((20, 45), "123 Avenue de la Santé — Lomé, Togo | Tél : +228 22 00 00 00", font=get_font(13), fill="white")

    # Titre du document
    draw.rectangle([0, 80, largeur, 120], fill="#D6E4F0")
    draw.text((20, 92), titre, font=get_font(18), fill=couleur_titre)

    # Ligne de séparation
    draw.line([20, 130, largeur - 20, 130], fill="#CCCCCC", width=2)

    # Corps du document
    y = 150
    for ligne in lignes:
        if ligne.startswith("##"):
            draw.text((20, y), ligne[2:].strip(), font=get_font(15), fill=couleur_titre)
            draw.line([20, y + 20, largeur - 20, y + 20], fill="#EEEEEE", width=1)
            y += 30
        elif ligne.startswith("**"):
            parts = ligne[2:].split("**")
            draw.text((20, y), parts[0], font=get_font(15), fill="#333333")
            if len(parts) > 1:
                draw.text((250, y), parts[1], font=get_font(15), fill="#111111")
            y += 28
        else:
            draw.text((20, y), ligne, font=get_font(14), fill="#555555")
            y += 26

    # Pied de page
    draw.rectangle([0, hauteur - 50, largeur, hauteur], fill="#F5F5F5")
    draw.line([0, hauteur - 50, largeur, hauteur - 50], fill="#CCCCCC", width=1)
    draw.text((20, hauteur - 35), "Document généré par SinistrAI — Usage académique uniquement", font=get_font(11), fill="#999999")
    draw.text((largeur - 180, hauteur - 35), "CONFIDENTIEL", font=get_font(11), fill="#CC0000")

    # Sauvegarde
    chemin = os.path.join(OUTPUT_DIR, nom_fichier)
    img.save(chemin)
    print(f"✅ Généré : {chemin}")
    return chemin


# ── Document 1 : Facture normale ─────────────────────────────────────────────
creer_document(
    nom_fichier="01_facture_normale.png",
    titre="FACTURE MÉDICALE — Consultation Généraliste",
    lignes=[
        "## Informations Patient",
        "**Nom :**          Jean DUPONT",
        "**Date de naissance :**    15/03/1985",
        "**N° Assuré :**    ASS0001",
        "**Date d'adhésion :**  01/01/2023",
        "",
        "## Détails de l'Acte",
        "**Code acte :**    CONS001",
        "**Libellé :**      Consultation généraliste",
        "**Médecin :**      Dr. MED0001 — Médecin Généraliste",
        "**Date de soin :** 15/01/2026",
        "**Date de dépôt :** 20/01/2026",
        "",
        "## Montant",
        "**Montant réclamé :**  8500 FCFA",
        "**Plafond autorisé :** 15000 FCFA",
        "**Statut :**       Dans les limites autorisées",
    ]
)

# ── Document 2 : Surfacturation (R01) ────────────────────────────────────────
creer_document(
    nom_fichier="02_surfacturation_R01.png",
    titre="FACTURE MÉDICALE — Chirurgie Mineure",
    couleur_titre="#8B0000",
    lignes=[
        "## Informations Patient",
        "**Nom :**          Marie KONÉ",
        "**Date de naissance :**    22/07/1990",
        "**N° Assuré :**    ASS0002",
        "**Date d'adhésion :**  01/06/2022",
        "",
        "## Détails de l'Acte",
        "**Code acte :**    CHIR001",
        "**Libellé :**      Chirurgie mineure — Appendicectomie",
        "**Médecin :**      Dr. MED0012 — Chirurgien",
        "**Date de soin :** 10/02/2026",
        "**Date de dépôt :** 12/02/2026",
        "",
        "## Montant",
        "**Montant réclamé :**  280000 FCFA",
        "**Plafond autorisé :** 150000 FCFA",
        "**⚠️ ANOMALIE R01 :** Montant dépasse le plafond de 130000 FCFA",
    ]
)

# ── Document 3 : Incohérence temporelle (R02) ────────────────────────────────
creer_document(
    nom_fichier="03_incoherence_date_R02.png",
    titre="ORDONNANCE MÉDICALE — Analyse Biologique",
    couleur_titre="#8B0000",
    lignes=[
        "## Informations Patient",
        "**Nom :**          Kofi MENSAH",
        "**Date de naissance :**    10/11/1978",
        "**N° Assuré :**    ASS0003",
        "**Date d'adhésion :**  01/01/2022",
        "",
        "## Détails de l'Acte",
        "**Code acte :**    LABO001",
        "**Libellé :**      Bilan biologique complet",
        "**Médecin :**      Dr. MED0007 — Biologiste",
        "**Date de soin :** 05/03/2021",
        "**Date de dépôt :** 10/06/2026",
        "",
        "## Montant",
        "**Montant réclamé :**  12000 FCFA",
        "**Plafond autorisé :** 20000 FCFA",
        "**⚠️ ANOMALIE R02 :** Date de soin antérieure à la date d'adhésion",
    ]
)

# ── Document 4 : Acte non couvert (R05) ──────────────────────────────────────
creer_document(
    nom_fichier="04_acte_non_couvert_R05.png",
    titre="FACTURE MÉDICALE — Soins Dentaires",
    couleur_titre="#8B0000",
    lignes=[
        "## Informations Patient",
        "**Nom :**          Ama SOW",
        "**Date de naissance :**    05/04/1995",
        "**N° Assuré :**    ASS0004",
        "**Date d'adhésion :**  15/09/2021",
        "",
        "## Détails de l'Acte",
        "**Code acte :**    DENT001",
        "**Libellé :**      Soins dentaires — Extraction molaire",
        "**Médecin :**      FANTOME_999 — Non référencé",
        "**Date de soin :** 20/03/2026",
        "**Date de dépôt :** 25/03/2026",
        "",
        "## Montant",
        "**Montant réclamé :**  35000 FCFA",
        "**Plafond autorisé :** Non défini",
        "**⚠️ ANOMALIE R05 :** Code acte DENT001 absent du référentiel",
    ]
)

# ── Document 5 : Prescripteur fantôme (R05 + score IF élevé) ─────────────────
creer_document(
    nom_fichier="05_prescripteur_fantome.png",
    titre="ORDONNANCE — Hospitalisation",
    couleur_titre="#8B0000",
    lignes=[
        "## Informations Patient",
        "**Nom :**          Paul DIALLO",
        "**Date de naissance :**    30/08/1970",
        "**N° Assuré :**    ASS0005",
        "**Date d'adhésion :**  10/03/2020",
        "",
        "## Détails de l'Acte",
        "**Code acte :**    HOSP001",
        "**Libellé :**      Hospitalisation — Service urgences",
        "**Médecin :**      FANTOME_777 — Identifiant non reconnu",
        "**Date de soin :** 01/04/2026",
        "**Date de dépôt :** 02/04/2026",
        "",
        "## Montant",
        "**Montant réclamé :**  450000 FCFA",
        "**Plafond autorisé :** 300000 FCFA",
        "**⚠️ ANOMALIES :** R01 Surfacturation + R05 Prescripteur non référencé",
    ]
)

print("\n🎉 Tous les documents ont été générés dans data/documents_test/")
print("📁 Importez-les dans SinistrAI pour tester le pipeline complet !")