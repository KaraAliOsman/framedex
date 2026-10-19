# DEKOPEN — Constitución de diseño y calidad

> **Estado:** obligatoria. P00 la commitea en `docs/design/CONSTITUCION.md`. A partir de ahí es la fuente de verdad del diseño. Prevalece sobre cualquier gusto personal, convención SaaS o "lo que suele hacerse". Si un encargo la contradice, gana la constitución; si la constitución no cubre un caso, decide según el §1 y deja la decisión registrada en el PR.
>
> **Origen:** consolida el punto de vista que DEKOPEN ya había definido y nunca adoptó: `dekopen-visual-identity-study.md`, `dekopen_interaction_study.md` y los tableros board-01 a board-06. Agrega la voz, las superficies, los momentos de firma, la lista anti-slop y el pase editorial.

> **Enmienda 2026-10 (encargo v1).** El dueño rechazó los dos temas, la tipografía de consola, los controles poco distinguibles, el cargador de cota y la mascota anteriores, y pidió una experiencia profesional, sencilla, viva y agradable ([encargo](../research/2026-10-17-claude/00-encargo-y-criterios.md), [dirección propuesta](../research/2026-10-17-claude/04-direccion-visual-e-interaccion.md)). Esta enmienda sustituye en el texto las reglas en conflicto: un tema claro único, lectura más cómoda, controles inequívocos, radios por función, iconos genéricos reconocibles, carga contextual con progreso real y un compañero IA circular 2D. **Se mantienen sin cambio** el dibujo como interfaz, la fuente única de cifras, lo desconocido visible, el revelado progresivo, la inmutabilidad, la accesibilidad y la eliminación de caminos sustituidos. Los valores concretos son la dirección de trabajo de la implementación; **no constan como aceptados por el dueño** hasta que revise el producto real.

> **Enmienda 2026-10-18 (dirección final del dueño).** DEKOPEN es primero un **cotizador manual profesional y completo**; el plan base no necesita IA ([dirección final](../research/2026-10-18-direccion-final/README.md)). Hay **dos vistas del mismo trabajo**: *Mesa de obra* (inicial recomendada) y *Estudio* (elegible por cada usuario), sobre la misma obra, revisión, selección, borrador y operaciones. El asistente pasa a ser un **popup global opcional, no modal**, cerrado al iniciar sesión, que nunca reserva columna, no reemplaza el inspector ni encoge el lienzo. Tiene modos **Chat/Trabajo** y tres autonomías (**Solo proponer · Con aprobación · Omitir todo**). El compañero se reconstruye con alta fidelidad al personaje animado de Grok Bot (cuerpo limpio y ojos negativos, sin placa facial). El catálogo normal es **real** (fabricante → serie → configuración/artículo) y el DEMO se consulta en un laboratorio explícito. Esta enmienda sustituye §5.1 (botón Asistente), §5.3, §5.4 (riel compartido), §5.11, la regla de vista previa universal de §6 y el catálogo por defecto de §11. **Se mantienen** motor como única fuente de cifras, Decimal, lo desconocido visible, inmutabilidad, número único, accesibilidad, clic humano para efectos externos y eliminación de caminos sustituidos.

---

## 0. Por qué existe este documento

Un modelo de lenguaje, cuando no tiene un punto de vista, entrega **el promedio estadístico de lo que ya existe**: tarjetas redondeadas, sombras suaves, un degradado morado, "¡Bienvenido de nuevo!", un dashboard con cuatro KPI. Se ve terminado en segundos y no resuelve nada. Eso es la **UI zombi**: software desechable, sin coherencia y sin alguien detrás que se haya preocupado.

DEKOPEN no puede ser eso, por cinco razones:

1. **Terminado no es bueno.** Una pantalla con bordes redondeados y sombras sutiles no está resuelta: solo tiene barniz. Un trabajo está bueno cuando un estimador cotiza 12 posiciones más rápido que con su software actual, sin dudar de ningún número.
2. **El punto de vista viene antes que la pantalla.** Si no lo fijamos nosotros, la IA impone el suyo, que es genérico y mira al pasado. Este documento es el nuestro.
3. **Se diseña el sistema que genera las pantallas.** Cada estándar de este documento se convierte en token, componente, guarda de lint o test (P01). Así no solo se escala la consistencia: se escala la intención.
4. **La calidad se filtra al final, con un editor implacable.** Producir es barato. Por eso cada PR termina con un pase editorial (§9) que revisa el flujo completo, se hace responsable de cada decisión y elimina lo arbitrario.
5. **La IA sirve para subir el techo, no solo para llegar más rápido al piso.** Cada superficie tiene un momento propio (§7) y una idea que va más allá de lo evidente (§8). Lo singular se protege (*protect the strange*).

---

## 1. Punto de vista

### 1.1 La frase

> **DEKOPEN se dibuja como se dibuja una ventana.**

La ventana y el documento son los protagonistas y deben parecer trabajo profesional bien resuelto; la interfaz hace fácil manipularlos. Entorno **claro, luminoso y preciso**, turquesa contenido, dibujos ricos en material y controles que se reconocen sin pasar el mouse. La personalidad sale de las proporciones, la respuesta inmediata y la claridad, no de metáforas técnicas por todas partes. **No es un SaaS genérico ni un ERP del 2005.**

**La prueba del taller y del cliente:** una persona del oficio debe saber qué hacer en la pantalla sin explicación previa, y un cliente final debe reconocer una propuesta seria en el documento. Falla si parece la promo de un plugin (degradados, sombras de color, copy simpático) y también si parece una consola técnica (mayúsculas pequeñas, todo en monoespaciada, controles que parecen texto).

### 1.2 Para quién diseñamos y qué debe sentir

