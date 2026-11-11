# -*- coding: utf-8 -*-
"""Alterna el servidor pyRevit Routes que publica el bridge. Solo lectura, sin Transaction."""
from pyrevit import routes, script

from bim_agent_panel import dialogos

__title__ = "Iniciar/Detener"
__doc__ = ("Inicia o detiene el bridge de BIM Agent en esta sesion de Revit.\n"
           "Si ya esta activo, lo detiene. Si no, lo inicia y muestra el puerto.")

logger = script.get_logger()


def _direccion(server):
    return "http://{}:{}".format(server.host or "localhost", server.port)


def main():
    server = routes.get_active_server()
    if server and server.is_running:
        direccion = _direccion(server)
        routes.deactivate_server()
        dialogos.avisar(
            "Bridge detenido.",
            "Estaba escuchando en {}.\n"
            "El agente no puede leer este modelo hasta que lo inicies de nuevo."
            .format(direccion))
        return

    try:
        server = routes.activate_server()
    except Exception as err:
        logger.debug("Fallo al activar Routes: %s", err)
        server = None

    if not server:
        dialogos.avisar(
            "No se pudo iniciar el bridge.",
            "Revisa que Routes este habilitado en pyRevit Settings, seccion Routes, "
            "y vuelve a cargar pyRevit.",
            advertencia=True)
        return

    dialogos.avisar(
        "Bridge activo en {}.".format(_direccion(server)),
        "Si tienes mas de una version de Revit abierta, cada una toma un puerto "
        "distinto. El servidor MCP busca del 48884 al 48890, asi que no hace falta "
        "configurar nada.")


main()
