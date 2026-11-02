# -*- coding: utf-8 -*-
"""Nombres crudos para audit_naming; el regex se evalua en mcp-server. IronPython 2.7."""
from bim_agent_bridge import serializers
from Autodesk.Revit.DB import (
    Family,
    FilteredElementCollector,
    Level,
    View,
    ViewSheet,
)

SYSTEM_VIEW_TYPES = ("Undefined", "ProjectBrowser", "SystemBrowser", "Internal", "DrawingSheet")


def _item(element, name, category=""):
    return {"name": name, "category": category,
            "unique_id": element.UniqueId, "element_id": element.Id.Value}


def _category_name(element):
    return element.Category.Name if element.Category is not None else ""


def _families(doc):
    for family in FilteredElementCollector(doc).OfClass(Family):
        category = family.FamilyCategory
        yield _item(family, family.Name, category.Name if category is not None else "")


def _types(doc):
    for element in FilteredElementCollector(doc).WhereElementIsElementType():
        if element.Category is not None:
            yield _item(element, serializers.element_name(element), element.Category.Name)


def _views(doc):
    for view in FilteredElementCollector(doc).OfClass(View):
        if view.IsTemplate or isinstance(view, ViewSheet) or str(view.ViewType) in SYSTEM_VIEW_TYPES:
            continue
        if view.Name.startswith("{"):
            continue
        yield _item(view, view.Name, str(view.ViewType))


def _sheets(doc):
    for sheet in FilteredElementCollector(doc).OfClass(ViewSheet):
        yield _item(sheet, sheet.Name)


def _sheet_numbers(doc):
    for sheet in FilteredElementCollector(doc).OfClass(ViewSheet):
        yield _item(sheet, sheet.SheetNumber)


def _levels(doc):
    for level in FilteredElementCollector(doc).OfClass(Level):
        yield _item(level, level.Name)


TARGETS = {"families": _families, "types": _types, "views": _views, "sheets": _sheets,
           "sheet_numbers": _sheet_numbers, "levels": _levels}


def run(doc, version, args):
    return {"items": list(TARGETS[args["target"]](doc))}
