"""Pruebas sin Revit del parseo de UniqueId que usa el boton Seleccionar del panel.

El modulo vive en el bridge (IronPython 2.7 y CPython), asi que se carga por
ruta en lugar de importarse como paquete instalado.
"""
import importlib.util
from pathlib import Path

import pytest

RUTA = (Path(__file__).parents[2] / "revit-bridge" / "BIMAgent.extension" /
        "lib" / "bim_agent_panel" / "uniqueids.py")

_spec = importlib.util.spec_from_file_location("bim_agent_panel_uniqueids", RUTA)
uniqueids = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(uniqueids)

UID_1 = "e86e0fb0-aaef-4c8d-af36-9f1e0c4f7962-00097c98"
UID_2 = "bdb1b609-ac6e-4ba6-b32d-4a65ac0ef4ab-000a269e"


@pytest.mark.parametrize("texto", [UID_1, UID_2, UID_1.upper()])
def test_reconoce_uniqueids_reales_de_snowdon(texto):
    assert uniqueids.es_uniqueid(texto)


@pytest.mark.parametrize("texto", [
    "",
    "UniqueId",
    "621720",                                      # ElementId, no UniqueId
    "e86e0fb0-aaef-4c8d-af36-9f1e0c4f7962",        # GUID sin el sufijo
    "e86e0fb0-aaef-4c8d-af36-9f1e0c4f7962-00097c9",   # sufijo corto
    "e86e0fb0-aaef-4c8d-af36-9f1e0c4f7962-00097c9z",  # sufijo no hexadecimal
])
def test_rechaza_lo_que_no_es_uniqueid(texto):
    assert not uniqueids.es_uniqueid(texto)


def test_separa_una_columna_copiada_de_excel():
    pegado, descartados = uniqueids.separar(
        "UniqueId\r\n{}\r\n{}\r\n".format(UID_1, UID_2))
    assert pegado == [UID_1, UID_2]
    assert descartados == ["UniqueId"]


@pytest.mark.parametrize("separador", ["\n", ", ", "; ", " ", "\t"])
def test_acepta_los_separadores_habituales(separador):
    pegado, _ = uniqueids.separar(separador.join([UID_1, UID_2]))
    assert pegado == [UID_1, UID_2]


def test_quita_repetidos_y_conserva_el_orden():
    pegado, _ = uniqueids.separar("\n".join([UID_2, UID_1, UID_2]))
    assert pegado == [UID_2, UID_1]


@pytest.mark.parametrize("texto", ["", "   \n\t  ", None])
def test_texto_vacio_no_devuelve_nada(texto):
    assert uniqueids.separar(texto) == ([], [])
