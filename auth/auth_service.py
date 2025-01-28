from flask import Flask, request, jsonify
from redis import Redis
import os
import csv
import jwt
import datetime
from functools import wraps
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)  # Inicializar Swagger

# Configuración de Redis
redis_client = Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)), decode_responses=True)

# Clave secreta para JWT
SECRET_KEY = os.getenv("SECRET_KEY", "mi_super_secreto")

# Cargar usuarios desde el archivo CSV
def load_users_from_csv():
    if redis_client.scard("users") == 0:
        with open("initial_data_users.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                user_id = row["id"]
                name = row["name"]
                password = row["password"]
                redis_client.hset(f"users:{user_id}", mapping={"id": user_id, "name": name, "password": password})
                redis_client.sadd("users", f"users:{user_id}")

load_users_from_csv()

# Decorador para validar tokens JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token manquant"}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expiré"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token invalide"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['POST'])
def login():
    """
    Endpoint pour se connecter et obtenir un token JWT.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: admin
            password:
              type: string
              example: admin123
    responses:
      200:
        description: Authentification réussie
      401:
        description: Échec de l'authentification
    """
    data = request.get_json()
    name = data.get("name")
    password = data.get("password")
    users = redis_client.smembers("users")

    for user_key in users:
        user = redis_client.hgetall(user_key)
        if user["name"] == name and user["password"] == password:
            token = jwt.encode(
                {"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
                SECRET_KEY,
                algorithm="HS256"
            )
            return jsonify({"message": "Authentification réussie", "token": token}), 200

    return jsonify({"error": "Nom d'utilisateur ou mot de passe incorrect"}), 401

@app.route('/users', methods=['GET'])
@token_required
def get_users():
    """
    Récupérer la liste des utilisateurs (protégé par JWT).
    ---
    security:
      - bearerAuth: []
    responses:
      200:
        description: Liste des utilisateurs
      401:
        description: Token invalide ou manquant
    """
    users = [redis_client.hgetall(user_id) for user_id in redis_client.smembers("users")]
    return jsonify(users), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
