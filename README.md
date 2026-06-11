# Proyecto 2: Sistema Multimodal de Recuperacion y Busqueda

Este repositorio documenta el diseno inicial de un sistema multimodal de recuperacion y busqueda para el curso de Base de Datos 2. El proyecto sigue la arquitectura propuesta en el enunciado: `split` del contenido en unidades atomicas, extraccion de caracteristicas por modalidad, construccion de un `codebook`, generacion de indices invertidos y comparacion frente a mecanismos nativos de PostgreSQL.

## 1. Descripcion del sistema y arquitectura

### 1.1 Objetivo del sistema

El sistema busca ofrecer una arquitectura unificada para recuperar informacion sobre multiples modalidades bajo un mismo paradigma de indexacion. En el alcance actual del proyecto se dara prioridad a `texto` e `imagen`.

La arquitectura base del sistema sigue estas etapas:

1. `split` del contenido en `chunks` o unidades atomicas
2. extraccion de caracteristicas segun la modalidad
3. construccion de un `codebook`
4. representacion de cada item como histograma de `codewords`
5. construccion de un indice invertido propio
6. almacenamiento y comparacion con PostgreSQL
7. recuperacion por modalidad o fusion multimodal

El backend debe ser generico y extensible. Las aplicaciones concretas no deben redefinir la arquitectura, sino reutilizarla cambiando solo la configuracion por modalidad y la estrategia de ranking.

### 1.2 Modalidades soportadas

El sistema se implementara inicialmente sobre dos modalidades prioritarias:

- `texto`
- `imagen`

La seleccion responde a la disponibilidad y coherencia del dataset elegido, que cubre de forma natural `imagen + texto`.

#### Texto

La modalidad textual servira para indexar nombres, descripciones y atributos de productos. El alcance inicial se limita a consultas por palabras clave en ingles, debido al idioma del dataset y al uso de TF-IDF; no se promete comprension semantica general de lenguaje natural.

#### Imagen

La modalidad visual servira para indexar imagenes de productos mediante descriptores locales y su posterior cuantizacion en un vocabulario visual. Esto permitira busqueda de similitud visual, recuperacion de productos parecidos y recomendaciones basadas en apariencia.

### 1.3 Tipos de consultas soportadas

El sistema debe soportar consultas monomodales y multimodales dentro del alcance actual `texto + imagen`.

#### Consultas textuales

Permiten ingresar palabras clave en ingles y recuperar productos relevantes segun el indice invertido textual.

Ejemplos:

- `"black sports shoes"`
- `"women casual handbag"`

#### Consultas por similitud visual

Permiten usar una imagen de entrada para recuperar productos o documentos visualmente parecidos.

Ejemplos:

- buscar prendas similares a una fotografia
- recuperar productos con estilo visual parecido

#### Consultas multimodales

Permiten combinar evidencia de mas de una modalidad en el ranking final.

Ejemplos:

- encontrar productos similares combinando apariencia y descripcion
- recomendar productos usando imagen y descripcion

### 1.4 Aplicaciones seleccionadas

De las cuatro ideas sugeridas en el enunciado, se seleccionaron las siguientes dos:

#### Idea 1: Busqueda Visual E-commerce

Esta aplicacion utiliza principalmente `imagen` y permite construir un caso de recuperacion por similitud visual dentro del dominio de productos de moda. La similitud observada no equivale necesariamente a preferencia humana, porque el dataset no incluye juicios explicitos de similitud. Se eligio porque:

- trabaja de forma natural con el dataset seleccionado
- permite recuperar productos visualmente similares a partir de una imagen consulta
- ofrece un caso simple y defendible para medir ranking por similitud visual
- reutiliza la misma representacion basada en `split`, extraccion y `codebook` visual

#### Idea 4: Recomendacion Multimodal

Esta aplicacion utiliza `imagen + texto` y permite cubrir la fusion multimodal dentro del mismo dominio. La recomendacion se entendera como recuperacion de productos relacionados, no como personalizacion, porque el dataset no contiene historial de usuarios. Se eligio porque:

