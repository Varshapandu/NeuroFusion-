import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000/api/fl"

print("▶ Starting FL client...")
r1 = requests.post(f"{BASE_URL}/start-client")
print("Status:", r1.status_code)
print(r1.text)

time.sleep(2)

print("\n📊 Fetching FL status...")
r2 = requests.get(f"{BASE_URL}/status")
print("Status:", r2.status_code)
print(json.dumps(r2.json(), indent=2))
