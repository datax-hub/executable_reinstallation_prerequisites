"""RF-11. Inicio del servicio de DATAX Analyze."""

from __future__ import annotations

from ..errors import ServicioError
from ..results import StageResult
from ..winapi import service

NOMBRE = "Iniciando servicio"
CRITICA = False


def ejecutar(ctx):
    nombre = ctx.config.servicio_nombre

    if not ctx.servicio_existia:
        return StageResult.omitir(
            f"El servicio '{nombre}' no existe en este equipo; no hay nada que iniciar.")

    if ctx.dry_run:
        return StageResult.exito(f"[SIMULACION] Se iniciaria el servicio '{nombre}'.")

    try:
        ok, final = service.iniciar(nombre, ctx.config.servicio_timeout_iniciar)
    except ServicioError as exc:
        return StageResult.advertencia(
            f"No se pudo iniciar el servicio '{nombre}': {exc}. "
            f"Inicielo manualmente desde services.msc.")

    if not ok:
        return StageResult.advertencia(
            f"El servicio '{nombre}' no llego a iniciarse tras "
            f"{ctx.config.servicio_timeout_iniciar} s "
            f"(estado final: {service.nombre_estado(final)}). "
            f"Inicielo manualmente desde services.msc.")

    return StageResult.exito(f"Servicio '{nombre}' iniciado correctamente.")
