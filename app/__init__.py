from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import os
from urllib.parse import urlparse

db_uri = os.environ['CARDS_DATABASE_URI']
# for legacy sqlite3 connection
db_path = urlparse(db_uri).path

db = SQLAlchemy()
bootstrap = Bootstrap()

def create_app(config_name):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '606d2fc4-31cb-4ce1-a35b-346ec660994d')

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    db.init_app(app)

    if os.environ.get('BOOTSTRAP_SERVE_LOCAL') in ['YES', 'TRUE', '1']:
        app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    bootstrap.init_app(app)

    from .main import main as main_bp
    app.register_blueprint(main_bp)

    return app
