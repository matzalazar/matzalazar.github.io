---
layout: post
title: "Diseño social sin métricas de vanidad"
date: 2026-03-24
category: arquitectura
description: "Cómo diseñar la capa social de una plataforma de lectura sin algoritmos de engagement, likes ni contadores de seguidores."
project: "Exogram"
project_part: 1
project_total: 3
---

# Diseño social sin métricas de vanidad: las decisiones de red de Exogram

Las redes sociales que conocemos resuelven un problema de optimización: maximizar el tiempo que el usuario pasa en la plataforma. Ese objetivo no es neutro. Produce un diseño específico: feeds algorítmicos que premian el contenido más provocador, contadores de likes que generan ciclos de aprobación, notificaciones diseñadas para interrumpir, métricas de popularidad que convierten a las personas en marcas.

Exogram parte de un objetivo diferente. Es una plataforma de subrayados de lectura — los usuarios importan sus highlights de Kindle, los anotan, y observan cómo se conectan semánticamente. El componente social no es el producto principal: es la capa que permite que esa práctica de lectura tenga una dimensión colectiva sin degradar la calidad de lo que cada uno construye. El desafío de diseño, entonces, es opuesto al de las redes convencionales: cómo hacer que la dimensión social exista sin que se coma todo lo demás.

Las decisiones que siguen son la respuesta a ese problema.

## El árbol de invitaciones como grafo social

La decisión más estructural de Exogram es la ausencia de registro abierto. La única forma de crear una cuenta es recibir una invitación de alguien que ya está en la plataforma, o ser activado desde la lista de espera por ese mismo usuario.

Esto produce una estructura de datos que es el grafo social subyacente del sistema: el árbol de invitaciones.

```python
# accounts/models.py
class Profile(models.Model):
    # ...
    invited_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name='invited_users',
        on_delete=models.SET_NULL,
    )
    # Profundidad desnormalizada para evitar traversals O(N) en cada request.
    # 0 = nodo raíz. Se calcula al momento de la invitación como depth(parent) + 1.
    invitation_depth = models.IntegerField(default=0)
```

Cada usuario tiene un padre en el árbol (quien lo invitó) y puede tener hijos (a quienes invitó). La profundidad está desnormalizada como campo en el perfil, lo que evita traversals recursivos en cada consulta. El grafo no es bidireccional ni simétrico: saber quién invitó a quién define la posición estructural de cada persona en la red, y esa posición tiene consecuencias directas sobre qué puede hacer.

La razón para esta decisión es directa: "Exogram no es una red para todos, es una red para lectores comprometidos". Pero hay una consecuencia técnica que vale explicar. El árbol de invitaciones no es solo un mecanismo de control de acceso: es el sistema de permisos. Toda la lógica de quién puede comentar qué, quién puede enviar mensajes a quién, y quién aparece en el feed de descubrimiento está expresada en términos de distancia en ese árbol.

## Privacidad granular: cuatro palancas, no un interruptor

El modelo de privacidad de Exogram no es binario. No hay un botón de "cuenta pública / cuenta privada" como en la mayoría de las redes. Hay cuatro controles independientes que pueden combinarse:

El primero es la **visibilidad de cada highlight**, que tiene tres estados: privado (solo el dueño), unlisted (accesible por link directo), y público (visible en el perfil). Esta granularidad existe porque un usuario puede querer que algunos subrayados sean parte de su perfil público y otros sean notas personales que nunca compartiría. El estado se controla highlight por highlight, no a nivel de cuenta.

El segundo es el **modo ermitaño**, que desactiva completamente la presencia pública del usuario: su perfil no es visible para terceros, sus highlights públicos tampoco, no puede recibir mensajes ni comentarios externos. Puede seguir usando la plataforma, puede comentar en highlights ajenos si está dentro del rango de red permitido, pero es invisible hacia afuera. Es el equivalente a "quiero los beneficios del sistema sin exposición".

El tercero es el flag de **descubrimiento**, que controla si el usuario aparece en el feed de lectores afines. Si está desactivado, el usuario no aparece como sugerencia para nadie, y además no tiene acceso a ver sugerencias él mismo. La simetría es intencional: si no querés ser descubierto, tampoco usás el sistema de descubrimiento.

