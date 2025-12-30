from flask import Flask
import os
from models import db, Student, Parent

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'erp.db'))}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    students = Student.query.all()
    created = 0
    for s in students:
        parent_username = f"{s.username}_parent"
        if not Parent.query.filter_by(username=parent_username).first():
            p = Parent(
                username=parent_username,
                name=f"Parent of {s.name}",
                email=s.email,
                student_roll=s.roll
            )
            # default password = student username
            p.set_password(s.username)
            db.session.add(p)
            created += 1
    if created:
        db.session.commit()
    print(f"Created {created} parent accounts")
