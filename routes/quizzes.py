from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.database import db
from models.learning import QuizAttempt
import random

quizzes_bp = Blueprint('quizzes', __name__)

@quizzes_bp.route('/quizzes')
@login_required
def index():
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.created_at.desc()).all()
    return render_template('quizzes.html', attempts=attempts)

@quizzes_bp.route('/api/quiz/generate', methods=['POST'])
@login_required
def generate_quiz():
    data = request.json
    subject = data.get('subject', 'General')
    topic = data.get('topic', 'Basics')
    
    # In a full implementation, this would call Gemini to generate questions based on RAG.
    # For now, return a standard structure.
    return jsonify({
        "subject": subject,
        "topic": topic,
        "questions": [
            {"q": f"What is a key concept in {topic}?", "options": ["A", "B", "C", "D"], "answer": "A"}
        ]
    })

@quizzes_bp.route('/api/quiz/submit', methods=['POST'])
@login_required
def submit_quiz():
    data = request.json
    attempt = QuizAttempt(
        user_id=current_user.id,
        subject=data.get('subject'),
        topic=data.get('topic'),
        score=data.get('score'),
        total=data.get('total')
    )
    db.session.add(attempt)
    db.session.commit()
    return jsonify({"status": "success", "id": attempt.id})
