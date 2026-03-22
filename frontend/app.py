import os
import sys
from functools import wraps
from flask import Flask, redirect, url_for, session

# Add project root to path so we can import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from frontend.config import Config


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from frontend.routes.auth import auth_bp
    from frontend.routes.inventory import inventory_bp
    from frontend.routes.api import api_bp
    from frontend.routes.home import home_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(home_bp)

    @app.route('/')
    def index():
        return redirect(url_for('home.home'))

    return app
