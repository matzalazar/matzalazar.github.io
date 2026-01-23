---
layout: post
title: "Diseñar la base de datos antes que la aplicación"
date: 2026-01-23
category: arquitectura
series: "Diseño evolutivo de sistemas"
series_part: 1
series_total: 3
---

# Diseñar la base de datos antes que la aplicación  

## Lecciones de un sistema que gestionó 1M+ eventos en 6 MB

Cuando un sistema crece, el principal problema rara vez es el volumen de datos. El verdadero riesgo aparece cuando la base de datos deja de representar fielmente la lógica del dominio y empieza a acumular estados derivados, agregados redundantes y excepciones implícitas.

Este artículo describe las decisiones de diseño detrás de una aplicación de gestión operativa que lleva cinco años en producción. El dominio concreto es deliberadamente abstracto: una organización distribuida en **ciudades**, que gestiona **oficinas**, donde **personas** registran horas laborales estándar y horas extra. Lo relevante no es la institución, sino las **invariantes** que el sistema debe respetar.

## Un dato empírico que cambia la perspectiva

Durante la migración del sistema, ocurrió algo revelador: el dump completo de la base de datos —con **1.2 millones de registros históricos**— ocupaba aproximadamente **6.2 MB**.

Ese número no fue resultado de compresión agresiva ni de purgado de datos. Fue la consecuencia natural de un modelo centrado en eventos: persistir únicamente lo ocurrido, evitando estados derivados y duplicación.

El tamaño funciona como un termómetro de diseño: indica cuánto del contenido de la base es información real y cuánto es cálculo repetido.

## El núcleo del problema: tiempo, responsabilidades y visibilidad

El sistema debía resolver simultáneamente tres capas de complejidad:

- **Responsabilidades territoriales**: cada ciudad tiene un responsable único.
- **Responsabilidades operativas**: una persona puede coordinar oficinas en distintas ciudades.
- **Restricciones temporales**: una persona no puede estar en dos lugares al mismo tiempo ni superar límites mensuales.

La decisión central fue:

> **El tiempo es global por persona.**  
> **Ciudad y oficina son contexto, no restricciones temporales.**

Esta regla evitó que el sistema se fracturara en calendarios separados por oficina, tipo de hora o ciudad.

## La invariante central

> **Ninguna persona puede tener dos eventos que se solapen temporalmente, sin importar tipo, oficina o ciudad.**

Todo el diseño —desde el modelo de datos hasta las validaciones— existe para hacer cumplir esta regla.  
Las tablas que no se crearon, los estados que no se persistieron y los **6 MB de dump** son consecuencias directas de haber identificado esta invariante antes de escribir la primera línea de código.

## Permisos que emergen de las relaciones, no se configuran

En lugar de tablas de permisos explícitas, el acceso se deriva de la estructura organizativa:

- una **ciudad** tiene un único responsable territorial;
- una **oficina** pertenece a una ciudad y puede tener un responsable operativo;
- un usuario puede ser responsable de una ciudad y, simultáneamente, coordinar oficinas específicas en otras ciudades.

La visibilidad se calcula como:

```
oficinas_visibles =
  (todas las oficinas de mis ciudades territoriales)
  ∪
  (oficinas que coordino en otras ciudades)
```

No hay `GROUP_PERMISSIONS` ni `USER_ACCESS_FLAGS`.  
Los permisos son una propiedad **emergente** del grafo de relaciones.

## Arquitectura de datos: solo lo necesario

A nivel de tablas, el sistema se reduce a:

```sql
-- Estructura organizativa
cities (id, name, territorial_manager_id)
offices (id, city_id, operational_manager_id)

-- Personas (independientes de la estructura)
people (id, name, identifier)

-- Eventos (inmutables)
work_shifts (id, person_id, office_id, started_at, ended_at)
extra_hours (id, person_id, city_id, started_at, ended_at)
```

Mirado en retrospectiva, el tamaño del dump refleja una decisión binaria tomada desde el inicio.

**Nota importante:** no existen:

- tablas de totales mensuales,
- campos `hours_accumulated` o `monthly_limit_exceeded`,
- estados de “cerrado” o “liquidado”,
- flags de “procesado”.

Cada evento es un hecho histórico. Los agregados se calculan **al vuelo**.

## Eventos, no estados

