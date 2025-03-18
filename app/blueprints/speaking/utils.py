import os
import json
import re
from flask import current_app
from werkzeug.utils import secure_filename
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def save_audio_file(request):
    """Handles file upload and saves it to the uploads folder."""
    if 'audio_file' not in request.files:
        return None, "No file uploaded."

    file = request.files['audio_file']
    filename = secure_filename(f"candidate_q{request.form['question_number']}.webm")
    audio_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    try:
        file.save(audio_file_path)
        print(f"✅ Audio file saved: {audio_file_path}")
        return audio_file_path, None
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return None, "Failed to save audio file."


def transcribe_audio(audio_path):
    """Transcribes an audio file using OpenAI Whisper."""
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


def generate_feedback(transcription):
    """Sends transcription to GPT-4 and extracts structured feedback."""
    messages = [
        {"role": "system", "content": (
            "You are an instructor for Trinity's ISE Digital Speaking exam. "
            "Your job is to give feedback based on the candidate's response, "
            "following the guidelines below. Return only a valid JSON object."
        )},
        {"role": "user", "content": f"Candidate's response:\n\n{transcription}"}
    ]

    try:
        chat_response = client.chat.completions.create(
            model="gpt-4", messages=messages, temperature=0.7, max_tokens=500
        )
        raw_feedback = chat_response.choices[0].message.content.strip()

        json_match = re.search(r'\{.*\}', raw_feedback, re.DOTALL)
        if json_match:
            feedback = json.loads(json_match.group(0))
            print(f"✅ Parsed feedback: {feedback}")
            return feedback, None
        else:
            raise ValueError("Could not extract valid JSON.")

    except Exception as e:
        print(f"❌ Error generating feedback: {e}")
        return {
            "general_comment": "Unable to parse feedback. Please check the response.",
            "did_well": [],
            "could_improve": []
        }, "Error processing feedback."
