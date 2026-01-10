from flask import Flask, redirect
from flask_cors import CORS
from flask_migrate import Migrate
from app.config import get_config
from app.models import db
import logging
from logging.handlers import RotatingFileHandler
import os


migrate = Migrate()


def create_app(config_name=None):
    """
    Application factory pattern.
    
    Args:
        config_name: Configuration name (development, testing, production)
    
    Returns:
        Flask application instance
    """
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
    
    # Register blueprints FIRST
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize Swagger AFTER blueprints
    from flasgger import Swagger
    
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Flow Manager API",
            "description": "Sequential task execution engine with conditional routing",
            "contact": {
                "responsibleOrganization": "Flow Manager",
                "email": "support@flowmanager.com",
            },
            "version": "1.0.0"
        },
        "host": f"localhost:{os.environ.get('FLASK_PORT', 5001)}",
        "basePath": "/",
        "schemes": ["http"],
    }
    
    swagger = Swagger(app, config=swagger_config, template=swagger_template)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    app.logger.info('Flow Manager application started with Swagger UI')
    
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


def register_error_handlers(app):
    """Register error handlers."""
    from flask import jsonify
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An internal error occurred'
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error)
        }), 400
