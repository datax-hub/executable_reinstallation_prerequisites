"""RF-06. Manejo de versiones superiores a la base.

Las subcarpetas de version mayores a 110 se apartan anteponiendo '_' al nombre
(140 -> _140) para que no interfieran con los componentes que Analyze necesita.
La 110 y las inferiores se conservan intactas.

Es idempotente: si _140 ya existe de una ejecucion anterior, no falla.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..errors import RutaInsegura
from ..results import StageResult
from ..safety import assert_ruta_renombrable

NOMBRE = "Revisando versiones superiores"
CRITICA = False

_SOLO_DIGITOS = re.compile(r"^\d+$")


def ejecutar(ctx):
    base = ctx.config.version_base
    detalles = []
    renombradas, conservadas, fallidas = 0, 0, 0

    for raiz in ctx.config.raices:
        raiz = Path(raiz)
        if not raiz.is_dir():
            ctx.log.info("  [NO EXISTE] %s", raiz)
            continue

        ctx.log.info("  Revisando: %s", raiz)
        for hijo in _subcarpetas(raiz, ctx):
            if not _SOLO_DIGITOS.match(hijo.name):
                continue

            numero = int(hijo.name)
            if numero <= base:
                ctx.log.info("    [OK - se conserva] %s", hijo.name)
                conservadas += 1
                continue

            destino = hijo.with_name("_" + hijo.name)

            if destino.exists():
                ctx.log.info("    [YA APARTADA] %s existe; se omite %s",
                             destino.name, hijo.name)
                detalles.append(f"ya apartada: {destino}")
                continue

            try:
                origen = assert_ruta_renombrable(hijo, ctx.config.raices)
            except RutaInsegura as exc:
                ctx.log.error("    RUTA RECHAZADA: %s", exc)
                detalles.append(f"ruta rechazada: {exc}")
                fallidas += 1
                continue

            if ctx.dry_run:
                ctx.log.info("    [SIMULACION] %s se renombraria a %s",
                             origen.name, destino.name)
                detalles.append(f"[SIMULACION] {origen} -> {destino.name}")
                renombradas += 1
                continue

            try:
                origen.rename(destino)
            except OSError as exc:
                ctx.log.error("    No se pudo renombrar %s: %s", origen, exc)
                detalles.append(f"fallo al renombrar {origen}: {exc}")
                fallidas += 1
                continue

            ctx.log.info("    Carpeta %s renombrada a %s", origen.name, destino.name)
            detalles.append(f"{origen} -> {destino.name}")
            renombradas += 1

    mensaje = (f"{renombradas} carpeta(s) apartada(s), "
               f"{conservadas} conservada(s).")
    if fallidas:
        return StageResult.advertencia(
            mensaje + f" {fallidas} no se pudo procesar.", detalles)
    return StageResult.exito(mensaje, detalles)


def _subcarpetas(raiz, ctx):
    try:
        return sorted(p for p in raiz.iterdir() if p.is_dir())
    except OSError as exc:
        ctx.log.warning("  No se pudo listar %s: %s", raiz, exc)
        return []
