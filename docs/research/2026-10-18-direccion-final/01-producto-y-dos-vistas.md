# Producto final: cotizador profesional con dos vistas

Decisión de producto para el paquete de implementación de Claude. Fecha: **18-10-2026**. Este documento define el resultado; no afirma que ya esté implementado ni probado.

## Autoridad y objetivo

La corrección más reciente del dueño prevalece sobre las propuestas del estudio anterior y sobre instrucciones históricas: **DEKOPEN es primero un cotizador manual profesional y completo. El plan principal no necesita IA. Estudio y Mesa de obra son dos vistas elegibles del mismo producto.** La IA queda como popup global opcional abierto por una acción del usuario. No ocupa el inspector ni reserva una columna permanente, y una conversación no es la puerta de entrada obligatoria al trabajo.

El PRD original adjunto `b8dca4f1-0c32-4aa3-824c-68bad9f2bf23/Texto pegado.txt` ya decía que todo podía hacerse manualmente y que la IA debía operar las funciones del sistema. Se conserva esa intención: precisión, precios privados, personalización, diseño, cotización y documentos de materiales. Sus importes de planes, modelos de IA, proveedores y funciones aspiracionales no se convierten en alcance aceptado. La lista de beneficios de startup tampoco acredita una integración implementada.

El informe `../2026-10-18-revision-profunda/tres-direcciones.md` proponía un asistente acoplado en Estudio/Mesa. **Esa parte queda sustituida.** Centro de encargos no es la arquitectura principal. La constitución actual §5.11 pide un panel persistente junto al trabajo: la fase de fundamentos debe alinearla con esta decisión del dueño, preservando sus reglas de calidad, exactitud, accesibilidad y acciones humanas. No hace falta volver a pedir una elección de concepto.

Resultado esperado: una empresa puede preparar una obra, diseñar ventanas, corregirlas, calcular su precio y obtener su propuesta sin créditos, proveedor, permiso o sesión de IA. Elegir vista cambia el foco de la interfaz; no crea otra obra ni recalcula con otra fórmula.

## Fuentes y alcance de verificación

Se inspeccionó el árbol local **`claude/v1-implementacion`, HEAD `6f78e3299d93816991fb7c2fe2a2044458fc5e7a` más cambios sin commit**, el 18-10-2026. Los hallazgos de código corresponden a ese árbol, no a HEAD limpio ni a una garantía de runtime. No se inició stack, se modificó base ni se ejecutó una campaña de pruebas en esta fase documental.

Conocimiento consultado: `docs/wiki/product/project-workspace.md`, `editor-canvas.md`, `catalog-authority.md`, `physical-openings.md`, `price-workspace.md`; `docs/design/CONSTITUCION.md`; `docs/ENGINEERING.md`; investigación de competidores/catálogos y auditoría local del 18-10. La wiki contiene aceptaciones históricas; cada afirmación de implementación usada abajo se contrastó con los símbolos actuales indicados. La auditoría de navegador anterior tiene sus propios objetos, rol y límites; no se reatribuye como prueba nueva.

## Un modelo, dos focos

| Contrato | Mesa de obra | Estudio |
|---|---|---|
| Pregunta que responde | ¿Qué lleva esta obra, qué falta y qué voy a entregar? | ¿Cómo queda esta ventana y cómo la modifico con precisión? |
| Objeto dominante | Colección de posiciones y entregable seleccionado. | Dibujo de una posición o conjunto, con selección física. |
| Uso preferente | Cotización de varias ventanas, revisión, cambios en lote y preparación documental. | Diseño manual repetido, aperturas, medidas, divisiones, uniones y materiales por selección. |
| Entrada | Ventanas de la obra con miniatura técnica y datos útiles. | Misma posición activa en el editor amplio; si no existe, biblioteca manual. |
| Componentes comunes | Cabecera de obra, cliente, revisión, filtros, selección y operaciones. | Los mismos; distinta distribución y densidad. |
| Precio | Total aplicado y estado de preparación de la propuesta. | Precio indicativo de edición, separado del aplicado de la obra. |
| Acceso a la otra vista | Selector «Mesa de obra / Estudio». | El mismo selector, posición y sección conservadas. |
| IA | Solo el popup global opcional invocado. | Solo ese popup; sin panel incrustado o hueco reservado. |

