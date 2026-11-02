# -*- coding: utf-8 -*-
"""Extraccion cruda para get_sheets_and_views. Solo lectura. IronPython 2.7."""
from Autodesk.Revit.DB import (
    ElementId,
    FilteredElementCollector,
    ScheduleSheetInstance,
    View,
    ViewSheet,
)

SYSTEM_VIEW_TYPES = ("Undefined", "ProjectBrowser", "SystemBrowser", "Internal", "DrawingSheet")


def _current_revision(doc, sheet):
    revision_id = sheet.GetCurrentRevision()
    if revision_id == ElementId.InvalidElementId:
        return ""
    return sheet.GetRevisionNumberOnSheet(revision_id) or ""


def run(doc, version, args):
    placed = set()
    sheets = []
    for sheet in FilteredElementCollector(doc).OfClass(ViewSheet):
        view_ids = list(sheet.GetAllPlacedViews())
        placed.update(view_id.Value for view_id in view_ids)
        sheets.append({
            "number": sheet.SheetNumber,
            "name": sheet.Name,
            "views_placed": len(view_ids),
            "current_revision": _current_revision(doc, sheet),
            "is_placeholder": sheet.IsPlaceholder,
            "unique_id": sheet.UniqueId,
            "element_id": sheet.Id.Value,
        })
    for instance in FilteredElementCollector(doc).OfClass(ScheduleSheetInstance):
        placed.add(instance.ScheduleId.Value)

    views = []
    for view in FilteredElementCollector(doc).OfClass(View):
        view_type = str(view.ViewType)
        if view.IsTemplate or view_type in SYSTEM_VIEW_TYPES or isinstance(view, ViewSheet):
            continue
        views.append({
            "name": view.Name,
            "view_type": view_type,
            "placed": view.Id.Value in placed,
            "unique_id": view.UniqueId,
            "element_id": view.Id.Value,
        })
    return {"sheets": sheets, "views": views}
