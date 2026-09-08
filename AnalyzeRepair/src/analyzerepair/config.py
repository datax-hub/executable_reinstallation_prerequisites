"""Carga y validacion de config.json.

Falla temprano y con mensaje claro: es preferible no arrancar a arrancar con una
configuracion incompleta y descubrirlo a mitad de una desinstalacion.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .errors import ConfigInvalida
from .winapi import paths

_GUID = re.compile(r"^\{[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}\}$")


def ruta_base():
    """Carpeta donde se buscan config.json y Prerequisites/.

    Empaquetado: junto al EXE. Desde fuente: la raiz del proyecto.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def ruta_embebida():
    """Carpeta temporal donde PyInstaller extrae los datos embebidos.

    Solo existe en la variante todo-en-uno. Devuelve None en los demas casos.
    """
    interna = getattr(sys, "_MEIPASS", None)
    return Path(interna) if interna else None


def ruta_salida():
    """Carpeta donde SE ESCRIBE (logs).

    Nunca puede ser la carpeta embebida: Windows la borra al terminar el
    proceso y el tecnico se quedaria sin el log justo cuando lo necesita.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _localizar_config(ruta):
    """Orden de busqueda del config.json.

    Un config.json colocado junto al EXE gana siempre al embebido: permite
    ajustar timeouts o rutas en un equipo concreto sin recompilar nada.
    """
    if ruta:
        return Path(ruta).resolve()

    externo = ruta_base() / "config.json"
    if externo.is_file():
        return externo

    embebido = ruta_embebida()
    if embebido is not None and (embebido / "config.json").is_file():
        return embebido / "config.json"

    return externo


@dataclass
class Componente:
    id: str
    orden: int
    archivo: str
    tipo: str
    producto: str | None
    product_code: str | None
    version_esperada: str | None
    arquitectura: str
    desinstalar: bool
    instalar: bool
    habilitado: bool
    args_instalacion: list[str] = field(default_factory=list)
    nota: str | None = None

    @property
    def nombre_visible(self):
        return self.producto or self.archivo

    def aplica_a(self, so_64bits):
        if not self.habilitado:
            return False
        if self.arquitectura == "x64":
            return so_64bits
        return True


@dataclass
class Exclusion:
    producto: str
    product_code: str
    motivo: str
    nunca_desinstalar: bool = True
    nunca_instalar: bool = True

    @property
    def clave(self):
        return (self.product_code or "").upper()


@dataclass
class Config:
    ruta: Path
    base: Path
    servicio_nombre: str
    servicio_timeout_detener: int
    servicio_timeout_iniciar: int
    servicio_si_no_existe: str
    version_base: int
    raices: list[Path]
    raices_omitidas: list[str]
    exclusiones: list[Exclusion]
    componentes: list[Componente]
    msiexec: dict
    limpieza: dict
    log: dict

    @property
    def carpeta_instaladores(self):
        return self.base / "Prerequisites"

    @property
    def carpeta_logs(self):
        # Junto al EXE, nunca en la carpeta embebida: esa la borra Windows.
        return ruta_salida() / self.log.get("carpeta", "logs")

    @property
    def es_todo_en_uno(self):
        embebida = ruta_embebida()
        return embebida is not None and self.base == embebida

    def componentes_aplicables(self, so_64bits):
        activos = [c for c in self.componentes if c.aplica_a(so_64bits)]
        return sorted(activos, key=lambda c: c.orden)

    def esta_excluido(self, product_code):
        if not product_code:
            return None
        clave = product_code.upper()
        for exclusion in self.exclusiones:
            if exclusion.clave == clave:
                return exclusion
        return None


def cargar(ruta=None):
    # La carpeta base es la que contiene config.json: junto al EXE en el
    # despliegue en carpeta, o la carpeta embebida en la variante todo-en-uno.
    # Pasar --config permite apuntar a otro despliegue completo
    # (config.json + Prerequisites/) sin duplicar los instaladores.
    ruta = _localizar_config(ruta)
    base = ruta.parent

    if not ruta.is_file():
        raise ConfigInvalida(
            f"No se encontro el archivo de configuracion: {ruta}\n"
            f"El ejecutable necesita config.json y la carpeta Prerequisites "
            f"junto a el.")

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigInvalida(f"config.json tiene un error de sintaxis: {exc}") from exc
    except OSError as exc:
        raise ConfigInvalida(f"No se pudo leer config.json: {exc}") from exc

    problemas = validar(datos)
    if problemas:
        raise ConfigInvalida(
            "config.json no es valido:\n  - " + "\n  - ".join(problemas))

    servicio = datos["servicio"]
    raices, omitidas = _expandir_raices(datos["raices_componentes"])

    return Config(
        ruta=ruta,
        base=base,
        servicio_nombre=servicio["nombre"],
        servicio_timeout_detener=int(servicio.get("timeout_detener_segundos", 60)),
        servicio_timeout_iniciar=int(servicio.get("timeout_iniciar_segundos", 90)),
        servicio_si_no_existe=servicio.get("si_no_existe", "advertir"),
        version_base=int(datos["version_base"]),
        raices=raices,
        raices_omitidas=omitidas,
        exclusiones=[_exclusion(e) for e in datos.get("exclusiones_absolutas", [])],
        componentes=[_componente(c) for c in datos["componentes"]],
        msiexec=datos.get("msiexec", {}),
        limpieza=datos.get("limpieza", {}),
        log=datos.get("log", {}),
    )


def _expandir_raices(plantillas):
    """Expande las plantillas; las que no aplican se omiten SIN error (RF-08)."""
    raices, omitidas = [], []
    for plantilla in plantillas:
        expandida = paths.expandir(plantilla)
        if expandida is None:
            omitidas.append(str(plantilla))
        else:
            raices.append(expandida)
    return raices, omitidas


def _componente(datos):
    return Componente(
        id=datos["id"],
        orden=int(datos["orden"]),
        archivo=datos["archivo"],
        tipo=datos.get("tipo", "msi"),
        producto=datos.get("producto"),
        product_code=datos.get("product_code"),
        version_esperada=datos.get("version_esperada"),
        arquitectura=datos.get("arquitectura", "any"),
        desinstalar=bool(datos.get("desinstalar", False)),
        instalar=bool(datos.get("instalar", False)),
        habilitado=bool(datos.get("habilitado", True)),
        args_instalacion=list(datos.get("args_instalacion", [])),
        nota=datos.get("nota"),
    )


def _exclusion(datos):
    return Exclusion(
        producto=datos.get("producto", "(sin nombre)"),
        product_code=datos.get("product_code", ""),
        motivo=datos.get("motivo", ""),
        nunca_desinstalar=bool(datos.get("nunca_desinstalar", True)),
        nunca_instalar=bool(datos.get("nunca_instalar", True)),
    )


def validar(datos):
    """Devuelve la lista de problemas encontrados. Vacia = configuracion valida."""
    problemas = []

    for clave in ("servicio", "version_base", "raices_componentes", "componentes"):
        if clave not in datos:
            problemas.append(f"falta la clave obligatoria '{clave}'")
    if problemas:
        return problemas

    if not isinstance(datos["servicio"], dict) or not datos["servicio"].get("nombre"):
        problemas.append("servicio.nombre es obligatorio")

    try:
        int(datos["version_base"])
    except (TypeError, ValueError):
        problemas.append("version_base debe ser un numero entero")

    if not isinstance(datos["raices_componentes"], list) or not datos["raices_componentes"]:
        problemas.append("raices_componentes debe ser una lista no vacia")

    vistos_id, vistos_orden = set(), set()
    for indice, comp in enumerate(datos.get("componentes", [])):
        etiqueta = comp.get("id", f"#{indice}")
        for clave in ("id", "orden", "archivo"):
            if clave not in comp:
                problemas.append(f"componente {etiqueta}: falta '{clave}'")
        if comp.get("id") in vistos_id:
            problemas.append(f"componente {etiqueta}: id duplicado")
        vistos_id.add(comp.get("id"))
        if comp.get("orden") in vistos_orden:
            problemas.append(f"componente {etiqueta}: orden duplicado")
        vistos_orden.add(comp.get("orden"))
        if comp.get("arquitectura") not in ("any", "x86", "x64", None):
            problemas.append(
                f"componente {etiqueta}: arquitectura debe ser any, x86 o x64")
        codigo = comp.get("product_code")
        if codigo and not _GUID.match(codigo):
            problemas.append(f"componente {etiqueta}: product_code mal formado")

    for indice, exc in enumerate(datos.get("exclusiones_absolutas", [])):
        codigo = exc.get("product_code")
        if not codigo or not _GUID.match(codigo):
            problemas.append(
                f"exclusion #{indice}: product_code obligatorio y bien formado")

    # Un componente jamas puede estar tambien en la lista de exclusiones.
    excluidos = {
        (e.get("product_code") or "").upper()
        for e in datos.get("exclusiones_absolutas", [])
    }
    for comp in datos.get("componentes", []):
        codigo = (comp.get("product_code") or "").upper()
        if codigo and codigo in excluidos:
            problemas.append(
                f"componente {comp.get('id')}: su product_code esta en "
                f"exclusiones_absolutas; no puede estar en ambas listas")

    return problemas
