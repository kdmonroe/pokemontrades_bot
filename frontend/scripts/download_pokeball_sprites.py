"""
One-time script to download pokeball sprites from PokeAPI and generate
SVG fallbacks for balls not available in the PokeAPI sprites repository.
"""
import os
import sys
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from pokeball_types import PokeballType

OUTPUT_DIR = Path(__file__).parent.parent / 'static' / 'img' / 'pokeballs'
SPRITE_BASE = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items'

# Mapping from PokeballType enum name (lowercase) to PokeAPI sprite filename
POKEBALL_URL_SLUGS = {
    'love': 'love-ball',
    'dream': 'dream-ball',
    'beast': 'beast-ball',
    'moon': 'moon-ball',
    'friend': 'friend-ball',
    'heavy': 'heavy-ball',
    'lure': 'lure-ball',
    'fast': 'fast-ball',
    'level': 'level-ball',
    'safari': 'safari-ball',
    'sport': 'sport-ball',
    'pokeball': 'poke-ball',
    'great': 'great-ball',
    'ultra': 'ultra-ball',
    'master': 'master-ball',
    'premier': 'premier-ball',
    'repeat': 'repeat-ball',
    'timer': 'timer-ball',
    'nest': 'nest-ball',
    'net': 'net-ball',
    'dive': 'dive-ball',
    'luxury': 'luxury-ball',
    'heal': 'heal-ball',
    'quick': 'quick-ball',
    'dusk': 'dusk-ball',
    'cherish': 'cherish-ball',
}

# Balls without PokeAPI sprites — generate SVG fallbacks with unique colors
SVG_FALLBACK_COLORS = {
    'pokeball_h': ('#e63946', '#2a2a3d', 'Poké Ball (H)'),
    'great_h': ('#448aff', '#2a2a3d', 'Great Ball (H)'),
    'ultra_h': ('#ffc400', '#2a2a3d', 'Ultra Ball (H)'),
    'heavy_h': ('#78909c', '#2a2a3d', 'Heavy Ball (H)'),
    'feather': ('#80deea', '#e0f7fa', 'Feather Ball'),
    'wing': ('#4fc3f7', '#b3e5fc', 'Wing Ball'),
    'jet': ('#1a237e', '#283593', 'Jet Ball'),
    'leaden': ('#616161', '#424242', 'Leaden Ball'),
    'gigaton': ('#8d6e63', '#5d4037', 'Gigaton Ball'),
    'origin': ('#7b1fa2', '#ffc400', 'Origin Ball'),
}


def generate_pokeball_svg(top_color: str, bottom_color: str, name: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">
  <title>{name}</title>
  <circle cx="20" cy="20" r="18" fill="{bottom_color}" stroke="#555" stroke-width="2"/>
  <path d="M2 20 A18 18 0 0 1 38 20 Z" fill="{top_color}"/>
  <line x1="2" y1="20" x2="38" y2="20" stroke="#555" stroke-width="2.5"/>
  <circle cx="20" cy="20" r="6" fill="#1a1a28" stroke="#555" stroke-width="2"/>
  <circle cx="20" cy="20" r="3" fill="#f5f0e8"/>
  <rect x="2" y="19" width="12" height="2" fill="#555" rx="1"/>
  <rect x="26" y="19" width="12" height="2" fill="#555" rx="1"/>
</svg>'''


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    generated = 0
    failed = 0

    for member in PokeballType:
        name = member.name.lower()

        # Try downloading from PokeAPI
        if name in POKEBALL_URL_SLUGS:
            slug = POKEBALL_URL_SLUGS[name]
            url = f'{SPRITE_BASE}/{slug}.png'
            out_path = OUTPUT_DIR / f'{name}.png'

            if out_path.exists():
                print(f'  [skip] {name}.png already exists')
                downloaded += 1
                continue

            try:
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200:
                    with open(out_path, 'wb') as f:
                        f.write(resp.content)
                    print(f'  [ok]   {name}.png downloaded ({len(resp.content)} bytes)')
                    downloaded += 1
                else:
                    print(f'  [fail] {name}.png — HTTP {resp.status_code}')
                    failed += 1
            except requests.RequestException as e:
                print(f'  [fail] {name}.png — {e}')
                failed += 1

        # Generate SVG fallback
        elif name in SVG_FALLBACK_COLORS:
            top, bottom, display_name = SVG_FALLBACK_COLORS[name]
            svg = generate_pokeball_svg(top, bottom, display_name)
            out_path = OUTPUT_DIR / f'{name}.svg'
            with open(out_path, 'w') as f:
                f.write(svg)
            print(f'  [svg]  {name}.svg generated')
            generated += 1

        else:
            print(f'  [???]  {name} — no URL mapping or fallback color defined')
            failed += 1

    print(f'\nDone: {downloaded} downloaded, {generated} SVG generated, {failed} failed')


if __name__ == '__main__':
    main()
