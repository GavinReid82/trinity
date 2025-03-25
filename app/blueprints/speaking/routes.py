from flask import Blueprint, render_template, request, session, redirect, url_for, current_app, jsonify, flash
from openai import OpenAI
import json
import os
import re
from werkzeug.utils import secure_filename
from app.blueprints.speaking import speaking_bp
from flask_login import current_user, login_required
from app.models import db, Task, Transcript
from app.blueprints.speaking.utils import save_audio_file, transcribe_audio, generate_feedback


speaking_bp = Blueprint('speaking', __name__, template_folder='templates')

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@speaking_bp.route('/')
def speaking_home():
    return render_template('speaking/home.html')

@speaking_bp.route('/speaking_tips')
def speaking_tips():
    return render_template('speaking/speaking_tips.html')

@speaking_bp.route('/speaking_task_2')
@login_required
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
                           question="What is the best holiday for families with children?", 
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
@login_required
def speaking_task_submit():
    # Initialize client inside the route
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print("="*50)
    print("Starting speaking task submission")
    print(f"Current user ID: {current_user.id}")
    
    # Clear any old feedback from session
    session.pop('feedback', None)
    
    questions = {
        "1": "What is the best holiday for families with children?",
        "2": "What do you do to relax?",
        "3": "I think life is becoming more stressful. Would you agree?"
    }

    # Save the audio file
    audio_path, error = save_audio_file(request)
    if error:
        print(f"Error saving audio: {error}")
        return redirect(url_for('speaking.speaking_task_1_feedback'))

    print(f"Successfully saved audio to: {audio_path}")

    # Transcribe the audio
    transcription, error = transcribe_audio(audio_path)
    if error:
        print(f"Error transcribing: {error}")
        return redirect(url_for('speaking.speaking_task_1_feedback'))

    print(f"Successfully transcribed: {transcription[:100]}...")

    # Generate feedback
    feedback, error = generate_feedback(transcription)
    if error:
        print(f"Error generating feedback: {error}")
        return redirect(url_for('speaking.speaking_task_1_feedback'))

    print(f"Successfully generated feedback: {feedback}")

    try:
        current_question = request.form.get('question_number')
        print(f"Processing question number: {current_question}")

        # Create or get task
        task_name = f"Speaking Task 1 Q{current_question}"
        task = Task.query.filter_by(name=task_name, type='speaking').first()
        if not task:
            print(f"Creating new task: {task_name}")
            task = Task(name=task_name, type='speaking')
            db.session.add(task)
            db.session.flush()  # Get the ID without committing

        # Create transcript
        transcript = Transcript(
            user_id=current_user.id,
            task_id=task.id,
            transcription=transcription,
            feedback=feedback
        )
        db.session.add(transcript)
        db.session.commit()
        print(f"Successfully saved transcript ID: {transcript.id}")

        # Set session data
        next_question_number = int(current_question) + 1 if int(current_question) < len(questions) else None
        session['feedback'] = {
            'question': questions[current_question],
            'transcription': transcription,
            'general_comment': feedback['general_comment'],
            'did_well': feedback['did_well'],
            'could_improve': feedback['could_improve'],
            'next_question': f'speaking.speaking_task_1_q{next_question_number}' if next_question_number else None
        }
        print("Successfully set session feedback")

    except Exception as e:
        print(f"Database error: {str(e)}")
        db.session.rollback()
        return redirect(url_for('speaking.speaking_task_1_feedback'))

    finally:
        # Clean up the audio file
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"Cleaned up audio file: {audio_path}")

    print("="*50)
    return redirect(url_for('speaking.speaking_task_1_feedback'))


