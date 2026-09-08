# Archivos deliberadamente fuera del alcance

Nada de esta carpeta debe entrar a `Prerequisites/` ni ser ejecutado por la herramienta.

## ADOMD.NET.msi
**Producto:** Microsoft ADOMD.NET 8.0
**ProductCode:** `{4877FB90-721E-49F3-8E89-9467CBA3686B}`

No se desinstala ni se instala. RF-04 del requerimiento lo marca como "No desinstalar", y el
responsable lo confirmo expresamente por tratarse de un componente sensible.

**Cuidado — son dos productos distintos con nombre parecido:**

| Instalador | Producto registrado | ProductCode | Trato |
| --- | --- | --- | --- |
| `ADOMD.NET.msi` | Microsoft ADOMD.NET **8.0** | `{4877FB90-...}` | **NO TOCAR** |
| `SQL_AS_ADOMDx86.msi` | Microsoft SQL Server 2012 ADOMD.NET | `{69ED3C12-...}` | desinstalar + reinstalar |
| `SQL_AS_ADOMDx64.msi` | Microsoft SQL Server 2012 ADOMD.NET | `{017C234E-...}` | desinstalar + reinstalar |

Un filtro por nombre que busque "ADOMD.NET" caza los tres. Por eso la deteccion (RF-03) discrimina
por **ProductCode**, no por DisplayName, y `config.json` declara el 8.0 en `exclusiones_absolutas`.

La version 8.0 corresponde a la carpeta `Microsoft.NET/ADOMD.NET/80`, que RF-06 conserva por ser
inferior a 110.

## Tipos de Cambio.cub
Archivo de datos de cubo. No es un prerrequisito.

## UpdateConsole.zip
DLLs .NET de la aplicacion Analyze; payload de `ActualizadorDll.exe`. Otro proceso, otro alcance.
