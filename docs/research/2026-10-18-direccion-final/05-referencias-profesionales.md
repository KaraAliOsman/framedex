# Referencias profesionales: qué tomar, por qué y hasta dónde

Consulta: 18-10-2026. Complemento del [contrato visual](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/02-diseno-y-referencias.md). Estas referencias afinan el producto manual elegido; no reabren la elección entre Mesa de obra y Estudio ni sustituyen los contratos del encargo. No se modificó código del producto ni se declara una apariencia aprobada.

## 1. Alcance y método

Se seleccionaron **17 fuentes oficiales adicionales** de Apple, Pentagram, Adobe, Shapr3D e IBM/Carbon, y se conectaron con tres referencias sectoriales ya estudiadas: Logikal, V6 y 3E. No son veinte competidores de ventanas: son veinte fuentes con una función concreta en el diseño. El dossier de quince competidores permanece en la [investigación profunda](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-revision-profunda/matriz-completa.md).

Se leyeron los textos primarios y fragmentos pertinentes de las transcripciones de WWDC y Adobe Learn. **No se reprodujeron esos vídeos ni se operaron las aplicaciones comerciales.** Las imágenes públicas observadas aquí son tres: identidad MIT Media Lab, identidad Windows 8 y composición de Final Cut Pro. Se conserva la separación entre observar una imagen, leer una función y ejecutarla.

| Marca | Significado en este documento |
|---|---|
| DOC | Texto oficial o transcripción leído; acredita lo que documenta su autor. |
| VIS | Imagen pública inspeccionada; acredita su composición visible. |
| RUN | Interacción ejecutada. No hay nuevas pruebas RUN de competidores en esta ampliación. |
| PROP | Decisión propia para DEKOPEN, derivada de necesidades del oficio y contrastada con las fuentes. |
| NV | No verificado: acceso privado, comportamiento real, precisión o integración que la fuente no permite comprobar. |

Las guías [apple-design](C:/Users/alios/.agents/skills/apple-design/SKILL.md) y [emil-design-eng](C:/Users/alios/.agents/skills/emil-design-eng/SKILL.md) ayudaron a formular las preguntas de revisión. No se confunden con evidencia independiente de un producto. Se verificaron fuentes oficiales en lugar de atribuir autoridad a todos los ejemplos de las guías.

## 2. Matriz de referencias y decisiones

La columna de decisión es **PROP**. Una regla de Apple, Adobe o Carbon no adquiere autoridad de cálculo para DEKOPEN.

