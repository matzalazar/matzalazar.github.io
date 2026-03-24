---
layout: post
title: "Búsqueda semántica sin LLMs"
date: 2026-03-24
category: datos
description: "pgvector, distancia coseno y embeddings locales con ONNX para conectar subrayados de libros por similitud de ideas."
project: "Exogram"
project_part: 3
project_total: 3
---

# Búsqueda semántica sin LLMs: pgvector, distancia coseno y embeddings locales

Hay una categoría de problemas para los que los LLMs son la solución obvia hasta que uno se detiene a pensar qué hace exactamente el problema. Este es uno de esos casos.

Exogram es una plataforma de subrayados de lectura. Los usuarios importan sus highlights de Kindle, los organizan, los anotan. Una funcionalidad central es conectar subrayados semánticamente similares — no los del mismo libro, sino los que comparten una idea a través de libros y autores distintos. Un fragmento de Borges sobre la memoria y uno de Oliver Sacks sobre lo mismo, escritos en géneros y décadas diferentes, deberían encontrarse. Un fragmento sobre incertidumbre en economía y otro sobre incertidumbre en física cuántica también.

Ese es el problema concreto. Y la solución no requiere un LLM.

## Por qué la búsqueda por palabras clave no alcanza

La búsqueda léxica — `ILIKE '%memoria%'`, índices de texto completo, incluso BM25 — resuelve el problema de encontrar documentos que contienen una palabra o sus variantes morfológicas. Pero el problema semántico es diferente: dos textos pueden hablar exactamente de lo mismo sin compartir ninguna palabra clave relevante.

"La certeza es una ilusión confortable" y "Vivir con ambigüedad es condición de todo pensamiento honesto" comparten una idea central. No comparten tokens. Una búsqueda léxica las trataría como textos completamente distintos.

Lo que necesitamos es una representación numérica del *significado* de un texto — un vector en un espacio donde la proximidad geométrica corresponda a similitud semántica. Ese es el rol de los embeddings.

## La herramienta matemática: distancia coseno

Antes de hablar de embeddings, vale entender qué métrica se usa para compararlos.

La distancia coseno entre dos vectores **A** y **B** se define como:

```
distancia_coseno(A, B) = 1 - (A · B) / (||A|| × ||B||)
```

El resultado varía entre 0 (vectores idénticos en dirección) y 2 (vectores opuestos), aunque en la práctica con embeddings normalizados se trabaja entre 0 y 1. Lo importante es que mide el *ángulo* entre los vectores, no su magnitud. Eso es relevante porque nos interesa la dirección semántica, no cuán "largo" sea el vector.

La distancia coseno es una herramienta matemática genérica. Lo que la hace semánticamente útil es que los vectores sobre los que se opera son embeddings generados por un modelo de lenguaje entrenado para que textos de significado similar produzcan vectores de dirección similar. Sin esa propiedad, calcular la distancia coseno entre dos vectores aleatorios de 384 dimensiones no tiene ningún significado.

Este punto es importante: la magia no está en la distancia coseno. Está en los embeddings.

## El modelo: paraphrase-multilingual-MiniLM-L12-v2

El modelo elegido es `paraphrase-multilingual-MiniLM-L12-v2`, exportado en formato ONNX desde Hugging Face. Sus características determinaron la elección:

**384 dimensiones.** Un balance razonable entre capacidad expresiva y costo de almacenamiento. Un modelo como `text-embedding-ada-002` de OpenAI produce vectores de 1536 dimensiones — cuatro veces más pesados en disco, en memoria y en tiempo de consulta, sin garantía de que ese delta de calidad importe para este caso de uso.

**Multilingüe.** Los highlights de los usuarios están en español, inglés, o mezclas de ambos. El modelo soporta más de 50 idiomas, lo que significa que un fragmento en español y su equivalente conceptual en inglés deberían tener vectores cercanos.

