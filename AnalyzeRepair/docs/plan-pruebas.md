# Plan de pruebas

Los escenarios 1, 2, 3, 5 y 7 destruyen el estado del equipo: ejecutar en VM **con snapshot** y
revertir entre pruebas. Los escenarios 4 y 6 no lo necesitan.

| # | Escenario | Como montarlo | Se espera |
| --- | --- | --- | --- |
| 1 | Windows 64 bits completo | VM Win10/11 x64, prerrequisitos instalados, carpetas > 110 presentes | Servicio detenido, componentes desinstalados, carpetas 110 vaciadas, > 110 renombradas, reinstalacion, servicio iniciado |
| 2 | Windows 32 bits | VM Win10 x86 | Ausencia de `Program Files (x86)` no genera error; los MSI x64 se omiten |
| 3 | Componentes no instalados | VM limpia | Deteccion informa "no instalado", no falla, instala igualmente |
| 4 | Servicio ya detenido | Detener el servicio a mano antes | Informa el estado y continua |
| 5 | Error de instalacion | Reemplazar un MSI por uno corrupto | Reporta el codigo de error, aborta, no dice "correcto" |
| 6 | Sin permisos | Ejecutar como usuario estandar | Solicita elevacion por UAC; si se cancela, sale con codigo 2 sin tocar nada |
| 7 | Versiones superiores | Crear carpetas `110 120 130 140 150` a mano | `110` intacta, resto renombradas a `_120 _130 _140 _150` |

Complementarias:

| # | Escenario | Se espera |
| --- | --- | --- |
| 8 | Windows en espanol | Resuelve `Archivos de programa` correctamente (RF-07) |
| 9 | `--dry-run` | No modifica nada; el log describe todas las acciones previstas |
| 10 | Archivo bloqueado en carpeta 110 | Reintenta, registra el archivo, no aborta |
| 11 | Doble ejecucion seguida | Idempotente: `_140` ya existente no provoca error (RF-06) |
| 12 | ADOMD.NET 8.0 instalado | **Permanece intacto** tras el proceso completo |

La prueba 12 es la mas importante en terminos de riesgo: verifica que la exclusion por ProductCode
funciona y que el componente sensible nunca se toca.
