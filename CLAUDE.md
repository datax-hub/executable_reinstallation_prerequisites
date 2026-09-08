# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Que es esto

`AnalyzeRepair/` es una herramienta Windows en Python 3 que automatiza la reparacion de los
prerrequisitos de DATAX Analyze: detiene el servicio, desinstala componentes, limpia directorios,
aparta versiones incompatibles, reinstala y vuelve a levantar el servicio.

El requerimiento (RF-01 a RF-12) esta en `AnalyzeRepair/docs/requerimiento/`. El `.docx` es la fuente
de verdad: **el `.md` tiene las rutas corrompidas** (donde dice `AS OLEDBH` el original dice
`AS OLEDB/110/`). Todo el proyecto -- UI, logs, documentacion -- esta en espanol.

Existe una implementacion previa ya compilada, `../Actualizador_PrerrequisitosAnalyze2026.exe`
(PyInstaller onefile, sin fuente disponible), y los logs de su corrida del 2026-08-25 en `../*.log`.
Son la mejor evidencia del comportamiento esperado; `../desinstalacion_sql2012.log` resume el pipeline
completo. Este proyecto es una reimplementacion desde la especificacion, no un parche a ese EXE.

## Comandos

Python 3.12 **de 32 bits** en `%LOCALAPPDATA%/Programs/Python/Python312-32/python.exe`. La
arquitectura no es negociable: un EXE x86 corre en Windows de 32 y 64 bits; al reves no.

```powershell
python -m analyzerepair --dry-run      # recorre el pipeline sin tocar el sistema
python -m analyzerepair --solo-detectar
pytest tests/                          # pruebas
pytest tests/test_safety.py -k nombre  # una sola prueba
pyinstaller build/AnalyzeRepair_TodoEnUno.spec   # EXE que se entrega (~123 MB)
pyinstaller build/AnalyzeRepair.spec             # EXE en carpeta (~6 MB, desarrollo)
```

Dos variantes de empaquetado. La **todo en uno** lleva config.json y los
instaladores dentro y es la que se entrega al tecnico. La **en carpeta** los
necesita a su lado y sirve para iterar sin recompilar 123 MB. Un config.json
junto al EXE gana siempre al embebido (`config._localizar_config`), y los logs
se escriben junto al EXE, nunca en `_MEIPASS`, que Windows borra al salir.

`--dry-run` es la herramienta principal de desarrollo: sin ella cada iteracion exige restaurar una VM.

## Arquitectura

Un modulo por requisito funcional; la trazabilidad RF -> archivo esta en
`AnalyzeRepair/docs/plan-implementacion.md`.

- `src/analyzerepair/stages/s01..s09` -- las etapas, en orden de ejecucion. Cada una expone
  `ejecutar(ctx) -> StageResult` y no sabe nada de las demas.
- `src/analyzerepair/winapi/` -- envoltorios ctypes de la API de Windows. **Sin dependencias
  externas**: nada de pywin32 (infla el EXE y complica el empaquetado).
- `src/analyzerepair/safety.py` -- guard de rutas. Toda operacion destructiva pasa por aqui.
- `config.json` -- externo al EXE, junto a `Prerequisites/`.

Pipeline: permisos -> detener servicio -> detectar -> desinstalar -> limpiar `110/` ->
renombrar `>110` -> instalar -> validar -> iniciar servicio.

Etapa critica fallida aborta el proceso; no critica advierte y continua. Codigos de salida:
`0` OK, `1` critico, `2` sin permisos, `3` advertencias, `4` requiere reinicio.

## Lista blanca verificada

ProductCode y version leidos de la tabla `Property` de cada MSI, no copiados del documento.
Viven en `config.json`; esta tabla es solo referencia.

