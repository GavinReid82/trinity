from flask import Blueprint

reading_bp = Blueprint('reading', __name__)

from app.blueprints.reading import routes
