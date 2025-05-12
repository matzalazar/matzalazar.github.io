---
layout: default
title: Proyecto Administración
permalink: /projects/administracion/
---

## 🧩 Ecosistema de Administración de Servicios

Este sistema fue desarrollado para gestionar los servicios de Policía Adicional en el ámbito de la Provincia de Buenos Aires, aunque puede adaptarse a otros entornos con lógica de turnos, permisos y validaciones de disponibilidad horaria.

### 🎯 Contexto

Previo a esta solución, la administración se realizaba manualmente mediante planillas Excel distribuidas, con alto margen de error y sin trazabilidad. La necesidad era clara: automatizar y centralizar la gestión de turnos, generar reportes oficiales y garantizar el cumplimiento de restricciones laborales. Todo esto, en el marco de una gestión descentralizada, en la que intervienen múltiples personas con distintos niveles de responsabilidad y tareas asociadas.

### 🔍 Desafíos

- Validar múltiples reglas por persona y servicio (superposición, límite de horas, días no laborables).
- Generar reportes oficiales en Excel, con fórmulas configuradas y listos para impresión y firma.
- Mantener una arquitectura modular, en la que cada componente pueda operar de forma autónoma (web, CLI, automatización GUI).
- Ejecutarse en entornos con recursos limitados, sin depender de grandes despliegues.

### 🛠️ Solución

**1. Primera etapa**

Se desarrolló una aplicación web en Django que define roles y permisos, gestiona servicios y valida turnos de acuerdo con la normativa vigente. Permite exportar automáticamente expedientes en formato Excel. Todo el sistema se apoya en una base de datos PostgreSQL alojada en un VPS y contempla control granular por usuario.

**2. Segunda etapa**

En 2022, el Ministerio de Seguridad implementó una plataforma oficial de carga que exige conexión mediante VPN y centralizó esa tarea en una única persona para múltiples servicios. Esto generó una sobrecarga operativa significativa. Para evitar abandonar el modelo descentralizado, se mantuvo el uso de la webapp como herramienta de precarga.

Se desarrolló entonces una app de escritorio con Flet, orientada a usuarios administrativos no técnicos, que automatiza la carga de datos al sistema ministerial utilizando Selenium. Esto permitió reducir los tiempos de carga y preservar la distribución de tareas.

**3. Tercera etapa**

Dado que la distribución de personal debe ajustarse tanto a restricciones individuales como a necesidades institucionales, se diseñó un software de consola (CLI) que toma como input un archivo Excel editable, se conecta a la base PostgreSQL remota y genera una asignación óptima de turnos. El sistema permite, además, una validación manual posterior para ajustar arbitrariamente el balance de horas entre personas.

---

### ✅ Resultados

- Se mantiene la descentralización del sistema sin perder confiabilidad.
- Se evita la sobrecarga operativa en pocas personas.
- Se reduce drásticamente el error humano.
- Tareas que antes tomaban días pueden resolverse en minutos.
