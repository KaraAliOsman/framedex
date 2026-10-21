# Patrones de interfaz y diseño de interacción para DEKOPEN (configurador, presupuestos, catálogo, taller, portal cliente, copiloto IA)

> Fecha de investigación: 2026-10-21. Notas de investigación (no informe final).
> Convención: **Hallazgos citados** = hecho verificado con URL consultada en esta sesión. **Inferencias** = juicio de diseño propio, no verificado. **Vacíos** = lo que no se pudo confirmar.
> Advertencia de método: búsquedas web limitadas (~16 llamadas). Los fabricantes de software de fenestración publican muy poca documentación visual abierta. Casi todos los detalles concretos de sus pantallas (paneles, barras, símbolos) que no aparecen abajo con URL **no se verificaron**. No los tomes como hechos.

---

## 1. ¿Cómo organizan sus editores y listas las herramientas líderes de fenestración (Logikal, KLAES, A+W, PrefSuite, Windowmaker, WindoorCraft, NuveraPRO)? ¿Qué está anticuado o confunde?

### Conclusión
Los líderes del sector siguen siendo, sobre todo, aplicaciones de escritorio Windows con modelo de cinta/menús (*ribbon*) y módulos separados: entrada de elementos, CAD 2D, 3D, presupuesto y producción. Su "modernización" de 2024-2026 consiste en recuperar la cinta, permitir personalizar menús, añadir vistas múltiples del presupuesto, portales web o CPQ y "hubs" de IA. No consiste en rediseñar la jerarquía de la interfaz. Eso deja libre el hueco de un editor web con lienzo e inspector al estilo Figma.

