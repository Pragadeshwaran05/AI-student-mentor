import os

base_dir = r"c:\Users\Pragadesh\OneDrive\Desktop\AI Student Mentor"

# Update requirements.txt
with open(os.path.join(base_dir, "requirements.txt"), "a") as f:
    f.write("google-generativeai==0.8.3\ngTTS==2.5.1\n")

files = {
    "config.py": """import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
""",
    "models/chat.py": """from models.database import db
from datetime import datetime

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), default="New Conversation")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade="all, delete-orphan")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender = db.Column(db.String(50), nullable=False) # 'user' or 'ai'
    message = db.Column(db.Text, nullable=False)
    mode = db.Column(db.String(50)) # e.g., 'explain', 'quiz', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
""",
    "services/ai_service.py": """import os
import google.generativeai as genai
from flask import current_app

class AIService:
    @staticmethod
    def _get_system_instruction(user, mode="Explain"):
        department = user.department or "General"
        year = user.year or "1st Year"
        style = user.learning_style or "Reading"
        
        base_instruction = (
            f"You are a supportive, knowledgeable AI Academic Mentor. "
            f"Your student is a {year} student in the {department} department. "
            f"Their preferred learning style is {style}. Tailor your explanations accordingly. "
            "IMPORTANT: Be helpful and encouraging. If you are uncertain about a fact, explicitly say: "
            "'I’m not fully certain. Please verify this with your course material or instructor.'"
        )
        
        mode_instructions = {
            "Explain": "Provide a comprehensive explanation. 1. Simple explanation. 2. Technical explanation. 3. Example. 4. Important points. 5. Common mistakes. 6. A follow-up question to check understanding.",
            "Simple Explanation": "Provide a very simple, beginner-friendly explanation using analogies. Avoid heavy jargon.",
            "Detailed Explanation": "Provide a deep, technical, and detailed explanation suitable for an advanced student.",
            "Example": "Focus primarily on providing clear, practical examples or case studies to illustrate the concept.",
            "Quiz Me": "Do not explain the concept. Instead, ask a challenging question about the topic to test the student's knowledge.",
            "Summarize": "Provide a brief, bulleted summary of the topic.",
            "Revision": "Provide quick flashcard-style points for rapid revision of the topic."
        }
        
        instruction = base_instruction + " \\n\\nMODE INSTRUCTION: " + mode_instructions.get(mode, mode_instructions["Explain"])
        return instruction

    @staticmethod
    def get_response(user, message_history, new_message, mode="Explain"):
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            return "Error: GEMINI_API_KEY is not configured in the environment. Please add it to your .env file."
        
        genai.configure(api_key=api_key)
        
        system_instruction = AIService._get_system_instruction(user, mode)
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        
        history = []
        for msg in message_history:
            role = "model" if msg.sender == "ai" else "user"
            history.append({"role": role, "parts": [msg.message]})
            
        chat = model.start_chat(history=history)
        
        try:
            response = chat.send_message(new_message)
            return response.text
        except Exception as e:
            return f"I encountered an error while thinking. Please try again. (Error: {str(e)})"
""",
    "services/speech_service.py": """import os
import uuid
import google.generativeai as genai
from gtts import gTTS
from flask import current_app

class SpeechService:
    @staticmethod
    def speech_to_text(audio_file_path):
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            return {"transcript": "", "status": "error", "error": "API key not configured."}
            
        genai.configure(api_key=api_key)
        
        try:
            audio_file = genai.upload_file(path=audio_file_path)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([
                "Please accurately transcribe this audio. Output ONLY the transcript without any extra text or formatting.",
                audio_file
            ])
            
            # Clean up the file from Gemini servers
            genai.delete_file(audio_file.name)
            
            # Calculate simple stats
            words = response.text.split()
            word_count = len(words)
            
            return {
                "transcript": response.text.strip(),
                "status": "success",
                "word_count": word_count,
                "detected_language": "Unknown (Auto-detected)"
            }
        except Exception as e:
            return {"transcript": "", "status": "error", "error": str(e)}

    @staticmethod
    def text_to_speech(text, output_dir):
        try:
            tts = gTTS(text=text, lang='en')
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(output_dir, filename)
            tts.save(filepath)
            return {"audio_url": f"/uploads/{filename}", "status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
""",
    "routes/chat.py": """import os
from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from models.database import db
from models.chat import Conversation, Message
from services.ai_service import AIService
from services.speech_service import SpeechService
import uuid

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
@login_required
def index():
    # Load all conversations for the sidebar
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    return render_template('chat.html', conversations=conversations)

@chat_bp.route('/api/conversations', methods=['POST'])
@login_required
def create_conversation():
    conv = Conversation(user_id=current_user.id, title="New Conversation")
    db.session.add(conv)
    db.session.commit()
    return jsonify({"id": conv.id, "title": conv.title})

@chat_bp.route('/api/conversations/<int:conv_id>', methods=['GET'])
@login_required
def get_conversation(conv_id):
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at.asc()).all()
    
    return jsonify({
        "id": conv.id,
        "title": conv.title,
        "messages": [
            {
                "id": m.id,
                "sender": m.sender,
                "message": m.message,
                "mode": m.mode,
                "created_at": m.created_at.isoformat()
            } for m in messages
        ]
    })

@chat_bp.route('/api/conversations/<int:conv_id>', methods=['DELETE'])
@login_required
def delete_conversation(conv_id):
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    db.session.delete(conv)
    db.session.commit()
    return jsonify({"status": "success"})

@chat_bp.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.json
    message_text = data.get('message', '')
    mode = data.get('mode', 'Explain')
    conv_id = data.get('conversation_id')
    
    if not message_text:
        return jsonify({'error': 'Message is required'}), 400
        
    if not conv_id:
        # Create a new conversation if none provided
        conv = Conversation(user_id=current_user.id, title=message_text[:30] + "..." if len(message_text) > 30 else message_text)
        db.session.add(conv)
        db.session.commit()
        conv_id = conv.id
    else:
        conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
        # Update title if it's the first real message
        if conv.title == "New Conversation":
            conv.title = message_text[:30] + "..." if len(message_text) > 30 else message_text
            
    # Save user message
    user_msg = Message(conversation_id=conv_id, sender='user', message=message_text, mode=mode)
    db.session.add(user_msg)
    db.session.commit()
    
    # Get conversation history (excluding the one we just added)
    history = Message.query.filter_by(conversation_id=conv_id).order_by(Message.created_at.asc()).all()[:-1]
    
    # Get AI response
    response_text = AIService.get_response(current_user, history, message_text, mode)
    
    # Save AI message
    ai_msg = Message(conversation_id=conv_id, sender='ai', message=response_text, mode=mode)
    conv.updated_at = db.func.now()
    db.session.add(ai_msg)
    db.session.commit()
    
    return jsonify({
        'message': response_text,
        'conversation_id': conv_id
    })

@chat_bp.route('/api/speech-to-text', methods=['POST'])
@login_required
def api_speech_to_text():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
        
    audio_file = request.files['audio']
    upload_dir = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save temporarily
    filepath = os.path.join(upload_dir, f"temp_{uuid.uuid4().hex}.webm")
    audio_file.save(filepath)
    
    # Process
    result = SpeechService.speech_to_text(filepath)
    
    # Cleanup
    if os.path.exists(filepath):
        os.remove(filepath)
        
    if result["status"] == "error":
        return jsonify(result), 500
        
    return jsonify(result)

@chat_bp.route('/api/text-to-speech', methods=['POST'])
@login_required
def api_text_to_speech():
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({"error": "Text is required"}), 400
        
    upload_dir = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    result = SpeechService.text_to_speech(text, upload_dir)
    
    if result["status"] == "error":
        return jsonify(result), 500
        
    return jsonify(result)

@chat_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(current_app.root_path, 'uploads'), filename)
""",
    "app.py": """from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models.database import db
from models.user import User
from models.chat import Conversation, Message
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
    "templates/chat.html": """{% extends "base.html" %}

{% block head %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/chat.css') }}">
<!-- Add Marked.js for Markdown parsing -->
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<!-- Add Highlight.js for code formatting -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
{% endblock %}

{% block content %}
<div class="chat-layout">
    <!-- Conversation History Sidebar -->
    <div class="conversations-sidebar">
        <div class="sidebar-header">
            <h3>History</h3>
            <button class="btn btn-sm btn-primary" id="newChatBtn"><i class="fas fa-plus"></i> New</button>
        </div>
        <div class="conversations-list" id="conversationsList">
            {% for conv in conversations %}
            <div class="conversation-item" data-id="{{ conv.id }}">
                <span class="conv-title">{{ conv.title }}</span>
                <button class="delete-conv-btn" onclick="deleteConversation({{ conv.id }}, event)"><i class="fas fa-trash"></i></button>
            </div>
            {% endfor %}
            {% if not conversations %}
            <div class="empty-conversations">No past conversations</div>
            {% endif %}
        </div>
    </div>

    <!-- Main Chat Area -->
    <div class="chat-container">
        <div class="chat-header">
            <div class="mentor-info">
                <div class="mentor-avatar"><i class="fas fa-robot"></i></div>
                <div>
                    <h2>AI Mentor</h2>
                    <p class="status">Online | <span id="currentConvTitle">New Conversation</span></p>
                </div>
            </div>
            <div class="chat-actions">
                <select id="aiMode" class="mode-selector">
                    <option value="Explain">Explain</option>
                    <option value="Simple Explanation">Simple Explanation</option>
                    <option value="Detailed Explanation">Detailed Explanation</option>
                    <option value="Example">Example</option>
                    <option value="Quiz Me">Quiz Me</option>
                    <option value="Summarize">Summarize</option>
                    <option value="Revision">Revision</option>
                </select>
                <button class="btn btn-sm btn-outline" id="clearChat"><i class="fas fa-eraser"></i> Clear</button>
            </div>
        </div>
        
        <div class="speech-analysis" id="speechAnalysis" style="display: none;">
            <h4><i class="fas fa-microphone-alt"></i> Speech Analysis</h4>
            <div class="analysis-stats">
                <span id="saDuration">Duration: 0s</span> | 
                <span id="saWords">Words: 0</span> |
                <span id="saStatus">Status: Success</span>
            </div>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message ai">
                <div class="message-content">
                    Hello {{ current_user.full_name.split()[0] }}! I'm your AI Academic Mentor. How can I help you with your studies today?
                </div>
            </div>
        </div>
        
        <div class="suggestions" id="suggestions">
            <button class="suggestion-btn" onclick="sendSuggestion('Explain recursion with an example')">Explain recursion with an example</button>
            <button class="suggestion-btn" onclick="sendSuggestion('Teach me OS scheduling')">Teach me OS scheduling</button>
            <button class="suggestion-btn" onclick="sendSuggestion('Quiz me on DBMS')">Quiz me on DBMS</button>
            <button class="suggestion-btn" onclick="sendSuggestion('Give me a Java coding problem')">Give me a Java coding problem</button>
            <button class="suggestion-btn" onclick="sendSuggestion('Summarize this topic')">Summarize this topic</button>
        </div>
        
        <div class="chat-input-area">
            <form id="chatForm">
                <button type="button" class="btn-icon voice-btn" id="recordBtn" title="Hold to speak or click to toggle">
                    <i class="fas fa-microphone"></i>
                </button>
                <input type="text" id="messageInput" placeholder="Ask anything..." autocomplete="off">
                <button type="submit" class="btn btn-primary btn-icon"><i class="fas fa-paper-plane"></i></button>
            </form>
            <div id="recordingIndicator" class="recording-indicator" style="display: none;">
                <span class="pulse"></span> Recording... Click mic to stop.
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/chat.js') }}"></script>
{% endblock %}
""",
    "static/css/chat.css": """.chat-layout {
    display: flex;
    gap: 1.5rem;
    height: calc(100vh - var(--header-height) - 4rem);
}

.conversations-sidebar {
    width: 250px;
    background-color: var(--bg-card);
    border-radius: 10px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.sidebar-header {
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.conversations-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
}

.conversation-item {
    padding: 0.8rem;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
    transition: background-color 0.2s;
}

.conversation-item:hover, .conversation-item.active {
    background-color: var(--bg-main);
}

.conv-title {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 0.9rem;
    flex: 1;
}

.delete-conv-btn {
    background: none;
    border: none;
    color: var(--danger-color);
    cursor: pointer;
    opacity: 0.5;
}

.delete-conv-btn:hover {
    opacity: 1;
}

.empty-conversations {
    text-align: center;
    padding: 2rem 1rem;
    color: var(--text-muted);
    font-size: 0.9rem;
}

.chat-container {
    flex: 1;
    background-color: var(--bg-card);
    border-radius: 10px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
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

.chat-actions {
    display: flex;
    gap: 10px;
    align-items: center;
}

.mode-selector {
    padding: 0.3rem 0.5rem;
    border-radius: 4px;
    border: 1px solid var(--border-color);
    font-size: 0.85rem;
}

.chat-messages {
    flex: 1;
    padding: 1.5rem;
    overflow-y: auto;
    background-color: var(--bg-main);
    display: flex;
    flex-direction: column;
    gap: 1rem;
    scroll-behavior: smooth;
}

.message {
    max-width: 85%;
    display: flex;
    flex-direction: column;
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
    line-height: 1.6;
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

/* Markdown styling inside messages */
.message.ai .message-content p {
    margin-bottom: 0.5rem;
}
.message.ai .message-content pre {
    background: #f6f8fa;
    padding: 10px;
    border-radius: 5px;
    overflow-x: auto;
    margin: 10px 0;
}
.message.ai .message-content code {
    font-family: monospace;
    background: #f0f0f0;
    padding: 2px 4px;
    border-radius: 3px;
}
.message.ai .message-content pre code {
    background: none;
    padding: 0;
}

.message-actions {
    display: flex;
    gap: 10px;
    margin-top: 5px;
    padding: 0 10px;
    align-self: flex-start;
}

.msg-action-btn {
    background: none;
    border: none;
    color: var(--text-muted);
    font-size: 0.85rem;
    cursor: pointer;
}

.msg-action-btn:hover {
    color: var(--primary-color);
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
    position: relative;
}

#chatForm {
    display: flex;
    gap: 0.5rem;
    align-items: center;
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

.voice-btn {
    background: none;
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.3s;
}

.voice-btn:hover {
    color: var(--primary-color);
    border-color: var(--primary-color);
}

.voice-btn.recording {
    background-color: var(--danger-color);
    color: white;
    border-color: var(--danger-color);
    animation: pulse 1.5s infinite;
}

.recording-indicator {
    position: absolute;
    top: -30px;
    left: 20px;
    background-color: var(--bg-card);
    padding: 5px 15px;
    border-radius: 15px;
    font-size: 0.85rem;
    color: var(--danger-color);
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
    gap: 8px;
}

.pulse {
    width: 10px;
    height: 10px;
    background-color: var(--danger-color);
    border-radius: 50%;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(230, 57, 70, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(230, 57, 70, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(230, 57, 70, 0); }
}

.speech-analysis {
    padding: 0.5rem 1.5rem;
    background-color: #f8f9fa;
    border-bottom: 1px solid var(--border-color);
    font-size: 0.85rem;
}

.speech-analysis h4 {
    margin-bottom: 0.2rem;
    color: var(--primary-color);
}

.analysis-stats {
    color: var(--text-muted);
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
    .chat-layout {
        flex-direction: column;
    }
    .conversations-sidebar {
        width: 100%;
        height: 150px;
    }
    .chat-container {
        height: calc(100vh - var(--header-height) - 150px - 2rem);
    }
    .message {
        max-width: 90%;
    }
}
""",
    "static/js/chat.js": """document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    const clearChatBtn = document.getElementById('clearChat');
    const suggestions = document.getElementById('suggestions');
    const aiMode = document.getElementById('aiMode');
    
    // Voice Elements
    const recordBtn = document.getElementById('recordBtn');
    const recordingIndicator = document.getElementById('recordingIndicator');
    const speechAnalysis = document.getElementById('speechAnalysis');
    
    // Conversation State
    let currentConversationId = null;
    
    // Marked configuration for markdown
    marked.setOptions({
        highlight: function(code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        }
    });
    
    // Auto-scroll to bottom
    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };
    
    // Play TTS
    window.playAudio = async (text, btnElement) => {
        const icon = btnElement.querySelector('i');
        icon.className = 'fas fa-spinner fa-spin';
        
        try {
            const response = await fetch('/api/text-to-speech', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            const data = await response.json();
            
            if (response.ok && data.status === "success") {
                const audio = new Audio(data.audio_url);
                icon.className = 'fas fa-stop';
                
                audio.play();
                
                audio.onended = () => {
                    icon.className = 'fas fa-volume-up';
                };
                
                btnElement.onclick = () => {
                    audio.pause();
                    audio.currentTime = 0;
                    icon.className = 'fas fa-volume-up';
                    btnElement.onclick = () => window.playAudio(text, btnElement);
                };
            } else {
                icon.className = 'fas fa-volume-mute';
                console.error("TTS Error:", data.error);
            }
        } catch (e) {
            icon.className = 'fas fa-volume-mute';
            console.error("TTS Request Failed:", e);
        }
    };
    
    // Add a message to the chat UI
    const appendMessage = (text, sender, isHistory=false) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (sender === 'ai') {
            contentDiv.innerHTML = marked.parse(text);
            
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'message-actions';
            
            const copyBtn = document.createElement('button');
            copyBtn.className = 'msg-action-btn';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
            copyBtn.title = 'Copy';
            copyBtn.onclick = () => { navigator.clipboard.writeText(text); copyBtn.innerHTML = '<i class="fas fa-check"></i>'; setTimeout(() => copyBtn.innerHTML = '<i class="fas fa-copy"></i>', 2000); };
            
            const ttsBtn = document.createElement('button');
            ttsBtn.className = 'msg-action-btn';
            ttsBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
            ttsBtn.title = 'Listen';
            
            // Clean text for TTS (remove markdown)
            const cleanText = text.replace(/[#*`_]/g, '');
            ttsBtn.onclick = function() { window.playAudio(cleanText, this); };
            
            actionsDiv.appendChild(copyBtn);
            actionsDiv.appendChild(ttsBtn);
            
            msgDiv.appendChild(contentDiv);
            msgDiv.appendChild(actionsDiv);
        } else {
            contentDiv.textContent = text;
            msgDiv.appendChild(contentDiv);
        }
        
        chatMessages.appendChild(msgDiv);
        
        if (!isHistory) {
            scrollToBottom();
        }
    };
    
    // Show typing
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
    
    const hideTyping = () => {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    };
    
    // Load conversation
    window.loadConversation = async (id, title) => {
        currentConversationId = id;
        document.getElementById('currentConvTitle').textContent = title;
        
        // Highlight active
        document.querySelectorAll('.conversation-item').forEach(el => el.classList.remove('active'));
        const activeEl = document.querySelector(`.conversation-item[data-id="${id}"]`);
        if (activeEl) activeEl.classList.add('active');
        
        // Clear chat
        chatMessages.innerHTML = '';
        if (suggestions) suggestions.style.display = 'none';
        
        try {
            const res = await fetch(`/api/conversations/${id}`);
            const data = await res.json();
            
            data.messages.forEach(msg => {
                appendMessage(msg.message, msg.sender, true);
            });
            scrollToBottom();
        } catch (e) {
            console.error("Failed to load conversation", e);
        }
    };
    
    // Delete conversation
    window.deleteConversation = async (id, event) => {
        event.stopPropagation();
        if(!confirm("Delete this conversation?")) return;
        
        try {
            const res = await fetch(`/api/conversations/${id}`, { method: 'DELETE' });
            if (res.ok) {
                const el = document.querySelector(`.conversation-item[data-id="${id}"]`);
                if (el) el.remove();
                
                if (currentConversationId === id) {
                    startNewChat();
                }
            }
        } catch(e) {
            console.error(e);
        }
    };
    
    // Setup click handlers for existing conversations
    document.querySelectorAll('.conversation-item').forEach(el => {
        el.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                loadConversation(el.dataset.id, el.querySelector('.conv-title').textContent);
            }
        });
    });
    
    const startNewChat = () => {
        currentConversationId = null;
        document.getElementById('currentConvTitle').textContent = "New Conversation";
        document.querySelectorAll('.conversation-item').forEach(el => el.classList.remove('active'));
        
        chatMessages.innerHTML = `
            <div class="message ai">
                <div class="message-content">
                    Hello! I'm your AI Academic Mentor. How can I help you with your studies today?
                </div>
            </div>
        `;
        if (suggestions) suggestions.style.display = 'flex';
    };
    
    document.getElementById('newChatBtn')?.addEventListener('click', startNewChat);
    
    // Send message to server
    const sendMessage = async (message) => {
        if (!message.trim()) return;
        
        if (suggestions) suggestions.style.display = 'none';
        
        const mode = aiMode ? aiMode.value : 'Explain';
        appendMessage(message, 'user');
        messageInput.value = '';
        
        showTyping();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message,
                    mode: mode,
                    conversation_id: currentConversationId
                })
            });
            
            const data = await response.json();
            hideTyping();
            
            if (response.ok) {
                appendMessage(data.message, 'ai');
                
                // If it was a new conversation, set the ID and reload sidebar ideally
                if (!currentConversationId && data.conversation_id) {
                    currentConversationId = data.conversation_id;
                    // Simply reload page to update sidebar for Phase 2 simplicity
                    // location.reload();
                }
            } else {
                appendMessage('Sorry, an error occurred. Please try again. ' + (data.error || ''), 'ai');
            }
        } catch (error) {
            hideTyping();
            appendMessage('Connection error. Please check your network.', 'ai');
        }
    };
    
    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            sendMessage(messageInput.value);
        });
    }
    
    window.sendSuggestion = (text) => sendMessage(text);
    if (clearChatBtn) clearChatBtn.addEventListener('click', startNewChat);

    // --- Voice Recording Logic ---
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let recordStartTime;
    
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        recordBtn.addEventListener('click', async () => {
            if (isRecording) {
                // Stop recording
                mediaRecorder.stop();
                isRecording = false;
                recordBtn.classList.remove('recording');
                recordingIndicator.style.display = 'none';
                return;
            }
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = e => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = async () => {
                    const duration = Math.round((Date.now() - recordStartTime) / 1000);
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    
                    // Stop tracks to release mic
                    stream.getTracks().forEach(track => track.stop());
                    
                    // Show processing state
                    recordBtn.querySelector('i').className = 'fas fa-spinner fa-spin';
                    
                    const formData = new FormData();
                    formData.append('audio', audioBlob);
                    
                    try {
                        const res = await fetch('/api/speech-to-text', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await res.json();
                        recordBtn.querySelector('i').className = 'fas fa-microphone';
                        
                        if (res.ok && data.status === 'success') {
                            messageInput.value = data.transcript;
                            
                            // Show analysis
                            document.getElementById('saDuration').textContent = `Duration: ${duration}s`;
                            document.getElementById('saWords').textContent = `Words: ${data.word_count}`;
                            speechAnalysis.style.display = 'block';
                            
                            // Optionally auto-send: sendMessage(data.transcript);
                        } else {
                            alert("Speech recognition failed: " + data.error);
                        }
                    } catch (e) {
                        recordBtn.querySelector('i').className = 'fas fa-microphone';
                        alert("Network error during speech recognition.");
                    }
                };
                
                mediaRecorder.start();
                isRecording = true;
                recordStartTime = Date.now();
                recordBtn.classList.add('recording');
                recordingIndicator.style.display = 'flex';
                speechAnalysis.style.display = 'none';
                
            } catch (e) {
                console.error("Mic access denied", e);
                alert("Microphone access denied. Please allow microphone access to use voice features.");
            }
        });
    } else {
        recordBtn.style.display = 'none'; // Not supported
    }
});
"""
}

for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Phase 2 scaffolding complete.")
