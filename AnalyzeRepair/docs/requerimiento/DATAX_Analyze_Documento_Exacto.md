# Mantenimiento y reinstalación de prerrequisitos de DATAX Analyze

## 1. Título del requerimiento
Desarrollo de ejecutable para desinstalación, limpieza y reinstalación automatizada de prerrequisitos de DATAX Analyze

## 2. Descripción general
DATAX Analyze es una aplicación desarrollada para sistemas operativos Windows que requiere la instalación previa de determinados componentes y librerías para funcionar correctamente.
Actualmente, cuando se presentan problemas relacionados con estos componentes, el proceso de mantenimiento requiere realizar manualmente la detención de servicios, desinstalación de programas, eliminación de carpetas y reinstalación de los prerrequisitos.
Se requiere desarrollar una herramienta ejecutable para Windows, utilizando Python, que permita automatizar este procedimiento de manera controlada, reduciendo el tiempo de soporte y evitando errores durante la intervención manual.
La herramienta deberá ejecutarse con permisos administrativos y realizar las operaciones necesarias en el orden establecido.

## 3. Objetivo general
Desarrollar un ejecutable para Windows que permita realizar de manera automática el proceso de:
*   Detención del servicio de DATAX Analyze.
*   Detección y desinstalación de los prerrequisitos existentes.
*   Limpieza de archivos y directorios relacionados.
*   Renombrado de versiones superiores de determinados componentes.
*   Instalación nuevamente de los prerrequisitos requeridos.
*   Inicio del servicio de DATAX Analyze.
*   Generación de información/logs que permita verificar el resultado de cada operación.

## 4. Prerrequisitos involucrados
La herramienta deberá trabajar con los siguientes componentes:

| Componente | Acción |
| :--- | :--- |
| ADOMD.NET.msi *** | No desinstalar |
| msxml6_x86.msi | Desinstalar y reinstalar |
| owc11.msi | Desinstalar y reinstalar |
| ptslite.exe | Desinstalar/reinstalar según procedimiento definido |
| SQL_AS_ADOMDx64.msi | Desinstalar y reinstalar |
| SQL_AS_ADOMDx86.msi | Desinstalar y reinstalar |

La herramienta deberá identificar correctamente los productos instalados en Windows. No deberá asumir que el nombre del archivo .msi corresponde exactamente al nombre con el que aparece registrado en Windows.
*** ADOMD.NET.msi creo q es mejor omitirlo 

## 5. Requerimientos funcionales

### RF-01. Verificación de permisos
Al iniciar, el programa deberá verificar si está siendo ejecutado con privilegios de administrador.
Si no posee los permisos necesarios, deberá:
*   Informar al usuario.
*   Solicitar la elevación de privilegios mediante UAC o indicar que debe ejecutarse como administrador.
*   No iniciar el proceso de mantenimiento hasta contar con los permisos requeridos.

### RF-02. Detención del servicio
La primera operación deberá ser detener el servicio:
`Datax.Analyze.service`
El programa deberá:
*   Verificar si el servicio existe.
*   Verificar su estado actual.
*   Detenerlo si está iniciado.
*   Esperar y comprobar que efectivamente se encuentre detenido.
*   Informar si la operación fue exitosa.
*   Registrar cualquier error.
Si el servicio no existe, la herramienta deberá informar esta situación y determinar, según el diseño definido, si puede continuar con el proceso.

### RF-03. Detección de componentes instalados
La herramienta deberá buscar en Windows los componentes relacionados con los prerrequisitos de Analyze.
El pasante deberá investigar y determinar el mecanismo más seguro para realizar esta identificación, pudiendo utilizar, entre otros:
*   Registro de Windows.
*   Windows Installer.
*   msiexec.
*   PowerShell.
*   WMI/CIM, cuando corresponda.
*   Otros mecanismos propios de Windows.
No se deberá basar únicamente en la existencia física de un archivo .msi.

### RF-04. Desinstalación de prerrequisitos
Se deberán desinstalar los componentes definidos, exceptuando ADOMD.NET.
La herramienta deberá:
*   Identificar si el componente está instalado.
*   Obtener su información de instalación.
*   Ejecutar el proceso de desinstalación de manera silenciosa, cuando sea posible.
*   Esperar a que finalice el proceso.
*   Validar el código de retorno.
*   Registrar el resultado.
La herramienta no deberá desinstalar componentes que no correspondan a los prerrequisitos definidos.

