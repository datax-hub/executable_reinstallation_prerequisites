"""Orquestador del pipeline y linea de comandos.

Orden (seccion 14 del requerimiento):
  permisos -> detener servicio -> detectar -> desinstalar -> limpiar ->
  renombrar versiones -> instalar -> validar -> iniciar servicio

Una etapa critica fallida aborta el proceso. Si el servicio ya estaba detenido
por nosotros, se intenta volver a levantarlo antes de salir: dejar Analyze caido
es peor que el fallo original.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field

from . import logger as _logger
from . import ui
from .config import Config, cargar
from .errors import AnalyzeRepairError
from .results import ExitCode, StageResult
from .stages import (s01_admin, s02_service_stop, s03_detect, s04_uninstall,
                     s05_cleanup, s06_versions, s07_install, s08_validate,
                     s09_service_start)
from .winapi import elevation, paths

VERSION = "1.0.0"

PIPELINE = (
    s01_admin, s02_service_stop, s03_detect, s04_uninstall, s05_cleanup,
    s06_versions, s07_install, s08_validate, s09_service_start,
)

SOLO_ANALISIS = (s01_admin, s03_detect)


@dataclass
class Contexto:
    config: Config
    log: object
    dry_run: bool = False
    so_64bits: bool = True
    servicio_existia: bool = False
    servicio_detenido_por_nosotros: bool = False
    detectados: dict = field(default_factory=dict)
    excluidos_presentes: dict = field(default_factory=dict)
    resultados: list = field(default_factory=list)


def construir_parser():
    parser = argparse.ArgumentParser(
        prog="AnalyzeRepair",
        description="Repara los prerrequisitos de DATAX Analyze.")
    parser.add_argument("--dry-run", action="store_true",
                        help="simula el proceso completo sin modificar nada")
    parser.add_argument("--solo-detectar", action="store_true",
                        help="solo analiza que hay instalado y sale")
    parser.add_argument("--config", metavar="RUTA",
                        help="ruta alternativa a config.json")
    parser.add_argument("--sin-elevar", action="store_true",
                        help="no intenta elevar por UAC (para diagnostico)")
    parser.add_argument("--sin-pausa", action="store_true",
                        help="no espera Intro al terminar")
    parser.add_argument("--version", action="version",
                        version=f"AnalyzeRepair {VERSION}")
    return parser


def main(argv=None):
    args = construir_parser().parse_args(argv)
    ui.preparar_consola()
    ui.banner(dry_run=args.dry_run)

    # Elevacion antes de cualquier otra cosa (RF-01).
    if not args.dry_run and not args.sin_elevar and not elevation.es_admin():
        ui.etapa("Solicitando privilegios administrativos", "..")
        if elevation.relanzar_elevado():
            return int(ExitCode.OK)
        ui.etapa("Verificando permisos administrativos", "ERROR")
        ui.cierre("SE REQUIEREN PRIVILEGIOS DE ADMINISTRADOR")
        if not args.sin_pausa:
            ui.pausar_si_interactivo()
        return int(ExitCode.SIN_PERMISOS)

    try:
        config = cargar(args.config)
    except AnalyzeRepairError as exc:
        ui.etapa("Cargando configuración", "ERROR")
        print(f"\n{exc}\n")
        if not args.sin_pausa:
            ui.pausar_si_interactivo()
        return int(ExitCode.ERROR_CRITICO)

    log, ruta_log = _logger.configurar(
        config.carpeta_logs,
        nivel_consola=None,               # la consola la maneja ui.py
        nivel_archivo=config.log.get("nivel_archivo", "DEBUG"),
        conservar_ultimos=int(config.log.get("conservar_ultimos", 30)),
        sufijo="_simulacion" if args.dry_run else "",
    )

    ctx = Contexto(config=config, log=log, dry_run=args.dry_run,
                   so_64bits=paths.es_so_64bits())

    log.info("Inicio del proceso. AnalyzeRepair %s%s",
             VERSION, " (SIMULACION)" if args.dry_run else "")
    log.info("Configuracion: %s", config.ruta)

    etapas = SOLO_ANALISIS if args.solo_detectar else PIPELINE
    codigo = ejecutar_pipeline(ctx, etapas)

    log.info("Proceso finalizado con codigo %d.", codigo)
    ui.resumen(ctx.resultados, ruta_log)
    if not args.sin_pausa:
        ui.pausar_si_interactivo()
    return codigo


def ejecutar_pipeline(ctx, etapas=PIPELINE):
    resultados = []
    ctx.resultados = resultados
    requiere_reinicio = False
    hubo_advertencias = False

    for etapa in etapas:
        nombre = etapa.NOMBRE
        try:
            resultado = etapa.ejecutar(ctx)
        except AnalyzeRepairError as exc:
            resultado = StageResult.fallo(str(exc))
        except Exception as exc:                       # noqa: BLE001
            ctx.log.exception("Error inesperado en la etapa '%s'", nombre)
            resultado = StageResult.fallo(f"Error inesperado: {exc}")

        resultados.append((nombre, resultado))
        ui.etapa(nombre, resultado.etiqueta)
        _registrar(ctx, nombre, resultado)

        requiere_reinicio = requiere_reinicio or resultado.requiere_reinicio
        if not resultado.ok:
            if resultado.critical:
                return _abortar(ctx, nombre, resultado)
            hubo_advertencias = True

    if requiere_reinicio:
        ui.cierre("PROCESO FINALIZADO - REINICIE WINDOWS PARA COMPLETARLO")
        return int(ExitCode.REQUIERE_REINICIO)
    if hubo_advertencias:
        ui.cierre("PROCESO FINALIZADO CON ADVERTENCIAS")
        return int(ExitCode.ADVERTENCIAS)
    ui.cierre("PROCESO FINALIZADO CORRECTAMENTE")
    return int(ExitCode.OK)


def _registrar(ctx, nombre, resultado):
    nivel = ctx.log.info if resultado.ok else (
        ctx.log.warning if not resultado.critical else ctx.log.error)
    nivel("[%s] %s: %s", resultado.etiqueta, nombre, resultado.message)
    for detalle in resultado.details:
        ctx.log.debug("    %s", detalle)


def _abortar(ctx, nombre, resultado):
    """Aborta informando, e intenta no dejar el servicio caido."""
    ctx.log.error("Proceso abortado en la etapa '%s'.", nombre)
    print(f"\n  {resultado.message}\n")

    if ctx.servicio_detenido_por_nosotros and not ctx.dry_run:
        ctx.log.warning(
            "Recuperacion: se intenta volver a iniciar el servicio para no "
            "dejar DATAX Analyze detenido.")
        recuperacion = s09_service_start.ejecutar(ctx)
        ui.etapa("Recuperación: iniciando servicio", recuperacion.etiqueta)
        _registrar(ctx, "Recuperación", recuperacion)
        ctx.resultados.append(("Recuperación: iniciando servicio", recuperacion))

    ui.cierre("PROCESO INTERRUMPIDO - REVISE EL LOG")
    return int(ExitCode.ERROR_CRITICO)


if __name__ == "__main__":
    sys.exit(main())
