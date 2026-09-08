"""RF-10. Validacion posterior a la instalacion.

Comprueba que los componentes esperados estan instalados con la version
correcta, que las carpetas base existen y no quedaron vacias, que no queda
ninguna version superior sin apartar, y -- lo mas importante en terminos de
riesgo -- que los componentes protegidos siguen intactos.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..results import StageResult
from ..winapi import registry

NOMBRE = "Validando instalacion"
CRITICA = False

_SOLO_DIGITOS = re.compile(r"^\d+$")


def ejecutar(ctx):
    if ctx.dry_run:
        return StageResult.omitir(
            "[SIMULACION] La validacion se omite: no se instalo nada.")

    inventario = registry.inventario()
    por_codigo = {(e.product_code or "").upper(): e for e in inventario}
    problemas, detalles = [], []

    # 1. Los componentes esperados estan presentes y con la version correcta.
    for componente in ctx.config.componentes_aplicables(ctx.so_64bits):
        if not componente.instalar:
            continue
        entrada = por_codigo.get((componente.product_code or "").upper())
        if entrada is None:
            entrada = _por_nombre(componente, inventario)
        if entrada is None:
            problemas.append(f"{componente.nombre_visible} no aparece instalado")
            continue
        detalles.append(f"instalado: {componente.id} {entrada.display_version}")
        esperada = componente.version_esperada
        if esperada and entrada.display_version and entrada.display_version != esperada:
            problemas.append(
                f"{componente.nombre_visible}: version {entrada.display_version}, "
                f"se esperaba {esperada}")

    # 2. Los componentes protegidos siguen instalados.
    for exclusion in ctx.config.exclusiones:
        estaba = exclusion.clave in ctx.excluidos_presentes
        sigue = exclusion.clave in por_codigo
        if estaba and not sigue:
            problemas.append(
                f"CRITICO: el componente protegido '{exclusion.producto}' ya no "
                f"esta instalado. Se esperaba que no fuera tocado.")
        elif estaba:
            ctx.log.info("  Componente protegido intacto: %s", exclusion.producto)
            detalles.append(f"protegido intacto: {exclusion.producto}")

    # 3. Las carpetas base existen y tienen contenido.
    version = str(ctx.config.version_base)
    for raiz in ctx.config.raices:
        objetivo = Path(raiz) / version
        if not objetivo.is_dir():
            detalles.append(f"no existe (puede ser normal): {objetivo}")
            continue
        if not _tiene_contenido(objetivo):
            problemas.append(f"la carpeta {objetivo} quedo vacia tras instalar")
        else:
            detalles.append(f"con contenido: {objetivo}")

    # 4. No quedan versiones superiores sin apartar.
    for raiz in ctx.config.raices:
        for hijo in _subcarpetas(Path(raiz)):
            if _SOLO_DIGITOS.match(hijo.name) and int(hijo.name) > ctx.config.version_base:
                problemas.append(
                    f"queda una version superior sin apartar: {hijo}")

    if problemas:
        for problema in problemas:
            ctx.log.warning("  %s", problema)
        return StageResult.advertencia(
            f"Validacion con {len(problemas)} observacion(es).",
            problemas + detalles)

    return StageResult.exito("Validacion correcta.", detalles)


def _por_nombre(componente, inventario):
    if not componente.producto:
        return None
    objetivo = " ".join(componente.producto.split()).casefold()
    vistas = ((registry.VISTA_64,) if componente.arquitectura == "x64"
              else (registry.VISTA_32,) if componente.arquitectura == "x86"
              else registry.VISTAS)
    for entrada in inventario:
        if entrada.vista in vistas and \
                " ".join(entrada.display_name.split()).casefold() == objetivo:
            return entrada
    return None


def _tiene_contenido(carpeta):
    try:
        return any(carpeta.iterdir())
    except OSError:
        return False


def _subcarpetas(raiz):
    try:
        return [p for p in raiz.iterdir() if p.is_dir()]
    except OSError:
        return []
