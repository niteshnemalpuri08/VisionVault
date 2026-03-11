from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False) 
    role = db.Column(db.String(20), nullable=False) # 'student', 'teacher', 'parent'
    name = db.Column(db.String(100), nullable=False)
    
    # Teacher Fields
    section = db.Column(db.String(10), nullable=True) 
    
    # Parent Field (Links to Student)
    child_roll = db.Column(db.String(80), nullable=True) 

    # Student Fields
    class_name = db.Column(db.String(50), nullable=True)
    parent_email = db.Column(db.String(120), nullable=True)
    parent_phone = db.Column(db.String(20), nullable=True)
    
    performance = db.relationship('StudentPerformance', backref='student', uselist=False)

class StudentPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Marks
    math_marks = db.Column(db.Float, default=0)
    physics_marks = db.Column(db.Float, default=0)
    chemistry_marks = db.Column(db.Float, default=0)
    cs_marks = db.Column(db.Float, default=0)
    english_marks = db.Column(db.Float, default=0)
    pe_marks = db.Column(db.Float, default=0)
    
    # Attendance
    total_classes = db.Column(db.Integer, default=60)
    present_classes = db.Column(db.Integer, default=0)
    attendance = db.Column(db.Float, default=0)
    
    avg_marks = db.Column(db.Float, default=0)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)

# --- THIS WAS MISSING ---
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(80), nullable=False)   # e.g., 't01' or 'p_24cse001'
    receiver = db.Column(db.String(80), nullable=False) # e.g., 'p_24cse001' or 't01'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)