**Mesa de obra es el valor inicial**, por la necesidad principal de cotizar una obra completa. El usuario puede elegir Estudio y la preferencia se recuerda por usuario y organización. Ninguna vista es una modalidad de tarifa ni una función de pago adicional. Galería/tabla es un ajuste de la colección de posiciones dentro de Mesa, no una tercera aplicación.

### Arquitectura de información común

Se preservan las áreas de navegación actuales por rol: **Obras, Clientes, Catálogos, Taller y Empresa**. Dentro de la obra se conservan cuatro destinos comprensibles: **Ventanas, Cotización, Materiales y corte, Actividad**. Los paneles especializados siguen dentro de su destino: Precio y margen, Cobros y Térmica bajo Cotización; Documentos y Comparar revisiones bajo Actividad. No se vuelve a exponer una fila de diez pestañas principales.

El selector de vista está en la cabecera de trabajo de la obra, no escondido en preferencias globales. Es textual, con estado elegido legible. Cambiarlo no dispara guardado, petición generativa, emisión, cambios de estado ni operación de precio. Los vínculos «Abrir editor» y «Volver a obra» son inequívocos y conservan el contexto de retorno.

### Mesa de obra

1. Cabecera con nombre de obra, cliente, referencia humana, revisión actual y estado comercial. Los estados de revisión y de precio se distinguen: «Borrador · precio aplicado» no se resume como libremente editable.
2. Región Ventanas con una acción principal «Añadir ventana», búsqueda y filtros discretos, agrupación opcional por piso/recinto/eje, galería/tabla y conteo real. No hay KPI de relleno.
3. Cada posición muestra dibujo fiel en vista declarada, código/nombre, cantidad, medidas, serie, vidrio, acabado y precio de venta cuando existe. Un precio ausente dice «Sin precio» y un dato faltante dice «Sin dato».
4. Clic selecciona; el botón textual «Abrir editor», miniatura activable y Enter abren la edición amplia. Doble clic puede ser atajo adicional, nunca requisito para descubrir la función. El detalle permite consultar materiales y medidas guardadas, con la acción de edición visible.
5. La selección múltiple tiene contador y alcance explícitos. Duplicar, ubicación, cantidad, cambios globales y eliminar usan los contratos existentes; el cambio potencialmente amplio muestra diff. «Seleccionar visibles» nunca significa toda la obra de forma silenciosa.
6. Cotización pone el documento y sus datos comerciales como objeto principal. Precio/margen es una herramienta del mismo proyecto, no una calculadora paralela. Materiales y corte declara qué es necesidad preliminar y qué pertenece a una OT/revisión liberada.

### Estudio

1. Franja de posiciones compacta a la izquierda o en una banda plegable. Muestra nombre/código y miniatura, permite siguiente/anterior y añadir. No multiplica tarjetas de resumen alrededor del dibujo.
2. El lienzo tiene el espacio predominante; herramientas reconocibles y el inspector solo explican el módulo, paño, división o unión seleccionados. La selección activa se nombra, tiene contorno y controles de manipulación claros.
3. Elevación, planta, sección y 3D son vistas de los mismos datos. Elevación es la entrada; planta se abre automáticamente al trabajar carriles/uniones cuando aporta información, puede plegarse y recuerda su estado por tarea. No mantener una planta grande por defecto en una ventana simple.
4. El inspector manual incluye dimensiones, apertura, vidrio/relleno, acabado y herrajes con progresión a detalles técnicos. No existe «Asistente y alternativas» permanente en su base. Las alternativas manuales se construyen duplicando/comparando; las generativas se delegan exclusivamente desde el popup.
5. La acción principal de edición es «Guardar ventana». El guardado informa pendiente, guardando, guardado o error. «Guardar y volver» conserva posición, scroll, filtros y selección. El usuario siempre sabe si modificó un borrador local o el registro del servidor.
6. Al visitar Cotización, Materiales o Actividad desde Estudio se muestra **el mismo panel funcional de Mesa**; el selector no duplica sus formularios ni endpoints. Al volver a Ventanas reaparece la misma sesión de edición.

### Editor amplio y pantallas pequeñas

«Abrir editor» amplía el editor existente, con identidad de obra/ventana y retorno visible. No abre un modal pequeño ni una segunda ventana del navegador obligatoria. Ambas vistas usan la misma sesión de edición y el mismo `AssemblyEditor`. El editor amplio elimina cromo no esencial y mantiene Guardar/Deshacer/Volver accesibles.

