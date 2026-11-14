# -*- coding: utf-8 -*-
"""Selecciona en Revit los elementos de un hallazgo a partir de sus UniqueId.

Cierra el paso 9 del flujo de usuario y hace medible CA-03: el usuario copia los
UniqueId de una hoja del reporte y comprueba el hallazgo en el modelo.

Los UniqueId se leen del portapapeles porque pedir texto en un cuadro de dialogo
depende de pyrevit.forms, que no existe bajo CPython (Revit 2027). Copiar la
columna en Excel y pulsar el boton tambien es un paso menos para el usuario.

Solo lectura: cambiar la seleccion de la interfaz no modifica el documento y no
abre ninguna Transaction (ADR-002).
"""
from System.Collections.Generic import List

from pyrevit import DB, revit, script

from bim_agent_panel import dialogos, uniqueids

__title__ = "Seleccionar"
__doc__ = ("Copia en Excel la columna de UniqueId del reporte y pulsa este boton "
           "para seleccionar esos elementos en el modelo.")

logger = script.get_logger()

EJEMPLO = "e86e0fb0-aaef-4c8d-af36-9f1e0c4f7962-00097c98"


def _resolver(doc, ids_texto):
    encontrados, faltantes = [], []
    for uid in ids_texto:
        try:
            elemento = doc.GetElement(uid)
        except Exception as err:
            logger.debug("UniqueId invalido %s: %s", uid, err)
            elemento = None
        if elemento is None:
            faltantes.append(uid)
        else:
            encontrados.append(elemento.Id)
    return encontrados, faltantes


def _encuadrables(doc, ids):
    """Separa lo que tiene geometria en una vista de familias, tipos y vistas.

    ShowElements sobre una familia, un tipo o una vista no encuentra donde encuadrar y
    Revit muestra "No good view could be found" (CA-03, 14/11). Esos elementos quedan
    seleccionados igual y se leen en Propiedades.
    """
    con_vista, sin_vista = [], 0
    for element_id in ids:
        elemento = doc.GetElement(element_id)
        if isinstance(elemento, (DB.Family, DB.ElementType, DB.View)):
            sin_vista += 1
        else:
            con_vista.append(element_id)
    return con_vista, sin_vista


def _informe(encontrados, faltantes, sin_vista=0):
    lineas = ["Seleccionados: {}".format(len(encontrados))]
    if sin_vista:
        lineas.append("{} sin vista para encuadrar (familias, tipos o vistas): "
                      "se ven en Propiedades.".format(sin_vista))
    if faltantes:
        lineas.append("No encontrados en este modelo: {}".format(len(faltantes)))
        lineas.append("")
        lineas.extend(faltantes[:10])
        if len(faltantes) > 10:
            lineas.append("y {} mas.".format(len(faltantes) - 10))
        lineas.append("")
        lineas.append("Revisa que el reporte sea de este modelo.")
    return "\n".join(lineas)


def main():
    doc, uidoc = revit.doc, revit.uidoc
    if doc is None or uidoc is None:
        dialogos.avisar("No hay un modelo abierto en Revit.",
                        "Abre el .rvt y repite la operacion.", advertencia=True)
        return
    if doc.IsFamilyDocument:
        dialogos.avisar("El documento activo es una familia, no un proyecto.",
                        "Activa la ventana del .rvt y repite la operacion.",
                        advertencia=True)
        return

    pegado, descartados = uniqueids.separar(dialogos.leer_portapapeles())
    if not pegado:
        dialogos.avisar(
            "El portapapeles no tiene ningun UniqueId.",
            "Copia en Excel la columna UniqueId de una hoja del reporte y vuelve a "
            "pulsar el boton.\n\nUn UniqueId se ve asi:\n" + EJEMPLO,
            advertencia=True)
        return

    detalle = "Se tomaron del portapapeles."
    if descartados:
        detalle += " Se ignoraron {} textos que no son UniqueId.".format(len(descartados))
    if not dialogos.confirmar("Seleccionar {} elementos?".format(len(pegado)), detalle):
        return

    encontrados, faltantes = _resolver(doc, pegado)
    if not encontrados:
        dialogos.avisar(
            "Ninguno de los {} UniqueId existe en {}.".format(len(pegado), doc.Title),
            "Revisa que el reporte corresponda a este modelo.", advertencia=True)
        return

    uidoc.Selection.SetElementIds(List[DB.ElementId](encontrados))
    con_vista, sin_vista = _encuadrables(doc, encontrados)
    if con_vista:
        try:
            uidoc.ShowElements(List[DB.ElementId](con_vista))
        except Exception as err:
            logger.debug("No se pudo encuadrar la vista: %s", err)

    dialogos.avisar("Hallazgo seleccionado en el modelo.",
                    _informe(encontrados, faltantes, sin_vista),
                    advertencia=bool(faltantes))


main()
