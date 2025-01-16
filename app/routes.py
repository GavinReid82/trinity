import json
from flask import render_template, request
from app import app
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client = OpenAI(
    api_key=OPENAI_API_KEY  # Replace with your actual OpenAI API key
)


@app.route('/')
def welcome():
    template_path = os.path.abspath('app/templates/layout.html')
    print(f"Loading template: {template_path}")
    return render_template('welcome.html')

@app.route('/task_1_group_chat')
def task_1_group_chat():
    return render_template('task_1_group_chat.html')

@app.route('/task_2_essay')
def task_2_essay():
    return render_template('task_2_essay.html')

@app.route('/task_2_report')
def task_2_report():
    return render_template('task_2_report.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Get the user's response from the form
    response = request.form.get('writingTask')
    
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
        'feedback.html',
        response=response,
        general_comment=feedback.get('general_comment', ''),
        did_well=feedback.get('did_well', []),
        could_improve=feedback.get('could_improve', [])
    )