# -*- coding: utf-8 -*-
"""Genera los iconos del panel BIMAgent y los escribe en cada pushbutton.

Se guardan como PNG en el repositorio, pero este script queda para poder
rehacerlos sin un editor de imagenes. Naranjas y amarillos, fondo transparente.
Los colores se eligieron para que el icono se lea a 32 px, que es el tamano al
que Revit los dibuja en la cinta.

    uv run --with pillow python scripts/generar_iconos.py
"""
import os

from PIL import Image, ImageDraw

LADO = 96
ESCALA = 8          # se dibuja grande y se reduce: antialias barato y parejo
L = LADO * ESCALA

AMBAR = (179, 83, 9, 255)        # naranja oscuro, para contorno y contraste
NARANJA = (240, 120, 24, 255)    # naranja principal
AMARILLO = (255, 199, 44, 255)   # amarillo de acento

AQUI = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.join(AQUI, os.pardir, "revit-bridge", "BIMAgent.extension",
                     "BIMAgent.tab", "Auditoria.panel")


def lienzo():
    img = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def caja(margen):
    return [margen * ESCALA, margen * ESCALA,
            (LADO - margen) * ESCALA, (LADO - margen) * ESCALA]


def iniciar_detener():
    """Simbolo de encendido: anillo abierto arriba y barra vertical."""
    img, d = lienzo()
    grosor = 11 * ESCALA
    d.arc(caja(16), start=-60, end=240, fill=NARANJA, width=grosor)
    x = L // 2
    d.line([(x, 14 * ESCALA), (x, 46 * ESCALA)], fill=AMARILLO, width=grosor)
    return img


def estado():
    """Punto central y un arco a cada lado: el bridge emitiendo."""
    img, d = lienzo()
    centro, radio = L // 2, 13 * ESCALA
    d.ellipse([centro - radio, centro - radio, centro + radio, centro + radio],
              fill=AMARILLO, outline=AMBAR, width=3 * ESCALA)
    d.arc(caja(22), start=-50, end=50, fill=NARANJA, width=10 * ESCALA)
    d.arc(caja(22), start=130, end=230, fill=NARANJA, width=10 * ESCALA)
    return img


def seleccionar():
    """Marco de seleccion por esquinas con un elemento dentro."""
    img, d = lienzo()
    grosor, m, largo = 10 * ESCALA, 12 * ESCALA, 26 * ESCALA
    f = L - m
    for x0, y0, dx, dy in ((m, m, 1, 1), (f, m, -1, 1), (m, f, 1, -1), (f, f, -1, -1)):
        d.line([(x0, y0), (x0 + dx * largo, y0)], fill=NARANJA, width=grosor)
        d.line([(x0, y0), (x0, y0 + dy * largo)], fill=NARANJA, width=grosor)
    d.rectangle(caja(34), fill=AMARILLO, outline=AMBAR, width=3 * ESCALA)
    return img


ICONOS = (("IniciarDetener.pushbutton", iniciar_detener),
          ("Estado.pushbutton", estado),
          ("Seleccionar.pushbutton", seleccionar))


def main():
    for carpeta, dibujar in ICONOS:
        destino = os.path.normpath(os.path.join(PANEL, carpeta, "icon.png"))
        dibujar().resize((LADO, LADO), Image.LANCZOS).save(destino)
        print("escrito", destino)


if __name__ == "__main__":
    main()
