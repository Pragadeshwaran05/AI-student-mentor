from models.database import db
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
