"""Configuracion del servidor MCP. Variables de entorno opcionales."""
import os
from pathlib import Path

BRIDGE_URL = os.environ.get("BIM_AGENT_BRIDGE_URL", "http://localhost:48884/bim-agent")
TIMEOUT_SECONDS = float(os.environ.get("BIM_AGENT_TIMEOUT", "60"))
TOKEN_PATH = Path(os.environ.get("APPDATA", str(Path.home()))) / "BIMAgent" / "token"
