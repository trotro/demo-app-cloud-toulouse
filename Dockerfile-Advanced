# Utiliser une image Python officielle comme base
FROM python:3.10-slim

RUN useradd -ms /bin/bash pythonuser

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de dépendances et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code de l'application
COPY /app .

# Exposer le port sur lequel l'application Flask va s'exécuter
EXPOSE 5000

USER pythonuser
# Variables d'environnement pour Flask
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Exécuter l'application avec Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
