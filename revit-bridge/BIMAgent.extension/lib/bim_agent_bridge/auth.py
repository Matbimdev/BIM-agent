# -*- coding: utf-8 -*-
"""Token compartido entre bridge y mcp-server (ADR-006). IronPython 2.7."""
import os
import uuid

TOKEN_DIR = os.path.join(os.environ.get("APPDATA", ""), "BIMAgent")
TOKEN_PATH = os.path.join(TOKEN_DIR, "token")


def get_or_create_token():
    if not os.path.isdir(TOKEN_DIR):
        os.makedirs(TOKEN_DIR)
    if os.path.isfile(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f:
            token = f.read().strip()
        if token:
            return token
    token = uuid.uuid4().hex
    with open(TOKEN_PATH, "w") as f:
        f.write(token)
    return token


def check(request):
    """Devuelve None si el token es valido, o un dict de error."""
    data = request.data if isinstance(request.data, dict) else {}
    if data.get("token") != get_or_create_token():
        return {"error": "unauthorized",
                "hint": "Envia POST con {'token': ..., 'args': {...}}. "
                        "El token esta en %APPDATA%\\BIMAgent\\token."}
    return None
