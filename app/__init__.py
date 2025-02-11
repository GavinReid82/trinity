from flask import Flask

# Initialize Flask app
app = Flask(__name__)

# Set file upload limit to 100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Defer importing routes to avoid circular imports
from app import routes