### Hallazgos citados
- **Logikal (Orgadata, ahora bajo la marca Forterro)**: el sitio de Orgadata aparece con el banner "Orgadata is now Forterro". Su módulo base incluye "element input" (entrada de elementos) con generación automática de cortes. Además hay un módulo aparte, "CAD-Suite 2D", descrito como un programa de dibujo completo para la industria de ventanas, puertas y muro cortina, y un módulo para AutoCAD que expone funciones de LogiKal dentro de AutoCAD. — [Orgadata module overview](https://www.orgadata.com/en/product/module-overview)
- Logikal anuncia una "interfaz 3D bidireccional y multifuncional" (noticia de 2019). Una página de webinars muestra una captura con vista 3D de una fachada de ventanas, lo que sugiere que el 3D forma parte del espacio de trabajo normal. El resultado de búsqueda no detalla sus funciones. — [Orgadata help/news](https://help.orgadata.com/en/news/page/24/); [Logikal events/webinars](https://www.logikal-software.com/en-in/services/events-webinars)
- Hay cobertura en español del lanzamiento de LogiKal en una feria (Interempresas). — [Interempresas: LogiKal, el nuevo software de construcción de ventanas de Orgadata](https://www.interempresas.net/Cerramientos_y_ventanas/161537-LogiKal-el-nuevo-software-de-construccion-de-ventanas-de-Orgadata.html)
- **KLAES (también dentro de Forterro)**: según su ficha de expositor en Fensterbau Frontale, su oferta actual incluye "Assembly connect", "KLAES AI Hub", "Measure connect" y "Digital production control". No encontré ninguna nota sobre una interfaz nueva de KLAES en 2026. — [Frontale: Klaes GmbH + Co. KG](https://www.frontale.de/en/exhibitors/klaes-gmbh-co-kg-2474807); [Forterro KLAES](https://www.forterro.com/en/windows-and-doors/klaes)
- KLAES expone en IWF Atlanta (25-28 de agosto de 2026, stand A10040). — [IWF Atlanta exhibitor](https://iwfatlanta.com/attend-iwf/exhibitor/108733-klaes-gmbh-co-kg/)
- **Cyncly V6 Advantage (software de ventanas, antes Soft Tech V6)**: entrada de blog del 26/04/2025 titulada "Modern UI in V6 Advantage". Novedades: **vuelve la cinta (ribbon)** con los comandos clave "donde los usuarios esperan"; el usuario puede **ocultar o mostrar elementos de menú** y crear **menús personalizados** para tareas repetitivas; hay **varias vistas de presupuesto** para cambiar de configuración "sin perder el sitio" y **vistas dinámicas** para presupuestos grandes; se mejoraron el filtrado y la búsqueda por palabra clave; el estilo visual es más limpio y está alineado con el sistema de diseño de Cyncly. El pie de una captura menciona un dibujo de ventana detallado, con medidas precisas y listas de componentes. — [Cyncly blog](https://cyncly.com/fr/blog/modern-ui-in-v6-advantage-smart-design-for-smarter-work)
- **Preference (PrefSuite / PrefWeb / ePref)**: PrefWeb se describe como CPQ web para gestionar una marca de ventanas y puertas. Permite crear y confirmar presupuestos, enviarlos a fábrica, seguir el avance y facturar. — [Frontale: PrefWeb CPQ](https://www.frontale.de/en/exhibitors/preference-sl-2473474/prefweb-cpq-online-configurator-2297852). ePref se presenta como herramienta web llave en mano para puertas, ventanas, escaparates y muro cortina, con **vistas 3D, secciones, detalle de esquinas y realidad virtual**. — [Interempresas: ePref](https://www.interempresas.net/Construccion/509727-ePref-software-llave-en-mano-para-puertas-ventanas-escaparates-y-muro-cortina.html). PrefSuite, según un folleto en español, cubre planificación de proyectos, control de producción, seguimiento de pedidos e inventario. — [Folleto Preference (PDF)](https://images.nuernbergmesse.de/files/c6043174-d1d4-57ce-6732-30c0aa91a298.pdf)
- **Windowmaker**: según su folleto, el configurador está alojado en Microsoft Azure y se vende por suscripción. Admite formas anguladas, arcos, *bay/bow*, georgianas y emplomadas; incluye biblioteca de diseños y de vidrios, y muestra y actualiza el precio al instante. Es "una sola solución para todos los materiales". — [Folleto Windowmaker (PDF)](https://images.nuernbergmesse.de/files/b6244aea-d4fd-e0b9-f91e-fcf761f87f5c.pdf). Un resumen de terceros lo describe como diseño de producto basado en reglas y menciona Windowmaker Web y Windowmaker Measure, una app móvil de toma de medidas. — [yespress: Windowmaker Software](https://yespress.io/windowmaker-software.md)
- No hay estudio específico de NN/g sobre configuradores. Un artículo académico preliminar (UNamur) revisó **50 configuradores de venta** y concluyó que con frecuencia se apartan de las pautas HCI estándar. — [UNamur research portal](https://researchportal.unamur.be/fr/publications/do-product-configurators-comply-with-hci-guidelines-a-preliminary)

### Inferencias (juicio de diseño)
- **Patrón dominante del sector**: espacio de trabajo modular por departamentos (presupuesto, CAD, producción), cinta de comandos, mucha jerga técnica en la interfaz y listas tipo hoja de cálculo. Que Cyncly haya **vuelto** a la cinta en 2025 indica que su base de usuarios premia la memoria muscular por encima de la reinvención. DEKOPEN no debería romper esos modelos mentales (posición > orden de comandos > nombres) aunque se aleje del estilo visual.
- **Lo anticuado o confuso, por inferencia sobre el patrón general**: (a) el 3D y el CAD como "módulos" aparte en lugar de vistas del mismo objeto; (b) la personalización de menús como solución al desorden, en vez de jerarquía por frecuencia de uso; (c) vistas de presupuesto como ventanas o pestañas sueltas; (d) la IA como "hub" separado, no incrustada en el contexto.
- **Oportunidad**: la propuesta de DEKOPEN puede ser "un objeto, muchas vistas": misma ventana en 2D acotada, en 3D, como lista de cortes, en precio y en documento, sincronizada en tiempo real. Lo de "tiempo real" se apoya en el precio instantáneo de Windowmaker, ya citado.
- ePref y Windowmaker muestran que el 3D y el precio instantáneo ya son lo mínimo exigible en el segmento web. No diferencian.

### Vacíos
- No obtuve descripciones verificables y concretas de **A+W (Cantor/iQuote)**, **WindoorCraft** ni **NuveraPRO**: ninguna búsqueda devolvió fuentes útiles en esta sesión. Tampoco de la disposición exacta de paneles, galerías de tipologías, convenciones de acotado o símbolos de apertura en ninguno de los productos. Para cerrar este vacío hay que revisar vídeos oficiales de YouTube (canales de Orgadata/Forterro, KLAES, A+W, Preference) o hacer demos y capturas reales.
- No se verificó que exista un producto llamado "PrefWise"; el buscador lo trató como posible error tipográfico.
- No hay datos publicados de usabilidad ni de quejas de usuarios, por ejemplo reseñas de Capterra con citas concretas, para ninguno de estos productos.

---

## 2. Mejores patrones de herramientas profesionales vecinas (Figma/Framer, SketchUp/Shapr3D/Onshape, Forma, configuradores de carpintería, dashboards Linear/Notion/Stripe, MES de tableta, PandaDoc/Proposify, copilotos IA)

### Conclusión
Los productos punteros convergen en tres ideas. (1) El **lienzo es protagonista** y la interfaz cede el paso: la navegación se atenúa y los paneles son redimensionables y colapsables. (2) En el **inspector, lo importante va primero**, sin romper la memoria muscular. (3) La **IA va incrustada en el contexto**, con controles explícitos y no solo un chat. En taller, los únicos números publicados son reglas prácticas de proveedores: objetivos táctiles grandes (~20 mm con guante), sin escritura, y color solo para lo anómalo.

### Hallazgos citados

**Lienzo + inspector (Figma UI3)**
- Figma UI3 (blog del 26/06/2024): **barra de herramientas fina en la parte inferior del lienzo**, que libera la parte superior y unifica el cambio entre productos Figma. Paneles **redimensionables y colapsables**, con opción de ocultar toda la interfaz. — [Figma: Behind our redesign UI3](https://www.figma.com/blog/behind-our-redesign-ui3/)
- En el panel de propiedades de UI3, los controles de componente (variantes, instancias) van **por encima** de atributos como color y tamaño. Ancho, alto y Auto Layout se fusionan en un solo bloque situado **debajo de x/y**, porque poner ancho y alto por encima de x/y "disrupted muscle memory too much" en las pruebas. — [Figma blog](https://www.figma.com/blog/behind-our-redesign-ui3/)
- Las **etiquetas de propiedades son opcionales**: se activan para aprender o se ocultan para una vista centrada en iconos. UI3 añade fondos a los campos, bordes a los desplegables y unos 200 iconos redibujados. — [Figma blog](https://www.figma.com/blog/behind-our-redesign-ui3/)
- Figma probó una interfaz "super-minimal" que aparecía solo al pasar el ratón, y barras laterales que aparecían y desaparecían. Las descartó porque hacían el entorno **demasiado inestable**. — [Figma blog](https://www.figma.com/blog/behind-our-redesign-ui3/)
- Con los comentarios de usuarios, Figma **volvió a anclar** los paneles de navegación y propiedades: los paneles flotantes molestaban, sobre todo en pantallas pequeñas. Solo se mantienen flotantes en "Minimize UI". — [Figma: Our approach to designing UI3](https://www.figma.com/blog/our-approach-to-designing-ui3/); [Centro de ayuda Figma: Navigating UI3](https://help.figma.com/hc/articles/23954856027159)
- Las funciones de **Figma AI** están en el menú *Actions*, para tener acceso rápido "sin interrumpir el trabajo en curso". Lema del rediseño: "simplifying Figma, without simplifying what you can do with Figma". — [Figma blog](https://www.figma.com/blog/behind-our-redesign-ui3/)
- Crítica de la comunidad: los controles contextuales que pasaron de la barra superior al panel derecho quedan a veces escondidos tras un menú "…" por falta de ancho. — [Foro Figma: UI3 feedback](https://forum.figma.com/t/ui3-feedback/77610/14)

**Densidad e información (Linear)**
- "Behind the latest design refresh" de Linear (12/03/2026, Charlie Aufmann y Maxime Heckel) propone dos principios: **"Don't compete for attention you haven't earned"** y **"Structure should be felt not seen"**. El reto era conservar la densidad de información sin que la interfaz agobiara. — [Linear: Behind the latest design refresh](https://linear.app/now/behind-the-latest-design-refresh)
- Decisiones concretas de Linear: **barra lateral "unos puntos" más tenue**, iconos más pequeños, texto inactivo apagado y más relleno vertical; pestañas más compactas que no ocupan todo el ancho y que, las primeras, se convierten en píldoras solo con icono; **menos iconos**, más pequeños y sin fondos de color por equipo; **menos separadores**, con bordes redondeados y menos contraste; la paleta pasa de un gris frío azulado a un **gris más cálido y menos saturado**, con la advertencia de que demasiada calidez se ve "muddy". El generador de temas sigue: color base, acento y contraste. — [Linear](https://linear.app/now/behind-the-latest-design-refresh)
- Proceso de Linear: barra de desarrollo con *feature flags* para comparar la interfaz vieja y la nueva con un clic; herramienta interna de color con controles de tono, croma y luminosidad por token, exportados como JSON a Figma. — [Linear](https://linear.app/now/behind-the-latest-design-refresh)
- El rediseño anterior de Linear (20/03/2024) redefinió las capas base para mejorar jerarquía, equilibrio y densidad, y ajustó barra lateral, pestañas, cabeceras y paneles para reducir ruido visual. — [Linear changelog 2024-03-20](https://linear.app/changelog/2024-03-20-new-linear-ui)

**Tablas densas**
- NN/g tiene un vídeo, "Designing Tables for Desktop Apps with Lots of Data", con 3 pautas. No pude leer su contenido. — [NN/g video](https://www.nngroup.com/videos/designing-tables-desktop-apps/)
- Pautas de un sistema de diseño público (California Courts): texto alineado a la izquierda, **números alineados a la derecha** para compararlos y cabeceras centradas. — [CA Courts design system: Table](https://webservices.courts.ca.gov/design-system/component-library/table)
- Fuentes secundarias recomiendan **fijar la cabecera** al desplazarse en vertical y **la primera columna** (identificador) al desplazarse en horizontal. En entornos empresariales, la tabla sigue siendo la forma más eficiente de comparar filas y recorrer datos en el orden que elija el usuario. — [uxdesign.cc: Designing better tables for enterprise applications](https://uxdesign.cc/designing-better-tables-for-enterprise-applications-f9ef545e9fbd); [Halo Lab: guide to data tables](https://www.halo-lab.com/blog/the-ultimate-guide-to-designing-data-tables/)

**Configuradores (guías de proveedores, no NN/g)**
- Recomendaciones habituales: agrupar opciones relacionadas, usar **divulgación progresiva** (mostrar lo complejo solo cuando hace falta) y usar controles y disposiciones conocidos. — [The Digital Bunch: UX/UI de configuradores 3D](https://www.thedigitalbunch.com/blog/how-to-uxui-design-a-3d-configurator-that-makes-sense); [DriveWorks: tips UX configurador](https://www.driveworks.co.uk/blog/our-top-tips-for-optimizing-configurator-user-experience/)
- **Venta guiada y dependencias**: guiar las decisiones en vez de listar opciones, y usar lógica condicional que oculta o bloquea combinaciones incompatibles. — [Cloudflight: best product configurators](https://www.cloudflight.io/en/blog/best-product-configurators-ecommerce/); [Kickflip: features of product configurators](https://gokickflip.com/blog/what-are-major-features-of-product-configurator)

**Pantallas de taller / MES en tableta**
- Un artículo académico de Tampere (APMS 2015) da pautas genéricas de interfaces "human-friendly" para planta, orientadas a la entrada de datos fiable y a la productividad. — [Jarvenpaa, APMS 2015 (PDF)](https://trepo.tuni.fi/bitstream/10024/128842/1/APMS2015_Jarvenpaa_FinalPaper.pdf)
- Reglas prácticas de proveedores MES, que ellos mismos presentan como "rules of thumb" y no como norma: **~20 mm por botón para uso con guante**, probado con los guantes reales; botones grandes y separados; **sin menús pequeños ni escritura**; mostrar solo lo que el operario necesita en marcha normal, con el detalle a un toque; **color solo para estados anómalos**, siempre con forma o posición además del color; nunca depender solo del sonido; texto de ~15 mm para leer a 3 m (regla distancia/200). — [iFactory: Automotive MES operator dashboard](https://ifactoryapp.com/blog/automotive-mes-operator-dashboard); [iFactory: food plant operator dashboard](https://ifactoryapp.com/article/food-plant-operator-dashboard-design)
- El mismo proveedor atribuye a NN/g un mínimo táctil de ~1 cm. **No pude verificar esa atribución.** — [iFactory](https://ifactoryapp.com/article/food-plant-operator-dashboard-design)

**Copilotos IA dentro de software profesional**
- NN/g, "Prompt Controls in GenAI Chatbots: 4 Main Uses and Best Practices" (Feifei Liu, 02/08/2024). Los controles de prompt (botones, tooltips, interruptores, tarjetas, menús alrededor del campo de texto) sirven para: (1) **descubrir funciones**; (2) **enseñar e inspirar**, con iniciadores de conversación y galerías de prompts editables; (3) **acotar** el alcance o el formato de salida (por ejemplo, el *Focus* de Perplexity o elegir tipo de gráfico); (4) **facilitar seguimientos**: fila de acciones de ChatGPT (editar, copiar, regenerar), "Shorter / More casual" de Gemini, preguntas relacionadas. — [NN/g: Prompt controls](https://www.nngroup.com/articles/prompt-controls-genai/)
- Pautas de NN/g para esos controles: iconos estándar **con etiqueta o tooltip**; **nombres claros**, no marcas vagas como "Think Carefully"; **agrupar por función**; respetar las convenciones de interacción (no ocultar mensajes de error ni cambiar el comportamiento de una pulsación larga). — [NN/g](https://www.nngroup.com/articles/prompt-controls-genai/)
- Patrones de catálogos secundarios: "prompt scaffolding" con entradas sugeridas para copilotos; controles de **interrumpir y aprobar/rechazar** en sistemas agénticos; "Inline Action" (pedir algo a la IA sobre lo que ya se ve en pantalla, según Shape of AI). — [UX Planet: 7 key design patterns for AI interfaces](https://uxplanet.org/7-key-design-patterns-for-ai-interfaces-893ab96988f6); [EL Passion: generative UI patterns (16/08/2026)](https://www.elpassion.com/blog/generative-ui-patterns)
- Microsoft Dynamics 365 Business Central documenta un "prompt mode" para diseñar funciones Copilot dentro de un ERP. — [Microsoft Learn: Copilot design prompt mode](https://learn.microsoft.com/en-gb/dynamics365/business-central/dev-itpro/developer/copilot-design-prompt-mode)
- KLAES ya comercializa un "AI Hub", lo que confirma que la IA ha entrado en el sector de la fenestración. — [Frontale: Klaes](https://www.frontale.de/en/exhibitors/klaes-gmbh-co-kg-2474807)

### Inferencias (juicio de diseño) — traducción a las 6 superficies de DEKOPEN
1. **Editor de ventana/puerta (2D/3D)**
   - Disposición tipo UI3: lienzo central con el alzado 2D acotado como vista primaria; inspector derecho anclado y redimensionable; árbol o estructura a la izquierda (marco → hojas → travesaños → vidrios), colapsable; barra de herramientas fina abajo (seleccionar, dividir vertical u horizontal, añadir hoja, tipo de apertura, cota, 2D/3D).
   - El 3D como **pestaña o vista dividida del mismo modelo**, nunca como módulo aparte.
   - Orden del inspector por frecuencia y por consecuencia: tipología/sistema → medidas generales → apertura → vidrio → color/acabado → herrajes → avanzado (colapsado). Igual que Figma, no reordenar lo que el usuario ya domina.
   - **Manipulación directa**: arrastrar un travesaño cambia una cota, y escribir una cota mueve el travesaño. Las cotas son editables en el propio lienzo, al estilo de las cotas de boceto de SketchUp/Onshape (patrón conocido, no verificado aquí). El motor recalcula y valida, y la interfaz nunca calcula por su cuenta (invariante de DEKOPEN).
   - Etiquetas del inspector **siempre visibles por defecto** para el público de DEKOPEN, que no es experto en informática. A diferencia de Figma, el modo "solo iconos" es opcional.
2. **Espacio de proyecto/presupuesto**
   - Lista densa al estilo Linear: barra lateral tenue, pocos separadores, números alineados a la derecha en tipografía tabular, cabecera y primera columna fijas.
   - Vista dividida: a la izquierda las líneas del presupuesto con miniatura del alzado; a la derecha el detalle o editor. Responde a lo que Cyncly resolvió con "varias vistas sin perder el sitio".
3. **Gestión de catálogo**: tabla con edición en línea, filtros guardados, historial inmutable visible (invariante de DEKOPEN) y diffs de precio antes de publicar.
4. **Taller (tableta)**: una tarea por pantalla, botones de ≥20 mm separados, cero escritura (escaneo o selección), color solo para lo anómalo y siempre doblado con icono o forma, texto grande legible a distancia, modo alto contraste.
5. **Portal de propuesta del cliente**: documento visual con alzados, opciones comparables y aceptación con clic humano explícito (invariante de DEKOPEN). Los patrones de PandaDoc/Proposify no se verificaron en esta sesión (ver Vacíos).
6. **Copiloto IA**:
   - Incrustado en el contexto, como el *Actions* de Figma o la "Inline Action": "explica este error de validación", "propón alternativa más barata", "resume este presupuesto".
   - Controles de prompt agrupados y con etiqueta (pauta NN/g).
   - **Nunca produce números**: cualquier cifra la calcula el motor, y la IA solo propone cambios de parámetros que el usuario aprueba o rechaza (patrón aprobar/rechazar).

### Vacíos
- No verifiqué en esta sesión fuentes primarias de **SketchUp, Shapr3D, Onshape, Autodesk Forma, Framer, Cabinet Vision, Mozaik, planificadores de IKEA, configuradores de coches o muebles, Notion, Stripe, PandaDoc, Proposify, Adobe Firefly/Acrobat AI, Notion AI ni Cursor**. Todo lo que se diga de ellos en el informe final debe marcarse como conocimiento general no verificado o investigarse aparte.
- No encontré cifras de NN/g ni normas ISO verificadas sobre objetivos táctiles para uso con guante. Solo hay reglas de proveedor.
- No hay datos cuantitativos (tasas de error, tiempo por presupuesto) que comparen interfaz de cinta frente a lienzo e inspector en fenestración.

---

## 3. Decisiones de sistema de diseño: tipografía, densidad, color para datos técnicos, iconos, estados vacíos, onboarding, teclado y paleta de comandos, divulgación progresiva, errores y validación de restricciones de ingeniería

### Conclusión
Lo verificable apunta a: **neutros cálidos y poco saturados**, tokens en un espacio de color perceptual (tono, croma, luminosidad), **menos iconos y menos bordes**, etiquetas opcionales pero disponibles, cifras alineadas a la derecha, y color reservado para lo anómalo y nunca como única señal. Sobre tipografía, paleta de comandos y estados vacíos no encontré fuentes primarias verificadas en esta sesión.

### Hallazgos citados
- **Color**: Linear pasó a un gris cálido y menos saturado y gestiona sus tokens con tono, croma y luminosidad. Su generador de temas expone base, acento y contraste. — [Linear](https://linear.app/now/behind-the-latest-design-refresh)
- **Iconos**: Linear reduce el uso y el tamaño de los iconos y quita los fondos de color. Figma redibujó unos 200 iconos y señala que diseñarlos es "a balancing act between ensuring visual consistency and conveying extremely complex ideas". — [Linear](https://linear.app/now/behind-the-latest-design-refresh); [Figma](https://www.figma.com/blog/behind-our-redesign-ui3/)
- **Bordes y estructura**: menos separadores y más suaves ("structure should be felt not seen"). — [Linear](https://linear.app/now/behind-the-latest-design-refresh). Figma, en cambio, **añadió** fondos a los campos y bordes a los desplegables para que los controles se reconozcan. — [Figma](https://www.figma.com/blog/behind-our-redesign-ui3/)
- **Etiquetas frente a iconos**: Figma permite activar las etiquetas de propiedades "para aprender qué hace cada control". — [Figma](https://www.figma.com/blog/behind-our-redesign-ui3/). NN/g pide iconos estándar con etiqueta o tooltip y nombres de función claros. — [NN/g](https://www.nngroup.com/articles/prompt-controls-genai/)
- **Números en tablas**: alinear a la derecha para comparar. — [CA Courts design system](https://webservices.courts.ca.gov/design-system/component-library/table)
- **Color para estados**: solo para lo anómalo, doblado con forma o posición. — [iFactory](https://ifactoryapp.com/blog/automotive-mes-operator-dashboard)
- **Divulgación progresiva y dependencias**: revelar lo complejo bajo demanda y ocultar o bloquear lo incompatible. — [The Digital Bunch](https://www.thedigitalbunch.com/blog/how-to-uxui-design-a-3d-configurator-that-makes-sense); [Kickflip](https://gokickflip.com/blog/what-are-major-features-of-product-configurator)
- **Errores**: NN/g advierte de que ocultar mensajes de error o romper convenciones aumenta la confusión y la complejidad percibida. — [NN/g](https://www.nngroup.com/articles/prompt-controls-genai/)
- **Teclado y densidad (fuente secundaria)**: un análisis de 2026 de la "estética Linear" trata tokens, densidad y UX centrada en el teclado. No lo leí entero y no es fuente primaria. — [buildmvpfast: The Linear aesthetic decoded](https://www.buildmvpfast.com/blog/linear-aesthetic-tokens-density-keyboard-first-ux-2026)
- **Estabilidad**: Figma descartó la interfaz que aparece y desaparece por ser "demasiado inestable". — [Figma](https://www.figma.com/blog/behind-our-redesign-ui3/)

### Inferencias (juicio de diseño)
- **Tipografía**: una sans de interfaz con **cifras tabulares** (`font-variant-numeric: tabular-nums`) en todas las cotas, precios y cantidades. Unidades siempre visibles ("1.250 mm", nunca "1250"), con separador de miles y decimales según la configuración regional (es-MX/es-AR/es-CO usan convenciones distintas: hay que parametrizar por organización). Una monoespaciada solo para códigos de perfil y referencias.
- **Densidad**: dos niveles. "Cómoda" por defecto para el usuario no experto y "Compacta" para quien presupuesta a diario. Linear demuestra que la densidad se sostiene si se quita ruido (bordes, iconos), no si se encoge el texto.
- **Color de datos técnicos**: neutros para la geometría; un acento único para la selección; semánticos reservados (rojo = viola una restricción del motor y bloquea; ámbar = advertencia que no bloquea; azul = información). La apertura y el sentido de giro se dibujan con línea o símbolo, no con color. El vidrio se representa con un tinte muy suave.
- **Validación de restricciones de ingeniería**:
  - El error se ancla **en el lugar exacto** (la cota o el componente en el lienzo, y el campo del inspector).
  - Lleva tres partes: qué límite se rompió, el valor actual frente al permitido (las cifras salen del motor) y una acción correctiva ("ajustar a 1.400 mm máx.", "cambiar a perfil reforzado").
  - Además, un panel "Problemas" con recuento, como los IDE, que se pueda recorrer con el teclado.
  - Nunca un modal genérico.
  - El copiloto puede **explicar** el error, pero no **inventar** el límite.
- **Paleta de comandos (⌘K / Ctrl+K)**: búsqueda unificada de clientes, proyectos, perfiles y acciones ("nueva ventana corredera 2 hojas"). Los atajos aparecen en los tooltips y menús, para que el usuario los aprenda sin un manual.
- **Estados vacíos**: cada lista vacía ofrece una acción primaria y una plantilla del catálogo `DEMO_60` (activo propio del repo) para empezar con datos de ejemplo.
- **Onboarding**: aprender haciendo con un proyecto de ejemplo precargado, mejor que tours de globos.

### Vacíos
- No verifiqué guías de **Apple HIG**, **Stripe** (sistema de diseño o dashboard) ni artículos de NN/g sobre paleta de comandos, estados vacíos u onboarding. Cifras como el mínimo de 44 pt de Apple son conocimiento general, no comprobado en esta sesión.
- No encontré fuentes sobre las convenciones de **símbolos de apertura** (triángulo con vértice hacia las bisagras, etc.) en las normas DIN/EN ni en los programas del sector. Hay que confirmarlas con normativa o con los PRD del repo.

---

## 4. Principios y antipatrones de software "simple pero profundo" para fabricantes pequeños no expertos, incluida la UX en español para LatAm

### Conclusión
El principio más respaldado es el de Figma: **"simplificar la herramienta sin simplificar lo que se puede hacer con ella"**. Se apoya en no competir por la atención (Linear), mantener la estabilidad espacial, proteger la memoria muscular y la divulgación progresiva. Sobre la UX específica en español para LatAm no encontré fuentes verificadas en esta sesión.

### Hallazgos citados
- "simplifying Figma, without simplifying what you can do with Figma" y "get as much signal as possible, then dial back as needed". — [Figma](https://www.figma.com/blog/behind-our-redesign-ui3/)
- "Don't compete for attention you haven't earned" / "Structure should be felt not seen". — [Linear](https://linear.app/now/behind-the-latest-design-refresh)
- Proteger la memoria muscular: Figma mantuvo x/y por encima de ancho y alto y restauró la cuadrícula de alineación de Auto Layout para no romper hábitos. — [Figma](https://www.figma.com/blog/behind-our-redesign-ui3/)
- Lo estable gana a lo mínimo: la interfaz que aparece y desaparece se descartó por inestable, y los paneles flotantes se volvieron a anclar tras las quejas. — [Figma](https://www.figma.com/blog/behind-our-redesign-ui3/); [Figma: Our approach](https://www.figma.com/blog/our-approach-to-designing-ui3/)
- El público del sector valora lo conocido: Cyncly recuperó la cinta y los comandos "donde los usuarios esperan". — [Cyncly](https://cyncly.com/fr/blog/modern-ui-in-v6-advantage-smart-design-for-smarter-work)
- Los configuradores suelen incumplir pautas HCI básicas (muestra de 50). — [UNamur](https://researchportal.unamur.be/fr/publications/do-product-configurators-comply-with-hci-guidelines-a-preliminary)
- En el taller: sin escritura, sin menús pequeños, y probar con las condiciones reales (guantes). — [iFactory](https://ifactoryapp.com/blog/automotive-mes-operator-dashboard)
- Los nombres de marca vagos en las funciones confunden: hay que nombrar por lo que hace. — [NN/g](https://www.nngroup.com/articles/prompt-controls-genai/)

### Inferencias (juicio de diseño)
**Principios propuestos para DEKOPEN**
1. **Un objeto, muchas vistas**: la ventana es la verdad, y alzado, 3D, cortes, precio y PDF son vistas sincronizadas.
2. **El motor manda, la interfaz traduce**: cada número visible procede del motor. La interfaz muestra de dónde sale (tooltip "calculado por el motor · regla X").
3. **Profundidad bajo demanda**: los valores por defecto sensatos del catálogo resuelven el 80 %, y lo avanzado se despliega en el lugar donde está, sin navegar a otra pantalla.
4. **Estabilidad espacial**: los paneles no saltan. Lo que cambia es el contenido, no la disposición.
5. **Lenguaje del oficio, no del software**: "hoja", "marco", "travesaño", "contravidrio", "herraje", "corte a 45°". Nada de "entidad", "nodo" ni "instancia".
6. **Cada error trae su arreglo**.
7. **Clic humano para lo irreversible**: emitir, enviar al cliente, cobrar (invariante del repo).

**Antipatrones a evitar**
- Módulos separados para el mismo objeto (CAD aparte, 3D aparte), como en el patrón Logikal/KLAES.
- Cintas con más de 40 comandos al mismo nivel. Menús personalizables como sustituto de una buena jerarquía.
- Modales encadenados para configurar. Asistentes lineales imposibles de saltar para el usuario experto.
- Iconos sin etiqueta. Jerga en inglés o en alemán traducida literalmente.
- Color como única señal. Rojo usado para decorar.
- Una IA que produce cifras o "hub" de IA separado del trabajo.
- Interfaz que aparece al pasar el ratón: inestable, y además no existe en tableta.

**Español para LatAm (juicio propio, sin fuente verificada)**
- Vocabulario regional variable: "ventana corrediza/corredera", "batiente/abatible", "vidrio/cristal", "perfil/perfilería", "herraje/herrajes", "mosquitero/mosquitera", "cotización/presupuesto". Se propone un **glosario por organización** o por país, con un término por defecto y sinónimos buscables en la paleta de comandos.
- Tuteo frente a ustedeo: elegir "tú" neutro en la interfaz y redactar los documentos al cliente en "usted".
- Formatos: separador decimal (coma frente a punto según el país), moneda local con código ISO visible en las propuestas, fechas dd/mm/aaaa.
- Los textos en español son ~20-30 % más largos que en inglés: los componentes deben tolerar etiquetas largas (la skill `break-ui` del repo sirve para probarlo). La cifra es conocimiento general, no verificado aquí.

### Vacíos
- No encontré estudios ni fuentes verificadas sobre UX de software B2B en español para LatAm, ni sobre el vocabulario técnico de carpintería de PVC y aluminio por país. Recomiendo validarlo con usuarios reales y con los PRD y el glosario del repo (`docs/PRD/`, `docs/design/CONSTITUCION.md`).
- No hay evidencia publicada sobre el nivel digital de los pequeños fabricantes latinoamericanos ni sobre su tolerancia a interfaces densas.
