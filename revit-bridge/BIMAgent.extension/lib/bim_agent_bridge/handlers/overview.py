# -*- coding: utf-8 -*-
"""Extraccion cruda para get_model_overview. Solo lectura. IronPython 2.7."""
from Autodesk.Revit.DB import (
    CategoryType,
    FilteredElementCollector,
    FilteredWorksetCollector,
    ImportInstance,
    Level,
    ModelPathUtils,
    RevitLinkType,
    SpecTypeId,
    WorksetKind,
)

from bim_agent_bridge import serializers


def _project(doc, version):
    info = doc.ProjectInformation
    units = doc.GetUnits()

    def unit_of(spec):
        return serializers.unit_token(units.GetFormatOptions(spec).GetUnitTypeId())

    central_path = ""
    if doc.IsWorkshared:
        central = doc.GetWorksharingCentralModelPath()
        if central is not None:
            central_path = ModelPathUtils.ConvertModelPathToUserVisiblePath(central)

    return {
        "name": info.Name or doc.Title,
        "number": info.Number or "",
        "client": info.ClientName or "",
        "address": info.Address or "",
        "revit_version": version,
        "units": {
            "length": unit_of(SpecTypeId.Length),
            "area": unit_of(SpecTypeId.Area),
            "volume": unit_of(SpecTypeId.Volume),
        },
        "worksharing": doc.IsWorkshared,
        "central_path": central_path,
    }


def _category_counts(doc):
    counts = {}
    collector = (FilteredElementCollector(doc)
                 .WhereElementIsNotElementType()
                 .WhereElementIsViewIndependent())
    for element in collector:
        category = element.Category
        if category is None or category.CategoryType != CategoryType.Model:
            continue
        key = (category.Name, str(category.BuiltInCategory))
        counts[key] = counts.get(key, 0) + 1
    return [{"category": key[0], "built_in": key[1], "count": count}
            for key, count in counts.items()]


def _levels(doc):
    return [{"name": level.Name, "elevation": serializers.length_m(level.Elevation)}
            for level in FilteredElementCollector(doc).OfClass(Level)]


def _worksets(doc):
    if not doc.IsWorkshared:
        return []
    return [workset.Name for workset in
            FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset)]


def _is_ifc_link(link_type):
    if not link_type.IsExternalFileReference():
        return False
    reference = link_type.GetExternalFileReference()
    path = ModelPathUtils.ConvertModelPathToUserVisiblePath(reference.GetPath())
    return ".ifc" in path.lower()


def _links(doc):
    links = {"rvt": 0, "ifc": 0, "cad_linked": 0, "cad_imported": 0}
    for link_type in FilteredElementCollector(doc).OfClass(RevitLinkType):
        links["ifc" if _is_ifc_link(link_type) else "rvt"] += 1
    for instance in FilteredElementCollector(doc).OfClass(ImportInstance):
        links["cad_linked" if instance.IsLinked else "cad_imported"] += 1
    return links


def run(doc, version, args):
    result = {
        "project": _project(doc, version),
        "categories": _category_counts(doc),
        "levels": _levels(doc),
        "phases": [phase.Name for phase in doc.Phases],
        "worksets": _worksets(doc),
    }
    if args.get("include_links", True):
        result["links"] = _links(doc)
    return result
