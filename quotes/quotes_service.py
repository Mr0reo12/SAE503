from flask import Flask, request, jsonify
from redis import Redis
import os
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)  # Inicializar Swagger

# Configuración de Redis
redis_client = Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)), decode_responses=True)

@app.route('/quotes', methods=['GET'])
def get_quotes():
    """
    Récupérer toutes les citations disponibles.
    ---
    responses:
      200:
        description: Liste des citations
    """
    quotes = redis_client.smembers("quotes")
    quote_list = [redis_client.hgetall(quote) for quote in quotes]
    return jsonify(quote_list), 200

@app.route('/search', methods=['GET'])
def search_quotes():
    """
    Rechercher des citations par mot-clé.
    ---
    parameters:
      - name: keyword
        in: query
        required: true
        type: string
        example: bonheur
    responses:
      200:
        description: Citations correspondant au mot-clé
      400:
        description: Mot-clé requis
    """
    keyword = request.args.get("keyword")
    if not keyword:
        return jsonify({"error": "Mot-clé requis"}), 400

    quotes = redis_client.smembers("quotes")
    filtered_quotes = [
        redis_client.hgetall(quote)
        for quote in quotes
        if keyword.lower() in redis_client.hget(quote, "quote").lower()
    ]
    return jsonify(filtered_quotes), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
