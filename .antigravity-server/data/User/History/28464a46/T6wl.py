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
print("\nTrying /pdf endpoint...")
pdf_url = f"{url}" # Just the same URL but maybe the response above has hidden keys?
# No, let's try appending /pdf
print(f"GET {url}/pdfl") # typo intentionally avoided? no, let's try standard
# Accessing result content directly?