| Persona | Contexto real | Lo que debe sentir | Densidad |
|---|---|---|---|
| **Estimador/a** | Oficina, monitor de 24", 30 a 80 posiciones por obra, presión de plazo | "Esto entiende ventanas y me ahorra horas" | `office` |
| **Dueño/a de la fábrica** | Notebook o celular, entre visitas a obra | "Sé dónde se gana y dónde se pierde plata hoy" | `office` |
| **Jefe/a de taller** | Pantalla en planta, con guantes, ruido | "Sé qué cortar, en qué orden y qué falta" | `workshop` |
| **Operario/a** | Tablet en la estación, de pie, 2 m de distancia | "Una pieza, una pantalla, cero dudas" | `workshop` |
| **Instalador/a** | Celular en obra, sol, una mano | "Sé qué llevar, dónde va y cómo cerrar el trabajo" | `workshop` |
| **Cliente final** | Celular o PC, sin vocabulario técnico | "Esta empresa es seria; entiendo qué compro y cuánto cuesta" | `document` |

### 1.3 Las cinco promesas (en este orden)

1. **"Esto entiende ventanas."** Cada dibujo obedece la lógica de la fenestración: vista declarada, simbología correcta, correderas en carriles, manilla del lado de cierre.
2. **"Es dramáticamente más fácil."** El usuario básico llega al precio con sistema, medidas, apertura, vidrio y color. Nada más.
3. **"Conecta lo que antes hacía a mano."** Cotización, compra, corte, producción, despacho e instalación salen del mismo modelo, sin volver a digitar.
4. **"Trabaja por mí."** Lo que el motor puede derivar, no se le pregunta al usuario. La IA ejecuta, no solo conversa.
5. **"Confío en los números."** Cada cifra tiene una fuente visible a un clic. Lo desconocido se muestra como desconocido.

### 1.4 Lo que DEKOPEN NO es

- No es un dashboard SaaS genérico con KPI decorativos.
- No es un formulario gigante con un dibujo de adorno.
- No es un chatbot pegado al costado.
- No es una demo: ningún botón existe sin efecto real.
- No es frío ni chistoso: es preciso, tranquilo y agradable de usar. La calidez está en la respuesta, los buenos valores por defecto y el cuidado del detalle, no en los chistes.

---

## 2. Principios (con "sí" y "no" concretos)

| # | Principio | Sí | No |
|---|---|---|---|
| P1 | **El dibujo es la interfaz.** | El lienzo ocupa ≥ 60 % del editor; se edita sobre la cota, en el lugar | Formularios de ancho completo con el dibujo como miniatura |
| P2 | **Un número, una fuente.** | Cada monto, medida o peso abre "¿De dónde sale?" con la traza del motor | Cifras calculadas en el frontend o escritas por la IA |
| P3 | **Lo desconocido se ve.** | "Sin dato · falta el peso del vidrio · Completar" | `0`, `—` sin causa, o un valor por defecto silencioso |
| P4 | **Divulgación progresiva.** | Básico: 6 decisiones. Avanzado: perfiles, refuerzos, herrajes, trazas | Las 40 opciones del sistema en la primera pantalla |
| P5 | **Nada es arbitrario.** | Cada color, radio, espacio y tamaño sale de un token con un rol | `margin: 13px`, `#3b82f6`, `border-radius: 12px` |
| P6 | **Hablar como el taller.** | Hoja, marco, junquillo, montante, travesaño, termopanel, manilla | `SASH`, `GLAZING_BEAD`, "ítem", "elemento", "objeto" |
| P7 | **Una acción principal por región.** | Un solo botón primario visible por panel; el resto, secundarios | Tres botones teal compitiendo en la misma franja |
| P8 | **El sistema trabaja.** | Prellenar, derivar, sugerir con causa, aplicar en lote con diff | Preguntar lo que ya se sabe; pedir confirmar lo obvio |
| P9 | **La inmutabilidad se ve.** | Revisión emitida con sello, huella y "Crear revisión B" | Editar un documento emitido "porque se puede" |
| P10 | **El estado es explícito.** | Etiqueta + tono + ícono + causa ("Bloqueada · falta perfil MARCO-70") | Puntos de color sin texto; "Error" a secas |
| P11 | **Proteger lo que sirve.** | Cota editable en el lugar, planta con carriles, "¿De dónde sale?", compañero IA con estados reales | Mantener un detalle singular que no ayuda al trabajo, o quitar uno que sí ayuda "para limpiar" |
| P12 | **Borrar antes que apilar.** | Cada rediseño elimina el componente viejo y su CSS muerto | Dejar la versión vieja escondida "por si acaso" |

---

## 3. Lenguaje visual

### 3.1 Color

**Un solo tema, claro.** No hay selector de tema ni tema oscuro de taller: el esfuerzo se concentra en una composición coherente con buen contraste. El taller y el terreno usan el mismo tema con controles más grandes (§3.7). No se fijan proporciones de color como objetivo: la mesa y el papel descansan, el turquesa marca acción y selección, el naranja es la marca y significa **"esto necesita a una persona"** (nunca un CTA ni un adorno).

**Rampas**

| Grafito | Hex | Rol |
|---|---|---|
| g-950 | `#161C1F` | Tinta, texto principal, trazo de perfil |
| g-900 | `#252D31` | Texto fuerte sobre tinte, cuerpo del compañero |
| g-700 | `#465158` | Texto secundario, texto de cotas, íconos |
| g-500 | `#727D82` | Texto atenuado (solo grande o metadato ≥ 12 px), guías |
| g-400 | `#9AA6A9` | Placeholder y deshabilitado |
| g-300 | `#CDD5D6` | Borde por defecto, reglas de tabla |
| g-200 | `#E0E6E5` | Línea fina, separadores |
| g-100 | `#EEF2F1` | Hover, relleno inset |
| g-50 | `#F5F7F6` | Fondo de la app (mesa de trabajo) |
| g-25 | `#FCFDFC` | Superficie de panel |
| paper | `#FFFFFF` | Hoja de dibujo y documento: **el papel es blanco, el metal es blanco roto** |

| Teal | Hex | Rol |
|---|---|---|
| teal-950 | `#042E2C` | Texto sobre tinte |
| teal-900 | `#064440` | Presionado sobre relleno |
| teal-800 | `#075F5A` | **Relleno primario** (botones), texto blanco 7.5:1 |
| teal-700 | `#0B7770` | **Texto interactivo** y enlaces sobre blanco (5.3:1) |
| teal-600 | `#0F8F85` | Bordes, anillo de foco, trazos del lienzo (3.9:1, nunca texto chico) |
| teal-500 | `#20A79A` | Acento del compañero IA y gráficos |
| teal-400 | `#48BCAF` | Gráficos |
| teal-200/100/50 | `#B0E4DC` / `#D4EFEA` / `#E6F4F2` | Rellenos suaves, selección, tinte del vidrio |

