---
layout: project
title: "Vigilant"
repo: https://github.com/matzalazar/vigilant
description: "Suite de procesamiento forense de video."
date: 2026-02-08
tags: [cybersecurity, forensic, python, ai, cctv]
permalink: /projects/vigilant/
---

**Vigilant** es una suite de procesamiento forense de video que convierte formatos propietarios de CCTV a estándares abiertos, con análisis visual asistido por IA local y chain of custody automatizado. Diseñado para investigadores, analistas forenses y profesionales de seguridad que requieren trazabilidad completa y reproducibilidad.

## Características Principales

- **Conversión Forense**: Pipeline multi-herramienta (HandBrake + FFmpeg) con modo de rescate automático para archivos corruptos
- **Chain of Custody**: Hashes SHA-256, metadata completa (`.integrity.json`), timestamps UTC y comandos reproducibles
- **Análisis Visual con IA**: Detección asistida con YOLO + LLaVA (modelos locales vía Ollama), con reportes legales generados por Mistral
- **Procesamiento PDF**: Extracción y correlación de metadata de reportes

## Nota Legal

Herramienta de **asistencia investigativa**. Los resultados deben ser revisados por profesionales calificados. No reemplaza el juicio humano ni la cadena de custodia física.