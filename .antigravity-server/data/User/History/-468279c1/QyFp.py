import requests
import json
import os

app_id = "palantir_pilot"
app_key = "120869bee25107f293c726520c24398bc2e4d8941c8b0573adf1aa1c7859eec0"

url = "https://api.mathpix.com/v3/converter"

# Simple MMD with Math and Structure
mmd_content = r"""
# Test PDF Generation

Here is a math equation:
$$
\int_0^\infty x^2 dx
$$

**Bold Text** and *Italic*.

\begin{equation}
E = mc^2
\end{equation}
"""

payload = {
    "mmd": mmd_content,
    "formats": {"pdf": True, "html": True},
    "options": {
        "pdf": {
            "page_size": "A4"
        }
    }
}

print(f"Sending request to {url}...")
headers = {"app_id": app_id, "app_key": app_key, "Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        res = response.json()
        if "conversion_id" in res:
            conv_id = res["conversion_id"]
            print(f"Conversion ID: {conv_id}")
            
            import time
            while True:
                status_url = f"{url}/{conv_id}"
                print(f"Polling {status_url}...")
                stat_resp = requests.get(status_url, headers=headers, timeout=10)
                stat_json = stat_resp.json()
                print(f"Status: {stat_json.get('status', 'unknown')}")
                
                if stat_json.get("status") == "completed":
                    if "pdf" in stat_json:
                        pdf_url = stat_json["pdf"]
                        print(f"PDF URL: {pdf_url}")
                        pdf_resp = requests.get(pdf_url)
                        with open("test_output.pdf", "wb") as f:
                            f.write(pdf_resp.content)
                        print("Downloaded test_output.pdf")
                    break
                elif stat_json.get("status") == "error":
                    print(f"Error: {stat_json}")
                    break
                    
                time.sleep(2)
        else:
            print(f"No ID. Resp: {res}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
