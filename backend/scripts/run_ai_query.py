import os
import json
import requests

url = os.getenv('API_URL','http://localhost:8000')
endpoint = f"{url}/api/copilot/chat"
payload = {"question": "What does BuildPulse do?"}
try:
    r = requests.post(endpoint, json=payload, timeout=30)
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print('request failed:', e)
