# -*- coding: utf-8 -*-
"""Lectura de UniqueId pegados desde el reporte. Sin dependencias de Revit.

Vive aparte del boton para poder probarse sin Revit, que es la regla del
proyecto: los errores de este tipo no los detecta ningun test si la logica
esta dentro del script de un pushbutton.
"""
import re

SEPARADORES = re.compile(r"[\s,;]+")
# Un UniqueId de Revit es un GUID, un guion y ocho digitos hexadecimales:
# e86e0fb0-aaef-4c8d-af36-9f1e0c4f7962-00097c98
UNIQUEID = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"
                      r"-[0-9a-fA-F]{8}$")


def es_uniqueid(texto):
    return bool(UNIQUEID.match(texto or ""))


def separar(texto):
    """Devuelve (uniqueids, descartados) a partir de un texto pegado.

    Acepta lo que sale de copiar una columna de Excel: saltos de linea, comas,
    puntos y coma o espacios. Conserva el orden, quita repetidos y aparta todo
    lo que no sea un UniqueId, como el encabezado de la columna.
    """
    if not texto or not texto.strip():
        return [], []
    uniqueids, descartados = [], []
    for parte in SEPARADORES.split(texto.strip()):
        parte = parte.strip()
        if not parte:
            continue
        if es_uniqueid(parte):
            if parte not in uniqueids:
                uniqueids.append(parte)
        elif parte not in descartados:
            descartados.append(parte)
    return uniqueids, descartados
