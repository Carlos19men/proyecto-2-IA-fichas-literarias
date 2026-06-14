# Desarrollo de interfaz — LetraScopio
### PRO-16 · Urgente · Asignado a: victor

Esta es la tarea técnica detallada para el desarrollo del **front-end**, diseñada para que un desarrollador establezca la base visual y funcional del proyecto **LetraScopio**, siguiendo los estándares de usabilidad e interactividad del modelo original.

---

## 🔍 Investigación UX: Benchmarking y Decisiones de Diseño

> *Esta sección fue añadida por el UX Designer del proyecto para orientar las decisiones visuales antes de entrar a Figma. No es opinión: es dirección.*

### ¿Qué hace la competencia? Análisis de referentes directos

LetraScopio no es un chatbot genérico ni una enciclopedia clásica. Es algo nuevo: un **agente literario conversacional con memoria y multimedia**. Eso define con quién competimos y a quién debemos superar en UX.

#### 1. ChatGPT / Claude / Gemini — Referente de interacción conversacional

**Qué hacen bien:**
- Input centrado, burbujas de respuesta con texto enriquecido, sidebar de historial
- Tema claro/oscuro nativo con transición suave
- Sugerencias de preguntas al inicio (chips clicables)
- Claude usa tipografía serif para las respuestas largas → transmite autoridad intelectual

**Qué les falta (nuestra oportunidad):**
- No tienen componentes multimedia nativos (galería, audio, PDF viewer)
- Identidad visual genérica — ninguno está pensado para cultura literaria
- La landing page es simplemente un campo de búsqueda vacío, sin contexto ni seducción

**Decisión para LetraScopio:** Tomar su patrón de interacción (probado y familiar para el usuario) pero construir **una identidad visual que huela a libro, a archivo, a cultura**.

---

#### 2. Perplexity AI — Referente de "respuesta enriquecida con fuentes"

**Qué hacen bien:**
- Las respuestas combinan texto + fuentes citadas con badges visuales
- Barra de búsqueda con sugerencias de seguimiento ("Related")
- Modo "Focus" que acota el dominio de búsqueda → muy aplicable a LetraScopio (Focus: Autores / Obras / Épocas)
- Diseño limpio: mucho espacio en blanco, tipografía sans-serif moderna

**Qué les falta:**
- Sin soporte multimedia (no reproduce audio, no muestra galerías)
- Sin personalidad visual de nicho — podría ser un buscador de cualquier cosa

**Decisión para LetraScopio:** Adoptar el patrón de **respuesta con metadatos visibles** (imagen del autor, fecha, géneros) como Perplexity muestra sus fuentes, pero integrado en una burbuja de chat diseñada para fichas literarias.

---

#### 3. Britannica / World Book — Referente de enciclopedia de cultura

**Qué hacen bien:**
- Jerarquía editorial clara: título del artículo, extracto, multimedia, lectura completa
- Imágenes de alta calidad como primer elemento visual
- Credibilidad institucional transmitida en tipografía y layout

**Qué les falta:**
- Cero conversacionalidad — no puedes preguntar en lenguaje natural
- Diseño anticuado y lento, sin dark mode, sin accesibilidad moderna
- Sin audio, sin integración con IA

**Decisión para LetraScopio:** Tomar su **autoridad editorial** (tipografía con personalidad, jerarquía de contenido literario) pero liberarla en una interfaz conversacional fluida. Britannica con alma de chat.

---

#### 4. Elicit.org — Referente de "conocimiento especializado con IA"

**Qué hacen bien:**
- Interfaz orientada a extracción estructurada de información (tablas, resúmenes, comparativas)
- Muy claro en mostrar "qué sabe" y "de dónde viene"
- Onboarding con ejemplos de uso inmediatos

**Qué les falta:**
- Frío y técnico — diseñado para investigadores, no para lectores
- Sin componentes para disfrutar el contenido (no reproduce nada, no muestra imágenes con elegancia)

**Decisión para LetraScopio:** El modelo de **datos estructurados dentro de la respuesta** (metadata de autor, género, época) es correcto, pero presentado con calidez visual, no como tabla de base de datos.

---

### Conclusiones del Benchmarking → Dirección de Diseño

