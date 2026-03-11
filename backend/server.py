from flask import Flask, request, jsonify, send_from_directory, send_file, make_response
from flask_cors import CORS
from models import db, User, Attendance, StudentPerformance, Message
from notifier import send_absent_email, send_absent_sms, send_payment_receipt
from datetime import date, datetime
import io
import stripe
import base64
import numpy as np
import cv2
import os
import pytesseract
from PIL import Image
import re
from werkzeug.utils import secure_filename

# --- 1. OCR / IMAGE PROCESSING IMPORTS ---
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ Pillow or Tesseract not installed. Advanced verification disabled.")

from predictor import predict_score 
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# 🔥 RECTIFIED CORS: Critical for mobile-laptop cross-communication
CORS(app, resources={r"/*": {"origins": "*"}}) 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'super_secret'
UPLOAD_FOLDER = 'uploads/payments'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Replace with your actual Stripe Secret Key
stripe.api_key = "sk_test_YOUR_STRIPE_SECRET_KEY" 

db.init_app(app)

# =================================================================
# 🧠 ENHANCED AI SETUP (OpenCV LBPH Face Recognition)
# =================================================================
face_recognizer = None
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
AI_READY = False

# ✅ ENHANCEMENT: Standard resolution for face comparison
FACE_SIZE = (200, 200)

def process_face(img_gray):
    """
    Standardizes lighting using Histogram Equalization and resizes the image.
    This significantly improves accuracy in different room lighting.
    """
    # 1. Histogram Equalization (Fixes shadows and bright spots)
    equalized = cv2.equalizeHist(img_gray)
    # 2. Resizing (Ensures consistent data points)
    resized = cv2.resize(equalized, FACE_SIZE)
    return resized

def train_ai():
    global AI_READY, face_recognizer
    
    if not hasattr(cv2, 'face'):
        print("❌ AI ERROR: 'cv2.face' missing. Ensure 'opencv-contrib-python' is installed.")
        return
    
    face_recognizer = cv2.face.LBPHFaceRecognizer_create()
    face_samples = []
    ids = []
    
    face_dir = os.path.join(os.getcwd(), "faces", "24cse001")
    
    if os.path.exists(face_dir):
        print(f"📸 Found training folder for 24cse001, processing images...")
        for filename in os.listdir(face_dir):
            if filename.lower().endswith((".jpg", ".png", ".jpeg")):
                img_path = os.path.join(face_dir, filename)
                img = cv2.imread(img_path)
                if img is None: continue
                
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                for (x, y, w, h) in faces:
                    # ✅ ENHANCEMENT: Pre-process training image
                    face_roi = process_face(gray[y:y+h, x:x+w])
                    face_samples.append(face_roi)
                    ids.append(1) 
        
        if len(face_samples) > 0:
            face_recognizer.train(face_samples, np.array(ids))
            AI_READY = True
            print(f"✅ AI Trained successfully with {len(face_samples)} samples for 24cse001")
        else:
            print("⚠️ AI ERROR: No faces detected in the provided training images.")
    else:
        target_img = "24cse001.jpg"
        if os.path.exists(target_img):
            print(f"📸 Folder missing, falling back to single image: {target_img}")
            try:
                ref_img = cv2.imread(target_img)
                gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(faces) > 0:
                    (x, y, w, h) = faces[0]
                    # ✅ ENHANCEMENT: Standardize fallback image
                    face_roi = process_face(gray[y:y+h, x:x+w])
                    face_recognizer.train([face_roi], np.array([1]))
                    AI_READY = True
                    print(f"✅ AI Trained (Single Image) for 24cse001")
            except Exception as e: print(f"❌ AI Error: {e}")
        else:
            print("⚠️ CRITICAL: Training data NOT FOUND")

with app.app_context():
    train_ai()

# =================================================================
# 🛡️ AUTH & FACE LOGIN ROUTES
# =================================================================

