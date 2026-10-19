# Referencias de ingeniería: Logikal, SchüCal, V6 Advantage y A+W Cantor

Fecha de consulta: **18 de octubre de 2026**. Informe parcial de la investigación competitiva de DEKOPEN; cubre cuatro suites de ingeniería y fabricación. No modifica el producto ni constituye una recomendación de compra.

## Alcance y calidad de la evidencia

Se consultaron páginas del fabricante, manuales operativos, fichas, formación y casos publicados por el proveedor. Las funciones se atribuyen al producto y módulo indicado; una integración, un desarrollo futuro y una instalación concreta no se convierten en una función universal de la licencia base.

- **DOC**: documentado en una fuente oficial consultada. Un procedimiento del manual sigue siendo DOC: no ejecutamos el programa.
- **OBS**: observado directamente en una ejecución identificable del producto. **Este informe no contiene observaciones OBS** ni una prueba instalada de estas cuatro suites.
- **NV**: no verificado con la evidencia reunida. No significa que la función no exista.
- **Propuesta DEKOPEN**: interpretación de diseño, separada de las capacidades del competidor. No autoriza fórmulas, coeficientes ni compatibilidades de fabricación.

Los intentos de captura del buscador devolvieron el marcador textual `<<ImageDisplayed>>`, sin píxeles inspeccionables. Por tanto, las referencias visuales de este documento son **localizadores de evidencia**, no evaluaciones de contraste, legibilidad o calidad visual. La captura y observación visual con navegador/REA corresponde al informe principal. No se decompilaron estas aplicaciones ni se inspeccionaron sus bases privadas. No se accedió a cuentas de fabricantes.

Las fuentes actuales se consultaron el 18-10-2026; cuando no existe fecha editorial se indica «s/f». Las fuentes de 2013, 2017, 2022 y 2023 se conservan como antecedentes fechados. El upload de un PDF en 2024 no actualiza una interfaz descrita en 2022. Los precios, licencias y disponibilidad varían por mercado; no se inventa una tarifa pública.

## Rúbrica común de 18 ejes

Esta rúbrica no asigna una puntuación numérica a una demo que no se ha usado. Cada casilla responde qué se sabe, de qué módulo y qué falta comprobar. El JSON compañero conserva además 24 dimensiones para cruzar el conjunto de competidores.

| Eje | Pregunta de evaluación y evidencia deseable |
|---|---|
| 1. Entrada y onboarding | ¿Quién prepara datos, clientes, empresa y reglas? ¿Se distingue comenzar una cotización de publicar un sistema técnico? |
| 2. Marcas, series y catálogos | ¿Se entiende la pertenencia fabricante → sistema/serie → artículo, su versión, imágenes y validez? |
| 3. Editor y aperturas | ¿Las hojas, manos, sentidos, campos y acoples tienen significado físico y restricciones? Hace falta probar el cambio de apertura. |
| 4. 2D y 3D | ¿Elevación, sección, configuración y representación 3D comparten los mismos datos? Una imagen comercial no prueba sincronización. |
| 5. Materiales | ¿Vidrio, perfiles, juntas, herrajes y acabados generan una lista trazable y compatible? |
| 6. Precios | ¿Se distinguen costo, lista, descuento, margen y permiso de lectura? La existencia de un precio no prueba privacidad. |
| 7. Presupuestos y PDF | ¿El documento comunica la configuración y las condiciones? ¿Se separa propuesta comercial de información de taller? |
| 8. Corte y retazos | ¿Se optimizan barras y se conoce el origen, longitud, cantidad y destino de los sobrantes? Optimizar no equivale a reservar inventario. |
| 9. Compras y stock | ¿Necesidad, orden, recepción, devolución y disponibilidad mantienen continuidad? |
| 10. Taller y CNC | ¿La información depende de la estación y de la máquina real? ¿Qué requiere módulo, postprocesador y validación? |
| 11. QR y terreno | ¿Se diferencia etiqueta de fabricación, pasaporte de unidad, despacho e incidencia de instalación? |
| 12. IA | ¿Existe una función concreta entregada? ¿Es asistente, regla, visión, sugerencia o ejecución? Una promesa «AI-ready» no prueba un agente. |
| 13. Historial y deshacer | ¿Se conserva conversación, versión de diseño, evento operativo y recuperación? Son historiales diferentes. |
| 14. Roles | ¿Qué puede ver y ejecutar cada persona? Los canales distribuidor/fábrica no demuestran por sí solos la seguridad de los permisos. |
| 15. Claridad visual | ¿Qué pantalla y contexto muestra el fabricante? Para puntuar jerarquía, densidad, color y foco se requieren píxeles y tareas observadas. |
| 16. Teclado y móvil | ¿Qué tareas están optimizadas para teclado y qué versión móvil existe? «Web» no acredita paridad móvil. |
| 17. Interoperabilidad | ¿Qué dato cruza cada interfaz, en qué dirección y con qué revisión humana? |
| 18. Madurez y precio | ¿Hay documentación, formación y casos? ¿Qué módulos y costos quedan por confirmar? Madurez documental no acredita ajuste al taller chileno. |

## 1. Orgadata / Forterro — Logikal

**Papel en la comparación.** Referencia de configuración técnica mult proveedor, estimación y preparación de fabricación. La documentación pública permite reconstruir operaciones concretas, sobre todo aperturas, fases de entrada e historial. Su interfaz de escritorio y extensión MES deben evaluarse separadamente. El producto no se reduce a una galería 3D.

### Fuentes primarias

Todos los enlaces de esta tabla se consultaron como texto oficial; s/f salvo indicación. Los IDs se usan también en el JSON.

