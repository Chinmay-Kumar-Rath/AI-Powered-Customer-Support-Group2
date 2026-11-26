import urllib.request, json, sys

def call(method, url, data=None):
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read()) if resp.headers.get("content-type","").startswith("application/json") else resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# Retry Jira sync
print("=== JIRA SYNC RETRY ===")
status, body = call("POST", "http://localhost:8000/integrations/jira/refresh/1", b"")
print(f"  Status: {status}")
print(f"  Response: {body}")

# Analytics overview
print("\n=== ANALYTICS OVERVIEW ===")
status, body = call("GET", "http://localhost:8000/analytics/overview")
print(json.dumps(body, indent=2))

# Analytics trends
print("\n=== ANALYTICS TRENDS (30 days) ===")
status, body = call("GET", "http://localhost:8000/analytics/trends?days=30")
if isinstance(body, list):
    for t in body[-3:]:
        print(t)
else:
    print(body)

# Analytics categories
print("\n=== ANALYTICS CATEGORIES ===")
status, body = call("GET", "http://localhost:8000/analytics/categories")
print(json.dumps(body, indent=2) if isinstance(body, (list, dict)) else body)

# Analytics escalations
print("\n=== ANALYTICS ESCALATIONS ===")
status, body = call("GET", "http://localhost:8000/analytics/escalations")
print(json.dumps(body, indent=2) if isinstance(body, (list, dict)) else body)

# Analytics satisfaction
print("\n=== ANALYTICS SATISFACTION ===")
status, body = call("GET", "http://localhost:8000/analytics/satisfaction")
print(json.dumps(body, indent=2) if isinstance(body, (list, dict)) else body)

# PDF report
print("\n=== PDF REPORT ===")
req = urllib.request.Request("http://localhost:8000/reports/summary?format=pdf")
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        pdf_data = resp.read()
        print(f"  Status: {resp.status}")
        print(f"  Content-Type: {resp.headers.get('content-type')}")
        print(f"  Size: {len(pdf_data)} bytes")
        print(f"  Starts with PDF header: {pdf_data[:5] == b'%PDF-'}")
except urllib.error.HTTPError as e:
    print(f"  Error: {e.code} - {e.read().decode()[:300]}")

# CSV report
print("\n=== CSV REPORT ===")
req = urllib.request.Request("http://localhost:8000/reports/summary?format=csv")
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        csv_data = resp.read().decode()
        print(f"  Status: {resp.status}")
        print(f"  Content-Type: {resp.headers.get('content-type')}")
        print(f"  Lines: {len(csv_data.splitlines())}")
        print(f"  First 3 lines:")
        for line in csv_data.splitlines()[:3]:
            print(f"    {line}")
except urllib.error.HTTPError as e:
    print(f"  Error: {e.code} - {e.read().decode()[:300]}")

# Integration status (final)
print("\n=== FINAL INTEGRATIONS STATUS ===")
status, body = call("GET", "http://localhost:8000/integrations/status")
print(json.dumps(body, indent=2) if isinstance(body, (list, dict)) else body)
