---
layout: post
title: "Fuentes externas y frontera del dominio"
date: 2026-02-03
category: arquitectura
series: "Diseño evolutivo de sistemas"
series_part: 3
series_total: 3
description: "Dónde debe vivir la lógica de cambio de estado cuando el disparador viene desde fuera del sistema"
---

# Del documento al estado: encapsulando cambios en el modelo de dominio

Esta trilogía comenzó modelando **invariantes atemporales**, continuó demostrando cómo evolucionar **la experiencia sin romper el modelo**, y ahora cierra con el desafío de mayor riesgo: integrar **fuentes externas no confiables** sin contaminar la lógica del dominio.

El primer artículo definió los cimientos: eventos inmutables que capturan hechos, no estados derivados.  

El segundo mostró la flexibilidad: una UX que se adapta porque el modelo permanece intacto.  

Este tercero responde la pregunta inevitable: **¿dónde vive la lógica cuando el cambio viene desde fuera?**

La respuesta, consecuente con todo lo anterior:

> El input no decide el cambio.  
> El modelo lo hace.

---

## El problema general

Muchos sistemas operativos comparten este patrón:

- existe un sistema interno que modela entidades con estado,
- existe una fuente externa (PDF, Excel, listado),
- esa fuente indica que ciertas entidades deben cambiar de estado,
- el input es ruidoso, incompleto o no estructurado.

Pensar esto como un problema de parsing es un error.
Es un problema de **arquitectura de dominio**.

## Separar detección, decisión y ejecución

Un documento externo puede, como mucho, disparar una intención.
Nunca debería imponer directamente un cambio.

Conviene separar explícitamente tres etapas:

1. **Detección**: identificar entidades potencialmente afectadas.
2. **Decisión**: validar si el cambio es válido según el dominio.
3. **Ejecución**: aplicar el cambio de forma consistente y auditable.

Solo la última pertenece al modelo.

## El anti-patrón: lógica de negocio en el pipeline

Un pipeline típico mal diseñado hace esto:

```
leer documento
extraer identificadores
calcular nuevo estado
actualizar base de datos
```

El problema no es técnico, es conceptual:

- el script “sabe” cómo cambiar el estado,
- la lógica queda duplicada fuera del modelo,
- la UI y los procesos batch empiezan a divergir,
- las invariantes se vuelven implícitas.

Cuando el sistema crece, nadie sabe dónde vive la verdad.

## El patrón correcto: el modelo como frontera

El enfoque robusto invierte la responsabilidad:

```
leer documento
extraer candidatos
→ delegar en el modelo la decisión y la ejecución
```

El script no cambia estados.
El script dice: *“esto podría requerir una acción”*.

## Ejemplo completo: del documento externo al cambio de estado

Para volver tangible el patrón, recorramos el flujo completo con un ejemplo deliberadamente simple, pero alineado con los artículos anteriores.

Partimos de un sistema donde:

- las entidades representan personas del sistema,
- el estado jerárquico es **secuencial y no saltable**,
- los cambios deben ser auditables,
- el sistema interno es la fuente de verdad.

El documento externo solo **notifica**.

```text
Documento Externo
        ↓
[1. Detección: Extraer IDs]
        ↓
[2. Filtrado: ¿Existe en el sistema?] → Descartar
        ↓
[3. Decisión: Modelo (dry-run)]
        ↓
[4. Revisión de Resultados Simulados]
        ↓
[5. Ejecución: Modelo (confirmar)]
        ↓
[6. Auditoría y Resultado Final]
```

### 1. Detección: extraer candidatos sin semántica

La primera etapa es puramente mecánica.
No intenta entender el dominio ni validar nada.

```python
# asumimos una búsqueda de DNIs en un archivo pdf

import re

def detectar_identificadores(texto: str) -> set[str]:
    patron = re.compile(r"\b\d{8}\b") # serie de ocho dígitos consecutivos
    return set(patron.findall(texto))
```

Características de esta etapa:

- admite falsos positivos,
- no valida existencia,
- no conoce estados,
- no decide cambios.

Su objetivo es **no perder candidatos reales**.

### 2. Filtrado: existencia en el sistema interno

La siguiente capa usa el sistema como filtro semántico mínimo.

```python
def obtener_entidades_existentes(identificadores):
    # sólo verificar existencia - sin validaciones de estado o elegibilidad
    for dni in identificadores:
        entidad = Empleado.objects.filter(dni=dni).first()
        if entidad:
            yield entidad
```

Todavía no hay cambios.
Solo se responde:

> ¿Esta identidad existe en el sistema?

