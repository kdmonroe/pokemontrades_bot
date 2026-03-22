import os
from pathlib import Path
from pokeball_types import PokeballType

SPRITE_DIR = Path(__file__).parent.parent / 'static' / 'img' / 'pokeballs'

# Build mapping: enum name (lowercase) -> static URL path
POKEBALL_SPRITE_MAP = {}
for member in PokeballType:
    name = member.name.lower()
    if (SPRITE_DIR / f'{name}.png').exists():
        POKEBALL_SPRITE_MAP[name] = f'/static/img/pokeballs/{name}.png'
    elif (SPRITE_DIR / f'{name}.svg').exists():
        POKEBALL_SPRITE_MAP[name] = f'/static/img/pokeballs/{name}.svg'

# Generic fallback for any unmapped ball
_FALLBACK = '/static/img/pokeballs/pokeball.png'


def get_pokeball_sprite_url(ball_name: str) -> str:
    return POKEBALL_SPRITE_MAP.get(ball_name.lower().strip(), _FALLBACK)


def get_all_pokeball_sprites() -> dict:
    return {name: get_pokeball_sprite_url(name) for name in POKEBALL_SPRITE_MAP}
