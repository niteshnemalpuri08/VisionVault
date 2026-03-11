from server import app, db
from models import User, StudentPerformance
import random

def seed_database():
    with app.app_context():
        # Optional: Clear old data to avoid duplicates
        db.drop_all()
        db.create_all()
        
        print("🌱 Seeding Database...")

        # 1. Create STUDENT (24cse001)
        student = User(
            username='24cse001',
            password='password123',
            role='student',
            name='Rahul Sharma',
            section='A',
            parent_email='parent@example.com',
            parent_phone='+1234567890'
        )
        
        # 2. Create TEACHER (t01)
        teacher = User(
            username='t01',
            password='password123',
            role='teacher',
            name='Mr. Amit',
            section='A'
        )

        # 3. Create PARENT (p_24cse001)
        parent = User(
            username='p_24cse001',
            password='password123',
            role='parent',
            name='Mr. Sharma',
            child_roll='24cse001' # Links to student
        )

        # 4. Add Performance Data for Student
        perf = StudentPerformance(
            student=student,
            math_marks=95, physics_marks=88, chemistry_marks=92,
            cs_marks=98, english_marks=85, pe_marks=96,
            total_classes=100, present_classes=85, attendance=85.0,
            avg_marks=92.3
        )

        db.session.add(student)
        db.session.add(teacher)
        db.session.add(parent)
        db.session.add(perf)
        
        db.session.commit()
        print("✅ Database Populated Successfully!")
        print("---------------------------------------")
        print("Student Login: 24cse001   / password123")
        print("Teacher Login: t01        / password123")
        print("Parent Login:  p_24cse001 / password123")
        print("---------------------------------------")

if __name__ == '__main__':
    seed_database()