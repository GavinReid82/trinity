from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.blueprints.listening import listening_bp
from app.models import db, Transcript, Task
import json

@listening_bp.route('/')
@login_required
def listening_home():
    return render_template('listening/home.html')

@listening_bp.route('/tips')
@login_required
def listening_tips():
    return render_template('listening/listening_tips.html')

@listening_bp.route('/talk')
@login_required
def listening_talk():
    return render_template('listening/listening_to_talk_retelling.html')

@listening_bp.route('/talk-retelling')
@login_required
def listening_to_talk_retelling():
    return render_template('listening/listening_to_talk_retelling.html')

@listening_bp.route('/talk-retelling/submit', methods=['POST'])
@login_required
def submit_listening_answers():
    try:
        data = request.get_json()
        answers = data.get('answers', {})
        score = data.get('score', 0)
        
        # Get or create the Listening Task
        task = Task.query.filter_by(name="Listening to a Talk").first()
        if not task:
            task = Task(name="Listening to a Talk", type="listening")
            db.session.add(task)
            db.session.commit()

        # Create transcript entry
        transcript = Transcript(
            user_id=current_user.id,
            task_id=task.id,
            transcription=json.dumps(answers),  # Store answers as JSON
            feedback={"score": score}  # Store score in feedback JSON
        )
        db.session.add(transcript)
        db.session.commit()
        
        return jsonify({"status": "success"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
