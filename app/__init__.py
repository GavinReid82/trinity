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
    # ✅ Allow microphone access using valid syntax for Permissions-Policy
    response.headers['Permissions-Policy'] = (
        "microphone=(self), microphone=(https://courses.trinitycollege.com), microphone=(https://app.northpass.com)"
    )

    # ✅ Keep existing security headers for iframe embedding
    response.headers['Content-Security-Policy'] = (
        "frame-ancestors 'self' https://courses.trinitycollege.com https://app.northpass.com"
    )
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'

    return response


# Defer importing routes to avoid circular imports
from app import routes

