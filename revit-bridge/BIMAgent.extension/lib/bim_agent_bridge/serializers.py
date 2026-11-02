# -*- coding: utf-8 -*-
"""Revit -> tipos planos. Unico punto de conversion desde pies internos. IronPython 2.7."""
from Autodesk.Revit.DB import BuiltInParameter, Element, ElementId

FEET_TO_METERS = 0.3048
_MAGNITUDES = {"length": (FEET_TO_METERS, "m"),
               "area": (FEET_TO_METERS ** 2, "m2"),
               "volume": (FEET_TO_METERS ** 3, "m3")}
_LEVEL_PARAMETERS = (BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM,
                     BuiltInParameter.FAMILY_BASE_LEVEL_PARAM,
                     BuiltInParameter.WALL_BASE_CONSTRAINT)


def length_m(feet):
    return {"value": feet * FEET_TO_METERS, "unit": "m"}


def unit_token(unit_type_id):
    """'autodesk.unit.unit:squareMeters-1.0.1' -> 'squareMeters'."""
    type_id = unit_type_id.TypeId
    return type_id.split(":")[-1].split("-")[0]


def element_name(element):
    """IronPython no resuelve .Name en tipos como FamilySymbol; se lee desde Element."""
    try:
        return Element.Name.GetValue(element) or ""
    except Exception:
        return ""


def magnitude(parameter):
    """Longitud, area o volumen en SI; None para cualquier otro tipo de dato."""
    token = parameter.Definition.GetDataType().TypeId.split(":")[-1].split("-")[0]
    if token not in _MAGNITUDES or not parameter.HasValue:
        return None
    factor, unit = _MAGNITUDES[token]
    return {"value": parameter.AsDouble() * factor, "unit": unit}


def level_name(doc, element):
    level_id = getattr(element, "LevelId", None)
    if level_id is not None and level_id != ElementId.InvalidElementId:
        level = doc.GetElement(level_id)
        if level is not None:
            return level.Name
    for built_in in _LEVEL_PARAMETERS:
        parameter = element.get_Parameter(built_in)
        if parameter is not None and parameter.HasValue:
            level = doc.GetElement(parameter.AsElementId())
            if level is not None:
                return level.Name
    return ""


def element_ref(doc, element_id):
    """Referencia plana de un elemento, o None si ya no existe en el documento."""
    element = doc.GetElement(element_id)
    if element is None:
        return None
    return {
        "unique_id": element.UniqueId,
        "element_id": element_id.Value,
        "name": element_name(element),
        "category": element.Category.Name if element.Category is not None else "",
        "level": level_name(doc, element),
    }
