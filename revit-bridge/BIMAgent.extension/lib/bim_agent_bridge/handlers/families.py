# -*- coding: utf-8 -*-
"""Extraccion cruda para audit_families. Solo lectura. IronPython 2.7."""
from Autodesk.Revit.DB import Family, FilteredElementCollector


def run(doc, version, args):
    families = list(FilteredElementCollector(doc).OfClass(Family))
    family_by_type = {}
    for family in families:
        for type_id in family.GetFamilySymbolIds():
            family_by_type[type_id.Value] = family.Id.Value

    # Por GetTypeId, no por FamilyInstance: las etiquetas tambien usan tipos de familia.
    instances = {}
    for element in FilteredElementCollector(doc).WhereElementIsNotElementType():
        family_id = family_by_type.get(element.GetTypeId().Value)
        if family_id is not None:
            instances[family_id] = instances.get(family_id, 0) + 1

    data = []
    for family in families:
        category = family.FamilyCategory
        data.append({
            "family": family.Name,
            "category": category.Name if category is not None else "",
            "built_in": str(category.BuiltInCategory) if category is not None else "",
            "in_place": family.IsInPlace,
            "types": family.GetFamilySymbolIds().Count,
            "instances": instances.get(family.Id.Value, 0),
            "unique_id": family.UniqueId,
            "element_id": family.Id.Value,
        })
    return {"families": data}
