"""RF-03. Deteccion de componentes instalados.

No se asume que el nombre del .msi coincida con el nombre registrado en Windows.
La identificacion se hace contra el registro, en ambas vistas WOW64.

Criterio de coincidencia, en orden:
  1. ProductCode exacto (el declarado en config.json).
  2. Nombre de producto exacto y normalizado, restringido a la vista del
     registro que corresponde a la arquitectura del componente.

Sobre ambos criterios se aplica un filtro duro: cualquier entrada cuyo
ProductCode figure en exclusiones_absolutas queda descartada SIEMPRE. Esa es la
salvaguarda que protege a Microsoft ADOMD.NET 8.0, cuyo nombre se parece al de
Microsoft SQL Server 2012 ADOMD.NET pero es un producto distinto.
"""

from __future__ import annotations

from ..results import StageResult
from ..winapi import registry

NOMBRE = "Detectando componentes instalados"
CRITICA = False


def _normalizar(texto):
    return " ".join((texto or "").split()).casefold()


def _vistas_de(componente):
    if componente.arquitectura == "x64":
        return (registry.VISTA_64,)
    if componente.arquitectura == "x86":
        return (registry.VISTA_32,)
    return registry.VISTAS


def ejecutar(ctx):
    inventario = registry.inventario()
    ctx.log.debug("Entradas de desinstalacion encontradas: %d", len(inventario))

    detalles = []

    # --- Exclusiones: se localizan primero para poder vigilarlas al final -----
    ctx.excluidos_presentes = {}
    for exclusion in ctx.config.exclusiones:
        for entrada in inventario:
            if (entrada.product_code or "").upper() == exclusion.clave:
                ctx.excluidos_presentes[exclusion.clave] = entrada
                ctx.log.info("PROTEGIDO: %s -- no se tocara. Motivo: %s",
                             entrada, exclusion.motivo)
                detalles.append(f"PROTEGIDO {entrada.display_name} "
                                f"{entrada.display_version}")
                break

    # --- Componentes de la lista blanca --------------------------------------
    encontrados = {}
    for componente in ctx.config.componentes_aplicables(ctx.so_64bits):
        entrada = _buscar(componente, inventario, ctx)
        if entrada is None:
            ctx.log.info("%s: no instalado.", componente.nombre_visible)
            detalles.append(f"no instalado: {componente.id}")
            continue
        encontrados[componente.id] = entrada
        ctx.log.info("%s detectado: version %s, vista %s, %s",
                     componente.nombre_visible,
                     entrada.display_version or "(sin version)",
                     registry.nombre_vista(entrada.vista),
                     entrada.product_code or entrada.clave)
        detalles.append(f"detectado: {componente.id} {entrada.display_version}")

    ctx.detectados = encontrados
    return StageResult.exito(
        f"{len(encontrados)} de {len(ctx.config.componentes_aplicables(ctx.so_64bits))} "
        f"componente(s) presentes; {len(ctx.excluidos_presentes)} protegido(s).",
        detalles)


def _buscar(componente, inventario, ctx):
    """Localiza la entrada del registro correspondiente al componente."""
    codigo_esperado = (componente.product_code or "").upper()

    # 1. ProductCode exacto.
    if codigo_esperado:
        for entrada in inventario:
            if (entrada.product_code or "").upper() != codigo_esperado:
                continue
            if _descartar_por_exclusion(entrada, ctx):
                continue
            return entrada

    # 2. Nombre exacto, limitado a la vista propia de la arquitectura.
    if componente.producto:
        objetivo = _normalizar(componente.producto)
        vistas = _vistas_de(componente)
        for entrada in inventario:
            if entrada.vista not in vistas:
                continue
            if _normalizar(entrada.display_name) != objetivo:
                continue
            if _descartar_por_exclusion(entrada, ctx):
                continue
            ctx.log.debug(
                "%s localizado por nombre (ProductCode %s difiere del esperado %s)",
                componente.id, entrada.product_code, componente.product_code)
            return entrada

    return None


def _descartar_por_exclusion(entrada, ctx):
    """Barrera final: nada que este excluido llega jamas a la lista de trabajo."""
    exclusion = ctx.config.esta_excluido(entrada.product_code)
    if exclusion is None:
        return False
    ctx.log.warning(
        "Se descarta '%s' por coincidir con una exclusion absoluta (%s).",
        entrada.display_name, exclusion.producto)
    return True
