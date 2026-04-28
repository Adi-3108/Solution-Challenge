import urllib.request
import json

data = json.dumps({"email": "test@test.com", "password": "password", "role": "viewer"}).encode("utf-8")
req = urllib.request.Request("http://localhost:8000/api/v1/auth/register", data=data, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print("Headers:", response.headers)
        print("Body:", response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("Status:", e.code)
    print("Headers:", e.headers)
    print("Body:", e.read().decode("utf-8"))
