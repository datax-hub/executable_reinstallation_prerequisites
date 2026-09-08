# AnalyzeRepair

Herramienta de mantenimiento que automatiza la reparacion de los prerrequisitos de **DATAX Analyze**
en Windows: detiene el servicio, desinstala los componentes, limpia directorios, aparta versiones
incompatibles, reinstala y vuelve a levantar el servicio, dejando log de cada paso.

Implementa el requerimiento de `docs/requerimiento/` (RF-01 a RF-12).

## Estructura

```
AnalyzeRepair/
├── config.json              Parametros: servicio, rutas, componentes, exclusiones
├── src/analyzerepair/       Codigo fuente
│   ├── main.py              Orquestador del pipeline
│   ├── safety.py            Guard de rutas destructivas
│   ├── winapi/              Envoltorios ctypes de la API de Windows
│   └── stages/              Una etapa por requisito funcional (s01..s09)
├── Prerequisites/           Instaladores que la herramienta ejecuta
├── _no-usar/                Archivos excluidos a proposito (ver su LEEME.md)
├── docs/                    Requerimiento y manuales
├── tests/                   Pruebas
└── build/                   Empaquetado PyInstaller
```

## Desarrollo

Requiere **Python 3.12 de 32 bits** (un EXE x86 corre en Windows de 32 y 64 bits; al reves no).

```powershell
%LOCALAPPDATA%\Programs\Python\Python312-32\python.exe -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

Ejecutar sin tocar el sistema:

```powershell
python -m analyzerepair --dry-run
```

## Empaquetado

Hay dos variantes, para dos usos distintos.

### Todo en uno -- para entregar al tecnico

```powershell
pyinstaller build/AnalyzeRepair_TodoEnUno.spec
```

Produce `dist/AnalyzeRepair_TodoEnUno.exe` (~123 MB): un unico archivo con
`config.json` y los instaladores dentro. **Es el que se entrega**: se copia, se
hace doble clic y funciona. No hay carpetas que se puedan perder por el camino.
Arranca en 1-2 s (extrae a `%TEMP%`).

Los logs se escriben junto al EXE, nunca en la carpeta temporal, que Windows
borra al terminar.

### En carpeta -- para desarrollo y mantenimiento

```powershell
pyinstaller build/AnalyzeRepair.spec
```

Produce `dist/AnalyzeRepair.exe` (~6 MB) y necesita `config.json` y
`Prerequisites/` a su lado. Permite actualizar un MSI o ajustar la
configuracion sin recompilar. Si falta alguno de los dos, el programa avisa y
sale con codigo 1 sin tocar nada.

### Ajustar la configuracion sin recompilar

Un `config.json` colocado **junto al EXE** tiene prioridad sobre el embebido,
tambien en la variante todo en uno. Sirve para cambiar un timeout o una ruta en
un equipo concreto sin volver a compilar.

## Codigos de salida

| Codigo | Significado |
| --- | --- |
| 0 | Proceso completado correctamente |
| 1 | Error critico: proceso abortado |
| 2 | Sin privilegios administrativos |
| 3 | Completado con advertencias |
| 4 | Completado, requiere reiniciar Windows |
