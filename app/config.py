"""
Configuration module for Flow Manager application.
Supports multiple environments: development, testing, production.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration class with common settings."""
    
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # JSON settings
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Request settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.environ.get('LOG_FILE', 'flow_manager.log')
    
    # Flow execution settings
    MAX_FLOW_EXECUTION_TIME = int(os.environ.get('MAX_FLOW_EXECUTION_TIME', 3600))  # 1 hour in seconds
    TASK_TIMEOUT = int(os.environ.get('TASK_TIMEOUT', 300))  # 5 minutes in seconds
    
    # Pagination settings
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///flow_manager_dev.db'
    SQLALCHEMY_ECHO = True  # Log all SQL queries in development
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing environment configuration."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///flow_manager_test.db'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Faster password hashing for tests
    BCRYPT_LOG_ROUNDS = 4
    
    # Short execution times for faster tests
    MAX_FLOW_EXECUTION_TIME = 60
    TASK_TIMEOUT = 10


class ProductionConfig(Config):
    """Production environment configuration."""
    
    # Database - will be validated when this config is actually used
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Don't echo SQL in production
    SQLALCHEMY_ECHO = False
    
    # Production logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration object based on environment name.
    
    Args:
        config_name: Name of the configuration ('development', 'testing', 'production')
                    If None, uses FLASK_ENV environment variable or 'default'
    
    Returns:
        Configuration class object
    
    Raises:
        ValueError: If production config is requested without DATABASE_URL
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    config_class = config.get(config_name, config['default'])
    
    # Validate production config when it's actually being used
    if config_name == 'production' and not os.environ.get('DATABASE_URL'):
        raise ValueError("DATABASE_URL environment variable must be set in production")
    
    return config_class