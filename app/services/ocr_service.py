import easyocr
import re
import json
import os
from pdf2image import convert_from_path
from PIL import Image

# Chemin Poppler
POPPLER_PATH = r"D:\DANIEL ESSONANI\sinistrai\poppler-25.12.0\Library\bin"

# Initialisation du lecteur EasyOCR (français + anglais)
# Le premier appel télécharge les modèles (~500MB), les suivants sont instantanés
reader = easyocr.Reader(['fr', 'en'], verbose=False)


def extraire_texte(chemin_fichier):
    """Extrait le texte brut d'un PDF ou d'une image."""
    extension = os.path.splitext(chemin_fichier)[1].lower()

    if extension == '.pdf':
        images = convert_from_path(chemin_fichier, poppler_path=POPPLER_PATH)
        texte_complet = ""
        for image in images:
            resultats = reader.readtext(np.array(image), detail=0)
            texte_complet += " ".join(resultats) + " "
        return texte_complet.strip()
    else:
        resultats = reader.readtext(chemin_fichier, detail=0)
        return " ".join(resultats)


def extraire_champs(texte):
    """Extrait les champs clés depuis le texte OCR."""
    champs = {
        "montant":      None,
        "date":         None,
        "beneficiaire": None,
        "texte_brut":   texte
    }

    # ── Extraction du montant ──────────────────────────────────────────────
    # Cherche des patterns comme : 15000, 15 000, 15.000, 15,000 FCFA/XOF/€/$
    patterns_montant = [
        r'(\d{1,3}(?:[.,\s]\d{3})+(?:[.,]\d{2})?)\s*(?:fcfa|xof|cfa|€|\$|f\.?cfa)?',
        r'(\d+[.,]\d{2})\s*(?:fcfa|xof|cfa|€|\$)?',
        r'montant\s*:?\s*(\d[\d\s.,]*)',
        r'total\s*:?\s*(\d[\d\s.,]*)',
        r'(\d{4,})',
    ]
    for pattern in patterns_montant:
        match = re.search(pattern, texte.lower())
        if match:
            montant_str = match.group(1).replace(' ', '').replace(',', '.')
            try:
                champs["montant"] = float(montant_str)
                break
            except ValueError:
                continue

    # ── Extraction de la date ──────────────────────────────────────────────
    # Cherche des patterns : 01/01/2024, 01-01-2024, 2024-01-01, 01 janvier 2024
    patterns_date = [
        r'\b(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})\b',
        r'\b(\d{4})[/\-\.](\d{2})[/\-\.](\d{2})\b',
        r'\b(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|'
        r'septembre|octobre|novembre|décembre)\s+(\d{4})\b',
    ]
    mois_map = {
        'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
        'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
        'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
    }
    for pattern in patterns_date:
        match = re.search(pattern, texte.lower())
        if match:
            groupes = match.groups()
            if len(groupes) == 3:
                if groupes[1] in mois_map:
                    champs["date"] = f"{groupes[2]}-{mois_map[groupes[1]]}-{groupes[0].zfill(2)}"
                elif len(groupes[0]) == 4:
                    champs["date"] = f"{groupes[0]}-{groupes[1]}-{groupes[2]}"
                else:
                    champs["date"] = f"{groupes[2]}-{groupes[1]}-{groupes[0]}"
                break

    # ── Extraction du bénéficiaire ─────────────────────────────────────────
    # Cherche des patterns : "Patient : Nom", "Assuré : Nom", "Nom : ..."
    patterns_beneficiaire = [
        r'(?:patient|assuré|bénéficiaire|nom)\s*:?\s*([A-ZÀ-Ÿa-zà-ÿ]+(?:\s+[A-ZÀ-Ÿa-zà-ÿ]+){1,3})',
        r'(?:m\.|mme|dr\.?|monsieur|madame)\s+([A-ZÀ-Ÿa-zà-ÿ]+(?:\s+[A-ZÀ-Ÿa-zà-ÿ]+){0,2})',
    ]
    for pattern in patterns_beneficiaire:
        match = re.search(pattern, texte, re.IGNORECASE)
        if match:
            champs["beneficiaire"] = match.group(1).strip().title()
            break

    return champs


def analyser_document(chemin_fichier):
    """Fonction principale : extrait texte + champs depuis un fichier."""
    try:
        texte = extraire_texte(chemin_fichier)
        champs = extraire_champs(texte)
        return {"succes": True, "champs": champs}
    except Exception as e:
        return {"succes": False, "erreur": str(e), "champs": {}}