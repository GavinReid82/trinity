from flask import Flask, make_response
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

# Set file upload limit to 100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# ✅ Allow requests from Northpass (both preview and production)
CORS(app, resources={r"/*": {"origins": ["https://*.northpass.com", "https://courses.trinitycollege.com"]}})

@app.after_request
def add_headers(response):
    # ✅ Correct X-Frame-Options for compatibility with Northpass preview
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'

    # ✅ Allow iframe embedding using CSP (Content Security Policy)
    response.headers['Content-Security-Policy'] = (
        "frame-ancestors 'self' https://*.northpass.com https://courses.trinitycollege.com"
    )

    return response

# Defer importing routes to avoid circular imports
from app import routes

