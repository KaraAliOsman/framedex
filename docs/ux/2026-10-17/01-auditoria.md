# Auditoría de producto y experiencia

[Volver al plan](README.md) · 17-10-2026

## Cómo se sostienen los hallazgos

- **V:** observado en el stack REVIEW durante esta investigación. Build sin SHA
  confirmado; fixture sintético, no una empresa operando en producción.
- **C:** confirmado por lectura del código en
  `edcfd2844d2c2fc7cbb0d3b543b50e9089ab9b3f`.
- **D:** documento/PDF inspeccionado o renderizado con un plan existente.
- **H:** contexto o aceptación histórica; orienta, no acredita el estado actual.
- **P:** propuesta o hipótesis de diseño. Requiere evaluación al implementarse.

La gravedad expresa cuánto impide trabajar: **crítica** afecta confianza o una
salida de trabajo; **alta** hace difícil una tarea principal; **media** añade
fricción o confusión; **baja** es un refinamiento. No son clasificaciones de
vulnerabilidad ni bugs de cálculo demostrados.

## Diagnóstico de fondo

La aplicación intenta hacer explícitos sus contratos y autoridades. Esa inversión
ha producido controles de dominio valiosos, pero también ha trasladado al usuario
el vocabulario y la estructura de la implementación. Una pantalla puede cumplir
permisos, estados y trazabilidad y aun así no dejar claro dónde hacer clic.

La experiencia necesita tres capas que hoy compiten entre sí:

| Capa | Pregunta del usuario | Presentación objetivo |
|---|---|---|
| Trabajo habitual | ¿Qué estoy diseñando y qué hago ahora? | Dibujo, decisiones esenciales y acción principal. |
| Decisión profesional | ¿Qué vidrio, apertura o solución me conviene? | Opciones comparables, restricciones relevantes y efecto visible. |
| Comprobación técnica | ¿De dónde sale y con qué autoridad? | Detalle bajo demanda, fuente, revisión y traza. |

## Hallazgos principales

