---
layout: post
title: "Ingeniería para la vida diaria"
date: 2025-12-03
---

# Ingeniería para la vida diaria  

## 1. El origen del problema: demasiadas fuentes, demasiada fricción

Durante años tuve una sensación persistente: mi presencia online estaba desordenada.  
No porque le faltara contenido, sino porque **cada plataforma contenía una parte de mí**, sin sincronización entre ellas.

- LinkedIn reflejaba mi perfil profesional.
- Goodreads mostraba qué leo.
- Plataformas como Coursera o el SIU Guaraní de la UPSO almacenaban qué estudio.
- GitHub contenía mi trabajo real como desarrollador.
- Obsidian tenía mis notas, ideas, reflexiones y borradores de artículos.
- Mi sitio personal… dependía de mi memoria para actualizarse.

Era una arquitectura humana defectuosa. Un sistema en el que yo era el *ETL* manual: leer, copiar, actualizar, sincronizar, volver a revisar.

Lo que en infraestructura se conoce como **falta de fuente de verdad**.  

Lo que en productividad se conoce como **fricción**.  

Lo que en la práctica significa: desactualización crónica.

El cambio sucedió cuando me pregunté lo que cualquier ingeniero se preguntaría:

**¿Por qué estoy haciendo tareas repetitivas que una computadora puede hacer mejor que yo?**

## 2. La idea: tratar mis datos personales como un producto

La solución no fue escribir un script. Fue diseñar un **pipeline completo**, con las mismas reglas que aplicaría en una empresa:

- fuentes de verdad claras,  
- un componente de recolección resiliente,  
- un componente de procesamiento y normalización,  
- un componente de publicación,  
- y la infraestructura mínima para sostenerlo sin intervención humana.

