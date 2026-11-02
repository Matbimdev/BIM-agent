"""Herramienta 8: parametros obligatorios y validos. Contrato en docs/02-contrato-herramientas.md."""
from typing import Any

from .common import compile_regex, envelope, rule_row


def fields(required: list[str], rules: list[dict[str, Any]]) -> list[str]:
    return list(dict.fromkeys([*required, *(rule["param"] for rule in rules)]))


def _invalid(value: str, rule: dict[str, Any]) -> tuple[bool, str]:
    if "allowed" in rule and value not in rule["allowed"]:
        return True, "Uno de: " + ", ".join(rule["allowed"])
    if "regex" in rule and not compile_regex(rule["regex"]).search(value):
        return True, f"Cumple {rule['regex']}"
    return False, ""


def evaluate(raw: dict[str, Any], required: list[str], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_param = {rule["param"]: rule for rule in rules}
    issues = []
    for element in raw["elements"]:
        for param in fields(required, rules):
            state = element["params"][param]
            value = (state.get("value") or "").strip() if state["found"] else ""
            issue, expected = None, "Con valor"
            if not state["found"]:
                if param in required:
                    issue, expected = "missing", "Parametro presente"
            elif not state["has_value"] or not value:
                if param in required:
                    issue = "empty"
            elif param in by_param:
                invalid, expected = _invalid(value, by_param[param])
                issue = "invalid" if invalid else None
            if issue:
                issues.append({"element": element, "param": param, "issue": issue,
                               "value": value or None, "expected": expected})
    return issues


def normalize(raw: dict[str, Any], required: list[str], rules: list[dict[str, Any]],
              limit: int | None = None) -> dict[str, Any]:
    issues = evaluate(raw, required, rules)
    summary = [{"param": param,
                **{kind: sum(1 for i in issues if i["param"] == param and i["issue"] == kind)
                   for kind in ("missing", "empty", "invalid")}}
               for param in fields(required, rules)]
    data = [{"unique_id": i["element"]["unique_id"], "element_id": int(i["element"]["element_id"]),
             "name": i["element"]["name"], "level": i["element"]["level"], "param": i["param"],
             "issue": i["issue"], "value": i["value"]} for i in issues]
    return {**envelope(data, limit), "checked": len(raw["elements"]), "summary": summary}


def rows(raw: dict[str, Any], category: str, required: list[str], rules: list[dict[str, Any]]) -> list[list[Any]]:
    return [rule_row("PAR", f"{category}: {i['param']}", i["element"], i["value"] or i["issue"], i["expected"])
            for i in evaluate(raw, required, rules)]
