import os
import json
import re
from flask import current_app
from werkzeug.utils import secure_filename
from openai import OpenAI
import openai


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
        Use the following criteria to guide your feedback:
        - Response fully addresses the task; all parts of task covered comprehensively.
        - Ideas are relevant, clear and well supported by detail.
        - Excellent coherence; response is well organised and progression of ideas is clear and logical.
        - Response is comprehensive and concludes naturally in the time allowed.

        Give feedback in the following JSON format:
            {
                "general_comment": "Overall assessment of the response",
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
            # Provide a generic structured feedback if JSON parsing fails
            return {
                "general_comment": "Your response needs to be more focused on addressing the task requirements.",
                "did_well": [
                    "You attempted to address the topic",
                    "You expressed your ideas in English"
                ],
                "can_improve": [
                    "Provide more specific details to support your points",
                    "Structure your response more clearly",
                    "Stay focused on addressing the task requirements"
                ]
            }, None

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


def generate_followup_feedback(main_transcription, followup_transcription, follow_up_question=None, task_type='speaking_2'):
    """Generate feedback specifically for follow-up responses by checking relevance to main talk and question"""
    print(f"\n=== generate_followup_feedback ===")
    print(f"Task type: {task_type}")
    print(f"Main transcription length: {len(main_transcription)}")
    print(f"Follow-up transcription length: {len(followup_transcription)}")
    print(f"Follow-up question: {follow_up_question}")
    
    try:
        # Choose the appropriate system prompt based on the task type
        if task_type == 'speaking_4':
            system_prompt = """You are an English speaking examiner.
            You have been given:
            1. The candidate's summary of a lecture/talk they listened to
            2. A follow-up question about pollution in cities
            3. The candidate's follow-up response to that question
            
            Analyze these elements and assess how well the follow-up response:
            - Directly addresses the specific follow-up question about reducing pollution
            - Provides relevant and practical suggestions for reducing pollution
            - Demonstrates understanding of environmental issues in urban contexts
            - Presents ideas that are logically organized and well-supported
            
            Address the candidate as "you" and use the word "you" in your response.
            Write in British English.
            Use the following criteria to guide your feedback:
            - Question relevance: The follow-up response directly answers the question about pollution
            - Content quality: The suggestions provided are practical, specific and well-explained
            - Organization: Ideas are presented in a logical sequence with clear progression
            - Support: Suggestions are supported with reasons or examples
            
            Give feedback in the following JSON format:
                {
                    "general_comment": "Overall assessment of the response to the pollution question",
                    "did_well": ["Point 1 about pollution response strengths", "Point 2"],
                    "can_improve": ["Area 1 to improve in pollution response", "Area 2"]
                }"""
        elif task_type == 'speaking_3':
            system_prompt = """You are an English speaking examiner.
            You have been given:
            1. The candidate's response about a group project experience
            2. A follow-up question about improving future group work
            3. The candidate's follow-up response to that question
            
            Analyze these elements and assess how well the follow-up response:
            - Directly addresses how to improve future group performance
            - Shows understanding of group dynamics and collaboration
            - Provides practical and specific suggestions for improvement
            - Demonstrates reflection on the main discussion
            
            Address the candidate as "you" and use the word "you" in your response.
            Write in British English.
            Use the following criteria to guide your feedback:
            - Question relevance: The follow-up response directly addresses future improvement
            - Content quality: The suggestions are practical and well-explained
            - Connection: Ideas connect logically to the main discussion
            - Reflection: Shows thoughtful consideration of group work challenges
            
            Give feedback in the following JSON format:
                {
                    "general_comment": "Overall assessment of the improvement suggestions",
                    "did_well": ["Point 1 about response strengths", "Point 2"],
                    "can_improve": ["Area 1 to improve", "Area 2"]
                }"""
        else:  # Default for speaking_2
            system_prompt = """You are an English speaking examiner.
            You have been given:
            1. The candidate's main prepared talk
            2. A follow-up question about their talk
            3. The candidate's follow-up response to that question
            
            Analyze these elements and assess how well the follow-up response:
            - Directly addresses the specific follow-up question asked
            - Maintains consistency with the main talk
            - Appropriately builds upon or extends ideas from the main talk
            - Demonstrates understanding of the relationship between the question and the main talk
            
            Address the candidate as "you" and use the word "you" in your response.
            Write in British English.
            Use the following criteria to guide your feedback:
            - Question relevance: The follow-up response directly answers the specific question
            - Content relevance: The follow-up response aligns logically with the main talk
            - Extension of ideas: The follow-up builds upon rather than simply repeats the main talk
            - Cohesion: The candidate creates clear links between the follow-up and main talk
            
            Give feedback in the following JSON format:
                {
                    "general_comment": "Overall assessment that mentions both the question and main talk",
                    "did_well": ["Point 1 about relevance to question/talk", "Point 2"],
                    "can_improve": ["Area 1 to improve relevance", "Area 2"]
                }"""

        # Add the follow-up question to the user content if it's provided
        user_content = f"Main talk/summary: {main_transcription}\n\n"
        if follow_up_question:
            user_content += f"Follow-up question: {follow_up_question}\n\n"
        user_content += f"Follow-up response: {followup_transcription}"

        response = OpenAI(api_key=os.getenv("OPENAI_API_KEY")).chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
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
        print(f"Error generating follow-up feedback: {str(e)}")
        return None, str(e)


def generate_task_4_feedback(user_transcription, discussion_transcript):
    """Generate feedback for Task 4 summary, comparing against the discussion."""
    print(f"\n=== generate_task_4_feedback ===") # Add logging
    print(f"User transcription length: {len(user_transcription)}")
    print(f"Discussion transcript length: {len(discussion_transcript)}")
    
    # Initialize the OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Ensure client is initialized

    try:
        # Define the system prompt for the AI
        system_prompt = """You are an English speaking examiner. 
        You have been given:
        1. A transcript of a podcast discussion about the benefits of city trees.
        2. A student's summary of that discussion.
        
        Your task is to evaluate the student's summary based ONLY on how well it reflects the content of the provided discussion transcript. 
        Provide feedback in British English, addressing the student as "you".
        Focus ONLY on task achievement: Did the summary accurately and completely capture the main points of the discussion?
        
        Use the following criteria:
        - Accuracy: Does the summary accurately reflect the key points about trees cleaning air, reducing temperatures, and the Abu Dhabi example?
        - Completeness: Does the summary cover the main benefits mentioned in the discussion?
        - Relevance: Does the summary stick to the points made in the discussion transcript?

        Provide feedback in the following JSON format ONLY:
            {
                "general_comment": "Overall assessment of the summary's accuracy and completeness compared to the discussion.",
                "did_well": ["Specific point from the summary that accurately reflects the discussion", "Another accurate point"],
                "can_improve": ["Specific point missed or misrepresented from the discussion", "Suggestion for better accuracy/completeness"]
            }"""

        # Construct the user content
        user_content = (
            f"Discussion transcript:\n'''\n{discussion_transcript}\n'''\n\n"
            f"Student's summary:\n'''\n{user_transcription}\n'''"
        )
        
        print("Sending request to OpenAI API for Task 4 feedback...")
        # *** REMOVED response_format parameter ***
        response = client.chat.completions.create(
            model="gpt-4", # Or "gpt-3.5-turbo" if preferred
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.5 # Adjust temperature as needed
            # response_format={"type": "json_object"} # REMOVED THIS LINE
        )

        # Extract the feedback from the response
        feedback_content = response.choices[0].message.content
        print(f"Raw OpenAI response content: {feedback_content}") # Log the raw response

        # Parse the feedback into JSON
        try:
            # Attempt to find JSON block even if there's surrounding text
            json_match = re.search(r"\{.*\}", feedback_content, re.DOTALL)
            if json_match:
                feedback_dict = json.loads(json_match.group(0))
                print("Successfully parsed JSON feedback.")
                return feedback_dict, None
            else:
                raise json.JSONDecodeError("No JSON object found in the response", feedback_content, 0)

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw GPT response content that failed parsing: {feedback_content}")
            # Fallback feedback if JSON parsing fails
            return {
                "general_comment": "Could not reliably parse the feedback structure. Please review your summary against the discussion points.",
                "did_well": [],
                "can_improve": ["Ensure your summary accurately reflects the main points of the provided discussion about city trees."]
            }, "Error parsing feedback JSON"

    except Exception as e:
        print(f"Error generating task 4 feedback: {str(e)}")
        import traceback
        print(traceback.format_exc()) # Print full traceback
        return None, f"Error generating feedback: {str(e)}"