- reutiliza la misma base de productos e imagenes
- permite fusionar similitud visual y descripcion textual
- produce resultados faciles de interpretar y demostrar
- cuenta con un dataset sugerido y accesible

### 1.5 Justificacion de la seleccion

La combinacion de las ideas 1 y 4 fue elegida por tres razones principales:

- coherencia del dominio: ambas aplicaciones operan sobre el mismo catalogo de productos de moda
- viabilidad de datos: un mismo dataset cubre ambas aplicaciones de forma natural
- reutilizacion del backend: las dos aplicaciones comparten `split`, extraccion, `codebook`, indexacion y fusion

Importancia de las aplicaciones:

- la busqueda visual e-commerce resuelve consultas donde el usuario conoce la apariencia deseada, pero no dispone del nombre o categoria exacta del producto
- la recomendacion multimodal permite compensar limitaciones de una sola modalidad: el texto aporta categoria y atributos, mientras la imagen aporta forma, color y apariencia
- ambas aplicaciones permiten demostrar el valor del mismo backend en recuperacion monomodal y fusion multimodal

### 1.6 Arquitectura general del backend

La arquitectura se organiza alrededor de modulos genericos para evitar implementaciones aisladas por aplicacion.

Capas propuestas:

- `Dataset Loader`: carga y normalizacion de datos
- `Splitter`: division del contenido en unidades atomicas
- `Feature Extractor`: extraccion de descriptores por modalidad
- `Codebook Builder`: construccion de vocabularios por modalidad
- `Indexer`: construccion de histogramas e indice invertido
- `Retriever`: ejecucion de consultas y ranking
- `Fusion Engine`: combinacion de puntajes multimodales
- `Persistence Layer`: almacenamiento en PostgreSQL

La implementacion de la arquitectura unificada se agrupa en `backend/src/multimodal/`, separada de las aplicaciones y de los modulos transversales:

| Etapa | Carpeta | Responsabilidad |
| --- | --- | --- |
| Contenido | `multimodal/stage_01_content/` | Carga, limpieza y particionado reproducible del dataset |
| Split Chunks | `multimodal/stage_02_split_chunks/` | Division del contenido en unidades procesables |
| Extractor Features | `multimodal/stage_03_extractor_features/` | Extraccion y preprocesamiento de caracteristicas textuales y visuales |
| Codebook | `multimodal/stage_04_codebook/` | Construccion de vocabularios e histogramas por modalidad |
| Indice Invertido | `multimodal/stage_05_inverted_index/` | Construccion de indices propios textuales y visuales |
| Busqueda por Similitud | `multimodal/stage_06_similarity_search/` | Recuperacion, ranking, catalogo y fusion multimodal |

Descripcion conceptual de los componentes:

- **Contenido:** representa la informacion original que ingresa al sistema. Reune las distintas modalidades asociadas a una misma entidad y garantiza que puedan relacionarse durante el procesamiento.
- **Split Chunks:** divide el contenido en unidades mas pequenas y manejables. Esto permite analizar cada parte de manera independiente sin perder su relacion con el contenido original.
- **Extractor Features:** identifica las caracteristicas mas representativas de cada unidad. Su objetivo es transformar contenidos de distinta naturaleza en representaciones que el sistema pueda comparar.
- **Codebook:** organiza las caracteristicas extraidas dentro de vocabularios compartidos. De esta manera, contenidos diferentes pueden describirse utilizando un conjunto comun de elementos representativos.
- **Indice Invertido:** registra donde aparece cada elemento representativo. Su funcion es reducir el espacio de busqueda y facilitar el acceso rapido a los contenidos potencialmente relevantes.
- **Busqueda por Similitud:** recibe una consulta, recupera candidatos y los ordena segun su semejanza. Cuando intervienen varias modalidades, tambien combina sus resultados para producir una respuesta unificada.

Aunque cada modalidad requiere un tratamiento particular, todas recorren estas etapas y producen resultados comparables. Esta estructura permite reutilizar el mismo flujo en diferentes aplicaciones y agregar nuevas modalidades sin modificar el proposito general de la arquitectura.

Los modulos transversales permanecen en `common/`, `persistence/`, `applications/` y `presentation/`. La interfaz visual ejecutable se mantiene separada en la carpeta `frontend/` ubicada en la raiz del proyecto.

