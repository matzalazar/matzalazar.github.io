---
layout: post
title: "Moodle Downloader: una solución headless con Selenium para entornos educativos"
date: 2025-05-14
categories: blog
---

## Moodle Downloader: una solución headless con Selenium para entornos educativos

### Introducción

Quienes cursamos materias en plataformas como **Moodle** sabemos lo engorroso que puede ser descargar manualmente los materiales de cada curso, semana tras semana. Este proceso no solo es repetitivo y lento, sino también propenso a errores o descargas incompletas.

Para resolverlo, desarrollé un sistema en **Python usando Selenium en modo headless** que automatiza por completo la descarga de archivos en el **campus virtual de la Universidad Provincial del Sudoeste (UPSO)**. Esta herramienta permite iniciar sesión, recorrer todos los cursos, capturar su estructura y descargar únicamente los archivos relevantes, sin intervención humana. Las ejecuciones posteriores solo descargan contenido nuevo.

### Objetivos del proyecto

El script automatizado permite:

- Iniciar sesión automáticamente en Moodle con credenciales personales que se almacenan localmente.
- Detectar los cursos y especificar manualmente de cuáles se pretende hacer un seguimiento. 
- Recolectar la estructura jerárquica de contenidos organizada por semanas y temas.
- Descargar archivos de forma inteligente (evitando duplicados y descartando formatos irrelevantes).
- Replicar fielmente la estructura de Moodle en el disco local.
- Generar a través de la API de _Todoist_ nuevas `task` sobre el nuevo material descargado.

### Estructura del proyecto

El proyecto está organizado modularmente en carpetas y scripts:

```bash
config/
├── creds.txt              # Usuario y contraseña
└── course_links.json      # Cursos seleccionados y seguimiento
└── todoist_token.txt      # API Token de Todoist

data/
├── trees/                 # Estructura jerárquica por curso (semanas y temas)
└── course/                # Contenido descargado 

scripts/
├── session.py             # Login automático
├── fetch_links.py         # Selección de cursos y URLs
└── extract_course_tree.py # Generación de árboles jerárquicos por curso
└── download_files.py      # Descarga de contenido
└── load_todoist.py        # Opcional: Para carga en Bandeja de Entrada de Todoist

main.sh                    # Script bash para orquestar todo
```

### Replicación estructural de Moodle

Uno de los objetivos clave fue **respetar la jerarquía y organización de los cursos tal como se ve en Moodle**. Esto incluye:

- Directorios por curso (`2025-1_C-509-INTRODUCCION_A_LA_PROGRAMACION_PYTHON`)
- Subdirectorios por semana o tema (`Semana_07_04_2025_-_13_04_2025`)
- Subcategorías como `Material_de_lectura`, `Actividades_y_trabajos_prácticos`, etc.
- Archivos individuales renombrados automáticamente para evitar ambigüedades.

El resultado es una estructura de carpetas limpia, cronológica y perfectamente ordenada, ideal para hacer backups o revisar el contenido offline sin depender del navegador.

### Descarga automática del ChromeDriver

Una de las principales molestias al usar Selenium suele ser la instalación y actualización manual del **ChromeDriver**. En este proyecto ese problema **se resuelve automáticamente** mediante la librería `webdriver-manager`.

Esto significa que:

- El script **detecta automáticamente la versión de Chrome** instalada (compatible con Windows, Linux y macOS).
- Descarga el ChromeDriver correspondiente sin intervención manual.
- Siempre ejecuta la versión correcta, evitando errores por incompatibilidades o cambios de navegador.

```python
# Detectar versión local de Chrome instalada
def obtener_version_chrome():
    try:
        sistema = platform.system()
        if sistema == "Windows":
            version = subprocess.check_output(
                r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
                shell=True
            )
            return version.decode().strip().split()[-1]
        elif sistema in ["Linux", "Darwin"]:
            for cmd in ["google-chrome", "google-chrome-stable", "chromium-browser", "chrome"]:
                try:
                    version = subprocess.check_output([cmd, "--version"]).decode().strip()
                    return version.split()[-1]
                except Exception:
                    continue
        else:
            print(f"⚠️ Sistema operativo no soportado: {sistema}")
            return None
    except Exception as e:
        print(f"⚠️ No se pudo obtener la versión de Chrome: {e}")
        return None

# Inicializar navegador con ChromeDriver
def init_browser():
    chrome_version = obtener_version_chrome()

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")

    try:
        if chrome_version and int(chrome_version.split('.')[0]) >= 115:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        else:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager(version=chrome_version).install()), options=options
            )
        return driver
    except Exception as e:
        print(f"⚠️ Error al iniciar navegador: {e}")
        return None
```

Este comportamiento está encapsulado en el archivo `session.py`, haciendo que cualquier script que lo importe pueda obtener una sesión autenticada en Moodle en una sola línea:

```python
from scripts.session import get_authenticated_browser

browser = get_authenticated_browser()
```

Ya no hay que preocuparse por `PATH`, instalaciones externas ni descargas manuales. Solo corrés el script, y el navegador se configura solo.

### Captura de estructura jerárquica

Además de la descarga de archivos, el sistema **extrae la estructura semántica de cada curso y la guarda como un árbol `.json`**.

Ejemplo:

```json
{
  "curso": "Matemática I",
  "semanas": [
    {
      "titulo": "Semana 1",
      "materiales": [
        {"nombre": "Clase 1", "url": "..."}
      ]
    }
  ]
}
```

Estos archivos permiten auditar los contenidos, generar reportes o sincronizar cambios futuros de forma incremental.

### Descarga inteligente

El sistema descarga únicamente archivos que cumplan con ciertas extensiones deseadas:

- `.pdf`, `.docx`, `.xlsx`, `.ipynb`, `.py`, etc.

Además:

- Verifica si el archivo ya existe antes de descargarlo.
- Si un nombre se repite, aplica un renombrado seguro.
- Ignora recursos sin utilidad directa como imágenes decorativas o enlaces rotos.

### Posibilidades futuras

Este proyecto puede extenderse con funcionalidades como:

- **Ejecución automática con cron o tareas programadas**.
- **Panel web simple para seleccionar cursos o ver estado de sincronización**.
- **Sincro incremental basada en fechas de modificación o tamaño de archivos**.

### Conclusión

Esta herramienta es una muestra concreta de cómo aplicar **automatización con Selenium** para resolver un problema real del día a día académico. Evita descargas manuales, respeta la organización del material y puede ejecutarse periódicamente como un sistema de backup local.

Es un buen ejemplo de cómo unir scripting, scraping y automatización para mejorar la experiencia educativa en entornos virtuales como Moodle.

> 📂 Podés ver el código fuente completo en [GitHub](https://github.com/matzalazar/moodle-downloader-upso.git)