Una decisión deliberada fue **no persistir estados derivados**.

Cada registro horario es un evento atómico e inmutable.  
Los totales, límites y cierres se calculan a partir de estos eventos.

**Ventajas:**

- elimina desincronizaciones;
- no requiere reconciliaciones;
- el crecimiento de la base es lineal con los hechos reales;
- auditabilidad completa.

**Costo:**

- algunas consultas son más complejas;
- necesidad de índices cuidadosos.

El trade-off valió la pena: después de cinco años, **cero inconsistencias reportadas**.

## Validación temporal: la invariante no negociable

La regla más importante del sistema:

> **Una persona no puede tener dos tramos horarios que se solapen en el tiempo**,  
> sin importar el tipo de hora, oficina o ciudad.

La validación se aplica antes de cada inserción, con una consulta eficiente:

```sql
SELECT EXISTS (
    SELECT 1 FROM (
        SELECT started_at, ended_at FROM work_shifts WHERE person_id = ?
        UNION ALL
        SELECT started_at, ended_at FROM extra_hours WHERE person_id = ?
    ) AS all_events
    -- Usamos el default '[)' (inclusive start, exclusive end)
    -- para que terminar a las 00:00 y empezar a las 00:00 no cuente como solapamiento.
    WHERE tsrange(started_at, ended_at) 
          && tsrange(?, ?)
);
```

Esta consulta:

- combina ambos tipos de horas en un solo eje temporal;
- utiliza rangos semiabiertos para evitar falsos positivos en bordes exactos;
- se ejecuta en menos de 10 ms con índices adecuados.

## Normalización temporal: dividir para reinar

Los tramos que cruzan medianoche se dividen en eventos diarios antes de persistir.  
Un turno de 22:00 a 06:00 se almacena como dos registros inmutables:

```sql
-- Día 1
(id: 123, person_id: 45, started_at: '2024-01-15 22:00', ended_at: '2024-01-16 00:00')

-- Día 2
(id: 124, person_id: 45, started_at: '2024-01-16 00:00', ended_at: '2024-01-16 06:00')
```

El intervalo original se reconstruye desde la interfaz cuando es necesario,  
pero la base solo conoce eventos diarios.

Aunque esto desnormaliza el concepto de 'turno real' (un turno de noche son dos registros), esta implementación simplifica:

- cálculo de límites diarios y mensuales;
- generación de reportes;
- integración con sistemas externos.

## La base como frontera de consistencia

La base de datos nunca contiene estados inválidos porque:

- cada inserción es transaccional;
- la validación es parte de la transacción;
- no existen procesos batch de “corrección posterior”.

Esto crea un círculo virtuoso: los usuarios confían en el sistema porque los errores se detectan inmediatamente, no días después.

## Por qué el tamaño importa

Los **6 MB para 1.2 M de registros** no son un logro de compresión, sino un síntoma de diseño saludable:

| Lo que SÍ hay         | Lo que NO hay         |
| --------------------- | --------------------- |
| Eventos atómicos      | Agregados persistidos |
| Relaciones esenciales | Estados duplicados    |
| Metadatos inmutables  | Flags temporales      |

Cuando el modelo captura fielmente el dominio, la optimización más poderosa es eliminar lo innecesario.

## Lecciones para el próximo sistema

- **El tiempo es una dimensión única** – no lo fragmentes sin necesidad.
- **Los permisos deben derivarse, no configurarse** – si tu sistema de permisos es más complejo que tu organigrama, algo está mal.
- **Persistí hechos, no conclusiones** – los cálculos se recomputan, los hechos son eternos.
- **Validá temprano, validá siempre** – la base debe ser la última línea de defensa.
- **La simplicidad escala** – los sistemas complejos no escalan, se derrumban.

---

## Cierre

Este artículo no es sobre PostgreSQL ni Django.  
Es sobre entender el dominio antes de escribir la primera migración.

Los cinco años en producción, los usuarios activos y los **6 MB de dump** son simplemente consecuencias observables de haber tomado esas decisiones al inicio.

La próxima vez que diseñes una base de datos, preguntate:

> **¿Estoy persistiendo lo que pasó,  
> o lo que creo que necesitaré calcular después?**

La respuesta puede ahorrarte migraciones dolorosas y, a tu base de datos, gigabytes innecesarios.