# ERP industrial de ventanas: KLAES, A+W Cantor, FeneVision (FeneTech/Cyncly) y V6 Advantage (Soft Tech/Cyncly)

Notas de investigación, 21 de octubre de 2026. Alcance: cómo estas cuatro suites cubren una fábrica de ventanas de PVC y aluminio de punta a punta, y qué deja espacio a una SaaS web AI-first (DEKOPEN, Chile/LatAm).

Convenciones:
- Hecho verificado: lleva URL. Casi todo viene del propio fabricante (marketing, notas de prensa o contenido patrocinado). Lo indico cuando importa.
- Inferencia: va en la subsección "Inferencias" y no es un hecho.
- Fecha: el material anterior a 2026 lleva su fecha.
- Metodología: búsqueda y lectura web en una sola sesión, con unas 18 llamadas. No pude ver vídeos de YouTube ni manuales de Scribd/Yumpu (ver Gaps).

---

## 1. Módulos y flujo completo, de la cotización a la instalación (por suite)

### Takeaway
Las cuatro suites cubren la misma cadena: configurador/tipologías, maestro de sistemas, despiece/BOM dinámico, optimización de barras y vidrio, precios, documentos, planificación por capacidad, estaciones con código de barras, enlace a máquinas, compras/stock, despacho, instalación y postventa. Se diferencian por foco:
- KLAES: PVC/madera, ERP completo, fuerte en producción y montaje.
- A+W Cantor: ERP+CIM con portal de distribuidores (iQuote) y app móvil de planta.
- FeneVision: Norteamérica, vidrio + ventana, con OPTI, despacho y RMA muy desarrollados.
- V6 Advantage: configurador/estimación e ingeniería de BOM para fabricantes y redes de distribuidores, más que ERP de planta.

### Cited Findings

