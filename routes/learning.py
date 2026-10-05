import os
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
