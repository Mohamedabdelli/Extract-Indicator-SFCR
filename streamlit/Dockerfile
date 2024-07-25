# Utilisez une image de base officielle Python
FROM python:3.10

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt contenant les bibliothèques Python à installer
COPY requirements.txt .

# Installer les bibliothèques Python spécifiées dans requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copier tous les fichiers de l'application dans le répertoire de travail du conteneur
COPY . .
# Copier le fichier .env
COPY .env .

# Exposer le port sur lequel l'application Streamlit sera accessible
EXPOSE 8501

# Commande pour exécuter l'application Streamlit
CMD ["streamlit", "run", "app.py"]
