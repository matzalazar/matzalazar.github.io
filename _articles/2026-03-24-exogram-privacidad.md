---
layout: post
title: "Privacidad como arquitectura"
date: 2026-03-24
category: arquitectura
description: "Las decisiones técnicas detrás de Exogram: sesiones HttpOnly, embeddings locales, email self-hosted y jurisdicción GDPR."
project: "Exogram"
project_part: 2
project_total: 3
---

# Privacidad como arquitectura: las decisiones técnicas detrás de Exogram

La privacidad en aplicaciones web se suele tratar como un problema de compliance: leer el GDPR, escribir una política de privacidad, agregar el banner de cookies, y tachar el ítem de la lista. El resultado es un sistema que cumple los requisitos formales mientras sigue enviando datos de usuarios a tres servicios de analytics, guarda tokens de autenticación en `localStorage`, y procesa emails a través de un proveedor de terceros radicado fuera de la jurisdicción europea.

Exogram parte de una premisa diferente: la privacidad es una propiedad arquitectural. No se agrega al final — se diseña desde el principio, en cada decisión del stack. Este artículo documenta esas decisiones: qué datos se recolectan y cuáles no, dónde vive la sesión de autenticación y por qué, qué datos salen del sistema y cuáles se procesan localmente, y por qué el servidor está en Alemania y no en Virginia.

## El dato mínimo: un email que nadie verá

El único dato personal que Exogram requiere para crear una cuenta es una dirección de email. No hay nombre real, no hay número de teléfono, no hay fecha de nacimiento. El campo existe en el modelo, pero está marcado explícitamente como dato de administración:

```python
# accounts/models.py
# Metadata (NUNCA expuesta en API pública)
verified_email = models.EmailField(
    verbose_name="Email verificado",
    help_text="Solo para admin/soporte. Nunca público."
)
full_name = models.CharField(
    max_length=100,
    blank=True,
    help_text="Solo para admin/soporte. Nunca público."
)
```

La identidad pública en la plataforma es el nickname — un nombre de usuario elegido durante el onboarding. El `PublicProfileSerializer`, que es lo que cualquier otro usuario puede ver de un perfil, expone exactamente tres campos: `nickname`, `bio` y `avatar`. Nada más.

La consecuencia técnica de esta separación es que el email nunca circula en la API. El login se hace con nickname y contraseña, no con email. Esto tiene una implicación de privacidad concreta: si alguien intercepta el tráfico de login (a pesar de HTTPS), no obtiene un dato que pueda correlacionar con otras plataformas. El nickname de Exogram puede ser cualquier cosa.

El campo `help_text` del modelo que dice "Tu identidad pública. Nadie verá tu email." es una restricción de diseño escrita en el código. Si en algún momento alguien intentara agregar el email a una respuesta de API, ese comentario es el recordatorio de que eso viola una decisión deliberada.

Incluso el flujo de recuperación de contraseña está diseñado para no revelar si un email existe en el sistema. La respuesta al endpoint es siempre la misma frase genérica, independientemente de si el email está registrado:

```python
# Siempre retorna el mismo mensaje para no exponer si el email existe.
# Un atacante no puede usar este endpoint para enumerar usuarios registrados.
return Response({
    'message': 'Si el email está registrado, recibirás un enlace en breve.'
})
```

Esta técnica — respuesta uniforme para casos positivos y negativos — es estándar en sistemas que toman la privacidad en serio, pero rara vez se implementa en proyectos que no la piensan explícitamente.

## El token de sesión que JavaScript no puede leer

La mayoría de los tutoriales de autenticación con JWT en SPAs instruyen al desarrollador a guardar el token en `localStorage`. Es la solución más simple: `localStorage.setItem('token', jwt)`, y después incluirlo en cada request como `Authorization: Bearer <token>`. El problema es que `localStorage` es accesible desde cualquier script que corra en la página. Un ataque XSS exitoso — un script inyectado a través de cualquier vulnerabilidad, incluyendo una dependencia de frontend comprometida — puede leer ese token, exfiltrarlo, y autenticarse como el usuario afectado indefinidamente.

Exogram guarda los tokens JWT exclusivamente en cookies con el flag `HttpOnly`. La propiedad `HttpOnly` hace que el navegador incluya la cookie en los requests pero la bloquee para JavaScript: `document.cookie` no la ve. Un XSS no puede robar lo que no puede leer.