| ID | Fuente oficial | Qué respalda |
|---|---|---|
| L01 | [Logikal FAQ](https://www.logikal-software.com/en/faq) | Alcance mult proveedor, estimación, cortes, módulos, exportaciones y modelo comercial sin tarifa verificada. |
| L02 | [Input of elements: user interface](https://help.orgadata.com/en/documentation/input-of-elements/user-interface/) | Dibujo, cinta, pasos/timeline y posibilidad de ocultar controles. |
| L03 | [Insertion selection](https://help.orgadata.com/en/documentation/input-of-elements/windows-and-doors/element/insertion-selection/) | Selección de inserciones/aperturas, búsqueda y selección de varios campos. |
| L04 | [3D view](https://help.orgadata.com/en/documentation/input-of-elements/user-interface/3d-view/) | Vistas interior/exterior, rotación y abrir/cerrar hoja elevadora corredera. Imagen en ruta de agosto de 2026. |
| L05 | [Couplings](https://help.orgadata.com/en/documentation/input-of-elements/windows-and-doors/grid/couplings/) | Acople elegido en la cuadrícula, representación en elevación y sección. |
| L06 | [Glazing](https://help.orgadata.com/en/documentation/input-of-elements/windows-and-doors/glazing/glazing/) | Relleno por campo, espesor, junquillo, acabados, datos de la selección y favoritos. |
| L07 | [System articles](https://help.orgadata.com/en/documentation/database/system-articles/) | Proveedor, artículo, dibujo, datos, colores, precios y longitudes. |
| L08 | [Commercial and technical article data](https://help.orgadata.com/en/documentation/dataservices/customised-databases/commercial-and-technical-article-data/) | Plantilla de importación, unidades, embalaje, largos y datos técnicos. |
| L09 | [Customized databases: requirements](https://help.orgadata.com/en/documentation/dataservices/customised-databases/requirements/) | Alcance que se debe acordar al preparar una base técnica. |
| L10 | [Discount groups](https://help.orgadata.com/en/documentation/estimation-and-labour-hours/estimation/estimation-data/discount-groups/) | Factores, descuentos y tratamiento comercial por grupo. |
| L11 | [Printouts](https://help.orgadata.com/en/documentation/printouts/) | Familias de informes comerciales, compras y fabricación. |
| L12 | [Material analysis](https://help.orgadata.com/en/documentation/printouts/estimation-printouts/material-analysis/) | Cantidades, dibujos de artículos, sobrantes y opciones de presentación. |
| L13 | [Residual lengths](https://help.orgadata.com/en/documentation/project-centre/article-options/residual-lengths/) | Introducir/editar sobrantes del proyecto e importar por Excel. |
| L14 | [Position history](https://help.orgadata.com/en/documentation/project-centre/position-history/) | Estados, historial automático opcional y recuperación como nueva posición. |
| L15 | [User settings](https://help.orgadata.com/en/documentation/settings/user/) | Perfiles, permisos y acceso a estimación, proyectos y CNC. Parte del texto dice estar en revisión. |
| L16 | [Keyboard shortcuts and combinations](https://help.orgadata.com/en/documentation/project-centre/keyboard-shortcuts-and-combinations/) | Atajos del centro de proyectos y de entrada. |
| L17 | [SimplyTag](https://help.orgadata.com/en/documentation/simplytag/) | QR de unidad, documentos/servicio, identidad y acceso móvil/web. |
| L18 | [Saw setup](https://help.orgadata.com/en/documentation/cnc/machine-setup/saw-setup/) | Configuración concreta de sierra; el manual no sustituye la formación. |
| L19 | [ERP export via MDB](https://help.orgadata.com/en/documentation/interfaces/erp/erp-export-via-mdb/) | Contrato de exportación heredado y advertencia de posible sobrescritura de dibujos. |
| L20 | [Create projects](https://help.orgadata.com/en/documentation/project-centre/create-projects/) | Datos de cliente, cabecera, referencias y condiciones del proyecto. |

### Evaluación por los 18 ejes

| Eje | Evidencia y límite | Implicación para DEKOPEN |
|---|---|---|
| 1. Entrada y onboarding | **DOC.** El centro de proyectos recoge cliente y referencias antes de las posiciones [L20]. Preparar una base técnica exige delimitar cálculo, documentación y fabricación [L09]; no equivale a subir un PDF. No se midió el tiempo hasta la primera cotización. | Dos recorridos claros: vender con un catálogo publicado y preparar/verificar un catálogo nuevo. |
| 2. Marcas/series/catálogos | **DOC.** En artículos se elige proveedor; lista, dibujo y datos quedan asociados [L07]. La importación diferencia código, unidad, embalaje y largo de barra [L08]. No se verificó que la taxonomía de cada proveedor coincida con Proline 60/70. | Marca y serie deben ser dueñas visibles de sus artículos y fuentes; una miniatura sola no demuestra aptitud técnica. |
| 3. Editor/aperturas | **DOC.** Tras la cuadrícula aparece la selección de inserciones. Hay búsqueda, selección múltiple y tipos como oscilobatiente, pivotante, corredero y puerta [L03]. Los acoples se añaden al perfil elegido [L05]. No se probaron reglas ni geometrías. | Paleta por compatibilidad real y lectura de mano/sentido; separar apertura de marco y acople. |
| 4. 2D/3D | **DOC.** El manual ofrece elevación/sección del acople [L05] y vista 3D orientable, interior/exterior y apertura/cierre de elevadora corredera [L04]. No hay aquí prueba de sincronización bajo edición, velocidad ni fidelidad de todas las tipologías. | Inspección física coherente, con controles de vista y movimiento identificables. |
| 5. Materiales | **DOC.** La fase de acristalamiento selecciona por campo, espesor y junquillo; presenta datos de ese relleno y admite favoritos [L06]. El análisis de material agrupa perfiles, herrajes, vidrio y otros componentes [L12]. | Inspector contextual y lista de materiales vinculada a la selección y a la revisión. No copiar fórmulas del competidor. |
| 6. Precios | **DOC.** Factores/descuentos por grupo y condiciones de proyecto están documentados [L10]; los permisos distinguen acceso a cálculo/estimaciones protegidas [L15]. No se auditó la autorización real ni la separación SaaS por empresa. | Vista comercial simple con costo/margen privado según rol; explicar precio aplicado y vigencia. |
| 7. Presupuestos/PDF | **DOC.** Los informes se separan entre venta, compras y fabricación [L11]. El análisis permite elegir detalle, dibujos y exposición de precios [L12]. La FAQ enumera PDF, Word y Excel [L01]. No se verificó aceptación de cliente o inmutabilidad de emisión. | Un presupuesto comunica; una hoja de taller instruye. No poner todos los documentos en una lista indiferenciada. |
| 8. Corte/retazos | **DOC.** La FAQ describe optimizar con barras/sobrantes [L01]. El proyecto permite registrar artículo, cantidad y largo residual e importar Excel [L13]. El manual específico de optimización de cortes está «under construction»; no demuestra el algoritmo ni la reserva global. | Explicar de qué inventario sale cada barra y qué sobrante físico se genera. No confundir un resultado calculado con stock reservado. |
| 9. Compras/stock | **DOC parcial.** Hay informes de pedido por tipo [L11], opciones de stock en artículo [L07] y exportación ERP [L19]. No se comprobó un ciclo completo de recepción, reserva, devolución y conciliación dentro de la misma licencia. | Distinguir necesidad, pedido y existencia disponible, y declarar la autoridad de cada cantidad. |
| 10. Taller/CNC | **DOC.** La sierra tiene configuración específica [L18]. MES aparece como extensión de operación del taller [L01]. Permisos separan crear archivos CNC [L15]. No se validó ninguna máquina ni postprocesador. | Solo ofrecer exportación o envío para adaptadores y revisiones validados; pantalla de estación enfocada en la operación actual. |
| 11. QR/terreno | **DOC.** SimplyTag vincula una unidad acabada con información, documentos y servicio; requiere identidad ORGADATA y dispone de acceso móvil/web [L17]. Es distinto del código de barra de producción. No se verificaron incidencias/instalación de extremo a extremo. | Mostrar para qué sirve cada código y en qué fase del ciclo se usa. |
| 12. IA | **NV.** Las fuentes consultadas no establecen un chat que navegue y ejecute tareas con políticas de aprobación. Restricciones de catálogo y cálculo automático no son evidencia de LLM. | Diseñar IA con operaciones tipadas y resultado verificable; no anunciar ventaja exclusiva frente a un mercado no auditado completo. |
| 13. Historial/deshacer | **DOC.** El historial opcional puede registrar cada cambio con comentario; una versión anterior se importa como **posición independiente** [L14]. «Frozen» bloquea edición mientras ese estado se mantiene, pero el estado es modificable. No demuestra emisión irrevocable ni historial de conversación. | Recuperación que preserve el original, versiones reconocibles y conversación persistente como responsabilidad aparte. |
| 14. Roles | **DOC parcial.** Perfiles heredados y permisos por usuario incluyen estimación, base propia, proyectos y CNC [L15]. El texto revisa parte de la matriz. No se probó seguridad ni aislamiento de organizaciones. | Presentar permisos de lectura y ejecución por dominio; verificar privacidad en servidor, no inferirla por esconder controles. |
| 15. Claridad visual | **DOC de estructura; NV de calidad visual.** Dibujo, cinta, máscaras y timeline tienen responsabilidades distintas y se pueden ocultar controles [L02]. Falta inspeccionar captura y usar tareas para valorar densidad y legibilidad. | Mantener orientación por fase y espacio para el lienzo; no copiar literalmente una cinta de escritorio. |
| 16. Teclado/móvil | **DOC.** Hay atajos para copiar, insertar, renombrar y controlar la entrada [L16]. SimplyTag es móvil [L17]. No hay prueba de que el editor completo de escritorio tenga paridad táctil. | Teclado para operaciones frecuentes del diseñador; móvil enfocado en consulta, medición y registro contextual. |
| 17. Interoperabilidad | **DOC.** La FAQ diferencia integraciones/módulos [L01]; MDB documenta opciones de salida y una advertencia de sobrescritura de archivos de dibujo [L19]. No equivale a API transaccional universal. | Cada exportación debe indicar formato, revisión, destino y compatibilidad; identidad de artefacto que evite sobrescrituras. |
| 18. Madurez/precio | **DOC.** Existe un corpus operativo público extenso y distribución por módulos/catálogos [L01–L20]. **NV** importe de licencia, implantación chilena, mantenimiento y costo total. | Comparar costo de catálogo, parametrización, capacitación y conectores; no solo licencia mensual. |

### Dos flujos operativos reconstruidos

**L-F1 — Configurar y cotizar. DOC; no ejecutado.** Crear proyecto y cliente [L20] → definir cuadrícula → escoger inserción válida por campo [L03] → acoplar si corresponde [L05] → elegir rellenos y junquillos [L06] → aplicar condiciones comerciales [L10] → generar propuesta desde los informes de venta [L11]. Los pasos exactos y dependencias pueden cambiar por sistema/módulo. La referencia útil es que la elección física precede al presupuesto.

**L-F2 — Preparar fabricación. DOC; no ejecutado.** Registrar/importar largos residuales de artículos del proyecto [L13] → revisar cantidades y detalle del análisis [L12] → optimizar con stock/retazos según el alcance declarado en la FAQ [L01] → emitir documentación y datos de máquina configurada [L11,L18] → usar MES cuando esté contratado [L01]. SimplyTag [L17] acompaña la unidad en uso/servicio; no se supone que sea el mismo proceso que la etiqueta de corte. Reserva física, retorno al almacén y conexión con toda máquina quedan pendientes de prueba.

### Referencias visuales y formación

| Referencia oficial | Localizador exacto | Qué permite investigar, sin atribuir observación visual |
|---|---|---|
| Editor por fases | [Manual de interfaz](https://help.orgadata.com/en/documentation/input-of-elements/user-interface/) | Organización de dibujo, cinta y timeline; capturar página y pantallas embebidas. |
| Aperturas | [Insertion selection](https://help.orgadata.com/en/documentation/input-of-elements/windows-and-doors/element/insertion-selection/) | Relación entre icono, tipo y campo seleccionado. |
| 3D, referencia prioritaria | [Manual 3D](https://help.orgadata.com/en/documentation/input-of-elements/user-interface/3d-view/) y [PNG oficial](https://help.orgadata.com/en/wp-content/uploads/sites/2/2026/08/EN-2026-3D-Ansicht001.png.pagespeed.ce.MyVfsHuKPk.png) | Orientaciones y controles de inspección. No puntuar fotorrealismo sin observar los píxeles. |
| Datos de artículo | [System articles](https://help.orgadata.com/en/documentation/database/system-articles/) | Jerarquía proveedor/lista/dibujo/datos. |
| Tour | [FAQ con enlace Demo Tour](https://www.logikal-software.com/en/faq) | Candidato a exploración guiada posterior; no completado en esta investigación. |

**Pendientes decisivos.** Prueba de 5 cambios de apertura con el mismo sistema; comparar 2D/3D/BOM después de cada cambio; recuperar versión y verificar identidad; recorrer un retazo hasta su reutilización; cotizar implantación y catálogo local. No hay video visto con tiempos verificables.

## 2. Schüco — SchüCal y su ecosistema

**Papel en la comparación.** Referencia de continuidad entre un sistema de fabricante, oficina, taller y terreno. Es esencial no atribuir a SchüCal todo el portafolio: **PolyCal** se presenta para PVC; FDC, MES, mobile, IoF y CNC tienen funciones y condiciones propias. JANIsoft se menciona solo como referencia de Jansen/acero, con evidencia histórica diferenciada.

### Fuentes primarias

| ID | Fuente oficial y fecha | Qué respalda |
|---|---|---|
| S01 | [SchüCal, España](https://www.schueco.com/es/fabricantes/soluciones-digitales/schuecal), s/f | Sistemas Schüco, cálculo/pedidos, licencias y conexiones. |
| S02 | [SchüCal, DE-EN](https://www.schueco.com/de-en/fabricators/digital-solutions/schuecal), s/f | Connect con revisión de carrito, MCo, FDC, IoF, interfaz ERP y GWP/EPD. |
| S03 | [Fabrication Data Center](https://www.schueco.com/uk/fabricators/digital-solutions/fabrication-data-center), s/f | Documentación de estación, barcode, 3D y FDC mobile. |
| S04 | [SchüCal MES](https://www.schueco.com/de/verarbeiter/digitale-loesungen/schuecal-mes), s/f | Secuencia de estaciones, incidencias e implantación. **Texto indexado consultado; apertura directa fallida.** |
| S05 | [SchüCal mobile](https://www.schueco.com/de-en/fabricators/digital-solutions/schuecal-mobile), s/f | Medir, fotos, cambios de cotas y sincronización con oficina. |
| S06 | [Docu Center](https://www.schueco.com/uk/specifiers/digital-solutions/docu-center), s/f | Recursos CAD/PDF organizados por sistemas y acceso web/móvil/offline. |
| S07 | [PolyCal, España](https://www.schueco.com/es/fabricantes/soluciones-digitales/polycal) y [Alemania](https://www.schueco.com/de/verarbeiter/digitale-loesungen/polycal), s/f | Producto específico para PVC; cálculo, documentación y fabricación. |
| S08 | [Digital Solutions in Construction, PDF](https://www.schueco.com/resource/blob/4249866/bd6e3252f6b70a93524d9f7b7ab3d2d1/digital_solutions_brochure_en.pdf?domain=no), fecha editorial no establecida | 34 páginas de PDF; mapa del ecosistema y referencias visuales. Contiene referencias a 2023: no datarlo 2026. |
| S09 | [The future of fabrication](https://www.schueco.com/uk/fabricators/magazine/the-future-of-fabrication), s/f | Automatización de maquinaria y continuidad de datos en fabricación. |
| S10 | [VX 800](https://www.schueco.com/de-en/fabricators/machinery/cnc-maschinen/cnc-machining/vx-800), s/f | Red con SchüCal y alcance concreto de máquina. |
| S11 | [Tutoriales oficiales SchüCal](https://youtube.com/playlist?list=PL1bRABLS_JWyI3pZJK_pcKyXL6v88PR6G), fecha/duración NV | Enlace obtenido del sitio oficial; acceso a reproducción no completado, videos no vistos. |
| S12 | [Licencias en My Workplace](https://www.schueco.com/uk/fabricators/my-workplace/software), autenticado | Redirección a SSO; precio y matriz completa no accesibles públicamente en esta consulta. |
| S13 | [Manual JANIsoft/SchüCal, PDF](https://www.jansen.com/servicepack/Homepage/KEY-USER/Template/JANIsoft-Schulung_Dokumentation_IT.pdf), junio de **2013** | Solo extracto indexado; apertura fallida. Contexto histórico, no interfaz actual. |
| S14 | [Jansen CNC AF 510](https://www.jansen.com/en-us/building-systems-profile-systems-steel/services-steel-systems/processing/machine-range/detail/cnc-af-510.html), s/f | JANIsoft genera datos para esa máquina; SchüCam como visualización de mecanizado. |

### Evaluación por los 18 ejes

| Eje | Evidencia y límite | Implicación para DEKOPEN |
|---|---|---|
| 1. Entrada/onboarding | **DOC.** Sistemas del fabricante y actualizaciones por service packs reducen la preparación técnica para el usuario Schüco [S01]. No se verificó onboarding autoservicio ni migración de una empresa con marcas mixtas. | Con catálogo validado, comenzar por proyecto/producto; publicar un sistema sigue siendo trabajo técnico separado. |
| 2. Marcas/series/catálogos | **DOC.** La autoridad es el ecosistema Schüco [S01]; Docu Center organiza documentación por grupos de sistema [S06]. PVC se comunica en PolyCal [S07]. No se acredita importación genérica mult marca. | Enseñar pertenencia de marca y familia material; Proline y Vinhaus no deben mezclarse en una lista de series sin dueño. |
| 3. Editor/aperturas | **DOC de alcance; NV de interacción.** La página enumera ventanas, puertas, correderas, plegables y fachadas [S01]. No se probó selector, sentido, carril ni manilla; la amplitud comercial no demuestra una apertura concreta correcta. | Probar la operación que hoy falla en DEKOPEN; no cerrar el problema porque exista un icono o un nombre. |
| 4. 2D/3D | **DOC.** SchüCad next y FDC cubren dibujo/visualización en el ecosistema [S01,S03]. FDC muestra mecanizado en 3D. **NV** render comercial fotorrealista y animación física de cada apertura dentro de SchüCal base. | Separar representación de venta de inspección técnica de fabricación, conservando la misma revisión. |
| 5. Materiales | **DOC.** SchüCal calcula material y tiempos; sus service packs siguen al sistema [S01]. PolyCal documenta colores/herrajes/accesorios y restricciones para PVC [S07]. No transferir reglas Schüco a otros proveedores. | Materiales compatibles por serie/familia, con fuente y vigencia. |
| 6. Precios | **DOC parcial.** SchüCal estima/cotiza [S01]; mobile permite consultar detalles de cálculo [S05]. **NV** matriz de costo/margen privado, descuentos del distribuidor y permisos efectivos. | Un acceso móvil no debe implicar que cualquier operario vea el costo de compra. |
| 7. Presupuestos/PDF | **DOC.** Cálculo y pedidos se comunican junto a documentos de sistema [S01,S06]. Se documenta generación de EPD/GWP en el alcance actual [S02]. No se inspeccionó un presupuesto emitido, versiones o aceptación del cliente. | Documento comercial y anexo técnico con fuentes/revisión; no decorar una cifra ambiental sin autoridad. |
| 8. Corte/retazos | **DOC parcial.** Hay optimización en el contexto de fabricación/máquina [S09,S10]; PolyCal enumera documentación de corte [S07]. **NV** libro de retazos reutilizables y reserva por ubicación. | La conexión de sierra no sustituye la trazabilidad de barra/retazo que necesita un taller. |
| 9. Compras/stock | **DOC.** La lista de materiales pasa a Connect como carrito/marcador para que el usuario revise/procese [S02]. **NV** almacén completo y recepción dentro de SchüCal base. | Una acción «preparar pedido» debe desembocar en una revisión identificable antes de comprar. |
| 10. Taller/CNC | **DOC.** FDC adapta información al puesto [S03]; MES documenta precedencia entre estaciones y registro de fallos [S04, indexado]. MCo es adicional [S02]. AF510 pertenece al caso JANIsoft/Jansen [S14]. Ningún caso prueba soporte de cualquier CNC. | Taller por estación, trabajo habilitado por estado y datos de máquina explícitos. |
| 11. QR/terreno | **DOC.** IoF asocia QR/NFC, unidad, documentos y mantenimiento; véase folleto [S08]. Mobile registra cotas y fotos de situación [S05]. Barcode FDC identifica perfiles [S03]. Son tres tareas relacionadas, pero diferentes. | Un código responde una pregunta concreta: qué fabricar, qué unidad es o qué incidencia registrar. |
| 12. IA | **NV.** Las fuentes consultadas no prueban un agente conversacional que edite/navegue. Expresiones promocionales de software inteligente no establecen LLM ni autonomía. | Exigir un flujo observable, proveedor actual y registro de operaciones antes de considerar IA entregada. |
| 13. Historial/deshacer | **NV.** Información actualizada en FDC y sincronización mobile [S03,S05] no demuestran historial de versiones recuperable, deshacer transaccional ni conversación persistente. | Versiones, acciones y chat requieren pruebas propias; «sincronizado» no significa «recuperable». |
| 14. Roles | **DOC de separación funcional; NV de permisos.** Oficina, FDC de taller y mobile se orientan a tareas distintas [S03,S05]. No se accedió a administración ni se auditó control de precios/órdenes. | Diseñar la pantalla del operario según su tarea, con permisos comprobados en backend. |
| 15. Claridad visual | **DOC de arquitectura; NV de calidad.** El folleto separa aplicaciones y puntos de transferencia [S08]. No se han inspeccionado aquí los píxeles ni medido contraste o descubribilidad. | Referencia de separación por rol y fase; no afirmar superioridad estética sin tarea visual observada. |
| 16. Teclado/móvil | **DOC.** SchüCal mobile permite levantamiento y conexión con oficina [S05]; FDC mobile cubre otros contextos [S03]. **NV** atajos actuales y paridad del editor de oficina en teléfono. | Móvil con fotos, medición y avance; escritorio con diseño de precisión y teclado. |
| 17. Interoperabilidad | **DOC.** Hay interfaces SchüCad next, FDC, E.R.Plus y Connect [S01,S02]. La dirección/confirmación de Connect está descrita, pero contratos API y soporte por licencia requieren comprobación. | Hacer visible el dato y estado de cada transferencia y evitar que un enlace aparente una integración operativa. |
| 18. Madurez/precio | **DOC.** Ecosistema modular, formación y documentación oficial [S01,S08,S11]. Tres niveles de licencia nombrados en España [S01]. **NV** importes; el detalle consultado está tras SSO [S12]. | Cotizar módulos y disponibilidad regional; no asumir que el alcance de varios países es idéntico. |

### Dos flujos operativos reconstruidos

**S-F1 — Oficina a compra. DOC; no ejecutado.** Elegir sistema Schüco → configurar elemento → calcular materiales/tiempos y presupuesto [S01] → transferir la necesidad a Connect → usuario revisa carrito/marcador y continúa compra [S02]. La revisión comercial es explícita; transferir la lista no significa emitir automáticamente una orden irrevocable.

**S-F2 — Oficina a taller y terreno. DOC; no ejecutado.** Transferir datos al FDC → identificar elemento/perfil con código y consultar información del puesto [S03] → secuenciar pasos de MES y registrar defecto, según la descripción indexada [S04] → consultar/actualizar medidas y fotos desde mobile [S05]. IoF conserva identidad/documentos de la unidad [S08]. Es una composición de productos, no una única pantalla ni una licencia base probada.

### Referencias visuales y formación

Páginas de PDF indicadas como **número humano, desde 1**, no índice cero. Las páginas impresas del folleto son diferentes porque cada página del archivo suele ser una doble página.

| Referencia | Localizador | Uso y límite |
|---|---|---|
| SchüCal, prioridad | [Folleto oficial](https://www.schueco.com/resource/blob/4249866/bd6e3252f6b70a93524d9f7b7ab3d2d1/digital_solutions_brochure_en.pdf?domain=no), **PDF p15**, impresas 23–24 | Panorama/pantalla SchüCal como candidato a captura; fecha editorial NV. |
| Conexiones | Mismo PDF, **p16**, impresas 25–26 | Diagrama de límites entre sistemas. |
| Dibujo CAD | Mismo PDF, **p18**, impresas 29–30 | SchüCad next; no atribuir esta aplicación a SchüCal base. |
| Taller | Mismo PDF, **p25**, impresas 43–44; **p26**, impresas 45–46 | FDC y FDC mobile: comparar tareas por dispositivo. |
| Secuenciación | Mismo PDF, **p27**, impresas 47–48 | MES. |
| Identidad de unidad | Mismo PDF, **p29**, impresas 51–52 | IoF QR/NFC y ciclo de vida. |
| Tutoriales | [Playlist oficial](https://youtube.com/playlist?list=PL1bRABLS_JWyI3pZJK_pcKyXL6v88PR6G) | No se pudo reproducir: títulos individuales, duración y timestamps NV. No se afirma haberlos visto. |

**Pendientes decisivos.** Configuración real de una oscilobatiente/corredera y su cambio de mano; licencia para el taller objetivo; prueba de retazos; matriz de permisos y precios; demo de historial recuperable. El manual JANIsoft de 2013 no resuelve estas preguntas actuales.

## 3. Cyncly — Soft Tech V6 / V6 Advantage

**Papel en la comparación.** Referencia de datos de fabricante distribuidos a ventas, configuración visual gobernada y continuidad CPQ→ERP. El **X3D Visualizer anunciado el 25-08-2026** cambia la referencia visual disponible; evaluar solo capturas antiguas de V6 omitiría el producto actual. El ERP V6 Advantage y sus módulos deben separarse del alcance base de CPQ.

### Fuentes primarias

| ID | Fuente oficial y fecha | Qué respalda |
|---|---|---|
| V01 | [V6 Advantage X3D Visualizer](https://www.cyncly.com/resources/news/v6-advantage-visualizer-award), **25-08-2026** | Configurador web 3D gobernado por reglas, componentes y composiciones. Premio descrito por el propio proveedor, no auditado aquí. |
| V02 | [Soft Tech V6 capabilities](https://www.cyncly.com/pt-BR/products/soft-tech-v6/capabilities), s/f | Página oficial que expone texto detallado en inglés: diseño, precios, optimización y alcance ERP/WMS. |
| V03 | [Soft Tech V6 modules](https://www.cyncly.com/en-GB/products/soft-tech-v6/modules), s/f | Deployment, Automation, Shop Drawing, Business Central y ERP como módulos. |
| V04 | [Soft Tech Academy](https://www.cyncly.com/en-GB/products/soft-tech-v6/academy), s/f | Formación para usuarios y desarrolladores de bases técnicas. |
| V05 | [V6 Accreditation, PDF](https://academy.softtech.com/img/Soft%20Tech%20Academy%20V6%20Accreditation.pdf), **2023**, 2 páginas | Currículo: familias, ensamblajes, artículos, precios y grupos. Algunas unidades estaban «in development»: no acreditan entrega actual. |
| V06 | [Datasheet for profile suppliers, PDF](https://wnaymg.files.cmp.optimizely.com/download/assets/WDG%2B-%2BDatasheet%2B-%2BV6%2B-%2BProfile%2Bsuppliers%2B-%2BEN%2BUS.pdf/56b13f8ab5e011f09db95ac263d27420), s/f, 2 páginas | Distribución de reglas/catálogos, BOM, tipologías y documentos. |
| V07 | [Datasheet for fabricators, PDF](https://wnaymg.files.cmp.optimizely.com/download/assets/DataSheet%2BV6%2BAdvantage%2B-%2BWindow%2Band%2BDoor%2BFabricators%2BAPAC%2BA4%2B%2B-%2BEN.pdf/29aa56227ec011f0970f5e1af917a384), s/f, 2 páginas | Cloud/on-premise, datos de proveedores, restricciones y separación ERP. |
| V08 | [AusFenEx 2025](https://www.cyncly.com/en-AU/resources/news/cyncly-ausfenex-2025), **2025** | Contexto de red proveedor/fabricante y dirección «AI-ready». No prueba agente ejecutor. |
| V09 | [Fensterbau Frontale 2026](https://www.cyncly.com/en-HU/resources/news/fensterbau-frontale-2026), **22-01-2026** | Anuncio de demostraciones del conjunto de productos; claims de IA de portafolio no transferibles automáticamente a V6. |
| V10 | [Overview V6, MP4 oficial](https://wnaymg.files.cmp.optimizely.com/download/assets/WDG%2B-%2BOverview%2B3%2B-%2BV6%2BOverview%2B-%2BEN.mp4/b23a65b4512911f09ad1f28d889ce8c1), fecha/duración NV | Enlace de video obtenido del sitio; la herramienta no pudo reproducirlo. No visto. |

### Evaluación por los 18 ejes

| Eje | Evidencia y límite | Implicación para DEKOPEN |
|---|---|---|
| 1. Entrada/onboarding | **DOC.** El proveedor prepara y distribuye datos/reglas [V06]; Academy diferencia usuario y desarrollador técnico [V04]. El currículo 2023 incluye clasificaciones y familias [V05]. No se midió una implantación autoservicio. | Al usuario de ventas se le ofrece configurar con datos listos; la definición del sistema merece herramientas y aprobación propias. |
| 2. Marcas/series/catálogos | **DOC.** El modelo centra el contenido/reglas en el proveedor y su distribución [V06,V03]. Los fabricantes reciben actualizaciones [V07]. No se acredita una galería local de marcas chilenas ni cobertura de Proline/Vinhaus. | Jerarquía de marca/serie con versión y procedencia; la importación debe expresar qué falta validar. |
| 3. Editor/aperturas | **DOC.** La ficha de proveedor enumera batiente, proyectante, corredera, plegable, pivotante y composiciones [V06]. X3D contempla configuraciones acopladas y mismas restricciones que producción según fabricante [V01]. No se ejecutó cambio de apertura/arrastre. | Tipologías reales y composiciones coherentes; probar rutas de edición concretas con el mismo catálogo. |
| 4. 2D/3D | **DOC actual.** X3D web actualiza materiales, vidrio, retícula, herraje y uniones; admite unidades y conjuntos [V01]. Shop Drawing exporta dibujos [V03]. No se midieron latencia, precisión geométrica ni correspondencia de todas las secciones. | La visualización comercial debe responder a la misma configuración que produce la ingeniería; evitar un render decorativo ajeno a BOM. |
| 5. Materiales | **DOC.** BOM dinámica y reglas técnicas de proveedor [V06]; la formación explica ensamblajes, extrusiones, juntas y rellenos [V05, histórico]. No se inspeccionó un resultado de fabricación real. | Mantener identidad de componente y justificación de su presencia en el conjunto. |
| 6. Precios | **DOC.** Capabilities describe listas, descuentos, margen y grupos de cliente [V02]. El currículo cita matrices/grupos [V05]. **NV** privacidad actual entre roles y protección entre empresas. | Costo, margen y precio de venta no deben convivir sin contexto/permisos claros. |
| 7. Presupuestos/PDF | **DOC.** La ficha de proveedor distingue documentos comerciales con marca/condiciones [V06]; Shop Drawing genera PDF [V03]. **NV** portal de aceptación del cliente, versiones emitidas y firma. | Un PDF de venta y un plano de taller son entregables distintos; ambos derivados de revisión identificada. |
| 8. Corte/retazos | **DOC parcial.** Se describen algoritmos lineales y comparar largos de stock antes de comprar [V02]. Automation cubre máquinas/sierra [V03]. **NV** vínculo exacto entre optimizador y retazo individual con ubicación/reserva. | Explorar escenarios de abastecimiento sin convertirlos en compra; materializar el sobrante con identidad cuando se ejecuta el corte. |
| 9. Compras/stock | **DOC del ERP opcional.** Capabilities describe inventario/recepción/devolución y WMS [V02]; modules identifica V6 Advantage ERP sobre Business Central [V03]. No atribuir el almacén completo a CPQ básico. | Mostrar qué está disponible, asignado y por recibir; producto y contrato deben coincidir con el alcance anunciado. |
| 10. Taller/CNC | **DOC modular.** Automation enlaza producción y máquinas [V03]; ERP añade programación/estado de trabajo [V02]. **NV** máquinas concretas, postprocesadores y entrega instalada. | Conectar una revisión liberada a un adaptador real; no presentar «solicitar optimización» como si completara producción. |
| 11. QR/terreno | **DOC parcial.** El alcance ERP/WMS incluye etiquetas y escaneo de materiales/unidades [V02]. **NV** pasaporte QR de posventa o app de incidencias de instalación equivalente a IoF/SimplyTag. | Diseñar QR por necesidad; no asumir que todo escaneo cubre terreno o garantía. |
| 12. IA | **DOC de dirección; NV de agente.** «AI-ready» y anuncios del portafolio se encuentran en eventos [V08,V09]. No acreditan chat ejecutor V6, proveedor, memoria, políticas o deshacer. X3D/rules tampoco prueban LLM. | Definir acciones entregadas y pruebas de resultados. Distinguir roadmap de comportamiento disponible. |
| 13. Historial/deshacer | **NV.** Publicación central de reglas y actualización de catálogo [V03,V07] no prueban historial de conversación, versiones recuperables ni rollback de operaciones del usuario. | Persistencia de chat y registro de acciones forman parte del contrato del asistente, no se deducen de la nube. |
| 14. Roles | **DOC parcial.** Hay canales proveedor/fabricante/distribuidor [V06,V07] y currículo de grupos/procesos [V05, 2023]. **NV** matriz actual de autorización y auditoría. | Roles reconocibles por tarea, con costo privado y operaciones de compra/emisión limitadas. |
| 15. Claridad visual | **DOC de artefactos; NV de evaluación.** Hay pantallas oficiales de módulos [V03] y una referencia actual X3D [V01]. No se observaron píxeles ni tareas. No se puntuó estética desde el premio promocional. | Capturar X3D y CPQ/taller por separado; evaluar foco, estado, cambio de opción y error con un guion común. |
| 16. Teclado/móvil | **DOC parcial.** X3D funciona en navegador sin instalación de render en el dispositivo del cliente [V01]; WMS usa móvil [V02]. **NV** atajos y editor técnico táctil completo. | Acceso web y trabajo móvil tienen requisitos distintos; validar dimensiones/tacto para la tarea de terreno. |
| 17. Interoperabilidad | **DOC.** Deployment, Automation, Shop Drawing y Business Central tienen responsabilidades explícitas [V03]. La ficha de fabricante distingue despliegue cloud/on-premise [V07]. **NV** contratos y conectores específicos del comprador. | Mapa de conexiones y estados; evitar que un botón de integración sustituya un flujo comprobable. |
| 18. Madurez/precio | **DOC.** Formación y fichas sectoriales; X3D publicado en 2026 [V01,V04,V06,V07]. **NV** tarifa, costo de parametrización y disponibilidad regional de módulos. | Comparar costo total y mantenimiento de datos, además de capacidades de una demo comercial. |

### Dos flujos operativos reconstruidos

**V-F1 — Proveedor a propuesta. DOC; no ejecutado.** Desarrollador del sistema prepara catálogo/reglas → Deployment distribuye cambios [V03,V06] → vendedor configura unidad/conjunto con opciones gobernadas y X3D [V01] → aplica política comercial → obtiene BOM → genera documentación comercial/plano PDF [V02,V03,V06]. La formación de 2023 describe conceptos de preparación [V05]; no confirma que su UI siga igual en 2026.

**V-F2 — Pedido a planta y salida. DOC de módulos; no ejecutado.** BOM de pedido → comparar largos de barra para optimización [V02] → Automation genera salida para equipo compatible [V03] → ERP/WMS recibe y asigna material, programa operaciones y registra avances → preparación/expedición [V02]. El alcance depende del ERP opcional. No se demuestra reserva/consumo de un retazo específico ni un despacho real instalado.

### Referencias visuales y formación

| Referencia | Localizador | Uso y límite |
|---|---|---|
| X3D **2026**, prioridad actual | [Anuncio oficial](https://www.cyncly.com/resources/news/v6-advantage-visualizer-award) y [imagen enlazada](https://www.cyncly.com/siteassets/assets/cyncly/news/v6-advantage) | Selección visual y conjuntos; inspeccionar antes de juzgar la calidad. |
| Plano de taller | [Página modules](https://www.cyncly.com/en-GB/products/soft-tech-v6/modules) y [captura oficial](https://www.cyncly.com/siteassets/assets/cyncly/products/soft-tech/v6-shop-drawing-module2.jpg) | Referencia capturable de documentación técnica; no es X3D. |
| Automatización | [Imagen oficial](https://www.cyncly.com/siteassets/assets/cyncly/products/soft-tech/v6-automation-module2.jpg) | Referencia de módulo; contenido de pantalla no inspeccionado aquí. |
| ERP | [Business Central](https://www.cyncly.com/siteassets/assets/cyncly/products/soft-tech/business-central-integration2.png) y [V6 Advantage](https://www.cyncly.com/siteassets/assets/cyncly/products/v6/vp-advantage.png) | Evaluar salto de tareas y estados entre CPQ y ERP. |
| Fichas | [Proveedor](https://wnaymg.files.cmp.optimizely.com/download/assets/WDG%2B-%2BDatasheet%2B-%2BV6%2B-%2BProfile%2Bsuppliers%2B-%2BEN%2BUS.pdf/56b13f8ab5e011f09db95ac263d27420), [fabricante](https://wnaymg.files.cmp.optimizely.com/download/assets/DataSheet%2BV6%2BAdvantage%2B-%2BWindow%2Band%2BDoor%2BFabricators%2BAPAC%2BA4%2B%2B-%2BEN.pdf/29aa56227ec011f0970f5e1af917a384), ambas 2 páginas | Página 2: familias y documentos; no confundir ilustración comercial con prueba runtime. |
| Video | [MP4 oficial Overview V6](https://wnaymg.files.cmp.optimizely.com/download/assets/WDG%2B-%2BOverview%2B3%2B-%2BV6%2BOverview%2B-%2BEN.mp4/b23a65b4512911f09ad1f28d889ce8c1) | No reproducido por formato no soportado; no hay timestamps ni análisis de video verificado. |

**Pendientes decisivos.** Ver X3D en tarea real con cambios incompatibles; diferencia exacta CPQ/ERP para pyme; retazos individualizados; permisos/costo privado; recuperación de versiones; demostración concreta de cualquier función IA que se ofrezca actualmente.

## 4. A+W — Cantor

**Papel en la comparación.** Referencia de continuidad de pedido, compras, fabricación, logística e instalación. Dealer Cloud, iQuote, ERP/CIM y Smart Companion cubren actores diferentes. **Smart Companion es evidencia de escaneo y formularios; su nombre no demuestra un asistente LLM.**

### Fuentes primarias

| ID | Fuente oficial y fecha | Qué respalda |
|---|---|---|
| A01 | [A+W Cantor](https://www.a-w.com/aw-cantor/), s/f | Ecosistema ERP/CIM, distribuidores y continuidad del pedido. |
| A02 | [A+W ERP/CIM](https://www.a-w.com/aw-cantor/aw-erpcim/), s/f | Datos técnicos, compras, inventario, producción, logística e instalación. |
| A03 | [Dealer Cloud](https://www.a-w.com/aw-cantor/aw-dealer-cloud/), s/f | Documentos/cartera del distribuidor, chequeos y confirmación electrónica. |
| A04 | [Cantor iQuote](https://www.a-w.com/software/cantor-iquote/), s/f | Configuración y pedido sobre la misma base técnica. |
| A05 | [Smart Companion, folleto PDF](https://news.a-w.com/hubfs/AW_English_NA_files/GlassBuild%202022%20Flyers/20220609_us_Messeflyer_AW_Cantor_Smart_Companion.pdf?hsLang=en-us), **2022**, 2 páginas | Production/Stock apps, escaneo, formularios y fotos de incidencia. |
| A06 | [Smart scanning at a window company](https://blog.a-w.com/us/smart-scanning-at-a-window-company), **01-02-2023** | Uso de teléfono Android/iOS para producción y almacén. |
| A07 | [TMP, caso oficial PDF](https://www.a-w.com/wp-content/uploads/2024/03/TMP-Artikel_Dialog_DEZ_2022_en.pdf), relato **2022**, subido 2024, 3 páginas | Ejemplo instalado: entrada de pedidos, materiales, puestos y logística. |
| A08 | [Schlotterer/iQuote, caso oficial PDF](https://www.a-w.com/wp-content/uploads/2024/03/E-Schlotterer_Website.pdf), relato de **BAU 2017**, subido 2024 | Antecedente de configurador/tablet y comparación de variantes, no UI 2026. |
| A09 | [Online configurator for dealers and end customers](https://blog.a-w.com/uk/online-configurator-for-dealers-and-end-customers), **2022** | Caso BE Bauelemente con adopción desde 2020; evidencia histórica de uso, no garantía universal. |

### Evaluación por los 18 ejes

| Eje | Evidencia y límite | Implicación para DEKOPEN |
|---|---|---|
| 1. Entrada/onboarding | **DOC.** ERP/CIM parte de una base técnica parametrizada [A02]; iQuote reutiliza esa base para vender [A04]. «Sin formación» es claim del fabricante, no resultado de una prueba. **NV** esfuerzo de preparar un catálogo local nuevo. | Separar el costo de preparar datos de la facilidad de configurar con datos ya preparados. |
| 2. Marcas/series/catálogos | **DOC parcial.** Hay datos maestros técnicos comunes entre ERP y configurador [A02,A04]. **NV** navegación visual actual marca→serie y biblioteca específica Chile. | Autoridad común, pero galería de marca/serie clara para personas que no conocen códigos. |
| 3. Editor/aperturas | **DOC de restricciones; NV de interacción.** El proveedor documenta chequeos técnicos/comerciales y viabilidad [A03,A04]. No se observó paleta de aperturas ni cambio de mano/carril. | Evaluar la tarea del diseñador, no inferir calidad del editor por amplitud ERP. |
| 4. 2D/3D | **DOC parcial histórico.** Casos de iQuote muestran comparación de variantes [A08,A09]. **NV** render 3D actual, animación de apertura y sincronización geométrica. La pantalla de pedido de TMP es de 2022 [A07]. | Seleccionar referencias según tarea/fecha; no hacer del ERP un benchmark de render sin evidencia. |
| 5. Materiales | **DOC.** Datos de perfiles/herrajes gobiernan pedido [A02]; el caso TMP vincula BOM, disponibilidad y reposición durante entrada [A07, instalación concreta]. **NV** cobertura de cada familia/material del catálogo local. | BOM vinculada a revisión y necesidades; disponibilidad nunca debe deducirse de una imagen de catálogo. |
| 6. Precios | **DOC parcial.** iQuote comprueba precio/viabilidad [A04]; Dealer Cloud añade trabajos libres/instalación y documentos propios [A03]. **NV** fórmula comercial actual y matriz de privacidad de costos. | Precio técnico y servicio comercial pueden coexistir sin perder procedencia ni permisos. |
| 7. Presupuestos/PDF | **DOC.** Dealer Cloud contempla propuesta, pedido, entrega y factura [A03]; el ecosistema dispone de archivo documental [A01]. **NV** plantilla actual, inmutabilidad y aceptación de cliente final por enlace. | Documentos reconocibles por fase, destinatario y revisión; no equiparar configurador distribuidor con portal de aprobación. |
| 8. Corte/retazos | **DOC parcial.** ERP/CIM enumera lotes/optimización [A02]. **NV** algoritmo, retazo lineal reutilizable, ubicación y reserva individual. | Un plan de corte terminado debe declarar su relación con stock y sobrantes, no solo un porcentaje de rendimiento. |
| 9. Compras/stock | **DOC.** Pedidos de proveedor, openTRANS y movimientos con escáner se describen en ERP/CIM [A02]. Smart Companion Stock registra recepción/traslado/inventario [A05]. No se ejecutó conciliación ni concurrencia. | Una recepción guiada y la identificación del lugar físico reducen ambigüedad de las existencias. |
| 10. Taller/CNC | **DOC.** ERP/CIM describe puestos con información pertinente, etiquetas y control de máquina [A02]; el caso TMP aporta instalación histórica [A07]. **NV** adaptador específico para el taller del usuario. | El operario debe recibir unidad, operación e instrucción actual; CNC necesita compatibilidad probada. |
| 11. QR/terreno | **DOC de barcode/fotos.** Smart Companion captura múltiples códigos, estados/ubicación y formulario de reclamación con foto [A05,A06]. **NV** pasaporte QR de consumidor y flujo completo offline de instalación. | Capturar una incidencia desde la unidad física, con relación al pedido, tiene más valor que un QR aislado. |
| 12. IA | **NV.** Smart Companion se documenta como app de escaneo [A05,A06]. El sitio de A+W puede anunciar IA a nivel portafolio; no se verificó agente conversacional Cantor que cambie proyectos con aprobación. | No llamar agente a un formulario; mostrar qué hizo la IA y qué hizo el usuario. |
| 13. Historial/deshacer | **DOC parcial.** Archivo y continuidad de estado [A01]; ERP/CIM relaciona refabricación con pedido original [A02]. **NV** versiones del diseño recuperables, conversación persistente o rollback. | Una refabricación conserva el vínculo con su origen; recuperar un diseño es una capacidad adicional distinta. |
| 14. Roles | **DOC de canales; NV de seguridad.** Dealer Cloud organiza actividad propia de distribuidores [A03] y Smart Companion sirve a almacén/planta [A05]. La expresión «cliente propio» no demuestra aislamiento RLS ni permisos por campo. | Espacios por rol y autorización verificable en cada recurso, especialmente precio y datos de clientes. |
| 15. Claridad visual | **DOC de referencia; NV de evaluación actual.** PDFs ofrecen ejemplos fechados de pedido/puesto [A07] y móvil [A05]. Sin inspección de píxeles ni demo actual, no hay juicio de contraste o estética. | Comparar densidad de oficina con foco de estación; no copiar interfaz de 2022 como solución final. |
| 16. Teclado/móvil | **DOC móvil.** Android/iOS y cámara para escaneo se documentan [A06]. iQuote tiene antecedentes tablet/web [A08]. **NV** teclado del editor actual, paridad móvil y offline. | Flujos cortos de captura en móvil; configuración de precisión puede necesitar escritorio. |
| 17. Interoperabilidad | **DOC.** iQuote usa datos de Cantor [A04]; ERP/CIM enumera openTRANS y conexión de planificación/instalación [A02]. **NV** API pública, contratos y disponibilidad regional por licencia. | Una sola identidad de pedido entre canales; estado de integración visible y recuperable. |
| 18. Madurez/precio | **DOC.** Ecosistema y casos de varios años [A01,A07–A09]. **NV** costo de licencia, consultoría, migración, soporte local y mínimos. Un caso de fábrica grande no prueba simplicidad para pyme. | Escalar alcance por necesidad y probar la tarea del taller objetivo antes de adoptar complejidad ERP. |

### Dos flujos operativos reconstruidos

**A-F1 — Distribuidor a entrega. DOC; no ejecutado.** Configurar y valorar con iQuote/Dealer Cloud → comprobación técnica/comercial → pedido y confirmación con fecha [A03,A04] → ERP/CIM coordina compra/material/capacidad → producción identificada y salida/instalación [A02]. La afirmación de continuidad viene del fabricante; no se midió latencia ni una instalación real.

**A-F2 — Unidad física a reclamación/refabricación. DOC; no ejecutado.** Escanear unidad/ubicación con Smart Companion → ver estado o rellenar incidencia con foto → enviar registro a CIM [A05,A06] → si corresponde, preparar refabricación vinculada al pedido original [A02]. La conexión conceptual está documentada; interfaz de aprobación, permisos y alcance exacto de la refabricación necesitan demo. No es evidencia de deshacer automático de una venta o producción.

### Referencias visuales y formación

| Referencia | Localizador | Uso y límite |
|---|---|---|
| Pedido/puesto, prioridad | [Caso TMP PDF](https://www.a-w.com/wp-content/uploads/2024/03/TMP-Artikel_Dialog_DEZ_2022_en.pdf), **p2** | Pantalla de entrada y puesto CIM; hecho histórico 2022, no interfaz 2026 confirmada. |
| Logística | Mismo PDF, **p3** | Contexto de uso en planta/logística; no equivale a prueba de software. |
| Escaneo móvil | [Smart Companion PDF](https://news.a-w.com/hubfs/AW_English_NA_files/GlassBuild%202022%20Flyers/20220609_us_Messeflyer_AW_Cantor_Smart_Companion.pdf?hsLang=en-us), **p2** | Referencia de teléfono y captura de códigos; documento 2022. |
| Canales distribuidor/fábrica | [Dealer Cloud](https://www.a-w.com/aw-cantor/aw-dealer-cloud/) y [diagrama oficial](https://a-w.com/wp-content/uploads/2024/05/AW_Cantor_DealerCloud2_240515.png) | Arquitectura del flujo, no necesariamente captura de UI. |
| Comparación de variantes | [Schlotterer PDF](https://www.a-w.com/wp-content/uploads/2024/03/E-Schlotterer_Website.pdf) | Caso BAU 2017; solo antecedente, no referencia visual actual sin contraste. |

**Pendientes decisivos.** Demo actual de editor/aperturas; parametrización de marca/serie; matriz de permisos de precio; retazos; historial recuperable; experiencia pyme y costo de implantación. No se obtuvo un tutorial de video reproducido con tiempos verificables.

## Comparación transversal sin puntuaciones inventadas

| Pregunta | Referencia con evidencia más concreta en este conjunto | Límite que permanece |
|---|---|---|
| ¿Cómo se elige una apertura? | Logikal documenta selector y lista de inserciones [L03]. | Falta ejecución y prueba de compatibilidad por sistema. |
| ¿Cómo se recupera un diseño anterior? | Logikal importa una versión como nueva posición [L14]. | No equivale a undo de IA, emisión inmutable ni historial conversacional. |
| ¿Qué catálogo es confiable? | Logikal expone datos técnicos/importación [L07–L09]; V6 centra reglas en proveedor [V03,V06]. | No se validaron los catálogos de Proline/Vinhaus ni datos de terceros. |
| ¿Cuál es una referencia comercial 3D actual? | X3D de V6, anuncio 25-08-2026 [V01]. | Claim/documento; no prueba runtime ni evaluación visual personal. |
| ¿Cómo se separan oficina y estación? | Schüco FDC/MES/mobile [S03–S05]; Cantor ERP/CIM/Smart Companion [A02,A05]. | Permisos, disponibilidad y costo por módulo no probados. |
| ¿Qué ocurre después del presupuesto? | Cantor detalla continuidad compras→planta→logística [A02–A04]. | Integración instalada y tamaño adecuado para el usuario requieren demo. |
| ¿Qué significa QR? | SimplyTag/IoF para ciclo de vida [L17,S08]; FDC/Smart Companion para operación [S03,A05]. | Barcode, QR de cliente e incidencia no son intercambiables. |
| ¿Quién ofrece el asistente solicitado por el dueño? | Ninguna de estas fuentes establece todo el contrato Chat/Work, navegación, memoria y aprobación. | No demuestra que el mercado carezca de ello; es un resultado acotado de esta consulta. |

## Requisitos de diseño propuestos para evaluar DEKOPEN

Estos puntos son **propuestas de análisis**, no cambios implementados ni nuevos requisitos de cálculo. El informe principal debe contrastarlos con código y producto actuales.

1. **Catálogo navegable y técnico.** Marca → familia/material → serie → artículos compatibles, con imagen contextual y dibujo técnico donde estén disponibles. Mostrar fuente, versión, cobertura y estado de revisión. Proline 60/70 pertenece a Proline. Un dato comercial incompleto puede ayudar a explorar, pero no debe pasar a fabricación como validado.
2. **Aperturas como primera prueba de confianza.** El mismo espécimen debe mantener mano, vista, hoja activa/pasiva, carriles, herrajes y trayectoria al cambiar apertura. Evaluar dibujo, 3D y BOM contra la autoridad del motor. No copiar coeficientes ni cotas desde la competencia.
3. **Acciones por momento de trabajo.** Cotizar, revisar ingeniería, liberar fabricación, cortar, recibir material e instalar necesitan focos distintos. «QR», «optimizar» y «CNC» no son tareas equivalentes del usuario y no deberían tener igual jerarquía sin contexto.
4. **Asistente persistente con Chat y Work.** Conversación para explicar; Work para ejecutar operaciones del producto y navegar con contexto. Acceso desde cualquier pantalla y espacio propio para trabajos/historial. Persistir mensajes, acciones, resultado, referencias a proyecto/revisión y recuperación. Una pestaña de chat vacía no sustituye esta continuidad.
5. **Tres políticas de acción con alcance explícito.** Conversar/proponer, trabajar con aprobación y ejecutar automáticamente lo reversible dentro del permiso concedido. El dueño debe elegir nombres finales. Compras, emisión, pagos y otras consecuencias externas conservan el clic humano exigido por el repositorio. «Omitir todo» debe traducirse a comportamiento observable, sin ambigüedad sobre qué se omite.
6. **Jerarquía visible en estados reales.** Color para selección, estado, validación y acción principal; variación de superficie/densidad para agrupar información. No multiplicar colores decorativos. La rúbrica visual debe valorar comprensión de tarea, no solo pulcritud de una captura.
7. **Almacén y corte con continuidad física.** Identificar barra/retazo, longitud, ubicación, reserva y consumo. Comparar escenarios es reversible; comprar y declarar ejecución son eventos explícitos. Explicar qué operación se completó y qué queda pendiente.
8. **Documentos y unidades con identidad.** Presupuesto, plano, corte, pedido y pasaporte de unidad comparten revisión/origen, pero tienen destinatario y jerarquía propios. Recuperar una versión no altera el documento emitido ni el pasado productivo.

## Cobertura entregada y límites del trabajo

- **Resuelto a nivel documental:** selección de cuatro referencias complementarias; fuentes oficiales; 18 ejes por producto; 24 dimensiones estructuradas; dos flujos reconstruidos por producto; localizadores de imágenes/PDF; distinción de módulos, fecha y autoridad.
- **Parcial:** evidencia visual todavía sin inspección de píxeles en este subinforme; tutoriales disponibles/localizados, pero no reproducidos; algunos detalles SchüCal/JANIsoft solo indexados y señalados.
- **No resuelto:** demos instaladas de estas suites, reverse engineering de sus binarios, permisos reales, mediciones de usabilidad/latencia, matrices de licencia locales, precios, soporte de las marcas solicitadas y verificación técnica de sus datos.

No se afirma haber revisado «todo» el software ni haber visto videos que no se reprodujeron. La matriz deja cada ausencia localizada para una siguiente demo. El informe principal reúne estas cuatro referencias con el resto de competidores y el análisis de DEKOPEN.
