# Orden Recomendado para Implementar el Codigo

Este documento define el orden de trabajo para construir una primera version funcional del proyecto con las modalidades `texto + imagen`.

La modalidad de audio queda fuera del alcance inicial. Se evaluara como ampliacion posterior, una vez que la version texto + imagen funcione, pueda demostrarse y tenga comparativas reproducibles.

## 1. Principios de implementacion

- `archive/` es una entrada de solo lectura.
- La unidad presentada al usuario es el producto identificado por `product_id`.
- Los chunks, descriptores, codebooks e indices son estructuras internas.
- Las aplicaciones deben depender de interfaces comunes, no de un motor concreto.
- El motor propio de la Fase 2 y PostgreSQL en la Fase 3 deben procesar los mismos datos y consultas.
- Cada etapa costosa debe guardar artefactos y permitir reanudar la ejecucion.
- Primero se implementara una version funcional sobre `1K` productos; despues se escalara a `10K` y a la coleccion completa.

## 2. Estructura inicial que debe crearse

```text
configs/
  base.yaml
  text.yaml
  vision.yaml
  postgres.yaml
src/
  common/
    __init__.py
    config.py
    models.py
    interfaces.py
    logging.py
  ingestion/
    __init__.py
    loader.py
    cleaner.py
    partitions.py
  text/
    __init__.py
    splitter.py
    extractor.py
    codebook.py
    histogram.py
  vision/
    __init__.py
    preprocessing.py
    sift_extractor.py
    codebook.py
    histogram.py
  phase2/
    __init__.py
    spimi.py
    inverted_index.py
    text_retriever.py
    visual_retriever.py
  phase3/
    __init__.py
    postgres_client.py
    text_retriever.py
    vector_retriever.py
  retrieval/
    __init__.py
    ranking.py
    fusion.py
  applications/
    __init__.py
    visual_search.py
    multimodal_recommender.py
  evaluation/
    __init__.py
    metrics.py
    benchmark.py
    resource_monitor.py
scripts/
sql/
tests/
artifacts/
reports/
docker-compose.yml
requirements.txt
```

`artifacts/` y `reports/` contendran archivos generados y no deben mezclarse con la dataset original.

## 3. Paso 1: Crear configuracion y modelos comunes

Implementar primero:

- `configs/base.yaml`: rutas, semilla, escala activa y directorios de artefactos
- `configs/text.yaml`: idioma, stopwords, stemming, top-k y parametros TF-IDF
- `configs/vision.yaml`: resolucion maxima, keypoints, muestra SIFT y valor de `k`
- `configs/postgres.yaml`: conexion, esquema e indices habilitados
- `src/common/config.py`: carga y validacion de configuracion
- `src/common/models.py`: modelos compartidos
- `src/common/interfaces.py`: contratos para extractores, indices y retrievers
- `src/common/logging.py`: logging consistente

Modelos minimos:

- `Product`
- `Chunk`
- `SearchResult`
- `Query`
- `CodebookMetadata`
- `ExperimentRun`

Interfaces minimas:

- `Splitter.split(item)`
- `FeatureExtractor.extract(chunk)`
- `Codebook.fit(features)` y `Codebook.transform(features)`
- `Indexer.build(items)` y `Indexer.load(path)`
- `Retriever.search(query, top_k)`

Criterio de cierre:

- la configuracion se carga desde archivos
- los modelos se pueden serializar
- las aplicaciones futuras pueden recibir cualquier implementacion de `Retriever`
- existen pruebas unitarias basicas

## 4. Paso 2: Implementar ingesta y particiones

Archivos principales:

- `src/ingestion/loader.py`
- `src/ingestion/cleaner.py`
- `src/ingestion/partitions.py`
- `scripts/build_catalog.py`

Trabajo:

