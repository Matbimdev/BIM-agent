"""Pruebas sin Revit de la separacion entre vistas no colocadas exigibles e informativas."""
import json
from pathlib import Path

from openpyxl import load_workbook

from bim_agent_mcp.session import Session
from bim_agent_mcp.tools import get_sheets_and_views
from bim_agent_mcp.tools.export_report import build


def _vista(n, nombre, tipo, colocada=False):
    return {"name": nombre, "view_type": tipo, "placed": colocada,
            "unique_id": "v{}".format(n), "element_id": str(n)}


# Un caso por tipo, con la misma mezcla que Snowdon: plantas, cortes, alzados, tablas y leyenda
# exigibles; 3D y planos de area informativos.
RAW = {"sheets": [], "views": [
    _vista(1, "L2", "FloorPlan"),
    _vista(2, "Longitudinal", "Section"),
    _vista(3, "North", "Elevation"),
    _vista(4, "Structural Column Schedule", "Schedule"),
    _vista(5, "Legend 1", "Legend"),
    _vista(6, "Structure Only", "ThreeD"),
    _vista(7, "L2", "AreaPlan"),
    _vista(8, "Colocada", "FloorPlan", colocada=True),
    _vista(9, "{3D}", "ThreeD"),
]}


def test_marca_cada_vista_como_exigible_o_informativa():
    out = get_sheets_and_views.normalize(RAW)
    marca = {(v["name"], v["view_type"]): v["required"] for v in out["unplaced_views"]["data"]}
    assert marca == {
        ("L2", "FloorPlan"): True,
        ("Longitudinal", "Section"): True,
        ("North", "Elevation"): True,
        ("Structural Column Schedule", "Schedule"): True,
        ("Legend 1", "Legend"): True,
        ("Structure Only", "ThreeD"): False,
        ("L2", "AreaPlan"): False,
    }


def test_no_oculta_las_informativas_y_las_cuenta_aparte():
    out = get_sheets_and_views.normalize(RAW)
    assert out["unplaced_views"]["total"] == 7
    assert out["unplaced_summary"] == {"required": 5, "informative": 2}


def test_el_filtro_por_tipo_sigue_funcionando():
    out = get_sheets_and_views.normalize(RAW, view_types=["ThreeD"])
    assert [v["name"] for v in out["unplaced_views"]["data"]] == ["Structure Only"]
    assert out["unplaced_summary"] == {"required": 0, "informative": 1}


def test_la_regla_vis_001_solo_lleva_exigibles():
    tipos = {fila[5] for fila in get_sheets_and_views.rows(RAW)}
    assert len(get_sheets_and_views.rows(RAW)) == 5
    assert "ThreeD" not in tipos and "AreaPlan" not in tipos


def test_el_score_cuenta_solo_las_exigibles(tmp_path):
    overview = json.loads((Path(__file__).parents[2] / "samples" / "payloads" /
                           "overview_sintetico.json").read_text(encoding="utf-8"))
    overview["document"] = "Proyecto de prueba"
    session = Session()
    session.record("get_model_overview", {}, overview)
    session.record("get_sheets_and_views", {}, {**RAW, "document": "Proyecto de prueba"})
    out = build(session, path=str(tmp_path / "r.xlsx"))
    valores = {c["name"]: c["value"] for c in out["health_score"]["components"]}
    assert valores["vistas_no_colocadas"] == 5
    hoja = load_workbook(out["path"])["Vistas no colocadas"]
    assert hoja.max_row == 6   # encabezado y cinco exigibles
