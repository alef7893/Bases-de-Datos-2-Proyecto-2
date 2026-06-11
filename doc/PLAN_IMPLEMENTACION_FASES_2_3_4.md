# Plan de Implementacion de las Fases 2, 3 y 4

Este documento contiene el plan operativo para implementar, comparar y evaluar el sistema definido en la Fase 1. No forma parte del informe de diseno inicial.

## 1. Alcance y decisiones previas

El plan principal implementara una version funcional con las modalidades `texto + imagen` y las aplicaciones de busqueda visual y recomendacion multimodal definidas en la Fase 1.

La modalidad de audio se pospone como ampliacion opcional. Solo se implementara despues de completar, demostrar y evaluar la version texto + imagen, si el tiempo disponible lo permite. La extension requerira un segundo dataset, MFCC, un codebook acustico y experimentos adicionales.

Decisiones tecnicas iniciales:

- lenguaje principal: Python
- persistencia: PostgreSQL con extension pgvector mediante Docker Compose
- representacion textual propia: tokens normalizados, codebook top-k, histogramas e indice SPIMI
- representacion visual propia: SIFT, K-Means e histogramas de visual words
- unidad de respuesta: producto
- unidad interna de indexacion: chunk
- configuracion, semillas y rutas fuera del codigo fuente
- ejecuciones largas con checkpoints para no repetir extraccion o clustering

## 2. Estructura propuesta del repositorio

```text
src/
  ingestion/
  text/
  vision/
  indexing/
  retrieval/
  fusion/
  persistence/
  applications/
  evaluation/
scripts/
sql/
configs/
tests/
artifacts/
reports/
docker-compose.yml
```

`archive/` se tratara como entrada de solo lectura. Los artefactos derivados, como particiones, descriptores, codebooks, histogramas y resultados, se almacenaran fuera de la dataset original.

## 3. Modelo minimo de persistencia

| Entidad | Contenido |
| --- | --- |
| `products` | `product_id`, texto limpio, categorias, rutas y banderas de calidad |
| `chunks` | `chunk_id`, `product_id`, modalidad, posicion y metadatos |
| `codebooks` | modalidad, version, valor de `k`, parametros y ruta o contenido |
| `histograms` | `chunk_id` o `product_id`, modalidad, vector y version del codebook |
| `postings` | modalidad, `codeword_id`, item asociado, frecuencia o peso |
| `experiment_runs` | configuracion, semilla, hardware, tiempos y estado |
| `query_results` | consulta, metodo, ranking, scores y metricas |

Los vectores de pgvector deben usar la misma representacion que el sistema propio cuando se compare el mecanismo de indexacion. Si se comparan representaciones distintas, se reportara como un experimento separado.

## 4. Fase 2: Implementacion del sistema multimodal

### 4.1 Hito: Base reproducible e ingesta

Trabajo:

1. Crear estructura del proyecto, configuracion, logging y pruebas.
2. Preparar Docker Compose con PostgreSQL y pgvector.
3. Implementar carga de CSV y JSON, limpieza de HTML y normalizacion.
4. Enlazar productos, imagenes y metadatos mediante `product_id`.
5. Generar particiones reproducibles, manteniendo duplicados visuales en una sola particion.
6. Persistir productos, banderas de calidad y manifiestos de particion.

Entregable: catalogo canonico consultable y particiones de `1K`, `10K` y coleccion completa.

Criterio de cierre: todos los productos validos se cargan sin modificar `archive/`, los cinco productos sin imagen quedan identificados y una segunda ejecucion produce las mismas particiones.

### 4.2 Hito: Pipeline textual

Trabajo:

1. Construir chunks desde nombre, atributos y descripcion limpia.
2. Implementar tokenizacion, minusculas, stopwords y stemming o lematizacion.
3. Calcular TF-IDF y seleccionar el codebook top-k usando solo entrenamiento.
4. Implementar SPIMI y persistir postings.
5. Generar histogramas textuales y ranking por similitud.
6. Crear pruebas con consultas por palabras clave.

Entregable: buscador textual propio con resultados por producto.