### RF-05. Limpieza de directorios
Después de la desinstalación, se deberán revisar y limpiar las siguientes ubicaciones:
*   `C:\Program Files\Microsoft Analysis Services\AS OLEDBH\`
*   `C:\Program Files\Microsoft.NET\ADOMD.NETH\`
*   `C:\Program Files (x86)\Microsoft Analysis Services\AS OLEDBH\`
*   `C:\Program Files (x86)\Microsoft.NET\ADOMD.NETH\`

La herramienta deberá:
*   Verificar si las carpetas existen.
*   Eliminar su contenido.
*   Manejar correctamente archivos bloqueados o protegidos.
*   Registrar los archivos/directorios que no pudieron eliminarse.
*   No generar errores si una carpeta no existe.

### RF-06. Manejo de versiones superiores a 110
Se deberá realizar una búsqueda de versiones superiores a 110 dentro de las rutas relacionadas con:
*   Microsoft Analysis Services\AS OLEDB
*   Microsoft.NET\ADOMD.NET

Por ejemplo, si existe:
`C:\Program Files (x86)\Microsoft.NET\ADOMD.NET``
la herramienta deberá cambiar su nombre a:
`C:\Program Files (x86)\Microsoft.NET\ADOMD.NET\_140`

El mismo criterio deberá aplicarse para otras versiones superiores a 110.
Ejemplos:
*   120 → _120
*   130 → _130
*   140 → _140
*   150 → _150
*   160 → _160

El objetivo es evitar que versiones superiores interfieran con los componentes requeridos por Analyze, manteniendo temporalmente la carpeta original mediante el prefijo _.

### RF-07. Compatibilidad con Windows en español e inglés
La herramienta deberá funcionar independientemente del idioma del sistema operativo.
Por ejemplo:
Windows en inglés:
*   `C:\Program Files\`
*   `C:\Program Files (x86)\`

Windows en español:
*   `C:\Archivos de programa\`
*   `C:\Archivos de programa (x86)\`

Se recomienda que el pasante investigue el mecanismo adecuado para obtener mediante Windows las rutas reales de las carpetas del sistema, en lugar de depender exclusivamente de textos como Program Files o Archivos de programa.

### RF-08. Compatibilidad con sistemas de 32 y 64 bits
La aplicación deberá identificar la arquitectura del sistema operativo.
Deberá contemplar al menos:
*   Windows de 32 bits.
*   Windows de 64 bits.

En sistemas de 32 bits puede no existir:
`Program Files (x86)`
La ausencia de esta carpeta no deberá generar un error.
En sistemas de 64 bits deberán revisarse tanto las ubicaciones de 64 bits como las correspondientes a componentes de 32 bits.

### RF-09. Instalación de prerrequisitos
Una vez finalizada la limpieza, la herramienta deberá instalar nuevamente los prerrequisitos requeridos.
Los instaladores deberán estar incluidos dentro de una estructura definida para la herramienta, por ejemplo:
```text
AnalyzeRepair│
├── AnalyzeRepair.exe
│
└── Prerequisites    ├── msxml6_x86.msi
    ├── owc11.msi
    ├── ptslite.exe
    ├── SQL_AS_ADOMDx64.msi
    ├── SQL_AS_ADOMDx86.msi
    └── ADOMD.NET.msi
```
El instalador deberá determinar qué componentes corresponden al sistema operativo y ejecutar únicamente los instaladores necesarios.
Importante: ADOMD.NET.msi no deberá ser desinstalado durante la etapa de limpieza. Si se requiere reinstalarlo, deberá definirse previamente con el responsable técnico, ya que el requerimiento establece expresamente que no debe desinstalarse.

### RF-10. Validación posterior a la instalación
Después de instalar los prerrequisitos, la herramienta deberá realizar una validación.
Como mínimo deberá comprobar:
*   Que los procesos de instalación finalizaron correctamente.
*   Que los componentes esperados se encuentran instalados.
*   Que las carpetas requeridas existen.
*   Que las versiones encontradas son las esperadas.
*   Que no quedaron componentes incompatibles que puedan interferir con Analyze.

### RF-11. Inicio del servicio
Una vez finalizado correctamente el proceso, se deberá iniciar:
`Datax.Analyze.service`
La herramienta deberá:
*   Ejecutar el inicio del servicio.
*   Esperar a que Windows confirme que está iniciado.
*   Validar el estado final.
*   Informar al usuario si el servicio inició correctamente.

### RF-12. Registro de operaciones
La aplicación deberá generar un archivo de log que permita conocer qué operaciones fueron realizadas.
Por ejemplo:
```text
[10:15:01] Inicio del proceso.
[10:15:02] Permisos administrativos verificados.
[10:15:03] Servicio Datax.Analyze.service detenido.
[10:15:05] SQL_AS_ADOMDx64 detectado.
[10:15:08] SQL_AS_ADOMDx64 desinstalado correctamente.
[10:15:10] Carpeta ADOMD.NETH encontrada.
[10:15:11] Contenido eliminado.
[10:15:15] Carpeta ADOMD.NET` renombrada a _140.
[10:15:20] Instalación de SQL_AS_ADOMDx64 iniciada.
[10:15:45] Instalación completada.
[10:15:50] Servicio Datax.Analyze.service iniciado.
[10:15:52] Proceso finalizado correctamente.
```
El log deberá registrar también los errores encontrados.

