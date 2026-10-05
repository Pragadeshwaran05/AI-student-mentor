from flask import Blueprint, render_template, request, redirect, url_for, flash
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
