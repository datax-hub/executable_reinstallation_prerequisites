"""RF-01. Verificacion de privilegios y relanzado elevado por UAC."""

from __future__ import annotations

import ctypes
import subprocess
import sys


def es_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (OSError, AttributeError):
        return False


def _linea_argumentos(argv):
    return subprocess.list2cmdline(list(argv))


def relanzar_elevado(argv=None) -> bool:
    """Vuelve a lanzar este mismo programa pidiendo elevacion por UAC.

    Devuelve True si Windows acepto lanzar el proceso elevado (el llamador debe
    entonces terminar). False si el usuario cancelo el dialogo de UAC.
    """
    argv = list(sys.argv[1:] if argv is None else argv)

    if getattr(sys, "frozen", False):
        ejecutable = sys.executable
        parametros = _linea_argumentos(argv)
    else:
        ejecutable = sys.executable
        parametros = _linea_argumentos(["-m", "analyzerepair"] + argv)

    try:
        codigo = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", ejecutable, parametros, None, 1)
    except (OSError, AttributeError):
        return False
    # ShellExecuteW devuelve <= 32 en caso de error; 5 = ERROR_ACCESS_DENIED
    # es lo que llega cuando el usuario cancela el dialogo de UAC.
    return int(codigo) > 32
