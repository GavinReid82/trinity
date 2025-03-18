from app.models import db, User, Task, Transcript
from app import create_app

app = create_app()

def init_tasks():
    with app.app_context():
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

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Task': Task, 'Transcript': Transcript}

if __name__ == '__main__':
    init_tasks()  # Initialize tasks when app starts
    app.run(debug=True)
