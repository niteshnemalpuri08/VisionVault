from flask import Flask
import os
from backend.models import db, Teacher

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'erp.db'))}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    teachers = Teacher.query.all()
    updated = 0
    for t in teachers:
        # If there is no password_hash, set one. Prefer existing plaintext password, otherwise fall back to username
        if not getattr(t, 'password_hash', None):
            plaintext = getattr(t, 'password', None) or t.username
            t.set_password(plaintext)
            db.session.add(t)
            updated += 1
    if updated:
        db.session.commit()
    print(f"Updated {updated} teacher password hashes")
