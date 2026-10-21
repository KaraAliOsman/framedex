# IA aplicada a la fabricación de ventanas y puertas (estado del arte y oportunidades para DEKOPEN)

> Fecha de corte: 21-oct-2026. Convenciones: "Cited Findings" = hecho verificable con URL (la mayoría son afirmaciones de los propios proveedores, marcadas como tales); "Inferences" = razonamiento propio, no verificado. Los materiales anteriores a 2026 llevan fecha. Ninguna cifra de precisión aquí ha sido verificada de forma independiente salvo donde se indica.

## 1. ¿Qué proveedores de software de fenestración anunciaron o ya ofrecen IA?

### Takeaway
A octubre 2026 la IA real en software de fenestración es escasa y concentrada en dos patrones: (a) asistente conversacional sobre datos de ERP (Extrusia/JOSIE, lanzado 12-oct-2026; la ejecución de tareas aún "en diseño") y (b) extracción de pedidos desde PDF con LLM (A+W Order Entry AI/Mira, dic-2025, para vidrio). Los grandes (Cyncly, Forterro: Klaes/Orgadata) usan "AI" como mensaje de marketing sin funciones concretas publicadas; nadie publica métricas de precisión.

### Cited Findings
**Extrusia (EE. UU.) — el competidor "AI-native" más directo**
- 12-oct-2026: Extrusia lanza una suite cloud para fabricantes de ventanas/puertas que conecta cotización de distribuidores, ingreso de pedidos, ERP, producción, control de calidad, despacho, finanzas y reportes en un solo sistema. Módulos: Dealer Connect (portal autoservicio: configurar productos, cotizar, enviar pedidos; los distribuidores agregan su margen y generan cotización al cliente final), Extrusia ERP, LINK (dashboards en tiempo real de producción, throughput, lead time, WIP, calidad, despacho, excepciones) y JOSIE — [Window & Door](https://www.windowanddoor.com/news/extrusia-launches-integrated-software-suite-window-and-door-manufacturers-0)
- JOSIE hoy: usuarios autorizados preguntan en lenguaje natural sobre pedidos, producción, programación, materiales, calidad, despacho, distribuidores y excepciones. La nota dice que JOSIE "is being designed to go beyond answering questions", es decir, ejecutar tareas operativas está en desarrollo — [Window & Door](https://www.windowanddoor.com/news/extrusia-launches-integrated-software-suite-window-and-door-manufacturers-0); el sitio del proveedor afirma que Josie ya "realiza tareas autorizadas dentro de Extrusia" (discrepancia entre prensa y marketing) — [Extrusia](https://extrusia.com/)
- Primer despliegue: Earthwise of Kansas City; en la semana de go-live alcanzó ~95% de su volumen normal de producción semanal. Sin precios, disponibilidad general ni métricas de IA publicadas — [Window & Door](https://www.windowanddoor.com/news/extrusia-launches-integrated-software-suite-window-and-door-manufacturers-0)

**A+W Software (vidrio; Alemania/EE. UU.) — extracción de pedidos PDF con LLM**
- 17-dic-2025: A+W Order Entry AI, con asistente "Mira" basado en LLM; early access para clientes more4more desde 9-dic-2025; uso gratuito durante Q1-2026; alojado en A+W Cloud — [A+W blog](https://blog.a-w.com/us/press-release-aw-order-entry-ai)
- Flujo: OCR de PDFs subidos o recibidos por correo; extracción con Google Gemini; mapeo del vocabulario de artículos del cliente a artículos del ERP; corrección vía chat (cambiar layout, ajustar datos, corregir mapeos) o edición directa en una UI avanzada; integración por API con el ERP. Sin métricas de precisión publicadas — [A+W blog](https://blog.a-w.com/us/press-release-aw-order-entry-ai)
- Jul-2026: A+W lo presentó en GlassBuild America 2026 (23–25 sep) como forma "simple y escalable" de automatizar el ingreso manual de pedidos PDF para fabricantes pequeños; según resumen de búsqueda, el sistema identifica datos ambiguos y prepara información estructurada para el ERP — [Glass on Web](https://www.glassonweb.com/news/aw-showcases-ai-powered-order-entry-solution-glassbuild-america-2026)

**Cyncly (V6 Advantage/Soft Tech, FeneVision, Window Designer)**
- 22-ene-2026: Cyncly anunció que en Fensterbau Frontale 2026 (Núremberg, 24–27 mar) mostraría "applied AI software" incluyendo V6 Advantage, FeneVision y Window Designer; el comunicado menciona "AI-enabled technology that delivers predictive insights and automated suggestions" sin atribuirla a una función o producto concreto — [Cyncly](https://www.cyncly.com/resources/news/fensterbau-frontale-2026)

**Forterro (Klaes, Orgadata/LogiKal)**
- Forterro adquirió Klaes; el anuncio dice que Klaes accederá a las "capacidades de IA" de Forterro, sin describir producto — [Forterro](https://www.forterro.com/en/news/forterro-acquires-klaes)
- Orgadata (LogiKal) pertenece a Forterro desde marzo 2025; sus productos siguen sin cambios; no encontré lanzamiento de IA — [LogiKal/Orgadata](https://www.logikal-software.com/en/orgadata)

**Otros**
- Windowmaker 2026: "Smarter Quote" = cotización como enlace web interactivo con precios, detalle, términos y vista 3D (no rotulado como IA) — [Windowmaker](https://windowmaker.com/product-releases-and-updates/)
- WindoorCraft: dibujo, cotización, render, cálculo de perfiles/vidrio y gestión de fábrica, con "AI rendering" — [WindoorCraft](https://windowcc.com/)
- ArchiLabs: "AI CAD" que convierte una medición en terreno en planos de fabricación listos para CNC (listas de corte, DXF/DWG) — [ArchiLabs](https://archilabs.ai/posts/ai-cad-for-custom-windows-and-doors-faster-shop-drawings)
- Emmegisoft FP Suite (FP Pro, Dealer, Gest, Facade, Opti2D, Cam, Workshop): sin funciones de IA descritas — [Emmegisoft](https://www.emmegisoft.com/en/page/fp-suite)
- WindowEdge publica una tesis de "agentic business OS" para home improvement (instaladores/retail, no fabricación) — [WindowEdge](https://windowedge-ai.ghost.io/agentic-business-os-for-home-improvement/)
- Hover: medición de ventanas/puertas exteriores desde fotos de smartphone; el proveedor declara que el 98% de sus medidas cae dentro de ±5% (agregado, no por segmento); el producto de interiores no requiere LiDAR — [Hover help](https://help.hover.to/articles/392328-how-accurate-are-the-measurements); [Hover ventanas](https://hover.to/measure/exterior/windows-and-doors); [Hover interiores](https://help.hover.to/en/articles/7061443-hover-for-interiors)
- Estudio académico: LiDAR de iPhone 13 Pro frente a escáner FARO y distanciómetro: calidad inferior a LiDAR de gama alta y con distorsiones — [UiTM / Scopus](https://update.library.uitm.edu.my/Record/2-s2.0-85212127746/Details)

### Inferences
- Nadie en fenestración publica precisión, tasa de error ni mecanismo de verificación de su IA: es un hueco de confianza que DEKOPEN puede ocupar con "cada número trazable al motor".
- El patrón JOSIE (preguntar sobre datos del ERP) es la base mínima del mercado en EE. UU.; el diferencial es ejecutar acciones con permisos, auditoría y aprobación, que Extrusia aún no demuestra públicamente.
- ±5% (Hover) es inaceptable para fabricar (tolerancia de DEKOPEN 0,00 mm sobre cotas ingresadas); medición por foto sirve para prospección/precotización, nunca para orden de corte sin rectificación en terreno.
- No encontré evidencia de IA en software de ventanas para Chile/LatAm (posible campo libre, pero ver Gaps).

### Gaps
- No pude verificar funciones de IA concretas en Klaes, LogiKal, Schüco, Elcom, FeneTech, Quotesoft, Lisec ni 3E/Preference; puede que existan anuncios en alemán/italiano no indexados.
- No investigué proveedores latinoamericanos (otro investigador puede cubrirlo).
- Sin datos de precio de los módulos de IA (A+W gratis solo en Q1-2026; Extrusia sin precio).

## 2. Industrias adyacentes con takeoff/estimación por IA maduros: qué funciona, precisión, patrones UX

### Takeaway
En construcción, el takeoff por IA (Togal, Ruh, Kreo, Bluebeam Max) es real y se vende como "punto de partida revisable", no como resultado final. La única evaluación independiente encontrada (Togal, jun-2026) muestra desviaciones pequeñas pero estadísticamente significativas y subestimación sistemática en áreas. Los mejores patrones UX: trazabilidad de cada cantidad a su hoja de origen, doble conteo ciego, marcar discrepancias en vez de promediar, y aprobación humana obligatoria antes de la propuesta.

### Cited Findings
- Togal: reconoce muros, pisos, cielos, puertas y ventanas; "hasta 80% más rápido" (afirmación del proveedor, sin cifra de precisión para puertas/ventanas) — [Togal blog](https://www.togal.ai/blog/construction-takeoffs-ai-speed-accuracy)
- Togal para vidriería: localiza ventanas, puertas y vanos vidriados en todo el set de planos, mide área vidriada y largo de marco, separa storefront/curtain wall por marca de vano; "hasta 4X más rápido" (proveedor) — [Togal glazing (resultado de búsqueda)](https://www.togal.ai/trade/glass-glazing-windows); [Togal trades](https://www.togal.ai/trades/glazing-windows-doors)
- Documentación Togal: el resultado automático es un punto de partida rápido que el usuario revisa, reclasifica y edita; detecta vanos de puerta y el usuario asigna tipos — [Togal help: botón Togal](https://help.togal.ai/en/articles/15602961-the-togal-button-togal-s-automated-takeoff); [Togal help: puertas/ventanas](https://help.togal.ai/en/articles/15611664-how-to-backout-doors-and-windows)
- Estudio independiente (Utica University, jun-2026): Togal vs takeoff del contratista en proyecto comercial real, 29 partidas (terminaciones, ventanas y puertas): desviaciones globales pequeñas pero estadísticamente significativas, con subestimación consistente en cantidades de área. Cita un estudio educativo con −51,3% de tiempo y +20,4% de precisión, y advierte que esos estudios miden experiencia de usuario, no exactitud frente a profesionales — [EasyChair](https://easychair.org/publications/paper/pkrRp)
- Ruh AI (vidriería): mide curtain wall (por pie²) y storefront (por pie lineal) desde elevaciones separando spandrel de visión; cuenta ventanas y puertas por tag (simples vs dobles); sellos perimetrales; 9 "recetas" de vidriería editables; cada cantidad enlazada a la hoja de origen; aberturas contadas dos veces con segundo conteo ciego; discrepancias se marcan al estimador "en lugar de promediarse"; precios desde la lista propia del cliente, mostrando la fuente de precio por línea; el paquete de curtain wall queda sin precio hasta ingresar la cotización del proveedor; "nada llega a la propuesta antes de que el estimador apruebe". Sin % de precisión publicado; testimonio de ~50% menos tiempo de licitación (un cliente) — [Ruh AI](https://www.ruh.ai/industrial/construction/estimating-software/glazing)
- Bluebeam Max: nivel de suscripción de Revu que agrega IA vía Model Context Protocol (MCP) — Claude se compra aparte; casos: etiquetas de página, marcadores, escalas, convertir correos en marcas PDF, apoyo a takeoff; se recomienda definir cómo se revisarán los resultados y probar en un proyecto controlado (IMAGINiT, 24-ago-2026) — [IMAGINiT](https://resources.imaginit.com/building-solutions-blog/bluebeam-max-and-ai-your-questions-answered); [Bluebeam](https://www.bluebeam.com/bluebeam-max)
- Kreo (Londres, 2017): takeoff 2D cloud, BIM takeoff y Kreo Modular; automatiza medición y conteo (fuentes de directorio, no verificadas) — [CB Insights](https://www.cbinsights.com/company/kreo/); [SoftwareReviews](https://www.softwarereviews.com/products/kreo-bim-takeoff)
- XBuild ofrece estimación de ventanas/puertas por IA para contratistas — [XBuild](https://x.build/windows-doors-estimating)
- CRL (C.R. Laurence) Storefronts & Partitions Online: estimador tradicional (no IA) para entradas, storefront, curtain wall y tabiques, genera paquetes de cotización — [CRL](https://www.crlaurence.com/onlinetools/details/StorefrontsPartitions)

### Inferences
- El patrón "doble conteo ciego + discrepancia marcada + enlace a la hoja de origen + línea sin precio hasta que hay fuente" de Ruh es casi exactamente la política que necesita DEKOPEN: la IA propone cantidades/tipologías, el motor calcula, y cualquier hueco se muestra como "sin calcular", nunca rellenado.
- La subestimación sistemática de áreas (estudio Togal) sugiere que un takeoff por IA para fenestración debe validarse contra cuadros de vanos (schedules) cuando existan, y presentar diferencias por tipología.
- Bluebeam vía MCP muestra que exponer funciones del producto como herramientas para un LLM externo es ya un patrón comercial; DEKOPEN podría exponer su motor por MCP/API con las mismas reglas de aprobación.

### Gaps
- No encontré cifras de precisión publicadas por ventana/puerta para ningún producto de takeoff, ni benchmarks independientes salvo el de Utica (cuyos números por partida no pude leer).
- No investigué software de carpintería/muebles (Cabinet Vision, Mozaik, etc.) por límite de búsquedas.
- La página específica de Togal para vidriería devolvió 404 al obtenerla; sus afirmaciones vienen del extracto del buscador.

## 3. Document AI para catálogos (tablas de perfiles, listas de precios, planos) y extracción de medidas desde planos; buenas prácticas de verificación

### Takeaway
Los LLM multimodales extraen bien texto y tablas simples, pero se degradan fuertemente con esquemas amplios y tablas largas (ExtractBench feb-2026: 0% de salidas válidas en un esquema de 369 campos para todos los modelos frontera probados). Por tanto, la extracción de catálogos de proveedores debe ser por lotes pequeños, con esquema acotado, validación determinística y revisión humana por diferencias; la detección de ventanas en planos es un problema de investigación activo con datasets limitados.

### Cited Findings
- ExtractBench (arXiv 2602.12247, feb-2026; Contextual AI): 35 PDFs, 12.867 campos evaluables, esquemas de decenas a cientos de campos; modelos probados GPT-5/5.2, Gemini-3 Flash/Pro, Claude 4.5 Opus/Sonnet; 0% de salida válida en esquema financiero de 369 campos en todos; la precisión cae fuertemente al ampliar el esquema; los modelos "siguen siendo poco fiables en esquemas realistas" — [arXiv abs](https://arxiv.org/abs/2602.12247)
- ExtractBench separa campos omitidos de campos alucinados y usa reglas de coincidencia por tipo (exacta para identificadores, tolerancia para cantidades) — [arXiv PDF](https://arxiv.org/pdf/2602.12247)
- Horn & Keuper (mar-2026): benchmark de 21 parsers PDF sobre 451 tablas; LLM-como-juez correlaciona r=0,93 con humanos frente a TEDS 0,68 y GriTS 0,70 — [arXiv 2603.18652](https://arxiv.org/abs/2603.18652)
- PDF-parser-benchmark (GitHub, nov-2025): similitud de edición GPT-5.1 92%, Gemini 3 Pro 87%, Claude Sonnet 4.5 80%; en facturas la mayoría de parsers logra 70–80% — [GitHub](https://github.com/applied-artificial-intelligence/pdf-parser-benchmark)
- Prueba informal de facturas (sin fecha): un modelo 83,8% sin partidas, baja a 68,1% al incluir tablas — [HackerNoon](https://hackernoon.com/can-your-llm-handle-an-invoice-i-tested-5heres-the-truth)
- Detección en planos: CubiCasa5K tiene anotaciones de más de 80 categorías; MuraNet trata segmentación de muros y detección de puertas/ventanas como multitarea — [MuraNet arXiv](https://arxiv.org/pdf/2309.00348); spotting panóptico de símbolos en planos CAD con ayuda de texto (2026) reduce a 10 clases contables incl. ventana y puerta — [arXiv 2607.12678](https://arxiv.org/pdf/2607.12678)
- DoorDet: los datasets públicos para detección fina multiclase de puertas son escasos; construye uno combinando detector + LLM — [arXiv 2509.17283](https://arxiv.org/pdf/2509.17283)
- Tesis finlandesa: con CubiCasa5k (y versión balanceada), YOLOv11 rinde mejor en datos esquemáticos 2D — [Doria](https://www.doria.fi/handle/10024/193626?show=full)
- A+W ya aplica OCR + Gemini + mapeo a artículos ERP + corrección por chat en pedidos PDF de vidrio (ver §1) — [A+W blog](https://blog.a-w.com/us/press-release-aw-order-entry-ai)

### Inferences
- Para catálogos de perfiles (pesos kg/m, inercias, descuentos de corte, precios por barra) conviene: extraer página a página con esquema pequeño por tipo de tabla; parsear números como texto y convertir a `Decimal` en código; validar con reglas (unidades, rangos, sumas, referencias cruzadas entre tablas); mostrar cada valor con recorte de la página origen; nada se publica en el catálogo sin aprobación humana y queda versionado.
- Doble extracción independiente (dos modelos o dos pasadas) y comparar; solo las discrepancias van a la cola de revisión (análogo al conteo ciego de Ruh).
- Las medidas de planos son de baja confianza: escala, cotas ilegibles y convenciones de vanos (luz vs vano terminado) varían; usar la IA para leer cuadros de vanos/etiquetas y cotas escritas, no para medir píxeles, y exigir confirmación por tipología.

### Gaps
- No encontré benchmarks específicos de extracción de fichas técnicas de perfiles (PVC/aluminio) ni de planos de taller de ventanas.
- No obtuve las métricas mAP/F1 de puertas/ventanas en CubiCasa5K.

## 4. Flujos agénticos: IA que ejecuta tareas multipaso en software de negocio con niveles de aprobación, auditoría, deshacer y presupuestos

### Takeaway
La guía consolidada en 2026: controles fuera del modelo (en la capa de aplicación), aprobación graduada por riesgo/reversibilidad, pausa en la llamada a herramienta sensible hasta aprobación humana, aprobaciones con alcance y vencimiento, y log de auditoría a prueba de manipulación. No existe un estándar autorizado sobre "deshacer"; la práctica es exigir aprobación para lo irreversible y planificar rollback.

### Cited Findings
- OpenAI Agents: herramientas sensibles marcadas como "requiere aprobación"; el modelo puede decidir que la acción es necesaria, pero la ejecución se pausa hasta aprobar o rechazar — [OpenAI docs](https://developers.openai.com/api/docs/guides/agents/guardrails-approvals)
- OWASP LLM06:2025 "Excessive Agency": un guardrail implementado solo como instrucción en el system prompt no es un guardrail; los controles van en la aplicación (citado vía blog) — [Enterprise DNA](https://enterprisedna.co/resources/playbooks/ai-agents-that-work/read/07-guardrails-and-human-approval)
- Aprobación por niveles: solo lectura sin revisión (evitar fatiga de aprobación), riesgo medio con un aprobador, riesgo alto con regla de dos personas; aprobar el plan completo, con aprobaciones que vencen y limitadas a recursos concretos — [DEV: approval gates](https://dev.to/hassann/ai-agent-guardrails-approval-gates-and-blast-radius-control-23hl); [DEV: guardrails 2026](https://dev.to/dublecc/ai-agent-safety-guardrails-human-approval-sandboxes-and-audit-logs-2026-20p6)
- Mapear cada gate, log y rollback a un propósito explícito de prevención o recuperación; exigir aprobación para acciones difíciles de revertir (reembolsos, borrados, cambios en producción) — [Geosurge](https://www.geosurge.ai/corpus/gen-4146/agent-assisted-automation/designing-agent-assisted-automation-guardrails-approval-gates-audit-logs-and-rollback-controls.html); [KodeKloud](https://notes.kodekloud.com/docs/AI-Foundations-for-Technical-Professionals/AI-Agents-and-Agentic-AI/Human-in-the-Loop-Approvals-Checkpoints-and-Guardrails/page)
- Herramientas gobernadas + revisión humana como patrón de paquete (R/LLMRagent) — [CRAN vignette](https://ftp.fau.de/cran/web/packages/LLMRagent/vignettes/governed-tools-and-human-review.html)
- En el sector: JOSIE opera solo para "usuarios autorizados" y la ejecución de tareas está en diseño — [Window & Door](https://www.windowanddoor.com/news/extrusia-launches-integrated-software-suite-window-and-door-manufacturers-0); Ruh exige aprobación del estimador antes de toda propuesta — [Ruh AI](https://www.ruh.ai/industrial/construction/estimating-software/glazing)

### Inferences
- Encaje con DEKOPEN: la IA llama a las mismas funciones (endpoints) que el usuario, con los permisos RLS del usuario; acciones clasificadas en (1) lectura libre, (2) borrador/propuesta reversible (crear cotización borrador, agregar ventana) sin aprobación pero con deshacer, (3) consecuencias externas o inmutables (emitir revisión, enviar al cliente, orden de compra, cobro) con clic humano explícito — coherente con la invariante "acciones externamente consecuentes requieren clic humano".
- Cada acción de IA debe registrar: prompt/intención, herramienta, parámetros, versión de catálogo y motor, resultado, usuario que aprobó; las revisiones emitidas ya son inmutables, lo que facilita la auditoría.
- Presupuestos/créditos: no encontré fuentes de buenas prácticas específicas; inferencia: medir costo por tarea y límite por organización, con degradación a "solo lectura" al agotarse.

### Gaps
- No encontré documentación autorizada sobre deshacer (undo) transaccional en agentes ni sobre modelos de créditos de IA en SaaS vertical.

## 5. Riesgos y modos de falla (números alucinados, dimensiones erróneas) y cómo se mitigan

### Takeaway
Los modos de falla documentados son: alucinación u omisión de campos en extracción, colapso en esquemas/tablas grandes, subestimación sistemática de áreas en takeoff, y medición por foto con error de ±5%. Los productos líderes mitigan con revisión humana obligatoria, trazabilidad al origen, doble conteo, líneas sin precio cuando falta fuente y corrección por chat/UI; ninguno publica tasas de error.

### Cited Findings
- Colapso de extracción estructurada en esquemas amplios (0% válido a 369 campos) — [ExtractBench](https://arxiv.org/abs/2602.12247)
- Omisión vs alucinación deben medirse por separado; tolerancia por tipo de campo — [ExtractBench PDF](https://arxiv.org/pdf/2602.12247)
- Precisión en facturas cae al incluir tablas de partidas (83,8% → 68,1%, prueba informal) — [HackerNoon](https://hackernoon.com/can-your-llm-handle-an-invoice-i-tested-5heres-the-truth)
- Subestimación consistente de áreas por takeoff IA frente a contratista — [EasyChair / Utica](https://easychair.org/publications/paper/pkrRp)
- Medición por foto: 98% dentro de ±5% (agregado, proveedor) — [Hover](https://help.hover.to/articles/392328-how-accurate-are-the-measurements); LiDAR de smartphone con distorsiones e inferior a LiDAR profesional — [UiTM](https://update.library.uitm.edu.my/Record/2-s2.0-85212127746/Details)
- Mitigaciones observadas: revisar/reclasificar/editar el resultado automático (Togal) — [Togal help](https://help.togal.ai/en/articles/15602961-the-togal-button-togal-s-automated-takeoff); conteo ciego, discrepancias marcadas, fuente de precio por línea, aprobación previa a propuesta (Ruh) — [Ruh AI](https://www.ruh.ai/industrial/construction/estimating-software/glazing); corrección vía chat y UI, mapeo a artículos ERP (A+W) — [A+W blog](https://blog.a-w.com/us/press-release-aw-order-entry-ai)
- Guardrails fuera del prompt (OWASP LLM06) — [Enterprise DNA](https://enterprisedna.co/resources/playbooks/ai-agents-that-work/read/07-guardrails-and-human-approval)

### Inferences
- La arquitectura de DEKOPEN (motor determinístico `Decimal` como única fuente de números) elimina por diseño la clase "número inventado" en salidas calculadas; el riesgo residual se desplaza a los insumos (medidas, tipologías, precios de catálogo extraídos) y a la elección de función/parámetros por la IA. Mitigación: validación de esquema + reglas de dominio en el backend, eco explícito de los parámetros que la IA pasó ("ancho 1.200 mm leído del plano p.3") y confirmación del usuario antes de emitir.
- Riesgos específicos de fenestración a vigilar: confundir vano vs luz/medida de fabricación, mm vs cm, ancho×alto invertidos, sentido de apertura (mano), unidades de precio (barra vs metro vs kg), IVA incluido/excluido, moneda (CLP/UF/USD).
- Texto generado por LLM en documentos al cliente (descripciones, correos) nunca debe contener cifras que no provengan de campos del motor; renderizar números solo desde plantillas con datos estructurados.

### Gaps
- No encontré informes públicos de incidentes reales (errores de fabricación) causados por IA en fenestración.

## 6. Ranking de 15–25 automatizaciones de IA de mayor valor para un fabricante de ventanas (con datos requeridos y verificación)

### Takeaway
Las de mayor valor y menor riesgo son las que convierten insumos desordenados (WhatsApp, correo, PDF, planos, fotos) en llamadas estructuradas al motor, y las que responden/operan sobre datos existentes; las de mayor riesgo (medición por foto, takeoff automático de planos para producción) deben quedar como borradores con confirmación. Todo el ranking es inferencia propia, apoyada en los patrones citados arriba.

### Cited Findings
- Precedentes de mercado que sustentan el ranking: extracción de pedidos PDF→ERP (A+W) — [A+W](https://blog.a-w.com/us/press-release-aw-order-entry-ai); asistente conversacional sobre datos de ERP (Extrusia JOSIE) — [Window & Door](https://www.windowanddoor.com/news/extrusia-launches-integrated-software-suite-window-and-door-manufacturers-0); takeoff de vanos desde planos (Togal, Ruh) — [Ruh AI](https://www.ruh.ai/industrial/construction/estimating-software/glazing); medición por foto (Hover) — [Hover](https://hover.to/measure/exterior/windows-and-doors); planos de fabricación desde medición (ArchiLabs) — [ArchiLabs](https://archilabs.ai/posts/ai-cad-for-custom-windows-and-doors-faster-shop-drawings); cotización web interactiva (Windowmaker) — [Windowmaker](https://windowmaker.com/product-releases-and-updates/); portal de distribuidores con márgenes (Extrusia Dealer Connect) — [Window & Door](https://www.windowanddoor.com/news/extrusia-launches-integrated-software-suite-window-and-door-manufacturers-0)

### Inferences
Ranking (valor × factibilidad × riesgo controlable). Formato: automatización — datos que necesita — cómo se verifica.

1. **Solicitud libre → cotización borrador** (texto/WhatsApp/correo/nota de voz: "3 correderas 1500x1200 blanco termopanel") — catálogo de tipologías/sistemas, defaults de la organización — IA solo mapea a tipología+parámetros; motor calcula; usuario ve cada parámetro inferido resaltado y confirma antes de emitir.
2. **Lectura de cuadro de vanos / listado de ventanas desde PDF o planilla del cliente** — PDF/Excel del arquitecto o constructora, mapeo de códigos (V1, P2) a tipologías — doble extracción + validación de rangos (dimensiones plausibles, cantidades enteras); tabla de revisión con recorte del origen por fila.
3. **Asistente operativo con herramientas ("copiloto que opera el producto")**: crear proyecto, agregar ventanas, duplicar, cambiar color/vidrio en lote, recalcular — API existente + permisos RLS — acciones reversibles con deshacer; emisión y envío requieren clic humano; log de auditoría.
4. **Preguntas sobre el negocio en lenguaje natural** (estado de proyectos, margen por obra, pendientes, cotizaciones por vencer) — datos transaccionales — respuestas citan los registros y cifras provienen de consultas/motor, no del texto del LLM.
5. **Importación de catálogos de proveedor desde PDF/Excel** (perfiles, accesorios, vidrios, listas de precios) — PDFs de proveedores (p. ej. sistemas de perfil), estructura del catálogo DEKOPEN — extracción por tabla con esquema pequeño, conversión a `Decimal` en código, diff contra versión previa, aprobación humana y versión inmutable.
6. **Actualización de listas de precios con detección de cambios** — nueva lista vs vigente — mostrar diff (+/−% por ítem), alertar saltos anómalos, aprobación antes de activar; historial inmutable.
7. **Revisión de consistencia antes de emitir** ("linter" de cotización: mano/apertura faltante, medida fuera de límites del sistema, vidrio incompatible, peso de hoja excesivo) — reglas del motor + límites del sistema — chequeos determinísticos; la IA solo explica en lenguaje claro y propone la corrección.
8. **Redacción de correos/mensajes de seguimiento y propuesta comercial** — datos de la cotización — números insertados desde campos estructurados; envío con clic humano.
9. **Explicación de la cotización al cliente** (por qué cuesta X, diferencias entre opciones) — desglose del motor — solo cita partidas existentes.
10. **Comparar alternativas** (PVC vs aluminio, DVH vs monolítico, otra serie) — catálogo + motor — cada alternativa es un cálculo real del motor, presentado lado a lado.
11. **Precotización desde fotos del vano** (tipo de ventana actual, cantidad, medidas aproximadas) — fotos del cliente — marcado explícito "estimación, requiere rectificación"; nunca pasa a orden de corte sin medida en terreno (±5% documentado en Hover).
12. **Captura asistida en terreno** (rectificador dicta medidas, foto con cinta) — app móvil, voz — eco de valores con unidad, doble confirmación, alerta si ancho/alto invertidos vs plano.
13. **Takeoff desde planos de arquitectura** (contar ventanas por tipo, leer cotas) — PDF/DWG de planos — tabla de revisión, conteo doble, discrepancias contra cuadro de vanos; estado borrador.
14. **Seguimiento comercial/priorización de cotizaciones** (cuáles llamar hoy) — historial de cotizaciones y cierres — recomendación con razones visibles; la acción la ejecuta el humano.
15. **Lectura de órdenes de compra/confirmaciones de proveedores y conciliación** (precio facturado vs lista) — PDFs de facturas/OC — diferencias marcadas, nada se paga automáticamente.
16. **Planificación de producción sugerida** (agrupar por color/sistema, fechas comprometidas) — pedidos, capacidad — el optimizador/plan es determinístico; la IA explica y permite reordenar con confirmación.
17. **Optimización de corte explicada** — resultado del optimizador del motor — la IA no optimiza, solo explica desperdicio y propone reutilizar retazos existentes en inventario.
18. **Compras sugeridas** (qué perfiles/barras pedir según pedidos y stock) — BOM del motor, stock — cantidades calculadas por el motor; OC enviada con clic humano.
19. **Onboarding guiado de la organización** (cargar datos, márgenes, plantillas) — formularios del producto — la IA rellena borradores, el usuario confirma cada pantalla.
20. **Soporte/ayuda contextual del producto** (cómo hacer X) — documentación — respuestas con enlace a la función; sin cifras.
21. **Clasificación de reclamos/postventa con fotos** (sello, burlete, vidrio roto) — fotos, historial del proyecto — sugiere categoría y piezas desde la BOM original; humano decide.
22. **Pronóstico de demanda/flujo de caja simple** — histórico de cotizaciones y ventas — valor bajo hasta tener datos suficientes; mostrar como rango y con supuestos explícitos.
23. **Detección de defectos por visión en planta** (soldadura PVC, rayas) — cámaras, dataset etiquetado — fuera del alcance inicial de un SaaS web; valor alto solo para plantas grandes.

Prioridad sugerida para DEKOPEN: 1–7 como núcleo (convierten trabajo manual en llamadas verificables al motor), 8–13 como segunda ola, 14–23 dependientes de datos/volumen.

### Gaps
- No hay datos públicos sobre cuánto tiempo dedica un fabricante chileno típico a cada tarea, por lo que el ranking de valor no está cuantificado.
- No se validó con usuarios reales de DEKOPEN ni con estudios de mercado LatAm.
