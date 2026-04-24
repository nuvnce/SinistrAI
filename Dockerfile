# Image de base Python 3.11 légère
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PRODUCTION=false

# Dépendances système nécessaires pour EasyOCR, Poppler et psycopg2
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libpq-dev \
    gcc \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Dossier de travail
WORKDIR /app

# Copier et installer les dépendances d'abord (cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet
COPY . .

# Créer les dossiers nécessaires
RUN mkdir -p app/static/uploads data/documents_test

# Port exposé
EXPOSE 5000

# Lancement
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120"]