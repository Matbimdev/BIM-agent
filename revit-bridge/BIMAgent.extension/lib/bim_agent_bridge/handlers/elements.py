# -*- coding: utf-8 -*-
"""Elementos de una categoria con parametros pedidos. Solo lectura. IronPython 2.7."""
from Autodesk.Revit.DB import BuiltInParameter, ElementId, FilteredElementCollector, StorageType

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
    return {"found": True, "source": source, "has_value": parameter.HasValue, "value": value,
            "quantity": serializers.magnitude(parameter)}


def _lookup(doc, element, name):
    parameter = element.LookupParameter(name)
    if parameter is not None:
        return _read(parameter, "instance")
    element_type = doc.GetElement(element.GetTypeId())
    if element_type is not None:
        parameter = element_type.LookupParameter(name)
        if parameter is not None:
            return _read(parameter, "type")
    return {"found": False, "source": "", "has_value": False, "value": None, "quantity": None}


def _type_names(doc, element):
    element_type = doc.GetElement(element.GetTypeId())
    if element_type is None:
        return "", ""
    return getattr(element_type, "FamilyName", "") or "", serializers.element_name(element_type)


def _collect(doc, category):
    return (FilteredElementCollector(doc)
            .OfCategoryId(category.Id)
            .WhereElementIsNotElementType())


def _available_parameters(doc, element):
    names = set(p.Definition.Name for p in element.Parameters)
    element_type = doc.GetElement(element.GetTypeId())
    if element_type is not None:
        names.update(p.Definition.Name for p in element_type.Parameters)
    return sorted(names)


def run(doc, version, args):
    category = _find_category(doc, args["category"])
    fields = args.get("fields") or []
    elements = []
    available = []
    for element in _collect(doc, category):
        if not available:
            available = _available_parameters(doc, element)
        ref = serializers.element_ref(doc, element.Id)
        ref["family"], ref["type"] = _type_names(doc, element)
        ref["params"] = dict((field, _lookup(doc, element, field)) for field in fields)
        elements.append(ref)
    return {"elements": elements, "available_params": available}


def _first_magnitude(element, built_ins):
    for built_in in built_ins:
        parameter = element.get_Parameter(built_in)
        if parameter is not None:
            value = serializers.magnitude(parameter)
            if value is not None:
                return value
    return None


def _phase_name(doc, element):
    phase_id = element.CreatedPhaseId
    if phase_id == ElementId.InvalidElementId:
        return ""
    phase = doc.GetElement(phase_id)
    return phase.Name if phase is not None else ""


def quantities(doc, version, args):
    category = _find_category(doc, args["category"])
    elements = []
    for element in _collect(doc, category):
        elements.append({
            "type": _type_names(doc, element)[1],
            "level": serializers.level_name(doc, element),
            "phase": _phase_name(doc, element),
            "length": _first_magnitude(element, (BuiltInParameter.INSTANCE_LENGTH_PARAM,
                                                 BuiltInParameter.CURVE_ELEM_LENGTH)),
            "area": _first_magnitude(element, (BuiltInParameter.HOST_AREA_COMPUTED,)),
            "volume": _first_magnitude(element, (BuiltInParameter.HOST_VOLUME_COMPUTED,)),
        })
    return {"category": category.Name, "built_in": str(category.BuiltInCategory), "elements": elements}
