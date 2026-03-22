import json
import time
import difflib
import requests
from pathlib import Path

CACHE_PATH = Path(__file__).parent.parent / 'static' / 'cache' / 'pokeapi_cache.json'
SPECIES_LIST_PATH = Path(__file__).parent.parent / 'static' / 'cache' / 'species_names.json'
POKEAPI_BASE = 'https://pokeapi.co/api/v2'


class PokeAPIService:

    def __init__(self):
        self._cache = self._load_cache()
        self._species_names = self._load_species_names()

    def _load_cache(self) -> dict:
        if CACHE_PATH.exists():
            with open(CACHE_PATH, 'r') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_PATH, 'w') as f:
            json.dump(self._cache, f, indent=2)

    def _load_species_names(self) -> list:
        if SPECIES_LIST_PATH.exists():
            with open(SPECIES_LIST_PATH, 'r') as f:
                return json.load(f)
        return []

    def _save_species_names(self):
        SPECIES_LIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SPECIES_LIST_PATH, 'w') as f:
            json.dump(self._species_names, f)

    def _ensure_species_list(self):
        if self._species_names:
            return
        try:
            resp = requests.get(f'{POKEAPI_BASE}/pokemon-species/?limit=2000', timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                self._species_names = [entry['name'] for entry in data['results']]
                self._save_species_names()
        except requests.RequestException:
            pass

    def _fuzzy_match(self, name: str) -> str | None:
        self._ensure_species_list()
        if not self._species_names:
            return None
        matches = difflib.get_close_matches(name, self._species_names, n=1, cutoff=0.75)
        return matches[0] if matches else None

    def _fetch_generation(self, name: str) -> str | None:
        try:
            resp = requests.get(f'{POKEAPI_BASE}/pokemon-species/{name}', timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('generation', {}).get('name', '')
        except (requests.RequestException, KeyError):
            pass
        return None

    def get_pokemon(self, name: str) -> dict | None:
        name = name.lower().strip()

        # Return cached data (including negative lookups)
        if name in self._cache:
            cached = self._cache[name]
            if cached.get('not_found'):
                return None
            # Backfill generation if missing from older cache entries
            if 'generation' not in cached and cached.get('sprite'):
                gen = self._fetch_generation(name)
                if gen:
                    cached['generation'] = gen
                    self._save_cache()
            return cached

        # Try direct fetch
        result = self._fetch_pokemon_data(name)

        # If failed, try fuzzy match
        if result is None:
            corrected = self._fuzzy_match(name)
            if corrected and corrected != name:
                result = self._fetch_pokemon_data(corrected)
                if result:
                    # Cache under both the original and corrected names
                    self._cache[corrected] = result
                    self._cache[name] = result
                    self._save_cache()
                    return result

        # Cache negative lookup
        if result is None:
            self._cache[name] = {'sprite': None, 'not_found': True}
            self._save_cache()
            return None

        self._cache[name] = result
        self._save_cache()
        return result

    def _fetch_pokemon_data(self, name: str) -> dict | None:
        try:
            resp = requests.get(f'{POKEAPI_BASE}/pokemon/{name}', timeout=10)
            if resp.status_code != 200:
                return None
            data = resp.json()
            all_abilities = []
            for a in data['abilities']:
                all_abilities.append({
                    'name': a['ability']['name'],
                    'is_hidden': a['is_hidden'],
                })
            result = {
                'sprite': data['sprites']['front_default'],
                'types': [t['type']['name'] for t in data['types']],
                'abilities': [a['ability']['name'] for a in data['abilities']],
                'all_abilities': all_abilities,
                'id': data['id'],
            }
            # Also fetch generation from species endpoint
            generation = self._fetch_generation(name)
            if generation:
                result['generation'] = generation
            return result
        except (requests.RequestException, KeyError):
            return None

    def get_sprites_for_inventory(self, inventory: dict) -> dict:
        sprites = {}
        for name in inventory:
            data = self.get_pokemon(name)
            if data and data.get('sprite'):
                sprites[name] = data['sprite']
        return sprites

    def get_all_pokemon_metadata(self, inventory: dict) -> dict:
        metadata = {}
        for name in inventory:
            data = self.get_pokemon(name)
            if data and not data.get('not_found'):
                metadata[name] = {
                    'types': data.get('types', []),
                    'generation': data.get('generation', ''),
                    'sprite': data.get('sprite'),
                }
        return metadata

    def search_pokemon(self, query: str, limit: int = 10) -> list:
        query = query.lower().strip()
        if not query:
            return []

        matches = [name for name in self._cache
                   if query in name and not self._cache[name].get('not_found')]
        if len(matches) >= limit:
            return matches[:limit]

        data = self.get_pokemon(query)
        if data and query not in matches:
            matches.insert(0, query)

        return matches[:limit]