El frontend separa las interfaces de las aplicaciones, pero utiliza una unica instancia compartida del backend:

- `frontend/app01_visual_search/`: interfaz de la aplicacion 1, busqueda visual e-commerce
- `frontend/app04_multimodal_recommender/`: interfaz de la aplicacion 4, recomendacion multimodal
- `frontend/shared/`: carga del backend y componentes visuales reutilizables
- `frontend/app.py`: punto de entrada y navegacion entre aplicaciones

La logica especifica de cada aplicacion debe limitarse a:

- definir que modalidades usa
- definir como se prepara la consulta
- definir como se combinan los puntajes del ranking

### 1.7 Adaptacion de la arquitectura por modalidad

| Etapa | Texto | Imagen |
| --- | --- | --- |
| Unidad original | Nombre, descripcion y atributos del producto | Imagen principal del producto |
| `split` | Un bloque corto o varios bloques descriptivos | Puntos de interes o grupos espaciales de descriptores |
| Extraccion | Tokens normalizados y ponderacion TF-IDF | Descriptores locales SIFT |
| `codebook` | Top-k terminos informativos despues del preprocesamiento | k centroides obtenidos con K-Means sobre una muestra de SIFT |
| Representacion | Vector o histograma de terminos | Histograma de visual words |
| Indice propio | SPIMI e indice invertido termino-producto | Indice invertido visual word-producto |
| Baseline PostgreSQL | Full-text search con GIN/GiST | Histogramas en pgvector con busqueda exacta, HNSW o IVFFlat |
| Ranking | Similitud textual | Similitud entre histogramas visuales |

En ambos casos, los resultados de chunks se agregaran por `product_id`. La fusion multimodal normalizara los puntajes textual y visual antes de combinarlos mediante pesos configurables.

## 2. Dataset utilizado y caracteristicas

### 2.1 Dataset seleccionado

El dataset seleccionado es `Fashion Product Images Dataset`, publicado en Kaggle y construido a partir de un catalogo de productos de Myntra. Es un dataset multimodal orientado a productos: cada item se identifica mediante un `product_id` y combina una imagen principal, atributos categoricos, un nombre descriptivo y metadatos JSON detallados.

La copia local analizada se encuentra en `archive/fashion-dataset/`. Cubre directamente las dos aplicaciones seleccionadas:

- idea 1: busqueda visual e-commerce mediante similitud entre imagenes
- idea 4: recomendacion multimodal mediante fusion de imagen y atributos textuales

### 2.2 Tamano y estructura fisica

La copia local, luego de eliminar una segunda copia completa que estaba anidada, ocupa `15,711,279,132 bytes`, equivalentes a `14.632 GiB`.

| Recurso | Contenido | Cantidad | Tamano aproximado |
| --- | --- | ---: | ---: |
| `images/` | Imagen principal de cada producto en formato JPEG | 44,441 archivos | 13.895 GiB |
| `styles/` | Metadatos detallados por producto en formato JSON | 44,446 archivos | 0.728 GiB |
| `styles.csv` | Tabla resumida de atributos por producto | 44,446 filas | 4.13 MiB |
| `images.csv` | Relacion entre nombre de imagen y URL original | 44,446 filas | 4.99 MiB |

La unidad logica principal es el producto. Las fuentes se enlazan mediante el mismo identificador numerico:

```text
styles.csv:        id = 15970
images/15970.jpg
styles/15970.json
images.csv:        filename = 15970.jpg
```

### 2.3 Modalidades y esquema de datos

#### Imagen

La modalidad visual contiene `44,441` imagenes JPEG legibles. No se detectaron archivos con extension incorrecta ni imagenes JPEG invalidas. Se encontraron `44` dimensiones distintas, concentradas principalmente en:

| Resolucion | Cantidad |
| --- | ---: |
| `1080 x 1440` | 24,459 |
| `1800 x 2400` | 19,721 |
| `150 x 200` | 119 |
| `360 x 480` | 60 |
| otras resoluciones | 82 |