### 3. Decisión: delegar explícitamente al modelo

Este es el punto clave del diseño.

El pipeline:
- no calcula el nuevo rango,
- no conoce el orden jerárquico,
- no valida elegibilidad.

Solo expresa una intención:

```python
resultados = []

for empleado in empleados:
    resultado = empleado.actualizar_rango(
        origen="documento_externo_2026_01",
        dry_run=True,
    )
    resultados.append(resultado)
```

Toda la semántica ocurre dentro del modelo.

### 4. Ejecución: el modelo valida, decide y aplica

El método `actualizar_rango` encapsula:

- validación de invariantes ya descritas en el primer artículo,
- elegibilidad operativa,
- cálculo del siguiente estado,
- persistencia,
- auditoría.

Desde afuera, el pipeline recibe un resultado explícito:

```json
{
  "from": "Rango 1",
  "to": "Rango 2",
  "aplicado": false
}
```

o bien:

```json
{
  "from": "Rango 1",
  "to": "Rango 2",
  "aplicado": true
}
```

No hay inferencias implícitas.

### 5. Confirmación: ejecutar sin simulación

Una vez revisado el impacto, el mismo flujo se ejecuta sin *dry-run*:

```python
empleado.actualizar_rango(
    origen="documento_externo_2026_01",
    dry_run=False,
)
```

El comportamiento es idéntico.
La única diferencia es el efecto persistente.

### 6. Qué NO hace ninguna capa

Tan importante como el flujo es lo que queda explícitamente fuera:

- el documento no decide estados,
- el parser no conoce el dominio,
- el pipeline no muta datos,
- la UI no reimplementa reglas.

Toda la verdad vive en el modelo.

## Modelos operacionales

Una entidad pasiva solo expone datos.
Un modelo de dominio expone **operaciones**.

Ejemplos genéricos:

- `cuenta.aplicar_credito()`
- `suscripcion.renovar()`
- `pedido.confirmar()`
- `empleado.actualizar_rango()`

El nombre del método expresa una acción del dominio, no una mutación técnica.

## Qué debe hacer un método de cambio de estado

Un método de dominio debería:

1. Validar invariantes.
2. Verificar elegibilidad.
3. Determinar el nuevo estado.
4. Persistir el cambio.
5. Registrar trazabilidad.

Siempre igual, sin importar si es llamado desde:
- una UI,
- un script,
- una API,
- o un proceso batch.

## Ejemplo técnico: método operacional en el modelo

```python
class Empleado(models.Model):
    rango = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)

    def actualizar_rango(self, *, origen: str, actor=None, dry_run=False):
        if not self.activo:
            raise DomainError("Entidad inactiva")

        orden = JERARQUIA_ORDER
        if self.rango not in orden:
            raise DomainError(f"Rango desconocido: {self.rango}")

        idx = orden.index(self.rango)
        if idx + 1 >= len(orden):
            raise DomainError("Rango máximo alcanzado")

        nuevo_rango = orden[idx + 1]

        if dry_run:
            return {
                "from": self.rango,
                "to": nuevo_rango,
                "aplicado": False,
            }

        self.rango = nuevo_rango
        self.save(update_fields=["rango"])

        RegistroCambioRango.objects.create(
            empleado=self,
            rango_anterior=orden[idx],
            rango_nuevo=nuevo_rango,
            origen=origen,
            actor=actor,
        )

        return {
            "from": orden[idx],
            "to": nuevo_rango,
            "aplicado": True,
        }
```

Toda la lógica sensible vive en un solo lugar.

## Beneficios estructurales

- **Un solo lugar para la verdad**
- **UI y batch coherentes**
- **Auditoría explícita**
- **Idempotencia controlable**
- **Automatización sin miedo**

## El patrón completo de la serie

1. Modelar invariantes primero.
2. Diseñar experiencia sin romper el modelo.
3. Encapsular operaciones en el dominio.

El tercer punto evita que la automatización se convierta en un sistema paralelo.

## Cierre

Todo sistema que interactúa con fuentes externas termina enfrentando la misma tensión: alguien debe decidir cuándo y cómo cambia el estado.

Esa decisión no se resuelve con parsing ni con scripts más complejos, sino con un modelo bien definido. Un modelo que no es una estructura pasiva, sino una frontera operativa.

Cuando esa responsabilidad vive en el modelo, el resto del sistema se simplifica. Los pipelines dejan de interpretar, las interfaces dejan de replicar reglas y la automatización se vuelve predecible. El dominio permanece íntegro porque nunca delegó la decisión que lo define.