@speaking_bp.route('/speaking_task_1_feedback', methods=['GET'])
@login_required
def speaking_task_1_feedback():
    print("="*50)
    print("Retrieving feedback")
    
    questions = {
        "1": "What is the best holiday for families with children?",
        "2": "What do you do to relax?",
        "3": "I think life is becoming more stressful. Would you agree?"
    }
    
    # Try to get feedback from session
    feedback = session.get('feedback', {})
    print(f"Session feedback: {feedback}")
    
    if not feedback:
        print("No session feedback, checking database")
        # Get the question number from the URL parameters
        question_number = request.args.get('question_number', '1')
        task_name = f"Speaking Task 1 Q{question_number}"
        
        # Get the specific task for this question
        speaking_task = Task.query.filter_by(name=task_name, type='speaking').first()
        if speaking_task:
            # Look for transcript for this specific task
            latest_transcript = Transcript.query.filter_by(
                user_id=current_user.id,
                task_id=speaking_task.id
            ).order_by(Transcript.created_at.desc()).first()
            
            if latest_transcript:
                print(f"Found latest transcript ID: {latest_transcript.id}")
                
                # Calculate next question
                next_q = int(question_number) + 1 if int(question_number) < len(questions) else None
                next_question = f'speaking.speaking_task_1_q{next_q}' if next_q else None
                
                feedback = {
                    'question': questions.get(question_number, 'Unknown question'),
                    'question_number': question_number,
                    'transcription': latest_transcript.transcription,
                    'general_comment': latest_transcript.feedback.get('general_comment', ''),
                    'did_well': latest_transcript.feedback.get('did_well', []),
                    'could_improve': latest_transcript.feedback.get('could_improve', []),
                    'next_question': next_question
                }
            else:
                print("No transcript found in database")
        else:
            print("No speaking task found in database")
    
    print(f"Final feedback being rendered: {feedback}")
    print("="*50)
    
    return render_template(
        'speaking/speaking_task_1_feedback.html',
        question=feedback.get('question', 'Unknown question'),
        question_number=feedback.get('question_number', '1'),
        transcription=feedback.get('transcription', 'No transcription available.'),
        general_comment=feedback.get('general_comment', 'No general comment provided.'),
        did_well=feedback.get('did_well', []),
        could_improve=feedback.get('could_improve', []),
        next_question=feedback.get('next_question', None)
    )

@speaking_bp.route('/speaking_task_2_submit', methods=['POST'])
@login_required
def speaking_task_2_submit():
    try:
        stage = request.form.get('stage', 'main')
        
        # Save audio file
        audio_path, error = save_audio_file(request, task_type='task_2', user_id=current_user.id)
        if error:
            return jsonify({'error': error}), 400

        # Transcribe audio
        transcription = transcribe_audio(audio_path)
        if isinstance(transcription, tuple):
            transcription = transcription[0]
        print(f"✅ Transcription: {transcription}")

        # Generate feedback
        feedback, error = generate_feedback(
            transcription=transcription,
            task_type='speaking_2',
            stage=stage
        )
        
        if error:
            return jsonify({'error': error}), 400

        # Get the task_id for speaking_task_2
        task = Task.query.filter_by(name='speaking_task_2').first()
        if not task:
            # Create the task if it doesn't exist
            task = Task(name='speaking_task_2', type='speaking')
            db.session.add(task)
            db.session.commit()

        # For main response
        if stage == 'main':
            transcript = Transcript(
                user_id=current_user.id,
                task_id=task.id,
                transcription=transcription,
                feedback=feedback  # This should work as the column is JSON type
            )
        else:
            # For follow-up, link to the main response
            main_transcript = Transcript.query.filter_by(
                user_id=current_user.id,
                task_id=task.id
            ).filter(Transcript.main_transcript_id.is_(None)).order_by(Transcript.created_at.desc()).first()

            transcript = Transcript(
                user_id=current_user.id,
                task_id=task.id,
                transcription=transcription,
                feedback=feedback,
                main_transcript_id=main_transcript.id if main_transcript else None
            )

        db.session.add(transcript)
        db.session.commit()

        # Clean up the audio file
        try:
            os.remove(audio_path)
        except Exception as e:
            print(f"Warning: Could not delete audio file: {e}")

        # Return response based on stage
        if stage == 'main':
            return jsonify({
                'success': True,
                'feedback': feedback,
                'follow_up_question': "What advice do you have for someone who wants to learn more about this topic?"
            })
        else:
            return jsonify({
                'success': True,
                'feedback': feedback
            })

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@speaking_bp.route('/speaking_task_2_feedback')
@login_required
def speaking_task_2_feedback():
    task = Task.query.filter_by(name='speaking_task_2').first()
    if not task:
        flash('Task not found.', 'error')
        return redirect(url_for('speaking.speaking_task_2'))

    # Get the main response (one without a main_transcript_id)
    main_transcript = Transcript.query.filter_by(
        user_id=current_user.id,
        task_id=task.id
    ).filter(Transcript.main_transcript_id.is_(None)).order_by(Transcript.created_at.desc()).first()

    # Get the follow-up response (linked to the main response)
    follow_up_transcript = None
    if main_transcript:
        follow_up_transcript = Transcript.query.filter_by(
            main_transcript_id=main_transcript.id
        ).order_by(Transcript.created_at.desc()).first()

    context = {
        'main_response': main_transcript.transcription if main_transcript else None,
        'main_feedback': main_transcript.feedback if main_transcript else None,
        'follow_up_response': follow_up_transcript.transcription if follow_up_transcript else None,
        'follow_up_feedback': follow_up_transcript.feedback if follow_up_transcript else None,
        'follow_up_question': "What advice do you have for someone who wants to learn more about this topic?"
    }
    
    return render_template('speaking/speaking_task_2_feedback.html', **context)
