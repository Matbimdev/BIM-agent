"""Smoke test de /health (ADR-006). Python 3, sin dependencias.
Uso: python scripts/smoke_health.py
"""
import json, os, urllib.request, urllib.error

URL = "http://localhost:48884/bim-agent/health"
token = open(os.path.join(os.environ["APPDATA"], "BIMAgent", "token")).read().strip()

def post(body):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

print("con token  :", post({"token": token, "args": {}}))
print("sin token  :", post({"args": {}}))
