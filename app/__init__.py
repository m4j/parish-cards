from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import os
import logging
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse

db_uri = os.environ['CARDS_DATABASE_URI']
# for legacy sqlite3 connection
db_path = urlparse(db_uri).path

db = SQLAlchemy()
bootstrap = Bootstrap()

def init_logging(app):
    """Initialize logging configuration for the application"""
    log_file = os.environ.get('CARDS_LOG')
    log_level = os.environ.get('CARDS_LOG_LEVEL', 'INFO')
    if log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = RotatingFileHandler(log_file,
                                         maxBytes=1048576, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(log_level)
    app.logger.info('Parish Cards startup')

def create_app(config_name):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '606d2fc4-31cb-4ce1-a35b-346ec660994d')

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    db.init_app(app)

    if os.environ.get('BOOTSTRAP_SERVE_LOCAL') in ['YES', 'TRUE', '1']:
        app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    bootstrap.init_app(app)

    # Initialize logging
    init_logging(app)

    from .main import main as main_bp
    from .application import application as application_bp
    from .payment import payment as payment_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(application_bp, url_prefix='/application')
    app.register_blueprint(payment_bp, url_prefix='/payment')

    return app

# Enable foreign key constraints for SQLite
from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()