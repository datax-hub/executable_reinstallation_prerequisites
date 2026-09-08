"""RF-07 + RF-08. Rutas reales del sistema.

Dos problemas que resuelve este modulo:

1. Idioma (RF-07): en Windows en espanol la carpeta puede llamarse
   "Archivos de programa". Nunca se usa el literal "Program Files".

2. Redireccion WOW64 (RF-08): un proceso de 32 bits en Windows de 64 recibe
   "C:/Program Files (x86)" cuando pregunta por %ProgramFiles%. Leer el registro
   con KEY_WOW64_64KEY devuelve la ruta real de 64 bits.

La fuente primaria es el registro, que da la ruta ya localizada al idioma del
sistema y resuelve ambos problemas de una vez. SHGetKnownFolderPath queda como
respaldo.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

from .registry import CURRENT_VERSION, HKLM, VISTA_64, leer_valor

_FOLDERID_PROGRAM_FILES_X64 = "{6D809377-6AF0-444B-8957-A3773F02200E}"
_FOLDERID_PROGRAM_FILES_X86 = "{7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E}"


def es_so_64bits() -> bool:
    """True si el SISTEMA es de 64 bits (no el proceso)."""
    if sys.maxsize > 2 ** 32:
        return True
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        es_wow64 = wintypes.BOOL()
        if kernel32.IsWow64Process(kernel32.GetCurrentProcess(),
                                   ctypes.byref(es_wow64)):
            return bool(es_wow64.value)
    except (OSError, AttributeError):
        pass
    return False


def _known_folder(folder_id):
    try:
        guid = ctypes.create_unicode_buffer(folder_id)
        iid = (ctypes.c_byte * 16)()
        if ctypes.windll.ole32.IIDFromString(guid, ctypes.byref(iid)) != 0:
            return None
        salida = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(
                ctypes.byref(iid), 0, None, ctypes.byref(salida)) != 0:
            return None
        try:
            return Path(salida.value) if salida.value else None
        finally:
            ctypes.windll.ole32.CoTaskMemFree(salida)
    except (OSError, AttributeError, ValueError):
        return None


def _desde_registro(nombre_valor):
    valor = leer_valor(HKLM, CURRENT_VERSION, nombre_valor, VISTA_64)
    if not valor:
        return None
    ruta = Path(str(valor).strip())
    return ruta if ruta.is_absolute() else None


def program_files():
    """Program Files nativo. En SO de 32 bits es el unico que existe."""
    return _desde_registro("ProgramFilesDir") or _known_folder(_FOLDERID_PROGRAM_FILES_X64)


def program_files_x86():
    """Program Files (x86). Devuelve None en SO de 32 bits: NO es un error (RF-08)."""
    if not es_so_64bits():
        return None
    return _desde_registro("ProgramFilesDir (x86)") or _known_folder(_FOLDERID_PROGRAM_FILES_X86)


def mapa():
    """Marcadores admitidos en config.json -> ruta real (o None si no aplica)."""
    return {
        "{ProgramFiles}": program_files(),
        "{ProgramFilesX86}": program_files_x86(),
    }


def expandir(plantilla):
    """Sustituye los marcadores de una plantilla de config.json.

    Devuelve None si el marcador no aplica en este sistema (por ejemplo
    {ProgramFilesX86} en Windows de 32 bits). El llamador debe omitir la ruta
    sin generar error.
    """
    texto = str(plantilla)
    for marcador, base in mapa().items():
        if marcador in texto:
            if base is None:
                return None
            texto = texto.replace(marcador, str(base))
    return Path(texto)


def describir_sistema():
    """Resumen para el log, util al diagnosticar un equipo remoto."""
    proceso = 64 if sys.maxsize > 2 ** 32 else 32
    return {
        "so_bits": 64 if es_so_64bits() else 32,
        "proceso_bits": proceso,
        "program_files": str(program_files() or "(no resuelto)"),
        "program_files_x86": str(program_files_x86() or "(no aplica)"),
    }
