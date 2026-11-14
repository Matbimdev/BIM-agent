"""Pruebas sin Revit de query_elements, get_quantities y audit_links_coordinates."""
import json
from pathlib import Path

import pytest

from bim_agent_mcp.revit_client import RevitError
from bim_agent_mcp.tools import audit_links_coordinates as links
from bim_agent_mcp.tools import get_quantities as quantities
from bim_agent_mcp.tools import query_elements as queries


def state(value=None, quantity=None, source="instance", found=True):
    return {"found": found, "source": source, "has_value": value is not None or quantity is not None,
            "value": value, "quantity": quantity}


def element(uid, level, width, mark, fire=None):
    return {"unique_id": uid, "element_id": "7", "name": "P", "category": "Doors", "family": "Puerta",
            "type": "T1", "level": level,
            "params": {"Width": state("3' 0\"", {"value": width, "unit": "m"}, "type"),
                       "Mark": state(mark), "Fire": state(fire)}}


RAW = {"available_params": ["Width", "Mark", "Fire Rating"],
       "elements": [element("a", "N1", 0.9, "P-01", "EI30"), element("b", "N2", 1.2, None)]}


def query(filters=(), fields=("Mark",), level=None, include_type=True, limit=100):
    return queries.normalize(RAW, level, None, list(filters), list(fields), include_type, limit)


def test_query_lee_magnitudes_y_texto():
    out = query(fields=["Width", "Mark"])
    assert out["data"][0]["params"] == {"Width": {"value": 0.9, "unit": "m"}, "Mark": "P-01"}
    assert out["data"][0]["element_id"] == 7


@pytest.mark.parametrize("rule,expected", [
    ({"param": "Mark", "op": "empty"}, ["b"]),
    ({"param": "Mark", "op": "not_empty"}, ["a"]),
    ({"param": "Mark", "op": "eq", "value": "p-01"}, ["a"]),
    ({"param": "Mark", "op": "neq", "value": "P-01"}, ["b"]),
    ({"param": "Mark", "op": "contains", "value": "-0"}, ["a"]),
    ({"param": "Width", "op": "gt", "value": 1}, ["b"]),
    ({"param": "Width", "op": "lt", "value": 1}, ["a"]),
])
def test_query_operadores(rule, expected):
    assert [e["unique_id"] for e in query([rule])["data"]] == expected


def test_query_filtra_nivel_y_excluye_tipo():
    assert query(level="n2")["total"] == 1
    assert query(fields=["Width"], include_type=False)["data"][0]["params"]["Width"] is None


def test_query_limite_maximo():
    raw = {"available_params": [], "elements": [element(str(i), "N1", 1, "M") for i in range(600)]}
    out = queries.normalize(raw, None, None, [], ["Mark"], True, 9999)
    assert out["returned"] == 500 and out["truncated"] is True


def test_query_parametro_inexistente_sugiere():
    raw = {"available_params": ["Fire Rating"], "elements": [
        {**element("a", "N1", 1, "M"), "params": {"Fire Rate": state(found=False)}}]}
    with pytest.raises(RevitError) as exc:
        queries.normalize(raw, None, None, [], ["Fire Rate"])
    assert exc.value.error_type == "ParameterNotFound"
    assert "Fire Rating" in exc.value.action


def test_query_filtro_invalido():
    for rule in ({"param": "Mark", "op": "like"}, {"param": "Width", "op": "gt", "value": "alto"}):
        with pytest.raises(RevitError) as exc:
            queries.validate([rule])
        assert exc.value.error_type == "InvalidFilter"


def q_element(kind, level, area):
    return {"type": kind, "level": level, "phase": "F", "length": None, "volume": None,
            "area": {"value": area, "unit": "m2"} if area is not None else None}


Q_RAW = {"category": "Floors", "built_in": "OST_Floors", "elements": [
    q_element("L20", "N1", 10.1234), q_element("L20", "N1", 5), q_element("L20", "N2", None), q_element("L30", "N2", 2)]}


def test_metrado_agrupa_y_declara_elementos_sin_valor():
    out = quantities.normalize(Q_RAW, ["type", "level"])
    assert out["metric"] == "area"
    assert out["data"][0] == {"group": {"type": "L20", "level": "N1"}, "count": 2,
                              "quantity": {"value": 15.123, "unit": "m2"}, "elements_without_value": 0}
    assert out["grand_total"] == {"count": 4, "quantity": {"value": 17.123, "unit": "m2"}}
    assert out["elements_without_value"] == 1
    assert "HOST_AREA_COMPUTED" in out["criterion"]


