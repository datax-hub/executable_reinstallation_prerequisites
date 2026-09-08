"""Punto de entrada: python -m analyzerepair (y del EXE empaquetado)."""

from __future__ import annotations

import sys

if __package__ in (None, ""):
    # Ejecutado como script suelto: asegurar que el paquete es importable.
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzerepair.main import main

if __name__ == "__main__":
    sys.exit(main())
