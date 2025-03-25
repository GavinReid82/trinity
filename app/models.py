from app.extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    access_code = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"

    @classmethod
    def find_by_access_code(cls, code):
        """Find a user by their access code."""
        return cls.query.filter_by(access_code=code).first()


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