| ID | Evidencia | Gravedad | Hallazgo y consecuencia | Decisión de diseño |
|---|---|---|---|---|
| A01 | V/C | Alta | La navegación replica dominios y permisos de lectura. Un jefe ve 13 destinos principales y grupos; necesita conocer la arquitectura para orientarse. | Navegar por trabajo y rol; accesos secundarios dentro de su contexto. |
| A02 | V | Alta | En proyecto, cabecera, seis fases, ocho pestañas, avisos y filtros desplazan las ventanas fuera del primer viewport. | Cabecera breve; ventanas visibles al entrar; progreso comercial compacto. |
| A03 | V | Media | El acceso al editor requiere descubrir el doble clic en la miniatura o abrir ficha y después editor. Un clic selecciona. | Acción Editar visible y coherente; selección múltiple diferenciada. |
| A04 | C | Alta | Crear proyecto exige nombre de proyecto y nombre del cliente. Los otros nueve campos comerciales ya son opcionales/plegados. Aun así, el cliente precede a poder dibujar. | Borrador inmediato, nombre automático editable y cliente posterior. |
| A05 | C | Alta | Añadir posición hace elegir serie, tipología, medidas, vidrio y color; hay tamaños iniciales, pero no una herencia completa del proyecto. | Biblioteca visual con defaults heredados; ajustar medidas en el dibujo. |
| A06 | C | Alta | Cambiar serie reinicia vidrio/color en la biblioteca. | Conservar opciones compatibles; sustituir incompatibles con explicación breve. |
| A07 | V | Alta | Lienzo con apariencia plana y selección turquesa dominante; cotas total/módulo repetidas. | Mejor jerarquía de líneas y cotas según selección y zoom. |
| A08 | V | Alta | Inspector mezcla decisiones con composición, dimensiones derivadas, kit y autoridad. | Sección esencial corta; ficha técnica separada, contextual y recordada. |
| A09 | V | Alta | En 3D el Nogal se ve marrón plano y el producto pequeño en el escenario. | Activos reales, mapeo por miembro y encuadre que haga legible el producto. |
| A10 | C | Alta | `memberBar` en 3D omite expresamente los ingletes; termina perfiles con cortes rectos. | Representar la junta declarada y resolver los encuentros visuales. |
| A11 | C | Alta | Hay carga de `texture_path`, repetición y material físico, pero no un mapeo en mm por perfil en los módulos inspeccionados. | Escala, orientación y continuidad de textura controladas. |
| A12 | V | Media | Selector de acabados con opciones y muestras planas; no permite reconocer bien el efecto antes de aplicar. | Muestras con veta real, dos caras y vista previa sobre la ventana. |
| A13 | V/C | Alta | Catálogo presenta varias versiones y series sintéticas al mismo nivel; secciones rectangulares sencillas. | Biblioteca de sistemas con versión vigente, alcance y fuente; separar entrenamiento de trabajo real. |
| A14 | V | Alta | Importación ofrece plantilla primero; input nativo y botón de archivo redundantes; lenguaje de revisión técnica. | Una zona principal para PDF y preparación automática. |
| A15 | C | Alta | Ya hay transporte multimodal, pero el helper envía texto en lugar de imagen cuando una página tiene texto. Puede perder diagramas de páginas mixtas; las citas se verifican contra líneas sin regiones. | Ampliar a documento/layout/OCR/visión por región, sin duplicar el transporte existente. |
| A16 | C | Alta | El helper de PDF limita el documento a 20 páginas; 100 000 caracteres piden dividir; revisión con límite de 2 000 filas. | Partición y reanudación internas; nunca pedir trocear a mano como camino normal. |
| A17 | V | Alta | La IA resuelve el cambio simple de ancho, pero expone modo, trabajo durable, propuesta y aprobación. | Acciones simples reversibles con Deshacer; jobs grandes en segundo plano. |
| A18 | V | Media | La propuesta de ancho añade una advertencia térmica extensa poco relacionada con el pedido. | Avisar por efecto y momento; no adjuntar todos los pendientes a cada cambio. |
| A19 | V | Alta | El despiece aparece en un modal estrecho con códigos, longitudes y cantidades; cuesta relacionarlo con la ventana. | Espacio de materiales amplio con vínculo pieza↔dibujo. |
| A20 | D | Alta | Cotización de 12 posiciones ocupa ocho páginas; primera página muy vacía, dibujos pequeños y resumen sin miniaturas. | Composición comercial con dibujos legibles y resumen visual. |
| A21 | D | Crítica | Plano de ensamblaje corta códigos a izquierda/derecha y superpone etiquetas con el producto. | Callouts cortos, márgenes de anotación y leyenda estable. |
| A22 | D | Alta | Pack de producción de cuatro unidades fijas ocupa 24 páginas; portada casi vacía y páginas de poca información. | Documentos por estación y paginación según contenido. |
| A23 | D | Media | En taller aparece `STEEL` sin traducir y referencias repetidas «Sin dato P01». | Vocabulario de taller; agrupar la causa sin dato sin esconderla. |
| A24 | V/C | Media | «Abrir cotización emitida» descarga un archivo por `download`; no permite inspección integrada. | Visor con revisión, descargar/imprimir y acceso al portal. |
| A25 | V | Alta | Tablero con 175 OT en una columna y otras vacías; tarjetas de texto sin miniatura. | Agrupar por obra/lote, vistas de cola y carga real de trabajo. |
| A26 | V | Alta | Detalle de una OT en calidad abre con docenas de piezas de corte antes de los chequeos. | El contenido inicial sigue la estación y la tarea actual. |
| A27 | V | Alta | Compras comunica «requisitos congelados» y «elegibilidad explícita»; bloques grandes de materiales. | Lista de faltantes comprables con acciones y explicación técnica bajo demanda. |
| A28 | V | Media | Bajo «Comprar lo que falta» aparece una necesidad con existencia suficiente y compra cero; sin proveedor/precio ocupa atención. | Priorizar cantidad pendiente positiva; material cubierto en resumen desplegable. |
| A29 | V/C | Alta | Inventario muestra filas visualmente idénticas; la identidad incluye variante interna que no siempre se ve. | Mostrar acabado, largo, unidad y variante; agrupar sin perder identidad. |
| A30 | V | Alta | Hoy contiene 176 acciones; numerosas OT del mismo proyecto repiten «Prepara el plan de corte». | Agrupar una causa común y resolver lotes desde el resumen. |
| A31 | V | Media | Terreno vacío para el manager muestra «Pide tu ruta de obra», mensaje orientado al instalador. | Vacío según rol: planificar visita para encargado, solicitar ruta para instalador. |
| A32 | V/C | Media | La misma experiencia mezcla «Inicio» en navegación y «Hoy» en título. | Nombres consistentes y explícitos. |
| A33 | V | Alta | Muchas franjas, bordes y controles con peso similar; el acento se extiende por la herramienta. | Jerarquía por tamaño, espacio y tinta; acento para selección/acción. |
| A34 | V/P | Alta | Dos temas multiplican variaciones sin corregir estructura o calidad visual. | Una dirección definitiva y criterios de lectura por tarea. |
| A35 | H/C/P | Alta | La aceptación pasada acredita contratos/casos; no demuestra que un profesional entienda el flujo sin ayuda. | Campaña final basada en tareas completas y observación de usuarios. |

