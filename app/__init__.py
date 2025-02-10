from flask import Flask, make_response
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

# Set file upload limit to 100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Enable CORS and allow embedding from Northpass
CORS(app, resources={r"/*": {"origins": ["https://*.northpass.com"]}})

@app.after_request
def add_headers(response):
    # Allow embedding via iframe
    response.headers['X-Frame-Options'] = 'ALLOW-FROM https://my-org.northpass.com'
    
    # Content Security Policy (CSP) for iframe embedding
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self' https://*.northpass.com"
    return response

# Defer importing routes to avoid circular imports
from app import routes