**KLAES (Alemania; desde 2026 dentro de Forterro)**
- Líneas de producto: Klaes premium (ERP integrado), Klaes professional (empresas con producción automatizada), Klaes vario (el precio escala con el volumen de pedidos), Klaes trade (comerciantes de ventanas) y Klaes 3D (invernaderos/jardines de invierno y fachadas) — [Klaes, preview FENSTERBAU FRONTALE 2026 (13-02-2026)](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- Módulos por área, según la misma fuente:
  - Planificación: capacidad (CAPA), gestión de materiales/inventario (MAWI), planificación de montaje, informes y CE-Generator (declaración CE).
  - Producción: e-prod, e-control, configuradores, DoorDesigner, CAM 2D y CAM 3D.
  - Web: webshop, webtrade, web business, web tracking y cloud trade.
  - Comunicación: Info Manager, CRM, DMS, gestión de tiempos y openTRANS (estándar de intercambio electrónico de documentos comerciales).
  - [Klaes FF2026](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- Novedades 2026 por etapa del flujo — [Klaes FF2026](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en):
  - **Medición (Measurement connect):** interfaz con apps de medición externas. El fabricante decide qué tipologías se pueden medir. Medidas, dirección, posición, fotos y notas vuelven solas al ERP, donde después se añaden persianas, DVH, etc.
  - **Compras (Klaes procure):** maestro central de artículos y proveedores. Detecta automáticamente los cambios de requerimiento para que se puedan rastrear. Incluye un centro de control de propuestas de pedido y pedidos con lógica de estados, filtros y aprobación estructurada de datos maestros.
  - **Webshop para distribuidores:** cupones limitados por tiempo o cantidad, descuentos por volumen por grupo de producto y control de qué tipos, variantes y grupos ve cada distribuidor.
  - **Producción:** Klaes e-control controla máquinas para elementos configurados individualmente, medidas especiales y series pequeñas, y envía los datos a máquinas o CAM. Klaes e-prod horizon da vista de producción, gestión de racks de entrega, ubicaciones de almacén y gestión de errores entre producción y logística.
  - **Montaje (Assembly connect / WinDo Flow):** une la planificación de montaje con una app móvil para instaladores en obra. Los datos llegan en tiempo real, la obra devuelve feedback y está disponible para todos los clientes.
  - **3D/CAD:** en los módulos "Plus", Klaes Alu plus genera vistas y cortes a partir del modelo 3D, sustituyendo el corte 2D clásico. Klaes 3D suma paquetes de datos 3D para fachadas de aluminio y madera-aluminio independientes del fabricante, una vista esquemática realista y control 3D con aristas de corte visibles (fachadas, pérgolas, portones).
- Klaes e-prod en madera: Klaes digitalizó la producción de un fabricante alemán de ventanas de madera y le suministró también hardware (PCs, pantallas, escáneres) como proveedor único. La nota recalca que la madera es más compleja que el PVC — [Interempresas](https://www.interempresas.net/Construccion/371608-Klaes-e-prod-la-digitalizacion-en-la-carpinteria-de-ventanas-de-madera.html)
- Productos destacados en la adquisición: ERP premium de gestión, e-prod para control de producción en tiempo real y optimización de planta, y software 3D especializado — [Glass Times](https://glasstimes.co.uk/news/forterro-acquires-software-specialist-klaes/) (resumen de búsqueda)

**A+W Cantor (A+W Software, Alemania; también A+W North America)**
- Cantor es un ERP para fabricantes de ventanas, puertas, persianas, portones y mosquiteros. Es modular: se empieza con lo necesario y se amplía. Cubre presupuestos, pedidos (con control de crédito), compras, materiales, producción, entrega, instalación, facturación y servicio, con archivo documental integrado ("casi sin papel"). Calcula las fechas clave desde la orden de compra hasta la instalación y actualiza los calendarios de cada departamento — [Window & Door, contenido patrocinado, 08-10-2025](https://www.windowanddoor.com/article/product-solution-aw-software)
- Bloques en la web oficial — [A+W Cantor](https://www.a-w.com/aw-cantor/):
  - ERP+CIM: ofertas y pedidos, compras y materiales, planificación de capacidad y fecha de entrega (incluido JIT), preparación del trabajo y control de producción con conexión a máquinas y puestos CIM.
  - Dealer Cloud: el fabricante da a sus distribuidores módulos para crear ofertas, pedidos, albaranes y facturas, más planificación de servicio e instalación y gestión de clientes del distribuidor.
  - iQuote: configurador web 24/7. El cálculo de precio y la validación constructiva son los mismos que en la entrada de pedidos, validados contra los datos maestros del fabricante, y el pedido entra a planificación sin recaptura.
  - Smart Companion: app móvil con escaneo de códigos de barras (continuo multi-ítem y modo lectura de estado), formularios dinámicos, reclamaciones con fotos enviadas a CIM, recepción de mercadería, traspasos e inventario, y solicitud de material escaneando en puntos de registro.
- Terminales CIM: el operario escanea códigos, sigue racks de herrajes y marcos y reporta en tiempo real. Smart Companion se integra con plataformas IoT — [Window & Door 2025](https://www.windowanddoor.com/article/product-solution-aw-software)
- iQuote integra configuradores de terceros, p. ej. Warema y ROMA (protección solar) — [Glass on Web, "A+W Cantor relies on smart partner networks"](https://www.glassonweb.com/news/aw-cantor-relies-smart-partner-networks) (resumen de búsqueda; fecha no confirmada)
- A+W Cantor 8.0 (anunciado el 07-09-2026, debut en GlassBuild America del 23 al 25-09-2026): une datos de planta con resultados financieros, mejora la gestión de inventario y las decisiones de proveedor, incorpora workflows embebidos y busca reducir la varianza. El anuncio no menciona IA ni cloud — [Glass on Web](https://www.glassonweb.com/news/aw-cantor-80-debuts-glassbuild-america-2026)
- En glasstec 2026 (20 al 23-10-2026, Hall 14, E59), A+W anuncia demos de logística, expedición, automatización e IA — [a-w.com](https://www.a-w.com/) (resumen de búsqueda)

**FeneVision (FeneTech, hoy marca de Cyncly)**
- Estructura: un producto CORE (ventas, fabricación, optimización) más módulos opcionales integrados. Existe también una versión LITE — [FeneTech, FeneVision ERP Modules](https://fenetech.com/?p=26030); [Cyncly capabilities](https://www.cyncly.com/en/products/fenevision/capabilities)
- Capacidades, todas según [Cyncly, FeneVision Capabilities](https://www.cyncly.com/en/products/fenevision/capabilities):
  - **Configuración y cotización:** configuración con visualización, precio automático y BOM dinámico; visualización interactiva para el cliente.
  - **Precios:** por pieza y opción, markup sobre costo, grillas de precio, matrices multi-eje, ajustes masivos; un solo libro de precios con descuentos por cliente; job costing que muestra el margen mientras avanza el trabajo.
  - **CAD:** FeneVision CAD Designer (perforaciones, recortes y cantos en vidrio, DXF multicapa). Módulos especiales: Shower (mamparas), Opening Designer y Bay & Bow Designer.
  - **BOM dinámico:** define costo, inventario y producción de productos mass-customized.
  - **Planificación:** reglas de secuenciación, lotes y rehechos; JIT y planificación por demanda; capacidad con lead times dinámicos, mantenimiento planificado, buffers y programación hacia adelante y atrás; ruteo de flujo, alertas de tareas fuera de orden y asignación de recursos.
  - **Planta:** seguimiento por código de barras en tiempo real; estaciones que muestran imagen del producto terminado y DXF; avisos automáticos de defectos comunes y reproceso automático de rechazos.
  - **Máquinas:** arquitectura abierta con interfaces a posicionadores lineales, soldadoras y CNC; reglas y códigos de ruteo por máquina programables en el BOM u opciones.
  - **OPTI (optimización):** vidrio e interlayer de PVC, formas estándar y no estándar, detección de formas DXF, nesting, etiquetas, gestión de almacén de vidrio e interfaz con mesas de corte. Optimización lineal de perfiles con bins y largos. OPTI-GLASS, OPTI-BREAK y OPTI-LOAD cubren corte, quiebre y carga, y OPTI existe también como software independiente — [búsqueda Cyncly/FeneTech](https://fenetech.com/?p=26030)
  - **Inventario:** binning desde la recepción hasta QA y despacho; punto de reorden, consumo diario y existencias; app FeneVision Mobile Inventory.
  - **Compras:** órdenes de compra dentro del flujo; EDI para enviar OCs y recibir recepciones.
  - **Despacho:** rutas estándar y secuencia de carga; rechazo de piezas dañadas antes de cargar; Delivery App con paradas, escaneo, fotos y firma.
  - **RMA:** devoluciones que agrupan reparaciones y rehechos en producción, con análisis de causa raíz.
  - **Portal (FeneVision WEB):** add-on protegido por contraseña para CORE o LITE, donde distribuidores, dealers y clientes crean estimaciones y pedidos y ven estado e historial con la misma configuración y precios del ERP. Importación EDI.
  - **Reporting:** dashboards de KPI configurables; integración base con Microsoft Business Central.
- El catálogo y los precios de FeneVision se integran en One Click Contractor (venta en domicilio, Norteamérica) — [Cyncly, 2024](https://www.cyncly.com/resources/news/fenetech-one-click-contractor)
- El módulo CRM funciona en navegador móvil, y el módulo RMA se enlaza con la app de reparto para recoger devoluciones — [Cyncly/FeneTech, resumen de búsqueda](https://cyncly.com/products/fenevision)

**V6 Advantage (Soft Tech, hoy Cyncly)**
- Lanzado el 05-03-2025 como "el software de configuración de ventanas y puertas más avanzado" de Cyncly, construido sobre Soft Tech V6. Sus objetivos son mejorar la estimación, fortalecer las redes de distribuidores y agilizar la fabricación. Incluye informes estándar y personalizados — [Cyncly, nota de prensa 2025](https://www.cyncly.com/resources/news/cyncly-v6-advantage)
- Testimonio de Kawneer: lo usa desde 1997 para BOM de ingeniería e informes de fabricación — [Compusoft Group](https://www.compusoftgroup.com/solutions/window-door-software/)
- X3D Visualizer (visualización 3D) recibió el premio "Best Digital Tool" de Window + Door — [Window & Door](https://www.windowanddoor.com/article/best-digital-tool-soft-tech-v6-advantage-x3d-visualizer); [Cyncly](https://www.cyncly.com/resources/news/v6-advantage-visualizer-award)

### Inferencias
- El flujo canónico que comparten las cuatro, y que DEKOPEN debe cubrir como mínimo, es: medición (app) → configurador con validación constructiva → BOM/despiece dinámico → precio (costo + markup/matrices) → documento → planificación por capacidad y fecha de entrega → optimización (barras, vidrio) → estaciones con escaneo → máquinas (CSV/CAM) → racks/despacho con app → montaje con app → RMA/postventa con fotos.
- Las reglas de despiece y refuerzos de PVC (refuerzo de acero según tamaño y color, descuentos por soldadura, etc.) no aparecen descritas en ninguna fuente pública que leí. Viven en los datos maestros que cargan los proveedores de sistemas o los consultores. Ahí está la barrera de implementación (ver sección 4).
- Klaes y A+W tratan el portal de distribuidores (webshop / iQuote / Dealer Cloud) como un producto aparte del ERP de escritorio. Es una costura que una SaaS web nativa no tendría.
- Por conocimiento previo, no verificado en esta sesión: Cyncly nació de la fusión de Compusoft y 2020 Spaces. FeneTech (EE. UU.) y Soft Tech (Nueva Zelanda) son adquisiciones de ese grupo, así que FeneVision y V6 conviven en la misma cartera, una más ERP de planta y la otra más configurador/estimación.

### Gaps
- No encontré documentación pública detallada del editor de tipologías ni del modelo de datos maestros (cómo se modelan sistemas, perfiles, refuerzos, herrajes, colores y reglas) en ninguna de las cuatro.
- No confirmé si V6 Advantage tiene planificación de planta, stock y despacho propios, o si eso se resuelve con FeneVision o integraciones.
- No encontré detalle público de la optimización de barras de Klaes ni de A+W (gestión de retales/offcuts). Solo FeneVision describe OPTI con algo de detalle.
- No verifiqué qué fabricantes de máquinas (sierras, soldadoras, centros de mecanizado) están conectados por nombre en cada suite.

---

## 2. UI/UX: pantallas, 3D, qué se siente moderno o anticuado

### Takeaway
Hay muy poca evidencia pública de UI. Las cuatro son aplicaciones de escritorio Windows con paradigma de ribbon/menús, y sus portales web son satélites. Los avances visibles en 2025-2026 son visualización 3D (X3D, Klaes 3D, Alu plus), apps móviles para planta, medición y montaje, y vistas personalizables. Ninguna fuente muestra una experiencia web-first coherente de punta a punta.

### Cited Findings
- A+W presenta Cantor como el primer paquete de construcción de ventanas basado en MS Windows con interfaz gráfica, y dice llevar unos 30 años con el equipo Cantor — [A+W timeline, "Cantor is launched"](https://www.a-w.com/timeline/cantor-is-launched/)
- V6 Advantage (2025): interfaz rediseñada y "por demanda popular, vuelve el ribbon"; menús que se pueden ocultar, menús personalizados con elementos propios, múltiples vistas de cotización para cambiar entre configuraciones sin perder el lugar, vistas dinámicas para cotizaciones grandes, filtro y búsqueda por palabra clave dentro de cotizaciones grandes. El blog incluye una captura del "product designer" con la ventana acotada y una lista de componentes — [Cyncly blog, Modern UI in V6 Advantage](https://www.cyncly.com/resources/blog/modern-ui-in-v6-advantage-smart-design-for-smarter-work)
- V6 Advantage funciona on-premises, en cloud o en transición entre ambos — [Cyncly 2025](https://www.cyncly.com/resources/news/cyncly-v6-advantage)
- Klaes 3D 2026: nueva vista esquemática "realista" en lugar de diagramas esquemáticos, y control 3D en el área de trabajo con aristas de corte visibles. En Alu plus, los planos de vista y corte salen del modelo 3D en lugar del corte 2D clásico — [Klaes FF2026](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- Klaes procure se presenta con "interfaz moderna" y un centro de control con estados y filtros — [Klaes FF2026](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- FeneVision: las estaciones de planta muestran imagen del producto terminado y DXF, y hay dashboards de KPI configurables — [Cyncly capabilities](https://www.cyncly.com/en/products/fenevision/capabilities)
- Formación FeneVision: "FeneVision University" con más de 80 vídeos por área (documento de soporte actualizado en abril de 2026) — [Cyncly support, Training Options](https://fenevision.support.cyncly.com/hc/en-us/articles/29268386351505-FeneVision-Training-Options)

### Inferencias
- Que en 2025 el "regreso del ribbon" se venda como mejora indica que la base instalada es de usuarios expertos de escritorio, reacios al cambio. Su UX está pensada para densidad y velocidad de un operador entrenado, no para un vendedor nuevo ni para el cliente final.
- Que haga falta un curriculum de más de 80 vídeos sugiere una curva de aprendizaje alta. DEKOPEN puede competir con descubribilidad en contexto (y asistencia IA) en lugar de cursos.
- Lo "moderno" en este segmento hoy es: 3D realista en el configurador, apps móviles nativas para escaneo, montaje y reparto, y portales de distribuidor con reglas de visibilidad. Lo "anticuado" es: escritorio Windows, menús profundos, CAD 2D, módulos separados por producto y reporting como "informes".

### Gaps
- No pude ver vídeos de YouTube (ni títulos ni timestamps verificados) ni manuales en Scribd/Yumpu/Issuu. La búsqueda no devolvió demos indexadas. Queda pendiente revisar los canales oficiales de Klaes, A+W y Cyncly y describir el lienzo del editor, los paneles de propiedades y las listas.
- No hay capturas públicas verificadas del editor de tipologías de Klaes, Cantor o FeneVision en lo que leí.

---

## 3. Plataforma, licenciamiento, tamaño objetivo y movimientos recientes (cloud, web, IA, analítica)

### Takeaway
2026 trae consolidación e IA:
- Forterro compró Klaes (abril de 2026) y lo suma a Logikal/Orgadata (aluminio), apostando por cloud, automatización con IA y analítica.
- Klaes lanzó un AI Hub sobre Microsoft 365.
- A+W muestra IA en glasstec 2026 y lanzó Cantor 8.0 centrado en finanzas de planta e inventario.
- Cyncly empuja V6 Advantage con modelo híbrido on-prem/cloud y FeneVision con hosting cloud y releases versionados por año.
- Ninguna publica precios.

### Cited Findings
- **Forterro–Klaes:** anuncio de abril de 2026. Klaes se mantiene como marca independiente dentro de la unidad Windows & Doors de Forterro. Logikal (antes Orgadata) cubre la configuración de aluminio. Sigue a las compras de Orgadata y BM Group en 2025. Los manufactureros "craft" ya son más del 25 % del grupo. Klaes tendrá acceso a las capacidades de IA de Forterro. Términos no divulgados; cierre sujeto a revisión regulatoria, previsto para el Q2 2026 — [Glass on Web, 23-04-2026](https://www.glassonweb.com/news/forterro-acquires-klaes); [Goodwin, abril de 2026](https://www.goodwinlaw.com/en/news-and-events/news/2026/04/announcements-otherindustries-goodwin-advises-forterro)
  - Conflicto de fechas: un resultado de búsqueda sitúa el anuncio de intención el 16-04-2026, mientras Glass on Web fecha la noticia el 23-04-2026. No verifiqué el cierre definitivo con fuente primaria.
- Foco declarado tras la compra: más inversión en plataformas cloud, automatización con IA y analítica avanzada — [GlassBalkan](https://glassbalkan.com/news/forterro-acquires-klaes-to-build-full-range-software-ecosystem-for-window-industry/); [Glass Times](https://glasstimes.co.uk/news/forterro-acquires-software-specialist-klaes/) (resúmenes de búsqueda)
- Klaes: fundada en 1983 en Bad Neuenahr-Ahrweiler, se declara con unos 7.600 clientes en más de 50 países (cifra autodeclarada) — [Glass Times](https://glasstimes.co.uk/news/forterro-acquires-software-specialist-klaes/); [Profiel](https://profiel-online.nl/en/software-automation/software-specialist-becomes-the-all-rounder-for-the-window-and-door-industry/) (resúmenes de búsqueda)
- **Klaes AI Hub (2026):** plataforma central para gestionar aplicaciones de IA. Conecta con el software Klaes, Teams, OneDrive y el correo de Microsoft 365. Ofrece chat con contexto de empresa (documentos, procedimientos, procesos), ayuda con email y citas, modelos de reglas y roles, resultados transparentes y mecanismos de seguridad y cumplimiento, y se extiende con workflows o apps. Se presenta como usable de inmediato. Klaes también ofrece servicios cloud de backup, terminal servers, clusters y telefonía — [Klaes FF2026](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- **Licenciamiento Klaes:** solo encontré que "Klaes vario" escala el precio con el volumen de pedidos. No hay cifras — [Klaes FF2026](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- **A+W:** Cantor 8.0 (septiembre de 2026) se orienta a finanzas e inventario. En glasstec 2026 muestra IA, logística y automatización — [Glass on Web](https://www.glassonweb.com/news/aw-cantor-80-debuts-glassbuild-america-2026); [a-w.com](https://www.a-w.com/)
- **Cyncly:** V6 Advantage se ofrece on-prem, cloud o híbrido, con portal de cliente (tickets, release notes), soporte de emergencia 24/7 y vídeos de formación. Cyncly declara más de 70.000 clientes en el grupo, no solo ventanas — [Cyncly 2025](https://www.cyncly.com/resources/news/cyncly-v6-advantage)
- **FeneVision:** release 2026.1 en marzo de 2026, después de la 18.7 de septiembre de 2025 (página actualizada el 27-04-2026). Ofrece Cloud Hosting dentro del "Customer Center", sin detalle público — [Cyncly support, Versions and Release Dates](https://fenevision.support.cyncly.com/hc/en-us/articles/45346229509009-FeneVision-Versions-and-Release-Dates) (resumen de búsqueda); [Cyncly FeneVision](https://cyncly.com:443/en/products/fenevision)
- Segmentos de FeneVision: proveedores de perfiles, fabricantes residenciales de ventanas y puertas, procesadores de vidrio plano, fabricantes comerciales y distribuidores de "architectural openings" — [Cyncly FeneVision](https://cyncly.com:443/en/products/fenevision)
- Cliente reciente: Press Glass (gran procesador europeo de vidrio) eligió FeneTech como socio de software a largo plazo (fecha no verificada en la lectura) — [US Glass Magazine](https://www.usglassmag.com/fenetech-is-the-new-software-partner-for-press-glass/); [WindoorExpert](https://www.windoorexpert.eu/suppliers--accessories/software/news,28022,w,press-glass-selected-software-specialist-fenetech-as-their-new-long-term-software-partner.html)

### Inferencias
- Tamaño objetivo: Klaes cubre desde comerciantes (trade) hasta plantas automatizadas (professional). A+W Cantor apunta a medianas y grandes con red de distribuidores. FeneVision apunta a medianas y grandes norteamericanas e incluso procesadores de vidrio industriales. V6 apunta a fabricantes con redes de distribuidores (p. ej. Kawneer). El fabricante chileno/LatAm típico, pequeño o mediano y con poca TI, queda mal servido por precio, idioma, implementación e infraestructura on-prem.
- La IA de los incumbentes en 2026 es horizontal (chat sobre documentos y Microsoft 365) o, por ahora, solo demo. No vi IA aplicada al núcleo técnico (configurar, despiezar, cotizar desde un plano o una foto). Ahí DEKOPEN puede diferenciarse, siempre que respete su invariante de que los números salen del motor y no del LLM.
- La consolidación (Forterro: Orgadata + Klaes; Cyncly: FeneTech + Soft Tech) suele traer migraciones, cambios de licenciamiento y clientes inquietos durante 2026-2027. Es una ventana comercial, aunque en LatAm la penetración de estas suites es probablemente baja (no verificado).

### Gaps
- No hay precios ni modelo de licencias públicos (por puesto, por módulo, por volumen) de ninguna de las cuatro. No los invento.
- No verifiqué la presencia de estas suites ni sus distribuidores en Chile/LatAm (Klaes tiene prensa en español en Interempresas, lo que sugiere presencia en España).
- No encontré release notes detalladas de FeneVision 2026.1 ni de Cantor 8.0.

---

## 4. Fortalezas, debilidades, dolor de implementación y quejas de usuarios

### Takeaway
Casi no hay reseñas independientes: G2, Software Advice y SoftwareFinder no tienen reseñas reales de estos productos. Las fortalezas que se pueden documentar son la profundidad funcional y décadas de base instalada. Las debilidades se infieren de señales indirectas: módulos que exigen implementación detallada, curva de aprendizaje, dependencia de datos maestros y arquitectura de escritorio con satélites web.

### Cited Findings
- Klaes en G2: 0 valoraciones y sin preguntas — [G2 Klaes](https://www.g2.com/products/klaes/discuss)
- Soft Tech V6 en Software Advice: sin reseñas — [Software Advice](https://www.softwareadvice.com/manufacturing/soft-tech-v6-profile/)
- FeneVision en SoftwareFinder: sin reseñas de usuarios. Sus pros y contras son editoriales: a favor, planificación y seguimiento de producción; en contra, documentación que no cubre todos los escenarios y lentitud ocasional bajo carga. Advierte que los módulos completos pueden exigir una implementación detallada — [SoftwareFinder FeneVision](https://softwarefinder.com/manufacturing-software/fenevision) (fuente secundaria de baja confiabilidad)
- Comparativa de un competidor (marketing, no independiente): WindoorERP puntúa a Soft Tech V6 con 62 % frente al 78 % propio — [WindoorERP compare](https://www.windoorerp.com/compare)
- Ranking genérico: WifiTalents da a V6 un 7,9/10 y lo etiqueta "enterprise" sin metodología clara — [WifiTalents](https://wifitalents.com/best/fenestration-software/) (baja confiabilidad)
- Fortaleza de longevidad: Kawneer usa V6 desde 1997 — [Compusoft](https://www.compusoftgroup.com/solutions/window-door-software/). Klaes existe desde 1983 — [Glass on Web](https://www.glassonweb.com/news/forterro-acquires-klaes). A+W lleva unos 30 años con Cantor — [A+W timeline](https://www.a-w.com/timeline/cantor-is-launched/)
- La implementación incluye hardware y consultoría: en un caso de madera, Klaes suministró PCs, pantallas y escáneres además del software — [Interempresas](https://www.interempresas.net/Construccion/371608-Klaes-e-prod-la-digitalizacion-en-la-carpinteria-de-ventanas-de-madera.html)
- Señal sobre optimización en talleres pequeños (fuente no especializada en estas suites): la optimización clásica casi no sirve para perfiles de ventana, y en talleres pequeños el esfuerzo de configurar optimizadores 1D a menudo supera el beneficio — [KI-Syndikat](https://www.ki-syndikat.de/usecases/handwerk/22-restholz-minimierung-tischlereibetrieb/)
- Que A+W destaque en 2025 la "validación contra datos maestros" en iQuote y Klaes la "aprobación estructurada de datos maestros de artículos" en 2026 confirma que la calidad del maestro es un punto crítico — [A+W Cantor](https://www.a-w.com/aw-cantor/); [Klaes FF2026](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)

### Inferencias
- Dolor de implementación probable: (1) carga y mantenimiento de datos maestros por sistema de perfil, que suele depender del proveedor de perfiles o de consultores; (2) parametrización de reglas de despiece y precio; (3) integración con máquinas por fabricante; (4) formación (más de 80 vídeos en FeneVision); (5) infraestructura on-prem o terminal server, que Klaes vende como servicio adicional.
- Que las cuatro tengan "portal web para distribuidores" como módulo aparte (iQuote, FeneVision WEB, Klaes webshop/webtrade, Dealer Cloud) indica que la experiencia de ventas externa y la del ERP no son la misma aplicación. Eso genera duplicación de reglas, sincronización y costes de licencia separados.
- Que no haya reseñas públicas no significa satisfacción: es un mercado B2B de nicho con pocos clientes muy grandes, y las quejas circulan en foros sectoriales o en LinkedIn, que no indexé.

### Gaps
- No encontré quejas concretas de usuarios en foros, LinkedIn ni ofertas de empleo (la búsqueda de empleos no devolvió resultados útiles). Queda pendiente buscar en LinkedIn Jobs "FeneVision administrator", "Klaes Stammdaten" o "A+W Cantor Anwendungsbetreuer" para medir la carga de personal dedicado.
- No hay datos de duración ni coste típico de implementación.

---

## 5. Table stakes y dónde puede ganar una SaaS web AI-first

### Takeaway
Para competir, DEKOPEN debe igualar un núcleo amplio: configurador con validación, BOM/despiece dinámico, precios multi-método, documentos, planificación por capacidad, optimización de barras y vidrio, estaciones con código de barras, compras/stock, despacho e instalación con app, RMA y portal de distribuidores. Puede ganar en experiencia web unificada, tiempo de implementación, datos maestros asistidos, IA en el núcleo (siempre auditada por el motor) y foco LatAm.

### Cited Findings (base de los table stakes)
- Configuración con visualización, precio automático y BOM dinámico — [FeneVision capabilities](https://www.cyncly.com/en/products/fenevision/capabilities)
- Precios: markup sobre costo, matrices multi-eje, ajustes masivos, descuentos por cliente y job costing con margen — [FeneVision capabilities](https://www.cyncly.com/en/products/fenevision/capabilities)
- Planificación de capacidad y fecha de entrega (JIT) — [A+W Cantor](https://www.a-w.com/aw-cantor/); CAPA en [Klaes](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- Optimización de vidrio y lineal, etiquetas — [FeneVision capabilities](https://www.cyncly.com/en/products/fenevision/capabilities)
- Estaciones con escaneo y racks — [Window & Door 2025 (A+W CIM)](https://www.windowanddoor.com/article/product-solution-aw-software); [Klaes e-prod horizon](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- Enlace a máquinas: soldadoras, CNC y posicionadores — [FeneVision](https://www.cyncly.com/en/products/fenevision/capabilities); e-control/CAM — [Klaes](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- Compras con propuestas y EDI — [Klaes procure](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en); [FeneVision](https://www.cyncly.com/en/products/fenevision/capabilities)
- Despacho con app (fotos, firma) — [FeneVision](https://www.cyncly.com/en/products/fenevision/capabilities)
- Montaje con app y feedback de obra — [Klaes Assembly connect](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- Medición en obra integrada — [Klaes Measurement connect](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- Portal de distribuidores con las mismas reglas y precios del ERP — [A+W iQuote](https://www.a-w.com/aw-cantor/); [FeneVision WEB](https://www.cyncly.com/en/products/fenevision/capabilities); [Klaes webshop](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- RMA/reclamaciones con fotos — [A+W Smart Companion](https://www.a-w.com/aw-cantor/); [FeneVision RMA](https://www.cyncly.com/en/products/fenevision/capabilities)
- Visualización 3D en la venta — [V6 X3D](https://www.windowanddoor.com/article/best-digital-tool-soft-tech-v6-advantage-x3d-visualizer); [Klaes 3D](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en)
- Dashboards de KPI, informes personalizados y vínculo entre planta y finanzas — [FeneVision](https://www.cyncly.com/en/products/fenevision/capabilities); [V6 Advantage](https://www.cyncly.com/resources/news/cyncly-v6-advantage); [Cantor 8.0](https://www.glassonweb.com/news/aw-cantor-80-debuts-glassbuild-america-2026)

### Inferencias (oportunidades para DEKOPEN, no verificadas como ausentes en los incumbentes salvo donde se indica)
1. **Una sola aplicación web para ERP, portal de distribuidores y apps de planta, obra y montaje.** Los incumbentes venden estas piezas como módulos o productos separados (iQuote/Dealer Cloud/Smart Companion; WEB/Delivery App/Mobile Inventory; webshop/WinDo Flow). Que distribuidor, vendedor, planta e instalador vean el mismo objeto con permisos por rol elimina sincronización y doble licencia.
2. **Datos maestros asistidos.** El cuello de botella es cargar sistemas, perfiles, refuerzos, herrajes y colores. Una IA puede leer catálogos PDF o tarifas del proveedor y proponer artículos y reglas, siempre con revisión humana y sin generar números finales; el cálculo sigue en el motor determinista con tests golden. Klaes 2026 apenas añade "aprobación estructurada" del maestro.
3. **IA en el núcleo técnico, no solo un chat.** Por ejemplo: de una foto o plano a una tipología propuesta; de un email de cliente a una cotización borrador; explicación del precio o del despiece en lenguaje natural citando la salida del motor; detección de anomalías de margen. El Klaes AI Hub es horizontal (M365) y A+W solo muestra IA en demos.
4. **Implementación en días, no en meses.** Catálogo demo precargado (como el DEMO_60 de DEKOPEN), plantillas por sistema de perfil común en LatAm y onboarding guiado, frente a consultoría, hardware y más de 80 vídeos.
5. **Medición y montaje móviles incluidos de serie.** Klaes recién en 2026 conecta apps de medición externas y una app de montaje. DEKOPEN puede integrarlas de forma nativa (PWA) desde el principio.
6. **Optimización pensada para talleres pequeños:** retales (offcuts) gestionados por escaneo y sin configuración compleja, que es justo donde la fuente KI-Syndikat dice que los optimizadores 1D clásicos fallan en pymes.
7. **Localización LatAm:** español nativo, documentos tributarios locales (p. ej. SII en Chile, no investigado aquí), moneda y UF, catálogos de proveedores regionales de perfiles y vidrio, y precio SaaS mensual transparente frente a la licencia on-prem sin precio público.
8. **Margen visible de punta a punta.** Cantor 8.0 y el job costing de FeneVision muestran que la tendencia es unir planta con finanzas. DEKOPEN puede mostrar el margen real frente al cotizado por pedido desde el inicio.
9. **UX moderna sin perder densidad.** El regreso del ribbon en V6 muestra que los usuarios expertos valoran la densidad y los atajos. DEKOPEN debe ofrecer teclado, edición en tabla y vistas guardadas, no solo pantallas "bonitas".

### Gaps
- No pude contrastar si alguno de los incumbentes ya ofrece importación asistida de catálogos o IA para configurar desde planos. La ausencia es inferencia por falta de menciones.
- Falta evidencia directa de UI (vídeos y manuales) para un benchmark pantalla por pantalla. Se recomienda una segunda pasada en YouTube (canales oficiales de Klaes, A+W y Cyncly/FeneVision University) y en Scribd/Yumpu.
