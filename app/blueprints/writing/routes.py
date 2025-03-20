from flask_login import current_user
from app.models import db, Transcript, Task
from flask import Blueprint, render_template, request, url_for, redirect, flash, jsonify
from openai import OpenAI
import json
import os
from app.blueprints.writing import writing_bp
from flask_login import login_required

writing_bp = Blueprint('writing', __name__, template_folder='templates')

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



@writing_bp.route('/')
def writing_home():
    return render_template('writing/home.html')

@writing_bp.route('/task_1')
def writing_task_1():
    return render_template('writing/writing_task_1.html')

@writing_bp.route('/task_2')
def writing_task_2():
    return render_template('writing/writing_task_2.html')

@writing_bp.route('/writing_tips')
def writing_tips():
    return render_template('writing/writing_tips.html')

@writing_bp.route('/writing_task_1_group_chat')
def writing_task_1_group_chat():
    return render_template('writing/writing_task_1_group_chat.html')

@writing_bp.route('/writing_task_1_discussion_board')
def writing_task_1_discussion_board():
    return render_template('writing/writing_task_1_discussion_board.html')

@writing_bp.route('/writing_task_1_direct_communication')
def writing_task_1_direct_communication():
    return render_template('writing/writing_task_1_direct_communication.html')

@writing_bp.route('/writing_task_2_essay')
def writing_task_2_essay():
    return render_template('writing/writing_task_2_essay.html')

@writing_bp.route('/writing_task_2_report')
def writing_task_2_report():
    return render_template('writing/writing_task_2_report.html')

@writing_bp.route('/writing_task_1_submit', methods=['POST'])
def writing_task_1_submit():
    if not current_user.is_authenticated:
        flash("You must be logged in to submit a writing task.", "warning")
        return redirect(url_for('auth.login'))
    
    response = request.form.get('writingTask1').replace("\r\n", "\n")
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are an instructor for Trinity's ISE Digital Writing exam. "
                "Your job is to give feedback to candidates based on their performance, following the guidelines below. "
                "Write in British English at all times. Your feedback language should be simple enough for a grade 5 (or A2 on CEFR) to understand.\n\n"
                
                "Task 1C: Group chat. Instructions to candidates. "
                "1. Respond to the Lilly.\n"
                "2, Ask the group to help you with something relevant to the group task"

                "The prompt for candidates:\n"
                "You are talking to your classmates about a group project for school. Write a message to your group and a) respond to Lilly b) ask the group to help you with something. "
                "Group project: Organise a book club\n"
                "I'm worried about time. We only have two weeks and there's so much to do!\n"

                "Your job is principally to ensure that the candidate has followed the task instructions and, if they haven't, suggest what they could do better."
                "For example, and this is IMPORTANT, the task is asking the candidate to participate in ORGANISING a book club, not just writing about a book club in general. The emphasis is on organising a club. "
                "Structure your feedback into three sections: "
                "1. General Comment, 2. What You Did Well (bullet points), and 3. What You Could Improve (bullet points). "
                "Return the feedback as JSON with keys: 'general_comment', 'did_well', and 'could_improve'."
            )
        },
        {"role": "user", "content": f"Here is the candidate's submission:\n\n{response}"}
    ]

    openai_response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=400
    )

    try:
        feedback = json.loads(openai_response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        feedback = {"general_comment": "Error processing feedback.", "did_well": [], "could_improve": []}

    # ✅ Get the Writing Task ID (Assuming it's already in the `tasks` table)
    task = Task.query.filter_by(name="Writing Task 1 - Group Chat").first()
    if not task:
        task = Task(name="Writing Task 1 - Group Chat", type="writing")
        db.session.add(task)
        db.session.commit()

    # ✅ Save to `transcripts` table
    transcript = Transcript(
        user_id=current_user.id,
        task_id=task.id,
        transcription=response,
        feedback=feedback
    )
    db.session.add(transcript)

    db.session.commit()
    
    return render_template(
        'writing/writing_task_1_feedback.html',
        response=response,
        general_comment=feedback.get('general_comment', ''),
        did_well=feedback.get('did_well', []),
        could_improve=feedback.get('could_improve', [])
    )

@writing_bp.route('/writing_task_2_essay_submit', methods=['POST'])
def writing_task_2_essay_submit():
    if not current_user.is_authenticated:
        flash("You must be logged in to submit a writing task.", "warning")
        return redirect(url_for('auth.login'))
    
    response = request.form.get('writingTask2essay').replace("\r\n", "\n")
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are an instructor for Trinity's ISE Digital Writing exam. "
                "Your job is to give feedback to candidates based on their performance, following the guidelines below. "
                "Write in British English at all times. Your feedback language should be simple enough for a grade 5 (or A2 on CEFR) to understand.\n\n"
                
                "Task 2 essay: . Instructions to candidates. "
                "1. Respond to the Lilly.\n"
                
                "The prompt for candidates:\n"
                "You are talking to your classmates about a group project for school. Write a message to your group and a) respond to Lilly b) ask the group to help you with something. "
                "Group project: Organise a book club\n"
                "I'm worried about time. We only have two weeks and there's so much to do!\n"

                "Your job is principally to ensure that the candidate has followed the task instructions and, if they haven't, suggest what they could do better."
                "For example, and this is IMPORTANT, the task is asking the candidate to participate in ORGANISING a book club, not just writing about a book club in general. The emphasis is on organising a club. "
                "Structure your feedback into three sections: "
                "1. General Comment, 2. What You Did Well (bullet points), and 3. What You Could Improve (bullet points). "
                "Return the feedback as JSON with keys: 'general_comment', 'did_well', and 'could_improve'."
            )
        },
        {"role": "user", "content": f"Here is the candidate's submission:\n\n{response}"}
    ]

    openai_response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=400
    )

    try:
        feedback = json.loads(openai_response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        feedback = {"general_comment": "Error processing feedback.", "did_well": [], "could_improve": []}

    # ✅ Get the Writing Task ID (Assuming it's already in the `tasks` table)
    task = Task.query.filter_by(name="Writing Task 2 - Essay").first()
    if not task:
        task = Task(name="Writing Task 2 - Essay", type="writing")
        db.session.add(task)
        db.session.commit()

    # ✅ Save to `transcripts` table
    transcript = Transcript(
        user_id=current_user.id,
        task_id=task.id,
        transcription=response,
        feedback=feedback
    )
    db.session.add(transcript)

    db.session.commit()
    
    return render_template(
        'writing/writing_task_2_feedback.html',
        response=response,
        general_comment=feedback.get('general_comment', ''),
        did_well=feedback.get('did_well', []),
        could_improve=feedback.get('could_improve', [])
    )

@writing_bp.route('/submit', methods=['POST'])
@login_required
def submit_writing():
    try:
        data = request.get_json()
        transcription = data.get('transcription', '')
        feedback = data.get('feedback', {})
        
        # Get or create the Writing Task
        task = Task.query.filter_by(name="Writing Task 1").first()
        if not task:
            task = Task(name="Writing Task 1", type="writing")
            db.session.add(task)
            db.session.commit()

        # Create transcript entry
        transcript = Transcript(
            user_id=current_user.id,
            task_id=task.id,
            transcription=transcription,
            feedback=feedback
        )
        db.session.add(transcript)
        db.session.commit()
        
        return jsonify({"status": "success"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