En 1440 y 1280 px caben dibujo e inspector; en 1024 px el inspector se vuelve drawer y el lienzo conserva un tamaño útil. Debajo de 1024 px se mantiene la política actual de lectura técnica del editor, con motivo visible y sin Guardar que parezca roto. Esto no convierte toda la aplicación móvil en lectura: cliente, consulta de obra/documentos, filtros y flujos de terreno siguen sus permisos propios. No prometer un CAD táctil completo como parte de este rediseño.

## Contrato de estado y navegación

### Rutas elegidas

La identidad de obra sigue en `/projects/:id`. Se añade `view=mesa|estudio`, independiente del `section` existente; `position=<id>` identifica la posición activa. Ejemplos:

```text
/projects/:id?view=mesa&position=:positionId
/projects/:id?view=estudio&position=:positionId
/projects/:id?view=estudio&section=quote&position=:positionId
/projects/:id/positions/:positionId/edit?view=mesa
/projects/:id/positions/new?view=estudio
```

El último ejemplo abre la misma creación manual. Las rutas antiguas sin query siguen funcionando. `section=quote|pricing|payments|thermal|production|documents|activity|imports|compare` conserva su semántica. Un valor desconocido se normaliza a un estado válido sin escribir negocio. No se introducen rutas separadas `/studio` y `/desk` con proyectos duplicados.

Prioridad de vista: query válida → preferencia del usuario/organización → Mesa. La posición de query se valida contra la obra y los permisos; después se usa la última selección de esa obra; después la primera posición visible por orden real. Una posición eliminada o ajena nunca recupera datos desde otra caché. El cambio deliberado de sección/posición deja historial navegable; cambiar presentación usa `replace` para no llenar Atrás de cambios cosméticos. Atrás/Adelante restauran un estado coherente.

El retorno desde el editor no admite una URL arbitraria: reconstruye una ruta interna de la misma obra con vista, sección y posición válidas. Filtros y scroll se conservan como estado de UI, no como campos del documento ni de la huella del motor.

### Una autoridad para cada clase de estado

| Estado | Dueño y persistencia | Regla de ambas vistas |
|---|---|---|
| Obra, posiciones, cliente, cantidad, ubicación y versión técnica | Servidor; consulta compartida por organización/obra. | Ambas consumen `useProjectView/projectKey`, sin copias divergentes ni carga completa duplicada al cambiar vista. |
| BOM, cortes, pesos y números derivados | Motor y snapshots asociados. | Nada se calcula en CSS, miniaturas, componentes de tabla o LLM. |
| Precio indicativo | Resultado de simulación de entradas/revisión exactas. | Se invalida si cambia diseño/cantidad/serie; no sustituye el aplicado ni habilita emisión. |
| Precio aplicado, revisiones emitidas y documentos | Autoridad comercial/documental del servidor. | Un selector visual no descongela ni actualiza estos artefactos. |
| Vista preferida | Preferencia de UI por usuario y organización. | Se recuerda sin crear una preferencia de catálogo ni mutar la obra. |
| Posición activa, lote marcado, filtros y agrupación | Sesión por usuario/organización/obra. | Viajan entre vistas. Selección activa, lote y foco son conceptos distintos. |
| Selección física del lienzo | Sesión de edición de la posición. | IDs estables módulo/paño/unión; se reconcilian después de undo/receta y nunca apuntan a un objeto inexistente. |
| Inputs de edición y undo/redo | **Una sesión de edición** para la posición activa, por encima de sus distribuciones visuales. | Cambiar vista, ampliar editor o abrir otra sección no reejecuta `loadDesign` ni vacía la historia. |
| Recuperación tras recarga | Buffer local explícito, no guardado del servidor. | Restaurar o descartar; declarar fecha, proyecto y posición. No se aplica automáticamente. |
| Formularios de propuesta, cobros, importación y térmica | Sus controladores existentes, conservados al visitar secciones. | Cambiar vista no remonta un formulario y pierde entradas. Cambiar identidad limpia el estado cargado. |
| Popup opcional de IA | Contrato separado del paquete. | Cerrado no reserva espacio; ausencia de IA no afecta estas autoridades. |

