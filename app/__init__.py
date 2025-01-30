from flask import Flask

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# Defer importing routes to avoid circular import
from app import routes