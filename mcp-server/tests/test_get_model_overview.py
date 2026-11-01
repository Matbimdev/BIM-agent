"""Pruebas sin Revit: fixture en samples/payloads y bridge simulado con MockTransport."""
import json
from pathlib import Path

import httpx
import pytest

from bim_agent_mcp.revit_client import RevitClient, RevitError
from bim_agent_mcp.tools.get_model_overview import CATEGORY_LIMIT, normalize

FIXTURE = Path(__file__).parents[2] / "samples" / "payloads" / "overview_sintetico.json"


@pytest.fixture
def raw():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def client(tmp_path, handler):
    token = tmp_path / "token"
    token.write_text("secreto\n", encoding="utf-8")
    return RevitClient(token_path=token, transport=httpx.MockTransport(handler))


def test_normalize_ordena_y_totaliza(raw):
    out = normalize(raw)
    assert [c["category"] for c in out["categories"]] == ["Floors", "Walls"]
    assert out["elements_total"] == 52
    assert [level["name"] for level in out["levels"]] == ["N1", "N2"]
    assert out["levels"][1]["elevation"] == {"value": 3.048, "unit": "m"}
    assert out["categories_meta"]["truncated"] is False


def test_normalize_traduce_unidades_y_conserva_las_desconocidas(raw):
    units = normalize(raw)["project"]["units"]
    assert units == {"length": "ft-in", "area": "ft2", "volume": "unidadRara"}


def test_truncado_avisa_y_conserva_el_total(raw):
    raw["categories"] = [{"category": f"C{i}", "count": 1} for i in range(CATEGORY_LIMIT + 5)]
    out = normalize(raw)
    assert len(out["categories"]) == CATEGORY_LIMIT
    assert out["categories_meta"]["truncated"] is True
    assert out["categories_meta"]["total"] == CATEGORY_LIMIT + 5
    assert out["categories_meta"]["hint"]
    assert out["elements_total"] == CATEGORY_LIMIT + 5


def test_links_se_omiten_si_no_se_piden(raw):
    del raw["links"]
    assert "links" not in normalize(raw)


def test_cliente_envia_token_y_args_en_el_cuerpo(tmp_path, raw):
    seen = {}

    def handler(request):
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=raw)

    client(tmp_path, handler).post("overview", {"include_links": False})
    assert seen == {"method": "POST", "path": "/bim-agent/overview",
                    "body": {"token": "secreto", "args": {"include_links": False}}}


def test_error_tipado_del_bridge_llega_con_accion(tmp_path):
    body = {"error": {"type": "NoDocument", "message": "Sin modelo", "action": "Abre el modelo"}}
    with pytest.raises(RevitError) as exc:
        client(tmp_path, lambda r: httpx.Response(409, json=body)).post("overview")
    assert exc.value.to_dict() == body


def test_token_rechazado(tmp_path):
    with pytest.raises(RevitError) as exc:
        client(tmp_path, lambda r: httpx.Response(401, json={"error": "unauthorized"})).post("overview")
    assert exc.value.error_type == "Unauthorized"


def test_revit_cerrado(tmp_path):
    def handler(request):
        raise httpx.ConnectError("rechazado")

    with pytest.raises(RevitError) as exc:
        client(tmp_path, handler).post("overview")
    assert exc.value.error_type == "BridgeUnavailable"


def test_timeout(tmp_path):
    def handler(request):
        raise httpx.ReadTimeout("lento")

    with pytest.raises(RevitError) as exc:
        client(tmp_path, handler).post("overview")
    assert exc.value.error_type == "Timeout"


def test_sin_archivo_de_token(tmp_path):
    with pytest.raises(RevitError) as exc:
        RevitClient(token_path=tmp_path / "no-existe").post("overview")
    assert exc.value.error_type == "BridgeUnavailable"
