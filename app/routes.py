import json
from flask import render_template, request, jsonify, url_for, redirect, session
from app import app
from openai import OpenAI
import re
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --------------------------------------- Welcome ---------------------------------------

@app.route('/')
def welcome():
    template_path = os.path.abspath('app/templates/layout.html')
    print(f"Loading template: {template_path}")
    return render_template('welcome.html')

@app.route('/reading')
def reading():
    return render_template('reading.html')

@app.route('/writing')
def writing():
    return render_template('writing_task_1_group_chat.html')

@app.route('/speaking')
def speaking():
    return render_template('speaking.html')

@app.route('/listening')
def listening():
    return render_template('listening.html')



# --------------------------------------- Writing ---------------------------------------
@app.route('/writing_tips')
def writing_tips():
    return render_template('writing_tips.html')

@app.route('/writing_task_1_group_chat')
def writing_task_1_group_chat():
    return render_template('writing_task_1_group_chat.html')

@app.route('/writing_task_2_essay')
def writing_task_2_essay():
    return render_template('writing_task_2_essay.html')

@app.route('/writing_task_2_report')
def writing_task_2_report():
    return render_template('writing_task_2_report.html')

@app.route('/writing_task_1_submit', methods=['POST'])
def writing_task_1_submit():
    # Get the user's response from the form
    response = request.form.get('writingTask1')
    
    # Define the custom assistant behavior
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
                "Structure your feedback into three sections: "
                "1. General Comment, 2. What You Did Well (bullet points), and 3. What You Could Improve (bullet points). "
                "Return the feedback as JSON with keys: 'general_comment', 'did_well', and 'could_improve'."
            )
        },
        {"role": "user", "content": f"Here is the candidate's submission:\n\n{response}"}
    ]
    
    # Use the new API structure to create a chat completion
    openai_response = client.chat.completions.create(
        model="gpt-4",  # Use "gpt-3.5-turbo" if applicable
        messages=messages,
        temperature=0.7,
        max_tokens=400
    )
    
    # Extract feedback from the response
    raw_feedback = openai_response.choices[0].message.content.strip()
    
    try:
        feedback = json.loads(raw_feedback)
    except json.JSONDecodeError:
        feedback = {
            "general_comment": "Unable to parse feedback. Please check the response.",
            "did_well": [],
            "could_improve": []
        }
    
    return render_template(
        'writing_task_1_feedback.html',
        response=response,
        general_comment=feedback.get('general_comment', ''),
        did_well=feedback.get('did_well', []),
        could_improve=feedback.get('could_improve', [])
    )


# --------------------------------------- Speaking ---------------------------------------

@app.route('/speaking_tips')
def speaking_tips():
    return render_template('speaking_tips.html')

@app.route('/speaking_task_2')
def speaking_task_2():
    return render_template('speaking_task_2.html')

@app.route('/speaking_task_3')
def speaking_task_3():
    return render_template('speaking_task_3.html')

@app.route('/speaking_task_4')
def speaking_task_4():
    return render_template('speaking_task_4.html')

@app.route('/speaking_task_1_q1')
def speaking_task_1_q1():
    return render_template('speaking_task_1.html', 
                           question="I'm planning to take my family on holiday next year. What kind of holiday is best and why?", 
                           question_number=1)


@app.route('/speaking_task_1_q2')
def speaking_task_1_q2():
    return render_template('speaking_task_1.html', 
                           question="What do you do to relax?", 
                           question_number=2)


@app.route('/speaking_task_1_q3')
def speaking_task_1_q3():
    return render_template('speaking_task_1.html', 
                           question="I think life is becoming more stressful. Would you agree?", 
                           question_number=3)


@app.route('/speaking_task_submit', methods=['POST'])
def speaking_task_submit():
    print(f"Request form keys: {request.form.keys()}")
    print(f"Request files: {request.files.keys()}")

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
    return redirect(url_for('speaking_task_1_feedback'))


@app.route('/speaking_task_1_feedback', methods=['GET'])
def speaking_task_1_feedback():
    feedback = session.get('feedback', {})
    question = feedback.get('question', 'Unknown question')
    transcription = feedback.get('transcription', 'No transcription available.')
    general_comment = feedback.get('general_comment', 'No general comment provided.')
    did_well = feedback.get('did_well', [])
    could_improve = feedback.get('could_improve', [])
    next_question = feedback.get('next_question', None)

    return render_template(
        'speaking_task_1_feedback.html',
        question=question,
        transcription=transcription,
        general_comment=general_comment,
        did_well=did_well,
        could_improve=could_improve,
        next_question=next_question
    )
