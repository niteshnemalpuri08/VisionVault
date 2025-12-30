import requests
print('Logging in teacher t01...')
r = requests.post('http://127.0.0.1:5000/auth/login', json={'username':'t01','password':'t01','role':'teacher'})
print(r.status_code)
print(r.text)
if r.status_code==200:
    token = r.json().get('token')
    print('Got token length', len(token))
    h={'Authorization':f'Bearer {token}'}
    r2 = requests.get('http://127.0.0.1:5000/api/teacher/t01/dashboard', headers=h)
    print('Dashboard', r2.status_code)
    print(r2.json())
