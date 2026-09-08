"""Lectura del registro en AMBAS vistas WOW64.

Un proceso de 32 bits en Windows de 64 ve por defecto la rama redirigida
(Wow6432Node) y no encuentra los productos de 64 bits. Por eso cada lectura
declara explicitamente su vista: KEY_WOW64_64KEY o KEY_WOW64_32KEY.
"""

from __future__ import annotations

import re
import winreg
from dataclasses import dataclass

VISTA_64 = winreg.KEY_WOW64_64KEY
VISTA_32 = winreg.KEY_WOW64_32KEY
VISTAS = (VISTA_64, VISTA_32)

HKLM = winreg.HKEY_LOCAL_MACHINE
HKCU = winreg.HKEY_CURRENT_USER

CURRENT_VERSION = r"SOFTWARE\Microsoft\Windows\CurrentVersion"
UNINSTALL = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"

_GUID = re.compile(r"^\{[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}\}$")


def nombre_vista(vista):
    return "64 bits" if vista == VISTA_64 else "32 bits"


@dataclass
class EntradaUninstall:
    """Una entrada de Agregar o quitar programas."""

    clave: str
    display_name: str
    display_version: str
    product_code: str | None
    uninstall_string: str
    vista: int
    hive: str

    @property
    def es_msi(self) -> bool:
        return self.product_code is not None

    def __str__(self):
        return f"{self.display_name} {self.display_version} [{self.product_code or self.clave}]"


def leer_valor(hive, subclave, nombre, vista):
    """Devuelve el valor o None. Nunca lanza por clave/valor inexistente."""
    try:
        with winreg.OpenKey(hive, subclave, 0, winreg.KEY_READ | vista) as clave:
            valor, _ = winreg.QueryValueEx(clave, nombre)
            return valor
    except OSError:
        return None


def _leer_str(clave, nombre, por_defecto=""):
    try:
        valor, _ = winreg.QueryValueEx(clave, nombre)
        return str(valor).strip() if valor is not None else por_defecto
    except OSError:
        return por_defecto


def listar_desinstalables(vista, hives=(HKLM, HKCU)):
    """Recorre las claves Uninstall de la vista indicada."""
    etiquetas = {HKLM: "HKLM", HKCU: "HKCU"}
    for hive in hives:
        try:
            raiz = winreg.OpenKey(hive, UNINSTALL, 0, winreg.KEY_READ | vista)
        except OSError:
            continue
        with raiz:
            try:
                total = winreg.QueryInfoKey(raiz)[0]
            except OSError:
                continue
            for indice in range(total):
                try:
                    nombre = winreg.EnumKey(raiz, indice)
                except OSError:
                    continue
                try:
                    with winreg.OpenKey(raiz, nombre, 0, winreg.KEY_READ | vista) as sub:
                        display = _leer_str(sub, "DisplayName")
                        if not display:
                            continue
                        yield EntradaUninstall(
                            clave=nombre,
                            display_name=display,
                            display_version=_leer_str(sub, "DisplayVersion"),
                            product_code=nombre if _GUID.match(nombre) else None,
                            uninstall_string=_leer_str(sub, "UninstallString"),
                            vista=vista,
                            hive=etiquetas.get(hive, "?"),
                        )
                except OSError:
                    continue


def inventario():
    """Todas las entradas de ambas vistas, sin filtrar."""
    salida = []
    for vista in VISTAS:
        salida.extend(listar_desinstalables(vista))
    return salida
