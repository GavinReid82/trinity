from flask import Flask, make_response
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

# Set file upload limit to 100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# ✅ CORS settings: Allow requests from Northpass and Trinity courses
CORS(app, resources={r"/*": {"origins": ["https://*.northpass.com", "https://courses.trinitycollege.com"]}})

@app.after_request
def add_headers(response):
    # ✅ Permissions-Policy: Allow microphone access from any domain within the iframe
    response.headers['Permissions-Policy'] = "microphone=(self https://*.northpass.com https://courses.trinitycollege.com)"

    # ✅ Content Security Policy: Allow iframe embedding from Northpass and Trinity courses
    response.headers['Content-Security-Policy'] = (
        "frame-ancestors 'self' https://*.northpass.com https://courses.trinitycollege.com"
    )

    # ✅ X-Frame-Options: Allow iframe embedding (no conflicts)
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'

    return response

# Defer importing routes to avoid circular imports
from app import routes

