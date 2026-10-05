import os
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
