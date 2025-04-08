from flask import Blueprint, render_template, request, session, redirect, url_for, current_app, jsonify, flash
from openai import OpenAI
import json
import os
import re
from werkzeug.utils import secure_filename
from app.blueprints.speaking import speaking_bp
from flask_login import current_user, login_required
from app.models import db, Task, Transcript
from app.blueprints.speaking.utils import save_audio_file, transcribe_audio, generate_feedback, generate_followup_feedback


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
    print("="*50)
    print("Starting speaking task submission")
    print(f"Current user ID: {current_user.id}")
    
    try:
        questions = {
            "1": "What do you like to do when you meet your friends?",
            "2": "I enjoy reading poetry. What do you like to read?",
            "3": "Do you think the Internet will replace books as a source of information? Why or why not?"
        }

        # Save the audio file
        audio_path, error = save_audio_file(request)
        if error:
            print(f"Error saving audio: {error}")
            return jsonify({'error': error}), 400

        print(f"Successfully saved audio to: {audio_path}")

        # Transcribe the audio
        transcription, error = transcribe_audio(audio_path)
        if error:
            print(f"Error transcribing: {error}")
            return jsonify({'error': error}), 400

        print(f"Successfully transcribed: {transcription[:100]}...")

        # Generate feedback
        feedback, error = generate_feedback(transcription)
        if error:
            print(f"Error generating feedback: {error}")
            return jsonify({'error': error}), 400

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
                db.session.flush()

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

            # Store in session for final feedback
            if 'task1_responses' not in session:
                session['task1_responses'] = []
            
            session['task1_responses'].append({
                'question': questions[current_question],
                'question_number': current_question,
                'transcription': transcription,
                'feedback': feedback
            })
            session.modified = True

            return jsonify({
                'success': True,
                'feedback': feedback,
                'question': questions[current_question]
            })

        except Exception as e:
            print(f"Database error: {str(e)}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

        finally:
            # Clean up the audio file
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"Cleaned up audio file: {audio_path}")

    except Exception as e:
        print(f"Error in speaking_task_submit: {str(e)}")
        return jsonify({'error': str(e)}), 500