Se necesita un contenedor de estado de obra por `userId:orgId:projectId` que mantenga la sesión a través de las rutas internas y de ambas vistas. La clave técnica de caché `projectKey(orgId,id)` puede mantenerse; el contenedor se reinicia al cambiar usuario/rol y se respetan los mecanismos de limpieza de autenticación. No es una segunda copia persistida de la obra.

### Guardar, recuperar y salir

- El usuario edita localmente; el motor evalúa con entradas identificadas. Mientras hay respuesta anterior/debounce, el dibujo puede seguir visible con «Calculando», pero no se llama actual al precio viejo ni se habilita guardar con resultado obsoleto.
- «Guardar ventana» mantiene `expected_updated_at` para registro existente y los gates técnicos. Solo una respuesta confirmada cambia la base y dice «Guardado».
- Cambiar Mesa/Estudio o abrir el mismo editor amplio conserva sesión y no muestra confirmación redundante. Elegir **otra** posición con cambios pide Guardar / Descartar / Cancelar. Escape equivale a cancelar esa navegación.
- Navegar fuera de la obra, cambiar organización o cerrar una sesión con borrador mantiene el guard pertinente. No guardar por sorpresa para permitir salir. El prompt de auth no puede exponer la obra de la sesión anterior.
- En 409 se conserva el borrador y se ofrece comparar/cargar la versión actual antes de reintentar. No sustituir el timestamp por el nuevo y reenviar silenciosamente el diseño viejo.
- Un alta con respuesta perdida mantiene estado incierto y consulta/reconcilia la operación antes de repetir. No desactivar `uncertainCreate` ni inventar éxito. Las operaciones de proyecto conservan clave de reintento y firma.
- El buffer local incluye versión de formato, usuario, organización, proyecto, posición o ID de creación, revisión, baseline/firma de origen y fecha. El código actual usa `org:position|copy|new`, insuficiente para dos altas nuevas de obras diferentes. Los borradores anteriores no se borran masivamente: se recuperan solo con identidad demostrable; un `new` ambiguo no se injerta en otra obra.
- La recarga ofrece recuperar datos compatibles. Si cambió baseline/revisión, la recuperación muestra diferencia y exige decisión; no convierte el borrador previo en edición de la nueva revisión ni reutiliza su evaluación calculada.

### Revisiones y concurrencia

Se conservan los tres bloqueos de `editable`: fase distinta de DRAFT, versión sellada de la revisión actual o precio aplicado. La UI los nombra por separado y ofrece el recorrido permitido existente: revisar precio, retirar/revisar precio borrador cuando sea válido, crear revisión sucesora o consultar documentos. Nunca eliminar el bloqueo para que la nueva vista aparente funcionar.

Una revisión emitida se consulta, compara y usa como origen conforme al contrato existente; no se edita su snapshot. La siguiente revisión conserva referencias/historia y obtiene su propia autoridad comercial. En producción comprometida se respetan las restricciones de sucesión. Reordenar posiciones no renumera códigos físicos. Duplicar diseño no copia medición del vano físico ni precio aplicado como si correspondieran al nuevo destino.

## Producto manual completo, sin dependencia de IA

| Trabajo | Interacción manual exigida | Base actual que se conserva |
|---|---|---|
| Crear obra/cliente | Formulario legible, vincular cliente real o crear ficha; referencias opcionales claras. | `ProjectMetadataForm`, `ClientEditor`, rutas existentes. |
| Usar preferencias | Serie/vidrio/acabado habituales editables; alcance empresa/obra/posición visible. | `DesignDefaults.tsx`, autoridad resuelta del backend. |
| Añadir ventana | Elegir fabricante/serie exacta, configuración compatible, medidas, relleno, acabado y cantidad. | `ProjectPositionLibrary`, `StarterGallery`, `sourcedStarter`, diseño por motor. |
| Dibujar/cambiar apertura | Selección sobre lienzo; dimensiones y aperturas físicas con reglas/fuente; divisiones y uniones. | `AssemblyEditor`, `OpeningPalette`, `openingChoices`, registro de operaciones. |
| Modificar muchas | Selección con alcance, formulario de cambio y diff; aplicar/deshacer sin chat. | `PositionCollection`, `useProjectOperations`, `QuotationGlobalChanges`. |
| Comparar variantes | Duplicar y editar manualmente; comparación conservando origen y cifras del motor. | Duplicación, revisiones/comparación existentes; adaptar sin generador LLM obligatorio. |
| Definir precio | Costos privados, métodos disponibles, lista, margen/descuento y aprobación cuando corresponda. | `ProjectPrices`: costo+margen, m² por tipología, matriz por medidas, margen de proyecto y lista con descuentos. |
| Preparar propuesta | Completar condiciones y presentación, guardar original estructurado, vista previa/emitir según contrato. | `QuotationDocument`, `ProjectQuotationPanel`, documentos existentes. |
| Revisar materiales | Lista trazable por obra/ventana, vidrio, perfiles, herrajes y preparaciones disponibles. | `ProjectMaterials`, `ProjectBom`, contratos de lectura. |
| Mantener catálogo | Formularios, adjuntar fuente, plantilla XLSX/CSV, revisión de diff y publicación autorizada. | `CatalogPage/catalogModel`, `CatalogImportsPanel`, editores de autoridad. |

