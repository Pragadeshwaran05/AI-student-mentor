import os

base_dir = r"c:\Users\Pragadesh\OneDrive\Desktop\AI Student Mentor"

files = {
    "models/learning.py": """from models.database import db
from datetime import datetime

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    gemini_file_id = db.Column(db.String(255), nullable=False)
    gemini_file_uri = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100))
    topic = db.Column(db.String(100))
    score = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudyTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(100))
    is_completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
""",
    "app.py": """from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models.database import db
from models.user import User
from models.chat import Conversation, Message
from models.learning import Document, QuizAttempt, StudyTask
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
        
    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.chat import chat_bp
    from routes.learning import learning_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(learning_bp)
    
    @app.route('/')
    def index():
        return render_template('landing.html')
        
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
        
    with app.app_context():
        db.create_all()
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
""",
    "routes/learning.py": """import os
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from models.database import db
from models.learning import Document, QuizAttempt, StudyTask
import google.generativeai as genai
import uuid

learning_bp = Blueprint('learning', __name__)

@learning_bp.route('/documents', methods=['GET'])
@login_required
def documents():
    docs = Document.query.filter_by(user_id=current_user.id).all()
    return render_template('documents.html', documents=docs)

@learning_bp.route('/api/upload_document', methods=['POST'])
@login_required
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    upload_dir = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")
    file.save(filepath)
    
    try:
        api_key = current_app.config.get('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        
        uploaded_file = genai.upload_file(path=filepath, display_name=file.filename)
        
        doc = Document(
            user_id=current_user.id,
            filename=file.filename,
            gemini_file_id=uploaded_file.name,
            gemini_file_uri=uploaded_file.uri
        )
        db.session.add(doc)
        db.session.commit()
        
        os.remove(filepath) # Clean up local
        return jsonify({'success': True, 'doc_id': doc.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@learning_bp.route('/analytics')
@login_required
def analytics():
    quizzes = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.created_at.desc()).limit(10).all()
    tasks = StudyTask.query.filter_by(user_id=current_user.id).all()
    return render_template('analytics.html', quizzes=quizzes, tasks=tasks)
""",
    "templates/documents.html": """{% extends "base.html" %}
{% block content %}
<div class="section-card">
    <h2>Your Documents</h2>
    <form id="uploadForm" enctype="multipart/form-data">
        <input type="file" id="docFile" name="file" accept=".pdf,.txt,.docx" required>
        <button type="submit" class="btn btn-primary">Upload to AI</button>
    </form>
    <div id="uploadStatus"></div>
    <ul style="margin-top:20px;">
        {% for doc in documents %}
        <li><i class="fas fa-file-pdf"></i> {{ doc.filename }} - Ready for chat</li>
        {% else %}
        <li>No documents uploaded yet.</li>
        {% endendfor %}
    </ul>
</div>
<script>
document.getElementById('uploadForm').onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    document.getElementById('uploadStatus').innerText = "Uploading to Gemini...";
    
    try {
        const res = await fetch('/api/upload_document', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if(res.ok) {
            window.location.reload();
        } else {
            document.getElementById('uploadStatus').innerText = "Error: " + data.error;
        }
    } catch(err) {
        document.getElementById('uploadStatus').innerText = "Network error";
    }
};
</script>
{% endblock %}
""",
    "templates/analytics.html": """{% extends "base.html" %}
{% block content %}
<div class="section-card">
    <h2>Progress Analytics</h2>
    <p>Your recent quiz scores:</p>
    <ul>
        {% for q in quizzes %}
        <li>{{ q.topic }}: {{ q.score }}/{{ q.total }}</li>
        {% else %}
        <li>No quizzes taken yet.</li>
        {% endfor %}
    </ul>
    
    <h3 style="margin-top:20px;">Study Planner</h3>
    <ul>
        {% for t in tasks %}
        <li>{{ t.title }} - {{ 'Completed' if t.is_completed else 'Pending' }}</li>
        {% else %}
        <li>No tasks scheduled.</li>
        {% endfor %}
    </ul>
</div>
{% endblock %}
"""
}

# Apply dashboard links update
dashboard_py = """from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.user import User
from models.database import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    from models.learning import QuizAttempt, StudyTask
    quizzes = QuizAttempt.query.filter_by(user_id=current_user.id).count()
    tasks = StudyTask.query.filter_by(user_id=current_user.id).count()
    return render_template('dashboard.html', user=current_user, q_count=quizzes, t_count=tasks)

@dashboard_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.college = request.form.get('college')
        current_user.department = request.form.get('department')
        current_user.year = request.form.get('year')
        current_user.learning_style = request.form.get('learning_style')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard.profile'))
    return render_template('profile.html', user=current_user)

@dashboard_bp.route('/coming-soon')
@login_required
def coming_soon():
    return render_template('coming_soon.html')
"""
files['routes/dashboard.py'] = dashboard_py

for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Phase 3 scaffolding complete.")
