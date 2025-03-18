import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    SQLALCHEMY_DATABASE_URI = 'postgresql://gavinreid@localhost/trinity_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False