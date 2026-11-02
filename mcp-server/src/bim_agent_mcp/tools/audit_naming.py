"""Herramienta 7: nomenclatura contra un regex. Contrato en docs/02-contrato-herramientas.md."""
import re
from typing import Any

from ..revit_client import RevitError
from .common import envelope, rule_row

TARGETS = ("families", "types", "views", "sheets", "sheet_numbers", "levels")


def validate_target(target: str) -> None:
    if target not in TARGETS:
        raise RevitError("InvalidTarget", f"El target '{target}' no es valido.", f"Usa: {', '.join(TARGETS)}.")


def evaluate(raw: dict[str, Any], pattern: re.Pattern[str], category: str | None = None) -> tuple[list[dict[str, Any]], int]:
    items = raw["items"]
    if category:
        items = [item for item in items if item["category"].lower() == category.lower()]
    failing = sorted((item for item in items if not pattern.search(item["name"])), key=lambda i: i["name"])
    return failing, len(items)


def normalize(raw: dict[str, Any], target: str, pattern: re.Pattern[str], rule_text: str,
              category: str | None = None, limit: int | None = None) -> dict[str, Any]:
    failing, checked = evaluate(raw, pattern, category)
    data = [{"name": item["name"], "target": target, "category": item["category"], "unique_id": item["unique_id"],
             "element_id": int(item["element_id"])} for item in failing]
    return {**envelope(data, limit), "pattern_used": pattern.pattern, "rule_text": rule_text,
            "checked": checked, "compliant": checked - len(failing)}


def rows(raw: dict[str, Any], pattern: re.Pattern[str], rule_text: str, category: str | None = None) -> list[list[Any]]:
    failing, _ = evaluate(raw, pattern, category)
    return [rule_row("NOM", rule_text, item, item["name"], f"Cumple {pattern.pattern}") for item in failing]
