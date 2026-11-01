# -*- coding: utf-8 -*-
"""Envoltura comun de los endpoints: token, documento activo y errores. IronPython 2.7."""
from pyrevit import routes

from bim_agent_bridge import auth, errors


def _active_document(uiapp):
    uidoc = uiapp.ActiveUIDocument
    if uidoc is None:
        raise errors.NoDocument("No hay un modelo abierto en Revit.",
                                "Abre el modelo .rvt y repite la consulta.")
    if uidoc.Document.IsFamilyDocument:
        raise errors.NoDocument("El documento activo es una familia, no un proyecto.",
                                "Activa la ventana del modelo .rvt y repite la consulta.")
    return uidoc.Document


def handle(request, uiapp, handler):
    """Ejecuta handler(doc, version, args) y responde siempre JSON, nunca un stack trace."""
    auth_error = auth.check(request)
    if auth_error:
        return routes.make_response(data=auth_error, status=401)
    try:
        doc = _active_document(uiapp)
        args = request.data.get("args") or {}
        return routes.make_response(
            data=handler(doc, uiapp.Application.VersionNumber, args))
    except errors.BridgeError as err:
        return routes.make_response(data=err.to_dict(), status=err.status)
    except Exception as err:
        internal = errors.BridgeError(
            "El bridge no pudo leer el modelo: {}".format(err),
            "Revisa que Revit no tenga un dialogo abierto y repite la consulta.")
        return routes.make_response(data=internal.to_dict(), status=internal.status)