1. Leer `styles.csv`, `images.csv` y JSON.
2. Construir un registro canonico por `product_id`.
3. Limpiar HTML y normalizar valores faltantes.
4. Registrar rutas de imagen y banderas de calidad.
5. Mantener productos sin imagen para texto y excluirlos de imagen/multimodal.
6. Mantener grupos de imagenes duplicadas dentro de una misma particion.
7. Crear manifiestos reproducibles para `1K`, `10K` y coleccion completa.

Salida esperada:

```text
artifacts/catalog/products.jsonl
artifacts/partitions/1k.json
artifacts/partitions/10k.json
artifacts/partitions/full.json
```

Criterio de cierre:

- dos ejecuciones con la misma semilla producen las mismas particiones
- no se modifica `archive/`
- todos los productos quedan asociados con sus modalidades disponibles

## 5. Paso 3: Implementar primero el pipeline textual propio

Se recomienda comenzar por texto porque permite validar rapidamente interfaces, chunks, codebooks, indices y rankings.

Archivos principales:

- `src/text/splitter.py`
- `src/text/extractor.py`
- `src/text/codebook.py`
- `src/text/histogram.py`
- `src/phase2/spimi.py`
- `src/phase2/text_retriever.py`
- `scripts/build_text_index.py`

Orden interno:

1. Construir texto canonico por producto.
2. Crear chunks textuales.
3. Tokenizar, normalizar, remover stopwords y aplicar stemming o lematizacion.
4. Calcular TF-IDF.
5. Seleccionar top-k terminos para el codebook.
6. Generar histogramas o pesos por chunk/producto.
7. Implementar SPIMI y persistir postings.
8. Implementar busqueda textual y ranking top-k.

Salida esperada:

```text
artifacts/text/codebook.json
artifacts/text/postings/
artifacts/text/document_norms.json
```

Criterio de cierre:

- consultas como `black sports shoes` devuelven productos razonables
- el indice puede reconstruirse y cargarse
- existen pruebas de tokenizacion, SPIMI y ranking

## 6. Paso 4: Implementar el pipeline visual propio

Archivos principales:

- `src/vision/preprocessing.py`
- `src/vision/sift_extractor.py`
- `src/vision/codebook.py`
- `src/vision/histogram.py`
- `src/phase2/inverted_index.py`
- `src/phase2/visual_retriever.py`
- `scripts/build_visual_index.py`

Orden interno:

1. Normalizar dimensiones sin deformar la imagen.
2. Extraer SIFT con limite de keypoints.
3. Guardar descriptores por producto para evitar reprocesamiento.
4. Muestrear descriptores solo desde entrenamiento.
5. Entrenar K-Means para generar visual words.
6. Cuantizar SIFT y construir histogramas visuales.
7. Construir indice invertido visual.
8. Implementar consulta por imagen y ranking top-k.

Salida esperada:

```text
artifacts/vision/descriptors/
artifacts/vision/codebook.pkl
artifacts/vision/histograms/
artifacts/vision/inverted_index/
```

Criterio de cierre:

- una imagen consulta devuelve productos visualmente relacionados
- el producto consulta se excluye del ranking
- el procesamiento se puede reanudar usando checkpoints

## 7. Paso 5: Implementar backend y aplicaciones compartidas

Archivos principales:

- `src/retrieval/ranking.py`
- `src/retrieval/fusion.py`
- `src/applications/visual_search.py`
- `src/applications/multimodal_recommender.py`

Trabajo:

1. Normalizar scores entre modalidades.
2. Implementar fusion ponderada configurable.
3. Construir busqueda visual e-commerce.
4. Construir recomendacion multimodal.
5. Permitir seleccionar retrievers mediante configuracion.

La dependencia debe seguir esta forma:

```text
Aplicacion -> interfaz Retriever -> motor propio o PostgreSQL
```

Criterio de cierre:

- ambas aplicaciones funcionan con el motor propio
- cambiar el retriever no requiere modificar la logica de la aplicacion

## 8. Paso 6: Preparar persistencia PostgreSQL

Archivos principales:

- `docker-compose.yml`
- `sql/001_extensions.sql`
- `sql/002_schema.sql`
- `src/phase3/postgres_client.py`
- `scripts/load_postgres.py`

