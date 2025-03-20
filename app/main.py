from app.models import db, User, Task, Transcript
from app import create_app

app = create_app()

def init_tasks():
    with app.app_context():
        # Initialize speaking tasks first
        speaking_questions = {
            "1": "What is the best holiday for families with children?",
            "2": "What do you do to relax?",
            "3": "I think life is becoming more stressful. Would you agree?"
        }
        
        for question_num in speaking_questions:
            task_name = f"Speaking Task 1 Q{question_num}"
            speaking_task = Task.query.filter_by(name=task_name).first()
            if not speaking_task:
                speaking_task = Task(name=task_name, type="speaking")
                db.session.add(speaking_task)
                print(f"✅ Created {task_name}")

        # Create Reading Paired Text task if it doesn't exist
        reading_task = Task.query.filter_by(name="Reading Paired Text").first()
        if not reading_task:
            reading_task = Task(name="Reading Paired Text", type="reading")
            db.session.add(reading_task)
            db.session.commit()
            print("✅ Created Reading Paired Text task")

        # Create Listening Task if it doesn't exist
        listening_task = Task.query.filter_by(name="Listening to a Talk").first()
        if not listening_task:
            listening_task = Task(name="Listening to a Talk", type="listening")
            db.session.add(listening_task)
            db.session.commit()
            print("✅ Created Listening to a Talk task")
        
        db.session.commit()
        print("✅ All tasks initialized")

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Task': Task, 'Transcript': Transcript}

if __name__ == '__main__':
    init_tasks()  # Initialize tasks when app starts
    app.run(debug=True)
