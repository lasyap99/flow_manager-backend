"""
Flask application factory.
"""

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from app.config import get_config
from app.models import db
import logging
from logging.handlers import RotatingFileHandler
import os


migrate = Migrate()


def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize Swagger BEFORE error handlers
    from flasgger import Swagger
    
    swagger = Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": "Flow Manager API",
            "description": "Sequential task execution engine",
            "version": "1.0.0"
        },
        "host": f"localhost:{os.environ.get('FLASK_PORT', 5001)}",
        "basePath": "/",
        "schemes": ["http"]
    })
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Debug: Print routes
    print("\n" + "="*70)
    print("ALL REGISTERED ROUTES:")
    print("="*70)
    for rule in app.url_map.iter_rules():
        print(f"{rule.rule:50s} -> {rule.endpoint}")
    print("="*70 + "\n")
    
    app.logger.info('Flow Manager application started')
    
    return app


def setup_logging(app):
    """Configure application logging."""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            app.config['LOG_FORMAT']
        ))
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
    
    app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))


def register_blueprints(app):
    """Register Flask blueprints."""
    from app.api.flows import flows_bp
    from app.api.executions import executions_bp
    from app.api.tasks import tasks_bp
    
    app.register_blueprint(flows_bp, url_prefix='/api/flows')
    app.register_blueprint(executions_bp, url_prefix='/api/executions')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
