import os

base_dir = r"c:\Users\Pragadesh\OneDrive\Desktop\AI Student Mentor"

directories = [
    "database",
    "models",
    "routes",
    "services",
    "templates",
    "static/css",
    "static/js",
    "uploads"
]

for d in directories:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

files = {
    "requirements.txt": """Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Werkzeug==3.0.1
python-dotenv==1.0.0
""",
    "config.py": """import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
""",
    "models/database.py": """from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
""",
    "models/user.py": """from models.database import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    college = db.Column(db.String(150))
    department = db.Column(db.String(100))
    year = db.Column(db.String(20))
    learning_style = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
""",
    "services/ai_service.py": """class AIService:
    @staticmethod
    def get_response(message):
        # Temporary development response for Phase 1
        return f"This is a placeholder AI response to: '{message}'. Full AI integration is coming in Phase 2!"
""",
    "routes/auth.py": """from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from models.database import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        return redirect(url_for('dashboard.index'))
        
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        college = request.form.get('college')
        department = request.form.get('department')
        year = request.form.get('year')
        learning_style = request.form.get('learning_style')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('auth.register'))
            
        user = User.query.filter_by(email=email).first()
        
        if user:
            flash('Email address already exists', 'danger')
            return redirect(url_for('auth.register'))
            
        new_user = User(
            email=email, 
            full_name=full_name, 
            password_hash=generate_password_hash(password),
            college=college,
            department=department,
            year=year,
            learning_style=learning_style
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
""",
    "routes/dashboard.py": """from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.user import User
from models.database import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    return render_template('dashboard.html', user=current_user)

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
""",
    "routes/chat.py": """from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from services.ai_service import AIService

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
@login_required
def index():
    return render_template('chat.html')

@chat_bp.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
        
    response = AIService.get_response(message)
    
    return jsonify({
        'message': response
    })
""",
    "app.py": """from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models.database import db
from models.user import User
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
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chat_bp)
    
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
    "templates/base.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Student Mentor</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <!-- FontAwesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    {% block head %}{% endblock %}
</head>
<body>
    {% if current_user.is_authenticated %}
    <div class="app-container">
        <!-- Sidebar -->
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h2><i class="fas fa-graduation-cap"></i> AI Mentor</h2>
                <button class="close-sidebar" id="closeSidebar"><i class="fas fa-times"></i></button>
            </div>
            <nav class="sidebar-nav">
                <a href="{{ url_for('dashboard.index') }}" class="nav-item"><i class="fas fa-home"></i> Dashboard</a>
                <a href="{{ url_for('chat.index') }}" class="nav-item"><i class="fas fa-robot"></i> AI Mentor</a>
                <a href="{{ url_for('dashboard.coming_soon') }}" class="nav-item"><i class="fas fa-book"></i> My Learning</a>
                <a href="{{ url_for('dashboard.coming_soon') }}" class="nav-item"><i class="fas fa-tasks"></i> Quizzes</a>
                <a href="{{ url_for('dashboard.coming_soon') }}" class="nav-item"><i class="fas fa-calendar-alt"></i> Study Planner</a>
                <a href="{{ url_for('dashboard.coming_soon') }}" class="nav-item"><i class="fas fa-file-alt"></i> Documents</a>
                <a href="{{ url_for('dashboard.coming_soon') }}" class="nav-item"><i class="fas fa-chart-line"></i> Progress</a>
                <a href="{{ url_for('dashboard.profile') }}" class="nav-item"><i class="fas fa-user"></i> Profile</a>
                <a href="{{ url_for('auth.logout') }}" class="nav-item logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
            </nav>
        </aside>
        
        <!-- Main Content -->
        <main class="main-content">
            <header class="top-header">
                <button class="menu-btn" id="openSidebar"><i class="fas fa-bars"></i></button>
                <div class="user-info">
                    <span>{{ current_user.full_name }}</span>
                    <div class="avatar">{{ current_user.full_name[0] }}</div>
                </div>
            </header>
            
            <div class="content-wrapper">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                {% block content %}{% endblock %}
            </div>
        </main>
        
        <!-- Overlay for mobile sidebar -->
        <div class="sidebar-overlay" id="sidebarOverlay"></div>
    </div>
    {% else %}
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages-container">
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        {% block public_content %}{% endblock %}
    {% endif %}

    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
""",
    "templates/landing.html": """{% extends "base.html" %}

{% block public_content %}
<div class="landing-page">
    <header class="landing-header">
        <div class="logo">
            <i class="fas fa-graduation-cap"></i> AI Student Mentor
        </div>
        <div class="auth-buttons">
            <a href="{{ url_for('auth.login') }}" class="btn btn-outline">Login</a>
            <a href="{{ url_for('auth.register') }}" class="btn btn-primary">Register</a>
        </div>
    </header>
    
    <main class="landing-main">
        <div class="hero-section">
            <div class="hero-content">
                <h1>Your Personalized AI Academic Mentor</h1>
                <p>Master any subject with an AI tutor that adapts to your learning style. Ask questions, take quizzes, and track your progress through interactive text and voice conversations.</p>
                <a href="{{ url_for('auth.register') }}" class="btn btn-primary btn-large">Start Learning Now</a>
            </div>
            <div class="hero-image">
                <i class="fas fa-robot hero-icon"></i>
            </div>
        </div>
        
        <div class="features-section">
            <h2>Why Choose AI Student Mentor?</h2>
            <div class="features-grid">
                <div class="feature-card">
                    <i class="fas fa-brain feature-icon"></i>
                    <h3>Personalized Learning</h3>
                    <p>The AI adapts explanations based on whether you are a visual, reading, or practical learner.</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-comments feature-icon"></i>
                    <h3>Text & Voice Mentor</h3>
                    <p>Interact naturally using text chat or speak directly to your mentor for on-the-go learning.</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-clipboard-check feature-icon"></i>
                    <h3>Smart Quizzes</h3>
                    <p>Test your knowledge with automatically generated quizzes tailored to what you've just learned.</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-file-upload feature-icon"></i>
                    <h3>Document Analysis</h3>
                    <p>Upload your syllabus or lecture notes and the AI will teach you directly from your materials.</p>
                </div>
            </div>
        </div>
    </main>
</div>
{% endblock %}
""",
    "templates/login.html": """{% extends "base.html" %}

{% block head %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/auth.css') }}">
{% endblock %}

{% block public_content %}
<div class="auth-container">
    <div class="auth-card">
        <div class="auth-header">
            <h2><i class="fas fa-graduation-cap"></i> Welcome Back</h2>
            <p>Login to continue your learning journey</p>
        </div>
        
        <form method="POST" action="{{ url_for('auth.login') }}" class="auth-form">
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required placeholder="Enter your email">
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required placeholder="Enter your password">
            </div>
            
            <div class="form-options">
                <label class="remember-me">
                    <input type="checkbox" name="remember"> Remember me
                </label>
                <a href="#" class="forgot-password">Forgot password?</a>
            </div>
            
            <button type="submit" class="btn btn-primary btn-block">Login</button>
        </form>
        
        <div class="auth-footer">
            <p>Don't have an account? <a href="{{ url_for('auth.register') }}">Register here</a></p>
        </div>
    </div>
</div>
{% endblock %}
""",
    "templates/register.html": """{% extends "base.html" %}

{% block head %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/auth.css') }}">
{% endblock %}

{% block public_content %}
<div class="auth-container">
    <div class="auth-card register-card">
        <div class="auth-header">
            <h2><i class="fas fa-user-plus"></i> Create Account</h2>
            <p>Join AI Student Mentor today</p>
        </div>
        
        <form method="POST" action="{{ url_for('auth.register') }}" class="auth-form">
            <div class="form-row">
                <div class="form-group">
                    <label for="full_name">Full Name</label>
                    <input type="text" id="full_name" name="full_name" required>
                </div>
                
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" required>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <div class="form-group">
                    <label for="confirm_password">Confirm Password</label>
                    <input type="password" id="confirm_password" name="confirm_password" required>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="college">College/University</label>
                    <input type="text" id="college" name="college" required>
                </div>
                
                <div class="form-group">
                    <label for="department">Department</label>
                    <input type="text" id="department" name="department" required>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="year">Year of Study</label>
                    <select id="year" name="year" required>
                        <option value="">Select Year</option>
                        <option value="1">1st Year</option>
                        <option value="2">2nd Year</option>
                        <option value="3">3rd Year</option>
                        <option value="4">4th Year</option>
                        <option value="grad">Graduate</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="learning_style">Preferred Learning Style</label>
                    <select id="learning_style" name="learning_style" required>
                        <option value="">Select Style</option>
                        <option value="visual">Visual (Images/Diagrams)</option>
                        <option value="reading">Reading/Writing</option>
                        <option value="practice">Practice (Hands-on)</option>
                        <option value="interactive">Interactive</option>
                    </select>
                </div>
            </div>
            
            <button type="submit" class="btn btn-primary btn-block">Register</button>
        </form>
        
        <div class="auth-footer">
            <p>Already have an account? <a href="{{ url_for('auth.login') }}">Login here</a></p>
        </div>
    </div>
</div>
{% endblock %}
""",
    "templates/dashboard.html": """{% extends "base.html" %}

{% block head %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css') }}">
{% endblock %}

{% block content %}
<div class="dashboard-header">
    <h1>Welcome back, {{ user.full_name }}! 👋</h1>
    <p>Here's an overview of your learning progress.</p>
</div>

<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-icon bg-blue"><i class="fas fa-question"></i></div>
        <div class="stat-info">
            <h3>Questions Asked</h3>
            <p class="stat-value">0</p>
        </div>
    </div>
    <div class="stat-card">
        <div class="stat-icon bg-green"><i class="fas fa-book-open"></i></div>
        <div class="stat-info">
            <h3>Topics Learned</h3>
            <p class="stat-value">0</p>
        </div>
    </div>
    <div class="stat-card">
        <div class="stat-icon bg-purple"><i class="fas fa-clipboard-check"></i></div>
        <div class="stat-info">
            <h3>Avg. Quiz Score</h3>
            <p class="stat-value">0%</p>
        </div>
    </div>
    <div class="stat-card">
        <div class="stat-icon bg-orange"><i class="fas fa-chart-line"></i></div>
        <div class="stat-info">
            <h3>Learning Progress</h3>
            <p class="stat-value">New</p>
        </div>
    </div>
</div>

<div class="dashboard-grid">
    <div class="dashboard-main">
        <div class="section-card">
            <div class="section-header">
                <h2>Quick Actions</h2>
            </div>
            <div class="quick-actions">
                <a href="{{ url_for('chat.index') }}" class="action-btn">
                    <i class="fas fa-comment-dots"></i>
                    <span>Ask Mentor</span>
                </a>
                <a href="{{ url_for('dashboard.coming_soon') }}" class="action-btn">
                    <i class="fas fa-tasks"></i>
                    <span>Take Quiz</span>
                </a>
                <a href="{{ url_for('dashboard.coming_soon') }}" class="action-btn">
                    <i class="fas fa-calendar"></i>
                    <span>Study Plan</span>
                </a>
                <a href="{{ url_for('dashboard.coming_soon') }}" class="action-btn">
                    <i class="fas fa-upload"></i>
                    <span>Upload Doc</span>
                </a>
                <a href="{{ url_for('dashboard.coming_soon') }}" class="action-btn">
                    <i class="fas fa-microphone"></i>
                    <span>Voice Mentor</span>
                </a>
            </div>
        </div>
        
        <div class="section-card">
            <div class="section-header">
                <h2>Recent Activity</h2>
            </div>
            <div class="empty-state">
                <i class="fas fa-history empty-icon"></i>
                <p>No recent activity. Start chatting with your AI mentor!</p>
                <a href="{{ url_for('chat.index') }}" class="btn btn-outline">Start Chatting</a>
            </div>
        </div>
    </div>
    
    <div class="dashboard-sidebar">
        <div class="section-card">
            <div class="section-header">
                <h2>Current Study Goal</h2>
            </div>
            <div class="goal-card">
                <p>Set a study goal to track your progress.</p>
                <a href="{{ url_for('dashboard.coming_soon') }}" class="btn btn-sm btn-outline">Set Goal</a>
            </div>
        </div>
        
        <div class="section-card">
            <div class="section-header">
                <h2>Recommended Topics</h2>
            </div>
            <ul class="recommended-list">
                <li><i class="fas fa-star"></i> Introduction to your major</li>
                <li><i class="fas fa-star"></i> Effective study techniques</li>
                <li><i class="fas fa-star"></i> Time management skills</li>
            </ul>
        </div>
    </div>
</div>
{% endblock %}
""",
    "templates/chat.html": """{% extends "base.html" %}

{% block head %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/chat.css') }}">
{% endblock %}

{% block content %}
<div class="chat-container">
    <div class="chat-header">
        <div class="mentor-info">
            <div class="mentor-avatar"><i class="fas fa-robot"></i></div>
            <div>
                <h2>AI Mentor</h2>
                <p class="status">Online | Ready to help</p>
            </div>
        </div>
        <button class="btn btn-sm btn-outline" id="clearChat"><i class="fas fa-trash"></i> Clear</button>
    </div>
    
    <div class="chat-messages" id="chatMessages">
        <div class="message ai">
            <div class="message-content">
                Hello {{ current_user.full_name.split()[0] }}! I'm your AI Academic Mentor. How can I help you with your studies today?
            </div>
        </div>
    </div>
    
    <div class="suggestions" id="suggestions">
        <button class="suggestion-btn" onclick="sendSuggestion('Explain DBMS normalization')">Explain DBMS normalization</button>
        <button class="suggestion-btn" onclick="sendSuggestion('Teach me recursion')">Teach me recursion</button>
        <button class="suggestion-btn" onclick="sendSuggestion('Give me a Python example')">Give me a Python example</button>
        <button class="suggestion-btn" onclick="sendSuggestion('Explain TCP vs UDP')">Explain TCP vs UDP</button>
        <button class="suggestion-btn" onclick="sendSuggestion('Create a quiz for me')">Create a quiz for me</button>
    </div>
    
    <div class="chat-input-area">
        <form id="chatForm">
            <input type="text" id="messageInput" placeholder="Ask anything..." autocomplete="off">
            <button type="submit" class="btn btn-primary btn-icon"><i class="fas fa-paper-plane"></i></button>
        </form>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/chat.js') }}"></script>
{% endblock %}
""",
    "templates/profile.html": """{% extends "base.html" %}

{% block content %}
<div class="profile-container">
    <div class="section-card">
        <div class="section-header">
            <h2>Your Profile</h2>
        </div>
        
        <form method="POST" action="{{ url_for('dashboard.profile') }}" class="profile-form">
            <div class="form-row">
                <div class="form-group">
                    <label for="full_name">Full Name</label>
                    <input type="text" id="full_name" name="full_name" value="{{ user.full_name }}" required>
                </div>
                
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" value="{{ user.email }}" disabled>
                    <small>Email cannot be changed.</small>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="college">College/University</label>
                    <input type="text" id="college" name="college" value="{{ user.college }}" required>
                </div>
                
                <div class="form-group">
                    <label for="department">Department</label>
                    <input type="text" id="department" name="department" value="{{ user.department }}" required>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="year">Year of Study</label>
                    <select id="year" name="year" required>
                        <option value="1" {% if user.year == '1' %}selected{% endif %}>1st Year</option>
                        <option value="2" {% if user.year == '2' %}selected{% endif %}>2nd Year</option>
                        <option value="3" {% if user.year == '3' %}selected{% endif %}>3rd Year</option>
                        <option value="4" {% if user.year == '4' %}selected{% endif %}>4th Year</option>
                        <option value="grad" {% if user.year == 'grad' %}selected{% endif %}>Graduate</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="learning_style">Preferred Learning Style</label>
                    <select id="learning_style" name="learning_style" required>
                        <option value="visual" {% if user.learning_style == 'visual' %}selected{% endif %}>Visual (Images/Diagrams)</option>
                        <option value="reading" {% if user.learning_style == 'reading' %}selected{% endif %}>Reading/Writing</option>
                        <option value="practice" {% if user.learning_style == 'practice' %}selected{% endif %}>Practice (Hands-on)</option>
                        <option value="interactive" {% if user.learning_style == 'interactive' %}selected{% endif %}>Interactive</option>
                    </select>
                </div>
            </div>
            
            <button type="submit" class="btn btn-primary">Save Changes</button>
        </form>
    </div>
</div>
{% endblock %}
""",
    "templates/coming_soon.html": """{% extends "base.html" %}

{% block content %}
<div class="empty-state" style="margin-top: 50px;">
    <i class="fas fa-tools empty-icon" style="font-size: 64px; color: var(--primary-color);"></i>
    <h2>Coming Soon!</h2>
    <p>This feature will be available in Phase 2/3 of AI Student Mentor.</p>
    <a href="{{ url_for('dashboard.index') }}" class="btn btn-primary" style="margin-top: 20px;">Back to Dashboard</a>
</div>
{% endblock %}
""",
    "templates/404.html": """{% extends "base.html" %}

{% block public_content %}
<div class="empty-state" style="height: 100vh; display: flex; flex-direction: column; justify-content: center;">
    <h1 style="font-size: 72px; color: var(--primary-color);">404</h1>
    <h2>Page Not Found</h2>
    <p>The page you are looking for does not exist.</p>
    <a href="/" class="btn btn-primary" style="margin-top: 20px;">Go Home</a>
</div>
{% endblock %}
""",
    "templates/500.html": """{% extends "base.html" %}

{% block public_content %}
<div class="empty-state" style="height: 100vh; display: flex; flex-direction: column; justify-content: center;">
    <h1 style="font-size: 72px; color: var(--danger-color);">500</h1>
    <h2>Server Error</h2>
    <p>Something went wrong on our end.</p>
    <a href="/" class="btn btn-primary" style="margin-top: 20px;">Go Home</a>
</div>
{% endblock %}
""",
    "static/css/style.css": """:root {
    --primary-color: #4a6fa5;
    --primary-hover: #375a8a;
    --secondary-color: #166088;
    --text-main: #333;
    --text-muted: #666;
    --bg-main: #f4f7f6;
    --bg-card: #fff;
    --border-color: #e0e0e0;
    --danger-color: #e63946;
    --success-color: #2a9d8f;
    --sidebar-width: 250px;
    --header-height: 60px;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

body {
    background-color: var(--bg-main);
    color: var(--text-main);
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: all 0.3s ease;
    text-align: center;
}

.btn-primary {
    background-color: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background-color: var(--primary-hover);
}

.btn-outline {
    background-color: transparent;
    color: var(--primary-color);
    border: 1px solid var(--primary-color);
}

.btn-outline:hover {
    background-color: var(--primary-color);
    color: white;
}

.btn-block {
    display: block;
    width: 100%;
}

.btn-large {
    padding: 0.8rem 1.5rem;
    font-size: 1.1rem;
}

.btn-sm {
    padding: 0.3rem 0.6rem;
    font-size: 0.875rem;
}

/* Forms */
.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.form-group input, .form-group select {
    width: 100%;
    padding: 0.6rem;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 1rem;
}

.form-group input:focus, .form-group select:focus {
    outline: none;
    border-color: var(--primary-color);
}

.form-row {
    display: flex;
    gap: 1rem;
}

.form-row .form-group {
    flex: 1;
}

/* Alerts */
.alert {
    padding: 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
}

.alert-danger {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.alert-success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.flash-messages-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
    width: 300px;
}

/* Layout */
.app-container {
    display: flex;
    min-height: 100vh;
}

/* Sidebar */
.sidebar {
    width: var(--sidebar-width);
    background-color: var(--bg-card);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    position: fixed;
    height: 100vh;
    z-index: 100;
    transition: transform 0.3s ease;
}

.sidebar-header {
    height: var(--header-height);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.5rem;
    border-bottom: 1px solid var(--border-color);
}

.close-sidebar {
    display: none;
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    color: var(--text-muted);
}

.sidebar-nav {
    padding: 1rem 0;
    flex: 1;
    overflow-y: auto;
}

.nav-item {
    display: flex;
    align-items: center;
    padding: 0.8rem 1.5rem;
    color: var(--text-main);
    text-decoration: none;
    transition: background-color 0.2s;
}

.nav-item i {
    margin-right: 10px;
    width: 20px;
    text-align: center;
    color: var(--primary-color);
}

.nav-item:hover {
    background-color: var(--bg-main);
}

.nav-item.logout {
    margin-top: auto;
    color: var(--danger-color);
}

.nav-item.logout i {
    color: var(--danger-color);
}

/* Main Content */
.main-content {
    flex: 1;
    margin-left: var(--sidebar-width);
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

.top-header {
    height: var(--header-height);
    background-color: var(--bg-card);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
}

.menu-btn {
    display: none;
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-main);
}

.user-info {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-left: auto;
}

.avatar {
    width: 35px;
    height: 35px;
    background-color: var(--primary-color);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}

.content-wrapper {
    padding: 2rem;
    flex: 1;
}

.sidebar-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 99;
}

/* Cards */
.section-card {
    background-color: var(--bg-card);
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.section-header {
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 2rem;
    color: var(--text-muted);
}

.empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: #cbd5e1;
}

/* Landing Page */
.landing-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.landing-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 5%;
    background-color: var(--bg-card);
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary-color);
}

.hero-section {
    display: flex;
    align-items: center;
    padding: 4rem 5%;
    background: linear-gradient(135deg, #f4f7f6 0%, #e2e8f0 100%);
    gap: 2rem;
}

.hero-content {
    flex: 1;
}

.hero-content h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: var(--text-main);
}

.hero-content p {
    font-size: 1.2rem;
    margin-bottom: 2rem;
    color: var(--text-muted);
}

.hero-image {
    flex: 1;
    display: flex;
    justify-content: center;
}

.hero-icon {
    font-size: 15rem;
    color: var(--primary-color);
    opacity: 0.8;
}

.features-section {
    padding: 4rem 5%;
    text-align: center;
}

.features-section h2 {
    margin-bottom: 3rem;
    font-size: 2rem;
}

.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
}

.feature-card {
    background-color: var(--bg-card);
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    transition: transform 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-5px);
}

.feature-icon {
    font-size: 3rem;
    color: var(--primary-color);
    margin-bottom: 1.5rem;
}

.feature-card h3 {
    margin-bottom: 1rem;
}

.feature-card p {
    color: var(--text-muted);
}

/* Utilities */
.bg-blue { background-color: #3b82f6; color: white; }
.bg-green { background-color: #10b981; color: white; }
.bg-purple { background-color: #8b5cf6; color: white; }
.bg-orange { background-color: #f59e0b; color: white; }

/* Responsive */
@media (max-width: 768px) {
    .sidebar {
        transform: translateX(-100%);
    }
    
    .sidebar.open {
        transform: translateX(0);
    }
    
    .close-sidebar {
        display: block;
    }
    
    .main-content {
        margin-left: 0;
    }
    
    .menu-btn {
        display: block;
    }
    
    .sidebar-overlay.active {
        display: block;
    }
    
    .hero-section {
        flex-direction: column;
        text-align: center;
    }
    
    .hero-icon {
        font-size: 10rem;
        margin-top: 2rem;
    }
    
    .form-row {
        flex-direction: column;
        gap: 0;
    }
}
""",
    "static/css/auth.css": """.auth-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background-color: var(--bg-main);
    padding: 2rem;
}

.auth-card {
    background-color: var(--bg-card);
    border-radius: 10px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    width: 100%;
    max-width: 400px;
    padding: 2rem;
}

.register-card {
    max-width: 600px;
}

.auth-header {
    text-align: center;
    margin-bottom: 2rem;
}

.auth-header h2 {
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.auth-header p {
    color: var(--text-muted);
}

.form-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.remember-me {
    display: flex;
    align-items: center;
    gap: 5px;
    color: var(--text-muted);
    font-size: 0.9rem;
}

.forgot-password {
    color: var(--primary-color);
    text-decoration: none;
    font-size: 0.9rem;
}

.forgot-password:hover {
    text-decoration: underline;
}

.auth-footer {
    text-align: center;
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-color);
    font-size: 0.9rem;
}

.auth-footer a {
    color: var(--primary-color);
    text-decoration: none;
    font-weight: 500;
}

.auth-footer a:hover {
    text-decoration: underline;
}
""",
    "static/css/dashboard.css": """.dashboard-header {
    margin-bottom: 2rem;
}

.dashboard-header h1 {
    color: var(--text-main);
    margin-bottom: 0.5rem;
}

.dashboard-header p {
    color: var(--text-muted);
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stat-card {
    background-color: var(--bg-card);
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    display: flex;
    align-items: center;
    gap: 1rem;
}

.stat-icon {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
}

.stat-info h3 {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin-bottom: 0.2rem;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--text-main);
}

.dashboard-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 1.5rem;
}

.quick-actions {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 1rem;
}

.action-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    background-color: var(--bg-main);
    border-radius: 8px;
    text-decoration: none;
    color: var(--text-main);
    transition: all 0.2s;
    text-align: center;
    border: 1px solid transparent;
}

.action-btn:hover {
    background-color: #e2e8f0;
    border-color: var(--border-color);
    transform: translateY(-2px);
}

.action-btn i {
    font-size: 1.5rem;
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.action-btn span {
    font-size: 0.85rem;
    font-weight: 500;
}

.goal-card {
    background-color: var(--bg-main);
    padding: 1rem;
    border-radius: 6px;
    text-align: center;
}

.goal-card p {
    margin-bottom: 1rem;
    color: var(--text-muted);
}

.recommended-list {
    list-style: none;
}

.recommended-list li {
    padding: 0.8rem 0;
    border-bottom: 1px solid var(--border-color);
    color: var(--text-main);
    display: flex;
    align-items: center;
    gap: 10px;
}

.recommended-list li:last-child {
    border-bottom: none;
}

.recommended-list li i {
    color: #f59e0b;
}

@media (max-width: 992px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
}
""",
    "static/css/chat.css": """.chat-container {
    background-color: var(--bg-card);
    border-radius: 10px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
    height: calc(100vh - var(--header-height) - 4rem);
    overflow: hidden;
}

.chat-header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #fff;
}

.mentor-info {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.mentor-avatar {
    width: 40px;
    height: 40px;
    background-color: var(--primary-color);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
}

.mentor-info h2 {
    font-size: 1.1rem;
    margin: 0;
}

.status {
    font-size: 0.8rem;
    color: #10b981;
    margin: 0;
}

.chat-messages {
    flex: 1;
    padding: 1.5rem;
    overflow-y: auto;
    background-color: var(--bg-main);
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.message {
    max-width: 80%;
    display: flex;
}

.message.user {
    align-self: flex-end;
}

.message.ai {
    align-self: flex-start;
}

.message-content {
    padding: 0.8rem 1.2rem;
    border-radius: 15px;
    line-height: 1.5;
}

.message.user .message-content {
    background-color: var(--primary-color);
    color: white;
    border-bottom-right-radius: 5px;
}

.message.ai .message-content {
    background-color: white;
    color: var(--text-main);
    border: 1px solid var(--border-color);
    border-bottom-left-radius: 5px;
}

.suggestions {
    padding: 1rem;
    background-color: white;
    border-top: 1px solid var(--border-color);
    display: flex;
    gap: 0.5rem;
    overflow-x: auto;
    white-space: nowrap;
}

.suggestions::-webkit-scrollbar {
    height: 4px;
}

.suggestions::-webkit-scrollbar-thumb {
    background-color: var(--border-color);
    border-radius: 4px;
}

.suggestion-btn {
    background-color: var(--bg-main);
    border: 1px solid var(--border-color);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
    color: var(--text-main);
}

.suggestion-btn:hover {
    background-color: #e2e8f0;
}

.chat-input-area {
    padding: 1rem;
    background-color: white;
}

#chatForm {
    display: flex;
    gap: 0.5rem;
}

#messageInput {
    flex: 1;
    padding: 0.8rem 1rem;
    border: 1px solid var(--border-color);
    border-radius: 25px;
    outline: none;
    font-size: 1rem;
}

#messageInput:focus {
    border-color: var(--primary-color);
}

.btn-icon {
    width: 45px;
    height: 45px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
}

.typing-indicator {
    padding: 0.8rem 1.2rem;
    background-color: white;
    border: 1px solid var(--border-color);
    border-radius: 15px;
    border-bottom-left-radius: 5px;
    align-self: flex-start;
    display: flex;
    gap: 5px;
}

.typing-dot {
    width: 8px;
    height: 8px;
    background-color: #cbd5e1;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) { animation-delay: 0s; }
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-5px); }
}

@media (max-width: 768px) {
    .chat-container {
        height: calc(100vh - var(--header-height) - 2rem);
    }
    
    .message {
        max-width: 90%;
    }
}
""",
    "static/js/main.js": """document.addEventListener('DOMContentLoaded', () => {
    // Sidebar toggle for mobile
    const openSidebarBtn = document.getElementById('openSidebar');
    const closeSidebarBtn = document.getElementById('closeSidebar');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (openSidebarBtn && sidebar && overlay) {
        openSidebarBtn.addEventListener('click', () => {
            sidebar.classList.add('open');
            overlay.classList.add('active');
        });
        
        const closeSidebar = () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        };
        
        if (closeSidebarBtn) {
            closeSidebarBtn.addEventListener('click', closeSidebar);
        }
        
        overlay.addEventListener('click', closeSidebar);
    }

    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(msg => {
                msg.style.opacity = '0';
                msg.style.transition = 'opacity 0.5s ease';
                setTimeout(() => msg.remove(), 500);
            });
        }, 5000);
    }
});
""",
    "static/js/chat.js": """document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    const clearChatBtn = document.getElementById('clearChat');
    const suggestions = document.getElementById('suggestions');
    
    // Auto-scroll to bottom
    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };
    
    // Add a message to the chat UI
    const appendMessage = (text, sender) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        
        msgDiv.appendChild(contentDiv);
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    };
    
    // Add typing indicator
    const showTyping = () => {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai typing-message';
        typingDiv.id = 'typingIndicator';
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        
        typingDiv.appendChild(indicator);
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    };
    
    // Remove typing indicator
    const hideTyping = () => {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    };
    
    // Send message to server
    const sendMessage = async (message) => {
        if (!message.trim()) return;
        
        // Hide suggestions after first message
        if (suggestions) {
            suggestions.style.display = 'none';
        }
        
        appendMessage(message, 'user');
        messageInput.value = '';
        
        showTyping();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            hideTyping();
            
            if (response.ok) {
                appendMessage(data.message, 'ai');
            } else {
                appendMessage('Sorry, an error occurred. Please try again.', 'ai');
            }
        } catch (error) {
            hideTyping();
            appendMessage('Connection error. Please check your network.', 'ai');
        }
    };
    
    // Form submission
    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            sendMessage(messageInput.value);
        });
    }
    
    // Handle suggestion buttons (global function)
    window.sendSuggestion = (text) => {
        sendMessage(text);
    };
    
    // Clear chat
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', () => {
            // Keep only the first welcome message
            const welcomeMsg = chatMessages.firstElementChild;
            chatMessages.innerHTML = '';
            if (welcomeMsg) {
                chatMessages.appendChild(welcomeMsg);
            }
            if (suggestions) {
                suggestions.style.display = 'flex';
            }
        });
    }
});
""",
    "README.md": """# AI Student Mentor

## Description
A personalized AI Academic Mentor application designed to help students learn effectively. This is Phase 1 of the project, which establishes the foundational web application architecture, user authentication, profile management, and a functional chat interface.

## Features (Phase 1)
- Modern, responsive landing page
- Student Registration & Login with secure password hashing
- Session-based Authentication
- Student Dashboard with progress tracking UI
- Profile Management
- Fully functional Chat UI with typing indicators and suggestions
- SQLite Database integration via SQLAlchemy
- Clean and extensible architecture ready for Phase 2 AI integration

## Tech Stack
- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login
- **Frontend:** HTML5, CSS3, JavaScript, FontAwesome
- **Database:** SQLite

## Folder Structure
```
AI-Student-Mentor/
├── app.py                 # Application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Dependencies
├── database/              # SQLite database storage
├── models/                # SQLAlchemy models (user, etc.)
├── routes/                # Flask Blueprints (auth, dashboard, chat)
├── services/              # Business logic (ai_service)
├── templates/             # HTML templates
└── static/                # CSS, JS, and Images
```

## Installation
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\\Scripts\\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Environment Variables
Create a `.env` file in the root directory (refer to `.env.example`):
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///database/database.db
```

## Database Initialization
The database is initialized automatically when you run the application for the first time.

## Run Command
Start the Flask development server:
```
python app.py
```
Then open your browser and navigate to `http://127.0.0.1:5000`

## Future Phases (Phase 2 & 3)
- Real AI chatbot integration (OpenAI/Anthropic)
- Voice input and Text-to-Speech
- AI question understanding and academic explanations
- Smart Quizzes generated from learning history
- Document upload and analysis
- Advanced learning analytics
""",
    ".env.example": """SECRET_KEY=super-secret-key-for-development
DATABASE_URL=sqlite:///database/database.db
"""
}

for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Scaffolding complete.")
