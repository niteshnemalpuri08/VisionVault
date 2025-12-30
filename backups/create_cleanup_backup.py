import os, zipfile
candidates = ['.venv','venv','backend/update_student_names.py','backend/assign_teachers.py','backend/assign_teacher_sections.py','backend/check_parent_credentials.py','backend/update_parent_credentials.py','backend/enhanced_model.pkl','frontend/gietlogo.jpg','test_predict_api.py']
os.makedirs('backups', exist_ok=True)
zip_path = os.path.join('backups','cleanup_backup.zip')
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in candidates:
        if os.path.exists(p):
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        full = os.path.join(root,f)
                        arcname = os.path.relpath(full)
                        try:
                            z.write(full, arcname)
                            print('Added',arcname)
                        except Exception as e:
                            print('Skip',arcname,'->',e)
            else:
                try:
                    z.write(p, os.path.relpath(p))
                    print('Added',p)
                except Exception as e:
                    print('Skip',p,'->',e)
        else:
            print('Missing',p)
print('\nBackup created at',zip_path)
print('Size:', os.path.getsize(zip_path) if os.path.exists(zip_path) else 'N/A')