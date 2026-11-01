"""Smoke test contra Revit abierto. Python 3, sin dependencias.
Uso: py -3 scripts/smoke.py overview [--save nombre] [--args "{\"include_links\": true}"]
"""
import argparse, json, os, sys, urllib.error, urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("endpoint")
parser.add_argument("--args", default="{}")
parser.add_argument("--save", help="guarda la respuesta en samples/payloads/<nombre>.json")
opts = parser.parse_args()

token = (Path(os.environ["APPDATA"]) / "BIMAgent" / "token").read_text().strip()
body = json.dumps({"token": token, "args": json.loads(opts.args)}).encode()
request = urllib.request.Request(f"http://localhost:48884/bim-agent/{opts.endpoint}", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(request, timeout=120) as response:
        status, text = response.status, response.read().decode("utf-8")
except urllib.error.HTTPError as err:
    status, text = err.code, err.read().decode("utf-8")
except urllib.error.URLError as err:
    sys.exit(f"Sin conexion con el bridge: {err.reason}")

print("HTTP", status)
pretty = json.dumps(json.loads(text), indent=2, ensure_ascii=False)
print(pretty)
if opts.save and status == 200:
    path = Path(__file__).parents[1] / "samples" / "payloads" / f"{opts.save}.json"
    path.write_text(pretty, encoding="utf-8")
    print("Guardado en", path)
