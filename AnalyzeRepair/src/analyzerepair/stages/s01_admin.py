"""RF-01. Verificacion de privilegios administrativos."""

from __future__ import annotations

from ..results import StageResult
from ..winapi import elevation, paths

NOMBRE = "Verificando permisos administrativos"
CRITICA = True


def ejecutar(ctx):
    info = paths.describir_sistema()
    ctx.log.debug("Sistema: %s", info)
    ctx.log.info("Sistema operativo de %d bits, proceso de %d bits.",
                 info["so_bits"], info["proceso_bits"])
    ctx.log.info("Program Files      : %s", info["program_files"])
    ctx.log.info("Program Files (x86): %s", info["program_files_x86"])

    if elevation.es_admin():
        return StageResult.exito("Privilegios administrativos verificados.")

    if ctx.dry_run:
        return StageResult.advertencia(
            "Sin privilegios administrativos. En modo simulacion se continua, "
            "pero la ejecucion real requiere ejecutar como administrador.")

    return StageResult.fallo(
        "El programa no tiene privilegios administrativos. "
        "Ejecutelo con boton derecho > Ejecutar como administrador.")
