# -*- coding: utf-8 -*-
"""Dialogos y portapapeles que funcionan con los dos motores de pyRevit.

`pyrevit.forms` solo existe bajo IronPython: bajo CPython, que es el motor con el
que corre Revit 2027 (.NET 10), cada atributo lanza PyRevitCPythonNotSupported.
Por eso el panel usa TaskDialog de la API de Revit, que esta en ambos motores.
"""
from pyrevit import UI

TITULO = "BIM Agent"


def avisar(mensaje, detalle=None, advertencia=False):
    """Muestra un TaskDialog de un solo boton."""
    dialogo = UI.TaskDialog(TITULO)
    dialogo.MainInstruction = mensaje
    if detalle:
        dialogo.MainContent = detalle
    if advertencia:
        dialogo.MainIcon = UI.TaskDialogIcon.TaskDialogIconWarning
    dialogo.CommonButtons = UI.TaskDialogCommonButtons.Close
    dialogo.Show()


def confirmar(mensaje, detalle=None):
    """Pregunta si o no. Devuelve True solo si el usuario responde que si."""
    dialogo = UI.TaskDialog(TITULO)
    dialogo.MainInstruction = mensaje
    if detalle:
        dialogo.MainContent = detalle
    dialogo.CommonButtons = (UI.TaskDialogCommonButtons.Yes |
                             UI.TaskDialogCommonButtons.No)
    dialogo.DefaultButton = UI.TaskDialogResult.Yes
    return dialogo.Show() == UI.TaskDialogResult.Yes


def leer_portapapeles():
    """Texto del portapapeles, o cadena vacia si no se puede leer."""
    try:
        import clr
        clr.AddReference("System.Windows.Forms")
        from System.Windows.Forms import Clipboard
        if Clipboard.ContainsText():
            return Clipboard.GetText() or ""
    except Exception:
        pass
    try:
        from System.Windows import Clipboard as WpfClipboard
        if WpfClipboard.ContainsText():
            return WpfClipboard.GetText() or ""
    except Exception:
        pass
    return ""
