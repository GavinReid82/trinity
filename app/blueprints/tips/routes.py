from flask import Blueprint, render_template
from flask_login import login_required

tips_bp = Blueprint('tips', __name__)

# Video URLs for each skill
VIDEO_URLS = {
    'reading': 'https://www.youtube.com/embed/your-reading-video-id',
    'writing': 'https://www.youtube.com/embed/your-writing-video-id',
    'speaking': 'https://www.youtube.com/embed/your-speaking-video-id',
    'listening': 'https://www.youtube.com/embed/your-listening-video-id'
}

# Key points for each skill
KEY_POINTS = {
    'reading': [
        'Read the questions before reading the text',
        'Scan for key words and phrases',
        'Look for main ideas in each paragraph',
        'Pay attention to context clues',
        'Practice reading different types of texts'
    ],
    'writing': [
        'Plan your writing before you start',
        'Use clear and concise language',
        'Check your grammar and spelling',
        'Organize your ideas logically',
        'Review and edit your work'
    ],
    'speaking': [
        'Practice speaking regularly',
        'Record yourself to identify areas for improvement',
        'Use appropriate intonation and stress',
        'Build your vocabulary',
        'Be confident and clear in your delivery'
    ],
    'listening': [
        'Focus on the main ideas',
        'Take notes while listening',
        'Pay attention to context',
        'Practice with different accents',
        'Use subtitles when available'
    ]
}

@tips_bp.route('/<skill>/tips')
@login_required
def show_tips(skill):
    if skill not in VIDEO_URLS:
        return render_template('404.html'), 404
    
    return render_template('tips.html',
                         skill=skill,
                         video_url=VIDEO_URLS[skill],
                         key_points=KEY_POINTS[skill]) 