| Naranja (la marca) | Hex | Rol |
|---|---|---|
| orange-700 | `#A84418` | Texto sobre tinte naranja |
| orange-500 | `#E56A32` | Marca + aviso de "requiere persona" + manijas de manipulación en el lienzo |
| orange-100 | `#FBEBE2` | Superficie de aviso |

**Semánticos** (texto siempre con ≥ 4.5:1 sobre su fondo suave)

| Rol | Base | Suave | Tinta |
|---|---|---|---|
| Correcto / en tolerancia | `#1E7A4C` | `#E3F2EA` | `#13502F` |
| Atención / restricción blanda | `#B25E09` | `#FDF1E3` | `#7A3D05` |
| Bloqueo / inválido / destructivo | `#B3372F` | `#FBE9E7` | `#7E1F19` |
| Información | teal-700 | teal-50 | teal-900 |
| Requiere persona (fabricación) | orange-500 | orange-100 | orange-700 |

**Roles funcionales:** `bg-app` `#F4F6F7` (mesa fría muy clara) · `surface-panel` paper (paneles, rieles, barra superior) · `surface-card` g-100 (relleno inset, filas agrupadas) · `surface-sheet` paper · `surface-hover` `#EBF0F0` · `surface-active` `#DDE5E4` · `surface-selected` teal-50 · `border-subtle` g-200 (separadores) · `border-default` g-300 · `border-control` `#B4BFC1` (borde de campos y botones secundarios: los controles se distinguen de la estructura) · `border-focus` teal-600 · `text-primary` g-950 · `text-secondary` g-700 · `text-muted` g-500 · `interactive` teal-700 · `interactive-fill` teal-800 (hover teal-700, presionado teal-900) · `mark` orange-500. Pasa el test de contraste AA.

**Lienzo:** hoja `paper` sobre `bg-app` · grilla `#DCE4E2` · perfil g-950 de 1,5 px · cotas g-700 en Plex Mono 12 · vidrio `rgba(15,143,133,.07)` con trazo teal-600 · símbolo de apertura g-700 de 1,25 px (continuo = hacia el observador, discontinuo = alejándose) · selección localizada: contorno teal-600 1,5 px + 8 % de relleno solo sobre el miembro elegido, sin cubrir textura ni vidrio del resto · manija orange-500 con borde paper · ajuste (snap) verde discontinuo `6 4` · vista previa orange-500 discontinua `8 5` · inválido = color de bloqueo + achurado a 45° (legible sin color). Las cotas que se muestran son las relevantes para la selección; no se reiteran todas.

### 3.2 Tipografía: una superfamilia, dos voces

**IBM Plex Sans** habla de interfaz. **IBM Plex Mono** habla de medidas. Se autoalojan (WOFF2, subconjunto latino, `font-display: swap`). La familia actual se reemplaza.

| Rol | Especificación | Uso |
|---|---|---|
| Display | Sans SemiBold 32/38, −1 % | Títulos de documento y portada |
| Título L | Sans SemiBold 24/30, −0,5 % | Título de página |
| Subtítulo | Sans SemiBold 18/24 | Título de diálogo y de sección principal |
| Título M | Sans SemiBold 15/20 | Encabezado de panel y de grupo |
| Etiqueta | Sans Medium 13/18, **en frase** (sin mayúsculas forzadas) | Etiquetas de campo y encabezados de tabla |
| Cuerpo | Sans Regular 14/20 (`office`) · 15/22 (`document`) · 16/24 (`workshop`) | Texto de interfaz |
| Celda | Sans Regular 13/18 | Filas de tabla y texto secundario de lista |
| **Medida** | **Mono Regular 13/18 o tabulares de Sans** | Medidas técnicas (`2 400 × 1 800 mm`) y códigos en Mono; montos comerciales en Sans con `tabular-nums` |
| Micro | Sans Regular 12/16, g-700 | Metadatos, tolerancias, ayudas breves |

Reglas:
- **Mínimo absoluto: 12 px** en la interfaz (11 px solo en cotas del lienzo y papel impreso).
- La monoespaciada se reserva para medidas técnicas y códigos donde ayuda; un precio o una cantidad comercial no se escriben como texto de terminal.
- Pesos 400, 500 y 600 en la app. **El 700 vive solo en el papel** (total del documento). El producto nunca grita.
- `font-variant-numeric: tabular-nums` es obligatorio donde haya números que se alinean o cambian.
- Glifos reales: `×` (no `x`), `−` (no `-`) para negativos, `²`, `°`, `·`. Comillas «» o “” en el copy, nunca `"`.

### 3.3 Números y unidades (decisión cerrada)

| Magnitud | Formato | Ejemplo |
|---|---|---|
| **Medidas en mm** (cotas, cortes, vanos) | Enteros, **espacio fino** (U+2009) como separador de miles, unidad en minúscula al 85 % y en g-500 | `2 400 × 1 800 mm` |
| Medidas con precisión declarada | Coma decimal según la autoridad | `1 249,5 mm` |
| **CLP** | `$` + punto de miles, sin decimales | `$1.435.471` |
| USD / UF | 2 decimales / 4 decimales si la autoridad lo declara | `US$ 1.234,50` · `UF 38,4521` |
| Porcentaje | 1 decimal, coma | `32,5 %` |
| Área | 2 decimales | `2,16 m²` |
| Peso | 1 decimal | `38,4 kg` |
| Uw / Ug | 2 decimales | `1,40 W/m²K` |
| Fecha | `dd-mm-aaaa`, America/Santiago; relativa en listas con la absoluta en tooltip | `04-10-2026` · `hace 2 h` |

*Por qué el espacio fino en medidas:* es la convención ISO del dibujo técnico, no se confunde con la coma decimal y separa visualmente el mundo de la ingeniería (mm) del mundo comercial (pesos). Es una decisión deliberada y se aplica en todas partes: lienzo, tablas, documentos, etiquetas y la IA.

