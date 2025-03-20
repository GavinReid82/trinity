from app.extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        """Hashes the password and stores it securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'speaking' or 'listening'

    def __repr__(self):
        return f"<Task {self.name} ({self.type})>"


class Transcript(db.Model):
    __tablename__ = 'transcripts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    transcription = db.Column(db.Text, nullable=False)
    feedback = db.Column(db.JSON, nullable=True)  # AI-generated feedback stored as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add this field to link follow-up responses to main responses
    main_transcript_id = db.Column(db.Integer, db.ForeignKey('transcripts.id'), nullable=True)

    # Add relationship
    main_transcript = db.relationship('Transcript', remote_side=[id], backref='follow_up_responses')

    def __repr__(self):
        return f"<Transcript User {self.user_id}, Task {self.task_id}>"