@speaking_bp.route('/speaking_task_1_feedback')
@login_required
def speaking_task_1_feedback():
    print("="*50)
    print("Retrieving feedback")
    
    # Get all responses from session
    feedback_list = session.get('task1_responses', [])
    print(f"Session feedback list: {feedback_list}")
    
    if not feedback_list:
        print("No session feedback, checking database")
        feedback_list = []
        
        # Get feedback for all questions from database
        for q_num in range(1, 4):
            task_name = f"Speaking Task 1 Q{q_num}"
            task = Task.query.filter_by(name=task_name, type='speaking').first()
            
            if task:
                transcript = Transcript.query.filter_by(
                    user_id=current_user.id,
                    task_id=task.id
                ).order_by(Transcript.created_at.desc()).first()
                
                if transcript:
                    feedback_list.append({
                        'question_number': q_num,
                        'question': {
                            "1": "What do you like to do when you meet your friends?",
                            "2": "I enjoy reading poetry. What do you like to read?",
                            "3": "Do you think the Internet will replace books as a source of information? Why or why not?"
                        }[str(q_num)],
                        'transcription': transcript.transcription,
                        'feedback': transcript.feedback
                    })
    
    print(f"Final feedback list being rendered: {feedback_list}")
    print("="*50)
    
    return render_template(
        'speaking/speaking_task_1_feedback.html',
        feedback_list=feedback_list
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

        # Get the task_id for speaking_task_2
        task = Task.query.filter_by(name='speaking_task_2').first()
        if not task:
            # Create the task if it doesn't exist
            task = Task(name='speaking_task_2', type='speaking')
            db.session.add(task)
            db.session.commit()

        # Generate appropriate feedback based on stage
        if stage == 'main':
            # Generate regular feedback for main talk
            feedback, error = generate_feedback(
                transcription=transcription,
                task_type='speaking_2',
                stage=stage
            )
            
            if error:
                return jsonify({'error': error}), 400

            # Define follow-up question (either hardcoded or generated)
            follow_up_question = "What advice do you have for someone who wants to learn more about this topic?"
            
            # Create transcript for main response
            transcript = Transcript(
                user_id=current_user.id,
                task_id=task.id,
                transcription=transcription,
                feedback=feedback,
                # You might need to add this field to your model
                # follow_up_question=follow_up_question  
            )
            db.session.add(transcript)
            db.session.commit()
            
            # Store the follow-up question in session for later use
            session['follow_up_question'] = follow_up_question
            
            return jsonify({
                'success': True,
                'feedback': feedback,
                'follow_up_question': follow_up_question
            })
        else:
            # For follow-up, get the main response to check consistency
            main_transcript = Transcript.query.filter_by(
                user_id=current_user.id,
                task_id=task.id
            ).filter(Transcript.main_transcript_id.is_(None)).order_by(Transcript.created_at.desc()).first()

            if not main_transcript:
                return jsonify({'error': 'No main response found'}), 400
            
            # Get the follow-up question from session or use default
            follow_up_question = session.get('follow_up_question', 
                "What advice do you have for someone who wants to learn more about this topic?")

            # Generate specialized follow-up feedback
            feedback, error = generate_followup_feedback(
                main_transcription=main_transcript.transcription,
                followup_transcription=transcription,
                follow_up_question=follow_up_question,
                task_type='speaking_2'
            )
            
            if error:
                return jsonify({'error': error}), 400

            # Create transcript for follow-up
            transcript = Transcript(
                user_id=current_user.id,
                task_id=task.id,
                transcription=transcription,
                feedback=feedback,
                main_transcript_id=main_transcript.id
            )
            db.session.add(transcript)
            db.session.commit()
            
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
        'follow_up_question': "Will you still find this interesting in 10 years?"
    }
    
    return render_template('speaking/speaking_task_2_feedback.html', **context)

@speaking_bp.route('/speaking_task_3_submit', methods=['POST'])
@login_required
def speaking_task_3_submit():
    try:
        stage = request.form.get('stage', 'main')
        
        # Save audio file
        audio_path, error = save_audio_file(request, task_type='task_3', user_id=current_user.id)
        if error:
            return jsonify({'error': error}), 400

        # Transcribe audio
        transcription, error = transcribe_audio(audio_path)
        if error:
            return jsonify({'error': error}), 400

        # Generate feedback
        feedback, error = generate_feedback(
            transcription=transcription,
            task_type='speaking_3',
            stage=stage
        )
        
        if error:
            return jsonify({'error': error}), 400

        # Get or create the task
        task = Task.query.filter_by(name='speaking_task_3').first()
        if not task:
            task = Task(name='speaking_task_3', type='speaking')
            db.session.add(task)
            db.session.commit()

        # Create transcript record
        if stage == 'main':
            transcript = Transcript(
                user_id=current_user.id,
                task_id=task.id,
                transcription=transcription,
                feedback=feedback
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

        # Clean up audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return jsonify({
            'success': True,
            'feedback': feedback
        })

    except Exception as e:
        print(f"Error in speaking_task_3_submit: {str(e)}")
        return jsonify({'error': str(e)}), 500

@speaking_bp.route('/speaking_task_3_feedback')
@login_required
def speaking_task_3_feedback():
    task = Task.query.filter_by(name='speaking_task_3').first()
    if not task:
        flash('Task not found.', 'error')
        return redirect(url_for('speaking.speaking_task_3'))

    # Get the main response
    main_transcript = Transcript.query.filter_by(
        user_id=current_user.id,
        task_id=task.id
    ).filter(Transcript.main_transcript_id.is_(None)).order_by(Transcript.created_at.desc()).first()

    # Get the follow-up response
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
        'follow_up_question': "Follow-up question from the video"
    }
    
    return render_template('speaking/speaking_task_3_feedback.html', **context)

