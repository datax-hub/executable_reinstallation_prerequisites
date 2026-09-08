"""Excepciones propias de AnalyzeRepair."""

from __future__ import annotations


class AnalyzeRepairError(Exception):
    """Base de todos los errores de la herramienta."""


class ConfigInvalida(AnalyzeRepairError):
    """config.json ausente, malformado o incompleto."""


class RutaInsegura(AnalyzeRepairError):
    """Una ruta no supero el guard de safety.py.

    Se lanza ANTES de cualquier operacion destructiva. Que aparezca significa
    que hay un error de construccion de rutas, no un problema del equipo.
    """


class InstaladorAusente(AnalyzeRepairError):
    """Falta un instalador declarado en config.json dentro de Prerequisites/."""


class ServicioError(AnalyzeRepairError):
    """Fallo al consultar o controlar el servicio de Windows."""
