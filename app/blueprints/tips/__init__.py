from flask import Blueprint

tips_bp = Blueprint('tips', __name__)

from app.blueprints.tips import routes 