**Matices que evitan un diagnóstico falso:** no se demostró un bug de stock por
ver filas repetidas; pueden ser variantes o datos de fixture. Tampoco se demostró
un error de cantidad por una página de vidrio con «1 piezas»: puede referirse al
tipo de pieza, a una unidad o a una agrupación. Son problemas de comprensión y
alcance que hay que aclarar antes de cambiar números.

## Antes, después y motivo

La tabla aplica la revisión de diseño de `emil-design-eng` a tareas concretas.

| Before | After | Why |
|---|---|---|
| Crear proyecto, completar cliente y después buscar cómo añadir. | Nueva obra → biblioteca visual o primer dibujo. | Permite empezar por lo que el profesional sabe hacer. |
| Seis fases y numerosas pestañas antes de las ventanas. | Ventanas primero; estado y siguiente acción en cabecera compacta. | Mantiene el objeto de trabajo a la vista. |
| Repetir vidrio/color/serie por ventana. | Defaults de obra con excepciones indicadas y edición múltiple. | Reduce errores y trabajo repetitivo. |
| Elegir nombres de aperturas en listas extensas. | Elegir sobre el paño con miniatura animable y vista declarada. | Facilita reconocer el resultado sin memorizar terminología. |
| 3D pequeño, nogal plano y encuentros rectos. | Encuadre generoso, juntas y veta por perfil. | Hace visible el oficio y la calidad física. |
| IA con modos y trámite para un cambio de ancho. | «Ancho actualizado» + diferencia útil + Deshacer. | La asistencia debe ahorrar pasos. |
| Excel o formulario de filas para entender el catálogo. | PDF → preparación → mapa del sistema → dudas puntuales. | Traslada el trabajo de organización a la aplicación. |
| Modal de códigos de material. | Dibujo y material se resaltan entre sí; totales con alcance. | Permite verificar y aprender sin adivinar códigos. |
| PDF con portada vacía y dibujo pequeño. | Propuesta con imágenes legibles, precios y condiciones ordenadas. | El documento vende y aclara lo acordado. |
| Código largo colocado encima de cada pieza. | Número de llamada corto + tabla de correspondencia. | Evita cortes y conserva trazabilidad. |
| 140+ tareas repetidas en Hoy. | Un grupo por causa/obra, con alcance y resolución por lote. | Una lista larga no equivale a priorización. |
| Comprar cero junto a faltantes. | Faltantes accionables primero; cubierto por stock agrupado. | Hace visible la decisión de compra. |
| Mensajes «requisitos congelados». | «Material de la revisión B · 4 ventanas». | Comunica significado y contexto. |

