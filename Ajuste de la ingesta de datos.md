# Ajuste de la ingesta de datos

**Objetivo: **ajustar el preprocesamiento de la información que será mandada a la base de datos.


**Lo que falta con respecto al esquema actual**

Separar el autor en nombres y apellidos.

Añadir familiares destacados.

Estructurar mejor lugares como objetos con ciudad, municipio, estado y país.

Incluir multimedia del autor: imagen, audio y lista de enlaces con tipo y restricción.

En obras: agregar multimedia, PDF, portada JPG, MP3, y más detalle editorial.

En críticas: agregar referencia bibliográfica más completa y enlace.

Agregar secciones para agrupaciones, revistas y antologías con sus campos específicos.

Agregar el bloque de mitos y leyendas.

Ampliar la capa de lectura para soportar más tipos de archivo que solo .md y .docx, como PDF, imágenes, audio o video, si eso entra en el flujo.

Resumen

ajustar la salida al siguiente formato

**Autor**

* **Identidad:**
  * `nombres`: Nombres del autor.
  * `apellidos`: Apellidos del autor.
  * `sexo`: Género del autor.
  * `seudonimo`: Seudónimo utilizado.
* **Cronología y Ubicación:**
  * `fechaDeNacimiento`: Fecha completa.
  * `fechaDeFallecimiento`: Fecha completa (si aplica).
  * `lugarDeNacimiento`: Objeto o string desglosado (ciudad, municipio, estado, país).
  * `lugarDeFallecimiento`: Objeto o string desglosado (ciudad, municipio, estado, país).
* **Trayectoria y Entorno:**
  * `actividadRelevante`: Tipo (estudios, cargos, profesión), lugar y periodo.
  * `familiaresDestacados`: Listado de parientes (padres, hermanos, hijos, etc.).
  * `contextoEnQueVivio`: Descripción del marco histórico y social.
* **Perfil Literario:**
  * `tematicaPrincipal`: Temas centrales en el conjunto de su obra.
  * `generoPrincipal`: Género principal cultivado.
* **Archivos y Multimedia:**
  * `imagenAutor`: Referencia o enlace al archivo **.jpg**.
  * `audioVoz`: Referencia o enlace al archivo **.mp3** (voz del autor).
  * `multimedia`: Lista de objetos con `enlace`, `tipo` y `restriccion`.

**Obras**: Representa los datos bibliográficos, tipológicos y editoriales de las obras creadas por el autor:

* Título
* Género (novela, cuento, poesía, ensayo, revista, antología. Incluir subgéneros)
* Fecha de publicación
* Lugar de publicación (ciudad, imprenta, editorial)
* Descripción o resumen (en caso de revistas o antologías, que exista la posibilidad de mencionar a autores, temas, números publicados…)
* Idioma original
* Multimedia (Enlace, Tipo, Restricción)
* Obra en archivo pdf, portada en jpg y en mp3 todas para descarga y lectura.

**Crítica:** Se entiende por crítica a las interpretaciones, lecturas y valoraciones realizadas a las obras y a los autores.

* Tipo (libro, artículo, reseña, trabajo de grado…)
* Autor
* Título
* Fecha de publicación
* Referencia bibliográfica (¿dónde fue publicada la crítica?, incluir además el enlace)
* Descripción o resumen de la crítica

 

**Agrupaciones, Obras colectivas y periódicas:** En esta ficha se incluyen obras como revistas y antologías, además de descripción de agrupaciones literarias.

* Tipo (Agrupación, Revista, Antología)

* Si es “**Agrupación**”, se deben desplegar los siguientes campos:
  * Nombre de la agrupación
  * Lugar de encuentros (ciudad, municipio)
  * Fecha de inicio
  * Fecha de culminación
  * Característica general de la agrupación (tendencia, ideología)
  * Integrantes (Nombres y Apellidos)
  * Publicaciones de la agrupación (Título, año, resumen de la obra)
  * Actividades de la agrupación

* Si es “**Revista**”, se deben desplegar los siguientes campos:
  * Título
  * Fecha de primer número
  * Fecha de último número
  * Números publicados
  * Lugar de publicación (ciudad, imprenta, editorial)
  * Creadores (director, comité editorial, etc.).
  * Secciones de la revista
  * Descripción (temas y géneros predominantes, autores relevantes)
  * Idioma original
  * Multimedia (Enlace, Tipo, Restricción)
  * Obra en archivo pdf y portada en jpg, todas para descarga y lectura.

 

* Si es “**Antología**”, se deben desplegar los siguientes campos:
  * Autor
  * Título
  * Género (novela, cuento, poesía, ensayo)
  * Fecha de publicación
  * Lugar de publicación (ciudad, imprenta, editorial)
  * Descripción o resumen (mencionar autores seleccionados)
  * Idioma original
  * Multimedia (Enlace, Tipo, Restricción)
  * Obra en archivo pdf y portada en jpg para descarga y lectura.

**Mitos y Leyendas**

* Título:
* Comunidad creadora:
* Lugar de difusión: (pueblo, municipio, ciudad, estado)
* Idioma original:
* Texto completo del mito o leyenda:
* Tema principal del mito o leyenda:
* Descripción o resumen:
* Multimedia:
* Obra en archivo jpg, audio o video.

## Metadata
- URL: [https://linear.app/proyecto-ia-fichas/issue/PRO-13/ajuste-de-la-ingesta-de-datos](https://linear.app/proyecto-ia-fichas/issue/PRO-13/ajuste-de-la-ingesta-de-datos)
- Identifier: PRO-13
- Status: Todo
- Priority: Urgent
- Assignee: Cristian Baczek
- Project: [Proyecto 2 de IA](https://linear.app/proyecto-ia-fichas/project/proyecto-2-de-ia-b65bb1818b97/overview). 
- Created: 2026-06-14T00:42:10.614Z
- Updated: 2026-06-14T02:11:30.688Z