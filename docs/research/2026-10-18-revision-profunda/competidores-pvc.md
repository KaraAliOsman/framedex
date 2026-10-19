# Competidores de PVC/aluminio: Klaes, PrefSuite y RA Workshop

Investigación del **18 de octubre de 2026** para DEKOPEN. Este dossier cubre tres empresas dentro de la comparación mayor. Es investigación y especificación de producto; no modifica el software, fórmulas, catálogo operativo ni datos del propietario.

## Cómo interpretar la rúbrica

- **OBS**: se inspeccionó una captura real o un procedimiento ilustrado del manual. No significa que se haya usado una licencia o reproducido la operación.
- **DOC**: declaración o procedimiento del fabricante leído. Sigue pendiente su validación en el producto y edición contratados.
- **NV**: no verificado en las fuentes consultadas. No significa que la capacidad no exista.
- Las lecciones para DEKOPEN son propuestas de diseño de esta investigación, no propiedades atribuidas al competidor.

Las 18 filas por empresa cubren el encargo humano; el [JSON complementario](competidores-pvc.json) conserva las 24 dimensiones normalizadas para comparación transversal. No se otorgan puntuaciones de rendimiento, exactitud matemática o accesibilidad a partir de publicidad y capturas. Todas las fuentes se consultaron el 18-10-2026; las fechas anteriores corresponden a publicación, actualización o interfaz cuando constan.

## 1. Klaes

ERP de cerramientos con construcción, cálculo comercial, producción y red de distribuidores. Su amplitud es una referencia de continuidad entre departamentos. No se debe convertir la existencia de módulos en una promesa de que toda licencia los incluye.

### Rúbrica de 18 ejes

| Eje | Evidencia y límite | Implicación para DEKOPEN |
|---|---|---|
| 1. Onboarding | **DOC**. Se configuran sistemas y detalles reutilizables; los manuales se abren desde Start Center, con idioma seleccionable. No se leyó el manual instalado. [K2], [K13] | Mostrar qué datos faltan para vender y para fabricar; incorporar conocimiento no puede depender solo de descubrir menús. |
| 2. Marcas, series y catálogos | **DOC**. El módulo 3D admite sistemas propios o paquetes de datos suministrados. No se comprobó Proline ni cobertura chilena. [K2] | Marca → serie → tipología → componentes, con procedencia y compatibilidad visibles. Una marca conocida no basta para declarar fabricabilidad. |
| 3. Editor y aperturas | **OBS/NV**. El Tour muestra árbol y posiciones con elevaciones acotadas. La taxonomía de aperturas y sus controles no se verificaron. [K17], [K13] | Conservar identidad de posición y dibujo; exigir prueba física separada por apertura y cara. |
| 4. 2D y 3D | **DOC**. En el módulo 3D se anuncian secciones, rayos X, nodos y despiece. No se atribuye a paquetes base. [K2] | La vista 3D debe resolver dudas de encuentro y montaje; indicar qué parte tiene autoridad técnica. |
| 5. Materiales y componentes | **DOC**. Door Designer incluye manillas y accesorios; e-prod ayuda a localizar vidrio. [K11], [K3] | Vincular pieza diseñada, lista de materiales y ubicación real. |
| 6. Precios y margen | **DOC/NV**. El Tour anuncia costeo de materiales y trabajo. No se inspeccionaron permisos de costo privado o margen. [K1] | Probar quién puede ver, cambiar y aprobar cada precio. |
| 7. Cotización y PDF | **DOC**. La preparación permite convertir oferta total, posiciones o cantidades parciales conservando el original. [K14] | Cotización, revisión y pedido deben mantener relaciones explícitas. |
| 8. Cortes y retazos | **DOC/NV**. Hay listas de corte; no se verificaron el algoritmo optimizador ni la identificación física de retazos. [K2], [K4] | Separar lista calculada, optimización y reserva de barras. |
| 9. Compras y stock | **DOC**. MAWI administra inventario; openTRANS intercambia pedidos y respuestas con proveedor coordinado. [K4], [K10] | Un envío no equivale a confirmación ni a recepción. |
| 10. Taller y CNC | **DOC**. e-prod enfoca información por estación y registra calidad/tiempos; e-control conecta controles de máquina. [K3], [K12] | Cada estación recibe solo instrucciones relevantes; CNC requiere validación específica. |
| 11. QR y terreno | **DOC**. e-prod usa códigos de barras. En 2026 se anuncian Measurement connect y montaje con WinDo Flow. QR específico no comprobado. [K3], [K15] | Etiqueta, posición, medida e incidencia deben llevar a un objeto reconocible. |
| 12. IA | **DOC**. AI Hub 2026 anuncia contexto de empresa, conexiones Microsoft y flujos controlados; la feria reporta demostraciones. No se observó agente operativo. [K15], [K16] | El listón ya incluye IA conectada; diferenciar con resultados y recibos verificables. |
| 13. Historial y deshacer | **DOC/NV**. Se conservan originales comerciales; no se verificó historial o deshacer semántico de IA. [K14], [K15] | Una conversación y una revisión emitida son historias distintas; ambas deben persistir. |
| 14. Roles | **DOC**. Web Business y seguimiento restringen datos según derechos. Matriz completa de permisos no inspeccionada. [K6], [K7] | Las capacidades del asistente deben heredar el rol y alcance del usuario. |
| 15. Claridad visual | **OBS**. Captura histórica: vidrio azul, madera en perfiles, etiquetas verdes y elevación por posición; comandos pequeños y densos. [K17] | Aprender semántica visual; evitar copiar su abundancia de iconos. |
| 16. Teclado y móvil | **DOC/NV**. Acceso web y productos móviles anunciados; accesibilidad, atajos y operación offline no probados. [K6], [K8] | Medir tareas reales en pantalla pequeña y teclado antes de declarar soporte. |
| 17. Interoperabilidad | **DOC**. openTRANS requiere módulos y acuerdo de integración con proveedor; e-control tiene configuración de máquina. [K10], [K12] | Cada integración debe declarar requisitos, dirección y manejo de errores. |
| 18. Madurez y precio | **DOC/NV**. Oferta modular y documentación industrial; no se obtuvo precio comparable ni coste completo de implantación. [K13], [K14] | Comparar coste de licencia, datos, capacitación, integración y mantenimiento por separado. |

