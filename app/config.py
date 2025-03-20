import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    SQLALCHEMY_DATABASE_URI = 'postgresql://gavinreid@localhost/trinity_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Add upload folder configuration
    # Create uploads directory in app root if it doesn't exist
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)