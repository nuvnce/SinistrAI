# 🛡️ SinistrAI

**Plateforme intelligente de gestion et de détection de fraude dans les remboursements d'assurance santé**

Projet tutoré — Master Big Data | UCAO-UUT | 2025–2026

---

## 📌 Description

SinistrAI est un prototype de plateforme web développé dans le cadre d'un mémoire 
professionnel de Master en Big Data. Il vise à démontrer la faisabilité technique 
d'un système combinant :

- L'extraction automatique de données via **OCR** (EasyOCR)
- La vérification par **règles métiers** simulées
- La **détection d'anomalies** par Machine Learning (Isolation Forest)

appliqués au traitement de dossiers de remboursement en assurance santé.

---

## 🏗️ Architecture
```
sinistrai/
├── app/
│   ├── __init__.py        # Initialisation Flask
│   ├── models.py          # Modèles SQLAlchemy (4 entités)
│   ├── routes/
│   │   ├── auth.py        # Authentification
│   │   └── dossiers.py    # Gestion des dossiers
│   ├── services/          # Logique métier & ML (à venir)
│   ├── static/            # CSS, JS, images
│   └── templates/         # HTML Jinja2
├── data/                  # Données synthétiques
├── config.py              # Configuration
├── run.py                 # Point d'entrée
└── requirements.txt       # Dépendances
```

---

## ⚙️ Installation

### Prérequis
- Python 3.9+
- pip

### Étapes

1. Cloner le dépôt :
```bash
   git clone https://github.com/votre-username/sinistrai.git
   cd sinistrai
```

2. Créer et activer l'environnement virtuel :
```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
```

3. Installer les dépendances :
```bash
   pip install -r requirements.txt
```

4. Lancer l'application :
```bash
   python run.py
```

5. Créer le compte admin de test :
   Ouvrir `http://127.0.0.1:5000/init-admin` dans le navigateur.

6. Se connecter sur `http://127.0.0.1:5000/login` :
   - Email : `admin@sinistrai.com`
   - Mot de passe : `admin123`

---

## 🚀 Fonctionnalités

| Fonctionnalité | Statut |
|---|---|
| Authentification sécurisée (bcrypt) | ✅ Terminé |
| Modèle de données (4 entités) | ✅ Terminé |
| Gestion des dossiers (CRUD) | 🔄 En cours |
| Import documents + OCR | ⏳ À venir |
| Moteur de règles métiers | ⏳ À venir |
| Détection d'anomalies (Isolation Forest) | ⏳ À venir |
| Tableau de bord | ⏳ À venir |

---

## 🛠️ Stack technique

| Couche | Technologie |
|---|---|
| Back-end | Python / Flask |
| Base de données | SQLite / SQLAlchemy |
| Front-end | HTML / Bootstrap 5 / JavaScript |
| OCR | EasyOCR |
| Machine Learning | scikit-learn (Isolation Forest) |
| Visualisation | Chart.js |

---

## 📄 Licence

Projet académique — Usage éducatif uniquement.