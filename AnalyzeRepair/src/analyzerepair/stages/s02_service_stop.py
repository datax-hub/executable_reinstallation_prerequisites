"""RF-02. Detencion del servicio de DATAX Analyze.

Etapa critica: desinstalar con el servicio en marcha deja archivos bloqueados y
la limpieza posterior falla.
"""

from __future__ import annotations

from ..errors import ServicioError
from ..results import StageResult
from ..winapi import service

NOMBRE = "Deteniendo servicio"
CRITICA = True


def ejecutar(ctx):
    nombre = ctx.config.servicio_nombre

    try:
        estado_actual = service.estado(nombre)
    except ServicioError as exc:
        return StageResult.fallo(f"No se pudo consultar el servicio: {exc}")

    if estado_actual is None:
        ctx.servicio_existia = False
        mensaje = f"El servicio '{nombre}' no existe en este equipo."
        if ctx.config.servicio_si_no_existe == "abortar":
            return StageResult.fallo(mensaje)
        return StageResult.advertencia(
            mensaje + " Se continua con el resto del proceso.")

    ctx.servicio_existia = True
    ctx.log.info("Servicio '%s' encontrado, estado actual: %s",
                 nombre, service.nombre_estado(estado_actual))

    if estado_actual == service.SERVICE_STOPPED:
        return StageResult.exito(f"El servicio '{nombre}' ya estaba detenido.")

    if ctx.dry_run:
        return StageResult.exito(
            f"[SIMULACION] Se detendria el servicio '{nombre}'.")

    try:
        ok, final = service.detener(nombre, ctx.config.servicio_timeout_detener)
    except ServicioError as exc:
        return StageResult.fallo(f"No se pudo detener el servicio: {exc}")

    if not ok:
        return StageResult.fallo(
            f"El servicio '{nombre}' no llego a detenerse tras "
            f"{ctx.config.servicio_timeout_detener} s "
            f"(estado final: {service.nombre_estado(final)}). "
            f"Detengalo manualmente y vuelva a ejecutar la herramienta.")

    ctx.servicio_detenido_por_nosotros = True
    return StageResult.exito(f"Servicio '{nombre}' detenido correctamente.")
