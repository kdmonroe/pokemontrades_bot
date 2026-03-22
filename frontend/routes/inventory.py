import os
import random
import uuid
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, send_file, current_app)
from frontend.app import login_required
from frontend.services.inventory_service import (InventoryService, ALL_POKEBALL_NAMES,
                                                    POKEMON_FORMS, GAME_VERSIONS)
from frontend.services.pokeapi_service import PokeAPIService
from frontend.services.pokeball_sprite_service import get_all_pokeball_sprites

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')
pokeapi = PokeAPIService()
pokeball_sprites = get_all_pokeball_sprites()


def _session_id() -> str:
    if '_inventory_sid' not in session:
        session['_inventory_sid'] = str(uuid.uuid4())
    return session['_inventory_sid']


def _ensure_inventory(service: InventoryService) -> dict:
    """Return inventory, auto-loading the default CSV if nothing is loaded yet."""
    inventory = service.get_inventory()
    if not inventory and not service.has_inventory():
        default_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                   'files', 'pokemon-list01.csv')
        if os.path.exists(default_csv):
            try:
                inventory = service.load_from_file(default_csv)
            except Exception:
                pass
    return inventory


def _grid_context(inventory: dict) -> dict:
    """Build the full template context dict for grid rendering."""
    sprites = pokeapi.get_sprites_for_inventory(inventory)
    # Build ability options and collect dex numbers from PokeAPI for each pokemon
    ability_options = {}
    dex_numbers = {}
    for name in inventory:
        data = pokeapi.get_pokemon(name)
        if data and data.get('all_abilities'):
            ability_options[name] = data['all_abilities']
        elif data and data.get('abilities'):
            ability_options[name] = [{'name': a, 'is_hidden': False} for a in data['abilities']]
        else:
            ability_options[name] = []
        if data and data.get('id'):
            dex_numbers[name] = data['id']

    # Shuffle inventory randomly for a fresh feel on each load
    items = list(inventory.items())
    random.shuffle(items)
    sorted_inventory = dict(items)

    return dict(
        inventory=sorted_inventory,
        pokeball_types=ALL_POKEBALL_NAMES,
        sprites=sprites,
        pokeball_sprites=pokeball_sprites,
        pokemon_forms=POKEMON_FORMS,
        game_versions=GAME_VERSIONS,
        ability_options=ability_options,
        dex_numbers=dex_numbers,
    )


def _single_row_context(pokemon: str, service: InventoryService) -> dict:
    """Build template context for rendering a single grid row."""
    inventory = service.get_inventory()
    data = inventory.get(pokemon, {})
    sprites = pokeapi.get_sprites_for_inventory({pokemon: data})
    pokeapi_data = pokeapi.get_pokemon(pokemon)
    ao = {}
    if pokeapi_data and pokeapi_data.get('all_abilities'):
        ao[pokemon] = pokeapi_data['all_abilities']
    elif pokeapi_data and pokeapi_data.get('abilities'):
        ao[pokemon] = [{'name': a, 'is_hidden': False} for a in pokeapi_data['abilities']]
    else:
        ao[pokemon] = []
    dex_numbers = {}
    if pokeapi_data and pokeapi_data.get('id'):
        dex_numbers[pokemon] = pokeapi_data['id']
    return dict(
        name=pokemon,
        data=data,
        pokeball_types=ALL_POKEBALL_NAMES,
        sprites=sprites,
        pokeball_sprites=pokeball_sprites,
        ability_options=ao,
        dex_numbers=dex_numbers,
    )


@inventory_bp.route('/')
@login_required
def index():
    service = InventoryService(_session_id())
    inventory = _ensure_inventory(service)
    ctx = _grid_context(inventory)
    return render_template('inventory/index.html', **ctx)


@inventory_bp.route('/upload', methods=['GET'])
@login_required
def upload_form():
    service = InventoryService(_session_id())
    has_data = service.has_inventory()
    count = len(service.get_inventory()) if has_data else 0
    return render_template('inventory/upload.html',
                           has_inventory=has_data,
                           pokemon_count=count)


