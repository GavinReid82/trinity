from flask import Flask, make_response
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

# Set file upload limit to 100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# CORS For local testing
CORS(app, resources={r"/*": {"origins": ["*"]}})

# PRODUCTION: Enable CORS and allow embedding from Northpass
#CORS(app, resources={r"/*": {"origins": ["https://*.northpass.com", "https://courses.trinitycollege.com"]}})

@app.after_request
def add_headers(response):
    # Allow iframe embedding from any origin (for testing only)
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    
    # OR restrict to specific domains (for production)
    response.headers['X-Frame-Options'] = 'ALLOW-FROM https://courses.trinitycollege.com'

    # Content Security Policy to allow iframe embedding
    response.headers['Content-Security-Policy'] = (
        "frame-ancestors 'self' https://*.northpass.com https://courses.trinitycollege.com"
    )

    return response


# Defer importing routes to avoid circular imports
from app import routes
