from flask import Flask, render_template
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
    from routes.quizzes import quizzes_bp
    from routes.planner import planner_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(quizzes_bp)
    app.register_blueprint(planner_bp)
    
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
