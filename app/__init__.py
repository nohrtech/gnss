from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mongo_client = None

def create_app():
    app = Flask(__name__)
    
    # Configure PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/gnss_data')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    
    # Initialize MongoDB
    global mongo_client
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    mongo_client = MongoClient(mongo_uri)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Ensure upload directory exists
    upload_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Register blueprints
    from .routes import main, api, auth
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(auth.bp, url_prefix='/auth')
    
    @app.before_first_request
    def create_tables():
        db.create_all()
    
    return app
