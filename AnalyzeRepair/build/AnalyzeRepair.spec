# PyInstaller spec para AnalyzeRepair.
#
# config.json y Prerequisites/ quedan FUERA del binario, junto al EXE (RF-09):
# el ejecutable pesa poco, arranca al instante y se puede actualizar un MSI sin
# recompilar. config.ruta_base() resuelve esa carpeta con sys.executable.
#
# Uso:  pyinstaller build/AnalyzeRepair.spec

import os

RAIZ = os.path.abspath(os.path.join(os.getcwd()))
ORIGEN = os.path.join(RAIZ, "src")
ICONO = os.path.join(RAIZ, "build", "AnalyzeRepair.ico")

a = Analysis(
    [os.path.join(ORIGEN, "analyzerepair", "__main__.py")],
    pathex=[ORIGEN],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    # Solo se excluye lo que con seguridad no interviene. Nada de quitar
    # 'inspect' (lo usa dataclasses) ni 'pickle'/'socket' (los arrastra logging).
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
    name="AnalyzeRepair",
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