| Dimensión | Competencia hace | LetraScopio debe hacer |
|---|---|---|
| Interacción | Chat centrado (ChatGPT) | Chat centrado + chips de sugerencia temáticos |
| Respuesta | Solo texto o texto+fuentes | Tarjeta literaria: texto + imagen + audio + PDF |
| Identidad | Genérica o académica fría | Literaria, cálida, con carácter editorial |
| Multimedia | Ausente o básica | Nativa y elegante (galería, mp3, PDF preview) |
| Landing | Campo vacío o marketing SaaS | Narración: "Explorá la literatura argentina con IA" |
| Temas | Claro/Oscuro estándar | Claro (papel de libro) / Oscuro (biblioteca nocturna) |

---

## 🎨 Sistema Visual — Token Design

### Paleta de Colores

```
TEMA CLARO — "Papel y Tinta"
  --bg-primary:    #FAF8F5   Blanco marfil cálido (no blanco puro)
  --bg-secondary:  #F0ECE6   Crema suave para paneles secundarios
  --accent:        #1A3A5C   Azul noche profundo (botones, links, logo)
  --accent-light:  #2E6DA4   Azul medio para estados hover
  --text-primary:  #1C1C1E   Casi negro (no negro puro — reduce fatiga)
  --text-muted:    #6B6B6B   Gris medio para metadata y secundario
  --border:        #DDD8D0   Borde suave, cálido

TEMA OSCURO — "Biblioteca Nocturna"
  --bg-primary:    #16181D   Casi negro con tono azulado (no negro puro)
  --bg-secondary:  #1E2128   Panel lateral y tarjetas
  --accent:        #4A9EE8   Azul brillante accesible sobre fondo oscuro
  --accent-light:  #6FB8FF   Versión hover del acento
  --text-primary:  #E8E6E1   Blanco cálido (no #FFFFFF — reduce fatiga)
  --text-muted:    #9B9B9B   Gris claro para metadata
  --border:        #2E3138   Borde sutil
```

**Por qué esta paleta:** El blanco marfil y el azul noche conectan con el universo del libro impreso y la biblioteca. Evita el azul eléctrico estándar de los productos tech genéricos. El modo oscuro tiene un tono azulado (no gris puro) que evoca la atmósfera de leer de noche.

---

### Tipografía

```
DISPLAY / HEADINGS:   "Playfair Display" — Serif con carácter editorial clásico
                      Uso: Logo, títulos de sección, nombre del autor en tarjetas
                      Estilo: 700 weight, tracking -0.02em

BODY / RESPUESTAS:    "Inter" — Sans-serif moderna y legible
                      Uso: Cuerpo de chat, UI labels, metadata
                      Estilo: 400/500 weight, line-height 1.6

MONOSPACE / CÓDIGO:   "JetBrains Mono" — Para mostrar IDs, referencias técnicas
                      Uso: Identificadores de ficha, citas con referencia
```

**Por qué Playfair Display:** Es la tipografía display más reconociblemente "literaria" sin ser anticuada. La usan publicaciones como The Guardian Books, Electric Literature y Longreads. Crea contraste elegante con Inter para el cuerpo.

**Alternativa si Playfair es demasiado clásica:** `Fraunces` (Variable font, más moderno, usado por Squarespace en contextos editoriales).

---

### El Elemento Firma de LetraScopio

**La Tarjeta Literaria (Literary Card)** — el componente que hace único a LetraScopio.

Cuando el agente responde sobre un autor u obra, no devuelve texto plano. Devuelve una **tarjeta estructurada** que combina:

```
┌─────────────────────────────────────────────────────┐
│  [Foto del autor]   OSCAR PIRRONGELLI               │
│  📸 thumbnail       Narrativa · 1943–2019           │
│                     Rosario, Argentina              │
│─────────────────────────────────────────────────────│
│  Respuesta del agente en texto natural...            │
│  Lorem ipsum sobre la obra y contexto histórico.    │
│─────────────────────────────────────────────────────│
│  🎵  Escuchar voz del autor    [▶ Play]             │
│  📄  Ver obra completa         [Abrir PDF]          │
│  🖼️  Galería fotográfica       [Ver 4 fotos]        │
└─────────────────────────────────────────────────────┘
```