### 3.4 Espaciado, radios, elevación y capas

**Espaciado (base 4):** `2 · 4 · 6 · 8 · 12 · 16 · 24 · 32 · 48 · 64`. No hay excepciones de 10, 14 ni 18 px. Si un ajuste óptico es necesario, se anota en el PR.

| Contexto | Valor |
|---|---|
| Alto de control | 32 compacto (tablas, inspector) · **38 habitual** · **48 en `workshop`** y portal móvil |
| Fila de inspector | 34 |
| Relleno de panel | 16–24 |
| Rieles | Navegación 216 · riel contextual (inspector o asistente) 320–384 · franja de herramientas 48 |
| Barra superior | 56 |
| Densidad objetivo | El inspector muestra **≥ 7 campos sin scroll** a 768 px de alto |

**Radios por función:** `r-0` 0 (lienzo, papel, celdas, geometría) · `r-1` 6 px (campos, botones, chips) · `r-2` 8 px (paneles puntuales, menús, popovers, tarjetas de colección) · `r-3` 12 px (diálogos y paneles flotantes) · `r-pill` solo para puntos de estado y el compañero IA. No se redondea todo por decoración; no hay botones píldora como estilo universal.

**La esquina en inglete** (catetos de 8 px, arriba a la derecha) es opcional en la hoja del lienzo y en la marca; no se usa en controles ni se repite.

**Elevación por delineado, no por sombra:**

| Nivel | Mecánica | Uso |
|---|---|---|
| E0 | `bg-app` plano | Mesa de trabajo |
| E1 | 1 px `border-subtle`, sin sombra | Paneles, inspector, tarjetas (**por defecto**) |
| E2 | Borde + `0 1px 2px rgb(22 28 31/5%), 0 4px 12px rgb(22 28 31/8%)` | Menús, popovers, tooltips |
| E3 | Borde + `0 2px 6px rgb(22 28 31/6%), 0 12px 32px rgb(22 28 31/14%)` | Diálogos, paleta de comandos, fantasma de arrastre |
| Hoja | paper + 1 px `border-default` + `0 1px 3px rgb(22 28 31/7%)` | Solo lienzo y documento |

Una sola capa flotante a la vez. Prohibidos: sombras de color, desenfoque, `backdrop-filter`, resplandor interior.

**Capas (z-index):** base 0 · sticky 10 · riel 20 · popover 40 · drawer 50 · diálogo 60 · toast 70 · paleta de comandos 80. Prohibidos los literales fuera de esta escala.

### 3.5 Movimiento: ensamblar, no animar

| Token | Valor | Uso |
|---|---|---|
| `t-micro` | 90 ms | Hover |
| `t-state` | 160 ms | Presionar, alternar, seleccionar |
| `t-spatial` | 220 ms | Paneles, diálogos, pestañas |
| `t-max` | **280 ms** | Techo absoluto |
| `t-cycle` · `t-cycle-slow` | 900 ms · 2 400 ms | Solo ciclos de actividad continua (indicador de carga); nunca transiciones |

**Excepción del compañero (2026-10-18).** El techo de 280 ms gobierna transiciones de controles, paneles y popup. Los **ciclos expresivos del personaje** (reposo, pensamiento, trabajo, reconocimiento) pueden durar varios segundos con amplitud moderada, se interrumpen sin saltos, se pausan fuera de vista y respetan `prefers-reduced-motion` con una pose estática equivalente. La excepción no autoriza animar tablas, cifras ni el lienzo técnico.

Entradas `cubic-bezier(.2,0,.38,1)`; salidas `cubic-bezier(.4,.14,1,1)` en ≤ 120 ms. La respuesta a pulsar es inmediata; los paneles aparecen desde su origen y se pueden interrumpir. Zoom, paneo y arrastre del lienzo van unidos al gesto (1:1). Una cifra no se anima mientras se escribe; un precio actualizado se sustituye y se señala una vez. Un lote aplicado resalta una vez los objetos afectados. `prefers-reduced-motion` desactiva todo lo no esencial. Prohibidos: rebote, transiciones con blur, degradados animados y *shimmer*.

**Carga:** la composición se mantiene estable. Una espera breve deshabilita solo la acción en curso con un estado local («Calculando precio»). Una lista reserva filas estáticas. Una tarea larga (IA, importación, PDF) muestra pasos y páginas reales cuando se conocen; sin avance medible, actividad indeterminada **sin porcentaje inventado**. El cargador de cota deja de ser marca obligatoria.

### 3.6 Iconografía: gramática de fenestración

- **Una sola familia genérica** (`ui/Icon`): monolínea de 1,75 px en grilla de 24 px, puntas y uniones redondeadas, tamaños 16/20/24. Metáforas comunes reconocibles (biblioteca para catálogo, carpeta para proyectos, tijera para corte); no se inventa una metáfora nueva para una acción común. Las acciones decisivas («Orden de corte», «Emitir cotización») llevan texto. El estado activo se distingue de hover y foco por fondo y color, no por un cambio mínimo de trazo.
- La familia de aperturas usa la convención de dibujo real: la línea parte de las esquinas del lado de las bisagras y el vértice apunta a la manilla; continuo = hacia el observador, discontinuo = alejándose; abatimiento desde abajo; oscilobatiente = ambos símbolos; corredera = flecha paralela al carril; fijo = silencio (sin símbolo). **Es la misma gramática en ícono, lienzo, documento y 3D.** El usuario la aprende una vez.
- Vocabulario propio: montante, travesaño, acople, junquillo, sección de perfil, cota, lista de corte, tronzadora, manilla, bisagra, soldadura. Los herrajes se dibujan seccionados, no como siluetas.
- Prohibidos: íconos rellenos tipo blob, emoji, perspectiva y degradados.

### 3.7 Densidades

`data-density` en el contenedor raíz de cada superficie. Un único tema claro en todas:

| Densidad | Superficies | Base | Control |
|---|---|---|---|
| `office` | Proyectos, editor, catálogos, taller de oficina, ajustes, analítica | 14 px | 32–38 |
| `workshop` | Estación de operario, kiosko de taller, app de instalador | 16 px | **≥ 48** |
| `document` | Portal del cliente, vistas imprimibles, PDF | 15 px | 44 (portal) |