| ID · fuente primaria | Detalle documentado u observado | Decisión para DEKOPEN | Razón | Límite |
|---|---|---|---|---|
| P01 · [Apple HIG: Typography](https://developer.apple.com/design/human-interface-guidelines/typography) | DOC: jerarquía mediante peso, tamaño y color; estilos combinan tamaño, peso e interlínea. Pide adaptar composición al crecer el texto. Se leyó su [Markdown oficial](https://developer.apple.com/design/human-interface-guidelines/typography.md). | Mantener Plex y roles tipográficos completos; conservar distinción entre título, dato, etiqueta y ayuda al ampliar texto. | La importancia se reconoce antes de leer todo el panel. | Sus puntos y mínimos nativos no se trasladan mecánicamente a píxeles web; no obliga a usar San Francisco. |
| P02 · [WWDC20: The details of UI typography](https://developer.apple.com/videos/play/wwdc2020/10175/) | DOC, transcripción: estilos integran peso/tamaño/interlínea; una variante enfatizada puede distinguir información sin aumentar tamaño. | Grupos del inspector con peso 600, valores con peso legible y ayuda subordinada; párrafos con aire propio. | Evita resolver cada nivel con otro tamaño o con gris cada vez más débil. | No se vio el vídeo completo. Las APIs y ajustes numéricos de UIKit no son receta CSS. |
| P03 · [WWDC18: Designing Fluid Interfaces](https://developer.apple.com/videos/play/wwdc2018/803/) | DOC, transcripción: respuesta inmediata, redirección/interrupción y consistencia espacial son principios separados. | Selección y cota responden al instante; un panel acepta cerrar durante su transición y vuelve a su origen coherente. | La interfaz acompaña cambios de intención sin hacer esperar por coreografías. | No se copia física de iPhone, rebote, rubber-banding o blur; la autoridad de movimiento del personaje es su contrato específico. |
| P04 · [Apple HIG: Modality](https://developer.apple.com/design/human-interface-guidelines/modality) | DOC: una presentación modal bloquea la vista padre; recomienda usarla con beneficio claro y evitar jerarquías modales extensas. Se leyó el [Markdown oficial](https://developer.apple.com/design/human-interface-guidelines/modality.md). | Popup IA modeless; diálogo modal solo para una decisión que lo requiera. Cerrar o minimizar el popup conserva el trabajo. | Cotizar y consultar al asistente deben poder alternarse sin interrumpir el modelo manual. | Es una transferencia de principios. No determina la memoria del agente, sus permisos ni su contrato de ejecución. |
| P05 · [Final Cut Pro: Arrange the main window](https://support.apple.com/en-ca/guide/final-cut-pro/ver2a27194eb/mac) | DOC: navegador, visor, timeline, sidebar e inspector se muestran, ocultan o redimensionan; admite composiciones guardadas. VIS: la imagen oficial diferencia esas regiones. | Dos composiciones nombradas sobre la misma sesión: Mesa y Estudio. Paneles auxiliares se cierran cuando falta espacio. | Se cambia el espacio de trabajo sin inventar otra aplicación ni perder selección. | No se propone un editor arbitrario de workspaces ni una timeline para ventanas. La captura tiene estética oscura que no se adopta. |
| P06 · [Final Cut Pro: Inspectors](https://support.apple.com/en-mide/guide/final-cut-pro/ver15f87af2/mac) | DOC: atributos e inspectores disponibles dependen de los elementos seleccionados; el inspector tiene acceso explícito y atajo. | Cabecera de selección inequívoca y controles correspondientes a ventana/hoja/montante; apertura y cierre visibles. | Evita editar una propiedad sin saber a qué parte se aplicará. | La documentación no prueba hit testing o edición por lote de DEKOPEN. No se copian sus atajos de macOS. |
| P07 · [Pentagram: MIT Media Lab](https://www.pentagram.com/work/mit-media-lab) | DOC: una retícula previa de 7 × 7 sustenta el monograma y un sistema para 23 grupos. VIS: símbolo y nombre conservan un orden y una alineación claros. | Una gramática compartida de proporciones, títulos, reglas y códigos conecta cotización, plano y etiqueta, con composición propia por tarea. | Coherencia permite variedad sin que cada salida parezca de otra empresa. | Es identidad y señalética, no prueba de usabilidad de un ERP. No se copian glifos, retícula literal o Helvetica. |
| P08 · [Pentagram: Windows](https://www.pentagram.com/work/windows) | DOC: la identidad Windows 8 vuelve a la metáfora de ventana; describe redibujo óptico del travesaño según tamaño. VIS: marca plana, símbolo y nombre separados. | Conservar identidad DEKOPEN ligada al oficio y revisar legibilidad real en riel, PDF y etiqueta. Preparar variante óptica solo si el tamaño la exige. | El símbolo debe sobrevivir a su soporte; un SVG escalado no garantiza lectura en una etiqueta. | Referencia histórica de marca; no recomienda copiar Metro, logo de Microsoft ni rediseñar ahora la marca de DEKOPEN. |
| P09 · [Illustrator: Properties panel](https://helpx.adobe.com/illustrator/desktop/get-started/learn-the-basics/properties-panel-overview.html) | DOC: sin selección muestra ajustes de documento; con selección muestra propiedades pertinentes; en selección múltiple, propiedades compartidas. | Inspector con estado sin selección útil, selección explícita y valores mixtos rotulados. Acciones comunes en lote solo cuando son compatibles. | Reduce opciones irrelevantes y hace visible el alcance del cambio. | Lectura de ayuda, sin operar Illustrator. La compatibilidad mecánica se decide con el modelo/catálogo propio. |
| P10 · [Adobe Learn: Format text in InDesign](https://www.adobe.com/learn/indesign/web/text-formatting-overview) | DOC y transcripción: estilos de párrafo/carácter centralizan formato; sus overrides locales se distinguen del estilo. | Roles de documento compartidos por plantilla y ámbito explícito “esta obra/empresa”. No introducir un procesador de textos libre. | Corrige consistencia sin editar cada bloque a mano ni propagar un cambio local por accidente. | La transferencia es estructural. No obliga a comprar Adobe, importar sus plantillas o convertir emitidos históricos. |
| P11 · [InDesign: Preflight panel](https://helpx.adobe.com/indesign/desktop/print/preflight/configure-and-use-the-preflight-panel.html) | DOC: agrupa problemas detectados, explica detalles/correcciones y permite llegar a contenido afectado. | Revisión documental con problema, página/posición y acción concreta; diferenciar contenido, composición y autoridad de emisión. | Una persona puede resolver el defecto sin buscarlo en todas las páginas. | Preflight editorial no equivale a validar fabricación, precios, RLS o CNC. No añadir un escáner general sin capacidad real. |
| P12 · [InDesign: Set reading order](https://helpx.adobe.com/indesign/desktop/interactive-elements-and-forms/forms-and-pdfs/set-reading-order.html) | DOC: el orden del contenido para exportación es distinto de su posición visual; PDF etiquetado requiere configuración explícita. | Orden lógico de títulos, posiciones, importes y condiciones; conservar texto seleccionable y comprobar extracción/lectura en el cierre final. | Una composición a dos columnas debe seguir teniendo sentido fuera de su apariencia. | No se afirma conformidad PDF/UA ni etiquetado accesible por existir un PDF; depende del renderer y validación efectivos. |
| P13 · [Shapr3D: Adaptive user interface](https://support.shapr3d.com/hc/en-us/articles/7873882619548-Adaptive-user-interface) | DOC: herramientas pertinentes se ofrecen según preselección; otras válidas se acceden mediante More. | Selección de hoja ofrece aperturas compatibles; selección de división ofrece su edición; el resto va a Más/Avanzado con nombre. | La aplicación puede ayudar determinísticamente sin IA, preguntas ni una parrilla de todas las herramientas. | Ayuda contextual no demuestra IA o automatización. No se importan operaciones de CAD sólido a un motor de fenestración. |
| P14 · [Shapr3D: Selecting geometry](https://support.shapr3d.com/hc/en-us/articles/7770768736924-Selecting-geometry) | DOC: filtros por tipo, relaciones destacadas y lista de candidatos cuando se superponen entidades; la selección se mantiene visible. | Desambiguar hoja/perfil/montante cuando coinciden; sincronizar árbol, lienzo e inspector. Mostrar relaciones pertinentes sin rellenar todo el conjunto. | La persona debe poder elegir una pieza estrecha sin adivinar qué recibió el clic. | Se documenta el patrón, no se ejecutó. No exige Select Through ni todo el sistema de restricciones de Shapr3D. |
| P15 · [Shapr3D: 2D Drawings](https://support.shapr3d.com/hc/en-us/articles/7874466328348-2D-Drawings) | DOC: vistas base/proyectadas/sección/detalle, propiedades de hoja/unidades y cajetines con variantes. | Plano con vistas derivadas y relacionadas, escala/unidad declaradas y cajetín por página; ampliar detalle antes que reducir texto. | El plano comunica ensamble y revisión; cada vista tiene una función. | No autoriza copiar cotas, tolerancias, precisión o edición manual de campos sellados. Las medidas siguen viniendo del motor. |
| P16 · [Carbon: Data table](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines) | DOC: distingue expansión, selección y acciones por lote; propone alturas por densidad y acciones con blanco propio. | En Mesa, abrir detalle, seleccionar para lote y abrir menú son acciones distintas. Materiales usa filas de 40 px; posiciones conservan espacio para dibujo. | Evita que tocar una fila cambie selección, cantidad y vista a la vez. | No instalar Carbon para cambiar el aspecto. Su catálogo de tamaños no fija la altura de una ficha técnica DEKOPEN. |
| P17 · [IBM Design Language: Typeface](https://www.ibm.com/design/language/typography/typeface/) | DOC: Plex reúne subfamilias Sans/Mono/Serif/Condensed y recursos tipográficos relacionados. | Conservar Sans para interfaz/comunicación y Mono para dimensión/código cuando ayuda a comparar. | Una familia coherente ya disponible puede ganar calidad mediante composición. | IBM no dicta usar Mono para todo número ni garantiza funciones OpenType del archivo local; verificarlas antes de depender de ellas. |
| P18 · [Logikal: 3D view](https://help.orgadata.com/en/documentation/input-of-elements/user-interface/3d-view/) | DOC, ya contrastado: vistas interior/exterior/laterales, rotación y funciones de apertura descritas. | Separar cámara, cara de observación y modificación de apertura. | Un giro visual no debe cambiar la mano ni crear otro estado fabricable. | Manual público, no producto operado. No todas las hojas tienen por qué admitir la misma simulación. |
| P19 · [V6: Modules](https://www.cyncly.com/en-GB/products/soft-tech-v6/modules) | DOC, ya contrastado: Drawing y Automation son capacidades distintas; el dossier conserva un plano público con elevaciones/secciones/cajetín. | Documentos técnicos útiles por sí mismos; salida industrial específica con su propia validación y autoridad. | Descargar un plano no demuestra compatibilidad de máquina. | No se probó V6 ni su posprocesado. No copiar datos de la lámina de muestra. |
| P20 · [3E: Mobile solutions](https://www.3e-it.com/en/window-design-software/mobile-solutions) | DOC, ya contrastado: información por componente y evidencia de campo; menciona NFC. | Terreno parte de la unidad asignada y su trabajo pendiente, con código humano y evidencia. | La continuidad de identidad aporta más que añadir un QR a cualquier pantalla. | NFC y QR son medios distintos. No se afirma prueba de escaneo, firma u offline en DEKOPEN. |

## 3. De la referencia a decisiones de oficio

### 3.1 Jerarquía: contexto, pieza, decisión y ayuda

El orden en el inspector será: **qué se edita → valor actual → cambio permitido → consecuencia o falta**. Una cabecera como “P-03 · Hoja 2” tiene mayor peso que “Propiedades”; la unidad permanece junto a la medida y la ayuda permanece junto al campo. El color nunca es la única diferencia entre valor, enlace y bloqueo.

Los roles tipográficos del contrato visual se implementan como parejas completas de tamaño/interlínea/peso. Ajustar solo `font-size` en cada pantalla rompe la misma jerarquía que se quiere recuperar. En texto largo se amplía interlínea o se hace reflujo; no se convierte la ayuda importante en letra pequeña atenuada. La tabla de posiciones y las instrucciones de operario tienen ritmos distintos por su tarea, aunque comparten familia.

**No se adopta una piel Apple.** Sus principios de respuesta, jerarquía y continuidad se aplican con Plex, tokens de DEKOPEN y reglas del oficio. No añadir San Francisco, vidrio esmerilado, sombras de color, luz especular o rebotes al cotizador por haber consultado HIG. El movimiento propio del personaje del asistente se rige por su encargo específico.

### 3.2 Lienzo, colección e inspector: tres trabajos diferentes

La colección responde “¿qué ventanas tiene esta obra?”. El lienzo responde “¿qué estoy construyendo?”. El inspector responde “¿qué puedo cambiar aquí?”. No se repite una colección completa dentro del inspector ni se introduce un chat fijo como cuarta región.

Final Cut demuestra documentalmente que una herramienta profesional puede reorganizar regiones sin alterar el proyecto. DEKOPEN toma esa continuidad para **dos vistas definidas**, con preferencia persistida, y conserva un mismo editor amplio. Abrirlo desde Mesa vuelve a la misma posición y vista. No se pide al usuario diseñar su workspace antes de cotizar.

El inspector conserva orden de grupos y título de selección estable. Sin selección muestra contexto útil y cómo seleccionar; con varias posiciones muestra cantidad, propiedades comunes y valores **Varios**. Un valor mixto no se sustituye visualmente por el de la primera ventana. Si parte de la selección no admite un cambio, se explica antes de aplicarlo y no se finge éxito general.

En 1.024 px se abre como drawer contextual. Bajo ese ancho se mantiene la política actual del editor técnico en lectura, con motivo y retorno a tareas disponibles. No se usa una referencia de CAD en iPad como promesa de CAD táctil ya implementado.

### 3.3 Selección sin adivinación

El contorno/tinte localizado de selección sobrevive al material y es distinto de un requisito cumplido. Hover es transitorio; selección es persistente; foco identifica el control que responde al teclado. No pueden ser tres nombres para el mismo relleno verde.

Cuando hoja, junquillo y montante coinciden visualmente, se ofrece un candidato identificable o un selector explícito de nivel, según lo que permita el modelo. El árbol y el inspector señalan la misma entidad. La UI puede ampliar el área de impacto sin cambiar el espesor físico ni alterar las cotas.

Una selección da acceso a las acciones **válidas para ella**. Eso es trabajo de la aplicación manual, no una prestación del plan IA. Abrir hoja o cambiar mano siguen los comandos y compatibilidades del motor; una lista contextual no inventa una operación ausente.

### 3.4 Identidad coherente y variedad con propósito

Pentagram aporta una disciplina: la forma puede nacer de una idea concreta y extenderse mediante reglas. Para DEKOPEN, esa idea ya existe en la ventana/perfil y en la relación entre dibujo y documento. El trabajo pendiente está en aplicarla consistentemente.

Una cotización necesita lectura comercial; un plano necesita relaciones geométricas; una etiqueta necesita identificación a distancia. Comparten proporciones, tipos, reglas y calidad de dibujo, con orden y densidad propios. La uniformidad de todos los componentes no es un objetivo. Las tres plantillas comerciales cambian composición de verdad, sin convertir cada una en otra identidad.

No rediseñar el logotipo por esta investigación ni importar las marcas de las referencias. Revisar su tamaño real en riel, papel y etiqueta permite decidir si requiere variante óptica; esa decisión se toma sobre evidencia de lectura.

### 3.5 Documento diseñado y verificable

Los estilos se centralizan por función: título de oferta, sección, identificación de posición, especificación, importe, dimensión, condición y pie. El usuario controla contenido/composición permitidos y el ámbito obra/empresa; no necesita reconstruir una plantilla mediante tamaños arbitrarios por bloque.

La revisión documental presenta faltantes localizables: página o posición afectada, causa y acción. Separa lo editorial de un bloqueo de emisión ya existente. No se agregan requisitos comerciales nuevos por inspiración de otra aplicación.

El orden de lectura se diseña junto al layout. Una propuesta debe conservar título, posiciones, importes y condiciones al seleccionar o extraer texto. Una imagen de página o un render visual impecable no acredita ese orden. El cierre 07 debe contrastar el PDF real; etiquetado o conformidad accesible solo se anuncian si se implementaron y verificaron.

### 3.6 Respuesta y control de la persona

Seleccionar, escribir una cota, mover una vista y pulsar un botón dan feedback inmediato. Confirmar guardado, emisión o avance físico depende de la respuesta persistida; la rapidez visual no permite anunciar un éxito todavía no confirmado.

Una transición corta puede explicar de dónde sale un panel. No debe impedir cerrarlo, cambiar de selección o volver al trabajo. El movimiento durante arrastre sigue el puntero; las animaciones de entrada/salida usan solo lo que ayuda a entender el cambio. Se conserva la preferencia de movimiento reducido.

El popup IA es global, opcional y modeless. El detalle de su personaje y movimiento se concreta en [06 · Grok Bot: personaje y movimiento](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/06-grok-bot-personaje-y-movimiento.md); este documento no inventa sus formas o estados. La fidelidad solicitada es principalmente al personaje animado; los estilos compatibles se adaptan a DEKOPEN sin imponer todo el chat o desktop de la referencia. El panel manual sigue disponible y el resultado delegado apunta al objeto real. Un diálogo de emisión mantiene la única decisión modal activa y el foco vuelve a su origen al cerrarse.

## 4. Evidencia visual nueva, con procedencia

Son **copias temporales de imágenes publicadas**, observadas el 18-10-2026. Permanecen en `.run/`; no son assets autorizados para integrar en el producto. Su fuente pública permite volver a consultarlas. No se recortaron ni alteraron para aparentar otra interfaz.

| Evidencia local | Fuente y lo realmente visible | Uso y límite |
|---|---|---|
| [pro-pentagram-mit.jpg](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/pro-pentagram-mit.jpg) | [Pentagram, MIT Media Lab](https://www.pentagram.com/work/mit-media-lab). Monograma negro de trazo consistente; nombre en tres líneas, alineado con el bloque del símbolo; blanco alrededor. | Estudio de relación símbolo/texto y alineación. Esta imagen sola no muestra los 23 grupos: ese dato procede del texto oficial. |
| [pro-pentagram-windows.jpg](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/pro-pentagram-windows.jpg) | [Pentagram, Windows](https://www.pentagram.com/work/windows). Símbolo de ventana en perspectiva, plano cian y nombre separados por espacio claro. | Estudio de metáfora y legibilidad de marca. El redibujo óptico se documenta en la página; no se deduce de una imagen única. |
| [pro-finalcut.png](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/pro-finalcut.png) | [Apple, composición de Final Cut](https://support.apple.com/en-ca/guide/final-cut-pro/ver2a27194eb/mac). Biblioteca a izquierda, medios, visor central, inspector a derecha y timeline inferior; divisiones y selección identificables. | Estudio de regiones y jerarquía espacial. No acredita persistencia ni redimensionado por observación: esas funciones proceden del manual. No se copia el tema oscuro. |

![Regiones de trabajo en una imagen oficial de Final Cut Pro](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/pro-finalcut.png)

La imagen es evidencia del producto de Apple, no una propuesta de diseño DEKOPEN. Las referencias técnicas de ventana, plano y taller permanecen en [evidencia visual sectorial](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-revision-profunda/evidencia-visual.md) y en R01–R24 del contrato visual.

## 5. Cambios exigibles y su justificación

| Before | After | Why |
|---|---|---|
| Panel con opciones de varios niveles, sin alcance visual suficiente. | Título de selección, propiedades pertinentes y acceso explícito a las demás. | Reduce cambios en la entidad equivocada y lectura irrelevante. P06/P09/P13. |
| Limpiar equivale a quitar detalles o bajar su contraste. | Importancia expresada por posición, peso, espacio y estados semánticos. | Un dato secundario puede seguir siendo legible; uno decisivo no debe desaparecer. P01/P02. |
| Cambiar de composición parece cambiar de aplicación. | Mesa/Estudio y editor amplio conservan una sesión, posición, borrador y retorno. | Las regiones cambian para la tarea, el trabajo continúa. P05. |
| Clic sobre geometría estrecha produce un resultado difícil de interpretar. | Candidato identificado, selección localizada y árbol/inspector sincronizados. | El usuario controla qué parte modifica. P14 y necesidades de fenestración. |
| Todas las salidas tienen la misma estructura visual. | Gramática común con cotización, plano, corte y etiqueta específicos. | Cada soporte tiene un lector y una tarea. P07/P08/P15. |
| Documento validado solo porque renderiza o se ve bien. | Revisión de defectos localizables, paginación, autoridad y lectura real. | El cliente y el taller necesitan un documento íntegro además de un PDF visible. P11/P12. |
| Opciones contextuales útiles presentadas como una función IA. | Ayuda y acciones determinísticas disponibles en el producto manual completo. | El plan sin IA debe resolver el oficio por sí mismo. P09/P13/P16. |

## 6. Aplicación dentro del encargo continuo

Esta ampliación refina la jerarquía, selección, documentación y continuidad de los contratos existentes. No agrega otra vista principal, tema, suite de componentes o sistema de cálculo. No introduce una etapa de aprobación ni una campaña de pruebas por referencia.

Claude integra estas decisiones durante 01–06 y comprueba el conjunto en **07**: dos vistas, popup cerrado/abierto según tarea, propiedades por selección, valores mixtos, teclado, 1.440/1.280/1.024/390 px con el alcance real del editor, PDFs cortos/largos y documentos de operación por rol. Los errores de compilación o integración se corrigen cuando aparecen; la aceptación común sigue pendiente de evidencia nueva.

La calidad se juzga por si una persona identifica la ventana, cambia la pieza correcta, entiende precio/autoridad y completa el trabajo permitido. Ninguna fuente de diseño sustituye motor, Decimal, org_id/RLS, revisión emitida inmutable o clic humano para acciones externas y consecuentes.