Trabajo:

1. Levantar PostgreSQL con pgvector.
2. Crear tablas para productos, chunks, codebooks, histogramas y ejecuciones.
3. Cargar los mismos productos e histogramas usados por el motor propio.
4. Verificar integridad y dimensiones de vectores.

Criterio de cierre:

- PostgreSQL puede reconstruirse desde scripts
- la cantidad de productos y vectores coincide con los artefactos de Fase 2

## 9. Paso 7: Implementar comparativa textual PostgreSQL

Archivos principales:

- `sql/003_text_indexes.sql`
- `src/phase3/text_retriever.py`

Trabajo:

1. Crear `tsvector` con el mismo texto canonico.
2. Crear indices GIN y GiST por separado.
3. Implementar retrievers compatibles con la interfaz comun.
4. Ejecutar las mismas consultas del motor SPIMI.

Criterio de cierre:

- las aplicaciones pueden usar SPIMI, GIN o GiST mediante configuracion
- se conservan resultados y tiempos por metodo

## 10. Paso 8: Implementar comparativa visual pgvector

Archivos principales:

- `sql/004_vector_indexes.sql`
- `src/phase3/vector_retriever.py`

Trabajo:

1. Almacenar los histogramas visuales de Fase 2 como vectores.
2. Implementar busqueda exacta.
3. Crear indices HNSW e IVFFlat.
4. Exponer cada metodo mediante la interfaz `Retriever`.
5. Comparar resultados contra el indice invertido visual.

Criterio de cierre:

- las aplicaciones pueden usar indice visual propio, pgvector exacto, HNSW o IVFFlat
- se puede medir recall aproximado respecto a busqueda exacta

## 11. Paso 9: Implementar evaluacion reproducible

Archivos principales:

- `src/evaluation/metrics.py`
- `src/evaluation/benchmark.py`
- `src/evaluation/resource_monitor.py`
- `scripts/run_benchmarks.py`

Trabajo:

1. Congelar consultas y criterios de relevancia.
2. Medir latencia, throughput, precision, memoria, disco e `I/O`.
3. Ejecutar escalas de productos `1K`, `10K` y `44,441`.
4. Ejecutar estres estructural de `1K`, `10K` y `100K chunks`.
5. Guardar resultados crudos antes de generar graficos.

Criterio de cierre:

- una configuracion produce resultados repetibles
- todos los motores reciben las mismas consultas y datos

## 12. Paso 10: Escalar y documentar

No se debe comenzar con toda la dataset.

Orden de escalamiento:

1. Completar flujo funcional sobre `1K` productos.
2. Corregir errores y validar calidad.
3. Ejecutar sobre `10K`.
4. Optimizar memoria, checkpoints y persistencia.
5. Ejecutar sobre la coleccion completa.
6. Ejecutar carga de `100K chunks`.
7. Generar tablas, graficos y conclusiones.

## 13. Extension futura: audio

Audio se implementara solo despues de completar la version funcional texto + imagen y si el tiempo disponible lo permite.

La extension requeriria:

- seleccionar y documentar un dataset de audio
- crear `src/audio/`
- implementar ventanas deslizantes
- extraer MFCC
- construir codebook acustico con K-Means o K-Medoids
- generar histogramas e indice invertido acustico
- almacenar vectores de audio en pgvector
- ampliar aplicaciones, evaluacion y comparativas

El codigo comun debe evitar supuestos exclusivos de texto e imagen para facilitar esta ampliacion, pero no se implementara funcionalidad de audio durante la primera version.

## 14. Proximo trabajo inmediato

El siguiente bloque de trabajo es:

1. Crear la estructura inicial de carpetas.
2. Crear los archivos de configuracion.
3. Implementar modelos e interfaces comunes.
4. Agregar pruebas unitarias basicas.

No se debe iniciar ingesta, SPIMI o SIFT antes de estabilizar estos contratos comunes.
