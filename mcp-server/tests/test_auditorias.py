"""Pruebas sin Revit de planos, familias, nomenclatura, parametros y su salida en Excel."""
import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

from bim_agent_mcp.revit_client import RevitError
from bim_agent_mcp.session import Session
from bim_agent_mcp.tools import audit_families, audit_naming, audit_parameters, get_sheets_and_views
from bim_agent_mcp.tools.common import compile_regex
from bim_agent_mcp.tools.export_report import build

DATA = json.loads((Path(__file__).parents[2] / "samples" / "payloads" / "auditorias_sintetico.json").read_text(encoding="utf-8"))
PATTERN = compile_regex(r"^[A-Z]{2}-PL-\d{3}$")
REQUIRED = ["Mark", "Fire Rating", "Costo"]
RULES = [{"param": "Mark", "regex": r"^P-\d{3}$"}]


def test_vistas_excluye_trabajo_y_sistema():
    out = get_sheets_and_views.normalize(DATA["sheets_views"])
    assert [s["number"] for s in out["sheets"]["data"]] == ["S-101", "S-102"]
    assert [v["name"] for v in out["unplaced_views"]["data"]] == ["Corte suelto"]
    assert out["unplaced_views"]["data"][0]["element_id"] == 22


def test_vistas_filtra_por_tipo():
    out = get_sheets_and_views.normalize(DATA["sheets_views"], view_types=["FloorPlan"])
    assert out["unplaced_views"]["total"] == 0


def test_familias_detecta_cada_regla():
    out = audit_families.normalize(DATA["families"])
    assert out["summary"] == {"in_place": 1, "unused": 1, "duplicated": 2, "type_count": 1}
    assert out["unused_not_evaluated"] == 2
    unused = [d["family"] for d in out["data"] if d["check"] == "unused"]
    assert unused == ["Puerta copia"]


def test_familias_no_confunde_tamanos_con_copias():
    found = audit_families.findings(DATA["families"])
    assert "Viga W 300" not in [f["family"] for f in found["duplicated"]]


def test_familias_ignora_referencias_y_nombres_parecidos():
    families = [{"family": name, "category": cat, "built_in": built_in, "in_place": False, "types": 1,
                 "instances": 0, "unique_id": name, "element_id": "1"}
                for name, cat, built_in in [
                    ("S1", "Rebar Shape", "OST_RebarShape"), ("S2", "Rebar Shape", "OST_RebarShape"),
                    ("Level Head", "Level Heads", "OST_LevelHeads"),
                    ("Column Tag", "Column Tags", "OST_StructuralColumnTags"),
                    ("Column Tag-45", "Column Tags", "OST_StructuralColumnTags"),
                    ("Door", "Doors", "OST_Doors"), ("Door 2", "Doors", "OST_Doors")]]
    found = audit_families.findings({"families": families})
    assert sorted(f["family"] for f in found["unused"]) == ["Column Tag", "Column Tag-45", "Door", "Door 2"]
    assert sorted(f["family"] for f in found["duplicated"]) == ["Door", "Door 2"]


def test_familias_filtra_checks():
    out = audit_families.normalize(DATA["families"], checks=["in_place"])
    assert list(out["summary"]) == ["in_place"]
    assert out["total"] == 1


def test_naming_cuenta_y_lista_incumplimientos():
    out = audit_naming.normalize(DATA["names"], "views", PATTERN, "BEP 4.2")
    assert (out["checked"], out["compliant"], out["total"]) == (3, 1, 2)
    assert out["data"][0]["element_id"] == 43


def test_naming_filtra_categoria():
    out = audit_naming.normalize(DATA["names"], "views", PATTERN, "BEP", category="section")
    assert out["checked"] == 1


def test_regex_invalido_y_target_invalido():
    with pytest.raises(RevitError) as exc:
        compile_regex("[")
    assert exc.value.error_type == "InvalidRegex"
    with pytest.raises(RevitError) as exc:
        audit_naming.validate_target("muros")
    assert exc.value.error_type == "InvalidTarget"


def test_parametros_distingue_faltante_vacio_e_invalido():
    out = audit_parameters.normalize(DATA["elements"], REQUIRED, RULES)
    summary = {s["param"]: s for s in out["summary"]}
    assert summary["Costo"]["missing"] == 2
    assert summary["Fire Rating"]["empty"] == 1
    assert summary["Mark"]["invalid"] == 1
    assert out["checked"] == 2
    assert out["total"] == 4


def test_parametro_opcional_vacio_no_es_hallazgo():
    assert audit_parameters.normalize(DATA["elements"], [], [{"param": "Fire Rating", "allowed": ["EI30"]}])["total"] == 0


def test_valores_permitidos():
    out = audit_parameters.normalize(DATA["elements"], [], [{"param": "Mark", "allowed": ["P-001"]}])
    assert [d["value"] for d in out["data"]] == ["X9"]


def test_limit_trunca_pero_el_reporte_conserva_todo():
    assert audit_parameters.normalize(DATA["elements"], REQUIRED, RULES, limit=1)["truncated"] is True
    assert len(audit_parameters.rows(DATA["elements"], "Doors", REQUIRED, RULES)) == 4


def test_reporte_con_todas_las_auditorias(tmp_path):
    session = Session()
    overview = json.loads((Path(__file__).parents[2] / "samples" / "payloads" / "overview_sintetico.json").read_text(encoding="utf-8"))
    overview["document"] = "Proyecto de prueba"
    session.record("get_model_overview", {}, overview)
    session.record("get_sheets_and_views", {}, DATA["sheets_views"])
    session.record("audit_families", {}, DATA["families"])
    session.record("audit_naming", {}, DATA["names"])
    session.add_rule_sheet("a", "Nombres", audit_naming.rows(DATA["names"], PATTERN, "BEP"))
    session.add_rule_sheet("b", "Nombres", audit_naming.rows(DATA["names"], PATTERN, "BEP 2"))
    session.record("audit_parameters", {}, DATA["elements"])
    session.add_rule_sheet("c", "Parametros", audit_parameters.rows(DATA["elements"], "Doors", REQUIRED, RULES))
    out = build(session, path=str(tmp_path / "r.xlsx"))
    assert out["sheets"] == ["Resumen", "Familias", "Vistas no colocadas", "Nombres 1", "Nombres 2", "Parametros 1", "Trazabilidad"]
    assert out["sections_missing"] == ["warnings", "links"]
    names = {c["name"]: c["value"] for c in out["health_score"]["components"]}
    assert names["familias_in_place"] == 1
    assert names["vistas_no_colocadas"] == 1
    book = load_workbook(out["path"])
    assert book["Familias"].max_row > 1
    assert book["Vistas no colocadas"]["D2"].value == 22
