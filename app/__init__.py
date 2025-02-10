from flask import Flask, make_response
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

# Set file upload limit to 100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Enable CORS and allow embedding from Northpass
CORS(app, resources={r"/*": {"origins": ["https://*.northpass.com", "https://courses.trinitycollege.com"]}})

@app.after_request
def add_headers(response):
    # Allow embedding within both preview and production Northpass environments
    response.headers['X-Frame-Options'] = 'ALLOW-FROM https://courses.trinitycollege.com'
    
    # Allow iframe embedding using Content Security Policy (CSP)
    response.headers['Content-Security-Policy'] = (
        "frame-ancestors 'self' https://*.northpass.com https://courses.trinitycollege.com"
    )

    return response

# Defer importing routes to avoid circular imports
from app import routes
