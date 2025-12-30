import requests

BASE = 'http://127.0.0.1:5000'

def login(username, password, role):
    r = requests.post(f'{BASE}/auth/login', json={'username':username,'password':password,'role':role})
    r.raise_for_status()
    return r.json()['token']

if __name__ == '__main__':
    token = login('t01','t01','teacher')
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.get(f'{BASE}/api/teacher/t01/dashboard', headers=headers)
    print('Dashboard status', r.status_code)
    print(r.json())
