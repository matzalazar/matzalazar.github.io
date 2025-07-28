---
layout: post
title: "Por qué tu contraseña del WiFi basada en tu DNI es vulnerable"
date: 2025-07-28
categories: blog
---

# Por qué tu contraseña del WiFi basada en tu DNI es vulnerable

## Introducción

En Argentina, millones de routers entregados por proveedores de Internet vienen configurados de fábrica con contraseñas que aparentan ser complejas, pero que siguen **patrones predecibles y fácilmente explotables**. Una de las combinaciones más frecuentes es:

`0141234567`

A simple vista parece segura: tiene 10 caracteres, todos numéricos. Pero si desglosamos su estructura, descubrimos que es **matemáticamente sencilla** de romper.

Este artículo presenta un análisis técnico y computacional de por qué este tipo de claves son débiles, cómo pueden ser vulneradas con herramientas accesibles, y qué prácticas deberías adoptar para proteger tu red WiFi hogareña o de PyME.

## El patrón vulnerable

Uno de los principales ISP de Argentina suele configurar los routers con contraseñas generadas bajo esta lógica:

- Prefijo fijo: `004`, `014`, `044`
- Sufijo: número de DNI del titular del servicio (a veces omitiendo el último dígito)

Ejemplo:

`0142345678`

Esto introduce una **vulnerabilidad estructural por predictibilidad**: el universo de posibles contraseñas es acotado, y puede generarse de forma masiva.

## Tamaño real del diccionario

Supongamos un rango razonable de documentos:
- Desde DNI 15.000.000 hasta 45.000.000
- 3 prefijos posibles

El espacio de búsqueda es:

`(45.000.000 - 15.000.000) × 3 = 90.000.000 claves posibles`

Aunque parezca un número grande, en realidad tiene una **entropía baja**:

`log2(90e6) ≈ 26.42 bits`

Para ponerlo en contexto: una contraseña realmente segura debe superar los 64 bits de entropía.

## Tiempo estimado para romperla

En una PC moderna con un Ryzen 7 (5800X o similar), `aircrack-ng` puede probar entre 50.000 y 70.000 claves por segundo. Supongamos 60.000:

`90.000.000 / 60.000 = 1.500 segundos ≈ 25 minutos`

Con una GPU o entorno optimizado, ese tiempo baja a menos de 10 minutos. Y si limitás el diccionario a rangos conocidos de DNI (o uno específico), puede tomar solo segundos.

## Ejemplo de generación de diccionario

Con este script simple en Python podés generar el diccionario completo:

```python
prefijos = ['004', '014', '044']
for prefijo in prefijos:
	for dni in range(15000000, 45000000):
		print(f"{prefijo}{dni}")
```

Esto genera 90 millones de combinaciones en menos de 5 minutos, y el archivo resultante se puede usar directamente con `aircrack-ng`.

## Alternativa vía OSINT

Incluso si no hacés fuerza bruta, la predictibilidad permite ataques de ingeniería social:

1. En edificios, muchas veces las facturas del ISP quedan visibles.
2. Se obtiene el nombre del titular.
3. Se consulta su CUIL o DNI en registros públicos.
4. Se combinan 3 prefijos + DNI → 3 claves posibles.
5. Probabilidad de éxito altísima.

## Buenas prácticas para proteger tu red

1. **Cambiá la contraseña por defecto del router**
   - No uses DNI ni datos personales.
   - Usá frases largas y aleatorias.

2. **Desactivá WPS**
   - Este sistema permite ataques por PIN.

3. **Cambiá el nombre del SSID**
   - No reveles tu ISP o modelo de router.

4. **Actualizá el firmware**
   - Las actualizaciones corrigen vulnerabilidades conocidas.

5. **Auditá tu red periódicamente**
   - Usá herramientas como `nmap`, `airodump-ng`, `arp-scan`.

6. **Usá WPA3 si está disponible**

7. **Cambiá las credenciales de administración**
   - Nunca dejes "admin/admin".

8. **Deshabilitá el acceso remoto si no lo necesitás**

9. **Revisá logs y alertas del router**

10. **Simulá ataques controlados**
    - Verificá si podés capturar un handshake y resistir un diccionario.

## Conclusión

La longitud no garantiza seguridad. Cuando las contraseñas siguen un patrón predecible —como usar tu DNI— son extremadamente vulnerables.

Este artículo busca generar conciencia. La ciberseguridad doméstica no es un lujo, es una necesidad.

¿Usás este patrón? Verificalo ahora: mira el sticker de tu router. Si empieza con 014/044, **cambiala YA**.

## Descargo legal

Este artículo tiene fines educativos y de concientización. Todas las pruebas documentadas en [este repositorio](https://github.com/matzalazar/vulnerabilidades-wifi-arg) fueron realizadas sobre redes propias o entornos controlados.

El uso de estas técnicas sobre redes ajenas sin consentimiento explícito es un delito, tipificado por la Ley 26.388 del Código Penal Argentino.