## 6. Interfaz de usuario
La herramienta no requiere inicialmente una interfaz gráfica compleja.
Se puede desarrollar una interfaz sencilla que muestre el avance del proceso, por ejemplo:
```text
========================================
 DATAX ANALYZE - REPARACIÓN
========================================
[OK] Verificando permisos administrativos
[OK] Deteniendo servicio
[OK] Detectando componentes instalados
[OK] Desinstalando prerrequisitos
[OK] Limpiando archivos
[OK] Revisando versiones superiores
[OK] Instalando prerrequisitos
[OK] Validando instalación
[OK] Iniciando servicio
========================================
 PROCESO FINALIZADO CORRECTAMENTE
========================================
```
Como mejora opcional, se podrá desarrollar una interfaz gráfica utilizando tecnologías disponibles en Python, por ejemplo Tkinter.

## 7. Requerimientos técnicos
El desarrollo deberá considerar:
*   Python 3.x.
*   Windows 10 y Windows 11.
*   Arquitecturas de 32 y 64 bits.
*   Ejecución con privilegios administrativos.
*   Manejo de procesos de Windows.
*   Manejo de servicios de Windows.
*   Manejo del Registro de Windows.
*   Ejecución de instaladores MSI y EXE.
*   Manejo de códigos de retorno.
*   Manejo de errores y excepciones.
*   Generación de archivos de log.
*   Empaquetado del proyecto como .exe.

Se deberá investigar la utilización de herramientas como PyInstaller para generar un ejecutable que pueda distribuirse a los equipos donde se encuentra instalado Analyze, evitando requerir una instalación independiente de Python.

## 8. Seguridad y precauciones
Debido a que la herramienta realizará operaciones administrativas sobre Windows, deberá implementarse con especial cuidado.
El programa deberá:
*   Solicitar privilegios administrativos.
*   No eliminar archivos fuera de las rutas definidas.
*   Validar las rutas antes de ejecutar operaciones destructivas.
*   Evitar eliminar carpetas completas cuando únicamente se requiere eliminar su contenido.
*   Registrar todas las operaciones realizadas.
*   Manejar adecuadamente errores de permisos.
*   Evitar continuar silenciosamente cuando una operación crítica falle.
*   Informar al usuario cuando sea necesaria una intervención manual.

Antes de realizar operaciones destructivas, se recomienda implementar una validación de las rutas objetivo para evitar errores derivados de rutas incorrectamente construidas.

## 9. Manejo de errores
La herramienta deberá contemplar, como mínimo, los siguientes escenarios:
*   El servicio no existe.
*   El servicio no puede detenerse.
*   El servicio no puede iniciarse.
*   Un programa no está instalado.
*   Un programa no puede desinstalarse.
*   El instalador MSI no existe.
*   El instalador devuelve un código de error.
*   Existen archivos bloqueados.
*   No existen las carpetas objetivo.
*   El usuario no posee permisos administrativos.
*   El sistema operativo es de 32 bits.
*   No existe Program Files (x86).
*   Existe una versión superior a 110.
*   Se requiere reiniciar Windows.
*   Un componente queda instalado parcialmente.

La herramienta deberá evitar quedar en un estado indefinido y deberá informar claramente qué operación falló.

## 10. Pruebas requeridas
El pasante deberá preparar un plan de pruebas que contemple diferentes escenarios.