@speaking_bp.route('/speaking_task_1_submit_all', methods=['POST'])
@login_required
def speaking_task_1_submit_all():
    try:
        all_feedback = []
        questions = {
            "1": "What do you like to do when you meet your friends?",
            "2": "I enjoy reading poetry. What do you like to read?",
            "3": "Do you think the Internet will replace books as a source of information? Why or why not?"
        }

        for q_num in range(1, 4):
            audio_file_key = f'audio_file_{q_num}'
            if audio_file_key not in request.files:
                return jsonify({'error': f'Missing audio file for question {q_num}'}), 400

            # Save the audio file
            audio_path, error = save_audio_file(request, file_key=audio_file_key)
            if error:
                return jsonify({'error': error}), 400

            # Transcribe the audio
            transcription, error = transcribe_audio(audio_path)
            if error:
                return jsonify({'error': error}), 400

            # Generate feedback
            feedback, error = generate_feedback(transcription)
            if error:
                return jsonify({'error': error}), 400

            # Create or get task
            task_name = f"Speaking Task 1 Q{q_num}"
            task = Task.query.filter_by(name=task_name, type='speaking').first()
            if not task:
                task = Task(name=task_name, type='speaking')
                db.session.add(task)
                db.session.flush()

            # Create transcript
            transcript = Transcript(
                user_id=current_user.id,
                task_id=task.id,
                transcription=transcription,
                feedback=feedback
            )
            db.session.add(transcript)

            # Store feedback for session
            all_feedback.append({
                'question': questions[str(q_num)],
                'question_number': q_num,
                'transcription': transcription,
                'feedback': feedback
            })

            # Clean up audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)

        db.session.commit()
        session['all_feedback'] = all_feedback
        
        return jsonify({'success': True})

    except Exception as e:
        print(f"Error in speaking_task_1_submit_all: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@speaking_bp.route('/speaking_task_1_feedback_all')
@login_required
def speaking_task_1_feedback_all():
    all_feedback = session.get('all_feedback', [])
    if not all_feedback:
        flash('No feedback available. Please complete the speaking task first.', 'error')
        return redirect(url_for('speaking.speaking_task_1_q1'))
    
    return render_template('speaking/speaking_task_1_feedback_all.html', feedback_list=all_feedback)

@speaking_bp.route('/speaking_task_1_transcribe', methods=['POST'])
@login_required
def speaking_task_1_transcribe():
    try:
        # Save the audio file
        audio_path, error = save_audio_file(request)
        if error:
            return jsonify({'error': error}), 400

        # Transcribe the audio
        transcription, error = transcribe_audio(audio_path)
        if error:
            return jsonify({'error': error}), 400

        current_question = request.form.get('question_number')

        # Create or get task
        task_name = f"Speaking Task 1 Q{current_question}"
        task = Task.query.filter_by(name=task_name, type='speaking').first()
        if not task:
            task = Task(name=task_name, type='speaking')
            db.session.add(task)
            db.session.flush()

        # Create transcript without feedback initially
        transcript = Transcript(
            user_id=current_user.id,
            task_id=task.id,
            transcription=transcription,
            feedback={}  # Empty feedback for now
        )
        db.session.add(transcript)
        db.session.commit()

        # Clean up audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error in speaking_task_1_transcribe: {str(e)}")
        return jsonify({'error': str(e)}), 500

@speaking_bp.route('/speaking_task_1_generate_feedback', methods=['POST'])
@login_required
def speaking_task_1_generate_feedback():
    try:
        questions = {
            "1": "What do you like to do when you meet your friends?",
            "2": "I enjoy reading poetry. What do you like to read?",
            "3": "Do you think the Internet will replace books as a source of information? Why or why not?"
        }

        all_feedback = []
        
        # Get all transcripts for this task
        for q_num in range(1, 4):
            task_name = f"Speaking Task 1 Q{q_num}"
            task = Task.query.filter_by(name=task_name, type='speaking').first()
            
            if task:
                transcript = Transcript.query.filter_by(
                    user_id=current_user.id,
                    task_id=task.id
                ).order_by(Transcript.created_at.desc()).first()

                if transcript:
                    # Generate feedback for this transcript
                    feedback, error = generate_feedback(transcript.transcription)
                    if error:
                        return jsonify({'error': error}), 400

                    # Update transcript with feedback
                    transcript.feedback = feedback
                    
                    # Store for session
                    all_feedback.append({
                        'question': questions[str(q_num)],
                        'question_number': q_num,
                        'transcription': transcript.transcription,
                        'feedback': feedback
                    })

        # Save all updates
        db.session.commit()

        # Store in session for feedback page
        session['task1_responses'] = all_feedback
        session.modified = True

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error in speaking_task_1_generate_feedback: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@speaking_bp.route('/speaking_task_4_submit', methods=['POST'])
@login_required
def speaking_task_4_submit():
    try:
        stage = request.form.get('stage', 'main')
        
        # Save audio file
        audio_path, error = save_audio_file(request, task_type='task_4', user_id=current_user.id)
        if error:
            return jsonify({'error': error}), 400

        # Transcribe audio
        transcription, error = transcribe_audio(audio_path)
        if error:
            return jsonify({'error': error}), 400

        # Get the task_id for speaking_task_4
        task = Task.query.filter_by(name='speaking_task_4').first()
        if not task:
            # Create the task if it doesn't exist
            task = Task(name='speaking_task_4', type='speaking')
            db.session.add(task)
            db.session.commit()

        # Generate appropriate feedback based on stage
        if stage == 'main':
            # Generate regular feedback for the summary
            feedback, error = generate_feedback(
                transcription=transcription,
                task_type='speaking_4',
                stage=stage
            )
            
            if error:
                return jsonify({'error': error}), 400

            # Define follow-up question (fixed for Task 4)
            follow_up_question = "What other steps could be taken to reduce pollution in cities?"
            
            # Create transcript for main response
            transcript = Transcript(
                user_id=current_user.id,
                task_id=task.id,
                transcription=transcription,
                feedback=feedback
            )
            db.session.add(transcript)
            db.session.commit()
            
            # Store the follow-up question in session for later use
            session['task4_follow_up_question'] = follow_up_question
            
            return jsonify({
                'success': True,
                'feedback': feedback,
                'follow_up_question': follow_up_question
            })
        else:
            # For follow-up, get the main response
            main_transcript = Transcript.query.filter_by(
                user_id=current_user.id,
                task_id=task.id
            ).filter(Transcript.main_transcript_id.is_(None)).order_by(Transcript.created_at.desc()).first()

            if not main_transcript:
                return jsonify({'error': 'No main response found'}), 400
            
            # Get the follow-up question from session or use default
            follow_up_question = session.get('task4_follow_up_question', 
                "What other steps could be taken to reduce pollution in cities?")

            # Generate specialized follow-up feedback
            feedback, error = generate_followup_feedback(
                main_transcription=main_transcript.transcription,
                followup_transcription=transcription,
                follow_up_question=follow_up_question,
                task_type='speaking_4'  # Specify task_type for appropriate feedback
            )
            
            if error:
                return jsonify({'error': error}), 400

            # Create transcript for follow-up
            transcript = Transcript(
                user_id=current_user.id,
                task_id=task.id,
                transcription=transcription,
                feedback=feedback,
                main_transcript_id=main_transcript.id
            )
            db.session.add(transcript)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'feedback': feedback
            })

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@speaking_bp.route('/speaking_task_4_feedback')
@login_required
def speaking_task_4_feedback():
    task = Task.query.filter_by(name='speaking_task_4').first()
    if not task:
        flash('Task not found.', 'error')
        return redirect(url_for('speaking.speaking_task_4'))

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
        'follow_up_question': "What other steps could be taken to reduce pollution in cities?"
    }
    
    return render_template('speaking/speaking_task_4_feedback.html', **context)
