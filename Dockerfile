FROM python:3.13-slim

# Installer des dépendances système nécessaires pour PyNUT (Network UPS Tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nut-client \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier requirements.txt et installer les dépendances Python
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script dans le conteneur
COPY ups-auto-shutdown.py ups-auto-shutdwon.py

# Définir le répertoire de travail
WORKDIR /app

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "ups-auto-shutdwon.py"]