@app.route('/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS': return jsonify({'success': True}), 200
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and user.password == data['password']:
        return jsonify({
            'success': True, 
            'role': user.role, 
            'username': user.username, 
            'name': user.name, 
            'section': user.section
        })
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/auth/face_login', methods=['POST'])
def face_login():
    if not AI_READY:
        return jsonify({'success': False, 'message': 'AI System Not Ready'})
    try:
        data = request.json
        image_data = data['image'].split(',')[1]
        img_bytes = base64.decodebytes(image_data.encode())
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        gray_camera = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_camera, 1.1, 4)

        if len(faces) == 0:
            return jsonify({'success': False, 'message': 'No face detected'})

        for (x, y, w, h) in faces:
            # ✅ ENHANCEMENT: Standardize live face for matching
            roi_gray = process_face(gray_camera[y:y+h, x:x+w])
            label, confidence = face_recognizer.predict(roi_gray)
            
            # Stricter threshold since preprocessing makes scores more stable
            if confidence < 70: 
                user = User.query.filter_by(username="24cse001").first()
                if user:
                    print(f"✅ Match Found: {user.name} (Conf: {round(confidence, 2)})")
                    return jsonify({
                        'success': True, 
                        'role': user.role,
                        'username': user.username, 
                        'name': user.name, 
                        'section': user.section
                    })
            else:
                print(f"❌ Stranger Detected: Confidence {round(confidence, 2)} too high.")
                    
        return jsonify({'success': False, 'message': 'Face Not Recognized'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# [Remaining Teacher, Payment, Parent, and System routes stay unchanged]
# =================================================================
# 🏫 TEACHER & ATTENDANCE ROUTES
# =================================================================
import re
@app.route('/api/teacher/students', methods=['POST'])
def get_teacher_students():
    data = request.json
    username = data.get('username')
    teacher = User.query.filter_by(username=username).first()
    
    if not teacher or teacher.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Extract teacher number (e.g., 't01' -> 1) to calculate range
        teacher_num = int(re.search(r'\d+', username).group())
        start_roll = ((teacher_num - 1) * 40) + 1
        end_roll = teacher_num * 40
    except (AttributeError, ValueError):
        start_roll, end_roll = 1, 40

    students = User.query.filter_by(role='student', section=teacher.section).all()
    student_lookup = {s.username: s for s in students}
    
    result = []
    for i in range(start_roll, end_roll + 1):
        formatted_roll = f"24cse{str(i).zfill(3)}"
        
        if formatted_roll in student_lookup:
            s = student_lookup[formatted_roll]
            p = s.performance
            result.append({
                'roll': s.username,
                'name': s.name,
                'attendance': p.attendance if p else 0,
                'avg_marks': p.avg_marks if p else 0,
                # ... [Keep your existing subject marks here]
            })
        else:
            # ✅ FIX: Instead of "Not Registered", use the Roll Number as the Name
            result.append({
                'roll': formatted_roll,
                'name': formatted_roll.upper(), # Shows "24CSE002" as the name
                'attendance': 0, 
                'avg_marks': 0,
                'math_marks': 0, 'physics_marks': 0, 'chemistry_marks': 0,
                'cs_marks': 0, 'english_marks': 0, 'pe_marks': 0
            })

    return jsonify({
        'teacher_id': username,
        'assigned_range': f"{start_roll} to {end_roll}",
        'students': result
    })
# =================================================================
# 👨‍👩‍👦 PARENT, CHAT & SYSTEM ROUTES
# =================================================================

@app.route('/api/parent/child', methods=['POST'])
def get_child_data():
    try:
        data = request.json
        parent = User.query.filter_by(username=data.get('username')).first()
        if not parent or not parent.child_roll: return jsonify({'error': 'No link'}), 404
        child = User.query.filter_by(username=parent.child_roll).first()
        p = child.performance
        return jsonify({
            'child_name': child.name, 'roll': child.username, 'section': child.section, 
            'attendance': p.attendance, 'avg': p.avg_marks,
            'math': p.math_marks, 'phy': p.physics_marks, 'chem': p.chemistry_marks, 
            'cs': p.cs_marks, 'eng': p.english_marks, 'pe': p.pe_marks
        })
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/chat/send', methods=['POST'])
def send_msg():
    try:
        data = request.json
        new_msg = Message(sender=data['sender'], receiver=data['receiver'], content=data['content'])
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({'success': True})
    except: return jsonify({'success': False}), 500

@app.route('/api/chat/history', methods=['POST'])
def get_chat_history():
    data = request.json
    u1, u2 = data.get('user1'), data.get('user2')
    msgs = Message.query.filter(((Message.sender == u1) & (Message.receiver == u2)) | ((Message.sender == u2) & (Message.receiver == u1))).order_by(Message.timestamp.asc()).all()
    return jsonify([{'sender': m.sender, 'content': m.content} for m in msgs])

@app.route('/service-worker.js')
def serve_sw():
    response = make_response(send_from_directory(app.static_folder, 'service-worker.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response

@app.route('/api/students/<username>', methods=['GET'])
def get_student_data(username):
    user = User.query.filter_by(username=username).first()
    if not user: return jsonify({'error': 'User not found'}), 404
    if not user.performance:
        return jsonify({'name': user.name, 'roll': user.username, 'section': user.section, 'avg_marks': 0, 'rank': "--", 'total_students': 0})
    section_students = User.query.filter_by(role='student', section=user.section).all()
    leaderboard = [s for s in section_students if s.performance is not None]
    leaderboard.sort(key=lambda x: x.performance.avg_marks, reverse=True)
    my_rank = next((i + 1 for i, s in enumerate(leaderboard) if s.username == username), 0)
    sums = {'math':0,'phy':0,'chem':0,'cs':0,'eng':0,'pe':0}
    count = len(leaderboard)
    for s in leaderboard:
        p = s.performance
        sums['math'] += p.math_marks; sums['phy'] += p.physics_marks; sums['chem'] += p.chemistry_marks
        sums['cs'] += p.cs_marks; sums['eng'] += p.english_marks; sums['pe'] += p.pe_marks
    avgs = {k: round(v/count, 1) if count > 0 else 0 for k,v in sums.items()}
    return jsonify({
        'name': user.name, 'roll': user.username, 'section': user.section,
        'math_marks': user.performance.math_marks, 'physics_marks': user.performance.physics_marks,
        'chemistry_marks': user.performance.chemistry_marks, 'cs_marks': user.performance.cs_marks,
        'english_marks': user.performance.english_marks, 'pe_marks': user.performance.pe_marks,
        'attendance': user.performance.attendance, 'avg_marks': user.performance.avg_marks,
        'rank': my_rank if my_rank > 0 else "--", 'total_students': count, 'class_averages': avgs
    })

@app.route('/api/predict/<username>', methods=['GET'])
def get_prediction(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user: return jsonify({'error': 'Student not found'}), 404
        if not user.performance:
            return jsonify({'current_avg': 0, 'current_attendance': 0, 'predicted_final_score': "No data"})
        p = user.performance
        pred = predict_score(p.math_marks, p.physics_marks, p.chemistry_marks, p.cs_marks, p.english_marks, p.pe_marks, p.attendance)
        return jsonify({
            'current_avg': p.avg_marks if p.avg_marks else 0,
            'current_attendance': p.attendance if p.attendance else 0,
            'predicted_final_score': round(pred, 2) if isinstance(pred, (int, float)) else pred
        })
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/repair_data')
def repair_data():
    db.create_all()
    if not User.query.filter_by(username='t01').first():
        db.session.add(User(username='t01', password='password', role='teacher', name='Prof. Sharma', section='A'))
    db.session.commit()
    return "✅ Data Repaired"

@app.route('/')
def serve_index(): return send_from_directory(app.static_folder, 'login.html')

@app.route('/<path:path>')
def serve_static(path): return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')