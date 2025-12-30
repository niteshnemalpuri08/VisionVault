import requests

def test(username, password, role):
    r = requests.post('http://127.0.0.1:5000/auth/login', json={'username':username,'password':password,'role':role})
    print('->', role, username, '->', r.status_code, r.text)

if __name__ == '__main__':
    test('24cse001','24cse001','student')
    test('t01','t01','teacher')
    test('24cse001_parent','24cse001','parent')
