from backend.models import db, Student, Teacher, Parent
from flask import Flask
import os
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'erp.db'))}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    print('students', Student.query.count())
    print('teachers', Teacher.query.count())
    print('parents', Parent.query.count())
