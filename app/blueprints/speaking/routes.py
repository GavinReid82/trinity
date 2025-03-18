from flask import Blueprint, render_template, request, session, redirect, url_for
from openai import OpenAI
import json
import os
import re
from werkzeug.utils import secure_filename
from app.blueprints.speaking import speaking_bp


speaking_bp = Blueprint('speaking', __name__, template_folder='templates')
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@speaking_bp.route('/')
def speaking_home():
    return render_template('speaking/home.html')

@speaking_bp.route('/speaking_tips')
def speaking_tips():
    return render_template('speaking/speaking_tips.html')

@speaking_bp.route('/speaking_task_2')
def speaking_task_2():
    return render_template('speaking/speaking_task_2.html')

@speaking_bp.route('/speaking_task_3')
def speaking_task_3():
    return render_template('speaking/speaking_task_3.html')

@speaking_bp.route('/speaking_task_4')
def speaking_task_4():
    return render_template('speaking/speaking_task_4.html')


@speaking_bp.route('/speaking_task_1_q1')
def speaking_task_1_q1():
    return render_template('speaking/speaking_task_1.html', 
                           question="I'm planning to take my family on holiday next year. What kind of holiday is best and why?", 
                           question_number=1)


@speaking_bp.route('/speaking_task_1_q2')
def speaking_task_1_q2():
    return render_template('speaking/speaking_task_1.html', 
                           question="What do you do to relax?", 
                           question_number=2)


@speaking_bp.route('/speaking_task_1_q3')
def speaking_task_1_q3():
    return render_template('speaking/speaking_task_1.html', 
                           question="I think life is becoming more stressful. Would you agree?", 
                           question_number=3)


@speaking_bp.route('/speaking_task_submit', methods=['POST'])
def speaking_task_submit():
    print(f"🔍 Request received at: {request.path}")
    print(f"🔍 Full request data: {request.form}")

    questions = {
    "1": "I'm planning to take my family on holiday next year. What kind of holiday is best and why?",
    "2": "What do you do to relax?",
    "3": "I think life is becoming more stressful. Would you agree?"
    }   

    if 'audio_file' not in request.files:
        return render_template(
            'speaking_task_1_feedback.html',
            question="Unknown question",
            transcription="No transcription available.",
            general_comment="No file uploaded.",
            did_well=[],
            could_improve=[]
        )

    # ✅ Save the uploaded binary audio file
    file = request.files['audio_file']
    filename = secure_filename(f"candidate_12345_q{request.form['question_number']}.webm")
    audio_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        file.save(audio_file_path)
        print(f"Audio file saved: {audio_file_path}")
    except Exception as e:
        print(f"Error saving file: {e}")
        return render_template(
            'speaking_task_1_feedback.html',
            question="Unknown question",
            transcription="No transcription available.",
            general_comment="Failed to save audio file.",
            did_well=[],
            could_improve=[]
        )

    # ✅ Send to OpenAI Whisper for transcription
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        transcription = response.strip()
        print(f"Transcription: {transcription}")

    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return render_template(
            'speaking_task_1_feedback.html',
            question="Unknown question",
            transcription="No transcription available.",
            general_comment="Audio transcription failed.",
            did_well=[],
            could_improve=[]
        )

    # ✅ Keep YOUR Detailed Prompt for GPT-4
    messages = [
        {"role": "system", "content": (
            "You are an instructor for Trinity's ISE Digital Speaking exam. "
            "Your job is to give feedback to candidates based on their performance, following the guidelines below. "
            "Write in British English at all times. Your feedback language should be simple enough for a grade 5 (or A2 on CEFR) to understand.\n\n"

            "Candidates are graded on the following: "
            "1. Task fulfilment: Ability to respond to the task with relevant details, organise ideas coherently, and respond fully in the time allowed (30 seconds per question). "
            "2. Language: Ability to use a range of grammar and lexis accurately and effectively. "
            "3. Delivery: Ability to use stress, intonation, and pace for the demands of the context, audience, and purpose; effective pronunciation and fluency. "
            
            "Your job is to ensure that the candidate has answered the question correctly and suggest improvements. "
            "Provide feedback in three sections:\n"
            "1. General Comment\n"
            "2. What You Did Well (bullet points)\n"
            "3. What You Could Improve (bullet points)\n\n"

            "**Return your response in JSON format ONLY.**\n"
            "**DO NOT** include any extra text, explanations, or preambles. **ONLY return a JSON object** with the following structure:\n"
            "{\n"
            '"general_comment": "string",\n'
            '"did_well": ["string", "string"],\n'
            '"could_improve": ["string", "string"]\n'
            "}"
        )},
        {"role": "user", "content": f"Here is the candidate's speaking response: {transcription}"}
    ]

    try:
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        raw_feedback = chat_response.choices[0].message.content.strip()
        print(f"Raw GPT-4 response: {raw_feedback}")

        # ✅ Extract JSON object using regex
        json_match = re.search(r'\{.*\}', raw_feedback, re.DOTALL)
        if json_match:
            raw_feedback = json_match.group(0)
            feedback = json.loads(raw_feedback)
            print(f"Parsed feedback: {feedback}")  # Log for verification
        else:
            raise ValueError("Could not find JSON object in GPT-4 response")

    except Exception as e:
        print(f"Error generating feedback: {e}")
        feedback = {
            "general_comment": "Unable to parse feedback. Please check the response.",
            "did_well": [],
            "could_improve": []
        }
    
    # ✅ Determine the next question number
    current_question_number = int(request.form['question_number'])
    next_question_number = current_question_number + 1 if current_question_number < len(questions) else None

    # ✅ Store feedback in session
    session['feedback'] = {
        'question': questions[str(current_question_number)],
        'transcription': transcription,
        'general_comment': feedback['general_comment'],
        'did_well': feedback['did_well'],
        'could_improve': feedback['could_improve'],
        'next_question': f'speaking_task_1_q{next_question_number}' if next_question_number else None
    }

    # ✅ Clean up and delete the audio file
    if os.path.exists(audio_file_path):
        os.remove(audio_file_path)
        print(f"Deleted audio file: {audio_file_path}")

    # ✅ Render the feedback page with all the necessary variables
    return redirect(url_for('speaking.speaking_task_1_feedback'))


@speaking_bp.route('/speaking_task_1_feedback', methods=['GET'])
def speaking_task_1_feedback():
    feedback = session.get('feedback', {})
    question = feedback.get('question', 'Unknown question')
    transcription = feedback.get('transcription', 'No transcription available.')
    general_comment = feedback.get('general_comment', 'No general comment provided.')
    did_well = feedback.get('did_well', [])
    could_improve = feedback.get('could_improve', [])
    next_question = feedback.get('next_question', None)

    return render_template(
        'speaking/speaking_task_1_feedback.html',
        question=question,
        transcription=transcription,
        general_comment=general_comment,
        did_well=did_well,
        could_improve=could_improve,
        next_question=next_question
    )