| Instalador | Producto registrado | ProductCode | Orden |
| --- | --- | --- | --- |
| `msxml6_x86.msi` | MSXML 6.0 Parser | `{A43BF6A5-D5F0-4AAA-BF41-65995063EC44}` | 1 |
| `owc11.msi` | Microsoft Office 2003 Web Components | `{90120000-00A4-0C0A-0000-0000000FF1CE}` | 2 |
| `SQL_AS_OLEDBx86.msi` | Microsoft AS OLE DB Provider for SQL Server 2012 | `{24AEC213-B7FC-46CB-9ACF-505C9C907757}` | 3 |
| `SQL_AS_OLEDBx64.msi` | Microsoft AS OLE DB Provider for SQL Server 2012 | `{2E333525-6784-4819-BE44-5A2794012B17}` | 4 |
| `SQL_AS_ADOMDx86.msi` | Microsoft SQL Server 2012 ADOMD.NET | `{69ED3C12-58E2-4447-964F-D6C6EEAE176D}` | 5 |
| `SQL_AS_ADOMDx64.msi` | Microsoft SQL Server 2012 ADOMD.NET | `{017C234E-38C6-4A64-88EF-2C2A7D71FEED}` | 6 |

x86 siempre antes que x64. `SQL_AS_OLEDB*` **no aparece en la tabla de la seccion 4 del
requerimiento**, pero el procedimiento real los instala y desinstala: la tabla esta incompleta.

`ptslite.exe` esta en `config.json` con `habilitado: false`. Es un stub InstallShield
(`OriginalFilename=stub32i.exe`) sin metadata ni ProductCode; sus switches silenciosos deben
descubrirse empiricamente en VM antes de activarlo.

## Invariantes

- **Microsoft ADOMD.NET 8.0 `{4877FB90-721E-49F3-8E89-9467CBA3686B}` no se toca jamas** -- ni
  detectar para desinstalar, ni instalar. Es un producto **distinto** de "Microsoft SQL Server 2012
  ADOMD.NET" pese al nombre parecido; un filtro por DisplayName que busque "ADOMD.NET" caza a los
  tres. Por eso la deteccion discrimina por **ProductCode**, nunca por nombre. Su instalador esta
  fuera de `Prerequisites/`, en `_no-usar/`. Ver `AnalyzeRepair/_no-usar/LEEME.md`.
- **Rutas del sistema resueltas via registro con `KEY_WOW64_64KEY`**, nunca variables de entorno ni
  el literal "Program Files". Un proceso de 32 bits en Windows de 64 sufre redireccion WOW64 y leeria
  las rutas y la rama de registro equivocadas. Esto resuelve RF-07 (espanol/ingles) y RF-08 (32/64)
  a la vez. En 32 bits `ProgramFilesDir (x86)` no existe: devolver `None` y omitir, sin error.
- **El registro se recorre en ambas vistas** (`KEY_WOW64_64KEY` y `KEY_WOW64_32KEY`).
- **Limpiar = vaciar el contenido, no borrar la carpeta**, y solo dentro de
  `{ProgramFiles,ProgramFilesX86}/Microsoft Analysis Services/AS OLEDB/110/` y
  `{...}/Microsoft.NET/ADOMD.NET/110/`.
- **Renombrado `>110`**: subcarpetas `^[0-9]+$` mayores a 110 pasan a `_NNN`. **110 y las inferiores
  se conservan** (el log real muestra `[OK - se conserva] 80`). Idempotente: `_140` ya existente no
  falla. Corre *despues* de desinstalar, asi que las carpetas de productos ya desinstalados no estan.
- **`3010` y `1641` de msiexec son exito con reinicio pendiente**, no fallo. `1605` = no instalado.
- **Fallar ruidosamente.** Ninguna operacion critica falla en silencio.

## Nota de entorno

El proyecto vive en OneDrive. Excluir `.venv/`, `logs/` y `build/dist/` del sync si da problemas.

Al escribir archivos con heredocs de bash, **las barras invertidas se colapsan** y algunas secuencias se interpretan como escapes. Escribir esos archivos con Python o con la herramienta Write, no con heredoc.
