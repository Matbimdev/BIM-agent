# -*- coding: utf-8 -*-
"""Extraccion cruda para audit_links_coordinates. Solo lectura. IronPython 2.7."""
import math

from Autodesk.Revit.DB import (
    BasePoint,
    BuiltInParameter,
    FilteredElementCollector,
    ImportInstance,
    LinkedFileStatus,
    ModelPathUtils,
    RevitLinkInstance,
    RevitLinkType,
)

from bim_agent_bridge import serializers


def _number(point, built_in):
    parameter = point.get_Parameter(built_in)
    return parameter.AsDouble() if parameter is not None and parameter.HasValue else 0.0


def _point(point, with_angle):
    position = point.Position
    result = {
        "ns": serializers.length_m(_number(point, BuiltInParameter.BASEPOINT_NORTHSOUTH_PARAM)),
        "ew": serializers.length_m(_number(point, BuiltInParameter.BASEPOINT_EASTWEST_PARAM)),
        "elevation": serializers.length_m(_number(point, BuiltInParameter.BASEPOINT_ELEVATION_PARAM)),
        "distance_from_origin": serializers.length_m(
            math.sqrt(position.X ** 2 + position.Y ** 2 + position.Z ** 2)),
    }
    if with_angle:
        result["angle_to_true_north"] = {
            "value": math.degrees(_number(point, BuiltInParameter.BASEPOINT_ANGLETON_PARAM)),
            "unit": "deg",
        }
    return result


def _link_path(link_type):
    if not link_type.IsExternalFileReference():
        return ""
    reference = link_type.GetExternalFileReference()
    return ModelPathUtils.ConvertModelPathToUserVisiblePath(reference.GetPath())


def _links(doc):
    instances = {}
    for instance in FilteredElementCollector(doc).OfClass(RevitLinkInstance):
        instances.setdefault(instance.GetTypeId().Value, []).append(instance)
    links = []
    for link_type in FilteredElementCollector(doc).OfClass(RevitLinkType):
        if link_type.IsNestedLink:
            continue
        placed = instances.get(link_type.Id.Value, [])
        status = link_type.GetLinkedFileStatus()
        links.append({
            "name": serializers.element_name(link_type),
            "kind": "ifc" if ".ifc" in _link_path(link_type).lower() else "rvt",
            "loaded": status == LinkedFileStatus.Loaded,
            "path_found": status != LinkedFileStatus.NotFound,
            "status": str(status),
            "instances": len(placed),
            "pinned": bool(placed) and all(instance.Pinned for instance in placed),
            "unpinned_instances": [{"unique_id": instance.UniqueId, "element_id": instance.Id.Value}
                                   for instance in placed if not instance.Pinned],
            "unique_id": link_type.UniqueId,
            "element_id": link_type.Id.Value,
        })
    return links


def _cad(doc):
    items = []
    for instance in FilteredElementCollector(doc).OfClass(ImportInstance):
        category = instance.Category
        items.append({
            "name": category.Name if category is not None else "",
            "linked": instance.IsLinked,
            "pinned": instance.Pinned,
            "unique_id": instance.UniqueId,
            "element_id": instance.Id.Value,
        })
    return items


def run(doc, version, args):
    base_point = None
    survey_point = None
    for point in FilteredElementCollector(doc).OfClass(BasePoint):
        if point.IsShared:
            survey_point = _point(point, False)
        else:
            base_point = _point(point, True)
    return {"base_point": base_point, "survey_point": survey_point,
            "links": _links(doc), "cad": _cad(doc)}
