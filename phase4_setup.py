import os

base_dir = r"c:\Users\Pragadesh\OneDrive\Desktop\AI Student Mentor"

files = {
    "routes/quizzes.py": """from flask import Blueprint, render_template, request, jsonify
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
""",
    "routes/planner.py": """from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.database import db
from models.learning import StudyTask

planner_bp = Blueprint('planner', __name__)

@planner_bp.route('/planner')
@login_required
def index():
    tasks = StudyTask.query.filter_by(user_id=current_user.id).order_by(StudyTask.created_at.desc()).all()
    return render_template('planner.html', tasks=tasks)

@planner_bp.route('/api/planner/add', methods=['POST'])
@login_required
def add_task():
    data = request.form
    task = StudyTask(
        user_id=current_user.id,
        title=data.get('title'),
        topic=data.get('topic')
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({"status": "success"})
""",
    "templates/quizzes.html": """{% extends "base.html" %}
{% block content %}
<div class="section-card">
    <h2>Quizzes</h2>
    <div style="display:flex; gap: 20px;">
        <div style="flex:1;">
            <h3>Generate New Quiz</h3>
            <form id="quizForm">
                <input type="text" id="subject" placeholder="Subject" class="form-control" style="margin-bottom:10px;">
                <input type="text" id="topic" placeholder="Topic" class="form-control" style="margin-bottom:10px;">
                <button type="submit" class="btn btn-primary">Start Quiz</button>
            </form>
        </div>
        <div style="flex:1;">
            <h3>Past Attempts</h3>
            <ul>
                {% for attempt in attempts %}
                <li>{{ attempt.subject }} - {{ attempt.topic }}: {{ attempt.score }}/{{ attempt.total }}</li>
                {% else %}
                <li>No attempts yet.</li>
                {% endfor %}
            </ul>
        </div>
    </div>
</div>
{% endblock %}
""",
    "templates/planner.html": """{% extends "base.html" %}
{% block content %}
<div class="section-card">
    <h2>Study Planner</h2>
    <form id="taskForm" style="margin-bottom: 20px;">
        <input type="text" id="title" placeholder="Task Title" required>
        <input type="text" id="topic" placeholder="Topic" required>
        <button type="submit" class="btn btn-primary">Add Task</button>
    </form>
    <ul>
        {% for task in tasks %}
        <li>{{ task.title }} ({{ task.topic }}) - {{ "Done" if task.is_completed else "Pending" }}</li>
        {% else %}
        <li>No tasks scheduled.</li>
        {% endfor %}
    </ul>
</div>
<script>
document.getElementById('taskForm').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('title', document.getElementById('title').value);
    formData.append('topic', document.getElementById('topic').value);
    await fetch('/api/planner/add', { method: 'POST', body: formData });
    window.location.reload();
};
</script>
{% endblock %}
"""
}

# Apply to app.py
import re
app_path = os.path.join(base_dir, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

if "from routes.quizzes import quizzes_bp" not in app_content:
    app_content = app_content.replace(
        "from routes.learning import learning_bp", 
        "from routes.learning import learning_bp\n    from routes.quizzes import quizzes_bp\n    from routes.planner import planner_bp"
    )
    app_content = app_content.replace(
        "app.register_blueprint(learning_bp)",
        "app.register_blueprint(learning_bp)\n    app.register_blueprint(quizzes_bp)\n    app.register_blueprint(planner_bp)"
    )
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)

for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Phase 4 finalization complete.")
