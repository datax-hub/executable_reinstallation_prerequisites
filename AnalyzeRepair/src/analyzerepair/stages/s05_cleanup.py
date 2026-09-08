"""RF-05. Limpieza de directorios.

Se VACIA el contenido de las carpetas de version base (110); la carpeta en si
se conserva. Los archivos bloqueados se reintentan, se registran y, si sigue sin
poder borrarse, se programa el borrado para el proximo reinicio.
"""

from __future__ import annotations

import ctypes
import shutil
import time
from pathlib import Path

from ..errors import RutaInsegura
from ..results import StageResult
from ..safety import assert_ruta_limpiable

NOMBRE = "Limpiando archivos"
CRITICA = False

MOVEFILE_DELAY_UNTIL_REBOOT = 0x4


def ejecutar(ctx):
    version = str(ctx.config.version_base)
    reintentos = int(ctx.config.limpieza.get("reintentos_archivo_bloqueado", 3))
    espera = float(ctx.config.limpieza.get("espera_entre_reintentos_segundos", 2))
    al_reiniciar = bool(ctx.config.limpieza.get("programar_borrado_al_reiniciar", True))

    detalles, bloqueados = [], []
    vaciadas = 0
    requiere_reinicio = False

    for raiz in ctx.config.raices:
        objetivo = Path(raiz) / version

        if not objetivo.exists():
            ctx.log.info("  [NO EXISTE] %s", objetivo)
            continue

        try:
            objetivo = assert_ruta_limpiable(objetivo, ctx.config.raices,
                                             nombre_esperado=version)
        except RutaInsegura as exc:
            ctx.log.error("  RUTA RECHAZADA: %s", exc)
            detalles.append(f"ruta rechazada: {exc}")
            continue

        ctx.log.info("  Carpeta encontrada: %s", objetivo)

        if ctx.dry_run:
            contenido = _contar(objetivo)
            ctx.log.info("  [SIMULACION] Se vaciaria (%d elemento(s)).", contenido)
            detalles.append(f"[SIMULACION] vaciaria {objetivo} ({contenido})")
            vaciadas += 1
            continue

        restantes = _vaciar(objetivo, reintentos, espera, ctx)
        if restantes:
            for ruta in restantes:
                bloqueados.append(str(ruta))
                if al_reiniciar and _programar_borrado(ruta):
                    requiere_reinicio = True
                    ctx.log.warning(
                        "  Bloqueado, se borrara al reiniciar: %s", ruta)
                else:
                    ctx.log.warning("  No se pudo eliminar: %s", ruta)
        else:
            ctx.log.info("  Contenido eliminado.")
        vaciadas += 1

    for omitida in ctx.config.raices_omitidas:
        ctx.log.info("  [NO APLICA] %s (sistema de 32 bits)", omitida)

    if vaciadas == 0:
        return StageResult.omitir(
            "No se encontro ninguna carpeta de version base para limpiar.")

    mensaje = f"{vaciadas} carpeta(s) procesada(s)."
    if bloqueados:
        detalles.extend(f"bloqueado: {b}" for b in bloqueados)
        return StageResult(
            ok=False, critical=False, requiere_reinicio=requiere_reinicio,
            message=(mensaje + f" {len(bloqueados)} archivo(s) bloqueado(s); "
                               f"ver el log para el detalle."),
            details=detalles)

    return StageResult.exito(mensaje, detalles, requiere_reinicio=requiere_reinicio)


def _contar(carpeta):
    try:
        return sum(1 for _ in carpeta.iterdir())
    except OSError:
        return 0


def _vaciar(carpeta, reintentos, espera, ctx):
    """Vacia el contenido. Devuelve la lista de rutas que no se pudieron borrar."""
    restantes = []
    for elemento in _listar(carpeta):
        if _borrar_con_reintentos(elemento, reintentos, espera, ctx):
            continue
        restantes.append(elemento)
    return restantes


def _listar(carpeta):
    try:
        return list(carpeta.iterdir())
    except OSError as exc:
        return []


def _borrar_con_reintentos(ruta, reintentos, espera, ctx):
    for intento in range(1, max(1, reintentos) + 1):
        try:
            if ruta.is_dir() and not ruta.is_symlink():
                shutil.rmtree(ruta)
            else:
                ruta.unlink()
            return True
        except OSError as exc:
            ctx.log.debug("  intento %d/%d fallido en %s: %s",
                          intento, reintentos, ruta, exc)
            _quitar_solo_lectura(ruta)
            if intento < reintentos:
                time.sleep(espera)
    return False


def _quitar_solo_lectura(ruta):
    try:
        import stat
        ruta.chmod(stat.S_IWRITE)
    except OSError:
        pass


def _programar_borrado(ruta):
    """Marca el archivo para que Windows lo borre en el proximo arranque."""
    try:
        return bool(ctypes.windll.kernel32.MoveFileExW(
            str(ruta), None, MOVEFILE_DELAY_UNTIL_REBOOT))
    except (OSError, AttributeError):
        return False
