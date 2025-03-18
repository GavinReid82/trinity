from flask import Blueprint

listening_bp = Blueprint('listening', __name__)

from app.blueprints.listening import routes
