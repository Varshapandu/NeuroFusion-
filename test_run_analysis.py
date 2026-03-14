import requests

url = "http://127.0.0.1:5000/api/run-analysis"

payload = {
    "filepath": r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\backend\uploads\3911565283.parquet"
}

response = requests.post(url, json=payload)

print("STATUS:", response.status_code)
print("RESPONSE:")
print(response.text)
