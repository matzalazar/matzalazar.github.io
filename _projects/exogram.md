---
layout: project
title: "Exogram"
repo: https://github.com/matzalazar/exogram
description: "Red social de subrayados de lectura con búsqueda semántica local y diseño orientado a la privacidad."
date: 2026-03-24
tags: [python, django, vue, postgresql, celery, docker, embeddings, privacy, social]
permalink: /projects/exogram/
---

**Exogram** es una plataforma de subrayados de lectura donde los usuarios importan sus highlights de Kindle, los anotan y los conectan semánticamente con los de otras personas. No hay algoritmos de engagement, ni contadores de likes, ni scroll infinito: solo lectores y lo que subrayan.

## Características Principales

- **Importación de highlights**: Soporte para exportaciones de Kindle con preservación de notas, ubicación en el texto y metadatos del libro
- **Búsqueda semántica local**: Embeddings con `paraphrase-multilingual-MiniLM-L12-v2` (ONNX Runtime, sin PyTorch) almacenados en pgvector — los textos de los usuarios no salen del sistema
- **Descubrimiento por afinidad**: Comparación de centroides semánticos entre usuarios para encontrar lectores con intereses similares, sin popularidad ni actividad como señal
- **Red por invitación**: Árbol de invitaciones como grafo social subyacente, con profundidad de comentarios configurable como modelo de confianza
- **Privacidad granular**: Visibilidad por highlight, modo ermitaño, flag de descubrimiento y control de quién puede comentar
- **Stack self-hosted**: Postal para email transaccional, Caddy para TLS, servidor en Alemania bajo jurisdicción GDPR

## Stack Técnico

Django 5.2 LTS · Vue 3 · PostgreSQL + pgvector · Celery + Redis · Docker · Caddy · GitHub Actions CI/CD
