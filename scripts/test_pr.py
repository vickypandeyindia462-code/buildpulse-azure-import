import requests

body = [{
    "id": "demo-script-001",
    "title": "Demo Script PR",
    "content": "Testing PR creation via script",
    "source": "script-test"
}]

r = requests.post('http://127.0.0.1:8000/submit/pr', json=body)
print('STATUS', r.status_code)
print(r.text)