Criterio de cierre: una consulta reproducible devuelve top-k, excluye el producto consulta cuando corresponda y permite reconstruir el indice desde cero.

### 4.3 Hito: Pipeline visual

Trabajo:

1. Normalizar dimensiones y limitar keypoints por imagen.
2. Extraer SIFT con checkpoints y registrar imagenes sin descriptores.
3. Muestrear descriptores de entrenamiento.
4. Entrenar K-Means para construir el codebook visual.
5. Cuantizar descriptores y generar histogramas de visual words.
6. Construir el indice invertido visual y ranking por similitud.

Entregable: buscador visual propio con top-k productos similares.

Criterio de cierre: el pipeline procesa las particiones definidas, reutiliza artefactos existentes y devuelve resultados sin incluir el producto consulta.

### 4.4 Hito: Backend extensible y aplicaciones

Trabajo:

1. Definir una interfaz comun de consulta y respuesta.
2. Implementar busqueda visual e-commerce.
3. Implementar recomendacion multimodal como recuperacion de productos relacionados.
4. Normalizar scores textual y visual.
5. Implementar fusion ponderada y configuracion de pesos.
6. Exponer endpoints o comandos reproducibles para demostracion.

Entregable: dos aplicaciones operativas sobre el mismo backend.

Criterio de cierre: ambas aplicaciones reutilizan ingesta, indices y ranking; cambiar pesos o modalidad no requiere modificar el nucleo.

## 5. Fase 3: Comparativas en PostgreSQL

### 5.1 Hito: Baseline textual GIN/GiST

Trabajo:

1. Construir `tsvector` con el mismo texto canonico.
2. Crear indices GIN y GiST por separado.
3. Ejecutar el mismo conjunto de consultas textuales.
4. Registrar latencia, throughput, tamano de indice, memoria e `I/O`.
5. Comparar resultados contra SPIMI bajo la misma definicion de relevancia.

Entregable: comparativa reproducible SPIMI vs. GIN vs. GiST.

### 5.2 Hito: Baseline visual pgvector

Trabajo:

1. Almacenar histogramas visuales como vectores.
2. Ejecutar busqueda vectorial exacta como referencia.
3. Crear y ajustar indices HNSW e IVFFlat.
4. Medir `Recall@K` aproximado respecto a la busqueda exacta.
5. Comparar latencia, precision, memoria, disco e `I/O` contra el indice invertido visual.

Entregable: comparativa reproducible indice visual propio vs. pgvector exacto, HNSW e IVFFlat.

### 5.3 Hito: Comparacion justa

Reglas:

- usar los mismos productos, consultas, histogramas y particiones
- separar tiempo de preparacion, construccion de indice y consulta
- registrar parametros de GIN, GiST, HNSW, IVFFlat y codebooks
- ejecutar calentamiento y mediciones repetidas
- no mezclar en una misma conclusion cambios de representacion con cambios de indice

## 6. Fase 4: Evaluacion experimental y analisis

### 6.1 Cargas

- calidad y recuperacion extremo a extremo: `1K`, `10K` y `44,441` productos multimodales
- estres estructural: `1K`, `10K` y `100K` chunks

### 6.2 Protocolo

1. Congelar consultas, particiones, semilla y ground truth aproximado.
2. Ejecutar cada combinacion de modalidad, escala y metodo.
3. Repetir consultas con condiciones controladas de cache y concurrencia.
4. Capturar latencia, throughput, precision, memoria, disco e `I/O`.
5. Guardar resultados crudos antes de generar tablas y graficos.
6. Analizar resultados globales y por categoria.
7. Documentar fallos, casos limite y amenazas a la validez.

### 6.3 Matriz minima de experimentos

| Modalidad | Sistema propio | Baselines |
| --- | --- | --- |
| Texto | SPIMI e indice invertido textual | PostgreSQL GIN y GiST |
| Imagen | Indice invertido de visual words | pgvector exacto, HNSW e IVFFlat |
| Multimodal | Fusion de scores textual y visual | Fusion de resultados obtenidos con baselines |

### 6.4 Productos finales

