from server import app
from models import db, User

with app.app_context():
    users = User.query.all()
    print("\n--- 🔍 CURRENT USERS IN DB ---")
    if not users:
        print("❌ The Database is EMPTY. Run seed_db.py again.")
    for u in users:
        print(f"✅ User: {u.username} | Role: {u.role} | Password: {u.password}")
    print("------------------------------\n")