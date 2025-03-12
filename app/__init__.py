from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from pymongo import MongoClient
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mongo_client = None

def setup_logging(app):
    """Configure detailed logging."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler
    log_file = os.path.join(log_dir, 'app.log')
    file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] - %(message)s'
    ))
    file_handler.setLevel(logging.DEBUG)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Specific loggers
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_logger.setLevel(logging.WARNING)

def create_app():
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Configure PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/gnss_data')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    
    # Configure file uploads
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    
    # Configure logging
    setup_logging(app)
    app.logger.info('Application starting up...')
    
    # Configure JSON settings
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    app.config['JSONIFY_MIMETYPE'] = 'application/json'
    
    # Initialize MongoDB
    global mongo_client
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    mongo_client = MongoClient(mongo_uri)
    app.logger.info('MongoDB client initialized')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    app.logger.info('Database initialized')
    
    # Configure login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    app.logger.info('Login manager initialized')
    
    # Ensure upload directory exists
    upload_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    app.logger.info(f'Upload directory created/verified: {upload_dir}')
    
    # Register blueprints
    from .routes import main, api, auth
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(auth.bp, url_prefix='/auth')
    app.logger.info('Blueprints registered')
    
    @app.before_first_request
    def create_tables():
        db.create_all()
        app.logger.info('Database tables created')
    
    app.logger.info('Application initialization complete')
    return app
