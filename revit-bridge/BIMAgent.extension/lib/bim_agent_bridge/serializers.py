# -*- coding: utf-8 -*-
"""Revit -> tipos planos. Unico punto de conversion desde pies internos. IronPython 2.7."""
FEET_TO_METERS = 0.3048


def length_m(feet):
    return {"value": feet * FEET_TO_METERS, "unit": "m"}


def unit_token(unit_type_id):
    """'autodesk.unit.unit:squareMeters-1.0.1' -> 'squareMeters'."""
    type_id = unit_type_id.TypeId
    return type_id.split(":")[-1].split("-")[0]


def element_ref(doc, element_id):
    """Referencia plana de un elemento, o None si ya no existe en el documento."""
    element = doc.GetElement(element_id)
    if element is None:
        return None
    level = None
    level_id = getattr(element, "LevelId", None)
    if level_id is not None:
        level_element = doc.GetElement(level_id)
        level = level_element.Name if level_element is not None else None
    try:
        name = element.Name
    except Exception:
        name = ""
    return {
        "unique_id": element.UniqueId,
        "element_id": element_id.Value,
        "name": name or "",
        "category": element.Category.Name if element.Category is not None else "",
        "level": level or "",
    }