### 3.8 Retícula y puntos de quiebre

Diseño a **1440 × 900**. Debe funcionar sin scroll horizontal a 1280 × 800 y 1024 × 768. Las superficies `workshop` y `document` funcionan a 390 × 844. Bajo 1280, los rieles laterales se pliegan a íconos y pasan a un *drawer*; el lienzo nunca baja del 55 % del ancho.

---

## 4. Voz y microcopy

- **Español de Chile, profesional y directo.** La interfaz interna **tutea** con verbos en imperativo ("Emitir cotización", "Completar peso"). Los documentos y el portal del cliente tratan de **usted**.
- **Fórmula de un error:** qué pasó + por qué + qué hacer. *"No se puede emitir: la posición 4 no tiene vidrio. Elige un vidrio en la posición 4."* Con un botón que lleva exactamente ahí.
- **Fórmula de una confirmación:** pregunta de ficha técnica + consecuencia. *"¿Aplicar termopanel 5-12-5 a 3 posiciones? El total sube $84.300."*
- **Prohibido:** signos de exclamación, emoji, "¡Genial!", "¡Ups!", "Algo salió mal", palabras en inglés en la UI, MAYÚSCULAS para enfatizar, "Por favor" repetido, jerga de marketing, "ítem" o "elemento" donde existe la palabra del taller.
- **Estados vacíos:** dicen por qué está vacío y ofrecen **una** acción. *"Este proyecto aún no tiene posiciones. Agrega la primera ventana o importa una planilla de vanos."*
- **Números en el texto:** siempre con su formato (§3.3) y su fuente si son calculados.

**Glosario canónico (usar · no usar)**

| Usar | No usar |
|---|---|
| Ventana · Puerta · Conjunto (posición en listas profesionales) | Ítem, línea, producto, elemento |
| Hoja · Marco · Junquillo · Montante · Travesaño · Inversor · Umbral | SASH, FRAME, GLAZING_BEAD, poste, mainel |
| Termopanel (DVH) · Laminado · Templado | Doble vidrio, IGU |
| Abatible · Oscilobatiente · Proyectante · Corredera · Fijo | Batiente (salvo que el catálogo lo use), tilt-turn |
| Vano · Medida de fabricación · Holgura | Hueco, tamaño |
| Cotización · Revisión · Emitir | Presupuesto (salvo preferencia del cliente), versión, publicar |
| Orden de trabajo (OT) · Estación · Lote | Job, tarea, ticket |
| Sin dato | N/A, null, —, 0 |

---

## 5. Superficies: anatomía obligatoria

### 5.1 Shell
Navegación lateral de 216 px con **cuatro áreas habituales**: Proyectos · Clientes · Catálogos · Taller, y **Empresa** como acceso inferior. Cada rol ve las áreas que puede leer (la API sigue autorizando). Barra superior de 56 px: migas con el **nombre** de la obra (el código va en detalle), búsqueda/paleta (`Ctrl+K`), avisos y, **solo cuando la organización tiene derecho a IA**, el botón «Asistente» con el compañero, que abre el popup global. El plan manual no monta botón, presencia ni sondeo de IA. El logo vuelve a Proyectos. Analítica se abre desde Empresa; el historial del asistente vive en su popup (y en lectura desde la cuenta tras pasar a manual), no en otra aplicación. Las direcciones antiguas redirigen al contexto equivalente.

### 5.2 Proyectos (inicio)
La entrada habitual del dueño y del estimador: «Nueva cotización», trabajos para retomar y, si no hay ningún sistema utilizable, «Importar catálogo». Debajo, pocas decisiones agrupadas por obra (cotizaciones por vencer, aprobaciones, bloqueos), cada una con un verbo. No es un mural de indicadores ni una consola de incidencias. El taller empieza en sus órdenes, el operario en su estación y el instalador en su agenda.

### 5.3 Proyecto
Cabecera compacta: nombre, cliente, estado comercial y **una** acción principal, con el selector textual **Mesa de obra · Estudio** (preferencia por usuario y organización; Mesa por defecto; `?view=mesa|estudio&position=<id>`). Cuatro destinos: **Ventanas · Cotización · Materiales y corte · Actividad**. En **Mesa**, la colección de ventanas es el contenido principal, con dibujo real, ambiente/nombre, medidas, cantidad, acabado y precio, en galería o tabla (formatos locales de la colección, no las vistas). Selección múltiple con alcance visible, cambios en lote y diff antes de aplicar. En **Estudio**, franja de posiciones plegable, dibujo predominante e inspector manual de la misma sesión de edición. Cambiar de vista no guarda, no recalcula y conserva selección, borrador y deshacer.

### 5.4 Editor (canvas-first)
El dibujo ocupa dos tercios o más del área de trabajo, con **islas flotantes**: herramientas frecuentes agrupadas (seleccionar, dividir, apertura, medidas, deshacer/rehacer, 2D/3D), zoom abajo a la izquierda, precio y estado de cálculo en una línea. Un único inspector contextual a la derecha (288–320 px; drawer a 1024 px), dedicado a la selección, que **cambia según el objeto elegido**, con lo más usado primero y "Avanzado" plegado. El asistente **no** comparte ni desplaza este riel: abrir el popup no cambia columnas ni ancho del lienzo. Cotas encadenadas editables en el lugar. Vista en planta con carriles para correderas. "Qué falta" como lista accionable, no como banners. Atajos de teclado según el estudio de interacción (`V`, `H`, `F`, `Shift+1`, `Ctrl+K`, etc.).

### 5.5 Tablas
Reglas finas, **sin cebra**, encabezado fijo con etiqueta en frase, números alineados a la derecha con cifras tabulares (Mono solo en medidas y códigos), orden y filtro, selección con barra de acciones en lote, virtualización sobre 200 filas, estados vacío/carga/error.

### 5.6 Formularios
Etiqueta arriba, ayuda breve debajo, error en español debajo del campo, unidad como sufijo. `noValidate` siempre. Un formulario largo se divide por secciones con títulos, nunca en un muro. Lo que se puede derivar no se pide.

