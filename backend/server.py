import os
import sys
import datetime
# Ensure package imports resolve when running the module as a script from project root
if os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from backend.models import db, Student, Teacher, Parent, InternalMark, Assignment, AssignmentSubmission, StudentBehavior, TeacherDepartment, TeacherSection, TeacherSubject, SubjectAttendance, Notification, WebhookEvent
import jwt
import bcrypt
from functools import wraps
from backend.ml_app import bp as ml_bp

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance', 'erp.db'))}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(ml_bp, url_prefix='/api/ml')

# JWT token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(" ")[1] if " " in token else token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Health check endpoint for Render
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

# --- API endpoints ---
@app.route("/api/students", methods=["GET"])
@token_required
def get_students(current_user):
    try:
        students = Student.query.all()
        return jsonify([student.to_dict() for student in students])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/students/username/<username>", methods=["GET"])
@token_required
def get_student_by_username(current_user, username):
    try:
        student = Student.query.filter_by(username=username).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        return jsonify(student.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/students/<roll>", methods=["GET"])
@token_required
def get_student(current_user, roll):
    try:
        student = Student.query.filter_by(roll=roll).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        return jsonify(student.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/students/<roll>", methods=["PATCH"])
@token_required
def update_student(current_user, roll):
    try:
        data = request.get_json() or {}
        student = Student.query.filter_by(roll=roll).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        old_roll = student.roll
        # Update allowed fields
        for field in ['name', 'email', 'username', 'class_name', 'section', 'attendance', 'avg_marks']:
            if field in data:
                setattr(student, field, data[field])

        # Update marks (if provided as object)
        if 'marks' in data and isinstance(data['marks'], dict):
            m = data['marks']
            if 'math' in m: student.math_marks = float(m['math'])
            if 'physics' in m: student.physics_marks = float(m['physics'])
            if 'chemistry' in m: student.chemistry_marks = float(m['chemistry'])
            if 'cs' in m: student.cs_marks = float(m['cs'])
            if 'english' in m: student.english_marks = float(m['english'])

        # Handle roll change and propagate
        if 'roll' in data and data['roll'] and data['roll'] != old_roll:
            new_roll = data['roll']
            # Ensure new_roll isn't already taken
            if Student.query.filter_by(roll=new_roll).first():
                return jsonify({'error': 'Roll already exists'}), 400
            student.roll = new_roll
            # Propagate to related tables
            Parent.query.filter_by(student_roll=old_roll).update({'student_roll': new_roll}, synchronize_session='fetch')
            InternalMark.query.filter_by(student_roll=old_roll).update({'student_roll': new_roll}, synchronize_session='fetch')
            SubjectAttendance.query.filter_by(student_roll=old_roll).update({'student_roll': new_roll}, synchronize_session='fetch')
            AssignmentSubmission.query.filter_by(student_roll=old_roll).update({'student_roll': new_roll}, synchronize_session='fetch')
            StudentBehavior.query.filter_by(student_roll=old_roll).update({'student_roll': new_roll}, synchronize_session='fetch')

        db.session.commit()
        return jsonify({'status': 'success', 'student': student.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route("/api/teachers", methods=["GET"])
@token_required
def get_teachers(current_user):
    try:
        teachers = Teacher.query.all()
        return jsonify([teacher.to_dict() for teacher in teachers])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/parents", methods=["GET"])
@token_required
def get_parents(current_user):
    try:
        parents = Parent.query.all()
        return jsonify([parent.to_dict() for parent in parents])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers/<username>', methods=['PATCH'])
@token_required
def update_teacher(current_user, username):
    try:
        data = request.get_json() or {}
        teacher = Teacher.query.filter_by(username=username).first()
        if not teacher:
            return jsonify({'error': 'Teacher not found'}), 404

        old_username = teacher.username
        for field in ['name', 'email', 'department', 'access_level']:
            if field in data:
                setattr(teacher, field, data[field])

        if 'username' in data and data['username'] and data['username'] != old_username:
            new_username = data['username']
            if Teacher.query.filter_by(username=new_username).first():
                return jsonify({'error': 'Username already exists'}), 400
            teacher.username = new_username
            # Propagate
            TeacherSection.query.filter_by(teacher_username=old_username).update({'teacher_username': new_username}, synchronize_session='fetch')
            TeacherSubject.query.filter_by(teacher_username=old_username).update({'teacher_username': new_username}, synchronize_session='fetch')
            Assignment.query.filter_by(teacher_username=old_username).update({'teacher_username': new_username}, synchronize_session='fetch')
            InternalMark.query.filter_by(teacher_username=old_username).update({'teacher_username': new_username}, synchronize_session='fetch')
            StudentBehavior.query.filter_by(recorded_by=old_username).update({'recorded_by': new_username}, synchronize_session='fetch')

        db.session.commit()
        return jsonify({'status': 'success', 'teacher': teacher.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/parents/<username>', methods=['PATCH'])
@token_required
def update_parent(current_user, username):
    try:
        data = request.get_json() or {}
        parent = Parent.query.filter_by(username=username).first()
        if not parent:
            return jsonify({'error': 'Parent not found'}), 404

        for field in ['name', 'email']:
            if field in data:
                setattr(parent, field, data[field])

        # Change student_roll if requested and exists
        if 'student_roll' in data and data['student_roll'] != parent.student_roll:
            new_roll = data['student_roll']
            if not Student.query.filter_by(roll=new_roll).first():
                return jsonify({'error': 'Target student roll not found'}), 404
            parent.student_roll = new_roll

        db.session.commit()
        return jsonify({'status': 'success', 'parent': parent.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance', methods=['POST'])
@token_required
def submit_attendance(current_user):
    try:
        payload = request.get_json() or {}
        records = payload.get('attendance', [])
        if not isinstance(records, list):
            return jsonify({'status': 'error', 'message': 'Invalid attendance payload'}), 400

        for rec in records:
            roll = rec.get('roll')
            present = bool(rec.get('present'))
            if not roll:
                continue

            # Use a default 'General' subject for teacher-submitted daily attendance
            sa = SubjectAttendance.query.filter_by(student_roll=roll, subject='General').first()
            if not sa:
                sa = SubjectAttendance(student_roll=roll, subject='General', total_classes=1, attended_classes=1 if present else 0)
                sa.update_percentage()
                db.session.add(sa)
            else:
                sa.total_classes = sa.total_classes + 1
                sa.attended_classes = sa.attended_classes + (1 if present else 0)
                sa.update_percentage()

            # Update aggregated student attendance (average across subjects)
            student = Student.query.filter_by(roll=roll).first()
            if student:
                # recompute student's avg attendance from all subject attendance rows
                rows = SubjectAttendance.query.filter_by(student_roll=roll).all()
                if rows:
                    avg = sum(r.attendance_percentage for r in rows) / len(rows)
                    student.attendance = round(avg, 2)

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Attendance recorded'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/auth/login", methods=["POST"])
def login():

    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'student')

        user = None
        if role == 'student':
            user = Student.query.filter_by(username=username).first()
        elif role == 'teacher':
            user = Teacher.query.filter_by(username=username).first()
        elif role == 'parent':
            user = Parent.query.filter_by(username=username).first()

        if user and user.check_password(password):
            token = jwt.encode({
                'user': username,
                'type': role,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")

            # Ensure token is a string (PyJWT may return bytes on older versions)
            if isinstance(token, bytes):
                token = token.decode('utf-8')

            return jsonify({
                'status': 'ok',
                'username': username,
                'role': role,
                'name': user.name if hasattr(user, 'name') else username,
                'token': token
            })

        return jsonify({'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route("/api/subject-attendance", methods=["GET"])
@token_required
def get_subject_attendance(current_user):
    try:
        student_roll = request.args.get('student_roll')
        if not student_roll:
            return jsonify({'error': 'student_roll parameter required'}), 400

        attendances = SubjectAttendance.query.filter_by(student_roll=student_roll).all()
        return jsonify([att.to_dict() for att in attendances])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/departments', methods=['GET'])
@token_required
def get_departments(current_user):
    try:
        # Return distinct departments
        deps = db.session.query(Teacher.department).distinct().all()
        return jsonify([d[0] for d in deps if d[0]])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sections', methods=['GET'])
@token_required
def get_sections(current_user):
    try:
        secs = db.session.query(TeacherSection.section, TeacherSection.class_name).distinct().all()
        return jsonify([{'name': s[0], 'class_name': s[1]} for s in secs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/assignments", methods=["GET"])
@token_required
def get_assignments(current_user):
    try:
        class_name = request.args.get('class')
        subject = request.args.get('subject')

        query = Assignment.query
        if class_name:
            query = query.filter_by(class_name=class_name)
        if subject:
            query = query.filter_by(subject=subject)

        assignments = query.all()
        return jsonify([assignment.to_dict() for assignment in assignments])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/behavior", methods=["GET"])
@token_required
def get_behavior(current_user):
    try:
        student_roll = request.args.get('student_roll')
        if not student_roll:
            return jsonify({'error': 'student_roll parameter required'}), 400

        behaviors = StudentBehavior.query.filter_by(student_roll=student_roll).all()
        return jsonify([behavior.to_dict() for behavior in behaviors])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/internal-marks", methods=["GET"])
@token_required
def get_internal_marks(current_user):
    try:
        student_roll = request.args.get('student_roll')
        subject = request.args.get('subject')

        query = InternalMark.query
        if student_roll:
            query = query.filter_by(student_roll=student_roll)
        if subject:
            query = query.filter_by(subject=subject)

        marks = query.all()
        return jsonify([mark.to_dict() for mark in marks])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/teacher/<username>/dashboard", methods=["GET"])
@token_required
def get_teacher_dashboard(current_user, username):
    try:
        # Verify the current user matches the requested username
        if current_user != username:
            return jsonify({'error': 'Unauthorized access'}), 403

        # Get teacher info
        teacher = Teacher.query.filter_by(username=username).first()
        if not teacher:
            return jsonify({'error': 'Teacher not found'}), 404

        # Get teacher's sections and subjects
        teacher_sections = TeacherSection.query.filter_by(teacher_username=username).all()
        teacher_subjects = TeacherSubject.query.filter_by(teacher_username=username).all()

        # Get students in teacher's sections
        # Note: TeacherSection stores `section`, and Student has `section` column (added in migration)
        section_names = [ts.section for ts in teacher_sections]
        students_in_sections = Student.query.filter(Student.section.in_(section_names)).limit(40).all()

        # Calculate stats
        total_students = len(students_in_sections)

        # Calculate average attendance (simplified - using SubjectAttendance)
        attendance_records = []
        for student in students_in_sections:
            student_attendance = SubjectAttendance.query.filter_by(student_roll=student.roll).all()
            if student_attendance:
                avg_attendance = sum(att.attendance_percentage for att in student_attendance) / len(student_attendance)
                attendance_records.append(avg_attendance)

        avg_attendance = sum(attendance_records) / len(attendance_records) if attendance_records else 0

        # Count low attendance students (< 75%)
        low_attendance_count = len([att for att in attendance_records if att < 75])

        # Count at-risk students (simplified - low attendance + behavior issues)
        at_risk_count = low_attendance_count  # For now, just use low attendance count

        # Get recent assignments
        recent_assignments = []
        for subject_rel in teacher_subjects:
            assignments = Assignment.query.filter_by(
                subject=subject_rel.subject,
                class_name=subject_rel.class_name
            ).order_by(Assignment.assigned_date.desc()).limit(3).all()
            recent_assignments.extend([{
                'title': a.title,
                'due_date': a.due_date.isoformat() if a.due_date else None,
                'subject': a.subject,
                'class_name': a.class_name
            } for a in assignments])

        # Get recent behavior records
        recent_behavior = []
        for student in students_in_sections[:10]:  # Check recent 10 students
            behaviors = StudentBehavior.query.filter_by(student_roll=student.roll)\
                .order_by(StudentBehavior.date_recorded.desc()).limit(2).all()
            recent_behavior.extend([{
                'behavior_type': b.behavior_type,
                'date_recorded': b.date_recorded.isoformat(),
                'student_roll': b.student_roll
            } for b in behaviors])

        # Get recent marks
        recent_marks = []
        for subject_rel in teacher_subjects:
            marks = InternalMark.query.filter_by(subject=subject_rel.subject)\
                .order_by(InternalMark.date_assessed.desc()).limit(3).all()
            recent_marks.extend([{
                'subject': m.subject,
                'marks_obtained': m.marks,
                'total_marks': m.max_marks if hasattr(m, 'max_marks') else None,
                'date_assessed': m.date_assessed.isoformat() if m.date_assessed else None,
                'student_roll': m.student_roll
            } for m in marks])

        return jsonify({
            'stats': {
                'total_students': total_students,
                'avg_attendance': round(avg_attendance, 1),
                'low_attendance_count': low_attendance_count,
                'at_risk_count': at_risk_count
            },
            'recent_assignments': recent_assignments[:5],  # Limit to 5 most recent
            'recent_behavior': recent_behavior[:5],
            'recent_marks': recent_marks[:5]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/teachers/<username>/accessible-students", methods=["GET"])
@token_required
def get_accessible_students(current_user, username):
    try:
        # Verify the current user matches the requested username
        if current_user != username:
            return jsonify({'error': 'Unauthorized access'}), 403

        # Get teacher's sections
        teacher_sections = TeacherSection.query.filter_by(teacher_username=username).all()
        section_names = [ts.section for ts in teacher_sections]
        # Get students in those sections (limit to 40 per teacher)
        students = Student.query.filter(Student.section.in_(section_names)).limit(40).all()

        # Calculate attendance for each student
        student_data = []
        for student in students:
            # Get average attendance across all subjects
            attendance_records = SubjectAttendance.query.filter_by(student_roll=student.roll).all()
            avg_attendance = 0
            if attendance_records:
                avg_attendance = sum(att.attendance_percentage for att in attendance_records) / len(attendance_records)

            student_data.append({
                'roll': student.roll,
                'name': student.name,
                'section': student.section,
                'class': student.class_name,
                'attendance': round(avg_attendance, 1)
            })

        return jsonify(student_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/parent/<username>/dashboard", methods=["GET"])
@token_required
def get_parent_dashboard(current_user, username):
    try:
        # Verify the current user matches the requested username
        if current_user != username:
            return jsonify({'error': 'Unauthorized access'}), 403

        # Get parent info
        parent = Parent.query.filter_by(username=username).first()
        if not parent:
            return jsonify({'error': 'Parent not found'}), 404

        # Get student's data
        student = Student.query.filter_by(roll=parent.student_roll).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Get student's marks
        marks = {
            'math': student.math_marks or 0,
            'physics': student.physics_marks or 0,
            'chemistry': student.chemistry_marks or 0,
            'cs': student.cs_marks or 0,
            'english': student.english_marks or 0
        }
        avg_marks = sum(marks.values()) / len(marks) if marks else 0

        # Get detailed attendance data by subject
        attendance_records = SubjectAttendance.query.filter_by(student_roll=student.roll).all()
        attendance = 0
        subject_attendance = []
        if attendance_records:
            attendance = sum(att.attendance_percentage for att in attendance_records) / len(attendance_records)
            subject_attendance = [{
                'subject': att.subject,
                'total_classes': att.total_classes,
                'attended_classes': att.attended_classes,
                'percentage': att.attendance_percentage
            } for att in attendance_records]

        # Get internal marks by subject
        internal_marks = InternalMark.query.filter_by(student_roll=student.roll)\
            .order_by(InternalMark.date_assessed.desc()).all()
        internal_marks_data = [{
            'subject': mark.subject,
            'marks_obtained': mark.marks,
            'max_marks': mark.max_marks,
            'percentage': (mark.marks / mark.max_marks * 100) if mark.max_marks else 0,
            'date_assessed': mark.date_assessed.isoformat() if mark.date_assessed else None,
            'teacher': mark.teacher_username
        } for mark in internal_marks]

        # Get assignments for the student
        assignments = AssignmentSubmission.query.filter_by(student_roll=student.roll)\
            .join(Assignment, AssignmentSubmission.assignment_id == Assignment.id)\
            .add_columns(Assignment.title, Assignment.subject, Assignment.due_date, Assignment.description)\
            .all()

        assignment_data = []
        for sub, title, subject, due_date, description in assignments:
            assignment_data.append({
                'title': title,
                'subject': subject,
                'due_date': due_date.isoformat() if due_date else None,
                'status': sub.status,
                'score': sub.score,
                'description': description,
                'submitted_date': sub.submitted_date.isoformat() if sub.submitted_date else None
            })

        # Get behavior records
        behavior_records = StudentBehavior.query.filter_by(student_roll=student.roll)\
            .order_by(StudentBehavior.date_recorded.desc()).all()

        behavior_data = [{
            'date': b.date_recorded.isoformat(),
            'type': b.behavior_type,
            'description': b.description,
            'points': b.points,
            'teacher': b.recorded_by
        } for b in behavior_records]

        # Behavior summary
        total_points = sum(b.points for b in behavior_records)
        recent_records = len([b for b in behavior_records if (datetime.datetime.now() - b.date_recorded).days <= 30])
        positive_records = len([b for b in behavior_records if b.points > 0])

        behavior_summary = {
            'total_points': total_points,
            'recent_records': recent_records,
            'positive_records': positive_records,
            'behavior_trend': 'positive' if total_points > 0 else 'needs_attention' if total_points < -10 else 'neutral'
        }

        # Get notifications for the parent
        parent_notifications = Notification.query.filter_by(parent_username=username)\
            .order_by(Notification.created_at.desc()).limit(10).all()

        notifications_data = [{
            'id': n.id,
            'title': n.title,
            'content': n.content,
            'type': n.type,
            'priority': n.priority,
            'icon': n.icon,
            'created_at': n.created_at.isoformat() if n.created_at else None,
            'read': n.read
        } for n in parent_notifications]

        # Get teacher's contact information for the student's section
        teacher_contacts = []
        teacher_sections = TeacherSection.query.filter_by(section=student.section).all()
        for ts in teacher_sections:
            teacher = Teacher.query.filter_by(username=ts.teacher_username).first()
            if teacher:
                teacher_contacts.append({
                    'name': teacher.name,
                    'username': teacher.username,
                    'department': teacher.department,
                    'email': teacher.email
                })

        # Performance insights
        performance_insights = {
            'attendance_status': 'excellent' if attendance >= 90 else 'good' if attendance >= 75 else 'needs_improvement',
            'academic_performance': 'excellent' if avg_marks >= 90 else 'good' if avg_marks >= 75 else 'needs_improvement',
            'behavior_status': behavior_summary['behavior_trend'],
            'overall_risk': 'low' if attendance >= 75 and avg_marks >= 60 and total_points >= -5 else 'medium' if attendance >= 60 and avg_marks >= 50 else 'high'
        }

        # Recent activities (assignments, behavior, marks)
        recent_activities = []

        # Recent assignments
        recent_assignments = assignment_data[:3]
        for assignment in recent_assignments:
            recent_activities.append({
                'type': 'assignment',
                'title': f"Assignment: {assignment['title']}",
                'subject': assignment['subject'],
                'date': assignment['submitted_date'] or assignment['due_date'],
                'status': assignment['status']
            })

        # Recent behavior
        recent_behavior = behavior_data[:3]
        for behavior in recent_behavior:
            recent_activities.append({
                'type': 'behavior',
                'title': f"Behavior: {behavior['type']}",
                'description': behavior['description'],
                'date': behavior['date'],
                'points': behavior['points']
            })

        # Recent marks
        recent_marks = internal_marks_data[:3]
        for mark in recent_marks:
            recent_activities.append({
                'type': 'marks',
                'title': f"Marks: {mark['subject']} - {mark['marks_obtained']}/{mark['max_marks']}",
                'subject': mark['subject'],
                'date': mark['date_assessed'],
                'percentage': mark['percentage']
            })

        # Sort activities by date
        recent_activities.sort(key=lambda x: x['date'] or '', reverse=True)

        return jsonify({
            'student': {
                'roll': student.roll,
                'name': student.name,
                'class': student.class_name,
                'section': student.section,
                'attendance': round(attendance, 1),
                'avg_marks': round(avg_marks, 1),
                'marks': marks
            },
            'subject_attendance': subject_attendance,
            'internal_marks': internal_marks_data,
            'assignments': assignment_data,
            'behavior_records': behavior_data,
            'behavior_summary': behavior_summary,
            'notifications': notifications_data,
            'teacher_contacts': teacher_contacts,
            'performance_insights': performance_insights,
            'recent_activities': recent_activities[:10]  # Limit to 10 most recent
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/notifications", methods=["GET"])
@token_required
def get_notifications(current_user):
    try:
        # Determine user type and get appropriate notifications
        user_type = request.args.get('user_type', 'student')
        student_roll = request.args.get('student_roll')

        query = Notification.query

        if user_type == 'student' and student_roll:
            query = query.filter(
                (Notification.student_roll == student_roll) |
                (Notification.student_roll.is_(None))  # General notifications
            )
        elif user_type == 'teacher':
            query = query.filter(
                (Notification.teacher_username == current_user) |
                (Notification.teacher_username.is_(None))
            )
        elif user_type == 'parent':
            query = query.filter(
                (Notification.parent_username == current_user) |
                (Notification.parent_username.is_(None))
            )

        notifications = query.order_by(Notification.created_at.desc()).all()

        # Convert to dict and add time ago
        result = []
        for n in notifications:
            n_dict = n.to_dict()
            # Add time ago calculation
            if n.created_at:
                now = datetime.datetime.utcnow()
                diff = now - n.created_at
                if diff.days > 0:
                    n_dict['time'] = f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
                elif diff.seconds >= 3600:
                    hours = diff.seconds // 3600
                    n_dict['time'] = f"{hours} hour{'s' if hours > 1 else ''} ago"
                elif diff.seconds >= 60:
                    minutes = diff.seconds // 60
                    n_dict['time'] = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                else:
                    n_dict['time'] = "Just now"
            else:
                n_dict['time'] = "Unknown"

            result.append(n_dict)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/notifications/<int:notification_id>/read", methods=["PATCH"])
@token_required
def mark_notification_read(current_user, notification_id):
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404

        # Check if user has permission to mark this notification
        user_type = request.args.get('user_type', 'student')
        student_roll = request.args.get('student_roll')

        can_access = False
        if user_type == 'student' and notification.student_roll == student_roll:
            can_access = True
        elif user_type == 'teacher' and notification.teacher_username == current_user:
            can_access = True
        elif user_type == 'parent' and notification.parent_username == current_user:
            can_access = True
        elif notification.student_roll is None and notification.teacher_username is None and notification.parent_username is None:
            can_access = True  # General notification

        if not can_access:
            return jsonify({'error': 'Unauthorized access to notification'}), 403

        notification.read = True
        db.session.commit()

        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route("/api/notifications", methods=["POST"])
@token_required
def create_notification(current_user):
    try:
        data = request.get_json() or {}

        # Only teachers can create notifications for now
        teacher = Teacher.query.filter_by(username=current_user).first()
        if not teacher:
            return jsonify({'error': 'Only teachers can create notifications'}), 403

        notification = Notification(
            student_roll=data.get('student_roll'),
            teacher_username=data.get('teacher_username', current_user),
            parent_username=data.get('parent_username'),
            title=data.get('title', ''),
            content=data.get('content', ''),
            type=data.get('type', 'general'),
            priority=data.get('priority', 'medium'),
            icon=data.get('icon', '📢')
        )

        db.session.add(notification)
        db.session.commit()

        return jsonify({'status': 'success', 'notification': notification.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route("/api/parent/<username>/insights", methods=["GET"])
@token_required
def get_parent_insights(current_user, username):
    try:
        # Verify the current user matches the requested username
        if current_user != username:
            return jsonify({'error': 'Unauthorized access'}), 403

        # Get parent info
        parent = Parent.query.filter_by(username=username).first()
        if not parent:
            return jsonify({'error': 'Parent not found'}), 404

        # Get student's data
        student = Student.query.filter_by(roll=parent.student_roll).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Academic performance trends
        internal_marks = InternalMark.query.filter_by(student_roll=student.roll)\
            .order_by(InternalMark.date_assessed).all()

        subject_performance = {}
        for mark in internal_marks:
            if mark.subject not in subject_performance:
                subject_performance[mark.subject] = []
            subject_performance[mark.subject].append({
                'marks': mark.marks,
                'max_marks': mark.max_marks,
                'percentage': (mark.marks / mark.max_marks * 100) if mark.max_marks else 0,
                'date': mark.date_assessed.isoformat() if mark.date_assessed else None
            })

        # Attendance trends
        attendance_records = SubjectAttendance.query.filter_by(student_roll=student.roll)\
            .order_by(SubjectAttendance.subject).all()

        attendance_trends = {}
        for att in attendance_records:
            attendance_trends[att.subject] = {
                'total_classes': att.total_classes,
                'attended_classes': att.attended_classes,
                'percentage': att.attendance_percentage
            }

        # Behavior analysis
        behavior_records = StudentBehavior.query.filter_by(student_roll=student.roll)\
            .order_by(StudentBehavior.date_recorded).all()

        behavior_trends = []
        for behavior in behavior_records:
            behavior_trends.append({
                'date': behavior.date_recorded.isoformat(),
                'type': behavior.behavior_type,
                'points': behavior.points,
                'description': behavior.description
            })

        # Assignment completion rate
        assignments = AssignmentSubmission.query.filter_by(student_roll=student.roll).all()
        total_assignments = len(assignments)
        completed_assignments = len([a for a in assignments if a.status == 'submitted'])
        completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0

        # Performance predictions using ML model
        prediction_data = None
        try:
            import requests
            prediction_payload = {
                'math_marks': student.math_marks or 0,
                'physics_marks': student.physics_marks or 0,
                'chemistry_marks': student.chemistry_marks or 0,
                'cs_marks': student.cs_marks or 0,
                'english_marks': student.english_marks or 0,
                'attendance': student.attendance or 0,
                'avg_marks': student.avg_marks or 0
            }
            # Assuming ML endpoint is running locally
            response = requests.post('http://localhost:5000/api/ml/predict', json=prediction_payload, timeout=5)
            if response.status_code == 200:
                prediction_data = response.json()
        except:
            pass

        # Recommendations based on data
        recommendations = []

        avg_marks = student.avg_marks or 0
        attendance = student.attendance or 0

        if attendance < 75:
            recommendations.append({
                'type': 'attendance',
                'priority': 'high',
                'message': 'Improve attendance - currently below 75%',
                'action': 'Contact teachers to understand attendance issues'
            })

        if avg_marks < 60:
            recommendations.append({
                'type': 'academic',
                'priority': 'high',
                'message': 'Academic performance needs improvement',
                'action': 'Consider additional tutoring or study support'
            })

        # Subject-specific recommendations
        for subject, marks in subject_performance.items():
            if marks:
                avg_subject_marks = sum(m['percentage'] for m in marks) / len(marks)
                if avg_subject_marks < 50:
                    recommendations.append({
                        'type': 'subject',
                        'priority': 'medium',
                        'message': f'Focus needed on {subject} - average {avg_subject_marks:.1f}%',
                        'action': f'Seek additional help in {subject}'
                    })

        return jsonify({
            'student_info': {
                'roll': student.roll,
                'name': student.name,
                'class': student.class_name,
                'section': student.section
            },
            'academic_performance': {
                'overall_avg': student.avg_marks,
                'subject_wise': subject_performance
            },
            'attendance_analysis': attendance_trends,
            'behavior_trends': behavior_trends,
            'assignment_completion': {
                'total': total_assignments,
                'completed': completed_assignments,
                'completion_rate': round(completion_rate, 1)
            },
            'performance_prediction': prediction_data,
            'recommendations': recommendations
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/parent/<username>/communication", methods=["GET", "POST"])
@token_required
def parent_communication(current_user, username):
    try:
        # Verify the current user matches the requested username
        if current_user != username:
            return jsonify({'error': 'Unauthorized access'}), 403

        parent = Parent.query.filter_by(username=username).first()
        if not parent:
            return jsonify({'error': 'Parent not found'}), 404

        if request.method == 'GET':
            # Get communication history (notifications sent to/received from teachers)
            sent_notifications = Notification.query.filter_by(parent_username=username)\
                .order_by(Notification.created_at.desc()).all()

            # Get teacher responses (notifications from teachers about this parent's student)
            teacher_notifications = Notification.query.filter_by(student_roll=parent.student_roll)\
                .filter(Notification.teacher_username.isnot(None))\
                .order_by(Notification.created_at.desc()).all()

            communications = []

            for notif in sent_notifications:
                communications.append({
                    'id': notif.id,
                    'type': 'sent',
                    'title': notif.title,
                    'content': notif.content,
                    'recipient': 'Teacher',
                    'date': notif.created_at.isoformat() if notif.created_at else None,
                    'read': notif.read
                })

            for notif in teacher_notifications:
                communications.append({
                    'id': notif.id,
                    'type': 'received',
                    'title': notif.title,
                    'content': notif.content,
                    'sender': notif.teacher_username,
                    'date': notif.created_at.isoformat() if notif.created_at else None,
                    'read': notif.read
                })

            # Sort by date
            communications.sort(key=lambda x: x['date'] or '', reverse=True)

            return jsonify({
                'communications': communications[:20],  # Limit to 20 most recent
                'unread_count': len([c for c in communications if not c['read']])
            })

        elif request.method == 'POST':
            # Send message to teacher
            data = request.get_json() or {}
            teacher_username = data.get('teacher_username')
            title = data.get('title', '')
            content = data.get('content', '')

            if not teacher_username or not content:
                return jsonify({'error': 'Teacher username and message content required'}), 400

            # Verify teacher exists
            teacher = Teacher.query.filter_by(username=teacher_username).first()
            if not teacher:
                return jsonify({'error': 'Teacher not found'}), 404

            # Create notification
            notification = Notification(
                student_roll=parent.student_roll,
                teacher_username=teacher_username,
                parent_username=username,
                title=title,
                content=content,
                type='parent_message',
                priority='medium',
                icon='👨‍👩‍👧‍👦'
            )

            db.session.add(notification)
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': 'Message sent successfully',
                'notification_id': notification.id
            })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route("/api/parent/<username>/progress-report", methods=["GET"])
@token_required
def get_parent_progress_report(current_user, username):
    try:
        # Verify the current user matches the requested username
        if current_user != username:
            return jsonify({'error': 'Unauthorized access'}), 403

        parent = Parent.query.filter_by(username=username).first()
        if not parent:
            return jsonify({'error': 'Parent not found'}), 404

        student = Student.query.filter_by(roll=parent.student_roll).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Generate comprehensive progress report
        report = {
            'student_info': {
                'roll': student.roll,
                'name': student.name,
                'class': student.class_name,
                'section': student.section
            },
            'generated_at': datetime.datetime.utcnow().isoformat(),
            'period': 'Current Academic Year'
        }

        # Academic Performance
        marks = {
            'math': student.math_marks or 0,
            'physics': student.physics_marks or 0,
            'chemistry': student.chemistry_marks or 0,
            'cs': student.cs_marks or 0,
            'english': student.english_marks or 0
        }
        avg_marks = sum(marks.values()) / len(marks)

        report['academic_performance'] = {
            'subject_marks': marks,
            'overall_average': round(avg_marks, 1),
            'grade': 'A' if avg_marks >= 90 else 'B' if avg_marks >= 80 else 'C' if avg_marks >= 70 else 'D' if avg_marks >= 60 else 'F'
        }

        # Attendance Summary
        attendance_records = SubjectAttendance.query.filter_by(student_roll=student.roll).all()
        total_classes = sum(att.total_classes for att in attendance_records)
        total_attended = sum(att.attended_classes for att in attendance_records)
        attendance_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0

        report['attendance_summary'] = {
            'total_classes': total_classes,
            'classes_attended': total_attended,
            'attendance_percentage': round(attendance_percentage, 1),
            'status': 'Excellent' if attendance_percentage >= 90 else 'Good' if attendance_percentage >= 75 else 'Needs Improvement'
        }

        # Behavior Summary
        behavior_records = StudentBehavior.query.filter_by(student_roll=student.roll).all()
        total_points = sum(b.points for b in behavior_records)
        positive_incidents = len([b for b in behavior_records if b.points > 0])
        negative_incidents = len([b for b in behavior_records if b.points < 0])

        report['behavior_summary'] = {
            'total_points': total_points,
            'positive_incidents': positive_incidents,
            'negative_incidents': negative_incidents,
            'behavior_rating': 'Excellent' if total_points > 10 else 'Good' if total_points > 0 else 'Needs Attention' if total_points > -10 else 'Concerning'
        }

        # Assignment Performance
        assignments = AssignmentSubmission.query.filter_by(student_roll=student.roll).all()
        submitted_count = len([a for a in assignments if a.status == 'submitted'])
        total_assignments = len(assignments)
        submission_rate = (submitted_count / total_assignments * 100) if total_assignments > 0 else 0

        report['assignment_performance'] = {
            'total_assignments': total_assignments,
            'submitted_assignments': submitted_count,
            'submission_rate': round(submission_rate, 1),
            'status': 'Excellent' if submission_rate >= 90 else 'Good' if submission_rate >= 75 else 'Needs Improvement'
        }

        # Teacher Comments (recent internal marks with comments)
        recent_marks = InternalMark.query.filter_by(student_roll=student.roll)\
            .order_by(InternalMark.date_assessed.desc()).limit(5).all()

        teacher_comments = []
        for mark in recent_marks:
            if hasattr(mark, 'comments') and mark.comments:
                teacher_comments.append({
                    'subject': mark.subject,
                    'teacher': mark.teacher_username,
                    'marks': f"{mark.marks}/{mark.max_marks}",
                    'comments': mark.comments,
                    'date': mark.date_assessed.isoformat() if mark.date_assessed else None
                })

        report['teacher_comments'] = teacher_comments

        # Overall Assessment
        overall_score = 0
        overall_score += 40 if avg_marks >= 75 else 20 if avg_marks >= 60 else 0  # Academic (40%)
        overall_score += 30 if attendance_percentage >= 75 else 15 if attendance_percentage >= 60 else 0  # Attendance (30%)
        overall_score += 20 if total_points >= 0 else 10 if total_points >= -5 else 0  # Behavior (20%)
        overall_score += 10 if submission_rate >= 75 else 5 if submission_rate >= 50 else 0  # Assignments (10%)

        report['overall_assessment'] = {
            'score': overall_score,
            'grade': 'A' if overall_score >= 80 else 'B' if overall_score >= 65 else 'C' if overall_score >= 50 else 'D' if overall_score >= 35 else 'F',
            'status': 'Outstanding' if overall_score >= 80 else 'Good' if overall_score >= 65 else 'Satisfactory' if overall_score >= 50 else 'Needs Improvement'
        }

        return jsonify(report)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Static file serving for frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.root_path, '..', 'frontend', path)):
        return send_from_directory(os.path.join(app.root_path, '..', 'frontend'), path)
    else:
        return send_from_directory(os.path.join(app.root_path, '..', 'frontend'), 'login.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
