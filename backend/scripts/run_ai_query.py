import os
import json
import requests

url = os.getenv('API_URL','http://localhost:8000')
endpoint = f"{url}/ai/chat"
payload = {"query": "What does BuildPulse do?", "use_db": True}
try:
    r = requests.post(endpoint, json=payload, timeout=30)
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print('request failed:', e)
