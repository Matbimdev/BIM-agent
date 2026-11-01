# -*- coding: utf-8 -*-
"""Revit -> tipos planos. Unico punto de conversion desde pies internos. IronPython 2.7."""
FEET_TO_METERS = 0.3048


def length_m(feet):
    return {"value": feet * FEET_TO_METERS, "unit": "m"}


def unit_token(unit_type_id):
    """'autodesk.unit.unit:squareMeters-1.0.1' -> 'squareMeters'."""
    type_id = unit_type_id.TypeId
    return type_id.split(":")[-1].split("-")[0]
