import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    roll = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)  # Keep for backward compatibility
    section = db.Column(db.String(10), default='A')
    attendance = db.Column(db.Float, default=0.0)
    avg_marks = db.Column(db.Float, default=0.0)

    # Marks as separate columns
    math_marks = db.Column(db.Float, default=0.0)
    physics_marks = db.Column(db.Float, default=0.0)
    chemistry_marks = db.Column(db.Float, default=0.0)
    cs_marks = db.Column(db.Float, default=0.0)
    english_marks = db.Column(db.Float, default=0.0)

    # Relationship with parents
    parents = db.relationship('Parent', backref='student', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'username': self.username,
            'name': self.name,
            'roll': self.roll,
            'email': self.email,
            'class': self.class_name,
            'attendance': self.attendance,
            'avg_marks': self.avg_marks,
            'marks': {
                'math': self.math_marks,
                'physics': self.physics_marks,
                'chemistry': self.chemistry_marks,
                'cs': self.cs_marks,
                'english': self.english_marks
            }
        }

class Teacher(db.Model):
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)  # Keep for backward compatibility
    access_level = db.Column(db.String(20), default='section')  # 'section', 'department', 'admin'

    # Relationships to mapping tables
    departments = db.relationship('TeacherDepartment', backref='teacher', lazy=True)
    sections = db.relationship('TeacherSection', backref='teacher', lazy=True)
    subjects = db.relationship('TeacherSubject', backref='teacher', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'access_level': self.access_level,
            'departments': [d.to_dict() for d in self.departments if d.is_active],
            'sections': [s.to_dict() for s in self.sections if s.is_active],
            'subjects': [s.to_dict() for s in self.subjects if s.is_active]
        }

class Parent(db.Model):
    __tablename__ = 'parents'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    student_roll = db.Column(db.String(20), db.ForeignKey('students.roll'), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'student_roll': self.student_roll
        }

class InternalMark(db.Model):
    __tablename__ = 'internal_marks'

    id = db.Column(db.Integer, primary_key=True)
    student_roll = db.Column(db.String(20), db.ForeignKey('students.roll'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    date_assessed = db.Column(db.Date, nullable=False)
    teacher_username = db.Column(db.String(50), db.ForeignKey('teachers.username'), nullable=False)
    remarks = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'student_roll': self.student_roll,
            'subject': self.subject,
            'assessment_type': self.assessment_type,
            'marks': self.marks,
            'max_marks': self.max_marks,
            'date_assessed': self.date_assessed.isoformat() if self.date_assessed else None,
            'teacher_username': self.teacher_username,
            'remarks': self.remarks
        }

class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(50), nullable=False)
    assigned_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    teacher_username = db.Column(db.String(50), db.ForeignKey('teachers.username'), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'subject': self.subject,
            'assigned_date': self.assigned_date.isoformat() if self.assigned_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'max_marks': self.max_marks,
            'teacher_username': self.teacher_username,
            'class_name': self.class_name
        }

class AssignmentSubmission(db.Model):
    __tablename__ = 'assignment_submissions'

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_roll = db.Column(db.String(20), db.ForeignKey('students.roll'), nullable=False)
    submission_date = db.Column(db.Date)
    marks_obtained = db.Column(db.Float)
    status = db.Column(db.String(20), nullable=False, default='pending')
    submission_file = db.Column(db.String(500))
    feedback = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'assignment_id': self.assignment_id,
            'student_roll': self.student_roll,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'marks_obtained': self.marks_obtained,
            'status': self.status,
            'submission_file': self.submission_file,
            'feedback': self.feedback
        }

class StudentBehavior(db.Model):
    __tablename__ = 'student_behavior'

    id = db.Column(db.Integer, primary_key=True)
    student_roll = db.Column(db.String(20), db.ForeignKey('students.roll'), nullable=False)
    behavior_type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    date_recorded = db.Column(db.Date, nullable=False)
    recorded_by = db.Column(db.String(50), db.ForeignKey('teachers.username'), nullable=False)
    remarks = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'student_roll': self.student_roll,
            'type': self.behavior_type,
            'description': self.description,
            'points': self.points,
            'date_recorded': self.date_recorded.isoformat() if self.date_recorded else None,
            'recorded_by': self.recorded_by,
            'remarks': self.remarks
        }

