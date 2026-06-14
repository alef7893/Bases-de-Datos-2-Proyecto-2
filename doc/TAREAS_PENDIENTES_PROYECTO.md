# Tareas pendientes del Proyecto 2

Esta lista contrasta los requisitos de `Proyecto 2.pdf` con la implementacion
actual. Texto e imagen cuentan con pipelines funcionales, aplicaciones,
comparativas PostgreSQL y evaluacion para la escala `1k`. Los principales
pendientes son audio, experimentos aislados de texto, escalas mayores,
persistencia de resultados y cierre del informe.

## Resumen de tareas pendientes

El trabajo pendiente se concentra en cinco objetivos:

1. Incorporar una nueva dataset musical: `Audio features and lyrics of Spotify
   songs` o `FMA: A Dataset For Music Analysis`.
2. Implementar el pipeline completo de audio: ventanas deslizantes, MFCC,
   codebook acustico, histogramas, indice custom y pgvector.
3. Integrar la **App 02: Busqueda Musical Inteligente**, que permitira buscar
   canciones mediante audio, letra o la fusion de ambas modalidades.
4. Completar la Fase 4: cargas variadas, metricas, comparacion de motores,
   graficos, trade-offs y respuestas a las preguntas de conclusiones.
5. Completar persistencia experimental, resultados, graficos, conclusiones,
   documentacion y preparacion de la demostracion.

## Prioridad 1: completar la modalidad de audio

La modalidad `AUDIO` existe en `backend/src/common/models.py`, pero no tiene
pipeline, recuperadores, persistencia, aplicacion ni experimentos.

- [ ] **Incorporar y documentar una nueva dataset publica de audio y texto.**
  - Ubicacion: `README.md`, secciones de dataset, distribucion y limitaciones.
  - Opciones:
    - `Audio features and lyrics of Spotify songs` de Kaggle.
    - `FMA: A Dataset For Music Analysis` de GitHub.
  - Trabajo requerido: descargar o enlazar la dataset, definir su ubicacion
    local, adaptar el cargador, relacionar audio con letras y crear particiones
    reproducibles.
  - Criterio de finalizacion: documentar licencia, cantidad de audios, duracion,
    formatos, texto disponible, clases, distribucion, espacio requerido y
    procedimiento de preparacion.

- [ ] **Agregar configuracion reproducible para audio.**
  - Ubicacion: `backend/configs/audio.yaml` y `backend/src/common/config.py`.
  - Parametros: sample rate, duracion de ventana, overlap, numero de MFCC,
    tamano del codebook, muestra de entrenamiento y semilla.
  - Criterio de finalizacion: la configuracion se valida y carga junto con los
    YAML existentes.

- [ ] **Extender los modelos de contenido para registrar audios.**
  - Ubicacion: `backend/src/common/models.py`.
  - Cambios: agregar `audio_path`, `has_audio` y metadatos relevantes al
    producto o crear una entidad de dominio apropiada para canciones.
  - Criterio de finalizacion: modelos y pruebas aceptan consultas de audio y
    multimodales texto-audio.

- [ ] **Implementar el split de audio mediante ventanas deslizantes.**
  - Ubicacion propuesta: `backend/src/pipeline/audio/splitter.py`.
  - Requisito del PDF: ventanas de aproximadamente `100-200 ms`.
  - Criterio de finalizacion: cada audio produce chunks reproducibles con
    posicion temporal, inicio, fin y `product_id`.

- [ ] **Implementar preprocesamiento y extraccion MFCC.**
  - Ubicacion propuesta:
    - `backend/src/pipeline/audio/preprocessing.py`
    - `backend/src/pipeline/audio/mfcc_extractor.py`
  - Criterio de finalizacion: cada ventana genera un descriptor MFCC valido,
    incluso ante audios cortos o corruptos.