### 5.7 Los cinco estados (obligatorios en toda superficie)
**Vacío** (por qué + una acción) · **Cargando** (reserva con la forma real, sin shimmer; progreso real o actividad indeterminada sin porcentaje en tareas largas) · **Error** (fórmula del §4 + "Detalles técnicos" plegable + reintentar) · **Sin permiso** (qué rol lo puede hacer y a quién pedírselo) · **Bloqueado** (qué falta, quién lo resuelve, botón al lugar exacto).

### 5.8 Documentos (DOC-01 y siguientes)
Cada familia documental tiene composiciones realmente distintas: **tres cotizaciones comerciales, dos pedidos de compra y tres órdenes de corte**. La cotización es una propuesta editorial con la marca de la empresa (white-label), dibujo, alcance y total claros; numeración humana configurable (Cotización N.º 1 por defecto, prefijo e inicio por empresa) con la revisión separada. La aceptación/firma es opcional y depende de la política del negocio o de una acción explícita. La huella técnica no ocupa el cuerpo comercial: permanece en el registro auditable y en los documentos de taller (OT, corte, etiquetas), donde el **cajetín** conserva proyecto · documento · número · revisión · fecha · página · huella. Cada ventana es una ficha con elevación (vista declarada, §3.6) y especificación. El original estructurado se edita en borrador; tras emitir se revisa. Sin cebra. Carta por defecto.

### 5.9 Portal del cliente
Una página que vende con autoridad: portada con la obra, resumen de lo que compra en lenguaje simple, posiciones con dibujo y opción de ver en 3D, alternativas comparables, condiciones claras, **una** acción (Aprobar) y el estado honesto del enlace (vigente, reemplazado, vencido, revocado). Funciona perfecto en 390 px.

### 5.10 Taller y obra (`workshop`)
**Una pieza, una pantalla.** Código grande (≥ 32 px Mono), qué hacer, medida, destino, siguiente. Botones de ≥ 44 px (idealmente 56). Escaneo de etiqueta como entrada principal. Funciona con guantes y a 2 m. Confirmaciones táctiles inequívocas, sin gestos ocultos.

### 5.11 Asistente y compañero
**Popup global opcional** (solo planes con IA): una instancia por sesión y organización, cerrada al iniciar sesión, no modal (sin scrim ni trampa de foco), movible, redimensionable, minimizable y ampliable; 420 × 600 px inicial, mínimo 340 × 420, siempre dentro del viewport. Cerrar o minimizar **no** cancela el trabajo; «Detener» es otra acción. Cabecera: Asistente, **Chat/Trabajo**, historial, minimizar, ampliar, cerrar. Chat responde y prepara sin mutar; Trabajo ejecuta con herramientas de dominio. Autonomías **Solo proponer · Con aprobación · Omitir todo**, selladas por tarea; Omitir todo ejecuta lo reversible autorizado sin aprobaciones intermedias y entrega un recibo final. El hilo sigue a la persona; cada encargo sella su destino al enviarse y navegar no lo redirige. Adjuntos (documentos, imágenes, planillas, texto) con vista previa, estado y citas al origen. Un encargo solo es «Completado» cuando el servidor comprueba sus postcondiciones; si no, «Parcial»/«Esperando datos». Emitir, enviar, publicar, comprar/pagar o liberar conserva el clic humano.

El **compañero** reproduce con alta fidelidad la gramática del personaje animado de Grok Bot: cuerpo redondo limpio de un color, dos ojos negativos que se cierran, estiran e inclinan, sin placa facial, brillo ni órbita. Sus gestos derivan del estado real del trabajo (reposo, cola, pensamiento, trabajo, espera, revisión, éxito, fallo/cancelado, no disponible); no acreditan progreso, no repiten el éxito al recargar ni llaman al modelo para animarse. El nombre sigue siendo «Asistente» de DEKOPEN.

---

## 6. Patrones de interacción transversales

- **Paleta de comandos** (`Ctrl+K`): navegar, crear, ejecutar operaciones del registro tipado (las mismas que usa la IA) y buscar entidades por código.
- **Deshacer siempre:** toda edición en el editor y en lote es deshacible (`Ctrl+Z`) hasta guardar; las acciones consecuentes piden confirmación explícita.
- **Vista previa antes de aplicar:** cambios manuales en lote, importaciones y emisiones muestran el diff (qué cambia, cuánto cambia el precio) antes del clic. En el copiloto, *Solo proponer* y *Con aprobación* muestran el diff antes de aplicar; *Omitir todo* aplica lo reversible ya delegado y muestra el diff en el recibo final, con deshacer seguro. Los efectos externos piden siempre clic humano.
- **"¿De dónde sale?"**: cualquier número calculado abre una traza breve (fórmula, entradas, autoridad del catálogo, versión del motor).
- **Foco visible** de 2 px teal-600 con 1 px de separación en todo elemento interactivo; orden de tabulación lógico; todo es operable por teclado.
- **Accesibilidad:** AA, objetivos ≥ 24 px en `office` y ≥ 44 px en `workshop`, `aria-label` en todo botón de ícono, sin información transmitida solo por color.

---

## 7. Momentos propios (con propósito)

Son lo que hace que DEKOPEN no se parezca a nada más **porque ayudan al trabajo**. No se exige una decoración por pantalla: se exige que cada momento tenga propósito y esté bien resuelto. Si un encargo toca una superficie que tiene uno, debe preservarlo o mejorarlo; si deja de servir, se registra por qué se retira.