class TeacherDepartment(db.Model):
    __tablename__ = 'teacher_departments'

    id = db.Column(db.Integer, primary_key=True)
    teacher_username = db.Column(db.String(50), db.ForeignKey('teachers.username'), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    assigned_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_username': self.teacher_username,
            'department': self.department,
            'assigned_date': self.assigned_date.isoformat() if self.assigned_date else None,
            'is_active': self.is_active
        }

class TeacherSection(db.Model):
    __tablename__ = 'teacher_sections'

    id = db.Column(db.Integer, primary_key=True)
    teacher_username = db.Column(db.String(50), db.ForeignKey('teachers.username'), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    assigned_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_username': self.teacher_username,
            'section': self.section,
            'class_name': self.class_name,
            'assigned_date': self.assigned_date.isoformat() if self.assigned_date else None,
            'is_active': self.is_active
        }

class TeacherSubject(db.Model):
    __tablename__ = 'teacher_subjects'

    id = db.Column(db.Integer, primary_key=True)
    teacher_username = db.Column(db.String(50), db.ForeignKey('teachers.username'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10))
    assigned_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_username': self.teacher_username,
            'subject': self.subject,
            'class_name': self.class_name,
            'section': self.section,
            'assigned_date': self.assigned_date.isoformat() if self.assigned_date else None,
            'is_active': self.is_active
        }


class SubjectAttendance(db.Model):
    __tablename__ = 'subject_attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_roll = db.Column(db.String(20), db.ForeignKey('students.roll'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    total_classes = db.Column(db.Integer, default=0, nullable=False)
    attended_classes = db.Column(db.Integer, default=0, nullable=False)
    attendance_percentage = db.Column(db.Float, default=0.0, nullable=False)
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationship to student
    student = db.relationship('Student', backref='subject_attendances')

    def to_dict(self):
        # Compute attendance percentage on-the-fly to ensure accuracy
        if self.total_classes and self.total_classes > 0:
            pct = round((self.attended_classes / float(self.total_classes)) * 100, 2)
        else:
            pct = 0.0

        return {
            'id': self.id,
            'student_roll': self.student_roll,
            'subject': self.subject,
            'total_classes': int(self.total_classes),
            'attended_classes': int(self.attended_classes),
            'present': int(self.attended_classes),
            'total': int(self.total_classes),
            'attendance_percentage': pct,
            'attendance': pct,  # compatibility field
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

    def update_percentage(self):
        """Calculate and update attendance percentage"""
        if self.total_classes > 0:
            self.attendance_percentage = (self.attended_classes / self.total_classes) * 100
        else:
            self.attendance_percentage = 0.0

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    student_roll = db.Column(db.String(20), db.ForeignKey('students.roll'), nullable=True)  # Null for general notifications
    teacher_username = db.Column(db.String(50), db.ForeignKey('teachers.username'), nullable=True)  # For teacher notifications
    parent_username = db.Column(db.String(50), db.ForeignKey('parents.username'), nullable=True)  # For parent notifications
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # academic, assignment, achievement, behavior, general
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    icon = db.Column(db.String(10), default='📢')  # Emoji icon

    def to_dict(self):
        return {
            'id': self.id,
            'student_roll': self.student_roll,
            'teacher_username': self.teacher_username,
            'parent_username': self.parent_username,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'priority': self.priority,
            'read': self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'icon': self.icon
        }

class WebhookEvent(db.Model):
    __tablename__ = 'webhook_events'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(200), unique=True, nullable=False)
    payload = db.Column(db.Text)
    received_at = db.Column(db.DateTime)
    processed = db.Column(db.Boolean, default=False)
    processed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'processed': self.processed,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
