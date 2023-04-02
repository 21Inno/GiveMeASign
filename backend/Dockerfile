# Utilisez une image Python pré-configurée
FROM python:3.9

# Installez les dépendances
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

# Copiez le code de votre application Flask dans le conteneur Docker
COPY . /app

# Définir la variable d'environnement FLASK_APP
ENV FLASK_APP=app.py

# Exposez le port sur lequel votre application Flask écoute
EXPOSE 5000

# Lancez l'application Flask
CMD ["flask", "run", "--host=0.0.0.0"]
