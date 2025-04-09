from flask import Blueprint, render_template, request, session, redirect, url_for, current_app, jsonify, flash
from openai import OpenAI
import json
import os
import re
from werkzeug.utils import secure_filename
from app.blueprints.speaking import speaking_bp
from flask_login import current_user, login_required
from app.models import db, Task, Transcript
from app.blueprints.speaking.utils import save_audio_file, transcribe_audio, generate_feedback, generate_followup_feedback, generate_task_4_feedback


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
    audio_path = None # Initialize audio_path
    try:
        stage = request.form.get('stage') # Get stage without default initially
        print(f"\n--- speaking_task_2_submit ---")
        print(f"Received stage from form: {stage}") # Log received stage

        if not stage or stage not in ['main', 'followup']:
             print(f"ERROR: Invalid stage received: {stage}")
             return jsonify({'error': 'Invalid stage provided'}), 400

        # Save audio file
        audio_path, error = save_audio_file(request, task_type='task_2', user_id=current_user.id) # Pass request object
        if error:
            print(f"Error saving audio: {error}")
            return jsonify({'error': error}), 400
        print(f"Audio saved to: {audio_path}")

        # Transcribe audio
        transcription, error = transcribe_audio(audio_path)
        if error:
            print(f"Error transcribing: {error}")
             # Clean up here if transcription fails
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"Cleaned up audio file after transcription error: {audio_path}")
            return jsonify({'error': error}), 400
        print(f"Transcription successful: {transcription[:50]}...")

        # Clean up audio file immediately after successful transcription
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"Cleaned up audio file after transcription: {audio_path}")
        audio_path = None # Reset path after cleanup


        if stage == 'main':
            print("Processing MAIN stage for Task 2")
            # Get or create the main task (ID 5)
            task = Task.query.filter_by(name='speaking_task_2', type='speaking').first()
            if not task:
                task = Task(name='speaking_task_2', type='speaking')
                db.session.add(task)
                db.session.commit() # Commit to get ID if new
                print(f"Created/Found main task (ID should be 5): {task.id}")
            else:
                 print(f"Found main task (ID should be 5): {task.id}")

            # Generate regular feedback
            feedback, error = generate_feedback(
                transcription=transcription,
                task_type='speaking_2',
                stage=stage
            )
            if error:
                print(f"Error generating main feedback: {error}")
                return jsonify({'error': error}), 400
            print("Generated main feedback.")

            # Create transcript for main response with correct task ID
            # *** Log the task ID being used ***
            print(f"Attempting to save MAIN transcript with task_id: {task.id} (should be 5)")
            transcript = Transcript(
                user_id=current_user.id,
                task_id=task.id,  # Explicitly using main task ID
                transcription=transcription,
                feedback=feedback
            )
            db.session.add(transcript)
            db.session.commit()
            print(f"Successfully saved MAIN transcript (ID: {transcript.id}) with task_id: {transcript.task_id}")

            session['follow_up_question'] = "What advice do you have for someone who wants to learn more about this topic?"
            session.modified = True # Ensure session is saved
            print("Set follow_up_question in session.")

            return jsonify({
                'success': True,
                'feedback': feedback,
                'follow_up_question': session['follow_up_question']
            })

        elif stage == 'followup': # Changed to elif for clarity
            print("Processing FOLLOWUP stage for Task 2")
            # Get or create the follow-up task (ID 10)
            followup_task = Task.query.filter_by(name='speaking_task_2_followup', type='speaking_followup').first()
            if not followup_task:
                followup_task = Task(name='speaking_task_2_followup', type='speaking_followup')
                db.session.add(followup_task)
                db.session.commit() # Commit to get ID if new
                print(f"Created/Found followup task (ID should be 10): {followup_task.id}")
            else:
                print(f"Found followup task (ID should be 10): {followup_task.id}")


            # Get the main response for context (using main task ID 5)
            main_task = Task.query.filter_by(name='speaking_task_2', type='speaking').first()
            if not main_task:
                 print("CRITICAL ERROR: Main task (speaking_task_2 / ID 5) not found in DB!")
                 return jsonify({'error': 'Main task configuration error'}), 500
            print(f"Looking for main transcript with task_id: {main_task.id}")

            main_transcript = Transcript.query.filter_by(
                user_id=current_user.id,
                task_id=main_task.id # Query using main task ID (5)
            ).order_by(Transcript.created_at.desc()).first()

            if not main_transcript:
                print(f"ERROR: No main transcript found for user {current_user.id} and task_id {main_task.id}")
                return jsonify({'error': 'No main response found to link follow-up'}), 400
            print(f"Found main transcript (ID: {main_transcript.id}) for context.")

            follow_up_question = session.get('follow_up_question',
                "What advice do you have for someone who wants to learn more about this topic?")
            print(f"Retrieved follow_up_question from session: {follow_up_question}")

            feedback, error = generate_followup_feedback(
                main_transcription=main_transcript.transcription,
                followup_transcription=transcription,
                follow_up_question=follow_up_question,
                task_type='speaking_2'
            )
            if error:
                print(f"Error generating followup feedback: {error}")
                return jsonify({'error': error}), 400
            print("Generated followup feedback.")

            # Create transcript for follow-up response with correct task ID
             # *** Log the task ID being used ***
            print(f"Attempting to save FOLLOWUP transcript with task_id: {followup_task.id} (should be 10) and main_transcript_id: {main_transcript.id}")
            transcript = Transcript(
                user_id=current_user.id,
                task_id=followup_task.id,  # Explicitly using followup task ID
                transcription=transcription,
                feedback=feedback,
                main_transcript_id=main_transcript.id
            )
            db.session.add(transcript)
            db.session.commit()
            print(f"Successfully saved FOLLOWUP transcript (ID: {transcript.id}) with task_id: {transcript.task_id}")

            return jsonify({
                'success': True,
                'feedback': feedback
            })

    except Exception as e:
        print(f"Exception occurred in speaking_task_2_submit: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        db.session.rollback() # Rollback on any exception
        return jsonify({'error': str(e)}), 500
    finally:
        # Ensure audio file is cleaned up even if errors occur before explicit removal
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                print(f"Cleaned up audio file in finally block: {audio_path}")
            except Exception as cleanup_error:
                 print(f"Error cleaning up audio file in finally block: {cleanup_error}")

@speaking_bp.route('/speaking_task_2_feedback')
@login_required
def speaking_task_2_feedback():
    main_task = Task.query.filter_by(name='speaking_task_2', type='speaking').first()
    if not main_task:
        flash('Task not found.', 'error')
        return redirect(url_for('speaking.speaking_task_2'))

    followup_task = Task.query.filter_by(name='speaking_task_2_followup', type='speaking_followup').first()

    main_transcript = Transcript.query.filter_by(
        user_id=current_user.id,
        task_id=main_task.id
    ).order_by(Transcript.created_at.desc()).first()

    follow_up_transcript = None
    if followup_task and main_transcript:
        follow_up_transcript = Transcript.query.filter_by(
            user_id=current_user.id,
            task_id=followup_task.id,
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

        # Clean up audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)

        if stage == 'main':
            # Get or create the main task
            task = Task.query.filter_by(name='speaking_task_3', type='speaking').first()
            if not task:
                task = Task(name='speaking_task_3', type='speaking')
                db.session.add(task)
                db.session.commit()

            # Generate regular feedback for main talk
            feedback, error = generate_feedback(
                transcription=transcription,
                task_type='speaking_3',
                stage=stage
            )
            
            if error:
                return jsonify({'error': error}), 400

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
            session['task3_follow_up_question'] = "For a group project everyone receives the same grade. What can you do next time to help your group do better?"
            
            return jsonify({
                'success': True,
                'feedback': feedback
            })
        else:
            # Get or create the follow-up task
            followup_task = Task.query.filter_by(name='speaking_task_3_followup', type='speaking_followup').first()
            if not followup_task:
                followup_task = Task(name='speaking_task_3_followup', type='speaking_followup')
                db.session.add(followup_task)
                db.session.commit()

            # Get the main response for context
            main_task = Task.query.filter_by(name='speaking_task_3', type='speaking').first()
            main_transcript = Transcript.query.filter_by(
                user_id=current_user.id,
                task_id=main_task.id
            ).order_by(Transcript.created_at.desc()).first()

            if not main_transcript:
                return jsonify({'error': 'No main response found'}), 400
            
            follow_up_question = session.get('task3_follow_up_question', 
                "For a group project everyone receives the same grade. What can you do next time to help your group do better?")

            # Generate specialized follow-up feedback
            feedback, error = generate_followup_feedback(
                main_transcription=main_transcript.transcription,
                followup_transcription=transcription,
                follow_up_question=follow_up_question,
                task_type='speaking_3'
            )
            
            if error:
                return jsonify({'error': error}), 400

            # Create transcript for follow-up with the correct task_id
            transcript = Transcript(
                user_id=current_user.id,
                task_id=followup_task.id,  # Use followup_task.id instead of task.id
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
        return jsonify({'error': str(e)}), 400

@speaking_bp.route('/speaking_task_3_feedback')
@login_required
def speaking_task_3_feedback():
    # Get main task
    main_task = Task.query.filter_by(name='speaking_task_3', type='speaking').first()
    if not main_task:
        flash('Task not found.', 'error')
        return redirect(url_for('speaking.speaking_task_3'))

    # Get follow-up task
    followup_task = Task.query.filter_by(name='speaking_task_3_followup', type='speaking_followup').first()

    # Get the main response
    main_transcript = Transcript.query.filter_by(
        user_id=current_user.id,
        task_id=main_task.id
    ).order_by(Transcript.created_at.desc()).first()

    # Get the follow-up response
    follow_up_transcript = None
    if main_transcript and followup_task:
        follow_up_transcript = Transcript.query.filter_by(
            user_id=current_user.id,
            task_id=followup_task.id,
            main_transcript_id=main_transcript.id
        ).order_by(Transcript.created_at.desc()).first()

    context = {
        'main_response': main_transcript.transcription if main_transcript else None,
        'main_feedback': main_transcript.feedback if main_transcript else None,
        'follow_up_response': follow_up_transcript.transcription if follow_up_transcript else None,
        'follow_up_feedback': follow_up_transcript.feedback if follow_up_transcript else None,
        'follow_up_question': "For a group project everyone receives the same grade. What can you do next time to help your group do better?"
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
        
        audio_path, error = save_audio_file(request, task_type='task_4', user_id=current_user.id)
        if error:
            return jsonify({'error': error}), 400

        transcription, error = transcribe_audio(audio_path)
        if error:
            return jsonify({'error': error}), 400

        if os.path.exists(audio_path):
            os.remove(audio_path)

        if stage == 'main':
            task = Task.query.filter_by(name='speaking_task_4', type='speaking').first()
            if not task:
                task = Task(name='speaking_task_4', type='speaking')
                db.session.add(task)
                db.session.commit()

            # Discussion transcript
            discussion_transcript = (
                "Welcome to today's podcast, GreenWise. This is your host, Colin Davies. My guest today is Aisha Gannop, "
                "head of City Trees, an international organisation focused on tree planting in urban areas. Welcome, Aisha. "
                "Hello, Colin. Thanks for inviting me. So, Aisha, we're all aware that trees can improve a city's appearance, "
                "but can you tell us more specifically about the benefits of city trees? I'd say the most important benefit is "
                "that large trees can make our cities cleaner. They can filter urban pollutants caused by vehicle emissions. "
                "In fact, a tree can absorb up to 150 kilos of CO2 in a year. That's a significant statistic, so important in "
                "terms of mitigating global warming. And in connection with that, trees can also reduce temperatures in cities. "
                "You're right. Basically, trees provide shade and if they are planted strategically around buildings in hot countries, "
                "they can reduce air conditioning needs by about 30%. Can you say a bit more about that? Well, as an example, an urban "
                "tree planting project in Abu Dhabi, the capital of UAE, where temperatures frequently go above 40 degrees, found that "
                "planting trees 6 metres apart in built-up areas lowered temperatures by nearly 1%. In addition, the shade the trees "
                "provided meant residents could socialise outside, which further reduced the time they had their air conditioning on. "
                "It's great to hear of such projects. Let's move on to benefits to wildlife now."
            )

            # Use the correct feedback function for Task 4
            feedback, error = generate_task_4_feedback(
                user_transcription=transcription,
                discussion_transcript=discussion_transcript
            )

            if error:
                return jsonify({'error': error}), 400

            transcript = Transcript(
                user_id=current_user.id,
                task_id=task.id,
                transcription=transcription,
                feedback=feedback
            )
            db.session.add(transcript)
            db.session.commit()
            
            session['task4_follow_up_question'] = "What other steps could be taken to reduce pollution in cities?"
            
            return jsonify({
                'success': True,
                'feedback': feedback
            })
        else:
            followup_task = Task.query.filter_by(name='speaking_task_4_followup', type='speaking_followup').first()
            if not followup_task:
                followup_task = Task(name='speaking_task_4_followup', type='speaking_followup')
                db.session.add(followup_task)
                db.session.commit()

            main_task = Task.query.filter_by(name='speaking_task_4', type='speaking').first()
            main_transcript = Transcript.query.filter_by(
                user_id=current_user.id,
                task_id=main_task.id
            ).order_by(Transcript.created_at.desc()).first()

            if not main_transcript:
                return jsonify({'error': 'No main response found'}), 400
            
            follow_up_question = session.get('task4_follow_up_question',
                "What other steps could be taken to reduce pollution in cities?")

            feedback, error = generate_followup_feedback(
                main_transcription=main_transcript.transcription,
                followup_transcription=transcription,
                follow_up_question=follow_up_question,
                task_type='speaking_4'
            )
            
            if error:
                return jsonify({'error': error}), 400

            transcript = Transcript(
                user_id=current_user.id,
                task_id=followup_task.id,
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
        return jsonify({'error': str(e)}), 400



@speaking_bp.route('/speaking_task_4_feedback')
@login_required
def speaking_task_4_feedback():
    main_task = Task.query.filter_by(name='speaking_task_4', type='speaking').first()
    if not main_task:
        flash('Task not found.', 'error')
        return redirect(url_for('speaking.speaking_task_4'))

    followup_task = Task.query.filter_by(name='speaking_task_4_followup', type='speaking_followup').first()

    main_transcript = Transcript.query.filter_by(
        user_id=current_user.id,
        task_id=main_task.id
    ).order_by(Transcript.created_at.desc()).first()

    follow_up_transcript = None
    if main_transcript and followup_task:
        follow_up_transcript = Transcript.query.filter_by(
            user_id=current_user.id,
            task_id=followup_task.id,
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




def init_speaking_tasks():
    """Initialize all speaking tasks including follow-ups"""
    try:
        # Main tasks (these already exist)
        main_tasks = [
            {'name': 'speaking_task_2', 'type': 'speaking'},
            {'name': 'speaking_task_3', 'type': 'speaking'},
            {'name': 'speaking_task_4', 'type': 'speaking'}
        ]
        
        # Follow-up tasks (these need to be added)
        followup_tasks = [
            {'name': 'speaking_task_2_followup', 'type': 'speaking_followup'},
            {'name': 'speaking_task_3_followup', 'type': 'speaking_followup'},
            {'name': 'speaking_task_4_followup', 'type': 'speaking_followup'}
        ]
        
        # Create all tasks if they don't exist
        for task_info in main_tasks + followup_tasks:
            task = Task.query.filter_by(name=task_info['name']).first()
            if not task:
                task = Task(name=task_info['name'], type=task_info['type'])
                db.session.add(task)
                print(f"Created task: {task_info['name']} ({task_info['type']})")
        
        db.session.commit()
        print("All speaking tasks initialized successfully")
        
    except Exception as e:
        print(f"Error initializing speaking tasks: {e}")
        db.session.rollback()
