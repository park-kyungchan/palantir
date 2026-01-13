import requests
import json

app_id = "palantir_pilot"
app_key = "120869bee25107f293c726520c24398bc2e4d8941c8b0573adf1aa1c7859eec0"

conv_id = "977fe8b8-65c7-45cf-ae4e-cc151950f200"
url = f"https://api.mathpix.com/v3/converter/{conv_id}"

headers = {"app_id": app_id, "app_key": app_key}

print(f"Checking status for {conv_id}...")
response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")
data = response.json()
print("Full Response:")
print(json.dumps(data, indent=2))

# Try direct endpoint
print("\nTrying /v3/converter/{id}.pdf endpoint...")
pdf_url = f"https://api.mathpix.com/v3/converter/{conv_id}.pdf"
resp = requests.get(pdf_url, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Content Type: {resp.headers.get('Content-Type')}")
if resp.status_code == 200:
    print("Found PDF content!")

print("\nTrying /v3/converter/{id}/pdf endpoint...")
pdf_url_2 = f"https://api.mathpix.com/v3/converter/{conv_id}/pdf"
resp2 = requests.get(pdf_url_2, headers=headers)
print(f"Status: {resp2.status_code}")
print(f"Content Type: {resp2.headers.get('Content-Type')}")
