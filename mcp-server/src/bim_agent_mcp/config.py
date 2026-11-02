"""Configuracion del servidor MCP. Variables de entorno opcionales."""
import os
from pathlib import Path

BRIDGE_URL = os.environ.get("BIM_AGENT_BRIDGE_URL", "http://localhost:48884/bim-agent")
TIMEOUT_SECONDS = float(os.environ.get("BIM_AGENT_TIMEOUT", "60"))
TOKEN_PATH = Path(os.environ.get("APPDATA", str(Path.home()))) / "BIMAgent" / "token"
REPORT_DIR = Path(os.environ.get("BIM_AGENT_REPORT_DIR", str(Path.home() / "Documents" / "BIMAgent")))

# Score de salud: heuristica sin calibrar. Cada componente vale 100% en 0 y 0% al llegar a su limite.
HEALTH_COMPONENTS = {
    "warnings_por_1000": {"weight": 0.25, "limit": 110},
    "familias_in_place": {"weight": 0.15, "limit": 20},
    "familias_no_usadas": {"weight": 0.15, "limit": 50},
    "vistas_no_colocadas": {"weight": 0.15, "limit": 50},
    "cad_importados": {"weight": 0.15, "limit": 10},
    "hallazgos_vinculos": {"weight": 0.15, "limit": 5},
}
