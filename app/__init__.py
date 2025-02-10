from flask import Flask, make_response
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

# Set file upload limit to 100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Production CORS: Allow only trusted domains (Northpass and Trinity courses)
CORS(app, resources={r"/*": {"origins": ["https://*.northpass.com", "https://courses.trinitycollege.com"]}})

@app.after_request
def add_headers(response):
    # X-Frame-Options: Modern browsers do not fully support ALLOW-FROM, so use CSP instead
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'  # No need for ALLOWALL or ALLOW-FROM

    # Content Security Policy to allow iframe embedding from specific domains
    response.headers['Content-Security-Policy'] = (
        "frame-ancestors 'self' https://*.northpass.com https://courses.trinitycollege.com"
    )

    return response

# Defer importing routes to avoid circular imports
from app import routes