- [ ] **Implementar codebook acustico con K-Means o K-Medoids.**
  - Ubicacion propuesta:
    - `backend/src/pipeline/audio/codebook.py`
    - `backend/src/pipeline/audio/encoder.py`
    - `backend/src/pipeline/audio/histogram.py`
  - Criterio de finalizacion: entrenar k centroides acusticos y convertir cada
    audio en un histograma normalizado de acoustic words.

- [ ] **Implementar indice invertido y recuperador custom de audio.**
  - Ubicacion propuesta:
    - `backend/src/retrieval/custom/audio/inverted_index.py`
    - `backend/src/retrieval/custom/audio/retriever.py`
  - Criterio de finalizacion: consultar un audio y devolver un ranking por
    similitud acustica excluyendo el elemento consultado.

- [ ] **Agregar persistencia PostgreSQL y pgvector para audio.**
  - Ubicacion:
    - `backend/sql/002_schema.sql`
    - nuevo script `backend/sql/005_audio_indexes.sql`
    - `backend/src/persistence/artifact_loader.py`
    - `backend/src/retrieval/postgres/audio/`
  - Criterio de finalizacion: almacenar chunks, codebook, histogramas,
    metadatos y vectores de audio; crear HNSW o IVFFlat y ejecutar consultas.

- [ ] **Agregar scripts de construccion y preparacion de audio.**
  - Ubicacion propuesta:
    - `backend/scripts/pipeline/build_audio_index.py`
    - `backend/scripts/persistence/prepare_audio_postgres.py`
  - Criterio de finalizacion: construir y persistir una escala mediante
    comandos reproducibles.

- [ ] **Integrar la App 02: Busqueda Musical Inteligente.**
  - Ubicacion propuesta:
    - `backend/src/applications/app02_music_search.py`
    - `frontend/applications/app02_music_search.py`
    - `frontend/applications/registry.py`
  - Modalidad primaria: audio + texto.
  - Consultas soportadas:
    - busqueda por letra mediante texto
    - busqueda por similitud acustica mediante audio
    - busqueda multimodal combinando letra, caracteristicas acusticas y genero
  - Criterio de finalizacion: demostracion visual con motores custom y
    PostgreSQL, selector de modalidad y ranking fusionado.

- [ ] **Agregar pruebas automatizadas de audio.**
  - Ubicacion propuesta:
    - `backend/tests/pipeline/test_audio_pipeline.py`
    - `backend/tests/retrieval/test_audio_retrieval.py`
    - `backend/tests/applications/test_app02.py`
  - Criterio de finalizacion: cubrir split, MFCC, codebook, histograma,
    recuperacion y casos de audio ausente o invalido.

## Prioridad 2: completar la Fase 4 y responder las conclusiones

- [ ] **Definir y ejecutar el marco de cargas variadas.**
  - Requisito: carga pequena de `1K` chunks, mediana de `10K` chunks y grande
    de `100K` chunks.
  - Ubicacion:
    - `backend/src/pipeline/catalog/partitions.py`
    - `backend/src/experiments/common/`
    - `backend/scripts/experiments/`
  - Trabajo requerido: registrar la cantidad real de productos y chunks
    utilizados por modalidad en cada experimento.
  - Limitacion conocida: la dataset de moda contiene aproximadamente 44 mil
    productos; debe justificarse el uso de `full` cuando no sea posible alcanzar
    `100K` elementos unicos.
  - Criterio de finalizacion: reportes reproducibles para las tres cargas o una
    justificacion documentada de cualquier carga no alcanzable.

- [ ] **Construir artefactos completos para `10k`.**
  - Comandos existentes:
    - `python -m scripts.pipeline.build_text_index --scale 10k`
    - `python -m scripts.pipeline.build_visual_index --scale 10k`
  - Criterio de finalizacion: artefactos custom y datos PostgreSQL disponibles.

