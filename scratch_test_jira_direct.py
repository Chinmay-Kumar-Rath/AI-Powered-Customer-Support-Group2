import urllib.request, json, base64

# Test direct Jira API connectivity
jira_url = "https://govindverma.atlassian.net"
email = "govind12022004@gmail.com"
token = "ATATT3xFfGF0dHJ-mg00HDRzQ3ZBr_NmDwdkvhtOwoPx-UV914ZoT3TMjKQN1uaap2T3DpvhzwQoVyPSW9Gb_PGvlnBg4SU1NUlBBSuLNO2Zy-O3tNly1WBRaZtLnufjh-bOpapT_eqlUPaMffSoLS5PawkeBFQIXyqKIBfAlCQt8X24sf-u8_U=2F39B3C0"

creds = base64.b64encode(f"{email}:{token}".encode()).decode()

# Test 1: Check if Jira is reachable
print("=== Test Jira API Connectivity ===")
req = urllib.request.Request(
    f"{jira_url}/rest/api/3/myself",
    headers={
        "Authorization": f"Basic {creds}",
        "Accept": "application/json"
    }
)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        print(f"Status: {resp.status}")
        print(f"User: {data.get('displayName', 'unknown')}")
        print(f"Email: {data.get('emailAddress', 'unknown')}")
        print("Jira API is reachable!")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP Error: {e.code}")
    print(f"Response: {body[:500]}")
except Exception as e:
    print(f"Connection Error: {e}")

# Test 2: Check project exists
print("\n=== Test Jira Project SUP ===")
req = urllib.request.Request(
    f"{jira_url}/rest/api/3/project/SUP",
    headers={
        "Authorization": f"Basic {creds}",
        "Accept": "application/json"
    }
)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        print(f"Status: {resp.status}")
        print(f"Project: {data.get('name', 'unknown')}")
        print(f"Key: {data.get('key', 'unknown')}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP Error: {e.code}")
    print(f"Response: {body[:500]}")
except Exception as e:
    print(f"Connection Error: {e}")