No se inventa soporte de precio por metro lineal o «total final objetivo» donde el registro actual no lo implemente. El PRD los menciona como intención histórica; si se amplía un método, pertenece al motor comercial y a una decisión documentada, nunca a aritmética de UI. El usuario debe entender margen frente a recargo sin imponer una fórmula nueva al contrato vigente.

Un plan sin IA no muestra huecos de chat, avisos de créditos en el flujo principal ni botones manuales deshabilitados por ausencia del proveedor. La importación estructurada y los formularios no consumen IA. Adjuntar un PDF como evidencia no equivale a delegar su interpretación generativa. Esa delegación se pide expresamente desde el popup opcional.

## Editor y catálogo: condiciones de confianza

Apertura nueva = movimiento, dirección, bisagra, rol de hoja, uso, receta/carriles y herrajes compatibles. Fijo en marco no se confunde con fijo en hoja; francesa no se fabrica como dos huecos con montante; vista interior/exterior no cambia el dato técnico. No ofrecer movimientos avanzados sin receta válida solo para completar una galería. Se conserva el transporte histórico de posiciones antiguas sin reinterpretarlo con autoridad nueva.

Catálogo = **fabricante → serie/sistema → configuración/artículos**, con versión y fuente. PRO6004 y PROSLIDE70 pertenecen a Proline; «60/70» puede ayudar a buscar, pero no es prueba de equivalencia ni una regla técnica. Fabricante, distribuidor y titular del documento son identidades distintas. «Vinhaus» sigue sin resolver: no fusionar automáticamente Winhouse, Winhaus.cl u otros nombres parecidos.

La biblioteca no está vacía: hoy muestra sistemas en lista plana y ya tiene secciones/datos de preparación. El rediseño mejora descubrimiento y jerarquía sin borrar la DB. DEMO permanece disponible en laboratorio/filtros explícitos y en revisiones que ya lo referencian; se retira de la entrada comercial normal. Una serie real incompleta puede verse como referencia con causas, pero no fabricarse ni cotizarse si falta la autoridad correspondiente.

Las fotos ayudan a reconocer; las secciones, fichas y fuentes explican qué es el artículo. Si no hay imagen legítima, usar dibujo técnico disponible o estado honesto, sin foto genérica que aparente una ventana certificada. Los precios de compra son privados de empresa y no se publican junto con las fichas técnicas compartidas.

## Competencia por tarea: referencias que sí aportan

