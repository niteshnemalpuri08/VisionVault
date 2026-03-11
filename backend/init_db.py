from server import app, db
from models import User, StudentPerformance
import random

def init_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("🔄 Generating Data: Teachers, Students, and Parents...")

        # 1. TEACHERS
        teachers = [
            ('t01', 'A', 'Mr. Amit'), ('t02', 'B', 'Ms. Priya'),
            ('t03', 'C', 'Mr. John'), ('t04', 'D', 'Ms. Sara'), ('t05', 'E', 'Mr. David')
        ]
        for u, s, n in teachers:
            db.session.add(User(username=u, password='password123', role='teacher', name=n, section=s))

        # 2. STUDENTS & PARENTS
        for i in range(1, 201):
            roll = f"24cse{str(i).zfill(3)}"
            
            # Section Logic
            if i <= 40: sec = 'A'
            elif i <= 80: sec = 'B'
            elif i <= 120: sec = 'C'
            elif i <= 160: sec = 'D'
            else: sec = 'E'

            # 24cse001 Special Data
            if i == 1:
                p_email = "niteshnemalpuri17@gmail.com"
                s_name = "Rahul Sharma"
                m, p, c, cs, e, pe = 95, 88, 92, 98, 85, 96
                pres = 58
            else:
                p_email = f"parent{roll}@gmail.com"
                s_name = f"Student {i}"
                m = random.randint(60, 95)
                p = random.randint(60, 95)
                c = random.randint(60, 95)
                cs = random.randint(70, 99)
                e = random.randint(70, 95)
                pe = random.randint(80, 99)
                pres = random.randint(30, 55)

            # Create STUDENT
            student = User(
                username=roll, password='password123', role='student',
                name=s_name, class_name='B.Tech', section=sec,
                parent_email=p_email, parent_phone='9876543210'
            )
            db.session.add(student)

            # Create PARENT (Linked to Student)
            parent = User(
                username=f"p_{roll}", # Login: p_24cse001
                password='password123',
                role='parent',
                name=f"Parent of {s_name}",
                child_roll=roll # <--- LINK IS HERE
            )
            db.session.add(parent)

            # Performance Data
            avg = round((m+p+c+cs+e+pe)/6, 2)
            att_pct = round((pres/60)*100, 1)

            perf = StudentPerformance(
                student=student,
                math_marks=m, physics_marks=p, chemistry_marks=c,
                cs_marks=cs, english_marks=e, pe_marks=pe,
                total_classes=60, present_classes=pres, attendance=att_pct,
                avg_marks=avg
            )
            db.session.add(perf)

        db.session.commit()
        print("✅ Database Created.")
        print("   - Parent Login: p_24cse001 / password123")

if __name__ == '__main__':
    init_database()