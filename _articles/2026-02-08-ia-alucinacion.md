---
layout: post
title: "Ética frente a la alucinación"
date: 2026-02-08
category: ciberseguridad
description: "Riesgos de alucinación y sesgo de prompt en VLMs aplicados a evidencia visual, y controles para reducir daño."
project: "Vigilant"
project_part: 3
project_total: 3
---

# El peligro del sesgo en IA generativa aplicada a evidencia visual

Los modelos generativos modernos —especialmente los modelos visión-lenguaje— pueden describir escenas con gran fluidez, tono técnico y aparente autoridad, incluso cuando la imagen es ambigua o insuficiente.

El resultado suena como un hecho.

Y en un contexto judicial o probatorio, afirmar algo categóricamente es una decisión crítica.

Este artículo analiza por qué ocurren las llamadas _alucinaciones_, cómo los prompts pueden introducir sesgo sin que el operador lo note y qué prácticas de diseño ayudan a reducir el riesgo cuando se utiliza IA para asistir análisis visual.

La tesis es simple:

> la IA puede priorizar revisión; nunca debe producir conclusiones probatorias.

## 1. El problema real no es el error, es la convicción

Un detector clásico (por ejemplo, un clasificador de objetos) suele fallar de forma visible:

- bounding box mal ubicada    
- score bajo
- clase incorrecta

El error es técnico, limitado y fácil de auditar.

Pero los modelos generativos son distintos.

Un modelo visión-lenguaje puede producir frases como:

> “La persona sostiene un arma corta en la mano derecha”.

Aunque:

- la imagen esté borrosa    
- el objeto sea ambiguo
- no exista suficiente evidencia visual

Y lo hace con lenguaje gramaticalmente perfecto y tono categórico.

El problema es que ese estilo de salida activa un sesgo cognitivo humano muy fuerte: **si suena profesional, debe ser correcto**.

Y ahí aparece el riesgo.

## 2. Por qué pasa

Estadística. Un modelo visión-lenguaje hace algo simple:

> predice el texto más probable dado la imagen + el prompt + su entrenamiento.

Tres fuentes de error se combinan:

### La imagen

Puede ser:

- baja resolución
- ruido
- motion blur
- compresión fuerte
- iluminación deficiente

La información real es limitada.

### El prompt

Puede inducir sesgo.

No es lo mismo preguntar: “Describe la escena” que: “¿Qué arma tiene en la mano?”.

La segunda presupone que hay un arma y el modelo intenta complacer esa presuposición.

### El entrenamiento

El dataset histórico puede contener correlaciones espurias:

- persona + gesto específico → arma
- noche + postura tensa → amenaza

El modelo aprende patrones plausibles, no verdades.

## 3. El sesgo del prompt: la trampa más silenciosa

El operador suele pensar que el modelo es objetivo. Pero el prompt es una instrucción semántica fuerte. Pequeños cambios alteran radicalmente la respuesta.

En el sesgo mencionado anteriormente, preguntar qué arma sostiene en la mano una persona introduce una narrativa que el modelo tiende a completar. 

Esto se parece mucho al **sesgo de confirmación humano**: buscar evidencia que respalde una hipótesis previa.

La diferencia es que aquí el sesgo está automatizado y amplificado.

## 4. Experimento mental sencillo

No hace falta un laboratorio sofisticado.

Cualquier persona puede comprobarlo con una imagen ambigua:

- una botella
- un teléfono
- un paraguas
- un objeto parcialmente oculto

Pregunte primero: “¿Qué objeto sostiene?”

Y luego: “¿Qué arma sostiene?”

En muchos casos, la segunda respuesta será más específica y más segura, aunque la imagen no cambie.

En análisis visual aplicado al contexto forense, eso es peligroso.

## 5. El riesgo específico en contextos probatorios

En sistemas de bajo impacto, una alucinación es molesta.

En contextos legales puede ser grave.

Problemas típicos:

### Falsa autoridad

Un reporte automático con lenguaje técnico parece más confiable de lo que realmente es.

### Sesgo de anclaje

El analista humano puede quedar influenciado por la primera descripción generada.

### Pérdida de trazabilidad

Es difícil explicar _por qué_ el modelo afirmó algo.

### No determinismo

Mismo frame + pequeña variación de prompt → respuestas distintas.

Eso choca directamente con requisitos de reproducibilidad.

## 6. Principio de diseño: tratar la IA como heurística, no como perito

La forma más segura de integrar IA generativa no es pedirle conclusiones.

Es usarla para:

- priorizar revisión
- reducir volumen
- generar hipótesis
- sugerir candidatos

Nunca para:

- afirmar hechos
- clasificar evidencia legal
- redactar conclusiones probatorias

Es un cambio de rol: de “decisor” a “asistente”.

## 7. Prácticas concretas para reducir riesgo

No existe mitigación perfecta, pero sí controles útiles.

### Preferir filtros deterministas cuando sea posible

Detectores clásicos (objetos, movimiento, reglas geométricas) son más auditables.

### Usar prompts neutrales

Evitar preguntas sugestivas o que presupongan conclusiones.

Mejor: “Describe lo que ves”
Peor: “Identifica el arma”

### Salidas estructuradas

Pedir JSON corto o etiquetas, no narrativa libre.

Menos lenguaje implica menos invención.

### Temperatura baja

Reducir aleatoriedad.

Aumenta consistencia entre ejecuciones.

### Múltiples evidencias

Confirmar eventos con:

- varios frames
- continuidad temporal
- movimiento consistente

Nunca con una única imagen.

### Humano obligatorio en el loop

Toda conclusión relevante debe ser validada por una persona.

Sin excepciones.

### Advertencias explícitas

Los reportes automáticos deben indicar claramente: “Salida generada por IA. Requiere verificación humana.”

La claridad legal importa.

## 8. Regla práctica

Una regla simple ayuda a mantener perspectiva:

Si el modelo produce texto que podría leerse en un informe judicial sin cambios, probablemente está haciendo demasiado. La IA no debería escribir conclusiones.

Debería señalar dónde mirar.

## 9. Conclusión

La IA generativa es poderosa, pero tiene una característica peligrosa: se equivoca de forma creíble.

Eso la vuelve especialmente riesgosa en contextos forenses, donde la confianza y la trazabilidad son tan importantes como la precisión.

El enfoque prudente no es prohibirla, sino ubicarla correctamente en la arquitectura:

- acelerar búsqueda    
- reducir carga humana
- priorizar revisión

Pero dejar la interpretación final en manos de personas.

Porque en evidencia digital, la certeza no puede ser estadística.  

Tiene que ser verificable.
