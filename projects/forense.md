---
layout: default
title: Suite Forense de Análisis de Video
permalink: /projects/forense/
---

## 🔎 Suite Forense de Análisis de Video

Este proyecto está orientado al análisis de grabaciones provenientes de cámaras de seguridad, particularmente en contextos judiciales. Fue desarrollado para facilitar tareas de inspección visual sobre material audiovisual en formatos propietarios, permitiendo extraer evidencia útil de manera más eficiente y automatizada.

### 🎯 Contexto

En muchas dependencias policiales o judiciales, las grabaciones provienen de sistemas de videovigilancia que exportan los archivos en formatos propietarios no compatibles con herramientas estándar (como `.mfs`). Esto dificulta su análisis, obliga a utilizar software cerrado y restringe la automatización de tareas repetitivas como la búsqueda de vehículos o personas en grandes volúmenes de material.

El proyecto busca resolver este cuello de botella mediante herramientas propias que permitan:  
- Convertir los archivos a formatos accesibles.  
- Aplicar técnicas de visión por computadora sobre los videos.  
- Sistematizar la búsqueda y registro de objetos o eventos de interés.

### 🔍 Desafíos

- Interpretar un formato propietario de video (`.mfs`) sin acceso al software original.
- Establecer una pipeline de conversión, análisis y reporte automatizable.
- Trabajar con resoluciones bajas, cámaras fijas y condiciones lumínicas variables.
- Preservar la trazabilidad de los datos y su integridad probatoria.

### 🛠️ Solución

**1. Conversor MFS → MP4**  

Se desarrolló un módulo que permite convertir archivos `.mfs` a `.mp4`, manteniendo la secuencia temporal y permitiendo su análisis posterior con herramientas estándares como OpenCV o ffmpeg.

**2. Análisis visual automatizado**  

Aplicando visión por computadora, se recorre el video cuadro por cuadro para identificar objetos de interés como bicicletas, vehículos o personas. Los resultados pueden filtrarse según tipo, color o comportamiento (ej. si un objeto se detiene, entra o sale de escena).

**3. Módulo de geolocalización y reporte**  

En casos donde el sistema de videovigilancia almacena metadatos (coordenadas GPS o timestamp), se extraen automáticamente para contextualizar los eventos detectados. El sistema genera un reporte ordenado, útil como insumo para investigadores, abogados o periodistas.

---

### ✅ Resultados

- Permite analizar grabaciones sin depender de software privativo.
- Reduce el tiempo necesario para revisar material extenso.
- Sistematiza la detección de eventos sin supervisión constante.
- Mejora la trazabilidad de evidencias audiovisuales.
