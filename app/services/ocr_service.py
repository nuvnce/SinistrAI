import re
import os
import numpy as np

# Détection environnement production
IS_PRODUCTION = os.environ.get('RENDER') or os.environ.get('PRODUCTION')

import platform

if not IS_PRODUCTION:
    import easyocr
    from pdf2image import convert_from_path
    from PIL import Image

    # Poppler : chemin Windows en local, None dans Docker/Linux
    POPPLER_PATH = (
        r"D:\DANIEL ESSONANI\sinistrai\poppler-25.12.0\Library\bin"
        if platform.system() == "Windows"
        else None
    )
    reader = easyocr.Reader(['fr', 'en'], verbose=False)

ACTES_PLAFONDS = {
    "CONS001": 15000, "CONS002": 25000, "RADIO001": 30000,
    "LABO001": 20000, "CHIR001": 150000, "HOSP001": 300000,
    "PHARMA001": 10000, "KINE001": 12000,
}


def extraire_texte(chemin_fichier):
    """Extrait le texte brut d'un PDF ou d'une image."""
    if IS_PRODUCTION:
        return "Document simulé en environnement de production."

    extension = os.path.splitext(chemin_fichier)[1].lower()
    if extension == '.pdf':
        kwargs = {"poppler_path": POPPLER_PATH} if POPPLER_PATH else {}
        images = convert_from_path(chemin_fichier, **kwargs)
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
        "montant":        None,
        "date":           None,
        "beneficiaire":   None,
        "code_acte":      None,
        "plafond_acte":   None,
        "assure_id":      None,
        "date_adhesion":  None,
        "prescripteur_id": None,
        "texte_brut":     texte
    }

    # ── Montant ────────────────────────────────────────────────────────────
    patterns_montant = [
        r'(\d{1,3}(?:[.,\s]\d{3})+(?:[.,]\d{2})?)\s*(?:fcfa|xof|cfa|€|\$|f\.?cfa)?',
        r'(\d+[.,]\d{2})\s*(?:fcfa|xof|cfa|€|\$)?',
        r'montant\s*r[eé]clam[eé]\s*:?\s*(\d[\d\s.,]*)',
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

    # ── Date de soin ───────────────────────────────────────────────────────
    patterns_date = [
        r'date\s*de\s*soin\s*:?\s*(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})',
        r'\b(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})\b',
        r'\b(\d{4})[/\-\.](\d{2})[/\-\.](\d{2})\b',
        r'\b(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|'
        r'septembre|octobre|novembre|décembre|january|february|march|april|'
        r'may|june|july|august|september|october|november|december)\s+(\d{4})\b',
    ]
    mois_map = {
        'janvier': '01', 'février': '02', 'fevrier': '02', 'mars': '03',
        'avril': '04', 'mai': '05', 'juin': '06', 'juillet': '07',
        'août': '08', 'aout': '08', 'septembre': '09', 'octobre': '10',
        'novembre': '11', 'décembre': '12', 'decembre': '12',
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12',
        'jan': '01', 'fév': '02', 'fev': '02', 'avr': '04',
        'juil': '07', 'aoû': '08', 'aou': '08', 'sept': '09',
        'oct': '10', 'nov': '11', 'déc': '12', 'dec': '12',
        'feb': '02', 'mar': '03', 'apr': '04', 'jun': '06',
        'jul': '07', 'aug': '08', 'sep': '09',
    }
    for pattern in patterns_date:
        match = re.search(pattern, texte.lower())
        if match:
            groupes = match.groups()
            if len(groupes) == 1:
                parts = re.split(r'[/\-\.]', groupes[0])
                if len(parts) == 3:
                    champs["date"] = f"{parts[2]}-{parts[1]}-{parts[0]}"
                break
            elif len(groupes) == 3:
                if groupes[1] in mois_map:
                    champs["date"] = f"{groupes[2]}-{mois_map[groupes[1]]}-{groupes[0].zfill(2)}"
                elif len(groupes[0]) == 4:
                    champs["date"] = f"{groupes[0]}-{groupes[1]}-{groupes[2]}"
                else:
                    champs["date"] = f"{groupes[2]}-{groupes[1]}-{groupes[0]}"
                break

    # ── Bénéficiaire ───────────────────────────────────────────────────────
    patterns_beneficiaire = [
        r'(?:patient|assuré|bénéficiaire|nom)\s*:?\s*([A-ZÀ-Ÿa-zà-ÿ]+(?:\s+[A-ZÀ-Ÿa-zà-ÿ]+){1,3})',
        r'(?:m\.|mme|dr\.?|monsieur|madame)\s+([A-ZÀ-Ÿa-zà-ÿ]+(?:\s+[A-ZÀ-Ÿa-zà-ÿ]+){0,2})',
    ]
    for pattern in patterns_beneficiaire:
        match = re.search(pattern, texte, re.IGNORECASE)
        if match:
            champs["beneficiaire"] = match.group(1).strip().title()
            break

    # ── Code acte ──────────────────────────────────────────────────────────
    patterns_acte = [
        r'code\s*acte\s*:?\s*([A-Z]+\d+)',
        r'\bcode\s*:?\s*([A-Z]+\d+)',
    ]
    for pattern in patterns_acte:
        match = re.search(pattern, texte, re.IGNORECASE)
        if match:
            champs["code_acte"] = match.group(1).upper().strip()
            break

    # ── Prescripteur ───────────────────────────────────────────────────────
    patterns_prescripteur = [
        r'm[eé]decin\s*:?\s*((?:MED|FANTOME)[\w_]+)',
        r'prescripteur\s*:?\s*((?:MED|FANTOME)[\w_]+)',
        r'Dr\.\s+(MED\w+)',
    ]
    for pattern in patterns_prescripteur:
        match = re.search(pattern, texte, re.IGNORECASE)
        if match:
            champs["prescripteur_id"] = match.group(1).upper().strip()
            break

    # ── Numéro assuré ──────────────────────────────────────────────────────
    patterns_assure = [
        r'n[°o\.]\s*assur[eé]\s*:?\s*(ASS\d+)',
        r'assur[eé]\s*:?\s*(ASS\d+)',
        r'\b(ASS\d{4})\b',
    ]
    for pattern in patterns_assure:
        match = re.search(pattern, texte, re.IGNORECASE)
        if match:
            champs["assure_id"] = match.group(1).upper().strip()
            break

    # ── Date d'adhésion ────────────────────────────────────────────────────
    patterns_adhesion = [
        r'adh[eé]sion\s*:?\s*(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})',
        r"d[''']adh[eé]sion\s*:?\s*(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})",
    ]
    for pattern in patterns_adhesion:
        match = re.search(pattern, texte, re.IGNORECASE)
        if match:
            try:
                parts = re.split(r'[/\-\.]', match.group(1))
                champs["date_adhesion"] = f"{parts[2]}-{parts[1]}-{parts[0]}"
            except Exception:
                pass
            break

    # ── Plafond depuis code acte ───────────────────────────────────────────
    if champs.get("code_acte"):
        champs["plafond_acte"] = ACTES_PLAFONDS.get(champs["code_acte"], 0)

    return champs


def analyser_document(chemin_fichier):
    """Fonction principale : extrait texte + champs depuis un fichier."""
    if IS_PRODUCTION:
        import random
        champs = {
            "montant":      random.choice([8500, 12000, 25000, 45000, 150000]),
            "date":         random.choice(["2026-01-15", "2026-02-10", "2026-03-20"]),
            "beneficiaire": random.choice(["Jean Dupont", "Marie Koné", "Kofi Mensah"]),
            "texte_brut":   "Simulation OCR — environnement de production."
        }
        return {"succes": True, "champs": champs}

    try:
        texte  = extraire_texte(chemin_fichier)
        champs = extraire_champs(texte)
        return {"succes": True, "champs": champs}
    except Exception as e:
        return {"succes": False, "erreur": str(e), "champs": {}}