- [ ] **Construir artefactos completos para `full`.**
  - Comandos existentes:
    - `python -m scripts.pipeline.build_text_index --scale full`
    - `python -m scripts.pipeline.build_visual_index --scale full`
  - Limitacion: la dataset tiene aproximadamente 44 mil productos, por lo que
    `full` reemplaza la carga solicitada de `100k` sin duplicar datos.

- [ ] **Ejecutar las evaluaciones de app 1 y app 4 en todas las escalas
  disponibles.**
  - Ubicacion de resultados:
    - `reports/phase4/app01/` o ajustar la salida visual actual a esta carpeta
    - `reports/phase4/app04/`
  - Criterio de finalizacion: reportes y graficos para `1k`, `10k` y `full`,
    con las mismas consultas, repeticiones y configuracion.

- [ ] **Medir todas las metricas requeridas de forma consistente.**
  - Metricas obligatorias: latencia, throughput, precision, memoria y accesos
    I/O.
  - Ubicacion:
    - `backend/src/experiments/common/metrics.py`
    - `backend/src/experiments/common/instrumentation.py`
    - evaluadores de `backend/src/experiments/app01/` y
      `backend/src/experiments/app04/`
  - Trabajo requerido: utilizar la misma definicion, unidad y metodologia para
    todos los motores y escalas.
  - Criterio de finalizacion: cada reporte contiene las cinco metricas y explica
    como fueron calculadas.

- [ ] **Comparar indice propio, GIN y pgvector mediante una metodologia comun.**
  - Motores actuales:
    - indice invertido propio de texto e imagen
    - PostgreSQL GIN para texto
    - PostgreSQL pgvector HNSW y busqueda exacta para imagen
  - Criterio de finalizacion: tablas comparables que identifiquen claramente el
    motor, escala, parametros y modalidad evaluada.

- [ ] **Generar graficos comparativos completos.**
  - Ubicacion:
    - `backend/src/experiments/common/plots.py`
    - `reports/phase4/`
  - Graficos requeridos: latencia, throughput, precision, memoria, espacio en
    disco y accesos I/O por motor y escala.
  - Criterio de finalizacion: los graficos se generan automaticamente y se
    enlazan desde el informe.

- [ ] **Realizar pruebas de sensibilidad del codebook.**
  - Requisito relacionado: analizar impacto de dimensionalidad y calidad
    dependiente de `k`.
  - Ubicacion propuesta:
    - `backend/scripts/experiments/run_codebook_sensitivity.py`
    - `reports/phase4/codebook_sensitivity/`
  - Criterio de finalizacion: comparar varios valores de `k` en latencia,
    memoria, precision y espacio.

- [ ] **Responder: que tecnica gano en cada metrica.**
  - Ubicacion: `README.md`, secciones 5 y 6.
  - Trabajo requerido: identificar ganadores de latencia, throughput,
    precision, memoria e I/O para cada aplicacion y escala.
  - Criterio de finalizacion: conclusiones respaldadas por tablas y graficos.

- [ ] **Responder: se recupero la misma informacion.**
  - Ubicacion: `README.md`, seccion 6.
  - Trabajo requerido: analizar `Precision@K`, `Recall@K` y solapamiento entre
    rankings; explicar falsos positivos y falsos negativos.
  - Criterio de finalizacion: respuesta cuantitativa y cualitativa para app 1 y
    app 4.

- [ ] **Documentar limitaciones experimentales.**
  - Ubicacion: `README.md`, seccion 6.
  - Incluir: ausencia de juicios externos de relevancia, uso de `articleType`
    como proxy, limite de aproximadamente 44 mil productos, artefactos faltantes
    y diferencias entre cargas por productos y chunks.

- [ ] **Redactar recomendaciones finales.**
  - Ubicacion: `README.md`, seccion 6.
  - Trabajo requerido: explicar cuando conviene usar el indice propio, GIN o
    pgvector considerando calidad, velocidad, memoria, persistencia y
    complejidad operacional.

## Prioridad 3: completar persistencia y reproducibilidad