## Lo que ya existe y conviene aprovechar

- Motor determinista y formatos Decimal; identidad de posición/pieza/unidad.
- Revisión emitida inmutable, trazas y autoridad de catálogo.
- Operaciones compartidas para edición y asistente; trabajos recuperables.
- Herencia y selección de dos caras de acabado en partes del modelo.
- Renderer 2D con lógica de aperturas, acoples y uniones; no empezar de cero.
- Carga de materiales/texturas y escena compartida entre 3D y miniaturas.
- Corte con barras, ángulos, secuencia y balance; etiquetas con QR e identidad.
- Virtualización y búsquedas: cuatro filas renderizadas no significan que faltan
  las otras posiciones de una obra grande.
- Roles, RLS y separación de costos: simplificar el menú no concede permisos.
- El flujo de documentos y de producción ya contiene más información útil que la
  que su composición visual permite aprovechar.

## Inventario de quitar, mover, simplificar y añadir

| Tratamiento | Elementos | Condición |
|---|---|---|
| Quitar de la experiencia habitual | Selector de tema, modos Preguntar/Agente, detalle de jobs técnicos en cambios triviales, duplicación de upload, avisos genéricos repetidos. | Conservar acceso de diagnóstico cuando sea útil. |
| Mover de lugar | Trazas, hashes, IDs largos, autoridad detallada, overrides, versiones antiguas y configuración industrial. | Accesibles desde Detalles técnicos, historial o ajustes del responsable. |
| Simplificar | Cabecera de proyecto, biblioteca, inspector, acabados, preparación de cotización, compras y tableros. | Mantener resultado/alcance/recuperación claros. |
| Añadir o elevar | Defaults por obra, acciones por lote, vínculo dibujo↔material, importación PDF real, visor de documento, callouts, muestra de veta y cola agrupada. | Aprovechar primero capacidades existentes y completar las que falten. |
| Mantener | Cálculo, permisos, fuentes, inmutabilidad, confirmación de consecuencias externas y precisión industrial. | Nunca convertir «simple» en fabricar o cobrar sobre suposiciones. |

## Cobertura de todo el sistema

La cobertura de planificación es integral; la profundidad de observación no fue
idéntica en todos los módulos. Esta tabla evita equiparar una lectura con una
prueba operativa.

