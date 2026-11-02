# -*- coding: utf-8 -*-
"""Elementos de una categoria con parametros pedidos. Solo lectura. IronPython 2.7."""
from Autodesk.Revit.DB import FilteredElementCollector, StorageType

from bim_agent_bridge import errors, serializers


def _find_category(doc, name):
    available = []
    for category in doc.Settings.Categories:
        if category.Name.lower() == name.lower():
            return category
        available.append(category.Name)
    raise errors.CategoryNotFound(
        "La categoria '{}' no existe en este modelo.".format(name),
        "Usa el nombre tal como aparece en Revit o en get_model_overview.")


def _read(parameter, source):
    if parameter.StorageType == StorageType.String:
        value = parameter.AsString()
    else:
        value = parameter.AsValueString()
    return {"found": True, "source": source, "has_value": parameter.HasValue, "value": value}


def _lookup(doc, element, name):
    parameter = element.LookupParameter(name)
    if parameter is not None:
        return _read(parameter, "instance")
    element_type = doc.GetElement(element.GetTypeId())
    if element_type is not None:
        parameter = element_type.LookupParameter(name)
        if parameter is not None:
            return _read(parameter, "type")
    return {"found": False, "source": "", "has_value": False, "value": None}


def run(doc, version, args):
    category = _find_category(doc, args["category"])
    fields = args.get("fields") or []
    elements = []
    collector = (FilteredElementCollector(doc)
                 .OfCategoryId(category.Id)
                 .WhereElementIsNotElementType())
    for element in collector:
        ref = serializers.element_ref(doc, element.Id)
        ref["params"] = dict((field, _lookup(doc, element, field)) for field in fields)
        elements.append(ref)
    return {"elements": elements}
