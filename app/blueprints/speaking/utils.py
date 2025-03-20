import os
import json
import re
from flask import current_app
from werkzeug.utils import secure_filename
from openai import OpenAI


def save_audio_file(request, task_type='task_1', user_id=None):
    """Save audio file with appropriate naming based on task type"""
    print(f"\n=== save_audio_file ===")
    print(f"Task type: {task_type}")
    print(f"User ID: {user_id}")
    
    try:
        if 'audio_file' not in request.files:
            print("No audio_file in request.files")
            return None, "No audio file provided"
            
        audio_file = request.files['audio_file']
        print(f"Audio file name: {audio_file.filename}")
        
        if audio_file.filename == '':
            print("Empty filename")
            return None, "No selected file"

        if task_type == 'task_1':
            filename = secure_filename(f"candidate_q{request.form['question_number']}.webm")
        else:
            stage = request.form.get('stage', 'main')
            filename = secure_filename(f"speaking_task_2_{stage}_{user_id}.webm")
        
        print(f"Generated filename: {filename}")
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        print(f"Upload folder: {upload_folder}")
        
        audio_path = os.path.join(upload_folder, filename)
        print(f"Full audio path: {audio_path}")
        
        audio_file.save(audio_path)
        print("File saved successfully")
        
        return audio_path, None

    except Exception as e:
        import traceback
        print(f"Exception in save_audio_file: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return None, str(e)


def transcribe_audio(audio_path):
    """Transcribes an audio file using OpenAI Whisper."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="text"
            )
        transcription = response.strip()
        print(f"✅ Transcription: {transcription}")
        return transcription, None
    except Exception as e:
        print(f"❌ Error transcribing audio: {e}")
        return None, "Audio transcription failed."


def generate_feedback(transcription, task_type='speaking_1', stage='main'):
    """Generate feedback for speaking tasks"""
    print(f"\n=== generate_feedback ===")
    print(f"Task type: {task_type}")
    print(f"Stage: {stage}")
    print(f"Transcription: {transcription}")
    
    try:
        system_prompt = """You are an English speaking examiner. 
        Analyze the candidate's response and provide feedback in British English.
        Address the candidate as "you" and use the word "you" in your response.
        Feedback should be given only on task achievement and should give helpful suggestions on how to improve.
        Use the following top-levelcriteria to guide your feedback:
        - Response fully addresses the task; all parts of task covered comprehensively.
        - Ideas are relevant, clear and well supported by detail.
        - Excellent coherence; response is well organised and progression of ideas is clear and logical.
        - Response is comprehensive and concludes naturally in the time allowed.

        Give feedbackin the following JSON format:
            {
                "general_comment": "Overall assessment of the follow-up response",
                "did_well": ["Point 1", "Point 2"],
                "can_improve": ["Area 1", "Area 2"]
            }"""

        response = OpenAI(api_key=os.getenv("OPENAI_API_KEY")).chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Candidate's response: {transcription}"}
            ],
            temperature=0.7
        )

        feedback = response.choices[0].message.content
        try:
            # Ensure the response is valid JSON
            feedback_dict = json.loads(feedback)
            return feedback_dict, None
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw GPT response: {feedback}")
            return {
                "general_comment": "Error processing feedback",
                "did_well": [],
                "can_improve": ["Unable to process feedback. Please try again."]
            }, "Error parsing feedback"

    except Exception as e:
        print(f"Error generating feedback: {str(e)}")
        return None, str(e)
    


def generate_follow_up_question(transcription):
    """Generate a relevant follow-up question based on the main response"""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    messages = [
        {"role": "system", "content": "Generate a single follow-up question based on the speaker's response about a place they visited. The question should be specific to their response and encourage them to expand on one aspect they mentioned."},
        {"role": "user", "content": transcription}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating follow-up: {e}")
        return "Could you tell me more about what you enjoyed most about this place?"