**ONNX Runtime sin PyTorch.** Esta es quizás la decisión más pragmática del stack. El mismo modelo puede cargarse con `sentence-transformers` sobre PyTorch, pero PyTorch suma ~1.5 GB de dependencias a la imagen Docker. ONNX Runtime es el motor de inferencia sin el framework de entrenamiento: la imagen pesa significativamente menos, el arranque es más rápido, y el modelo funciona igual.

```python
class PureONNXEmbeddingModel:
    """
    Modelo de embeddings usando ONNX Runtime puro.

    Modelo: paraphrase-multilingual-MiniLM-L12-v2
    - Multilingüe (50+ idiomas), incluyendo español
    - 384 dimensiones de salida
    - ~470MB en disco / ~1GB en RAM en runtime
    - Sin dependencias de PyTorch, Transformers o SentencePiece
    """

    def encode(self, texts, normalize=True):
        # ...

        # Mean pooling ponderado por attention mask
        token_embeddings = outputs[0][0]      # [seq_len, hidden_size]
        attention_mask   = inputs['attention_mask'][0]

        mask_expanded  = np.expand_dims(attention_mask, -1).astype(float)
        sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=0)
        sum_mask       = np.sum(mask_expanded, axis=0)
        embedding      = sum_embeddings / np.maximum(sum_mask, 1e-9)

        # Normalización L2 — necesaria para que la distancia coseno sea
        # equivalente al producto escalar, simplificando la query en pgvector
        if normalize:
            norms      = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.maximum(norms, 1e-9)

        return embeddings
```

El pooling elegido es mean pooling ponderado por attention mask, no el token CLS. La razón es que el token CLS captura una representación global pero depende fuertemente de cómo el modelo fue preentrenado. Mean pooling sobre todos los tokens activos tiende a ser más robusto para frases cortas y de longitud variable — exactamente el tipo de texto que son los highlights.

La normalización L2 al final hace que el producto escalar entre dos vectores sea equivalente a su similitud coseno, lo que permite usar los índices de pgvector de manera óptima.

**Por qué no una API externa.** La alternativa más obvia era llamar a `text-embedding-ada-002` o `text-embedding-3-small` de OpenAI. El razonamiento para descartarla fue doble: los highlights de los usuarios son anotaciones personales de sus lecturas, y enviarlos a un servicio externo para procesarlos tiene implicancias de privacidad que no vale introducir cuando existe una alternativa local. El segundo argumento es el costo: cero por consulta frente a un costo por token que escala con el volumen. Para este caso, la calidad del modelo local es suficiente.

## pgvector: el almacén vectorial que ya estaba en el stack

Una vez resuelto el modelo, la pregunta es dónde almacenar los vectores y cómo consultarlos por similitud.

Las opciones dedicadas son conocidas: Pinecone, Qdrant, Weaviate, Milvus. Todas resuelven exactamente este problema y tienen rendimiento excelente a escala de millones de vectores. También suman un servicio más al stack, con su latencia de red, su autenticación, su sincronización con la base de datos principal y su punto de falla propio.

La decisión fue usar `pgvector`, la extensión de PostgreSQL que agrega un tipo `vector` con operadores de similitud. El razonamiento es directo: el proyecto ya usa PostgreSQL. Agregar `pgvector` es cambiar la imagen base de `postgres:16` a `pgvector/pgvector:pg16` y habilitar la extensión. El esquema sigue siendo gestionado por migraciones de Django como cualquier otro campo:

```python
# books/models.py
class Highlight(models.Model):
    # ...
    # Embedding vectorial para similitud semántica
    # Modelo: paraphrase-multilingual-MiniLM-L12-v2 — 384 dimensiones, multilingüe
    embedding = VectorField(dimensions=384, null=True, blank=True)

    class Meta:
        indexes = [
            HnswIndex(
                name='highlight_embedding_hnsw',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            ),
        ]
```

El índice HNSW (*Hierarchical Navigable Small World*) es el tipo de índice aproximado estándar para búsqueda vectorial. `m=16` controla la conectividad del grafo; `ef_construction=64` controla la precisión durante la construcción. Ambos valores son conservadores y apropiados para el volumen esperado (miles a decenas de miles de vectores por usuario, no millones).

