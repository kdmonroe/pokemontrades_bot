from flask import Blueprint, jsonify, request
from frontend.services.pokeapi_service import PokeAPIService

api_bp = Blueprint('api', __name__, url_prefix='/api')
pokeapi = PokeAPIService()


@api_bp.route('/pokemon/<name>')
def get_pokemon(name):
    data = pokeapi.get_pokemon(name)
    if data is None:
        return jsonify({'error': 'Pokemon not found'}), 404
    return jsonify(data)


@api_bp.route('/pokemon/search')
def search_pokemon():
    query = request.args.get('q', '')
    matches = pokeapi.search_pokemon(query)
    return jsonify(matches)