def test_metrado_conteo_y_categoria_sin_metrica_natural():
    raw = {"category": "Doors", "built_in": "OST_Doors", "elements": [q_element("P", "N1", None)]}
    out = quantities.normalize(raw, [])
    assert out["metric"] == "count"
    assert out["grand_total"] == {"count": 1, "quantity": None}


def test_metrado_validaciones():
    with pytest.raises(RevitError):
        quantities.validate(["type", "level", "phase"], None)
    with pytest.raises(RevitError):
        quantities.validate(["color"], None)
    with pytest.raises(RevitError):
        quantities.validate([], "peso")


def link(**kwargs):
    base = {"name": "EST.rvt", "kind": "rvt", "loaded": True, "path_found": True, "status": "Loaded",
            "instances": 1, "pinned": True, "unique_id": "l", "element_id": "9"}
    return {**base, **kwargs}


def cad(linked, pinned):
    return {"name": "x.dwg", "linked": linked, "pinned": pinned, "unique_id": "c", "element_id": "8"}


def point(distance):
    zero = {"value": 0.0, "unit": "m"}
    return {"ns": zero, "ew": zero, "elevation": zero, "distance_from_origin": {"value": distance, "unit": "m"}}


def links_raw(items=(), cads=(), distance=0.0):
    return {"links": list(items), "cad": list(cads), "base_point": point(distance), "survey_point": point(0.0)}


def rules(raw):
    return [item["rule"] for item in links.findings(raw)]


def test_vinculos_sin_hallazgos_y_declaran_lo_no_evaluado():
    out = links.normalize(links_raw([link()], [cad(True, True)]))
    assert out["findings"] == []
    assert out["links"][0]["positioning"] == "not_evaluated"
    assert out["not_evaluated"]


def test_vinculos_detecta_cada_regla():
    assert rules(links_raw([link(pinned=False)])) == ["link_pinned"]
    assert rules(links_raw([link(loaded=False, status="Unloaded")])) == ["link_loaded"]
    assert rules(links_raw([link(loaded=False, path_found=False, status="NotFound")])) == ["link_path"]
    assert rules(links_raw(cads=[cad(False, True)])) == ["cad_imported"]
    assert rules(links_raw(cads=[cad(True, False)])) == ["cad_pinned"]
    assert rules(links_raw(distance=10001)) == ["base_point_distance"]
    assert rules(links_raw(distance=10000)) == []


def test_vinculos_filas_del_reporte():
    rows = links.rows(links_raw([link(pinned=False)]))
    assert rows[0][0] == "VIN-003"
    assert rows[0][3] == 9


def test_vinculo_sin_fijar_apunta_a_la_instancia_y_no_al_tipo():
    raw = links_raw([link(pinned=False, unpinned_instances=[{"unique_id": "inst-1", "element_id": "91"}])])
    found = links.findings(raw)
    assert [(f["rule"], f["unique_id"], f["element_id"], f["target"]) for f in found] == [
        ("link_pinned", "inst-1", "91", "EST.rvt")]
    out = links.normalize(raw)
    assert out["links"][0]["unique_id"] == "l"
    assert out["links"][0]["unpinned_instances"] == [{"unique_id": "inst-1", "element_id": 91}]
    assert out["findings"][0]["element_id"] == 91


def test_vinculo_con_varias_instancias_da_un_hallazgo_por_instancia_sin_fijar():
    raw = links_raw([link(instances=3, pinned=False, unpinned_instances=[
        {"unique_id": "a", "element_id": "1"}, {"unique_id": "b", "element_id": "2"}])])
    assert [f["unique_id"] for f in links.findings(raw)] == ["a", "b"]
    assert [row[2] for row in links.rows(raw)] == ["a", "b"]


def test_snowdon_real_hallazgos_de_vinculos_apuntan_a_instancias():
    fixture = Path(__file__).parents[2] / "samples" / "payloads" / "links_coordinates_snowdon.json"
    raw = json.loads(fixture.read_text(encoding="utf-8"))["raw"]
    out = links.normalize(raw)
    pinned = [f for f in out["findings"] if f["rule"] == "link_pinned"]
    type_ids = {link["unique_id"] for link in out["links"]}
    assert len(pinned) == 6
    assert all(f["unique_id"] not in type_ids for f in pinned)
    assert [f["rule"] for f in out["findings"]].count("cad_imported") == 1
    assert [f["rule"] for f in out["findings"]].count("cad_pinned") == 1
