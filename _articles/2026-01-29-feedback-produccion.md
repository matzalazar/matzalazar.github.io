---
layout: post
title: "Feedback en producción"
date: 2026-01-29
category: arquitectura
series: "Diseño evolutivo de sistemas"
series_part: 2
series_total: 3
description: "Cómo el diseño de eventos inmutables permitió evolucionar la UX sin tocar el modelo de dominio"
---

# Cuando el modelo resiste  

## Feedback real y rediseño de la experiencia sin romper el modelo de dominio

> Este artículo es la segunda parte de la serie **"Diseño evolutivo de sistemas"**, donde expliqué cómo decisiones iniciales de modelado resultaron en un sistema con **1.2M de eventos en solo 6 MB**.  
> 
> Aquí muestro lo que sucedió después: cómo ese diseño permitió **evolucionar la experiencia sin tocar el modelo de dominio ni las estructuras operativas**.

El primer artículo se centró en decisiones de diseño de base de datos: eventos inmutables, validación temporal estricta y permisos derivados de relaciones. El resultado fue un sistema que, después de cinco años en producción, acumuló más de un millón de eventos con un historial consistente y sin estados inválidos.

Este segundo artículo no trata sobre cómo diseñar ese modelo, sino sobre **qué fue posible hacer después**, precisamente porque el modelo nunca se rompió.

---

## Punto de partida: el sistema funcionaba

Es importante aclarar algo desde el inicio: el rediseño no surgió de un sistema fallido.

La aplicación:
- funcionaba,
- cumplía las reglas del dominio,
- no generaba inconsistencias,
- y resolvía el problema operativo para el que había sido creada.

Sin embargo, el uso cotidiano expuso fricciones. No errores lógicos, sino **costos de interacción**: pasos repetidos, cambios innecesarios de contexto y flujos diseñados con el conocimiento disponible en el momento inicial.

El rediseño no fue una corrección. Fue aprendizaje acumulado.

## Feedback real, no supuestos

El feedback no llegó en forma de tickets estructurados ni métricas sofisticadas. Llegó como frases recurrentes de usuarios que usaban el sistema todos los días:

- “Esto lo cargo siempre igual.”
- “Para ver esto tengo que salir y volver a entrar.”
- “Esto debería ser más rápido.”
- “Acá siempre me equivoco.”

No eran pedidos de features. Eran señales de fricción.

El objetivo del rediseño fue **reducir fricción sin relajar ninguna invariante** del sistema.

## Caso 1: el calendario — de vista separada a interacción contextual

### Antes  
El calendario de eventos existía como una vista dedicada. Para consultar distribuciones mensuales, por ejemplo, el usuario debía abandonar el flujo de carga o revisión y navegar a una pantalla distinta.

### Después  
El calendario se integró como un modal contextual, embebido en el flujo principal de trabajo. El usuario puede visualizar los eventos sin cambiar de contexto ni perder el estado de la tarea actual.

### Lo importante  
El calendario siempre leyó los mismos datos: eventos inmutables con `started_at` y `ended_at`.  
El rediseño fue **exclusivamente de interacción**.

El modelo no se tocó. Y eso fue una ventaja.

## Caso 2: creación de usuarios — de registro abierto a trazabilidad explícita

### El problema original  
Existía un formulario de registro abierto. Muchos usuarios creaban cuentas “para ver cómo era el sistema”.  
El resultado era ruido: usuarios válidos técnicamente, pero sin permisos reales, sin acceso a información, y sin responsabilidad operativa.

### El rediseño  
- Se eliminó el registro abierto.
- Solo existe pantalla de login.
- Los usuarios son creados por otros usuarios ya existentes.
- Se asigna una contraseña temporal.
- En el primer login, el nuevo usuario debe cambiarla.

Cada cuenta nueva tiene un **origen trazable**.  

El único cambio requerido fue la incorporación de un flag técnico de autenticación para forzar el cambio de contraseña en el primer login. No afectó entidades de negocio, eventos ni reglas de consistencia  

### Resultado  
- Menos ruido.
- Mayor control distribuido.
- Ningún superusuario central gestionando altas.

El sistema dejó de optimizar para curiosos y empezó a optimizar para responsabilidad.

## Caso 3: carga de personas — prevenir errores sin bloquear el flujo

### Antes  
Solo se permitía seleccionar personas existentes. Esto evitaba errores, pero bloqueaba casos legítimos donde la persona aún no estaba cargada en la base de datos.

### Después  
- Búsqueda por identificador único.
- Advertencia explícita si la persona ya existe.
- Alta guiada si no existe.
- Verificaciones explícitas de integridad y trazabilidad de creación.

El control no desapareció. Se volvió **explícito y auditable**.

Este cambio redujo errores reales sin introducir estados ambiguos ni datos inconsistentes.

## Caso 4: carga masiva de eventos — modelar patrones reales

Este fue el cambio con mayor impacto operativo.

### Observación clave  
Los usuarios no cargan eventos arbitrarios.  
Cargan **patrones**:

- mismos días de la semana,
- mismos horarios,
- semanas completas,
- meses con reglas previsibles.

### Rediseño  
Se implementó carga múltiple declarativa:
- selección de rangos de fechas,
- días específicos,
- horarios recurrentes.

El sistema genera automáticamente los eventos individuales, aplicando **exactamente la misma validación temporal** que en la carga manual.

### Ejemplo técnico

```python
# Misma validación para carga masiva y manual
def crear_turnos_masivos(persona, patron_fechas, hora_inicio, hora_fin):
    for fecha in patron_fechas:
        inicio = datetime.combine(fecha, hora_inicio)
        fin = datetime.combine(fecha, hora_fin)

        # La invariante central del primer artículo
        validar_solapamiento(persona, inicio, fin)

        # Crear el evento (Turno)
        # El modelo de datos subyacente no cambia
        WorkShift.objects.create(
            persona=persona,
            started_at=inicio,
            ended_at=fin,
            created_by=request.user  # Trazabilidad
        )
```

### Por qué fue posible  
Cada evento es independiente, validado y sin estado compartido.  
No hubo que modificar el modelo de datos operativo ni las validaciones existentes. Solo cambiar la forma de **generar eventos válidos**.

## Qué no cambió (y por qué eso importa)

Durante todo el rediseño:

- no cambió la estructura de eventos;
- no cambió la validación de solapamientos;
- no cambió el modelo de permisos;
- no hubo migraciones complejas.

El rediseño fue superficial en el mejor sentido: tocó **interacción**, no **verdad**.

## Modelo y experiencia: una comparación simple

```
ANTES:   Modelo → Interfaz rígida → Usuario se adapta
DESPUÉS: Modelo → Interfaz flexible ← Usuario guía mejoras
```

Cuando el modelo captura bien la verdad del dominio, la interfaz puede cambiar sin miedo.

## Lección central del segundo orden

Un buen diseño no evita cambios.  
Los **habilita**.

En este caso, la estabilidad del diseño permitió iterar rápido, escuchar feedback real y reducir fricción sin comprometer consistencia.

## Cierre

El primer artículo fue sobre cimientos.  
Este fue sobre qué ocurre cuando esos cimientos no se rompen.

Un modelo que captura correctamente la verdad del dominio no evita el cambio: **lo hace seguro**.

Cuando la experiencia necesita evolucionar, el sistema no se reescribe ni se parchea. Se adapta.

Si cada mejora de experiencia de usuario te obliga a redefinir el núcleo del sistema, el problema no está en la interfaz.

Está en el diseño.