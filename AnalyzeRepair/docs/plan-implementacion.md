# Plan de implementacion

## Fases

| Fase | Contenido | Estado |
| --- | --- | --- |
| 0 | Python 3.12 x86, estructura, config.json | **hecho** |
| 1 | `logger` · `config` · `winapi/paths` · `safety` + `--dry-run` | pendiente |
| 2 | `winapi/elevation` · `winapi/service` · `winapi/registry` · `s01` `s02` `s03` | pendiente |
| 3 | `s04` desinstalar · `s05` limpiar · `s06` versiones | pendiente |
| 4 | `s07` instalar · `s08` validar · `s09` servicio · `main` · `ui` | pendiente |
| 5 | PyInstaller + 7 escenarios de prueba | pendiente |
| 6 | Manual tecnico, manual de usuario, evidencias | pendiente |

## Trazabilidad requisito -> codigo

| RF | Modulo |
| --- | --- |
| RF-01 permisos | `winapi/elevation.py` + `stages/s01_admin.py` |
| RF-02 detener servicio | `winapi/service.py` + `stages/s02_service_stop.py` |
| RF-03 deteccion | `winapi/registry.py` + `stages/s03_detect.py` |
| RF-04 desinstalacion | `stages/s04_uninstall.py` |
| RF-05 limpieza | `stages/s05_cleanup.py` + `safety.py` |
| RF-06 versiones > 110 | `stages/s06_versions.py` + `safety.py` |
| RF-07 idioma del SO | `winapi/paths.py` |
| RF-08 32/64 bits | `winapi/paths.py` + `winapi/registry.py` |
| RF-09 instalacion | `stages/s07_install.py` |
| RF-10 validacion | `stages/s08_validate.py` |
| RF-11 iniciar servicio | `stages/s09_service_start.py` |
| RF-12 log | `logger.py` |
| Seccion 6 interfaz | `ui.py` |
| Seccion 8 seguridad | `safety.py` |
| Seccion 9 errores | `results.py` + `errors.py` |

## Los dos riesgos reales

**1. Redireccion WOW64.** El EXE se compila en 32 bits para correr en ambas arquitecturas. Pero un
proceso de 32 bits en Windows de 64 recibe `C:/Program Files (x86)` cuando pregunta por
`%ProgramFiles%`, y ve una rama distinta del registro. Sin tratarlo, la herramienta limpia las rutas
equivocadas y no detecta los productos de 64 bits.

Solucion en `winapi/paths.py`, por orden de preferencia:

1. Registro `HKLM/SOFTWARE/Microsoft/Windows/CurrentVersion`, valores `ProgramFilesDir` y
   `ProgramFilesDir (x86)`, abierto con **`KEY_WOW64_64KEY`**. Devuelve la ruta real, ya localizada
   al idioma del sistema: resuelve RF-07 y RF-08 de una sola vez.
2. Fallback: `SHGetKnownFolderPath` con `FOLDERID_ProgramFilesX64` / `FOLDERID_ProgramFilesX86`.
3. Nunca variables de entorno ni el literal "Program Files".

En Windows de 32 bits `ProgramFilesDir (x86)` no existe: se devuelve `None` y las etapas lo omiten
sin error (RF-08).

**2. Borrado con privilegios de administrador.** Un error al construir una ruta destruye el sistema.
`safety.py` valida antes de cada operacion destructiva: ruta normalizada con `resolve()`,
estrictamente contenida en una raiz permitida, distinta de la raiz misma, con profundidad minima,
existente, y con nombre que case el patron esperado. Si algo falla: excepcion, log y aborto de la
etapa. Nunca "seguir por si acaso".

`--dry-run` recorre el pipeline completo registrando lo que haria sin tocar nada. Es la red de
seguridad del desarrollo y la herramienta de diagnostico para soporte.

## Contrato de errores

Cada etapa devuelve `StageResult(ok, critical, message, details, requiere_reinicio)`.

- Etapa **critica** fallida: aborta, informa que fallo y que queda por hacer a mano.
- Etapa **no critica** fallida: advierte, continua, se refleja en el resumen final.

Codigos msiexec: `0` exito · `3010`/`1641` exito con reinicio pendiente (no es fallo) ·
`1605` no estaba instalado (informativo) · resto error.