- tablas y graficos por escala y metodo
- resultados de precision aproximada y evaluacion manual
- analisis de trade-offs entre exactitud, velocidad, memoria y disco
- respuesta sustentada sobre que tecnica gana en cada metrica
- limitaciones, amenazas a la validez y recomendaciones

## 7. Orden de ejecucion y dependencias

| Orden | Hito | Depende de |
| ---: | --- | --- |
| 1 | Base e ingesta | Fase 1 |
| 2 | Pipeline textual | Base e ingesta |
| 3 | Pipeline visual | Base e ingesta |
| 4 | Backend y aplicaciones | Pipelines textual y visual |
| 5 | GIN/GiST | Base e ingesta y pipeline textual |
| 6 | pgvector | Base e ingesta y pipeline visual |
| 7 | Comparacion justa | Baselines textuales y visuales |
| 8 | Fase 4 Evaluacion | Fases 2 y 3 completas |

El pipeline textual puede avanzar en paralelo con el visual. Las comparativas de PostgreSQL pueden comenzar cuando la representacion correspondiente quede estable, sin esperar a terminar las dos aplicaciones.

## 8. Riesgos principales y mitigaciones

| Riesgo | Mitigacion |
| --- | --- |
| La ampliacion de audio consume tiempo necesario para estabilizar texto e imagen | No iniciar audio hasta completar y evaluar la version funcional texto + imagen |
| Extraccion SIFT y K-Means exceden memoria o tiempo | Limitar resolucion y keypoints, muestrear descriptores y guardar checkpoints |
| Imagenes duplicadas inflan precision | Agrupar por hash y evitar cruces entre particiones |
| Ground truth visual debil | Separar etiquetas aproximadas de evaluacion manual |
| Dataset desbalanceada | Muestreo estratificado y metricas por categoria |
| Carga de 100K no representa productos unicos | Reportarla explicitamente como carga de chunks |
| Comparacion injusta entre metodos | Mantener datos, consultas y representaciones iguales por experimento |

## 9. Definicion de terminado

Las Fases 2, 3 y 4 se consideraran completas cuando:

- los pipelines textual y visual puedan reconstruirse de forma reproducible
- SPIMI y el indice visual propio devuelvan rankings por producto
- las dos aplicaciones funcionen sobre un backend compartido
- PostgreSQL almacene metadatos, codebooks e histogramas
- existan comparativas contra GIN, GiST, pgvector exacto, HNSW e IVFFlat
- las escalas definidas tengan resultados crudos, tablas y graficos
- las conclusiones indiquen que metodo gana por metrica y bajo que limitaciones

## 10. Iteraciones y distribucion sugerida

La duracion exacta debe ajustarse al calendario del curso. El orden recomendado usa iteraciones, no fechas fijas:

| Iteracion | Objetivo principal | Resultado verificable |
| --- | --- | --- |
| 1 | Infraestructura, PostgreSQL, ingesta y particiones | Catalogo canonico y dataset reproducible |
| 2 | Split, extraccion, codebook e indice textual SPIMI | Busqueda textual propia operativa |
| 3 | Normalizacion visual, SIFT, K-Means e indice visual | Busqueda visual propia operativa |
| 4 | Persistencia completa, backend y fusion multimodal | Dos aplicaciones demostrables |
| 5 | GIN, GiST, pgvector exacto, HNSW e IVFFlat | Baselines comparables |
| 6 | Experimentos, graficos, analisis y documentacion | Informe final y demostracion |

Distribucion sugerida para cinco integrantes:

| Rol principal | Responsabilidades |
| --- | --- |
| Integrante 1 | Ingesta, calidad de datos, particiones y reproducibilidad |
| Integrante 2 | Pipeline textual, TF-IDF, codebook textual y SPIMI |
| Integrante 3 | Pipeline visual, SIFT, K-Means e indice visual |
| Integrante 4 | PostgreSQL, pgvector, GIN/GiST y persistencia |
| Integrante 5 | Backend, fusion multimodal, evaluacion y visualizaciones |

Cada modulo debe tener al menos un revisor distinto de su responsable principal. Las tareas compartidas, como pruebas, documentacion y experimentos, deben distribuirse entre todo el equipo y registrarse mediante issues e hitos.
