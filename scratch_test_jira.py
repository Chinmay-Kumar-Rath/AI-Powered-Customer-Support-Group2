import urllib.request, json

# Step 3: Jira refresh for ticket 1
req = urllib.request.Request(
    "http://localhost:8000/integrations/jira/refresh/1",
    data=b"",
    headers={"Content-Type": "application/json"},
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
