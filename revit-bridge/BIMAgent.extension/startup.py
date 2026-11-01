# -*- coding: utf-8 -*-
"""Registro de rutas BIM Agent en pyRevit Routes (ADR-001, ADR-006). Solo lectura."""
from pyrevit import routes
from bim_agent_bridge import auth

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
