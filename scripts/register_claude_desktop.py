"""Agrega bim-agent a la configuracion de Claude Desktop, sin tocar lo demas.
Crea una copia .bak antes de escribir. Uso: py -3 scripts/register_claude_desktop.py
"""
import glob, json, os, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
candidates = [Path(os.environ["APPDATA"]) / "Claude"]
candidates += [Path(p) for p in glob.glob(os.path.join(
    os.environ.get("LOCALAPPDATA", ""), "Packages", "Claude_*", "LocalCache", "Roaming", "Claude"))]
folders = [c for c in candidates if c.is_dir()]
if not folders:
    sys.exit("No encontre la carpeta de Claude Desktop. Abre Settings > Developer > Edit Config y repite.")

uv = shutil.which("uv")
if not uv:
    sys.exit("No encontre uv en el PATH. Instalalo y repite.")

entry = {"command": uv,
         "args": ["run", "--directory", str(ROOT / "mcp-server"), "bim-agent-mcp"]}

for folder in folders:
    path = folder / "claude_desktop_config.json"
    config = {}
    if path.exists():
        text = path.read_text(encoding="utf-8-sig")
        try:
            config = json.loads(text) if text.strip() else {}
        except ValueError as err:
            sys.exit(f"{path} no es JSON valido, no lo modifique: {err}")
        shutil.copy2(path, path.with_name(path.name + ".bak"))
    config.setdefault("mcpServers", {})["bim-agent"] = entry
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Actualizado:", path)

print("Listo. Cierra Claude Desktop por completo y vuelve a abrirlo.")
