# PyInstaller spec para la variante TODO EN UNO.
#
# Un unico .exe que lleva dentro config.json y los instaladores. El tecnico lo
# copia, hace doble clic y funciona: no hay nada que descomprimir ni carpetas
# que se puedan perder por el camino.
#
# A cambio, cada arranque extrae ~106 MB a %TEMP% (10-20 s) y cambiar un MSI
# obliga a recompilar. Para desarrollo y mantenimiento use AnalyzeRepair.spec.
#
# Aunque los datos viajen dentro, un config.json colocado junto al EXE tiene
# prioridad sobre el embebido (ver config._localizar_config), asi que se pueden
# ajustar timeouts o rutas en un equipo concreto sin recompilar.
#
# Uso:  pyinstaller build/AnalyzeRepair_TodoEnUno.spec

import os

RAIZ = os.path.abspath(os.getcwd())
ORIGEN = os.path.join(RAIZ, "src")
ICONO = os.path.join(RAIZ, "build", "AnalyzeRepair.ico")

# ADOMD.NET.msi vive en _no-usar/ y NO se empaqueta a proposito: si no viaja
# dentro del ejecutable, ningun error de codigo puede llegar a ejecutarlo.
datos = [
    (os.path.join(RAIZ, "config.json"), "."),
    (os.path.join(RAIZ, "Prerequisites"), "Prerequisites"),
]

a = Analysis(
    [os.path.join(ORIGEN, "analyzerepair", "__main__.py")],
    pathex=[ORIGEN],
    binaries=[],
    datas=datos,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter", "unittest", "doctest", "pdb", "pydoc",
        "sqlite3", "multiprocessing", "asyncio", "xmlrpc",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AnalyzeRepair_TodoEnUno",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    uac_admin=True,          # RF-01: pide elevacion al arrancar
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICONO,
)
