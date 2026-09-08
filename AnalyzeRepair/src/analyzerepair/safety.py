"""Seccion 8 del requerimiento. Guard de rutas.

Esta herramienta borra y renombra con privilegios de administrador. Un error al
construir una ruta destruye el sistema. TODA operacion destructiva pasa por aqui
antes de ejecutarse; si algo no cuadra se lanza RutaInsegura y la etapa aborta.
Nunca se continua "por si acaso".
"""

from __future__ import annotations

import re
from pathlib import Path

from .errors import RutaInsegura

# Profundidad minima de una ruta objetivo, contando la raiz de unidad.
# "C:/", "Program Files", "Microsoft.NET", "ADOMD.NET", "110" -> 5
_MIN_COMPONENTES = 4

_PATRON_VERSION = re.compile(r"^\d+$")

# Carpetas que jamas pueden ser objetivo, por muy bien construida que este la ruta.
_PROHIBIDAS = {
    "windows", "system32", "syswow64", "users", "usuarios",
    "program files", "program files (x86)",
    "archivos de programa", "archivos de programa (x86)",
    "programdata", "documents and settings",
}


def _normalizar(ruta):
    try:
        return Path(ruta).resolve(strict=False)
    except (OSError, ValueError) as exc:
        raise RutaInsegura(f"No se pudo normalizar la ruta '{ruta}': {exc}") from exc


def _dentro_de(ruta, raices):
    """La ruta debe estar ESTRICTAMENTE dentro de alguna raiz permitida."""
    for raiz in raices:
        if raiz is None:
            continue
        raiz = _normalizar(raiz)
        if ruta == raiz:
            continue
        try:
            ruta.relative_to(raiz)
        except ValueError:
            continue
        return raiz
    return None


def _comprobaciones_comunes(ruta, raices):
    ruta = _normalizar(ruta)

    if len(ruta.parts) < _MIN_COMPONENTES:
        raise RutaInsegura(
            f"Ruta demasiado corta para ser un objetivo valido: {ruta}")

    if ruta.parent == ruta:
        raise RutaInsegura(f"La ruta es la raiz de una unidad: {ruta}")

    if ruta.name.strip().lower() in _PROHIBIDAS:
        raise RutaInsegura(f"Carpeta protegida del sistema: {ruta}")

    raiz = _dentro_de(ruta, raices)
    if raiz is None:
        raise RutaInsegura(
            f"La ruta esta fuera de las carpetas permitidas: {ruta}")

    if ruta.is_symlink():
        raise RutaInsegura(
            f"La ruta es un enlace simbolico y podria apuntar fuera: {ruta}")

    if not ruta.exists():
        raise RutaInsegura(f"La ruta no existe: {ruta}")

    if not ruta.is_dir():
        raise RutaInsegura(f"La ruta no es un directorio: {ruta}")

    return ruta, raiz


def assert_ruta_limpiable(ruta, raices_permitidas, nombre_esperado=None):
    """Valida una carpeta antes de VACIAR su contenido (RF-05).

    Se vacia el contenido, nunca se borra la carpeta.
    """
    ruta, _ = _comprobaciones_comunes(ruta, raices_permitidas)
    if nombre_esperado is not None and ruta.name != str(nombre_esperado):
        raise RutaInsegura(
            f"Se esperaba la carpeta '{nombre_esperado}' y se recibio '{ruta.name}': {ruta}")
    return ruta


def assert_ruta_renombrable(ruta, raices_permitidas):
    """Valida una carpeta de version antes de RENOMBRARLA (RF-06).

    Solo se admiten nombres puramente numericos: 120, 130, 140...
    """
    ruta, _ = _comprobaciones_comunes(ruta, raices_permitidas)
    if not _PATRON_VERSION.match(ruta.name):
        raise RutaInsegura(
            f"Solo se renombran carpetas de version numerica, no '{ruta.name}': {ruta}")
    return ruta


def es_subruta(candidata, raices_permitidas):
    """Version no lanzante, para comprobaciones informativas."""
    try:
        return _dentro_de(_normalizar(candidata), raices_permitidas) is not None
    except RutaInsegura:
        return False
