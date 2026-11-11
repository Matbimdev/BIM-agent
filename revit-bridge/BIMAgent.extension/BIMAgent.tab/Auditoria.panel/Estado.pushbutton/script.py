# -*- coding: utf-8 -*-
"""Estado del bridge, del modelo activo y de la version de Revit. Solo lectura.

No llama a /health por HTTP a proposito: pyRevit Routes despacha cada peticion al
hilo principal de Revit, de modo que una llamada a si mismo desde un boton
bloquearia ese hilo esperando su propia respuesta. El estado se lee en memoria.
"""
import os

from pyrevit import HOST_APP, revit, routes, script

from bim_agent_panel import dialogos

__title__ = "Estado"
__doc__ = ("Muestra si el bridge esta activo y en que puerto, el modelo abierto "
           "y la version de Revit.")

logger = script.get_logger()

TOKEN_PATH = os.path.join(os.environ.get("APPDATA", ""), "BIMAgent", "token")


def _estado_servidor():
    server = routes.get_active_server()
    if not server:
        return "Bridge detenido", ["Inicialo con el boton Iniciar/Detener de este panel."]
    if not server.is_running:
        return ("Bridge registrado pero sin aceptar conexiones",
                ["Puerto: {}".format(server.port),
                 "Detenlo y vuelve a iniciarlo con Iniciar/Detener."])
    lineas = ["Direccion: http://{}:{}".format(server.host or "localhost", server.port)]
    try:
        rutas = routes.get_routes("bim-agent") or {}
        lineas.append("Rutas publicadas: {}".format(len(rutas)))
    except Exception as err:
        logger.debug("No se pudieron contar las rutas: %s", err)
    return "Bridge activo", lineas


def _linea_modelo():
    doc = revit.doc
    if doc is None:
        return "Modelo: ninguno abierto. Abre el .rvt antes de pedir una auditoria."
    if doc.IsFamilyDocument:
        return ("Modelo: el documento activo es una familia, no un proyecto. "
                "Activa la ventana del .rvt.")
    return "Modelo: {}".format(doc.Title)


def main():
    titulo, detalle = _estado_servidor()
    lineas = ["Revit: {}".format(HOST_APP.version), _linea_modelo(), ""]
    lineas.extend(detalle)
    lineas.append("")
    lineas.append("Token: {}".format(
        "presente" if os.path.isfile(TOKEN_PATH)
        else "no encontrado en la carpeta BIMAgent de APPDATA"))
    dialogos.avisar(titulo, "\n".join(lineas))


main()
