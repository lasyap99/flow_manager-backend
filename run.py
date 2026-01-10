"""
Application entry point.
Run the Flask application.
"""

import os
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Get host and port from environment or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"Starting Flow Manager on {host}:{port}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    app.run(host=host, port=port, debug=debug)