La diferencia de resoluciones exige normalizar dimensiones o limitar la cantidad de keypoints SIFT para evitar que las imagenes grandes dominen la construccion del codebook.

#### Texto y atributos estructurados

`styles.csv` contiene los campos `id`, `gender`, `masterCategory`, `subCategory`, `articleType`, `baseColour`, `season`, `year`, `usage` y `productDisplayName`.

Los JSON contienen un esquema mas rico con marca, precio, rating, categorias, atributos variables, descripcion HTML, URLs de imagen y opciones de talla. De los `44,446` JSON:

- los `44,446` se pueden parsear correctamente
- `44,381` contienen una descripcion de producto
- `36,797` contienen atributos especificos del articulo
- se identificaron `424` marcas distintas

### 2.4 Distribucion de la coleccion

La coleccion no esta balanceada. Las categorias dominantes deben considerarse al construir subconjuntos y al interpretar las metricas.

| Campo | Valores con mayor frecuencia |
| --- | --- |
| `gender` | Men: 22,165; Women: 18,632; Unisex: 2,164; Boys: 830; Girls: 655 |
| `masterCategory` | Apparel: 21,400; Accessories: 11,289; Footwear: 9,222; Personal Care: 2,404 |
| `subCategory` | Topwear: 15,405; Shoes: 7,344; Bags: 3,055; Bottomwear: 2,694; Watches: 2,542 |
| `articleType` | Tshirts: 7,070; Shirts: 3,217; Casual Shoes: 2,846; Watches: 2,542; Sports Shoes: 2,036 |
| `baseColour` | Black: 9,732; White: 5,540; Blue: 4,922; Brown: 3,494; Grey: 2,741 |
| `season` | Summer: 21,476; Fall: 11,445; Winter: 8,519; Spring: 2,985 |
| `usage` | Casual: 34,414; Sports: 4,025; Ethnic: 3,208; Formal: 2,359 |

Cardinalidades observadas: `7` categorias principales, `45` subcategorias, `143` tipos de articulo, `47` colores base y `424` marcas.

### 2.5 Integridad, cobertura y calidad

Los identificadores de `styles.csv`, `images.csv` y los nombres de archivo son unicos dentro de cada fuente.

- `44,441` productos aparecen simultaneamente en `styles.csv`, `images.csv`, `images/` y `styles/`
- `5` productos tienen metadatos pero no imagen local: `12347`, `39401`, `39403`, `39410` y `39425`
- no existen imagenes locales ni JSON sin una fila correspondiente en `styles.csv`
- faltan `season` en 21 filas, `year` en 1 fila y `usage` en 1 fila

El analisis SHA-256 encontro `652` grupos de imagenes con contenido identico bajo IDs diferentes. Representan `779` archivos redundantes y aproximadamente `0.269 GiB`. No deben eliminarse automaticamente: cada ID puede representar un producto distinto y debe conservarse para mantener la integridad referencial.

### 2.6 Preparacion e ingesta

La ingesta debe construir un registro canonico por `product_id`. Para el pipeline principal se usara la interseccion de `44,441` productos que tienen imagen y metadatos completos.

Tratamiento propuesto:

1. Cargar `styles.csv` como fuente base de categorias.
2. Enlazar `images/<id>.jpg` y `styles/<id>.json` mediante `id`.
3. Extraer y limpiar `productDisplayName`, descripcion HTML y atributos relevantes.
4. Normalizar valores como `NA`, campos vacios, mayusculas y nombres de color.
5. Mantener los cinco productos sin imagen solo en pruebas textuales; excluirlos de experimentos visuales y multimodales.
6. Conservar IDs distintos aunque compartan la misma imagen.
7. Agrupar por hash las imagenes identicas antes de dividir entrenamiento, validacion y prueba, para impedir que copias identicas aparezcan en particiones distintas.

Texto canonico inicial por producto:

```text
productDisplayName + gender + masterCategory + subCategory +
articleType + baseColour + season + usage + brandName +
productDescriptors.description + articleAttributes
```

### 2.7 Estrategia para cargas experimentales

La coleccion contiene `44,446` productos y `44,441` productos multimodales completos. Por ello se separaran dos tipos de experimento:

