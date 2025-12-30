from backend.models import db, Teacher
from flask import Flask
import os
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'erp.db'))}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    t = Teacher.query.first()
    if t:
        print('Teacher', t.username)
        print('password repr:', repr(getattr(t, 'password', None)))
        print('password_hash repr:', repr(getattr(t, 'password_hash', None)))
    else:
        print('No teacher found')
