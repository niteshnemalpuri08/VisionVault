import requests
import time
BASE='http://127.0.0.1:5000'

def wait_until_server(timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f'{BASE}/health', timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            time.sleep(0.5)
    return False


def login(u,p,role):
    r = requests.post(f'{BASE}/auth/login', json={'username':u,'password':p,'role':role})
    r.raise_for_status()
    return r.json()['token']

if __name__=='__main__':
    if not wait_until_server(15):
        print('Server not available, aborting tests')
        raise SystemExit(1)

    t = login('t01','t01','teacher')
    headers = {'Authorization':f'Bearer {t}'}

    # 1) Test attendance submission
    print('Posting attendance...')
    r = requests.post(f'{BASE}/api/attendance', json={'attendance':[{'roll':'24CSE001','present':True},{'roll':'24CSE002','present':False}]}, headers=headers)
    print('status', r.status_code, r.json())

    # 2) Test update student roll
    print('Updating student roll...')
    r = requests.patch(f'{BASE}/api/students/24CSE001', json={'roll':'24CSE999','name':'Student 001 Updated'}, headers=headers)
    print('status', r.status_code, r.json())

    # Verify parent rows updated (check there is at least one parent with student_roll 24CSE999)
    print('Checking parent for new roll...')
    r = requests.get(f'{BASE}/api/parents', headers=headers)
    parents = r.json()
    found = any(p.get('student_roll') == '24CSE999' for p in parents)
    print('parent updated?', found)

    # Revert roll back for idempotence
    print('Reverting roll...')
    r = requests.patch(f'{BASE}/api/students/24CSE999', json={'roll':'24CSE001','name':'Student 001'}, headers=headers)
    print('revert', r.status_code, r.json())