El cuarto es `comment_allowance_depth`, que es el control más inusual y el que más directamente refleja la filosofía del sistema.

## La profundidad de comentarios como modelo de confianza social

```python
# accounts/models.py
# Controla cuántos saltos en el árbol de invitaciones puede
# recorrer un usuario para llegar a comentar en tus highlights.
# 0 = solo vos. 1 = vos + padres e hijos directos. 2 = default.
# Rango: 0-10. Promovido automáticamente de 0 a 1 a los 30 días.
comment_allowance_depth = models.IntegerField(default=2)
```

Este campo responde a una pregunta que las redes convencionales no se hacen: ¿quién tiene permiso de hablarme? En Twitter, cualquiera puede responder a cualquiera. En Instagram, los comentarios son públicos si la cuenta es pública. El modelo por defecto es apertura total, con la opción de bloquear a personas específicas después del hecho.

Exogram invierte esa lógica. El acceso por defecto está acotado por la distancia en el árbol de invitaciones. Un usuario recién llegado entra con `comment_allowance_depth = 0`: puede leer, puede subrayar, pero no puede comentar en highlights ajenos hasta que el sistema lo promueve automáticamente a depth=1 luego de treinta días. La promoción es automática y no requiere intervención manual, pero tampoco es instantánea.

```python
# books/management/commands/promote_trust_levels.py
# Tarea diaria. Criterio deliberadamente conservador:
# solo se promueve una vez, y solo si lleva 30+ días en la plataforma.
candidates = Profile.objects.filter(
    created_at__lte=cutoff_date,
    comment_allowance_depth=0,
    trust_promoted_at__isnull=True,
)
```

La implementación es un management command que corre diariamente vía Celery Beat. Su diseño es conservador en dos sentidos: la promoción ocurre una sola vez (no hay promociones automáticas más allá de depth=1), y el criterio es puramente temporal. No hay métricas de "actividad" que aceleren o demoren la promoción, porque esas métricas crearían incentivos para generar actividad artificial.

A partir de depth=1, el usuario puede ajustar manualmente su `comment_allowance_depth` entre 0 y 10. Puede cerrarlo completamente o abrirlo hasta 10 saltos, cubriendo prácticamente toda la red conectada en la mayoría de los escenarios reales.

## Followers sin contadores: la filosofía zen del seguimiento

El modelo de seguimiento existe pero está diseñado para no importar como métrica.

```python
# social/models.py
class UserFollow(models.Model):
    follower  = models.ForeignKey(Profile, related_name='following_set', on_delete=models.CASCADE)
    following = models.ForeignKey(Profile, related_name='followers_set', on_delete=models.CASCADE)

    class Meta:
        # "Filosofía Zen: Nadie sabe quién lo sigue ni cuántos seguidores tiene.
        #  Solo sirve para ver los highlights de esta persona en tu propio feed."
        unique_together = ('follower', 'following')
```

El comentario en el código es literal: seguir a alguien no genera ninguna notificación para quien es seguido. No hay contador de seguidores expuesto en la API pública ni en el perfil. El `PublicProfileSerializer` solo expone `nickname`, `bio` y `avatar`. Ninguna otra cosa.

```python
# accounts/serializers.py — esto es todo lo que el mundo ve de un perfil
class PublicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Profile
        fields = ['nickname', 'bio', 'avatar']
```

La ausencia es funcional. El número de seguidores es uno de los mecanismos más potentes que tienen las redes sociales para crear jerarquías de visibilidad. Una cuenta con 50.000 seguidores no solo llega a más gente: es *percibida como más válida*. Esa percepción cambia el comportamiento de quien publica y de quien consume. Eliminar el contador no es un detalle cosmético: es una decisión sobre qué tipo de interacciones la plataforma quiere favorecer.

## Threads privados: mensajería con fricción intencional

La mensajería directa en Exogram tiene restricciones que en otro contexto parecerían limitaciones técnicas pero son decisiones de diseño.

