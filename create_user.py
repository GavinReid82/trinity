from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.models import User, db

app = create_app()

def create_user(email, access_code):
    with app.app_context():
        user = User(email=email, access_code=access_code)
        db.session.add(user)
        db.session.commit()
        print(f"Created user: {email} with access code: {access_code}")

if __name__ == "__main__":
    create_user("gavinjohnreid@gmail.com", "GAVIN123")