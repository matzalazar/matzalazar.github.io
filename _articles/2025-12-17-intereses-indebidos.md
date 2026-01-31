---
layout: post
title: "Intereses indebidos"
date: 2025-12-17
category: datos
description: "Análisis de liquidaciones de deuda usando Pandas para detectar errores en cálculo de intereses compensatorios"
---

# Cuando un pago “en término” termina generando intereses

### Un problema clásico de timezones en sistemas financieros

_"Pagué a las 22:58 del vencimiento y según el código civil y comercial es en fecha. El sistema no puede contradecir la ley."_ Este reclamo, publicado hace poco en [X](https://x.com/dzapatillas/status/2001116949858615464), resume un problema que miles de usuarios enfrentan (y basta con mirar las respuestas al tuit original): pagos realizados dentro del plazo que, por un error técnico, son registrados como atrasados, generando intereses injustos.

En una de las respuestas, otro usuario confirmaba que esto no era un caso aislado: algunos bancos registran los pagos como correspondientes al día siguiente si se realizan luego de las 19 hs. Al investigar un poco más, surgió un dato relevante: la entidad en cuestión estaba radicada en España.

Y ahí me surgió una pregunta inevitable: **¿qué podría estar pasando realmente?** Sin acceso al sistema interno, solo puede hablarse de una hipótesis técnica plausible. Y eso pretendo hacer en este artículo.

El problema no es menor. Si ese día era el **último día de pago**, muchas personas terminan **pagando intereses por un supuesto pago fuera de término**, cuando en los hechos **el pago se realizó dentro del plazo**. En algunos casos, incluso, esto puede derivar en antecedentes negativos en sistemas de información crediticia.

La pregunta entonces deja de ser anecdótica y pasa a ser técnica:  **¿cómo puede un sistema llegar a esa conclusión?**

## El problema no es el pago, es cómo se modela el tiempo

En sistemas financieros (y en sistemas reales en general) conviven dos conceptos que parecen triviales, pero no lo son:

- el **timestamp**, que representa el instante exacto en que ocurrió un evento (fecha + hora),
- y la **fecha contable** o **fecha valor**, que es el “día” que el sistema utiliza para aplicar reglas de negocio: vencimientos, cierres, intereses, penalidades.  

El error aparece cuando ambos conceptos se confunden o se derivan uno del otro sin el contexto adecuado.  

Hoy es práctica común —y correcta— almacenar timestamps en **UTC**. El problema surge cuando, a partir de ese timestamp, se calcula la fecha contable **sin convertir previamente a la zona horaria del usuario o del marco legal correspondiente**.

## Un ejemplo simple, pero realista

Supongamos el siguiente escenario:

1. una persona en Argentina (UTC−3), 
2. paga su tarjeta el **día del vencimiento** a las 22:48, 
3. el sistema registra correctamente el evento como timestamp en UTC: 01:48 del día siguiente, 
4. y luego deriva la fecha contable usando directamente ese timestamp. 

Desde el punto de vista técnico, el dato es consistente.  
Desde el punto de vista del usuario, el pago fue **en término**.  
Desde el punto de vista del sistema, el pago ocurrió **al día siguiente**.

Ese pequeño desfasaje de horas termina habilitando:

- intereses,  
- cargos,
- y eventualmente consecuencias crediticias.

No porque el usuario haya pagado tarde, sino porque el sistema **modeló mal el tiempo**.

## ¿Por qué siempre aparece una “hora límite”?

Cuando muchas personas reportan que el problema ocurre: después de las 19 hs, o después de las 21 hs, o “de noche” en general, no suele tratarse de una regla legal explícita.  

Suele tratarse de un **artefacto de implementación**.

Algunas causas frecuentes:

- cierres contables fijos definidos en otra zona horaria,
- procesos batch nocturnos que recalculan estados,
- derivación de fechas usando `DATE(timestamp_utc)`,
- sistemas pensados desde un país y usados en otro.

En este contexto, que una entidad esté radicada en otro país no es irrelevante: **las decisiones técnicas suelen arrastrar supuestos locales** que dejan de ser válidos cuando el sistema se usa globalmente. Por ejemplo, el usuario que se quejaba de que un banco de España registraba cualquier pago que se hiciera desde Argentina al día siguiente si se hacía después de las 19 hs. España está en UTC +2; Argentina en UTC -3. Entre las 19 hs y las 24 hs están esas cinco horas de diferencia: exactamente el tipo de desfasaje que aparece cuando los sistemas no convierten correctamente las zonas horarias antes de aplicar reglas de negocio.

## No es un problema legal, es un problema de diseño

Al menos en Argentina, no existe una regla general que diga que un pago electrónico deja de ser válido antes de las 24:00 del día del vencimiento. Si un pago se realiza ese día, está en término.

Cuando el sistema dice lo contrario, no está aplicando la ley: está aplicando **una representación defectuosa del tiempo**.

Y esto es importante:  

**el software no puede redefinir conceptos legales solo porque es más cómodo técnicamente**.  

Además, este tipo de errores no requieren sistemas complejos para aparecer; basta una decisión mal tomada en una línea de código.

## Un ejemplo técnico (adaptado) en Python / Django

Para ilustrar el problema desde el punto de vista del diseño, supongamos un **escenario adaptado** en el que una webapp estuviera implementada en Django.  
Esto **no implica** que el sistema financiero real utilice Django ni Python; el ejemplo sirve únicamente para mostrar **cómo se evita este tipo de errores**.

### El bug típico

Un error muy común es derivar la fecha contable directamente desde un timestamp en UTC:

```python
def fecha_contable_incorrecta(fecha_pago_utc):
    return fecha_pago_utc.date()
```

Si el pago ocurrió de noche en horario local, esta función empuja automáticamente el evento al día siguiente.

### Una implementación correcta

Una implementación segura separa claramente responsabilidades:

- UTC para almacenar,
- zona horaria local para decidir fechas,
- reglas de negocio basadas en fechas, no en timestamps crudos.

Ejemplo:

```python
import pytz
from django.utils import timezone

# Asumiendo que, si es naive, proviene de una fuente que usa UTC. En sistemas robustos, todos los timestamps deben ser aware.

ZONA_HORARIA_LOCAL = pytz.timezone("America/Argentina/Buenos_Aires")

def fecha_contable_correcta(fecha_pago_utc):
    if timezone.is_naive(fecha_pago_utc):
        fecha_pago_utc = timezone.make_aware(fecha_pago_utc, timezone.utc)

    fecha_local = fecha_pago_utc.astimezone(ZONA_HORARIA_LOCAL)
    return fecha_local.date()
```

Y luego, la evaluación de vencimiento:

```python
def pago_en_termino(fecha_pago_utc, fecha_vencimiento):
    fecha_pago = fecha_contable_correcta(fecha_pago_utc)
    return fecha_pago <= fecha_vencimiento
```

Con este enfoque:

- un pago a las 22:48 sigue siendo del día correcto,
- no se generan intereses indebidos,
- y el sistema refleja la realidad del usuario.

## El tiempo es uno de los dominios más traicioneros

El problema del tiempo en software es conocido, pero sigue subestimándose.  
No falla de forma ruidosa: falla **en los bordes**, en los casos límite, y con consecuencias reales.  

Cuando un pago hecho en término termina generando intereses, el problema rara vez es del usuario. En muchos casos, es simplemente una consecuencia de cómo se decidió modelar el tiempo dentro del sistema.

Diseñar bien estas decisiones no es un lujo ni una optimización:  
es parte central de construir sistemas justos, confiables y alineados con la realidad que dicen representar.

Si tu sistema financiero no sabe manejar husos horarios, no tenés un sistema financiero; tenés una máquina de generar intereses indebidos.