**Prueba 1 – Windows 64 bits**
Equipo con:
*   Windows 10/11 de 64 bits.
*   Todos los prerrequisitos instalados.
*   Versiones superiores a 110 existentes.
Validar que:
*   Se detiene el servicio.
*   Se desinstalan los componentes correspondientes.
*   Se limpian las carpetas.
*   Se renombran las versiones superiores.
*   Se reinstalan los prerrequisitos.
*   Se inicia el servicio.

**Prueba 2 – Windows 32 bits**
Validar que la ausencia de:
`Program Files (x86)`
no genere errores.

**Prueba 3 – Componentes no instalados**
Ejecutar la herramienta en un equipo donde algunos prerrequisitos no estén instalados.

**Prueba 4 – Servicio detenido**
Ejecutar la herramienta cuando Datax.Analyze.service ya se encuentre detenido.

**Prueba 5 – Error de instalación**
Simular o provocar un error durante la instalación de uno de los prerrequisitos y validar que el programa informe correctamente la situación.

**Prueba 6 – Falta de permisos**
Ejecutar el programa sin privilegios administrativos y verificar el comportamiento.

**Prueba 7 – Versiones superiores**
Crear escenarios donde existan carpetas:
*   110
*   120
*   130
*   140
*   150
y verificar que las versiones superiores sean renombradas correctamente:
*   110
*   _120
*   _130
*   _140
*   _150

## 11. Entregables del pasante
El proyecto deberá entregar:
1.  **Código fuente:** Proyecto completo desarrollado en Python, organizado y documentado.
2.  **Ejecutable:** Archivo .exe listo para ser utilizado en equipos Windows.
3.  **Instaladores:** Estructura organizada con los instaladores de los prerrequisitos requeridos, respetando las políticas internas de distribución de software.
4.  **Archivo de configuración:** Si corresponde, parámetros configurables como: Nombre del servicio, Rutas, Ubicación de instaladores, Opciones de instalación.
5.  **Manual técnico:** Documento que explique: Arquitectura del programa, Librerías utilizadas, Funcionamiento, Mecanismo de detección de software, Manejo de servicios, Manejo de versiones, Proceso de generación del .exe.
6.  **Manual de usuario:** Documento sencillo indicando: Cómo ejecutar la herramienta, Requisitos, Qué hace cada etapa, Qué hacer ante un error.
7.  **Plan y evidencias de pruebas:** Se deberán documentar las pruebas realizadas y sus resultados.

## 12. Conocimientos deseables del pasante
Se busca un estudiante de Ingeniería de Sistemas, Informática o carreras afines, con conocimientos básicos o intermedios en:
*   Python.
*   Programación orientada a objetos.
*   Manejo de archivos y directorios.
*   Procesos del sistema operativo.
*   Windows.
*   Registro de Windows.
*   Servicios de Windows.
*   Línea de comandos.
*   Instalación/desinstalación de aplicaciones.
*   Git.
*   Manejo de excepciones y logs.

Será valorado el conocimiento en:
*   PyInstaller.
*   PowerShell.
*   Windows API.
*   MSI / Windows Installer.
*   Automatización de tareas administrativas.
*   Desarrollo de interfaces gráficas en Python.

## 13. Habilidades que desarrollará el pasante
Durante el desarrollo del proyecto, el pasante tendrá la oportunidad de adquirir experiencia en:
*   Desarrollo de aplicaciones para Windows.
*   Automatización de procesos de soporte técnico.
*   Administración básica de Windows.
*   Manipulación del Registro de Windows.
*   Gestión de servicios.
*   Instalación automatizada de software.
*   Desarrollo de herramientas de mantenimiento.
*   Manejo de errores y logging.
*   Generación de ejecutables.
*   Pruebas de software.
*   Documentación técnica.
*   Control de versiones mediante Git.

## 14. Resultado esperado
Al finalizar el proyecto se deberá contar con un ejecutable portable para Windows que permita al personal de soporte técnico ejecutar un proceso automatizado de reparación de los prerrequisitos de DATAX Analyze.
El objetivo final es que el técnico pueda ejecutar una única herramienta y que esta realice de forma controlada el proceso completo:
Detener servicio → Detectar componentes → Desinstalar → Limpiar → Renombrar versiones incompatibles → Instalar prerrequisitos → Validar → Iniciar servicio → Generar log.
La herramienta deberá minimizar la intervención manual y proporcionar información clara sobre el resultado de cada etapa.
