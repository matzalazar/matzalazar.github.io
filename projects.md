---
layout: default
---

## 🚀 Proyectos destacados

### TMDB Data Pipeline · [Repositorio](https://github.com/matzalazar/tmdb-data-pipeline)

Pipeline en Python que extrae películas y detalles desde la API de TMDB, almacena snapshots diarios en Delta Lake (Bronze) y construye una capa Silver enriquecida y limpia. Permite seguir la permanencia en cartelera, la evolución de ratings y entrenar modelos predictivos. Ejecutable de forma incremental y modular.

*Stack:* Python · Spark · Delta Lake · Airflow

### Moodle Downloader UPSO · [Repositorio](https://github.com/matzalazar/moodle-downloader-upso)

Automatización en Python con Selenium para recorrer cursos del campus virtual Moodle, estructurando su contenido en formato JSON jerárquico (Curso > Semana > Tema) y descargando en paralelo todos los archivos relevantes (.pdf, .docx, .ipynb, etc.). Permite realizar seguimientos académicos offline, evitando duplicados y preservando la organización original.

*Stack:* Python · Selenium · JSON · Automatización Headless

---

### Gestor de Turnos y Distribución

Este proyecto consta de varios repositorios que conforman un ecosistema de iniciativas destinadas a la gestión integral de servicios de Policía Adicional en el ámbito de la Provincia de Buenos Aires. Aunque puede ser adaptado para distintos ámbitos de aplicación que posean lógicas similares.

1. **WebApp en Django** que define roles y permisos, cuenta con diversos tipos de validaciones (máximo de horas permitido y superposición) y genera reportes oficiales en Excel directamente desde el backend, reduciendo errores y tiempos operativos. 

*Stack:* Python · Django · Excel

2. **App de escritorio desarrollada en Flet** que permite automatizar el proceso de data entry a la web ministerial. Pensada para usuarios no técnicos, optimiza el proceso a través de una conexión local con la base de datos remota de PostgreSQL que opera a través de la webapp en Django.

*Stack:* Python · Flet · Selenium

3. **Software de línea de comandos** que se conecta a una base de datos remota PostgreSQL (VPS), analiza restricciones horarias por persona y genera una asignación mensual de turnos optimizada. Toma como input un archivo Excel con los requerimientos (mínimo y máximo de horas, días hábiles, personal requerido).

*Stack:* CLI · ORTools · Bash

**_(En producción desde 2020)_.**

📁 Por confidencialidad, estos repositorios son privados. [Aquí podés leer más sobre su desarrollo.](./projects/administracion) 
 
Si te interesa ver el código, no dudes en contactarme. Comparto acceso bajo NDA.

---

### Suite Forense de Análisis de Video

Pensado principalmente para análisis de material fílmico proveniente de cámaras de monitoreo municipal, este proyecto resulta también de utilidad para todos los involucrados en un proceso judicial: desde policías hasta periodistas.

1. **Conversor MFS que elimina la restricción del formato `.mfs` propietario**, convirtiendo los archivos a `.mp4` para facilitar su visualización, análisis y compatibilidad con software de procesamiento.

2. Sistema de **análisis visual automatizado**, que recorre los videos cuadro por cuadro aplicando visión por computadora para detectar objetos de interés como vehículos, bicicletas o personas, permitiendo generar un resumen visual filtrado.

3. Módulo de **parseo** y **geolocalización**, que interpreta los metadatos asociados a las grabaciones, extrae coordenadas y tiempos, y genera reportes enriquecidos útiles para investigaciones.

*Stack*: OpenCV · Python · Bash · Docker

**_(En producción desde 2025)_.**

📁 Por confidencialidad, estos repositorios son privados. [Aquí podés leer más sobre su desarrollo.](./projects/forense) 
 
Si te interesa ver el código, no dudes en contactarme. Comparto acceso bajo NDA.