| Dominio | Base usada en este estudio | Tratamiento dentro del plan |
|---|---|---|
| Acceso, empresa y onboarding | Código/wiki/reporte H; acceso real a dos roles V | Alta progresiva, datos mínimos, roles por tarea, conexión avanzada posterior. |
| Hoy y navegación | V/C | Priorizar causas, agrupar trabajo, nombres consistentes y menú por rol. |
| Clientes | C/H; enlaces desde proyecto V | Buscar/crear breve, historial comercial útil y dirección cuando se usa. |
| Obra/proyecto/posiciones | V/C | Ventanas primero, defaults, duplicar, ordenar, agrupar por recinto y lote. |
| Editor y conjuntos | V/C; modelo y capacidades H | Manipulación directa, selección, cotas, aperturas, conjunto y especialista. |
| Vidrio, herraje y accesorios | Inspector V/C; dominios H | Recetas elegibles, presets, opciones compatibles y efecto visible. |
| Vano/medición/térmica | C/H; alertas V | Separar cotización de levantamiento; preguntar por dato con consecuencia. |
| 2D/3D/planos | V/C/D | Capas de lectura, juntas y materiales coherentes. |
| Catálogos/importación | Importador V; pipeline C; histórico H | PDF principal, análisis multimodal y revisión por excepción. |
| Precio/costo/margen | Precio en editor/IA V; C/H | Precio explicado, lote y comparación; costos según permisos. |
| Cotización/PDF | PDF existente D; flujo C/H | Vista previa, composición comercial y emisión separada del envío. |
| Portal y acuerdo | Código/wiki/reporte H | Mismo producto/revisión, aceptación legible y móvil. No se ejecutó aceptación. |
| Cobros/fiscal/plataforma | C/H | Próximo cobro, estado externo verificado y administración secundaria. No se probó pago ni emisión fiscal. |
| Producción, corte y etiquetas | V/C/D | Cola por trabajo, estación y dibujo; conservar exactitud y QR. |
| CNC/máquinas | C/H | Área especialista, capacidad real, preview físico y exportación humana. No se operó una máquina. |
| Compras/inventario | V/C | Faltantes, agrupación por variante/unidad, proveedor y recepción práctica. |
| Despacho/postventa | C/H | Preparar carga, escanear, entrega y seguimiento con evidencia. |
| Terreno | Estado vacío V; capacidad C/H | Agenda por rol, medición móvil y sincronización comprensible. |
| Analítica | C/H | Preguntas de negocio, desvíos accionables y definición de cada dato. |
| IA/jobs/correo | Una petición V; C/H | Una entrada contextual, resumen, recuperación y envío humano. |
| Ajustes y permisos | C/H; sesión manager V | Agrupar configuración por tarea y responsable; conservar autorización backend. |

## Límites que la ejecución debe cerrar

No se verificaron de forma nueva: responsive del editor, uso real con guantes,
lector QR físico, móvil sin red, catálogo comercial completo, todas las familias
de apertura, máquina CNC, experiencia íntegra del dueño con MFA, envío de correo,
pago, tributación y acuerdo real de cliente. Se incluirán en la campaña final
solo con recursos y conexiones reales apropiados; un sandbox no los acredita.

No hay tiempos de tarea, tasas de éxito ni satisfacción medidos formalmente en
esta auditoría. Los objetivos de [ejecución](07-ejecucion.md) son metas futuras.

## Anclajes de código para retomar sin redescubrir

| Tema | Entrada en el repositorio |
|---|---|
| Menú por permiso de lectura | `frontend/src/app/navigation.ts` |
| Metadatos y cabecera de proyecto | `frontend/src/features/projects/ProjectPages.tsx` |
| Nueva posición | `frontend/src/features/projects/ProjectPositionLibrary.tsx` |
| Editor e inspector | `frontend/src/features/canvas/AssemblyEditor.tsx`, `frontend/src/features/inspector/` |
| SVG de producto | `frontend/src/features/canvas/ProductFrontSvg.tsx` |
| Perfil, geometría y acabado 3D | `Product3DScene.ts`, `scene3dGeometry.ts`, `finishMaterials3d.ts` en `frontend/src/features/canvas/` |
| Interfaz de importación | `frontend/src/features/catalogs/CatalogImportsPanel.tsx` |
| Ingesta real de catálogo | `backend/ingest/catalog_service.py:238`, `catalog_ai.py:75`, `extract.py:60` |
| Transporte multimodal compartido | `backend/ai_gateway/service.py`, `providers.py:336`, `multimodal.py` |
| OCR de posiciones, otro camino | `backend/ingest/service.py` |
| Contrato IA | `backend/ai_gateway/prompts/agent-v2.md`, `frontend/src/features/assistant/` |
| Cotización/documentos | `backend/documents/quotation.py`, `drawing.py`, `renderers.py`, `service.py`, `artifacts.py` |
| Documentos de taller | `backend/production/pack.py:298`, `cut_pack.py`, `cut_documents.py`, `cut_labels.py` |

Las rutas se verificaron en el ref indicado. Los números de línea pueden cambiar
durante la implementación; buscar el símbolo antes de editar.
