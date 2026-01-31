---
layout: post
title: "Cuando los tests pasan, y el bug vive igual"
date: 2026-01-07
category: arquitectura
description: "Bug silencioso en exportación Excel: cómo un flag de vista invisible causaba duplicación de datos"
---

El Excel de Rendición exportaba perfecto.  

Se filtraban ciertos datos desde la UI, se hacía click en _“Generar Reporte”_ y una vista usaba `openpyxl` para copiar un _modelo `.xlsx`_ y poblarlo con datos, fórmulas y parseos.  

Los tests pasaban.  

Pero cuando el área Comercial de la empresa editaba una celda, el número se copiaba mágicamente a otra hoja.  

¿Por qué pasaba esto? Porque había algo invisible viajando en ese Excel.

# Cuando los tests pasan… y el bug vive igual

Hay bugs que no te hacen dudar de tu código.  
Te hacen dudar de tus suposiciones.

Este fue uno de esos.

## El síntoma (o por qué esto no parecía un bug de lógica)

El problema apareció en una exportación Excel de “Rendición”.  
Nada raro: un archivo con una hoja **General** y varias hojas individuales.

El síntoma fue el siguiente:

1. Edité manualmente la celda `E13` en la hoja **General**.
2. Puse un valor simple, algo como `31`.
3. Guardé, imprimí… y noté algo raro.
4. Ese mismo `31` había aparecido **en la celda `E13` de la hoja individual siguiente**.

No en todas.  
No en una celda relacionada.  
Exactamente en la misma coordenada (`E13`) de la hoja inmediata.

Ese detalle fue clave.

## Primeras hipótesis (y todas equivocadas)

Hasta ese momento, todo indicaba un bug clásico:

- referencias cruzadas entre hojas,
- fórmulas mal copiadas,
- reutilización accidental de un objeto,
- o un error al clonar worksheets.

Pero había algo que no cerraba:  
`E13` en **General** era conceptualmente *independiente* del resto del Excel. No tenía ningún motivo para afectar a otra hoja.

Además:
- el archivo se exportaba bien,
- los valores iniciales eran correctos,
- no había fórmulas visibles.

Y los tests… todos verdes.

### El código que parecía inocente

En la exportación, cada hoja individual se generaba copiando una hoja base.  
Algo tan simple como esto:

```python
# Copia de la hoja base para cada efectivo
# Nada raro a simple vista
nueva_hoja = wb.copy_worksheet(hoja_base)
```

Nada en este código sugiere que editar una hoja pueda afectar a otra.  
Y sin embargo, el problema estaba ahí.

## El momento de quiebre: “esto no es un bug de datos”

El punto de inflexión no vino del código, vino del **comportamiento**.

El hecho de que:
- el valor se replicara **solo al editar**,
- **solo después de abrir el Excel**,
- y **solo en hojas específicas**,

me obligó a hacer una pregunta distinta:

> ¿Y si el bug no está en lo que genero, sino en cómo Excel interpreta el archivo?

Ahí dejé de mirar valores… y empecé a mirar **estado**.

## Root cause: el flag fantasma

Excel tiene una funcionalidad llamada **Sheet Grouping**.  
Cuando varias hojas están seleccionadas al mismo tiempo, cualquier edición que hagas en la hoja activa se replica en todas las hojas agrupadas, en la misma celda.

Eso explica todo:

- por qué el valor se copiaba solo al editar,
- por qué era la misma coordenada (`E13`),
- por qué afectaba solo a ciertas hojas,
- y por qué el backend no “veía” nada raro.

El archivo se estaba abriendo con **más de una hoja marcada como seleccionada**.

### Por qué eso pasaba (y acá sí entra la herramienta)

`openpyxl` copia las hojas de forma fiel:  
valores, estilos… y también atributos de vista (`sheet_view`).

Desde la perspectiva de la librería, esto es lo correcto:  
una copia exacta de la hoja original.

El problema no es `openpyxl`.  
El problema es que Excel interpreta ese estado de vista como “edición en grupo”.    
Y mi backend nunca tuvo en cuenta esa interpretación.  

Irónicamente, el bug ocurre porque `openpyxl` hace su trabajo demasiado bien: clona la hoja con tanta fidelidad que se lleva hasta el estado de selección de la interfaz.  

## El fix: imponer un invariante antes de guardar

La solución no fue reescribir lógica, sino **limpiar el estado** antes de entregar el archivo.

Antes de `wb.save()`:

```python
# Asegurar que no queden hojas agrupadas/seleccionadas
for sheet in wb.worksheets:
    sheet.sheet_view.tabSelected = False

# Activar explícitamente la primera hoja
wb.active = 0
```

Con eso, el Excel vuelve a abrir en un estado “normal”:
- una sola hoja activa,
- sin edición en grupo implícita.

## Y ahora lo importante: ¿por qué los tests no lo detectaron?

Porque este bug **vive fuera del alcance razonable del testing backend**.

Los tests pueden (y deben) verificar que:
- las hojas existen,
- los valores están bien,
- el archivo se genera sin errores.

Pero el bug:
- aparece **después**,
- cuando un humano edita el archivo,
- en un software externo,
- interpretando un flag de UI que no es parte del dominio del negocio.

No es que faltó un test.  
Es que el sistema **salió del runtime que los tests cubren**.

El runtime real, en producción, era Excel.

## Qué sí se puede hacer (sin caer en dogmas)

Este caso no enseña “hay que testear más”, sino algo más sutil:

> Hay que identificar invariantes en los bordes del sistema.

En este caso, el invariante es claro:

> **Un Excel exportado nunca debe abrir con hojas agrupadas.**

Eso sí se puede proteger con un test barato.

### Snippet de test de regresión (pytest)

```python
def test_exported_workbook_has_no_grouped_sheets():
    wb = build_rendicion_workbook(...)  # parámetros mínimos

    # Ninguna hoja debe quedar seleccionada
    for sheet in wb.worksheets:
        assert sheet.sheet_view.tabSelected is False

    # Debe haber una hoja activa explícita
    assert wb.active == 0
```

Este test:
- no abre Excel,
- no simula interacción humana,
- pero fija un **contrato técnico explícito** que antes era implícito.

## Cierre

Este bug no me enseñó a escribir mejores tests unitarios.

Me recordó que, como en otros problemas que encontré antes (timezones, feriados), a veces el error no está en tu lógica, sino en cómo el mundo exterior interpreta tus datos.  

Y que, muchas veces, la solución no es más código ni más tests, sino un paso de saneamiento que imponga un invariante simple:  

**nunca exportar hojas agrupadas.**  

Porque cuando los tests pasan,  
el bug igual puede estar esperando del otro lado.