Los threads son estrictamente uno a uno — no hay grupos, no hay canales, no hay conversaciones con más de dos participantes. Solo se puede iniciar un thread con alguien que esté en la misma red de invitaciones: `are_in_same_network()` verifica que exista algún camino en el árbol que conecte a ambas personas. Hermit mode bloquea la posibilidad de ser contactado. No hay notificaciones de nuevos mensajes: el cliente hace polling periódico. Los mensajes son inmutables una vez enviados — no hay edición, no hay eliminación, no hay indicadores de lectura.

Cada una de estas restricciones agrega fricción. La fricción es intencional. Mensajear a alguien requiere que ya exista una conexión estructural en el árbol, lo que significa que hay un contexto mínimo previo. La ausencia de notificaciones push elimina la presión de respuesta inmediata. La inmutabilidad de los mensajes hace que el medio no sea adecuado para conversaciones rápidas o volátiles. El contexto optativo de libro (`context_book_title`) sugiere cuál debería ser el punto de partida de una conversación.

El resultado es un sistema de mensajería que funciona mejor para intercambios reflexivos que para chat en tiempo real. Esa es exactamente la intención declarada en la documentación: "mini-foro de la antigua internet, sin likes, sin contadores, sin algoritmos".

## Descubrimiento por afinidad semántica, no por popularidad

El feed de descubrimiento no rankea usuarios por popularidad ni por actividad reciente. Calcula la distancia coseno entre el centroide semántico del usuario — el promedio de los vectores de todos sus highlights — y los centroides de los demás usuarios visibles. Los más cercanos semánticamente son los que aparecen.

Este mecanismo tiene una propiedad importante: es completamente ciego a la popularidad. Un usuario con tres highlights y un perfil semántico muy particular puede aparecer antes que uno con mil highlights si su centroide está más cerca del tuyo. No hay forma de "gaming" porque no hay métrica que optimizar.

El acceso al descubrimiento está condicionado por el flag `is_discoverable`. La simetría aquí es una consecuencia lógica: si el sistema de descubrimiento se basa en exponer tu perfil semántico a otros, no tiene sentido que puedas consumir perfiles ajenos sin exponer el tuyo.

## Los tradeoffs honestos

Este diseño tiene costos reales que vale nombrar.

El más obvio es el crecimiento. Con un máximo de diez invitaciones por usuario y sin registro abierto, la plataforma no puede crecer viralmente. No hay mecanismo de "compartir" que traiga usuarios nuevos desde fuera. El crecimiento es aritmético en el mejor caso, y requiere que cada usuario existente tome una decisión activa de invitar a alguien. El ADR correspondiente lo documenta sin rodeos: "el crecimiento es lento por diseño. Esto es intencional".

El segundo costo es la accesibilidad. Alguien que quiere usar Exogram pero no conoce a ningún usuario activo no puede entrar directamente. La lista de espera existe como válvula de escape, pero depende de que algún usuario con cuota disponible decida activar a esa persona. Es un proceso manual, no automático.

El tercer costo es la ausencia de loops de engagement. Las redes sociales convencionales son adictivas en parte porque el feedback es inmediato y variable: a veces tu publicación recibe muchos likes, a veces pocos, y esa variabilidad activa mecanismos de recompensa intermitente. Exogram no tiene ese loop. No hay likes. No hay notificaciones de comentarios. No hay contador de visualizaciones. Un usuario que publica subrayados no recibe señales de que alguien los está leyendo o valorando, salvo que ese alguien inicie una conversación explícita.

Para algunos usuarios, esto es un alivio. Para otros, es desorientador. La ausencia de feedback hace difícil saber si lo que uno comparte es relevante para alguien más. Es un tradeoff consciente: la plataforma elige no usar esas señales como mecanismo de retención porque las consecuencias de ese mecanismo — la optimización del contenido para maximizar reacciones — son incompatibles con el tipo de práctica que quiere sostener.

La pregunta que este diseño responde no es "¿cómo hacemos crecer la red?" sino "¿cómo hacemos que la red que existe funcione bien para lo que importa?". Son preguntas distintas, y responderlas produce plataformas distintas.