Esta tarjeta es el **diferenciador #1** de LetraScopio frente a cualquier competidor. Ningún chatbot existente hace esto de forma nativa y elegante.

---

## 🏗️ Arquitectura de Pantallas

### Wireframe — Landing Page

```
┌────────────────────────────────────────────────────────┐
│  LetraScopio                              [☀️/🌙] [ES] │
├────────────────────────────────────────────────────────┤
│                                                        │
│         Explorá la literatura argentina                │
│              con inteligencia artificial               │
│                                                        │
│    ┌──────────────────────────────────────────┐       │
│    │ 🔍 Preguntame sobre un autor u obra...   │       │
│    └──────────────────────────────────────────┘       │
│                                                        │
│    [¿Quién fue Pirrongelli?]  [Obras del 60]          │
│    [Literatura gauchesca]     [Autoras del NOA]        │
│                                                        │
├────────────────────────────────────────────────────────┤
│  ✦ Búsqueda semántica    ✦ Audio y fotos de autores   │
│  ✦ Obras completas en PDF  ✦ Memoria contextual       │
├────────────────────────────────────────────────────────┤
│  [Vista previa animada del chat con mock data]         │
└────────────────────────────────────────────────────────┘
```

**Nota de UX:** La landing no debe ser un hero vacío como ChatGPT. Debe **narrar** y **demostrar**. El área de preview muestra una conversación simulada con una tarjeta literaria real (mock data) para que el usuario entienda el valor antes de empezar.

---

### Wireframe — Módulo de Chat

```
┌──────────────┬─────────────────────────────────────────┐
│   SIDEBAR    │              CHAT AREA                  │
│              │                                         │
│  LetraScopio │  ┌─────────────────────────────────┐   │
│              │  │ 👤 ¿Quién fue Oscar Pirrongelli? │   │
│  + Nueva     │  └─────────────────────────────────┘   │
│  conversación│                                         │
│              │  ┌──────────────────────────────────┐  │
│  ─────────── │  │ 🤖  [TARJETA LITERARIA]           │  │
│              │  │  [Foto] OSCAR PIRRONGELLI         │  │
│  📜 Conversac│  │         Narrativa · 1943-2019     │  │
│  anterior 1  │  │  ─────────────────────────────   │  │
│              │  │  Texto de respuesta del agente... │  │
│  📜 Conversac│  │  ─────────────────────────────   │  │
│  anterior 2  │  │  🎵 [Play]  📄 [PDF]  🖼️ [Fotos] │  │
│              │  └──────────────────────────────────┘  │
│              │                                         │
│              │  ┌─ Preguntas relacionadas ──────────┐  │
│              │  │ [¿Qué obras escribió?]            │  │
│              │  │ [¿De qué corriente literaria?]    │  │
│              │  └──────────────────────────────────┘  │
│              │                                         │
│              │  ┌──────────────────────────────────┐  │
│              │  │  Escribí tu pregunta...    [🎤][→]│  │
│              │  └──────────────────────────────────┘  │
└──────────────┴─────────────────────────────────────────┘
```

---

## 🧩 Componentes Principales a Desarrollar

### A. Landing Page

- **Hero Section:** Titular + subtítulo + buscador central + chips de ejemplo
- **Demo Preview:** Conversación animada con mock data que muestra una tarjeta literaria
- **Feature Grid:** 4 características clave con íconos (búsqueda semántica, multimedia, PDF, memoria)
- **Footer:** Créditos, versión del proyecto, links al equipo

### B. Módulo de Chat Inteligente

- **Input de Usuario:** Campo de texto central con botón de envío y botón de micrófono (🎤) para futura integración de voz
- **Burbujas de Chat:** Distinción visual entre pregunta del usuario (derecha, fondo acento suave) y respuesta del agente (izquierda, tarjeta estructurada)
- **Tarjeta Literaria:** El componente clave — ver diseño detallado arriba. Mapea directamente el JSON del backend
- **Chips de Seguimiento:** Sugerencias de preguntas relacionadas que aparecen tras cada respuesta
- **Sidebar de Historial:** Lista de conversaciones anteriores con título generado automáticamente

