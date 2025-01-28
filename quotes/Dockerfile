# Utiliser une image de base Python 3.9 légère
FROM python:3.9-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers nécessaires dans le conteneur
COPY . /app

# Installer les dépendances requises
RUN pip install --no-cache-dir flask redis
RUN pip install flasgger 
# Exposer le port utilisé par l'application
EXPOSE 5001

# Commande pour exécuter l'application
CMD ["python", "quotes_service.py"]
