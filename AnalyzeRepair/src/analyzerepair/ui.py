"""Seccion 6. Interfaz de consola.

Formato del requerimiento:

    ========================================
     DATAX ANALYZE - REPARACION
    ========================================
    [OK] Verificando permisos administrativos
    ...
"""

from __future__ import annotations

import ctypes
import sys

ANCHO = 56
_LINEA = "=" * ANCHO


def preparar_consola():
    """Deja la consola en UTF-8 para que los acentos se vean bien."""
    try:
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except (OSError, AttributeError):
        pass
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _escribir(texto=""):
    try:
        print(texto, flush=True)
    except UnicodeEncodeError:
        print(texto.encode("ascii", "replace").decode("ascii"), flush=True)


def banner(dry_run=False):
    _escribir()
    _escribir(_LINEA)
    _escribir(" DATAX ANALYZE - REPARACIÓN DE PRERREQUISITOS")
    if dry_run:
        _escribir(" MODO SIMULACIÓN - no se modificará nada")
    _escribir(_LINEA)


def etapa(nombre, etiqueta):
    _escribir(f"[{etiqueta}] {nombre}")


def cierre(mensaje):
    _escribir(_LINEA)
    _escribir(f" {mensaje}")
    _escribir(_LINEA)
    _escribir()


def resumen(resultados, ruta_log):
    """Detalle final: solo lo que el tecnico necesita ver."""
    incidencias = [(n, r) for n, r in resultados if not r.ok]
    if incidencias:
        _escribir()
        _escribir(" Incidencias:")
        for nombre, resultado in incidencias:
            _escribir(f"   - {nombre}: {resultado.message}")
    if ruta_log:
        _escribir()
        _escribir(f" Log completo: {ruta_log}")


def pausar_si_interactivo():
    """Evita que la ventana se cierre de golpe al hacer doble clic en el EXE."""
    if not sys.stdin or not sys.stdin.isatty():
        return
    try:
        input("Pulse Intro para salir...")
    except (EOFError, KeyboardInterrupt):
        pass