### C. Componentes Multimedia

| Componente | Trigger JSON | Comportamiento |
|---|---|---|
| Galería de imágenes | `metadata.imagenes` | Grid 2x2 con lightbox al clicar. Soporta JPG/PNG |
| Reproductor de audio | `metadata.audios` | Player inline con waveform visual, play/pause, scrubber |
| Visor de documentos | `metadata.pdfs` | Preview de primera página + botón "Abrir en nueva pestaña" |

---

## 📋 Tarea: Desarrollo de la Interfaz (Original)

**Objetivo:** Construir la base del front-end para el diccionario literario utilizando una arquitectura moderna, centrada en una interfaz de chat inteligente que permita consultas en lenguaje natural y la visualización de contenidos multimedia.

### 1. Tecnologías y Herramientas Obligatorias

- **NextJS:** Para la creación de la interfaz, aprovechando su capacidad de renderización rápida y carga estática de páginas para optimizar la experiencia del usuario.
- **Figma:** Debe utilizarse para el diseño previo de los wireframes e interactividad de las pantallas antes de la codificación.
- **Tailwind CSS (Recomendado):** Para implementar de forma ágil la paleta de colores y el diseño bitemático.

### 2. Identidad Visual y Accesibilidad

- **Nombre del Proyecto:** La aplicación debe identificarse claramente como **LetraScopio** en el encabezado, usando Playfair Display.
- **Paleta de Colores Dual:** Ver sistema de tokens definido en la sección de investigación UX.
- **Comandos de Voz:** Incluir un botón de micrófono para integrar en el futuro la capacidad de realizar preguntas mediante grabación de voz.

---

## 🔗 Consideraciones para la Conexión Posterior con el Modelo

Aunque por ahora se trabajará en la base visual, el desarrollador debe tener en cuenta los siguientes procesos para la integración futura con el motor de IA:

1. **Flujo de Comunicación:** El front-end (NextJS) enviará la pregunta del usuario mediante una petición **POST** a una API en **NestJS**, la cual servirá de puente con el servidor del agente inteligente en **FastAPI**.

2. **Manejo de Estados con LangGraph:** La interfaz debe estar preparada para manejar "estados". El backend enviará la respuesta una vez que el agente haya pasado por los nodos de clasificación, generación de Cypher y recuperación en Neo4j.

3. **Procesamiento del JSON de Salida:** El modelo GraphRAG devolverá un objeto JSON que el front-end mapeará automáticamente:

```json
{
  "respuesta_texto": "→ Burbuja de chat",
  "metadata": {
    "nombre": "Oscar Pirrongelli",
    "disciplina": "Narrativa",
    "periodo": "1943–2019",
    "imagenes": ["→ Componente galería"],
    "audios":   ["→ Reproductor mp3"],
    "pdfs":     ["→ Visor de documentos"]
  }
}
```

4. **Memoria Contextual:** La estructura de datos del chat debe soportar un historial de mensajes para la futura fase de memoria contextual. Diseñar el estado del chat como un array de mensajes desde el día 1.

---

## ✅ Entregable Esperado

Un prototipo funcional en NextJS con:

- Landing page con sección hero, demo animada con mock data y grid de características
- Interfaz de chat operativa con respuestas simuladas (mock data) que renderice la Tarjeta Literaria completa (texto + imagen placeholder + audio player + PDF link)
- Cambio de tema claro/oscuro funcional con los tokens definidos en este documento
- Sidebar de historial de conversaciones (con datos mock)
- Chips de sugerencias de preguntas configurables

---

## 📎 Metadata

- **URL:** [PRO-16 en Linear](https://linear.app/proyecto-ia-fichas/issue/PRO-16/desarrollo-de-interfaz)
- **Identifier:** PRO-16
- **Status:** Todo
- **Priority:** Urgent
- **Assignee:** victor
- **Project:** [Proyecto 2 de IA](https://linear.app/proyecto-ia-fichas/project/proyecto-2-de-ia-b65bb1818b97/overview)
- **Created:** 2026-06-14T01:11:16.055Z
- **Updated:** 2026-06-14 (UX Research añadido)
