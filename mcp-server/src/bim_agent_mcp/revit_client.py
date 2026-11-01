"""Unico punto que habla HTTP con el bridge (ADR-006)."""
from pathlib import Path
from typing import Any

import httpx

from . import config


class RevitError(Exception):
    """Error tipado con el mensaje y la accion que ve el agente."""

    def __init__(self, error_type: str, message: str, action: str):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.action = action

    def to_dict(self) -> dict[str, Any]:
        return {"error": {"type": self.error_type, "message": self.message, "action": self.action}}


def _unavailable() -> RevitError:
    return RevitError(
        "BridgeUnavailable",
        "No se pudo conectar con Revit.",
        "Abre Revit con la extension BIMAgent cargada y el servidor de Routes de pyRevit activo.",
    )


class RevitClient:
    def __init__(
        self,
        base_url: str = config.BRIDGE_URL,
        token_path: Path = config.TOKEN_PATH,
        timeout: float = config.TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._token_path = token_path
        self._timeout = timeout
        self._transport = transport

    def _token(self) -> str:
        try:
            return self._token_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise _unavailable() from exc

    def post(self, endpoint: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        body = {"token": self._token(), "args": args or {}}
        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                response = client.post(f"{self._base_url}/{endpoint}", json=body)
        except httpx.TimeoutException as exc:
            raise RevitError(
                "Timeout",
                "Revit no respondio a tiempo.",
                "Revisa que Revit no tenga un dialogo abierto o un comando en curso y repite la consulta.",
            ) from exc
        except httpx.TransportError as exc:
            raise _unavailable() from exc

        if response.status_code == 401:
            raise RevitError(
                "Unauthorized",
                "El bridge rechazo el token.",
                "Recarga pyRevit para sincronizar el token en %APPDATA%\\BIMAgent\\token.",
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise _unavailable() from exc
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, dict):
            raise RevitError(
                error.get("type", "InternalError"),
                error.get("message", "Error desconocido en el bridge."),
                error.get("action", "Repite la consulta."),
            )
        if response.status_code != 200 or not isinstance(payload, dict):
            raise _unavailable()
        return payload
