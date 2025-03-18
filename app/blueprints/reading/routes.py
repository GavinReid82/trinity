from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.blueprints.reading import reading_bp
from app.models import db, Transcript, Task
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@reading_bp.route('/tips')
@login_required
def reading_tips():
    return render_template('reading/reading_tips.html')

@reading_bp.route('/paired-text')
@login_required
def reading_a_paired_text():
    return render_template('reading/reading_a_paired_text.html')

@reading_bp.route('/paired-text/submit', methods=['POST'])
@login_required
def submit_reading_answers():
    try:
        data = request.get_json()
        logger.info(f"Received data: {data}")
        
        answers = data.get('answers', {})
        score = data.get('score', 0)
        logger.info(f"Answers: {answers}")
        logger.info(f"Score: {score}")
        
        # Get or create the Reading Task
        task = Task.query.filter_by(name="Reading Paired Text").first()
        if not task:
            task = Task(name="Reading Paired Text", type="reading")
            db.session.add(task)
            db.session.commit()
            logger.info(f"Created new task with ID: {task.id}")
        else:
            logger.info(f"Found existing task with ID: {task.id}")

        # Create transcript entry
        transcript = Transcript(
            user_id=current_user.id,
            task_id=task.id,
            transcription=json.dumps(answers),  # Store answers as JSON
            feedback={"score": score}  # Store score in feedback JSON
        )
        db.session.add(transcript)
        db.session.commit()
        logger.info(f"Created transcript with ID: {transcript.id}")
        
        return jsonify({"status": "success"})

    except Exception as e:
        logger.error(f"Error submitting answers: {str(e)}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500