import os

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    PKMN_USERNAME = os.environ.get('PKMN_USERNAME', 'admin')
    PKMN_PASSWORD = os.environ.get('PKMN_PASSWORD', 'admin')
