"""RF-12. Registro de operaciones.

Log dual: consola (resumido) y archivo (detallado), un archivo por ejecucion.
El archivo va en UTF-8 con BOM para que el Bloc de notas muestre bien los acentos.
"""

from __future__ import annotations

import datetime as _dt
import logging
import sys
from pathlib import Path

NOMBRE = "analyzerepair"

_ruta_actual: Path | None = None


class _FormatoConsola(logging.Formatter):
    """[HH:MM:SS] mensaje -- el formato del ejemplo de la seccion 12."""

    def __init__(self):
        super().__init__("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")


class _FormatoArchivo(logging.Formatter):
    def __init__(self):
        super().__init__(
            "[%(asctime)s] %(levelname)-7s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def configurar(carpeta, nivel_consola="INFO", nivel_archivo="DEBUG",
               conservar_ultimos=30, sufijo=""):
    """Deja el logger listo y devuelve (logger, ruta_del_log)."""
    global _ruta_actual

    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)

    marca = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = carpeta / f"AnalyzeRepair_{marca}{sufijo}.log"

    log = logging.getLogger(NOMBRE)
    log.setLevel(logging.DEBUG)
    log.handlers.clear()
    log.propagate = False

    # nivel_consola=None: la consola la maneja ui.py como unico canal, para no
    # imprimir cada mensaje dos veces.
    if nivel_consola is not None:
        consola = logging.StreamHandler(sys.stdout)
        consola.setLevel(getattr(logging, nivel_consola, logging.INFO))
        consola.setFormatter(_FormatoConsola())
        log.addHandler(consola)

    archivo = logging.FileHandler(ruta, encoding="utf-8-sig")
    archivo.setLevel(getattr(logging, nivel_archivo, logging.DEBUG))
    archivo.setFormatter(_FormatoArchivo())
    log.addHandler(archivo)

    _ruta_actual = ruta
    _purgar(carpeta, conservar_ultimos)
    return log, ruta


def obtener():
    return logging.getLogger(NOMBRE)


def ruta_log_actual():
    return _ruta_actual


def ruta_log_msi(nombre_componente):
    """Ruta del log verboso que genera msiexec para un componente."""
    if _ruta_actual is None:
        return None
    return _ruta_actual.parent / f"{_ruta_actual.stem}_{nombre_componente}.log"


def _purgar(carpeta, conservar):
    """Borra los logs mas antiguos. Nunca falla el proceso por esto."""
    if not conservar or conservar <= 0:
        return
    try:
        logs = sorted(carpeta.glob("AnalyzeRepair_*.log"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
        for viejo in logs[conservar:]:
            try:
                viejo.unlink()
            except OSError:
                pass
    except OSError:
        pass
