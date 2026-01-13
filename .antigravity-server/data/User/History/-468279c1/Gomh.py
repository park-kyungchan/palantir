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
        print("Success!")
        print(f"Keys: {response.json().keys()}")
        with open("test_output.pdf", "wb") as f:
            # Need to check how PDF is returned. Usually a URL or base64?
            # Docs say 'pdf' key in response might be a URL.
            res = response.json()
            if "pdf" in res:
                pdf_url = res["pdf"]
                print(f"PDF URL: {pdf_url}")
                pdf_resp = requests.get(pdf_url)
                f.write(pdf_resp.content)
                print("Downloaded test_output.pdf")
            else:
                print(f"No PDF key. Resp: {res}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
