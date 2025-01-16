from flask import Flask

app = Flask(__name__)

# Defer importing routes to avoid circular import
from app import routes