| Tarea | Fuente concreta | Decisión que inspira; límite |
|---|---|---|
| Elegir apertura por campo | [Logikal insertion selection](https://help.orgadata.com/en/documentation/input-of-elements/windows-and-doors/element/insertion-selection/) | Tipos físicos y contexto seleccionado. Manual leído, no runtime usado. |
| Orientarse al diseñar | [Logikal user interface](https://help.orgadata.com/en/documentation/input-of-elements/user-interface/) | Fases y dibujo como referencia. No copiar una cinta densa de escritorio. |
| Catálogo técnico reconocible | [Logikal system articles](https://help.orgadata.com/en/documentation/database/system-articles/) | Proveedor, artículo, dibujo y datos relacionados. No usar sus fórmulas. |
| Recuperar estado anterior | [Logikal position history](https://help.orgadata.com/en/documentation/project-centre/position-history/) | Recuperación como nueva posición independiente; no demuestra inmutabilidad de emisión. |
| Presentar configuración coherente | [V6 X3D, 25-08-2026](https://www.cyncly.com/resources/news/v6-advantage-visualizer-award) | Configuración web bajo reglas comunes. Afirmación del fabricante; no medición visual/runtime propia. |
| Un solo pedido entre canales | [Cantor iQuote](https://www.a-w.com/software/cantor-iquote/) y [ERP/CIM](https://www.a-w.com/aw-cantor/aw-erpcim/) | Continuidad de dato de venta/material/planta. No convertir el cotizador pyme en un ERP obligatorio. |
| Rol y fase correctos | [Schüco FDC](https://www.schueco.com/uk/fabricators/digital-solutions/fabrication-data-center) | Información de estación distinta de oficina; QR/CNC no invaden la cotización. |
| Comprar con revisión | [SchüCal/Connect](https://www.schueco.com/de-en/fabricators/digital-solutions/schuecal) | BOM a carrito para revisión humana. Preparar y emitir pedido son actos distintos. |

Matriz documental ampliada: `../2026-10-18-revision-profunda/competidores-ingenieria.md` y su JSON. No se atribuyen colores, atajos, velocidad ni calidad estética no observados a las capturas del buscador sin píxeles.

## Gaps actuales comprobados y trabajo concreto

| Hecho actual y localizador | Qué conservar | Ajuste requerido |
|---|---|---|
| `useProject.ts:15`, `projectKey`: consulta compartida por org/obra. | Caché y autorización existente. | Añadir estado de UI de las dos vistas alrededor de esa lectura; no duplicar endpoints. |
| `ProjectPages.tsx:338/344`: cuatro destinos y paneles; `ProjectWorkspace` tiene selección local y `visited`. | Jerarquía y conservación de formularios visitados. | Selector Mesa/Estudio, selección/ruta/retorno compartidos y sesión de edición estable. |
| `PositionCollection.tsx`: `view=list|grid`, filtros, `checked`, `activeId`, teclado y virtualización. | Galería/tabla, selección por lote y navegación. | No confundir estos formatos con las dos vistas; persistir y comunicar alcances al cambiar layout. |
| `ProjectPositionEditor.tsx:331`, `PositionWorkspace`: editor real con API de opciones y motor. | Cálculo, guardas, baseline y guardado existente. | Extraer/reutilizar su controlador y presentación sin copiar otro editor para Estudio. |
| `ProjectPositionEditor.tsx:634`, `positionDraft.ts:17`: buffer local ya existe. | Recuperación explícita y guard de cambios. | Identidad usuario/obra/creación y baseline; el `new` actual colisiona entre obras de la misma org en la misma pestaña. Es un riesgo estático, no un incidente runtime probado. |
| `ProjectOpsReview.tsx:19`: preview/apply/undo, `before_sig` y `operation_key`. | Operaciones de lote y concurrencia. | Una sola instancia compartida; reconciliar selección/cache tras aplicar o deshacer en cualquiera de las vistas. |
| `backend/projects/project_ops.py:460–496`: estado, preview, apply y undo. | Registro tipado y autorización por servidor. | Usar estos contratos; no permitir escritura directa desde una nueva tabla visual. |
| `backend/projects/service.py:118/136/565/885`: `editable`, `unchanged`, `save_position`, `start_successor`. | Locks, concurrencia y revisiones. | Explicar bloqueos y ruta de recuperación; no suprimirlos para mejorar apariencia. |
| `AssemblyEditor.tsx:3734`: details «Asistente y alternativas» con `AssistantPanel` y `AlternativesPanel`. | Operaciones registradas y puente de diseño; no el panel incrustado. | Quitar el panel permanente y migrar delegación al popup global. Las alternativas generativas consumen proveedor: no presentarlas como comparación manual gratuita. |
| `canvasStore.ts`: undo/redo, `commitInputs`, `acceptIntent`, `reconciledSelection`; `canvasSession.ts` limpia autenticación. | Historia y reconciliación. | Cambiar layout no debe cargar de nuevo/resetear; limpiar a tiempo al cambiar identidad. |
| `physicalOpenings.ts:204` y `OpeningPalette.tsx:56`: opciones desde capabilities/recetas. | Semántica física y filtro, con fallback histórico. | Diagnosticar bloqueo/selección/catálogo antes de inventar otra paleta. La auditoría anterior sí cambió una bisagra y deshizo. |
| `CatalogPage.tsx:278/365`: lista plana, fabricante como prefijo. | Sistemas, filtros base y recursos reales. | Entrada por fabricante y versiones en detalle; no afirmar que no había datos. |
| `SystemWorkspace.tsx`, `ArticleCard`: secciones y procedencia; `catalogModel.ts` contiene manufacturer/family. | Evidencia, dibujo y editores técnicos. | Jerarquía y medios útiles; aprovechar los campos antes de crear un modelo paralelo. |
| `CatalogImportsPanel.tsx`: plantilla XLSX/CSV, filas revisables, diff, token y publicar/deshacer. | Flujo manual estructurado y revisión. | Separarlo de PDF/IA opcional; exponerlo por función y no como formulario inmenso en la portada. |
| `ProjectPrices.tsx:868`, `QuotationDocument.tsx:133`, `ProjectMaterials.tsx:74`. | Herramientas manuales presentes. | Un único acceso coherente desde ambas vistas; no reemplazarlas por mockups ni reimplementar cálculos. |

## Vacíos, errores y recuperación

| Situación | Presentación y acción exigidas |
|---|---|
| Obra nueva, sin ventanas | Explicar que todavía no hay posiciones; una acción «Añadir ventana». En Estudio abre biblioteca; en Mesa abre la misma creación. Sin sugerencia de hablar con IA para empezar. |
| Solo hay DEMO | Explicar que faltan series reales preparadas; abrir Catálogos o «Ver laboratorio» explícito. No ocultar todas las opciones dejando un selector sin explicación. |
| Serie real de referencia | Mostrar fuente e información disponible; causa de bloqueo y rol/enlace de revisión. No etiqueta verde universal «Listo». |
| Sin resultado de búsqueda | Mantener búsqueda visible y «Limpiar filtros»; no afirmar que la obra/catálogo no tiene registros. |
| Sin posición seleccionada | Mostrar resumen/primera posición válida; selección de lote no desaparece por ello. No abrir editor de ID ajeno. |
| Error de lectura | Causa legible y Reintentar del mismo recurso/org; los datos parciales visibles se identifican como anteriores. No sustituir por una pantalla vacía exitosa. |
| Opciones técnicas no cargadas | Conservar dibujo; indicar carga/error de la serie, bloquear solo edición que depende de opciones y permitir reintentar. |
| Evaluación inválida | Señalar campo/objeto y causa concreta; mantener inputs corregibles, deshacer y última base guardada. No arreglar con una sugerencia IA obligatoria. |
| Guardado en curso/error | Estado junto a Guardar; prevenir duplicación. Error conserva edición. Guardado incierto no dice finalizado. |
| 409 o revisión cambiada | Comparar/cargar servidor, conservar borrador y explicar qué cambió; no pisar a otra persona. |
| Sin permiso | Tarea disponible en lectura y responsable que puede ejecutarla; ocultar únicamente acciones no pertinentes. RLS continúa autorizando. |
| Dibujo sin WebGL | 2D y especificación disponibles; error/limitación 3D sin bloquear diseño ni cotización. |
| Documento/precio bloqueado | Checklist por causa y enlace exacto al campo/rol; sin «falta completar» genérico ni botón muerto. |

## Entrega y campaña final

La implementación se realiza en secuencia: fundamentos del paquete → prompt 02 cotizador/dos vistas → prompt 03 editor/catálogos → restantes módulos del paquete → **una campaña final integrada**, seguida de correcciones y repetición solo de casos afectados. Este contrato no ordena correr toda la suite en cada fase.

Durante desarrollo se mantienen pruebas existentes y se preparan los casos necesarios para cambios con riesgo; no se debilitan guardas ni se borran goldens. La fase final comprobará, con la IA deshabilitada, crear obra/cliente, añadir varias posiciones, alternar vistas durante una edición, guardar/recargar, lote/diff/undo, precio, propuesta y revisión. También verificará identidad/caché/borradores, concurrencia, roles, aperturas, 2D/3D, catálogo real y los estados de error en los anchos requeridos. Su ausencia de ejecución hasta esa fase se declara expresamente; nunca se llama «listo» a un prompt completado sin esa evidencia final.
