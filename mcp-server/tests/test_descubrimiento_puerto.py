"""Descubrimiento del puerto del bridge cuando hay varias sesiones de Revit abiertas."""
import json

import httpx
import pytest

from bim_agent_mcp.revit_client import RevitClient, RevitError


def make_client(tmp_path, sessions, discover=True):
    """sessions: {puerto: titulo del documento o None}. Puertos ausentes rechazan la conexion."""
    token = tmp_path / "token"
    token.write_text("secreto", encoding="utf-8")
    calls = []

    def handler(request):
        port = request.url.port
        calls.append((port, request.url.path))
        if port not in sessions:
            raise httpx.ConnectError("rechazado")
        doc = sessions[port]
        if request.url.path.endswith("/health"):
            return httpx.Response(200, json={"status": "ok", "revit_version": "2027", "document": doc})
        if doc is None:
            return httpx.Response(409, json={"error": {"type": "NoDocument", "message": "Sin modelo", "action": "Abre"}})
        return httpx.Response(200, json={"port": port, "document": doc})

    client = RevitClient(token_path=token, transport=httpx.MockTransport(handler),
                         discover=discover, ports=range(48884, 48888))
    return client, calls


def test_usa_48884_sin_buscar_si_responde(tmp_path):
    client, calls = make_client(tmp_path, {48884: "Snowdon"})
    assert client.post("overview")["port"] == 48884
    assert calls == [(48884, "/bim-agent/overview")]


def test_otra_sesion_sin_modelo_en_48884(tmp_path):
    client, _ = make_client(tmp_path, {48884: None, 48885: "Snowdon"})
    assert client.post("overview")["port"] == 48885
    assert client.base_url.endswith(":48885/bim-agent")


def test_48884_libre_y_revit_en_48885(tmp_path):
    client, _ = make_client(tmp_path, {48885: "Snowdon"})
    assert client.post("overview")["port"] == 48885


def test_ninguna_sesion_con_modelo_mantiene_nodocument(tmp_path):
    client, _ = make_client(tmp_path, {48884: None})
    with pytest.raises(RevitError) as exc:
        client.post("overview")
    assert exc.value.error_type == "NoDocument"


def test_sin_revit_bridge_unavailable(tmp_path):
    client, _ = make_client(tmp_path, {})
    with pytest.raises(RevitError) as exc:
        client.post("overview")
    assert exc.value.error_type == "BridgeUnavailable"


def test_url_fija_no_busca(tmp_path):
    client, calls = make_client(tmp_path, {48884: None, 48885: "Snowdon"}, discover=False)
    with pytest.raises(RevitError):
        client.post("overview")
    assert calls == [(48884, "/bim-agent/overview")]
