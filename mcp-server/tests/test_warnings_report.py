"""Pruebas sin Revit de get_warnings, la sesion y export_report."""
import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

from bim_agent_mcp.revit_client import RevitError
from bim_agent_mcp.session import Session
from bim_agent_mcp.tools.export_report import build, health_score
from bim_agent_mcp.tools.get_warnings import normalize

PAYLOADS = Path(__file__).parents[2] / "samples" / "payloads"


def load(name):
    return json.loads((PAYLOADS / name).read_text(encoding="utf-8"))


@pytest.fixture
def session():
    current = Session()
    overview = load("overview_sintetico.json")
    overview["document"] = "Proyecto de prueba"
    current.record("get_model_overview", {}, overview)
    current.record("get_warnings", {"top": 20}, load("warnings_sintetico.json"))
    return current


def test_agrupa_ordena_y_calcula_densidad():
    out = normalize(load("warnings_sintetico.json"), elements_total=52)
    assert out["total"] == 3
    assert out["data"][0]["description"] == "Muros superpuestos"
    assert out["data"][0]["count"] == 2
    assert [e["unique_id"] for e in out["data"][0]["sample_elements"]] == ["u1", "u2"]
    assert out["data"][0]["sample_elements"][0] == {
        "unique_id": "u1", "element_id": 1, "name": "=Muro", "category": "Walls", "level": "N1"}
    assert out["warnings_por_1000_elementos"] == 57.7


def test_filtro_no_cambia_la_densidad_del_modelo():
    out = normalize(load("warnings_sintetico.json"), 52, severity="error")
    assert out["total"] == 1
    assert out["warnings_por_1000_elementos"] == 57.7


def test_top_trunca_y_avisa():
    out = normalize(load("warnings_sintetico.json"), 52, top=1)
    assert out["truncated"] is True
    assert out["groups_total"] == 2
    assert out["hint"]


def test_modelo_sin_elementos_no_divide_por_cero():
    assert normalize({"warnings": []}, 0)["warnings_por_1000_elementos"] is None


def test_score_parcial_lo_declara():
    score = health_score({"warnings_por_1000": 44, "cad_importados": 0})
    assert score["complete"] is False
    assert "familias_in_place" in score["missing_components"]
    assert score["components"][0]["points"] == 15.0
    assert score["value"] == 75


def test_cambio_de_documento_reinicia_la_sesion(session):
    session.record("get_model_overview", {}, {"document": "Otro modelo"})
    assert list(session.results) == ["get_model_overview"]
    assert len(session.calls) == 1


def test_reporte_excel(tmp_path, session):
    out = build(session, path=str(tmp_path / "r.xlsx"))
    assert out["sheets"] == ["Resumen", "Warnings", "Trazabilidad"]
    assert out["sections_included"] == ["warnings"]
    assert "families" in out["sections_missing"]
    book = load_workbook(out["path"])
    rows = list(book["Warnings"].values)
    assert rows[1][:5] == ("WARN-001", "Muros superpuestos", "u1", 1, "=Muro")
    assert len(rows) == 5
    assert book["Warnings"]["E2"].data_type == "s"
    assert rows[4][0] == "WARN-002"
    assert "(parcial)" in book["Resumen"]["B5"].value
    assert [row[0] for row in book["Trazabilidad"].values][1:] == ["get_model_overview", "get_warnings"]


def test_reporte_sin_auditorias_no_inventa():
    current = Session()
    current.record("get_model_overview", {}, {"document": "x"})
    with pytest.raises(RevitError) as exc:
        build(current)
    assert exc.value.error_type == "NoAuditData"


def test_seccion_invalida(session):
    with pytest.raises(RevitError) as exc:
        build(session, ["inventada"])
    assert exc.value.error_type == "InvalidSection"


def test_archivo_bloqueado_da_error_util(tmp_path, session):
    target = tmp_path / "r.xlsx"
    target.mkdir()
    with pytest.raises(RevitError) as exc:
        build(session, path=str(target))
    assert exc.value.error_type == "ReportNotSaved"