- [ ] **Persistir resultados experimentales completos en PostgreSQL.**
  - Falta actual: `experiment_runs` registra cargas, pero los evaluadores
    escriben principalmente JSON en `reports/`.
  - Ubicacion propuesta:
    - nuevo `backend/src/persistence/experiment_repository.py`
    - extender `backend/sql/002_schema.sql` o agregar
      `backend/sql/006_experiment_results.sql`
  - Datos: configuracion, metricas agregadas, resultados por consulta, rutas de
    graficos, estado y tiempos.
  - Criterio de finalizacion: poder consultar y comparar ejecuciones desde SQL.

- [ ] **Registrar versiones y procedencia de artefactos.**
  - Ubicacion: `backend/src/persistence/artifact_loader.py` y tablas
    `codebooks`/`experiment_runs`.
  - Criterio de finalizacion: cada reporte identifica dataset, split, semilla,
    configuracion, commit y artefactos usados.

- [ ] **Agregar validacion automatica del esquema y extensiones.**
  - Ubicacion propuesta: `backend/tests/persistence/test_postgres_integration.py`.
  - Criterio de finalizacion: verificar tablas, pgvector, GIN, HNSW y futuras
    estructuras de audio sobre una instancia de prueba.

## Prioridad 4: completar informe y entregables

- [ ] **Completar la seccion de resultados experimentales del README.**
  - Ubicacion: `README.md`, seccion 5.
  - Falta actual: la seccion todavia no resume las tablas y graficos generados.
  - Criterio de finalizacion: incluir resultados de todas las escalas y
    modalidades evaluadas.

- [ ] **Completar trade-offs y conclusiones finales.**
  - Ubicacion: `README.md`, seccion 6.
  - Responder explicitamente:
    - que tecnica gano en cada metrica
    - si se recupero la misma informacion
    - limitaciones
    - recomendaciones

- [ ] **Agregar graficos ilustrativos al informe.**
  - Ubicacion: enlazar desde `README.md` los SVG generados en `reports/`.
  - Criterio de finalizacion: graficos legibles de latencia, throughput,
    precision, memoria, almacenamiento e I/O.

- [ ] **Documentar ejemplos de uso de al menos dos aplicaciones.**
  - Ubicacion: `README.md`.
  - Estado actual: existen app 1 y app 4; falta incorporar capturas o ejemplos
    reproducibles de entradas y resultados.

- [ ] **Preparar demostracion viva.**
  - Aplicaciones actuales: app 1 y app 4.
  - Pendiente recomendado: incluir app 2 si se completa audio.
  - Criterio de finalizacion: guion de ejecucion, PostgreSQL preparado,
    consultas de ejemplo y plan de contingencia.

- [ ] **Crear y mantener GitHub Projects, issues e hitos.**
  - Ubicacion: GitHub, fuera del repositorio local.
  - Criterio de finalizacion: tareas asignadas, issues cerrados con evidencia,
    hitos y contribuciones del equipo documentadas.

- [ ] **Revisar documentacion, ortografia y comentarios del codigo.**
  - Ubicacion: todo el repositorio, principalmente `README.md`.
  - Criterio de finalizacion: terminologia consistente, comandos vigentes y
    explicaciones tecnicas concisas.

## Orden recomendado

1. Incorporar la nueva dataset musical y definir configuracion de audio.
2. Implementar pipeline, indice custom y pruebas de audio.
3. Persistir audio y agregar recuperacion pgvector.
4. Implementar la App 02 Busqueda Musical Inteligente y su frontend.
5. Construir artefactos `10k` y `full`.
6. Ejecutar la Fase 4 completa con todas las metricas y cargas disponibles.
7. Generar tablas, graficos y comparaciones entre motores.
8. Responder las preguntas de conclusiones y redactar recomendaciones.
9. Persistir resultados experimentales.
10. Completar el informe, cerrar issues, hitos y preparar la demostracion oral.
