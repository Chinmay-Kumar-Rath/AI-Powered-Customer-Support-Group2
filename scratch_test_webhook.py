import urllib.request, json, sys

payload = json.dumps({
    "subject": "VPN connection drops frequently",
    "description": "My VPN connection drops every 10 minutes since Monday morning. I am unable to access internal resources reliably.",
    "requester_email": "gv254860@gmail.com",
    "priority": "P2",
    "category": "VPN"
}).encode()

req = urllib.request.Request(
    "http://localhost:8000/intake/webhook",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "X-API-Key": "sp_wh_9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode()
        print(f"Status: {resp.status}")
        print(f"Response: {body}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Response: {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