- recuperacion extremo a extremo: `1K`, `10K` y `44,441` productos completos
- estres de indexacion: `1K`, `10K` y `100K` chunks derivados de texto y regiones visuales

Las metricas de calidad se calcularan sobre rankings de productos. Los `100K chunks` se usaran para medir construccion del indice, almacenamiento, latencia de acceso a chunks y agregacion hacia productos; no se presentaran como `100K` productos unicos.

El muestreo debe ser reproducible, estratificado por `masterCategory`, `subCategory` y, cuando sea posible, `articleType`. Los grupos con imagenes identicas deben permanecer en una sola particion.

Para evaluar relevancia:

- busqueda visual: `articleType` como relevancia aproximada, complementada con color y juicios manuales sobre un conjunto pequeno
- recomendacion multimodal: coincidencia ponderada de `articleType`, `subCategory` y atributos textuales, complementada con juicios manuales
- reportar metricas globales y por categoria para exponer el efecto del desbalance

### 2.8 Justificacion y limitaciones

La seleccion se justifica porque un mismo dataset soporta las dos aplicaciones elegidas, permite enlazar imagen y texto mediante una clave estable y contiene etiquetas utiles para construir criterios de relevancia reproducibles.

Limitaciones identificadas:

- la coleccion esta desbalanceada por categoria y uso
- cinco productos carecen de imagen local
- algunas descripciones contienen HTML y requieren limpieza
- existen imagenes identicas asociadas a IDs distintos
- las etiquetas permiten aproximar relevancia semantica, pero no constituyen juicios humanos de similitud visual
- la coleccion no alcanza `100K` productos unicos; esa escala debe construirse a nivel de chunks

## 3. Detalles de implementacion por modulo

### 3.1 Requisitos funcionales del sistema

El sistema debe cumplir los siguientes requisitos funcionales:

1. Debe permitir indexar datos de `texto` e `imagen` bajo una arquitectura comun.
2. Debe dividir cada modalidad en unidades manejables de procesamiento.
3. Debe extraer caracteristicas apropiadas para cada modalidad.
4. Debe construir un `codebook` por modalidad.
5. Debe generar un indice invertido o estructura equivalente para recuperar rapidamente items relevantes.
6. Debe soportar consultas de texto e imagen, asi como ranking multimodal por fusion de ambas modalidades.
7. Debe permitir combinar resultados de multiples modalidades en al menos dos aplicaciones.
8. Debe almacenar metadatos, histogramas y estructuras auxiliares en PostgreSQL.
9. Debe permitir comparar la recuperacion del sistema propio frente a `GIN/GiST` y `pgvector`.
10. Debe devolver un ranking ordenado con un `score` de relevancia o similitud.
11. Debe distinguir entre `chunk_id` y `product_id`, agregando resultados de chunks hacia un ranking final de productos.
12. Debe excluir o degradar de forma explicita las modalidades ausentes, sin inventar contenido.

### 3.2 Requisitos no funcionales

El sistema debe cumplir objetivos iniciales de calidad y rendimiento:

#### Latencia esperada

No se fijan umbrales absolutos antes de conocer el hardware, la configuracion de PostgreSQL y el valor de `k`. Los valores de latencia se trataran como resultados experimentales, no como requisitos garantizados.

La latencia debe medirse por modalidad y por tipo de indice, reportando promedio, mediana y `P95`. Se compararan cargas de `1K`, `10K` y `44,441` productos para recuperacion extremo a extremo, ademas de una carga de estres de `100K chunks`.

#### Precision esperada

La dataset no incluye ground truth de similitud ni comportamiento de usuarios. Por ello, la calidad se reportara usando dos niveles:

- relevancia aproximada basada en etiquetas, principalmente `articleType` y `subCategory`
- juicios manuales sobre un conjunto pequeno y fijo de consultas

La comparacion con PostgreSQL medira diferencias entre metodos bajo el mismo criterio de relevancia. Para indices aproximados de pgvector, tambien se medira `Recall@K` respecto a una busqueda vectorial exacta.

#### Otros atributos no funcionales

