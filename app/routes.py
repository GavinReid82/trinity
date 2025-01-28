import json
from flask import render_template, request, jsonify
from app import app
from openai import OpenAI
import base64
from dotenv import load_dotenv
import os
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client = OpenAI(
    api_key=OPENAI_API_KEY  # Replace with your actual OpenAI API key
)


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
    question_number = int(request.form['question_number'])
    audio_data = request.form['audio_data']

    print(f"Received audio_data: {audio_data}")

    # Validate the audio_data
    if not audio_data or "," not in audio_data:
        return jsonify({"error": "Invalid or missing audio data"}), 400

    # Define questions
    questions = {
        1: "I'm planning to take my family on holiday next year. What kind of holiday is best and why?",
        2: "What do you do to relax?",
        3: "I think life is becoming more stressful. Would you agree?"
    }
    
    # Decode and save audio file
    audio_content = audio_data.split(",")[1]
    audio_dir = "uploads"
    os.makedirs(audio_dir, exist_ok=True)
    audio_file_path = os.path.join(audio_dir, f"candidate_12345_q{question_number}.wav")

    with open(audio_file_path, "wb") as audio_file:
        audio_file.write(base64.b64decode(audio_content))

    # Send audio to OpenAI Whisper for transcription
    with open(audio_file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )

    transcription = response

    # Process transcription with GPT for feedback
    messages = [
        {"role": "system", "content": (
            "You are an instructor for Trinity's ISE Digital Speaking exam. "
            "Your job is to give feedback to candidates based on their performance, following the guidelines below. "
            "Write in British English at all times. Your feedback language should be simple enough for a grade 5 (or A2 on CEFR) to understand.\n\n"

            "Candidates are graded on the following: "
            "1. Task fulfilment: Ability to respond to task with relevant details, organise ideas coherently and respond fully in the time allowed (30 seconds per question). "
            "2. Language: Ability to use a range of grammar and lexis accurately and effectively. "
            "3. Delivery: Ability to use stress, intonation and pace for the demands of the context, audience and purpose; effective pronunciation and fluency. "
            
            "Your job is principally to ensure that the candidate has answered the question correctly and suggest improvements. "
            "Provide feedback in three sections: 1. General Comment, 2. What You Did Well (bullet points), and 3. What You Could Improve (bullet points). "
            "Return the feedback as JSON with keys: 'general_comment', 'did_well', and 'could_improve'."
        )},
        {"role": "user", "content": f"Here is the candidate's speaking response: {transcription}"}
    ]

    chat_response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )

    raw_feedback = chat_response.choices[0].message.content.strip()

    try:
        feedback = json.loads(raw_feedback)
    except json.JSONDecodeError:
        feedback = {
            "general_comment": "Unable to parse feedback. Please check the response.",
            "did_well": [],
            "could_improve": []
        }

    os.remove(audio_file_path)

    # Determine next question route
    next_question = None
    if question_number < 3:
        next_question = f"speaking_task_1_q{question_number + 1}"

    return render_template(
        'speaking_task_1_feedback.html',
        question=questions[question_number],
        transcription=transcription,
        general_comment=feedback.get('general_comment', 'No general comment provided.'),
        did_well=feedback.get('did_well', []),
        could_improve=feedback.get('could_improve', []),
        next_question=next_question
    )
