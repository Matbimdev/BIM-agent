# -*- coding: utf-8 -*-
"""Registro de rutas BIM Agent en pyRevit Routes (ADR-001, ADR-006). Solo lectura."""
from pyrevit import routes
from bim_agent_bridge import auth
from bim_agent_bridge import routes as bridge_routes
from bim_agent_bridge.handlers import elements, families, names, overview, sheets_views, warnings

api = routes.API("bim-agent")
auth.get_or_create_token()


@api.route("/health", methods=["POST"])
def health(request, uiapp):
    err = auth.check(request)
    if err:
        return routes.make_response(data=err, status=401)
    doc = uiapp.ActiveUIDocument.Document if uiapp.ActiveUIDocument else None
    return routes.make_response(data={
        "status": "ok",
        "revit_version": uiapp.Application.VersionNumber,
        "document": doc.Title if doc else None,
    })


@api.route("/overview", methods=["POST"])
def overview_route(request, uiapp):
    return bridge_routes.handle(request, uiapp, overview.run)


@api.route("/warnings", methods=["POST"])
def warnings_route(request, uiapp):
    return bridge_routes.handle(request, uiapp, warnings.run)


@api.route("/sheets_views", methods=["POST"])
def sheets_views_route(request, uiapp):
    return bridge_routes.handle(request, uiapp, sheets_views.run)


@api.route("/families", methods=["POST"])
def families_route(request, uiapp):
    return bridge_routes.handle(request, uiapp, families.run)


@api.route("/names", methods=["POST"])
def names_route(request, uiapp):
    return bridge_routes.handle(request, uiapp, names.run)


@api.route("/elements", methods=["POST"])
def elements_route(request, uiapp):
    return bridge_routes.handle(request, uiapp, elements.run)
