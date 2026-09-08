"""RF-04. Desinstalacion de los prerrequisitos.

Solo se desinstala lo que la etapa de deteccion coloco en la lista de trabajo,
que ya paso el filtro de exclusiones. Nunca se recorre el registro aqui.
"""

from __future__ import annotations

from ..results import StageResult
from ..winapi import process

NOMBRE = "Desinstalando prerrequisitos"
CRITICA = True


def ejecutar(ctx):
    opciones = ctx.config.msiexec
    exito = list(opciones.get("codigos_exito", [0]))
    con_reinicio = list(opciones.get("codigos_exito_con_reinicio", [3010, 1641]))
    no_instalado = list(opciones.get("codigos_no_instalado", [1605]))
    timeout = int(opciones.get("timeout_segundos", 900))
    args_base = list(opciones.get("args_desinstalacion", ["/qn", "/norestart"]))

    pendientes = [
        (comp, ctx.detectados[comp.id])
        for comp in ctx.config.componentes_aplicables(ctx.so_64bits)
        if comp.desinstalar and comp.id in ctx.detectados
    ]

    if not pendientes:
        return StageResult.omitir("No hay componentes que desinstalar.")

    desinstalados, fallidos, detalles = 0, [], []
    requiere_reinicio = False

    for componente, entrada in pendientes:
        codigo_producto = entrada.product_code
        if not codigo_producto:
            fallidos.append(componente.id)
            detalles.append(
                f"{componente.nombre_visible}: sin ProductCode, no se puede "
                f"desinstalar de forma silenciosa. Requiere intervencion manual.")
            ctx.log.error(detalles[-1])
            continue

        # Cinturon y tirantes: se vuelve a comprobar la exclusion justo antes
        # de ejecutar la desinstalacion.
        exclusion = ctx.config.esta_excluido(codigo_producto)
        if exclusion is not None:
            ctx.log.error(
                "ABORTADO: se intento desinstalar '%s', que esta protegido.",
                exclusion.producto)
            return StageResult.fallo(
                f"Se intento desinstalar un componente protegido "
                f"({exclusion.producto}). Proceso detenido por seguridad.")

        comando = ["msiexec", "/x", codigo_producto] + args_base
        ctx.log.info("Desinstalando: %s (version %s)",
                     componente.nombre_visible,
                     entrada.display_version or "desconocida")
        ctx.log.info("  Comando: %s", " ".join(comando))

        if ctx.dry_run:
            detalles.append(f"[SIMULACION] desinstalaria {componente.id}")
            desinstalados += 1
            continue

        resultado = process.ejecutar(comando, timeout=timeout)

        if resultado.codigo in exito:
            ctx.log.info("  OK - Desinstalado correctamente (codigo 0)")
            desinstalados += 1
        elif resultado.codigo in con_reinicio:
            ctx.log.info("  OK - Desinstalado, requiere reiniciar (codigo %d)",
                         resultado.codigo)
            desinstalados += 1
            requiere_reinicio = True
        elif resultado.codigo in no_instalado:
            ctx.log.info("  El producto ya no estaba instalado (codigo %d)",
                         resultado.codigo)
        else:
            fallidos.append(componente.id)
            mensaje = (f"{componente.nombre_visible}: msiexec devolvio "
                       f"{resultado.codigo}")
            if resultado.expiro:
                mensaje += " (tiempo de espera agotado)"
            ctx.log.error("  ERROR - %s", mensaje)
            if resultado.error:
                ctx.log.debug("  stderr: %s", resultado.error)
            detalles.append(mensaje)

    resumen = f"{desinstalados} desinstalado(s), {len(fallidos)} fallido(s)."
    if fallidos:
        return StageResult.fallo(
            resumen + " No se continua para no dejar el equipo a medias.",
            detalles)
    return StageResult.exito(resumen, detalles, requiere_reinicio=requiere_reinicio)