```python
# accounts/authentication.py — el backend setea las cookies en la respuesta
response.set_cookie(
    key=settings.JWT_ACCESS_COOKIE_NAME,     # 'exo_access'
    value=str(access_token),
    httponly=True,
    secure=settings.JWT_COOKIE_SECURE,       # True en producción (solo HTTPS)
    samesite=settings.JWT_COOKIE_SAMESITE,   # 'Lax'
    path=settings.JWT_ACCESS_COOKIE_PATH,    # '/api/'
)
response.set_cookie(
    key=settings.JWT_REFRESH_COOKIE_NAME,    # 'exo_refresh'
    value=str(refresh_token),
    httponly=True,
    secure=settings.JWT_COOKIE_SECURE,
    samesite=settings.JWT_COOKIE_SAMESITE,
    path=settings.JWT_REFRESH_COOKIE_PATH,   # '/api/auth/'
)
```

Hay dos tokens, con paths deliberadamente diferentes. El access token tiene path `/api/` y vive 20 minutos: el navegador lo incluye en cada request a la API. El refresh token tiene path `/api/auth/` y vive 7 días: el navegador *solo* lo incluye en los requests a ese subpath específico, que es donde se renueva la sesión. El token de larga vida nunca viaja en requests normales — solo viaja cuando es necesario renovar la sesión. Esto minimiza la ventana de exposición del token más valioso.

Que las cookies sean automáticamente enviadas por el navegador introduce el problema opuesto: CSRF. Si el token viaja en una cookie, un sitio externo malicioso podría hacer un request a la API y el navegador incluiría la cookie. La protección es el patrón Double Submit Cookie: Django emite una cookie de CSRF que *sí* es legible por JavaScript (no tiene `HttpOnly`), y el frontend la lee y la incluye como header `X-CSRFToken` en cada request mutante. El backend verifica que el valor del header coincida con el valor de la cookie. Un atacante externo no puede leer la cookie por Same-Origin Policy, por lo tanto no puede construir el header correcto.

```javascript
// frontend/src/services/api.js
// Lee el token CSRF de la cookie y lo incluye como header en mutaciones
if (MUTATING_METHODS.has(method)) {
    const csrfToken = getCookieValue('csrftoken')
    if (csrfToken) headers['X-CSRFToken'] = csrfToken
}
```

El resultado es un esquema que resiste XSS (el token JWT no es legible) y CSRF (el header requerido no puede ser fabricado externamente). No es un esquema complicado — es el esquema correcto, que simplemente requiere más trabajo inicial que `localStorage`.

## Los datos que nunca salen del sistema

La plataforma tiene dos componentes que en otras implementaciones típicamente involucran servicios externos: los embeddings semánticos para búsqueda y los emails transaccionales.

Los highlights son anotaciones personales de lecturas. Son el dato más sensible de la plataforma: revelan qué lee una persona, qué le importa, cómo piensa. Generar embeddings de ese contenido enviándolo a una API de OpenAI o Cohere implicaría que esos textos personales salen del sistema para ser procesados por un tercero. El ADR correspondiente lo documenta directamente: "user highlights never leave the system for processing. Full privacy."

La alternativa implementada es cargar el modelo de embeddings localmente en el worker de Celery usando ONNX Runtime. El modelo es `paraphrase-multilingual-MiniLM-L12-v2`, 470 MB, que corre en CPU. Cada highlight se vectoriza en el servidor propio, sin ninguna llamada externa. El costo es ~1 GB de RAM extra en el worker. El beneficio es que los textos de los usuarios no viajan a ningún proveedor.

Lo mismo aplica al email. Los correos transaccionales — invitaciones, resets de contraseña — podrían enviarse a través de SendGrid, Mailgun o Amazon SES. Son servicios confiables, con buena deliverability, y con integraciones triviales. El problema es que esos servicios procesan los emails (incluyendo el contenido y los destinatarios) en sus propios sistemas. Para un servicio de acceso restringido por invitación, los emails de invitación contienen información sobre quién es usuario y a quién quieren sumar.

Exogram usa Postal, un servidor SMTP self-hosted que corre en el mismo stack de Docker. Los emails nunca pasan por ningún intermediario:

```yaml
# docker-compose.yml
postal:
    image: ghcr.io/postalserver/postal:latest
    # Solo levanta con --profile mail. En desarrollo,
    # los emails se imprimen en consola sin enviar nada.
    profiles: ["mail"]
```

La complejidad operacional es real: hay que configurar registros SPF, DKIM y PTR/rDNS, y hay que gestionar la deliverability manualmente. Es trabajo que los servicios gestionados eliminan. Pero es trabajo que se hace una vez, y el resultado es que ningún proveedor externo tiene acceso a los destinatarios de los emails del sistema.

## El servidor en Alemania: jurisdicción como decisión técnica

Exogram corre en un servidor VPS CX33 de Hetzner en el datacenter de Falkenstein, Alemania. Esta elección no es solo de precio/performance — es una decisión de jurisdicción.

