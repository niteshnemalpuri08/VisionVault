import requests
import time
from requests.exceptions import ConnectionError

BASE = 'http://127.0.0.1:5000'


def login(username, password, role):
    attempts = 0
    while attempts < 3:
        try:
            r = requests.post(f'{BASE}/auth/login', json={'username': username, 'password': password, 'role': role}, timeout=5)
            if r.status_code != 200:
                print(f'Login failed for {username} ({role}):', r.status_code, r.text)
                r.raise_for_status()
            return r.json()['token']
        except ConnectionError as e:
            attempts += 1
            print(f'Connection error during login for {username}, retry {attempts}/3')
            time.sleep(0.5)
    raise ConnectionError('Failed to connect to server after 3 attempts')


def check(endpoint, headers=None, params=None):
    url = f'{BASE}{endpoint}'
    attempts = 0
    while attempts < 3:
        try:
            r = requests.get(url, headers=headers or {}, params=params, timeout=5)
            print(f'{endpoint} ->', r.status_code)
            try:
                data = r.json()
                print('  keys:', list(data.keys()) if isinstance(data, dict) else f'len={len(data)}')
            except Exception:
                print('  non-json response')
            r.raise_for_status()
            return
        except ConnectionError:
            attempts += 1
            print(f'Connection error for {endpoint}, retry {attempts}/3')
            time.sleep(0.5)
    raise ConnectionError(f'Failed to fetch {endpoint} after 3 attempts')


if __name__ == '__main__':
    print('Logging in teacher t01...')
    ttoken = login('t01', 't01', 'teacher')
    theaders = {'Authorization': f'Bearer {ttoken}'}

    print('Logging in student 24cse001...')
    stoken = login('24cse001', '24cse001', 'student')
    sheaders = {'Authorization': f'Bearer {stoken}'}

    print('Logging in parent 24cse001_parent...')
    try:
        ptoken = login('24cse001_parent', '24cse001_parent', 'parent')
        pheaders = {'Authorization': f'Bearer {ptoken}'}
    except Exception:
        print('Continuing without parent-specific tests')
        pheaders = None

    # public
    check('/health')
    # lists (require auth)
    check('/api/students', headers=theaders)
    check('/api/teachers', headers=theaders)
    check('/api/parents', headers=theaders)

    # student-specific
    check('/api/students/24CSE001', headers=theaders)

    # teacher endpoints
    check('/api/subject-attendance', headers=theaders, params={'student_roll': '24CSE001'})
    check('/api/assignments', headers=theaders)
    check('/api/behavior', headers=theaders, params={'student_roll': '24CSE001'})
    check('/api/internal-marks', headers=theaders, params={'student_roll': '24CSE001'})
    check('/api/teacher/t01/dashboard', headers=theaders)
    check('/api/teachers/t01/accessible-students', headers=theaders)

    # parent/student relevant endpoints
    check('/api/assignments', headers=pheaders)
    if pheaders:
        check(f'/api/parent/24cse001_parent/dashboard', headers=pheaders)
    print('Smoke tests completed successfully')
