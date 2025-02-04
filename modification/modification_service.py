from flask import Flask, request, jsonify
from redis import Redis
import os
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)  # Initialiser Swagger

# Configuration Redis
redis_client = Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)), decode_responses=True)



@app.route('/', methods=['GET'])
def get_home():
    """
    Page d'accueil de l'API.
    ---
    responses:
      200:
        description: Page d'accueil
    """
    return jsonify({"message": "Bienvenue sur l'API de modification"}), 200

@app.route('/quotes', methods=['POST'])
def add_quote():
    """
    Ajouter une nouvelle citation.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: string
              example: "1"
            quote:
              type: string
              example: "Ceci est une nouvelle citation."
    responses:
      201:
        description: Citation ajoutée avec succès
      400:
        description: user_id et quote sont requis
    """
    data = request.get_json()
    user_id = data.get("user_id")
    quote = data.get("quote")
    if not user_id or not quote:
        return jsonify({"error": "user_id et quote sont requis"}), 400

    quote_id = redis_client.incr("quote_id")
    redis_client.hset(f"quotes:{quote_id}", mapping={"user_id": user_id, "quote": quote})
    redis_client.sadd("quotes", f"quotes:{quote_id}")
    return jsonify({"message": "Citation ajoutée", "id": quote_id}), 201

@app.route('/quotes/<int:quote_id>', methods=['PUT'])
def update_quote(quote_id):
    """
    Mettre à jour une citation existante.
    ---
    parameters:
      - name: quote_id
        in: path
        required: true
        type: integer
        example: 1
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            quote:
              type: string
              example: "Ceci est une citation mise à jour."
    responses:
      200:
        description: Citation mise à jour avec succès
      404:
        description: Citation non trouvée
    """
    data = request.get_json()
    new_quote = data.get("quote")
    if not redis_client.exists(f"quotes:{quote_id}"):
        return jsonify({"error": "Citation non trouvée"}), 404

    redis_client.hset(f"quotes:{quote_id}", "quote", new_quote)
    return jsonify({"message": "Citation mise à jour"}), 200

@app.route('/quotes/<int:quote_id>', methods=['DELETE'])
def delete_quote(quote_id):
    """
    Supprimer une citation existante.
    ---
    parameters:
      - name: quote_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Citation supprimée avec succès
      404:
        description: Citation non trouvée
    """
    if not redis_client.exists(f"quotes:{quote_id}"):
        return jsonify({"error": "Citation non trouvée"}), 404

    redis_client.delete(f"quotes:{quote_id}")
    redis_client.srem("quotes", f"quotes:{quote_id}")
    return jsonify({"message": "Citation supprimée"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
