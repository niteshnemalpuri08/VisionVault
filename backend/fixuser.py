# Save this as fix_sections.py in the backend folder and run it
from server import app, db, User

with app.app_context():
    # Force teacher t01 and student 24cse001 into "Section A"
    t = User.query.filter_by(username='t01').first()
    s = User.query.filter_by(username='24cse001').first()
    
    if t and s:
        t.section = "Section A"
        s.section = "Section A"
        db.session.commit()
        print("✅ Teacher and Student are now both in 'Section A'")