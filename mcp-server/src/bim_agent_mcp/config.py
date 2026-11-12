"""Configuracion del servidor MCP. Variables de entorno opcionales."""
import os
from pathlib import Path

# Si BIM_AGENT_BRIDGE_URL esta definida se usa fija. Si no, se parte de 48884 y, cuando ese puerto
# no responde o no tiene modelo, se busca en BRIDGE_PORTS: pyRevit da el siguiente puerto libre a
# cada sesion de Revit abierta (por ejemplo 2026 en 48884 y 2027 en 48885).
BRIDGE_URL_FIXED = os.environ.get("BIM_AGENT_BRIDGE_URL")
BRIDGE_PORTS = range(48884, 48891)
BRIDGE_URL = BRIDGE_URL_FIXED or "http://localhost:48884/bim-agent"
DISCOVERY_TIMEOUT_SECONDS = 2.0
TIMEOUT_SECONDS = float(os.environ.get("BIM_AGENT_TIMEOUT", "60"))
TOKEN_PATH = Path(os.environ.get("APPDATA", str(Path.home()))) / "BIMAgent" / "token"
REPORT_DIR = Path(os.environ.get("BIM_AGENT_REPORT_DIR", str(Path.home() / "Documents" / "BIMAgent")))

# Score de salud: heuristica provisional, sin calibrar. Pesos y limites son juicio del autor, no
# salen de datos: con un solo modelo de prueba no se pueden calibrar.
# Cada componente vale su peso completo con valor 0 y baja en linea recta hasta 0 al llegar a su
# limite. Warnings va por cada 1000 elementos; los demas son conteos absolutos, asi que no escalan
# con el tamano del modelo (50 familias sin usar pesan igual en 185 familias que en 2000).
# Referencia: Snowdon Towers Structural limpio da 76 (11/11/2026). Pierde 13,2 puntos por 44
# familias sin usar, 24 de ellas etiquetas de plantilla, y 10,8 por 36 vistas exigibles sin plano.
HEALTH_COMPONENTS = {
    "warnings_por_1000": {"weight": 0.25, "limit": 110},
    "familias_in_place": {"weight": 0.15, "limit": 20},
    "familias_no_usadas": {"weight": 0.15, "limit": 50},
    "vistas_no_colocadas": {"weight": 0.15, "limit": 50},
    "cad_importados": {"weight": 0.15, "limit": 10},
    "hallazgos_vinculos": {"weight": 0.15, "limit": 5},
}

# Vistas que no exigen plano: prefijo de trabajo y vistas creadas por Revit, como {3D}.
WORKING_VIEW_PATTERN = r"^(WIP|TRABAJO|\{)"
# Tipos de vista que la regla VIS-001 exige ver en un plano. Los demas (ThreeD, AreaPlan, ...) se
# reportan como informativos y no cuentan para la regla ni para el score.
REQUIRED_VIEW_TYPES = frozenset({
    "FloorPlan", "CeilingPlan", "EngineeringPlan", "Elevation", "Section", "Detail", "DraftingView",
    "Legend", "Schedule", "PanelSchedule", "ColumnSchedule",
})
RESULT_LIMIT = 200
