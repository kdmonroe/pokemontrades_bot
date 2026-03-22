import io
import pandas as pd
from pkmn_csv_reader import PokemonCsvReader
from pokeball_types import PokeballType, validate_pokeball


ALL_POKEBALL_NAMES = [e.name.lower() for e in PokeballType]

# CSV column name mapping (enum name -> CSV header as it appears in the file)
POKEBALL_CSV_HEADERS = {
    'pokeball': 'poke',
    'pokeball_h': 'poke-h',
    'great_h': 'great-h',
    'ultra_h': 'ultra-h',
    'heavy_h': 'heavy-h',
}

# Regional/special form variants from the LLM training data
POKEMON_FORMS = [
    'regular', 'alolan', 'galarian', 'hisuian', 'paldean',
    'blaze breed', 'aqua breed', 'combat breed',
]

# Game versions supported (latest two Switch titles + Home)
GAME_VERSIONS = ['SV', 'PLA', 'SWSH', 'BDSP', 'Home']

# Default game for new entries
DEFAULT_GAME = 'SV'


def _csv_col_name(ball_name: str) -> str:
    return POKEBALL_CSV_HEADERS.get(ball_name, ball_name)


# Server-side inventory store keyed by session ID
_inventories = {}


class InventoryService:

    def __init__(self, session_id: str):
        self.session_id = session_id

    def load_from_file(self, filepath: str) -> dict:
        reader = PokemonCsvReader()
        reader.read_file(filepath)
        inventory = reader.get_pokemons()
        # Ensure all entries have the extended fields
        for name, data in inventory.items():
            data.setdefault('form', '')
            data.setdefault('game', DEFAULT_GAME)
            data.setdefault('shiny', False)
            data.setdefault('special', '')
            data.setdefault('iv', None)
        _inventories[self.session_id] = inventory
        return inventory

    def get_inventory(self) -> dict:
        return _inventories.get(self.session_id, {})

    def has_inventory(self) -> bool:
        return self.session_id in _inventories

    def toggle_pokeball(self, pokemon: str, pokeball: str) -> bool:
        inventory = self.get_inventory()
        pokemon = pokemon.lower().strip()
        pokeball = pokeball.lower().strip()

        if pokemon not in inventory:
            return False
        if not validate_pokeball(pokeball):
            return False

        pokeballs = inventory[pokemon]['pokeballs']
        if pokeball in pokeballs:
            pokeballs.remove(pokeball)
        else:
            pokeballs.append(pokeball)
        return True

    def add_pokemon(self, name: str, abilities: list,
                    form: str = '', game: str = '',
                    shiny: bool = False, special: str = '',
                    iv: int | None = None) -> bool:
        inventory = self.get_inventory()
        name = name.lower().strip()
        if name in inventory:
            return False
        inventory[name] = {
            'abilities': [a.lower().strip() for a in abilities if a.strip()],
            'pokeballs': [],
            'form': form.lower().strip(),
            'game': game.upper().strip() or DEFAULT_GAME,
            'shiny': shiny,
            'special': special.strip(),
            'iv': iv,
        }
        return True

    def set_ability(self, pokemon: str, ability: str) -> bool:
        inventory = self.get_inventory()
        pokemon = pokemon.lower().strip()
        ability = ability.lower().strip()
        if pokemon not in inventory:
            return False
        current = inventory[pokemon]['abilities']
        if ability in current:
            current.remove(ability)
        else:
            current.append(ability)
        return True

    def cycle_ability(self, pokemon: str, ability_options: list) -> str | None:
        """Cycle to the next ability from the PokeAPI options list.

        Returns the new ability name, or None if no options available.
        """
        inventory = self.get_inventory()
        pokemon = pokemon.lower().strip()
        if pokemon not in inventory or not ability_options:
            return None

        option_names = [a['name'] for a in ability_options]
        current = inventory[pokemon]['abilities']

        if current and current[0] in option_names:
            idx = option_names.index(current[0])
            next_ability = option_names[(idx + 1) % len(option_names)]
        else:
            # Pick first non-hidden, or first overall
            non_hidden = [a['name'] for a in ability_options if not a.get('is_hidden')]
            next_ability = non_hidden[0] if non_hidden else option_names[0]

        inventory[pokemon]['abilities'] = [next_ability]
        return next_ability

    def set_iv(self, pokemon: str, iv: int | None) -> bool:
        inventory = self.get_inventory()
        pokemon = pokemon.lower().strip()
        if pokemon not in inventory:
            return False
        inventory[pokemon]['iv'] = iv
        return True

    def remove_pokemon(self, name: str) -> bool:
        inventory = self.get_inventory()
        name = name.lower().strip()
        if name not in inventory:
            return False
        del inventory[name]
        return True

    def export_csv(self) -> io.BytesIO:
        inventory = self.get_inventory()
        rows = []
        for name, data in inventory.items():
            row = {
                'Pokemon': name.title(),
                'Ability': ', '.join(data['abilities']),
                'IV': data.get('iv') if data.get('iv') is not None else '',
                'Form': data.get('form', ''),
                'Game': data.get('game', DEFAULT_GAME),
                'Shiny': 'yes' if data.get('shiny') else '',
                'Special': data.get('special', ''),
            }
            for ball in ALL_POKEBALL_NAMES:
                col = _csv_col_name(ball)
                row[col] = 'x' if ball in data['pokeballs'] else ''
            rows.append(row)

        columns = (['Pokemon', 'Ability', 'IV', 'Form', 'Game', 'Shiny', 'Special']
                   + [_csv_col_name(b) for b in ALL_POKEBALL_NAMES])
        df = pd.DataFrame(rows, columns=columns)
        buffer = io.BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer

    def filter_by_name(self, query: str) -> dict:
        inventory = self.get_inventory()
        query = query.lower().strip()
        if not query:
            return inventory
        return {k: v for k, v in inventory.items() if query in k}

    def filter_by_pokeball(self, pokeball: str) -> dict:
        inventory = self.get_inventory()
        pokeball = pokeball.lower().strip()
        if not pokeball:
            return inventory
        return {k: v for k, v in inventory.items() if pokeball in v['pokeballs']}

    def filter_combined(self, query: str = '', pokeball: str = '') -> dict:
        inventory = self.get_inventory()

        if query:
            query = query.lower().strip()
            inventory = {k: v for k, v in inventory.items() if query in k}
        if pokeball:
            pokeball = pokeball.lower().strip()
            inventory = {k: v for k, v in inventory.items()
                         if pokeball in v['pokeballs']}
        return inventory
