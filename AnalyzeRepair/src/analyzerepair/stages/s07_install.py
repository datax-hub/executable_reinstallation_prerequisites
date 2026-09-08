"""RF-09. Instalacion de los prerrequisitos.

Orden estricto (x86 antes que x64 en cada par) y filtrado por arquitectura: los
paquetes x64 se omiten en Windows de 32 bits.
"""

from __future__ import annotations

from ..results import StageResult
from ..winapi import process
from .. import logger as _logger

NOMBRE = "Instalando prerrequisitos"
CRITICA = True


def ejecutar(ctx):
    opciones = ctx.config.msiexec
    exito = list(opciones.get("codigos_exito", [0]))
    con_reinicio = list(opciones.get("codigos_exito_con_reinicio", [3010, 1641]))
    timeout = int(opciones.get("timeout_segundos", 900))
    args_base = list(opciones.get("args_instalacion", ["/qn", "/norestart"]))
    verboso = bool(opciones.get("log_verboso", True))

    carpeta = ctx.config.carpeta_instaladores
    pendientes = [c for c in ctx.config.componentes_aplicables(ctx.so_64bits)
                  if c.instalar]

    if not pendientes:
        return StageResult.omitir("No hay componentes que instalar.")

    ctx.log.info("  Carpeta de instaladores: %s", carpeta)
    ctx.log.info("  Se instalaran %d paquete(s) en este orden:", len(pendientes))
    for indice, comp in enumerate(pendientes, 1):
        ctx.log.info("    %d. %s", indice, comp.archivo)

    faltantes = [c.archivo for c in pendientes if not (carpeta / c.archivo).is_file()]
    if faltantes:
        return StageResult.fallo(
            "Faltan instaladores en la carpeta Prerequisites: "
            + ", ".join(faltantes))

    instalados, fallidos, detalles = 0, [], []
    requiere_reinicio = False

    for componente in pendientes:
        ruta = carpeta / componente.archivo
        comando = _comando(componente, ruta, args_base, verboso)

        ctx.log.info("Instalando: %s", componente.archivo)
        ctx.log.info("  Comando: %s", " ".join(str(x) for x in comando))

        if ctx.dry_run:
            detalles.append(f"[SIMULACION] instalaria {componente.archivo}")
            instalados += 1
            continue

        resultado = process.ejecutar(comando, timeout=timeout)

        if resultado.codigo in exito:
            ctx.log.info("  [OK] %s instalado correctamente.", componente.archivo)
            instalados += 1
        elif resultado.codigo in con_reinicio:
            ctx.log.info("  [OK] %s instalado, requiere reiniciar (codigo %d).",
                         componente.archivo, resultado.codigo)
            instalados += 1
            requiere_reinicio = True
        else:
            fallidos.append(componente.archivo)
            mensaje = f"{componente.archivo}: codigo de retorno {resultado.codigo}"
            if resultado.expiro:
                mensaje += " (tiempo de espera agotado)"
            ctx.log.error("  [ERROR] %s", mensaje)
            if resultado.error:
                ctx.log.debug("  stderr: %s", resultado.error)
            detalles.append(mensaje)

    resumen = f"{instalados} instalado(s), {len(fallidos)} fallido(s)."
    if fallidos:
        return StageResult.fallo(
            resumen + " Revise el log de msiexec correspondiente.", detalles)
    return StageResult.exito(resumen, detalles, requiere_reinicio=requiere_reinicio)


def _comando(componente, ruta, args_base, verboso):
    if componente.tipo == "exe":
        return [str(ruta)] + list(componente.args_instalacion)

    comando = ["msiexec", "/i", str(ruta)] + args_base
    if verboso:
        destino = _logger.ruta_log_msi(componente.id)
        if destino is not None:
            comando += ["/l*v", str(destino)]
    return comando