- escalabilidad extremo a extremo sobre `1K`, `10K` y `44,441` productos
- escalabilidad estructural sobre `1K`, `10K` y `100K` chunks
- uso compacto de memoria gracias a histogramas y `codewords`
- persistencia reproducible de indices y metadatos
- extensibilidad del backend para nuevas aplicaciones

#### Criterios verificables de aceptacion

Los requisitos no funcionales se evaluaran mediante criterios relativos, porque la Fase 1 todavia no fija hardware ni parametros finales:

- latencia: reportar mediana y `P95`; el `P95` no debe superar `2x` la mediana sin explicar las causas
- throughput: mantener una tasa estable durante una carga sostenida y reportar consultas por segundo
- precision: comparar todos los enfoques con el mismo conjunto de consultas y relevancia; reportar la diferencia frente al baseline exacto
- memoria y disco: medir el consumo total y por producto indexado para permitir comparaciones entre escalas
- reproducibilidad: conservar semilla, particiones, parametros, versiones y configuracion de PostgreSQL

Estos criterios no anticipan que un metodo deba ganar; permiten determinar de forma verificable sus trade-offs.

### 3.3 Modulo de ingesta

Este modulo recibe el dataset, normaliza su estructura y registra cada item con sus metadatos y referencias a contenido.

Ejemplos:

- productos: `product_id`, imagen, descripcion, categoria

La salida del modulo debe ser un registro canonico que permita alimentar el resto del pipeline.

El modulo debe registrar indicadores de calidad como `has_image`, `has_description` y `duplicate_image_group`, para que cada experimento pueda filtrar datos de forma reproducible.

### 3.4 Modulo de split

Este modulo transforma cada item en unidades atomicas procesables.

#### Texto

El `split` textual se aplicara sobre nombres, descripciones limpias y atributos asociados al catalogo.

- si el texto es largo, se divide en `chunks` como parrafos o bloques descriptivos
- si falta la descripcion o el texto es corto, se construye un unico `chunk` con `productDisplayName` y atributos estructurados disponibles

#### Imagen

La imagen se normalizara antes de detectar puntos de interes con `SIFT`. Cada descriptor o grupo espacial de descriptores puede actuar como chunk visual, mientras que el ranking final se agregara por producto.

### 3.5 Modulo extractor

Este modulo genera caracteristicas a partir de las unidades producidas por `split`.

#### Texto

Se seguira un pipeline linguistico clasico:

- conversion a minusculas
- eliminacion de puntuacion
- tokenizacion
- eliminacion de `stopwords`
- `stemming` o lematizacion
- ponderacion con `TF-IDF`

#### Imagen

Se utilizaran descriptores `SIFT`, tal como sugiere el enunciado. Debido a las resoluciones altas y variables, se fijara un tamano maximo de imagen y un limite reproducible de keypoints por producto.

### 3.6 Modulo codebook

Este modulo transforma las caracteristicas extraidas en un vocabulario finito de `codewords`.

#### Texto

El `codebook` textual se formara a partir de las `k` palabras mas frecuentes o mas informativas de la coleccion, luego del preprocesamiento.

#### Imagen

Los descriptores `SIFT` de entrenamiento se agruparan con `K-Means` para obtener un vocabulario de `visual words`. Para mantener viable el costo de memoria, el entrenamiento usara una muestra reproducible de descriptores tomada solo de la particion de entrenamiento.

### 3.7 Modulo de representacion e indexacion

Cada chunk se representara sobre el `codebook` correspondiente. Los histogramas de chunks se agregaran a nivel de `product_id`, que sera la unidad devuelta al usuario.

Este modulo debe producir:

- histogramas por item o por `chunk`
- indice invertido propio
- estructuras persistidas en PostgreSQL
- vectores o histogramas comparables mediante `pgvector`
- relacion explicita entre chunks y productos

### 3.8 Modulo de consulta y ranking

Este modulo transforma la consulta de entrada con el mismo pipeline de la modalidad correspondiente y genera un ranking final.

Debe soportar:

- ranking textual
- ranking visual
- ranking multimodal con fusion de puntajes

### 3.9 Adaptacion por aplicacion