### Dos flujos concretos documentados

**Oferta → preparación de trabajo.** La brochure ubica en la página impresa 9 (índice PDF 8) el paso de oferta a pedido completo, parcial o por cantidades. El original se conserva y después se prepara el trabajo. Es una referencia de continuidad documental, no una prueba de inmutabilidad en su base de datos. [K14]

**Estación → seguimiento.** e-prod lleva instrucciones al puesto, permite escaneo y recoge tiempo/calidad; el seguimiento web expone avance a actores con derechos. La demo invitada anunciada por el fabricante no se utilizó. [K3], [K7]

### Referencia visual y fricciones

**K-V1, inspeccionada:** [pantalla dentro del Tour](https://www.klaes.de/en-tour) · [imagen oficial directa](https://www.klaes.de/assets/images/z/en-11-sonderseiten-leadpage-bildschirm-konstruktion-tuer-und-fenster-holz-5pj18w3kgnrqxth.png). La propia interfaz lleva fecha **06-09-2019**. Localizador: árbol de proyecto a la izquierda, dibujos acotados en la tabla central y columnas comerciales a la derecha. El valor está en reconocer la ventana en cada posición; la fricción visible es la densidad de comandos. No usarla para afirmar cómo luce una versión 2026.

Otras referencias localizables: página impresa 11 de [K14] para producción; páginas de [K2] para estructuras y [K3] para estación. Se leyeron como documentación; no se inspeccionaron aquí como una sesión de producto.

Ventaja relevante: conecta venta, preparación, producción y red comercial. Fricción de adopción: módulo, datos e integración no son la misma compra. Incertidumbres: catálogo local, aperturas exactas, retazos, accesibilidad, precio y acciones/rollback de IA.

## 2. PrefSuite / Preference

Referencia industrial con herramientas distintas para datos, diseño, gestión y producción. Los manuales Mercosur permiten observar decisiones concretas y advertencias operativas. Su alcance regional no demuestra una configuración idéntica para Chile.

### Rúbrica de 18 ejes

| Eje | Evidencia y límite | Implicación para DEKOPEN |
|---|---|---|
| 1. Onboarding | **DOC**. El servicio Pre-Go-Live incluye implementar series y centralizar conocimiento técnico/comercial. [P3] | Incorporar un catálogo real es un proyecto de datos, con revisión y criterios de salida. |
| 2. Marcas, series y catálogos | **DOC**. Portfolio Mercosur distingue sistemas disponibles, no disponibles y sujetos a autorización del proveedor. [P4] | Mostrar marca y series dentro de ella, estado, fuente y permiso. No mezclar “referencia PDF” con “lista para producción”. |
| 3. Editor y aperturas | **OBS/DOC**. Captura PrefCad con hojas y cotas; PrefOne documenta cambiar dirección por hoja y alternar interior/exterior. [P18], [P15] | El usuario debe saber qué hoja altera y desde qué cara la observa. |
| 4. 2D y 3D | **DOC**. PrefOne incluye giro 3D, despiece y secciones; las cotas visibles dependen de datos configurados. [P15] | Mantener modelo y datos detrás de la visualización; 3D no sustituye la cota técnica. |
| 5. Materiales y componentes | **DOC**. Herrajes se generan desde tablas asociadas a la apertura; el manual distingue generación automática y sustitución. [P16] | El inspector debe explicar origen y consecuencias de cambiar un componente. |
| 6. Precios y margen | **DOC/NV**. Hay gestión comercial y recálculo; privacidad de costo y matriz de aprobación no comprobadas. [P2], [P15] | Probar permisos comerciales con roles reales. |
| 7. Cotización y PDF | **DOC**. Croquis personalizados se asocian por código de ítem. Un artículo de 2025 documenta alternativa por impresora PDF ante incompatibilidades. [P10], [P17] | Revisar el PDF final y su dibujo, además de los datos del formulario. |
| 8. Cortes y retazos | **DOC**. Cuatro estrategias de barras con longitudes especiales. La documentación advierte un caso de necesidad omitida si la longitud permitida es insuficiente. [P6] | Toda pieza debe acabar colocada o declarada como no ubicable; nunca desaparecer. |
| 9. Compras y stock | **DOC**. PrefNeeds genera listas manuales, desde obra o fusionadas y conserva origen; ERP integra movimientos. [P7], [P1] | Consolidar necesidades sin borrar de qué proyecto vienen. |
| 10. Taller y CNC | **DOC**. PrefCIM monitoriza estaciones; ERP anuncia planificación y CAM. Compatibilidad concreta de máquina pendiente. [P12], [P1] | Pantalla por estación y validación por máquina; evitar “compatible con todo”. |
| 11. QR y terreno | **DOC/NV**. CIM anuncia códigos de barras y expedición etiquetada. QR, medición offline e instalación no inspeccionados. [P1] | Validar el recorrido físico de la etiqueta y cada rol de terreno. |
| 12. IA | **NV**. No se encontró evidencia pública fiable de agente IA en el corpus consultado. [P1], [P2], [P3] | No puntuar ausencia; demostrar trabajo ejecutado al comparar DEKOPEN. |
| 13. Historial y deshacer | **DOC/NV**. Se documenta versión activa de obra. Historial conversacional y deshacer de agente no verificados. [P13] | Separar revisión comercial, edición del modelo y acciones IA. |
| 14. Roles | **DOC/NV**. Registro de usuario desde empleado/CRM y vínculo con presupuestador; no demuestra permisos de lectura/escritura. [P14] | No confundir existencia de usuarios con aislamiento de datos. |
| 15. Claridad visual | **OBS**. Elevación con vidrio azul, perfiles tramados, flechas y cotas diferenciadas; alta densidad de herramientas. [P18] | Conservar la riqueza técnica con una jerarquía y nombres más claros. |
| 16. Teclado y móvil | **OBS/DOC/NV**. Captura muestra atajos; tutorial usa flecha abajo para nuevas líneas. Venta web/móvil anunciada, accesibilidad no probada. [P18], [P16], [P2] | Atajos visibles junto al comando y operación completa sin ratón. |
| 17. Interoperabilidad | **DOC**. Plataforma SQL y conexiones CRM/ERP anunciadas; sincronización exacta no ejecutada. [P1] | Definir propietario de cada dato y recuperación ante fallos. |
| 18. Madurez y precio | **DOC/NV**. Hay documentación regional detallada e implantación específica; no se obtuvo precio total comparable. [P3], [P6] | Medir coste de datos, soporte y capacitación además de licencia. |

### Tres flujos concretos documentados

**Obra → necesidades de compra.** PrefNeeds ofrece lista independiente, derivada del cálculo o fusión. El informe distingue materiales del proyecto y añadidos manuales e incluye proveedor y destino. No se creó una compra durante esta investigación. [P7]

**Material neto → barras.** El usuario entra a datos de producción, recalcula con estrategia y longitudes permitidas y revisa barras/pérdidas. El tutorial advierte sobre cálculo prolongado y un caso de longitudes especiales insuficientes. Son advertencias del fabricante; no se reprodujeron ni demuestran que toda versión actual tenga el mismo comportamiento. [P6]

**Herraje → modelo alternativo.** El manual recomienda copiar el modelo, inspeccionar el origen de herrajes, sustituir vínculos y regenerar materiales. Exige códigos registrados y vinculados al color. Es una referencia de procedencia, no una prueba de compatibilidad física automática. [P16]

### Referencias visuales y videos

**P-V1, inspeccionada:** [manual de niveles de hojas](https://prefsuite.zendesk.com/hc/pt-br/articles/34430593841684-PrefSuite-N%C3%ADveis-de-folhas) · [imagen directa PrefCad](https://canaldocliente.esquadgroup.com.br/uploads/manual/51680436.jpg). Localizador: dos hojas correderas, flechas en vidrio, cotas negras/azules y menú Editar abierto. El artículo figura actualizado el 03-02-2025. [P5], [P18]

**P-V2, texto leído e imágenes pendientes:** [tutorial PrefOne](https://prefsuite.zendesk.com/hc/pt-br/articles/23326502475796-Principais-recursos-PrefOne), secciones 3.1.6 (aperturas), 3.2.1 (3D) y 3.2.4 (interior/exterior). Útil para futuras capturas comparables.

Videos oficiales regionales inventariados: [FastOffering / tipología rápida](https://canaldocliente.esquadgroup.com.br/presuite/video/40) y [construcción PVC](https://canaldocliente.esquadgroup.com.br/presuite/video/42). **No se reprodujeron**; no hay minutos observados ni conclusiones extraídas de su reproducción.

Ventaja relevante: manuales revelan procedencia de materiales, parametrización y transiciones operativas. Fricciones documentadas: tareas masivas pueden ser lentas [P8], rutas de croquis requieren configuración [P10] y exportación PDF puede necesitar alternativa [P17]. No extrapolar incidencias documentadas a toda edición instalada.

## 3. RA Workshop

Configurador, presupuesto y producción con ediciones diferenciadas y complementos. Su manual de optimización es especialmente útil para relacionar matemática y almacenamiento real. Smart Office debe evaluarse como oferta regional de acceso anticipado.

### Rúbrica de 18 ejes

| Eje | Evidencia y límite | Implicación para DEKOPEN |
|---|---|---|
| 1. Onboarding | **DOC**. FAQ separa base demo inmediata de datos reales, normalmente 2–4 semanas con información de perfiles y herrajes. [R3] | Quitar demos no resuelve validación: mostrar preparación real y pendientes. |
| 2. Marcas, series y catálogos | **OBS/DOC**. Tabla Profile Systems con fabricante/serie, tipo y material; manual define sistema de perfiles compatibles. [R14], [R4] | Anidar marcas y series para navegar; conservar búsqueda por propiedades. |
| 3. Editor y aperturas | **DOC**. Familias corredera, abatible/oscilobatiente y avanzadas dependen de edición; videos describen edición en tablero o propiedades. [R1], [R9] | Probar toda apertura con orientación y restricciones reales. |
| 4. 2D y 3D | **DOC/NV**. Hay diseño técnico documentado; render 3D navegable no verificado en estas fuentes. [R9], [R2] | No usar la presencia de dibujo como prueba de simulación 3D. |
| 5. Materiales y componentes | **DOC**. Base de vidrio y sistemas de herrajes; agrupaciones por color/tipo/perfil. [R1] | Compatibilidad y agrupación deben explicar los materiales que producirán. |
| 6. Precios y margen | **DOC/NV**. Professional distingue costo, beneficio y tarifas cliente/distribuidor. Permisos efectivos sin inspeccionar. [R2] | Una columna privada necesita control de acceso, no solo ocultación visual. |
| 7. Cotización y PDF | **DOC**. Informes diferenciados por destinatario y salidas comerciales/técnicas. No se generó PDF. [R2] | Presentación comercial y documento de fabricación deben tener contratos propios. |
| 8. Cortes y retazos | **DOC**. Optimización combina longitudes estándar y retazos; política máxima por perfil cambia decisiones. [R5] | La estrategia debe ajustarse al orden físico del almacén. |
| 9. Compras y stock | **DOC**. RA Inventory recibe BOM/órdenes y gestiona compras, recepción y disponibilidad. [R8] | Necesidad, compra, recepción y consumo son estados distintos del mismo recorrido. |
| 10. Taller y CNC | **DOC**. Proyectos de producción y CNC según edición/complemento; videos globales describen instalaciones concretas. [R1], [R9] | Validar máquinas y conservar origen de cada posición liberada. |
| 11. QR y terreno | **DOC/NV**. Hay etiquetas entre informes; QR e instalación móvil no verificadas. [R1] | Un QR requiere objeto, lector, permisos y resultado de escaneo definidos. |
| 12. IA | **DOC**. Smart Office regional anuncia lectura documental, RAG y automatizaciones; acceso anticipado Bulgaria/Professional. [R11], [R13] | Comparar madurez real y alcance regional antes de proclamar paridad. |
| 13. Historial y deshacer | **DOC/NV**. Oferta regional anuncia actividad sobre aprobar, cambiar y cancelar pasos; reversión geométrica no probada. [R13] | Conservar recibo, versión anterior y efecto; “cancelar” no prueba rollback. |
| 14. Roles | **DOC/NV**. Smart Office anuncia permisos/auditoría. No se inspeccionó matriz RA Workshop global. [R11] | La autoridad del agente debe coincidir con permisos reales del ejecutor. |
| 15. Claridad visual | **OBS**. Tabla filtrable y agrupable con fila seleccionada azul, códigos y material; toolbar densa. [R14] | Ficha reconocible de marca/serie y filtros técnicos; nombrar acciones críticas. |
| 16. Teclado y móvil | **DOC/NV**. Videos históricos describen Ctrl para multiselección; FAQ permite escritorio offline salvo licencia. No equivale a móvil offline. [R9], [R3] | Separar capacidad de escritorio, navegación por teclado y trabajo en terreno. |
| 17. Interoperabilidad | **DOC**. Exportación de BOM hacia RA Inventory y CNC por módulo; sincronización no ejecutada. [R8], [R2] | Transportar versión y procedencia para reconciliar cambios. |
| 18. Madurez y precio | **DOC/NV**. FAQ ofrece suscripción anual, concurrencia y prueba; precio local total sin verificar. [R3] | Comparar edición y complemento necesarios para cada flujo. |

### Tres flujos concretos documentados

**Sistema de perfiles.** El manual y captura permiten identificar código, denominación, tipo y material, buscar/filtrar y confirmar o cancelar. Se inspeccionó la captura; no se creó un sistema. La tabla repite fabricante en nombres y **no demuestra** árbol anidado de marcas. [R4], [R14]

**Stock → optimización → aceptación.** Se define política por perfil, se usan barras y retazos, se revisa el resultado y se acepta para actualizar existencias. El manual distingue origen estándar/retazo y advierte de la organización física necesaria. No se observaron corte real ni inventario reconciliado. [R5]

**Factura → automatización regional.** Smart Office describe extracción, contraste con pedido/recepción, excepciones para responsable y paso de documentos aprobados a finanzas/almacén. No se observó extracción real. Su disponibilidad está limitada por acceso anticipado regional, edición y activación. [R13], [R11]

### Referencia visual y videos

**R-V1, inspeccionada:** [manual Profile Systems](https://help.raworkshop.bg/docs?lang=bg&url=https://www.raworkshop.com/Help/Ra%2520Workshop/4.1/en/topics/profile-system-overview.htm) · [imagen directa](https://help.raworkshop.bg/api/docs/resource?url=https%3A%2F%2Fwww.raworkshop.com%2FHelp%2FRa%2520Workshop%2F4.1%2Fen%2Ftopics%2Fimages%2Fannotations%2Fprofile_system_overview%2Fprofile%2520system%2520-%2520dialog.png). Localizador: columnas Code, Designation, Type y Material; series Deceuninck y material PVC. No se verificó Proline. La ayuda regional sirve material de manual 4.1, no una sesión actual.

Inventario regional seleccionado; fechas/duraciones declaradas, **no videos vistos ni timestamps de momentos observados**:

| Recurso | Publicación declarada | Duración | Uso posterior |
|---|---|---|---|
| [Instalación Lite 4](https://www.youtube.com/watch?v=6SwFCN_x2U0) | 06-11-2022 | 11:10 | Evaluar primer arranque y datos iniciales. |
| [Primera cotización](https://www.youtube.com/watch?v=OnJoKmzFIOQ) | 02-01-2023 | 2:55 | Comparar pasos hasta primer resultado. |
| [Precios](https://www.youtube.com/watch?v=aIbXqgvuNyc) | 31-03-2021 | 39:07 | Revisar modelo comercial y transparencia. |
| [Crear sistema PVC](https://www.youtube.com/watch?v=7PBRhmjlNp0) | 21-03-2021 | 2:15:13 | Estimar esfuerzo de preparación de datos. |
| [Opening Directions — Common Mistakes](https://raworkshop.bg/en/resources/videos) | 15-01-2023 | 13:57 | Revisar confusiones de cara y dirección. |

El catálogo global [R9] incluye material 3.x, por lo que su interfaz es histórica. También describe instalaciones CNC reales, incluida Ventalplast en Santiago; la descripción no se convirtió en validación técnica ni video observado.

Ventaja relevante: distinción entre proyecto comercial, lote productivo y retazos utilizables. Fricciones: datos reales requieren preparación, cobertura varía por edición y la IA regional tiene madurez/disponibilidad limitadas.

## Lecciones transversales para la propuesta DEKOPEN

Estas son inferencias de diseño que deberán contrastarse con la auditoría del código y la elección del propietario:

1. **Catálogo reconocible y con autoridad.** La pantalla inicial debe mostrar marcas e imágenes técnicas reales; dentro de Proline, sus series; dentro de cada serie, tipos compatibles y estado de preparación. Un PDF público puede servir de referencia sin convertirse en fuente automática de fórmulas, precios o compatibilidad.
2. **Editor con física visible.** Selección inequívoca de hoja, vista interior/exterior, sentido, activa/pasiva, medidas y límites. Los ejemplos competidores sugieren que dirección, nivel, vidrio y sección no deben quedar escondidos tras iconos genéricos.
3. **Color como información.** Distinguir selección, material, vidrio, estado, alerta y acción principal. Los tres ejemplos inspeccionados usan color técnico; la sobriedad no obliga a perder señales.
4. **Separar las decisiones operativas.** Cotización, cálculo de materiales, lote, optimización, reserva, corte y recepción necesitan objetos y estados propios enlazados. Un botón genérico de “solicitar optimización” no puede representar toda esa cadena.
5. **Retazos con identidad.** Longitud útil, perfil, acabado, ubicación, reserva y origen. La política de aprovechamiento tiene que ser comprensible para quien busca la pieza en el almacén.
6. **Ninguna pieza desaparece.** El resultado de cortes debe reconciliar demanda y asignaciones y declarar sobrantes o imposibles, con causa. Las advertencias de manual sirven para diseñar esta comprobación, no para acusar a una versión no probada.
7. **Asistente que entrega trabajo.** La presencia de Klaes AI Hub hace insuficiente un chat genérico. Chat y Trabajo deben persistir contexto, conversaciones, operaciones, versiones y resultado. La preferencia del propietario “Omitir aprobaciones” permite encadenar trabajo reversible; la IA no reemplaza el motor ni inventa reglas numéricas.
8. **Recibo y recuperación.** Tras una tarea, abrir el objeto cambiado, resumir qué cambió y ofrecer la recuperación aplicable. Separar deshacer edición, restaurar borrador y emitir nueva revisión.
9. **Taller y terreno por tarea.** Código físico con destino verificable; información reducida según estación o instalación. No mezclar códigos, solicitudes y administración en un mismo bloque sin jerarquía.
10. **Versión final demostrable.** Una promesa comercial, una captura antigua y una función realmente ejecutada son evidencias distintas. La futura aceptación necesita un recorrido con datos reales autorizados, aperturas completas, documentos revisados y trazabilidad de cálculo.

## Registro de fuentes primarias

IDs usados en tablas y JSON. Todas son del fabricante o su canal regional; los recursos no ejecutados mantienen ese límite.


### Klaes

- **[K1]** [Klaes Tour](https://www.klaes.de/en-tour) — product; sin fecha editorial verificada.
- **[K2]** [Klaes 3D](https://www.klaes.de/en-klaes-3d) — product; sin fecha editorial verificada.
- **[K3]** [Klaes e-prod](https://www.klaes.de/en-e-prod) — product; sin fecha editorial verificada.
- **[K4]** [Inventory Management / MAWI](https://www.klaes.de/en-inventory-management) — product; sin fecha editorial verificada.
- **[K5]** [Klaes Reports](https://www.klaes.de/en-reports) — product; sin fecha editorial verificada.
- **[K6]** [Klaes Web Business](https://www.klaes.de/en-web-business) — product; sin fecha editorial verificada.
- **[K7]** [Klaes Web Tracking](https://www.klaes.de/en-web-tracking) — product; sin fecha editorial verificada.
- **[K8]** [Klaes webtrade](https://www.klaes.de/en-webtrade) — product; sin fecha editorial verificada.
- **[K9]** [Klaes webshop](https://www.klaes.de/en-webshop) — product; sin fecha editorial verificada.
- **[K10]** [Klaes openTRANS](https://www.klaes.de/en-opentrans) — product; sin fecha editorial verificada.
- **[K11]** [Klaes Door Designer](https://www.klaes.de/en-klaes-door-designer) — product; sin fecha editorial verificada.
- **[K12]** [Klaes e-control](https://www.klaes.de/en-e-control) — product; sin fecha editorial verificada.
- **[K13]** [Cómo acceder a los manuales](https://www.klaes.de/en-manual) — manual-route; sin fecha editorial verificada. Límite: El fabricante dirige a los manuales dentro del Start Center; no se accedió a su contenido..
- **[K14]** [Brochure Work Worlds](https://www.klaes.de/files/Content_data_website/01_Startseite/News%20Slider/EN/Startslider/2024-10-Arbeitswelten-Klaes-Imagebrosch%C3%BCre-en.pdf) — brochure; fecha: 2024-10. Límite: La fecha procede del nombre del archivo; páginas localizables, no ejecución del producto..
- **[K15]** [Fensterbau Frontale 2026 preview](https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en) — news; fecha: 2026-02-13.
- **[K16]** [The perfect exhibition](https://www.klaes.de/en-news/the-perfect-exhibition) — news; fecha: 2026-04-02.
- **[K17]** [Captura de construcción del Tour](https://www.klaes.de/assets/images/z/en-11-sonderseiten-leadpage-bildschirm-konstruktion-tuer-und-fenster-holz-5pj18w3kgnrqxth.png) — image; fecha: 2019-09-06. Límite: Fecha visible en la propia interfaz. Referencia histórica publicada todavía en el sitio actual..

### PrefSuite / Preference

- **[P1]** [Integrated ERP Platform](https://www.preference.com/integrated-erp-platform/) — product; sin fecha editorial verificada.
- **[P2]** [Quotation and Selling Software](https://www.preference.com/quotation-and-selling-software/) — product; sin fecha editorial verificada.
- **[P3]** [Pre Go-Live Services](https://www.preference.com/pre-go-live-services/) — product; sin fecha editorial verificada.
- **[P4]** [Portfolio PrefSuite Mercosur](https://preferencemercosur.com/portfolio-prefsuite/) — product; sin fecha editorial verificada.
- **[P5]** [PrefSuite — Níveis de folhas](https://prefsuite.zendesk.com/hc/pt-br/articles/34430593841684-PrefSuite-N%C3%ADveis-de-folhas) — tutorial; fecha: 2025-02-03.
- **[P6]** [PrefSuite — Otimização de Barras](https://prefsuite.zendesk.com/hc/pt-br/articles/34522274674708-PrefSuite-Otimiza%C3%A7%C3%A3o-de-Barras) — tutorial; fecha: 2025-09-04. Límite: Advertencia de barras especiales documentada; no defecto reproducido en esta revisión..
- **[P7]** [PrefSuite — Romaneio de Materiais](https://prefsuite.zendesk.com/hc/pt-br/articles/34491852776468-PrefSuite-Romaneio-de-Materiais) — tutorial; fecha: 2025-09-17.
- **[P8]** [Registro de tratamiento para perfiles](https://prefsuite.zendesk.com/hc/pt-br/articles/34491745286804-PrefSuite-Cadastro-de-um-novo-tratamento-para-os-perfis) — tutorial; fecha: 2025-10-09.
- **[P9]** [Cambiar color de varios ítems](https://prefsuite.zendesk.com/hc/pt-br/articles/34491592376596-PrefSuite-Alterar-a-cor-de-v%C3%A1rios-itens-da-obra-ao-mesmo-tempo) — tutorial; sin fecha editorial verificada.
- **[P10]** [Croquis personalizado en propuesta](https://prefsuite.zendesk.com/hc/pt-br/articles/34491820785428-PrefSuite-Troca-de-Croquis-em-Proposta) — tutorial; sin fecha editorial verificada.
- **[P11]** [PrefWeb](https://preferencemercosur.com/prefweb/) — product; sin fecha editorial verificada.
- **[P12]** [PrefCIM](https://preferencemercosur.com/prefcim/) — product; sin fecha editorial verificada.
- **[P13]** [Listado de obras por presupuestador](https://prefsuite.zendesk.com/hc/pt-br/articles/23349345677588-Relat%C3%B3rio-de-listagem-de-obras-por-or%C3%A7amentista) — tutorial; fecha: 2025-12-01.
- **[P14]** [Registro de usuarios](https://prefsuite.zendesk.com/hc/pt-br/articles/34491799716500-PrefSuite-Cadastro-de-novos-usu%C3%A1rios) — tutorial; fecha: 2025-02-03.
- **[P15]** [Principales recursos PrefOne](https://prefsuite.zendesk.com/hc/pt-br/articles/23326502475796-Principais-recursos-PrefOne) — tutorial; fecha: 2025-02-13. Límite: Documenta funciones desde versión 2020; actualización del artículo no equivale a fecha de toda captura..
- **[P16]** [Sustituir componentes de un modelo](https://prefsuite.zendesk.com/hc/pt-br/articles/23326116065300-Substituir-componentes-de-um-modelo) — tutorial; fecha: 2024-02-01.
- **[P17]** [Guardar informes PDF](https://prefsuite.zendesk.com/hc/pt-br/articles/23349197510548-Salvar-relat%C3%B3rios-em-formato-PDF) — tutorial; fecha: 2025-11-12.
- **[P18]** [Captura de niveles de hojas PrefCad](https://canaldocliente.esquadgroup.com.br/uploads/manual/51680436.jpg) — image; sin fecha editorial verificada. Límite: Captura inspeccionada procedente del artículo regional P5..
- **[P19]** [Video: tipología rápida FastOffering](https://canaldocliente.esquadgroup.com.br/presuite/video/40) — video-index; sin fecha editorial verificada. Límite: Título inventariado; video no reproducido..
- **[P20]** [Video: construcción de tipologías PVC](https://canaldocliente.esquadgroup.com.br/presuite/video/42) — video-index; sin fecha editorial verificada. Límite: Título inventariado; video no reproducido..

### RA Workshop

- **[R1]** [Compare editions](https://www.raworkshop.com/compare-editions/) — editions; sin fecha editorial verificada. Límite: No se atribuye cada función a Lite; cobertura depende de edición y complementos..
- **[R2]** [RA Workshop Professional](https://www.raworkshop.com/ra-workshop-professional/) — product; sin fecha editorial verificada.
- **[R3]** [FAQ](https://www.raworkshop.com/faq/) — product; sin fecha editorial verificada.
- **[R4]** [Manual 4.1 — Profile systems](https://help.raworkshop.bg/docs?lang=bg&url=https://www.raworkshop.com/Help/Ra%2520Workshop/4.1/en/topics/profile-system-overview.htm) — manual; sin fecha editorial verificada. Límite: Envoltura regional en búlgaro, captura inglesa; texto traducido, no manual global nuevo..
- **[R5]** [Manual 4.1 — Full stock optimization](https://help.raworkshop.bg/docs?lang=bg&url=https://www.raworkshop.com/Help/Ra%2520Workshop/4.1/en/topics/stock-optimization-full-optimization.htm) — manual; sin fecha editorial verificada.
- **[R8]** [RA Inventory](https://www.raworkshop.com/ra-inventory/) — product; sin fecha editorial verificada.
- **[R9]** [Media — videos globales](https://www.raworkshop.com/media/) — video-index; sin fecha editorial verificada. Límite: Descripciones mayormente de versiones 3.0–3.3. No se reprodujeron videos..
- **[R10]** [Recursos — videos regionales](https://raworkshop.bg/en/resources/videos) — video-index; sin fecha editorial verificada. Límite: Títulos, fechas y duraciones inventariados. Videos no reproducidos; duración no es marca temporal verificada..
- **[R11]** [Smart Office regional — alcance y disponibilidad](https://raworkshop.bg/en/products/smart-office) — regional-product; sin fecha editorial verificada. Límite: Acceso anticipado opcional para clientes Professional en Bulgaria, activación manual; partes disponibles y partes planificadas..
- **[R13]** [Smart Office — automation and AI](https://raworkshop.bg/products/smart-office/automation-ai) — regional-product; sin fecha editorial verificada. Límite: Funciones comerciales de oferta regional, no demostración ejecutada ni disponibilidad global..
- **[R14]** [Captura Profile Systems](https://help.raworkshop.bg/api/docs/resource?url=https%3A%2F%2Fwww.raworkshop.com%2FHelp%2FRa%2520Workshop%2F4.1%2Fen%2Ftopics%2Fimages%2Fannotations%2Fprofile_system_overview%2Fprofile%2520system%2520-%2520dialog.png) — image; sin fecha editorial verificada.

## Evidencia local y alcance de entrega

Imágenes temporales inspeccionadas, fuera del árbol del producto:

- `C:/Users/alios/AppData/Local/Temp/dekopen-competitors-pvc-20261018/klaes-editor.png`
- `C:/Users/alios/AppData/Local/Temp/dekopen-competitors-pvc-20261018/prefsuite-leaf-levels.jpg`
- `C:/Users/alios/AppData/Local/Temp/dekopen-competitors-pvc-20261018/ra-profile-systems.png`

El coordinador puede seleccionar y conservar capturas de referencia. Este dossier no afirma haber realizado análisis REA de binarios competidores, acceso a áreas privadas, reproducción de videos ni pruebas operativas de sus cálculos. La inspección REA del proyecto local y la síntesis de diez o más competidores pertenecen al informe conjunto.

[K1]: https://www.klaes.de/en-tour
[K2]: https://www.klaes.de/en-klaes-3d
[K3]: https://www.klaes.de/en-e-prod
[K4]: https://www.klaes.de/en-inventory-management
[K5]: https://www.klaes.de/en-reports
[K6]: https://www.klaes.de/en-web-business
[K7]: https://www.klaes.de/en-web-tracking
[K8]: https://www.klaes.de/en-webtrade
[K9]: https://www.klaes.de/en-webshop
[K10]: https://www.klaes.de/en-opentrans
[K11]: https://www.klaes.de/en-klaes-door-designer
[K12]: https://www.klaes.de/en-e-control
[K13]: https://www.klaes.de/en-manual
[K14]: https://www.klaes.de/files/Content_data_website/01_Startseite/News%20Slider/EN/Startslider/2024-10-Arbeitswelten-Klaes-Imagebrosch%C3%BCre-en.pdf
[K15]: https://www.klaes.de/en-news/fensterbau-frontale-2026-preview-en
[K16]: https://www.klaes.de/en-news/the-perfect-exhibition
[K17]: https://www.klaes.de/assets/images/z/en-11-sonderseiten-leadpage-bildschirm-konstruktion-tuer-und-fenster-holz-5pj18w3kgnrqxth.png
[P1]: https://www.preference.com/integrated-erp-platform/
[P2]: https://www.preference.com/quotation-and-selling-software/
[P3]: https://www.preference.com/pre-go-live-services/
[P4]: https://preferencemercosur.com/portfolio-prefsuite/
[P5]: https://prefsuite.zendesk.com/hc/pt-br/articles/34430593841684-PrefSuite-N%C3%ADveis-de-folhas
[P6]: https://prefsuite.zendesk.com/hc/pt-br/articles/34522274674708-PrefSuite-Otimiza%C3%A7%C3%A3o-de-Barras
[P7]: https://prefsuite.zendesk.com/hc/pt-br/articles/34491852776468-PrefSuite-Romaneio-de-Materiais
[P8]: https://prefsuite.zendesk.com/hc/pt-br/articles/34491745286804-PrefSuite-Cadastro-de-um-novo-tratamento-para-os-perfis
[P9]: https://prefsuite.zendesk.com/hc/pt-br/articles/34491592376596-PrefSuite-Alterar-a-cor-de-v%C3%A1rios-itens-da-obra-ao-mesmo-tempo
[P10]: https://prefsuite.zendesk.com/hc/pt-br/articles/34491820785428-PrefSuite-Troca-de-Croquis-em-Proposta
[P11]: https://preferencemercosur.com/prefweb/
[P12]: https://preferencemercosur.com/prefcim/
[P13]: https://prefsuite.zendesk.com/hc/pt-br/articles/23349345677588-Relat%C3%B3rio-de-listagem-de-obras-por-or%C3%A7amentista
[P14]: https://prefsuite.zendesk.com/hc/pt-br/articles/34491799716500-PrefSuite-Cadastro-de-novos-usu%C3%A1rios
[P15]: https://prefsuite.zendesk.com/hc/pt-br/articles/23326502475796-Principais-recursos-PrefOne
[P16]: https://prefsuite.zendesk.com/hc/pt-br/articles/23326116065300-Substituir-componentes-de-um-modelo
[P17]: https://prefsuite.zendesk.com/hc/pt-br/articles/23349197510548-Salvar-relat%C3%B3rios-em-formato-PDF
[P18]: https://canaldocliente.esquadgroup.com.br/uploads/manual/51680436.jpg
[P19]: https://canaldocliente.esquadgroup.com.br/presuite/video/40
[P20]: https://canaldocliente.esquadgroup.com.br/presuite/video/42
[R1]: https://www.raworkshop.com/compare-editions/
[R2]: https://www.raworkshop.com/ra-workshop-professional/
[R3]: https://www.raworkshop.com/faq/
[R4]: https://help.raworkshop.bg/docs?lang=bg&url=https://www.raworkshop.com/Help/Ra%2520Workshop/4.1/en/topics/profile-system-overview.htm
[R5]: https://help.raworkshop.bg/docs?lang=bg&url=https://www.raworkshop.com/Help/Ra%2520Workshop/4.1/en/topics/stock-optimization-full-optimization.htm
[R8]: https://www.raworkshop.com/ra-inventory/
[R9]: https://www.raworkshop.com/media/
[R10]: https://raworkshop.bg/en/resources/videos
[R11]: https://raworkshop.bg/en/products/smart-office
[R13]: https://raworkshop.bg/products/smart-office/automation-ai
[R14]: https://help.raworkshop.bg/api/docs/resource?url=https%3A%2F%2Fwww.raworkshop.com%2FHelp%2FRa%2520Workshop%2F4.1%2Fen%2Ftopics%2Fimages%2Fannotations%2Fprofile_system_overview%2Fprofile%2520system%2520-%2520dialog.png

