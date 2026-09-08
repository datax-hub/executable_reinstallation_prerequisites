"""Genera el icono del ejecutable a partir del logotipo de DATAX.

El original (assets/favicondatax.ico) es una sola imagen de 256x219. Windows
espera iconos CUADRADOS y con varias resoluciones: si se entrega tal cual, el
sistema lo deforma al reducirlo para la barra de tareas y el explorador.

Este script lo centra sobre un lienzo cuadrado transparente y emite un .ico con
todas las medidas que Windows usa.

Uso (requiere Pillow, solo para desarrollo):
    python build/generar_icono.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "assets" / "favicondatax.ico"
DESTINO = RAIZ / "build" / "AnalyzeRepair.ico"

# Medidas que Windows solicita segun el contexto: lista de archivos, barra de
# tareas, iconos grandes del explorador, vista previa.
MEDIDAS = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

# Margen relativo para que el logo respire dentro del cuadro.
MARGEN = 0.06


def cuadrar(imagen):
    """Centra la imagen en un lienzo cuadrado transparente, sin deformarla."""
    lado = max(imagen.size)
    lado = int(lado * (1 + MARGEN * 2))

    escala = min(
        (lado * (1 - MARGEN * 2)) / imagen.width,
        (lado * (1 - MARGEN * 2)) / imagen.height,
    )
    nuevo = (max(1, round(imagen.width * escala)), max(1, round(imagen.height * escala)))
    reducida = imagen.resize(nuevo, Image.LANCZOS)

    lienzo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    lienzo.paste(
        reducida,
        ((lado - nuevo[0]) // 2, (lado - nuevo[1]) // 2),
        reducida,
    )
    return lienzo


def main():
    if not ORIGEN.is_file():
        print(f"No se encontro el logotipo de origen: {ORIGEN}")
        return 1

    original = Image.open(ORIGEN).convert("RGBA")
    print(f"Origen : {ORIGEN.name}  {original.width}x{original.height}")

    cuadrada = cuadrar(original)
    print(f"Cuadrado: {cuadrada.width}x{cuadrada.height}")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    cuadrada.save(DESTINO, format="ICO", sizes=MEDIDAS)

    resultado = Image.open(DESTINO)
    print(f"Destino: {DESTINO.name}  resoluciones: "
          f"{sorted(resultado.ico.sizes())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
