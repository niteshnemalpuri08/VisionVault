import os, datetime
items = ['.venv','venv','backend/update_student_names.py','backend/assign_teachers.py','backend/assign_teacher_sections.py','backend/check_parent_credentials.py','backend/update_parent_credentials.py','backend/enhanced_model.pkl','frontend/gietlogo.jpg','test_predict_api.py']
for i in items:
    path = os.path.join(os.getcwd(), '..', '..', i) if i.startswith('.')==False and not i.startswith('backend') and not i.startswith('frontend') and i!='test_predict_api.py' else os.path.join(os.getcwd(), '..', '..', i) if i in ('.venv','venv') else os.path.join(os.getcwd(), '..', '..', i)
    # Simplify: treat path as relative to repo root
    path = i
    if os.path.exists(path):
        if os.path.isdir(path):
            total = 0
            for root, _, files in os.walk(path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root,f))
                    except Exception:
                        pass
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            print(f"{i}\tDIR\t{total}\t{mtime}")
        else:
            size = os.path.getsize(path)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            print(f"{i}\tFILE\t{size}\t{mtime}")
    else:
        print(f"{i}\tMISSING")
print('\nNote: sizes are in bytes.')