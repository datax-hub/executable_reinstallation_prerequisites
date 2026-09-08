"""Ejecucion de msiexec y de instaladores EXE.

Siempre con lista de argumentos y sin shell: los nombres de archivo y rutas
llevan espacios y acentos, y shell=True abriria la puerta a inyeccion.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

CREATE_NO_WINDOW = 0x08000000


@dataclass
class ResultadoProceso:
    codigo: int
    salida: str
    error: str
    expiro: bool = False

    @property
    def ok(self):
        return self.codigo == 0 and not self.expiro


def ejecutar(args, timeout=900, sin_ventana=True):
    """Ejecuta un proceso y espera su codigo de retorno."""
    args = [str(a) for a in args]
    flags = CREATE_NO_WINDOW if sin_ventana else 0
    try:
        completado = subprocess.run(
            args,
            capture_output=True,
            timeout=timeout,
            creationflags=flags,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ResultadoProceso(-1, "", f"El proceso excedio {timeout} s", expiro=True)
    except FileNotFoundError as exc:
        return ResultadoProceso(-1, "", f"No se encontro el ejecutable: {exc}")
    except OSError as exc:
        return ResultadoProceso(-1, "", f"No se pudo ejecutar: {exc}")

    return ResultadoProceso(
        completado.returncode,
        _texto(completado.stdout),
        _texto(completado.stderr),
    )


def _texto(datos):
    if not datos:
        return ""
    for codificacion in ("utf-8", "cp1252", "latin-1"):
        try:
            return datos.decode(codificacion).strip()
        except UnicodeDecodeError:
            continue
    return datos.decode("utf-8", errors="replace").strip()