La query de similitud en Django es notablemente legible:

```python
# similarity_views.py
similar = qs.annotate(
    distance=CosineDistance('embedding', highlight.embedding)
).filter(
    distance__lt=0.45      # umbral: ~0.55 de similitud coseno
).order_by('distance')[:limit]
```

Que se traduce internamente al operador `<=>` de pgvector:

```sql
SELECT *, (embedding <=> query_embedding) AS distance
FROM books_highlight
WHERE (embedding <=> query_embedding) < 0.45
ORDER BY distance
LIMIT 10;
```

El umbral de `0.45` es el resultado de calibrar cuándo la similitud semántica empieza a ser significativa para este tipo de texto. Por debajo de ese valor, los resultados tienden a ser variaciones sobre el mismo tema. Por encima, empiezan a aparecer coincidencias superficiales.

## El pipeline completo: asincronía y centroides

Los embeddings no se generan en el momento de la importación. Hacerlo de forma sincrónica bloquearía la request ~50ms por highlight, y una importación típica puede traer cientos de ellos. En cambio, la importación guarda los highlights en la base de datos y encola una tarea de Celery:

```python
# highlight_views.py — después de cerrar la transacción de importación
pending_ids = list(
    Highlight.objects.filter(
        user=request.user.profile,
        embedding__isnull=True
    ).values_list('id', flat=True)
)
if pending_ids:
    batch_generate_embeddings.delay(pending_ids)
```

La tarea procesa los highlights en sub-lotes de 16 para no bloquear la base de datos con escrituras masivas, y es idempotente: solo procesa highlights con `embedding__isnull=True`, por lo que reencolarla por error o reintentos no produce duplicados.

Además de los embeddings individuales, el sistema mantiene un *centroide* por usuario: el promedio normalizado de todos sus vectores de highlights. Este centroide representa el "centro de gravedad semántico" de sus lecturas y es lo que se usa para encontrar lectores afines — no comparando highlight por highlight entre usuarios (costoso), sino comparando un único vector por usuario:

```python
# affinity/tasks.py
matrix   = np.array(embeddings, dtype=np.float32)
centroid = np.mean(matrix, axis=0)
norm     = np.linalg.norm(centroid)
if norm > 0:
    centroid = centroid / norm
```

## Los límites honestos de este enfoque

La implementación descrita es suficiente para un problema bien acotado: encontrar similitud semántica entre fragmentos de texto cortos (highlights de libros), de un dominio razonablemente homogéneo (no-ficción, literatura, ensayo), con usuarios que leen en un conjunto limitado de idiomas.

Hay casos donde genuinamente no alcanzaría.

**Comprensión de contexto multi-turno.** Si el problema fuera responder preguntas sobre el contenido de los highlights — "¿qué dice mi biblioteca sobre el estoicismo?" —, la distancia coseno sobre embeddings estáticos no es suficiente. El embedding codifica el significado del texto en el momento del encoding, pero no razona sobre él. Ahí sí tiene sentido un LLM con RAG.

**Relaciones semánticas sutiles o negaciones.** Los modelos de embeddings de esta familia tienden a codificar mal las negaciones: "la confianza es esencial para el liderazgo" y "la confianza no es suficiente para el liderazgo" pueden producir vectores más cercanos de lo que debieran. Para aplicaciones donde esa distinción importa, el modelo no es adecuado.

**Textos muy cortos o muy largos.** El modelo tiene un límite de tokens de entrada. Los highlights muy largos se truncan. Los muy cortos (una sola oración, pocas palabras) producen vectores menos estables porque hay menos señal semántica que procesar.

**Multimodalidad o código.** Si los textos a comparar mezclan código, ecuaciones o imágenes, este modelo no tiene las representaciones adecuadas.

**Crecimiento de escala.** pgvector con HNSW funciona bien hasta el orden de decenas de millones de vectores en una instancia correctamente configurada. Más allá de eso, la presión sobre PostgreSQL como datastore único probablemente justifique migrar la capa vectorial a un servicio dedicado como Qdrant.