| # | Momento | Dónde | Por qué importa |
|---|---|---|---|
| F1 | **La esquina en inglete** (opcional) | Hoja del lienzo, marca | La hoja está cortada como el marco que cotiza |
| F2 | **La huella en el cajetín** | Documentos de taller emitidos, etiquetas, OT y registro auditable | La autoridad congelada se verifica sin ensuciar la propuesta comercial |
| F3 | **Progreso honesto** | Importación, IA, PDF y cálculos largos | Se ven pasos y páginas reales; nunca un porcentaje inventado |
| F4 | **La cota editable en el lugar** | Editor, vista de proyecto | Se cambia la medida donde se lee |
| F5 | **La franja de planta con carriles** | Editor y documento de correderas | Las correderas se entienden por fin |
| F6 | **"¿De dónde sale?"** | Todo número calculado | "Confío en los números" deja de ser una promesa |
| F7 | **Naranja = requiere persona** | Lienzo, OT, documentos | Un color con un único significado |
| F8 | **El compañero conectado a trabajos reales** | Barra superior, panel del asistente, resultados | La IA tiene presencia y honestidad |
| F9 | **Una pieza, una pantalla** | Estación de taller | El operario no lee: mira y actúa |
| F10 | **La sección de perfil en la marca** | Marca, favicon, etiquetas | `DEK⧈PEN`: la O es el producto (dirección B del estudio de identidad) |
| F11 | **El sello de revisión** | Cotizaciones emitidas, portal | Lo emitido no se toca; se revisa |

---

## 8. Subir el techo: lo que la competencia no hace

Cada superficie debe tener **al menos una** capacidad que vaya más allá de lo evidente. Siempre respaldada por el motor, nunca de adorno.

| Superficie | Idea que sube el techo |
|---|---|
| Editor | Escribir "partir en tres, centro fijo" en la paleta y ver la propuesta dibujada antes de aplicar; las cotas responden como en Shapr3D |
| Proyecto | Cambio global con diff: "todo el 2º piso a termopanel Low-E" → lista de posiciones afectadas + Δ de precio + Δ de Uw antes de aplicar |
| Precios | Cascada viva del costo al precio con banda de margen; mover el margen muestra el efecto en la utilidad de la obra, no solo en el total |
| Cotización | Checklist "Qué falta para emitir" que se cumple sola a medida que se completa; vista previa real del PDF antes de emitir |
| Portal | El cliente compara alternativas lado a lado (A: PVC blanco / B: foliado nogal) con el dibujo y el precio de cada una, y aprueba la que elige |
| Producción | Plan de corte que muestra cada barra con sus piezas y el destino del retazo; la estación dice qué cortar a continuación |
| Compras | "Comprar lo que falta" calcula contra stock y retazos, agrupa por proveedor y deja la orden lista para enviar con un clic |
| Instalación | El instalador ve en el celular la posición, su ubicación en la obra, qué llevar y cierra con foto y firma |
| Analítica | Margen real vs. cotizado por obra, con la causa de la diferencia (merma, remake, horas) |
| IA | Un pedido en lenguaje natural produce un plan de operaciones tipadas, una simulación con el motor y un diff aplicable; si falta un dato, pregunta con opciones |

---

## 9. El pase editorial (terminado ≠ bueno)

### 9.1 Definición

- **Terminado:** compila, los tests pasan, la pantalla existe.
- **Bueno:** un usuario real completa el flujo más rápido que con su herramienta actual, sin dudar de un número, sin encontrar un estado roto y sin un solo detalle arbitrario.

**Ningún PR se entrega en "terminado".** Antes de entregar, el autor hace el pase editorial y lo documenta en el PR.

### 9.2 Cómo se hace

1. **Recorre el flujo completo** de la superficie con datos realistas, como la persona del §1.2 (no solo la pantalla tocada: de dónde viene el usuario y adónde va después).
2. **Para cada elemento visible pregunta:** ¿justifica su existencia? ¿Si lo quito, algo empeora? Si la respuesta es no, **se quita**.
3. **Pasa la rúbrica** (§9.3) en 1440, 1280 y 1024 y, si aplica, en 390. Todo ítem que falle se corrige antes de entregar.
4. **Tres veces mejor:** identifica las 3 cosas más débiles que quedan y mejóralas. Repite una vez más.
5. **Documenta** en el PR la tabla de la rúbrica con PASA/FALLA, capturas de antes y después, lo que se quitó y por qué, y el momento de firma y la idea del §8 que la superficie implementa.

### 9.3 Rúbrica (todo debe pasar)

| # | Revisión | Falla si… |
|---|---|---|
| R1 | Números en Mono tabular, con unidad y formato del §3.3 | Dígitos proporcionales, `x` por `×`, sin unidad, `.00` sobrantes |
| R2 | Radios por función (6 controles · 8 contenedores · 12 diálogos · 0 papel) desde tokens | Radios literales, píldoras como botón universal, todo redondeado |
| R3 | Jerarquía por borde, peso y espacio; ≤ 1 superficie flotante | Sombras grandes o de color, tarjetas sobre tarjetas, brillo |
| R4 | Naranja solo como marca o "requiere persona" | Naranja en CTA, insignias decorativas |
| R5 | Teal como único croma del cromo | Colores aleatorios por módulo |
| R6 | Vocabulario del taller y voz del §4 | Enums, inglés, "ítem", exclamaciones, emoji |
| R7 | Densidad elegida por tarea: lectura cómoda (cuerpo 14) y tablas compactas donde sirven | Páginas de relleno, o todo leído como tabla técnica en 11–12 px |
| R8 | Estados explícitos con texto y causa; los 5 estados existen | Puntos de color sin texto, estados faltantes |
| R9 | El lienzo/documento es papel sobre mesa | Lienzo y cromo del mismo gris |
| R10 | Selección = contorno + tinte + manijas | Brillo al pasar el mouse, tarjetas que se elevan |
| R11 | Íconos de la familia única `ui/Icon`, simbología de apertura correcta, texto en acciones decisivas | Íconos mixtos, metáforas inventadas, símbolo de apertura erróneo |
| R12 | Foco visible en todo; operable por teclado | Sin foco o anillo azul del navegador |
| R13 | Movimiento ≤ 280 ms, interrumpible y con origen coherente; reduce-motion respetado | Rebote, fade-up escalonado, shimmer, cifras que bailan |
| R14 | Una acción principal por región | Varios primarios compitiendo |
| R15 | Cada número calculado tiene fuente; lo desconocido dice "Sin dato" | Ceros falsos, valores inventados |
| R16 | **Cero degradados, cero blur, cero brillo, cero morado IA** | Cualquiera = falla automática |
| R17 | Sin scroll horizontal y nada cortado en los anchos exigidos | Desbordes, textos truncados sin tooltip |
| R18 | Nada muerto: sin botones sin efecto, sin código viejo paralelo | Botones decorativos, componentes duplicados |
| R19 | Los momentos propios (§7) que aplican están resueltos con propósito | Lo útil se quitó "por limpieza" o se añadió decoración sin propósito |
| R20 | La idea del §8 funciona de verdad, con el motor | Una maqueta que no hace nada |

