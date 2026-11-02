"""Resultados de la sesion para export_report. Se reinicia si cambia el documento activo."""
from datetime import datetime
from typing import Any


class Session:
    def __init__(self) -> None:
        self.document: str | None = None
        self.results: dict[str, dict[str, Any]] = {}
        self.calls: list[dict[str, Any]] = []

    def record(self, tool: str, args: dict[str, Any], raw: dict[str, Any]) -> None:
        document = raw.get("document")
        if document != self.document:
            self.document = document
            self.results = {}
            self.calls = []
        self.results[tool] = raw
        self.calls.append({"tool": tool, "args": args, "time": datetime.now().astimezone()})