#### Idea 1: Busqueda Visual E-commerce

Flujo previsto:

- entrada: imagen de producto
- `split` visual sobre `patches` o puntos de interes
- extraccion `SIFT` para imagen
- `codebook` visual
- ranking por similitud visual entre productos

#### Idea 4: Recomendacion Multimodal

Flujo previsto:

- entrada: imagen + descripcion del producto
- `split` visual sobre `patches` o puntos de interes
- `split` textual sobre descripcion
- extraccion `SIFT` para imagen y `TF-IDF` para texto
- `codebook` visual y textual
- ranking visual, textual o fusionado

### 3.10 Metricas de evaluacion definidas

La evaluacion experimental del proyecto comparara el backend propio con las alternativas nativas de PostgreSQL.

#### Metricas de rendimiento

- latencia promedio, mediana y `P95`, medida en milisegundos desde la recepcion de la consulta hasta la obtencion del top-k
- `throughput` en consultas por segundo bajo una concurrencia y duracion fijas
- tiempo de construccion del `codebook`
- tiempo de indexacion

#### Metricas de calidad

- `Precision@5`
- `Precision@10`
- `Recall@5`
- `Recall@10`
- `MAP`, solo sobre consultas con conjunto de relevantes definido
- `NDCG`, solo sobre el subconjunto con juicios manuales graduados
- `Recall@K` de HNSW o IVFFlat respecto a busqueda vectorial exacta

#### Metricas de recursos

- memoria maxima y promedio consumida por `codebook`, histogramas e indice, medida en MiB
- espacio en disco total y bytes por producto o chunk de las estructuras propias y de PostgreSQL
- lecturas y escrituras de bloques, tiempos de `I/O` y planes de ejecucion obtenidos con herramientas del sistema y `EXPLAIN (ANALYZE, BUFFERS)`

#### Protocolo minimo

Cada experimento debe:

1. fijar semilla, particion y unidad de carga: producto o chunk
2. mantener grupos de imagenes identicas dentro de una misma particion
3. fijar la carga de productos (`1K`, `10K` o `44,441`) o de chunks (`1K`, `10K` o `100K`)
4. construir el indice propio y el baseline de PostgreSQL sobre los mismos datos
5. ejecutar el mismo conjunto fijo de consultas
6. registrar latencia, calidad, memoria, disco e `I/O`
7. repetir mediciones y reportar agregados junto con hardware y parametros

#### Definicion de relevancia

La relevancia debe definirse por aplicacion y no puede inferirse directamente de que dos archivos sean iguales o pertenezcan a una categoria amplia:

- busqueda visual: usar `articleType` como etiqueta aproximada y evaluar manualmente una muestra para capturar color, forma y estilo
- recomendacion multimodal: combinar `articleType`, `subCategory` y atributos textuales; no afirmar personalizacion porque no existen datos de usuarios

Se deben reportar por separado los resultados basados en etiquetas aproximadas y los resultados del subconjunto evaluado manualmente. En consultas por producto se excluira el propio producto del ranking. Los productos con imagen duplicada no deben cruzar particiones ni inflar las metricas como aciertos independientes.

## 4. Verificacion de cumplimiento de la Fase 1

| Requisito del enunciado | Evidencia en el informe | Estado |
| --- | --- | --- |
| Especificar requisitos funcionales: modalidades y consultas | Secciones 1.2, 1.3 y 3.1 | Completo |
| Especificar requisitos no funcionales: latencia y precision | Seccion 3.2, incluidos criterios verificables | Completo |
| Seleccionar y documentar un dataset publico | Secciones 2.1 a 2.8: tamano, estructura, distribucion, integridad y limitaciones | Completo |
| Disenar la arquitectura y adaptar `split`, extraccion y `codebook` | Secciones 1.6, 1.7 y 3.3 a 3.9 | Completo |
| Definir metricas de latencia, throughput, precision, memoria y disco | Seccion 3.10 | Completo |
| Seleccionar al menos dos aplicaciones y sustentar su importancia | Secciones 1.4 y 1.5 | Completo |

La Fase 1 queda definida como diseno y protocolo de evaluacion. Las mediciones y comparaciones numericas se completaran en fases posteriores.

