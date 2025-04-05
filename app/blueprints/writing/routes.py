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
    word_count = len(response.strip().split())

    
    messages = [
        {
            "role": "system",
            "content": (
                "You are an instructor for Trinity's ISE Digital Writing exam. "
                "Your job is to give feedback to candidates based on their performance, following the guidelines below. "
                "Write in British English at all times. Your feedback language should be simple enough for a grade 5 (or A2 on CEFR) to understand.\n\n"
                "Your job is principally to ensure that the candidate has followed the task instructions and, if they haven't, suggest what they could do better."
                f"IMPORTANT: The submission is {word_count} words. The task requires about 250 words (maximum 300 words). "
                "If the word count exceeds 300, you MUST include this as a point to improve.\n"
                "IMPORTANT: the candidate MUST use ideas from texts A and B AND their own ideas.\n"
                "IMPORTANT: the candidate MUST NOT copy directly from the texts.\n"
                
                "The prompt for candidates:\n"
                "Write a formal essay for your course tutor, developing an argument on the following topic: "
                "Some people believe that in the future everyone will live in high-rise buildings. To what extent do you agree or disagree?\n"

                "Text A: Book summary, Streets in the Sky by Robert Kay\n"
                "Paragraph 1: Robert Kay's book is about communities in Britain who were moved from houses into so-called 'high-rise' accommodation. 'High-rise' means apartments in tall buildings with anything more than four floors, although many buildings had twenty or thirty floors. In the 1960s many people lived in small two-storey houses with poor heating and little plumbing. The authorities thought these houses were too crowded and old-fashioned for Britain's growing population.\n"
                "Paragraph 2: The authorities expected them to be happier in blocks of apartments they called 'streets in the sky'. But many people disliked their new homes. The architects used concrete as it was easy to build with, but the public thought it made the buildings look dull. Residents missed their old neighbours, and they didn't get to know their new neighbours because the tower blocks had few shared areas to meet in. For the children, there were no gardens to play in. Many residents moved back into houses when they could afford it, and some less popular tower blocks were demolished in the 1990s.\n"

                "Text B: Living Spaces Magazine, Reimagining Home\n"
                "Paragraph 1: We continue our series on Reimagining Home. Last month, we looked at co-housing communities and why more people are sharing their living space. This month, we ask a different question: can high-rise buildings feel like home?\n"
                "Paragraph 2: A recent satisfaction survey revealed that, while high-rise apartments are seen as convenient and good value for money, they are still thought to be smaller, noisier, and less safe than houses.\n"
                "Paragraph 3: A new project in Westchester City, England may start to change people's minds. The architects of 'Rose Park Towers' say that their development shows that high-rise living is moving away from the lonely grey concrete blocks of the past.\n"
                "Paragraph 4: The buildings are certainly beautiful, with four ten-storey towers of rose-coloured glass offering wide views of the city. Neighbours can meet and relax in the rooftop gardens. The development also has its own supermarket, gym, two restaurants, and friendly security staff. Most residents here are happy with their accommodation, despite the surprisingly high price. As a luxury development, some Rose Parks apartments cost just as much as a house in the suburbs.\n"
                "Paragraph 5: The government has praised the project for its ecological design and is now planning to use similar solutions which use solar energy and sustainable materials to other urban infrastructure.\n"

                "Structure your feedback into three sections: "
                "1. General Comment, 2. What You Did Well (bullet points), and 3. What You Could Improve (bullet points). "
                "Before giving feedback, count the words in the submission. If it's over 300 words, include this in 'could_improve'."
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