@inventory_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('inventory.upload_form'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('inventory.upload_form'))

    if not (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        flash('Please upload a CSV or XLSX file.', 'error')
        return redirect(url_for('inventory.upload_form'))

    sid = _session_id()
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], sid)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)

    try:
        service = InventoryService(sid)
        service.load_from_file(filepath)
        flash(f'Loaded inventory from {file.filename}', 'success')
    except Exception as e:
        flash(f'Error reading file: {e}', 'error')
        return redirect(url_for('inventory.upload_form'))

    return redirect(url_for('inventory.index'))


@inventory_bp.route('/export')
@login_required
def export():
    service = InventoryService(_session_id())
    _ensure_inventory(service)
    csv_buffer = service.export_csv()
    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='pokemon-inventory.csv'
    )


@inventory_bp.route('/filter')
@login_required
def filter_inventory():
    service = InventoryService(_session_id())
    query = request.args.get('q', '')
    pokeball_filter = request.args.get('pokeball', '')

    inventory = service.filter_combined(query=query, pokeball=pokeball_filter)

    ctx = _grid_context(inventory)
    return render_template('inventory/_grid_table.html', **ctx)


@inventory_bp.route('/toggle/<pokemon>/<pokeball>', methods=['POST'])
@login_required
def toggle(pokemon, pokeball):
    service = InventoryService(_session_id())
    service.toggle_pokeball(pokemon, pokeball)
    return render_template('inventory/_grid_row.html',
                           **_single_row_context(pokemon, service))


@inventory_bp.route('/add', methods=['POST'])
@login_required
def add_pokemon():
    service = InventoryService(_session_id())
    name = request.form.get('name', '')
    abilities = request.form.get('abilities', '').split(',')
    form = request.form.get('form', '')
    game = request.form.get('game', '')
    shiny = request.form.get('shiny') == 'on'
    special = request.form.get('special', '')
    iv_raw = request.form.get('iv', '').strip()
    iv = None
    if iv_raw:
        try:
            iv = max(0, min(31, int(iv_raw)))
        except ValueError:
            iv = None

    if not name:
        return '', 400

    service.add_pokemon(name, abilities, form=form, game=game,
                        shiny=shiny, special=special, iv=iv)
    inventory = service.get_inventory()
    ctx = _grid_context(inventory)
    return render_template('inventory/_grid_table.html', **ctx)


@inventory_bp.route('/toggle-ability/<pokemon>/<ability>', methods=['POST'])
@login_required
def toggle_ability(pokemon, ability):
    service = InventoryService(_session_id())
    service.set_ability(pokemon, ability)
    return render_template('inventory/_grid_row.html',
                           **_single_row_context(pokemon, service))


@inventory_bp.route('/cycle-ability/<pokemon>', methods=['POST'])
@login_required
def cycle_ability(pokemon):
    service = InventoryService(_session_id())
    # Get ability options from PokeAPI
    pokeapi_data = pokeapi.get_pokemon(pokemon)
    ao_list = []
    if pokeapi_data and pokeapi_data.get('all_abilities'):
        ao_list = pokeapi_data['all_abilities']
    elif pokeapi_data and pokeapi_data.get('abilities'):
        ao_list = [{'name': a, 'is_hidden': False} for a in pokeapi_data['abilities']]

    service.cycle_ability(pokemon, ao_list)
    return render_template('inventory/_grid_row.html',
                           **_single_row_context(pokemon, service))


@inventory_bp.route('/update-iv/<pokemon>', methods=['POST'])
@login_required
def update_iv(pokemon):
    service = InventoryService(_session_id())
    iv_raw = request.form.get('iv', '').strip()
    iv = None
    if iv_raw:
        try:
            iv = max(0, min(31, int(iv_raw)))
        except ValueError:
            iv = None
    if not service.set_iv(pokemon, iv):
        return '', 404
    return render_template('inventory/_grid_row.html',
                           **_single_row_context(pokemon, service))


@inventory_bp.route('/remove/<pokemon>', methods=['DELETE'])
@login_required
def remove_pokemon(pokemon):
    service = InventoryService(_session_id())
    service.remove_pokemon(pokemon)
    return '', 200