Los datos almacenados en servidores dentro de la Unión Europea están protegidos por el GDPR. Eso significa, en términos prácticos, que no pueden ser accedidos ni transferidos a terceros sin base legal explícita, que el usuario tiene derecho a acceder a sus datos y a solicitar su eliminación, y que los incidentes de seguridad deben reportarse en plazos específicos. Un servidor en Virginia, Oregon, o cualquier región de AWS/GCP/Azure en Estados Unidos queda fuera de esa protección, bajo la jurisdicción de las leyes estadounidenses, que incluyen instrumentos como las National Security Letters que permiten acceso gubernamental a datos sin notificación al afectado.

Esto no es una postura política: es una consecuencia técnica de elegir dónde vive la infraestructura. Hetzner, como empresa alemana operando en territorio alemán, está sujeta a la regulación europea. Ese contexto jurídico es parte del diseño del sistema tanto como cualquier decisión de código.

## El derecho a salir: export y borrado como funcionalidades de primera clase

El GDPR establece dos derechos fundamentales: el derecho de acceso (saber qué datos tiene el sistema sobre vos) y el derecho al olvido (solicitar que esos datos sean eliminados). En la práctica, muchos sistemas implementan estos derechos como procesos manuales lentos que requieren contactar soporte. Exogram los implementa como endpoints de API que cualquier usuario autenticado puede usar directamente.

El export devuelve todos los datos del usuario en JSON: perfil, highlights, notas, libros:

```python
# accounts/views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_data(request):
    """
    Exporta todos los datos del usuario en formato JSON.
    GET /api/me/export/
    """
    profile = request.user.profile
    highlights = Highlight.objects.filter(user=profile)
    data = {
        'export_date': timezone.now().isoformat(),
        'profile': {
            'nickname': profile.nickname,
            'bio': profile.bio,
            'email': profile.verified_email,  # En el export propio, el email sí aparece
            # ...
        },
        'highlights': [ ... ]
    }
    return Response(data)
```

El borrado de cuenta es un hard delete — no soft delete, no desactivación, no "tu cuenta quedará inactiva por 30 días". El registro del usuario y todos los datos asociados se eliminan por cascade en la base de datos. El endpoint requiere confirmación explícita del string `"DELETE_MY_ACCOUNT"` para prevenir eliminaciones accidentales:

```python
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """
    HARD DELETE — No reversible
    Requiere: { "confirm": "DELETE_MY_ACCOUNT" }
    """
    if request.data.get('confirm') != 'DELETE_MY_ACCOUNT':
        return Response({'error': '...'}, status=400)

    request.user.delete()  # CASCADE: elimina Profile, highlights, notas, threads
```

Que el borrado sea irreversible es una consecuencia directa de tomar la privacidad en serio. Un sistema que guarda los datos "por si acaso" después del borrado no está implementando el derecho al olvido — está posponiéndolo.

## La capa de transporte: Caddy y los headers de seguridad

El proxy inverso que termina TLS es Caddy. La elección sobre Nginx no es principalmente de performance sino de operación: Caddy gestiona automáticamente los certificados TLS via Let's Encrypt sin configuración de certbot ni crons de renovación. Menos superficie de configuración manual significa menos oportunidades de que un certificado venza sin que nadie lo note.

Caddy también emite headers de seguridad para todas las rutas:

```
Content-Security-Policy
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

El `Referrer-Policy` controla qué información de origen envía el navegador en requests externos — relevante para no filtrar URLs internas de la plataforma a recursos de terceros. El `Permissions-Policy` declara explícitamente que la aplicación no solicita acceso a cámara, micrófono ni geolocalización. Django también emite estos headers por su propio middleware, produciendo doble cobertura en caso de que alguna ruta no pase por Caddy.

## El costo real de este diseño

Sería deshonesto presentar este stack sin nombrar sus costos.

Self-hosting Postal implica gestionar deliverability de email, que es un problema difícil. Los grandes ESPs tienen reputación de IP construida durante años. Un servidor nuevo puede tener emails que van a spam mientras esa reputación se establece. Hay configuración de DNS que hacer correctamente y que puede variar entre proveedores.

Correr los embeddings localmente requiere ~1 GB de RAM adicional en el worker de Celery y un modelo de 470 MB que hay que persistir y gestionar. Un deployment nuevo necesita descargar ese modelo antes de poder procesar highlights.

Un VPS en Alemania tiene latencia más alta para usuarios en América Latina que un servidor en São Paulo o en Virginia. Para una aplicación de lectura — uso asincrónico, no tiempo real — esa latencia es aceptable. Para otras aplicaciones no lo sería.

Ninguna de estas limitaciones es accidental. Son los tradeoffs de elegir control sobre conveniencia. La pregunta relevante no es si este diseño es universalmente superior, sino si los tradeoffs tienen sentido para el producto específico. Para una plataforma cuyo propósito es que los usuarios traigan sus lecturas más personales y las compartan con confianza, la respuesta es sí.

La privacidad se construye en el código.