### 9.4 Señales de "AI slop" (eliminar en el acto)

- Tarjetas idénticas en grilla para contenido que no es una colección.
- KPI decorativos sin decisión asociada.
- Copy genérico ("Gestiona tus proyectos de forma fácil y rápida").
- Íconos puestos "para rellenar" junto a cada título.
- Espaciados distintos entre secciones equivalentes.
- Dos componentes que hacen lo mismo con estilos distintos.
- Ilustraciones genéricas de personas o de nubes.
- Textos de relleno, lorem ipsum, "Próximamente".
- Un modal para algo que cabe en el inspector.
- Explicaciones que repiten lo que la interfaz ya muestra.

---

## 10. Cómo se codifica (para que no dependa de la memoria de nadie)

| Estándar | Mecanismo (P01, salvo que se indique otro) |
|---|---|
| Colores, tipos, espacios, radios, sombras, capas, movimiento | Tokens en `tokens.css`; test que falla con `var()` sin definir |
| Contraste AA | Test que calcula cada par texto/fondo del tema |
| Hex inline, `border-radius` > 4 px, `box-shadow` fuera de tokens, `linear-gradient`/`radial-gradient`, `backdrop-filter`, `font-weight: 700` en la app, `transition` > 280 ms, `z-index` literal, `font-size` < 11 px, `.toFixed(` para mostrar, `pattern=` | Guardas con trinquete en `scripts/check_guards.py` (`make lint`) |
| Enums visibles | Test de exhaustividad de `domainLabels` contra el cliente generado |
| Formatos de número | Formateadores únicos con tests (`<Dims>`, `<Money>`, …) |
| UUID, hex, enums, inglés, exclamaciones, emoji, "MOCK", desbordes, fuente < 11 px, objetivos < 44 px en `workshop`, varios primarios por región, sombras/radios/degradados computados fuera de norma | Detectores de `ux:capture` (P00 + P01) sobre la app en vivo |
| Rúbrica del §9.3 | Plantilla de PR (`.github/pull_request_template.md`) con la tabla obligatoria |
| Muestrario | `/dev/ui` con todas las primitivas en las tres densidades |

---

## 11. Decisiones por defecto (el dueño puede cambiarlas después)

Los encargos **no se detienen** por estas decisiones: usan el valor por defecto, lo hacen **configurable en Ajustes** y lo registran en `docs/decisions/valores-por-defecto.md`.

| Decisión | Valor por defecto | Dónde se cambia |
|---|---|---|
| Papel de los documentos | **Carta** | Ajustes › Documentos |
| Anticipo | 50 % al aprobar, saldo contra entrega | Ajustes › Condiciones comerciales |
| Validez de la cotización | 15 días corridos | Ajustes › Condiciones comerciales |
| Garantía | Texto plantilla editable, sin plazo inventado: "[completar plazo]" visible solo en Ajustes, nunca impreso vacío | Ajustes › Condiciones comerciales |
| Plazo de entrega | Calculado desde la carga de producción si existe; si no, campo obligatorio por cotización | Cotización |
| Banda de margen | Objetivo 35 %, mínimo 25 %; bajo el mínimo requiere aprobación del dueño | Ajustes › Precios |
| IVA | 19 %, precios netos en la app y total con IVA en el documento | Ajustes › Impuestos |
| Pie "Generado con DEKOPEN" | **Oculto** en documentos del cliente (white-label); visible solo en el portal, discreto | Ajustes › Documentos |
| Nombre del asistente | "Asistente" (DEKOPEN) con el compañero de ojos negativos. **No se usa "STARWIN"** ni se afirma entrenamiento propio | Ajustes › Marca |
| Vista de obra | **Mesa de obra**; Estudio elegible por usuario y organización | Selector en la cabecera de la obra |
| Autonomía del copiloto | Con aprobación (preferencia del hilo; se sella por tarea) | Popup del asistente |
| Numeración de cotizaciones | Cotización N.º 1, correlativa por empresa; prefijo e inicio editables | Empresa › Documentos |
| Aceptación/firma en la cotización | Desactivada; se activa por política del negocio o con «Solicitar aceptación» | Empresa › Documentos |
| Tema | Claro único (sin selector) | — |
| Marca de la app | Dirección B del estudio de identidad (`DEK⧈PEN`) | P25 |
| Moneda | CLP; USD y UF opcionales | Ajustes › Moneda |
| Catálogo | Fabricantes y series reales con fuente; el DEMO (precios de semilla fija) vive en «Laboratorio» y conserva su marca en obras antiguas | Catálogos |

---

## 12. Referencias y qué tomar de cada una

| Referencia | Tomar | No tomar |
|---|---|---|
| Linear | Paleta de comandos, atajos, densidad, velocidad percibida | Su estética morada |
| tldraw / Excalidraw | Islas flotantes, panel de estilo, menú de zoom, minimapa | El trazo a mano alzada |
| Shapr3D | Cotas editables en el lugar | — |
| Moxisys | Lienzo grande, cotas encadenadas, franja en planta con carriles | Su cromo recargado |
| Orgadata / LogiKal (Musterangebot) | Ficha por posición con vista declarada, vidrio con composición y U, accesorios como sublíneas | La densidad tipográfica de los 90 |
| Windowmaker Web | Cambios globales, cotización interactiva con 3D | — |
| FeneCAM / Stolcad | Corte en secuencia, destino del retazo, etiquetas | — |
| PandaDoc / Qwilr | La propuesta web que vende | Plantillas de marketing genéricas |
| Manuales técnicos Schüco / Reynaers | La autoridad visual: líneas finas, secciones, números | Su maquetación impresa en pantalla |
| Dieter Rams / Otl Aicher | "Menos, pero mejor"; la identidad extraída del producto | La nostalgia |