## 5. Resultados experimentales

Esta seccion sera completada mas adelante con tablas, metricas y graficos obtenidos durante la evaluacion del sistema.

## 6. Analisis de trade-offs y conclusiones

Esta seccion sera completada mas adelante con el analisis comparativo entre el indice propio, `GIN/GiST` y `pgvector`, junto con las conclusiones finales del proyecto.

## 7. Instrucciones de instalacion y uso

### 7.1 Requisitos

- Python `3.13`
- `pip` disponible para instalar dependencias
- Docker Desktop con Docker Compose, requerido solamente para PostgreSQL
- dataset descomprimido en `archive/fashion-dataset/`
- indices propios construidos antes de ejecutar las aplicaciones

La estructura esperada antes de iniciar es:

```powershell
Proyecto02/
|-- archive/fashion-dataset/
|-- artifacts/
|-- backend/
|-- frontend/
`-- README.md
```

Cada bloque de comandos presentado a continuacion supone que la terminal se encuentra inicialmente en la raiz `Proyecto02/`.

### 7.2 Preparacion del entorno Python

Desde la raiz del proyecto, crear y activar un entorno virtual:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

El archivo `backend/requirements.txt` documenta las dependencias utilizadas por el pipeline multimodal, PostgreSQL, el frontend y las pruebas.

### 7.3 Configuracion

La configuracion principal se encuentra en `backend/configs/`. Por defecto, el proyecto utiliza:

- dataset: `archive/fashion-dataset/`
- artefactos generados: `artifacts/`
- escala activa: `1k`
- PostgreSQL: puerto host `5433`

Para personalizar PostgreSQL, crear `backend/.env` a partir del ejemplo:

```powershell
cd backend
Copy-Item .env.example .env
```

### 7.4 Construccion de artefactos de Fase 2

Los comandos de construccion deben ejecutarse desde `backend/`. Primero se genera el catalogo y las particiones reproducibles:

```powershell
cd backend
python -m scripts.build_catalog
```

Luego se construyen los indices textuales y visuales. La escala `1k` es la recomendada para pruebas rapidas:

```powershell
cd backend
python -m scripts.build_text_index --scale 1k
python -m scripts.build_visual_index --scale 1k
```

Tambien se admiten las escalas `10k` y `full`, pero requieren mas tiempo, memoria y espacio de almacenamiento.

### 7.5 Persistencia PostgreSQL

Esta etapa es opcional para las aplicaciones de Fase 2. Para levantar PostgreSQL con pgvector:

```powershell
cd backend
docker compose up -d
```

Aplicar el esquema y cargar los artefactos construidos:

```powershell
cd backend
python -m scripts.load_postgres --scale 1k --init-schema
```

La carga puede repetirse sin duplicar registros. Para consultar los conteos persistidos:

```powershell
cd backend
python -m scripts.load_postgres --counts-only
```

Para detener PostgreSQL:

```powershell
cd backend
docker compose down
```

### 7.6 Ejecucion por consola

Desde `backend/`, ejecutar la aplicacion 1 de busqueda visual:

```powershell
cd backend
python -m scripts.run_visual_search --product-id 1550 --scale 1k --top-k 5
```

Ejecutar la aplicacion 4 de recomendacion multimodal:

```powershell
cd backend
python -m scripts.run_multimodal_recommender --product-id 1550 --scale 1k --top-k 5
```

Ambos comandos reutilizan la misma arquitectura multimodal y los mismos artefactos de la escala seleccionada.

### 7.7 Frontend visual

Desde la raiz del proyecto, iniciar la interfaz compartida:

```powershell
python -m streamlit run frontend/app.py
```

El frontend carga una unica instancia del backend y presenta dos interfaces separadas:

- `App 01 - Busqueda visual`: consulta mediante un producto del catalogo o una imagen subida
- `App 04 - Recomendacion multimodal`: combina la informacion textual y visual de un producto

El frontend utiliza actualmente la escala `1k`.

### 7.8 Pruebas

Ejecutar la suite automatizada desde `backend/`:

```powershell
cd backend
python -m pytest
```
