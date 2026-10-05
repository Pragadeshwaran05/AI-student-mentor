from flask import Blueprint, render_template, request, jsonify
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
