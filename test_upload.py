import requests

url = "http://127.0.0.1:5000/api/upload"
files = {"file": open(r"C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project\Dataset\test_eegs\3911565283.parquet", "rb")}

response = requests.post(url, files=files)

print("STATUS CODE:", response.status_code)
print("RAW RESPONSE:")
print(response.text)