Nació así el proyecto que hoy rige mi ecosistema digital: [personal-tracker](https://github.com/matzalazar/personal-tracker), un sistema autónomo de RPA personal que captura, versiona y distribuye mis datos.

Y sobre él, un **builder estático** que convierte esos datos en contenido para mi sitio Jekyll.

El objetivo no era la automatización por la automatización misma. Era **sacar la edición manual del circuito**. Hacer que mi vida digital se exprese sola sin perder tiempo en mantener mi presencia digital.

## 3. Diseño conceptual: un mini data‑lake doméstico

Entendí rápidamente que mis datos estaban distribuidos en múltiples plataformas, pero que todas compartían un patrón:

- eran estructurables (roles, cursos, libros, proyectos);
- eran transformables en JSON;
- y se actualizaban con una frecuencia razonable (diaria o semanal).

La idea entonces fue construir algo parecido a un **data‑lake personal**, pero extremadamente minimalista.

Este modelo tenía dos beneficios inmediatos:

1. **Separación total entre datos y presentación.**  
   La web no es donde creo contenido: es donde el contenido se refleja.

2. **Independencia absoluta de plataformas externas.**  
   Aunque cambien APIs o políticas, yo siempre conservo un historial propio.

## 4. La Raspberry Pi como servidor personal 24/7

Elegir la Raspberry Pi no fue casual. Necesitaba:

- un entorno que corra **sin depender de mi laptop**,  
- bajo consumo eléctrico,  
- uptime estable,  
- y un espacio donde aplicar prácticas de DevOps reales.

La Pi cumple con todo:

- funciona como un **servidor doméstico**;  
- tiene Tailscale, así que puedo accederla desde cualquier lugar;  
- permite correr Selenium headless con Xvfb para scraping complejo;  
- me obliga (y me permite) respetar estándares como **FHS** y **systemd**.

## 5. Arquitectura del proyecto `personal-tracker`: ingeniería para la vida diaria

`personal-tracker` es un proyecto escrito como si fuera un microservicio productivo, con responsabilidades claras y aislamiento entre capas.

### 5.1 FHS: jerarquía estricta

```
/opt/personal-track      → código del sistema
/etc/personal-track      → configuración + cookies + tokens
/var/lib/personal-track  → datos persistentes (JSON versionados)
/var/log/personal-track  → logs, errores, auditoría
```

Esta estructura impone disciplina:

- no mezclo código y datos;  
- sé dónde vive cada cosa;  
- puedo hacer backups selectivos;  
- los permisos son más simples y seguros.

### 5.2 El patrón BaseScraper: Template Method

Todos los scrapers heredan de un objeto base que define:

- validación inicial  
- carga de cookies/tokens  
- ejecución del scraping  
- normalización  
- exportación del JSON  
- manejo de errores  
- logging estandarizado  

Cada scraper solo implementa la parte específica del “cómo obtener los datos”.

Es exactamente la misma idea que se usa en empresas para homogenizar scrapers o workers heterogéneos.

### 5.3 Versionado diario de datos

Cada salida produce un archivo con timestamp:

```
goodreads_2025-12-03.json
coursera_2025-12-03.json
github_2025-12-03.json
```

Esto me permite:

- mantener un historial cronológico,  
- comparar períodos,  
- reconstruir actividad pasada,  
- depurar diferencias entre días,  
- y tolerar fallos sin perjudicar el build.

### 5.4 Resiliencia por diseño

Hacer scraping es una práctica frágil. Cookies expiran, selectores cambian, APIs rate-limitan.

Mi solución fue diseñar para la **imperfección**:

- expiración controlada de cookies (las guardo en `/etc/personal-track`),  
- reintentos con backoff,  
- logs legibles,  
- fallback automático al último JSON válido,  
- aislamiento: si Goodreads falla, nada más se rompe.

La filosofía es simple: **prefiero información incompleta antes que un pipeline caído.**

## 6. El segundo componente: el builder de Jekyll

Una vez recolectados los datos, otro timer systemd en la Raspberry Pi ejecuta un script de build que transforma los JSON en:

- YAML para `_data/`,
- Markdown para secciones del sitio,
- logs generados desde Obsidian,
- y un archivo de metadatos con timestamps.

El builder siempre toma **el último JSON disponible** por prefijo. Si no hay datos nuevos una noche, la web igual se construye.

### 6.1 Artefactos generados

#### YAML
- `_data/reading.yml` (generado desde Goodreads)  
- `_data/studies.yml` (generado desde Coursera y UPSO)   
- `_data/work.yml` (generado desde Github)  

#### Markdown
- `about.md` (generado desde LinkedIn)  
- `_logs/*.md` (notas breves desde Obsidian)

#### Metadatos
- `_data/meta.yml` (marca del último build)

Es un sistema declarativo: **el sitio es un reflejo, no un origen.**

## 7. El flujo diario: del mundo real a la web

El pipeline completo es este:

```
00:00  Tracker → Scraping de todas las fuentes → JSON diario
00:05  Builder → Normalización → YAML/MD → Git commit/push
00:06  GitHub Pages / Actions → Despliegue del sitio
```

El proceso completo, desde el mundo real hasta la web final, sucede sin intervención humana.

## 8. ¿Qué cambió en la práctica?

Este sistema reformuló completamente cómo administro mi presencia online.

- No “actualizo” mi web. **Mi sitio personal es una consulta SQL a mi vida digital.**

- **Mi CV nunca vuelve a quedarse viejo**. LinkedIn es la fuente de verdad. El sitio solo lo refleja.  

- **El blog ya no es una plataforma**. Escribo en Obsidian, marco `status: publicar` en la metadata de la nota, y eso es todo.  

- Mis datos no desaparecen. Tienen su historia. **Cuento con una trazabilidad total de mi actividad**.  

- **Pose una arquitectura extensible fácilmente**:

1. crear un scraper heredado,  
2. guardar su JSON en `/var/lib/personal-track`,  
3. ajustar el builder si corresponde.

## 9. Casos reales: cómo se siente usar el sistema

- **Termino un libro** → Goodreads lo marca → al día siguiente aparece como completado en mi web.  
- **Comienzo un curso nuevo** → Coursera lo registra → Jekyll agrega la tarjeta del curso.  
- **Escribo una nota en el celular** → Obsidian la sincroniza → aparece en la sección "logs".  
- **Subo un commit** → GitHub lo registra → el builder lo incorpora al historial del día.  
- **Actualizo un rol profesional** → LinkedIn lo refleja → `about.md` se regenera solo.

**El sistema trabaja para mí.**

## 10. Cómo replicarlo: guía técnica resumida

1. Definir fuentes de verdad.  
2. Construir un scraper por fuente (idealmente con BaseScraper).  
3. Respetar FHS para separar código, datos y secretos.  
4. Versionar salidas en `/var/lib`.  
5. Crear un builder que genere YAML/MD.  
6. Automatizar con timers systemd.  
7. Desplegar con GitHub Pages o similar.  
8. Proteger cookies y tokens en `/etc`.  
9. Nunca editar Jekyll manualmente.

## 11. Reflexión final: automatizarse para recuperar tiempo

Este proyecto empezó como un intento por evitar la fricción de actualizar mi CV, pero terminó siendo algo distinto: **un sistema de RPA personal**, una infraestructura mínima pero poderosa que documenta mi vida diaria sin pedirme atención.  

Y en ese proceso descubrí algo interesante:  

> Automatizar no es delegar tareas.  
> Automatizar es rediseñar la relación entre uno mismo y sus herramientas.  

Mi sitio ya no es algo que “tengo que mantener”. Es simplemente la proyección organizada de lo que hago todos los días.  

Y eso —para mí— fue liberador.
