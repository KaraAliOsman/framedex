# Prompt 04 — Documentos y operación listos para trabajar

Este es un tramo del encargo continuo definido en el [prompt maestro](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/prompt-maestro.md). Encontrar este archivo no autoriza ejecutarlo durante la investigación de Codex. Claude lo implementará junto con el resto del paquete, sin pedir aceptación de cada etapa.

## Objetivo y contrato

Implementa la experiencia documental y operativa completa sobre el modelo existente: cotización profesional, plano técnico, materiales/abastecimiento, plan de corte, etiquetas, estación de taller y terreno. **Debe funcionar de forma manual con IA desactivada.** El popup opcional puede preparar trabajo mediante las mismas operaciones autorizadas; no se necesita chat para usar ningún flujo manual.

La obra y la ventana son el objeto central; cada salida conserva posición, unidad, pieza, revisión y autoridad. No conviertas los documentos en capturas de pantalla del editor, ni un tablero bonito en sustituto de producción real. No aceptes el diseño anterior/DEMO como resultado visual final. Las fixtures siguen sirviendo para estrés y regresión, claramente aisladas y rotuladas; el recorrido normal usa catálogo real con capacidades honestas.

Lee primero el [contrato visual](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/02-diseno-y-referencias.md), especialmente §§7–11 y 14; las [referencias profesionales](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/05-referencias-profesionales.md), especialmente P10–P12 y §3.5; el [contrato manual y dos vistas](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/01-producto-y-dos-vistas.md), la constitución reconciliada en 01 y el [contrato de copiloto](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/03-copiloto-y-planes.md). Mesa y Estudio muestran el mismo estado documental; no implementes dos editores, dos numeraciones ni dos proyecciones de precio.

Conserva motor como única fuente de números calculados, Decimal, org_id/RLS, snapshots emitidos inmutables, movimientos auditados e idempotencia. Emitir, enviar, publicar catálogo, comprometer compra/pago o liberar trabajo de fabricación conserva el clic humano explícito y el gate del servidor. Omitir todo del copiloto no omite estas reglas.

**Ritmo de trabajo:** desarrolla e integra este tramo sin montar una batería de pruebas o campaña de capturas propia de la etapa. Corrige errores de compilación/integración cuando aparezcan. La batería formal, recorridos de roles, proveedor real, render de PDF y pase editorial se ejecutan una vez en 07, al final del paquete completo. No declares esta etapa aceptada por haber creado componentes.

## 1. Reutiliza la autoridad que ya existe

Inspecciona el estado y los cambios locales antes de editar. No sobrescribas el trabajo de Claude previo ni regeneres históricos para aplicar un diseño nuevo.

Puntos de entrada reales:

- [QuotationDocument.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/projects/QuotationDocument.tsx), [QuotationReview.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/projects/QuotationReview.tsx), [ProjectQuotationPanel.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/projects/ProjectQuotationPanel.tsx) y [ProjectMaterials.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/projects/ProjectMaterials.tsx).
- [quotation.py](C:/Users/alios/Downloads/framedex/backend/documents/quotation.py), [preferences.py](C:/Users/alios/Downloads/framedex/backend/documents/preferences.py), [numbering.py](C:/Users/alios/Downloads/framedex/backend/documents/numbering.py), [issuance.py](C:/Users/alios/Downloads/framedex/backend/documents/issuance.py), [artifacts.py](C:/Users/alios/Downloads/framedex/backend/documents/artifacts.py), [drawing.py](C:/Users/alios/Downloads/framedex/backend/documents/drawing.py), [workshop_layouts.py](C:/Users/alios/Downloads/framedex/backend/documents/workshop_layouts.py).
- [ProductionPage.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/production/ProductionPage.tsx), [CutPlanView.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/production/CutPlanView.tsx), [OperatorStation.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/production/OperatorStation.tsx), [PieceScanner.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/production/PieceScanner.tsx) y [TraceView.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/production/TraceView.tsx).
- [production service](C:/Users/alios/Downloads/framedex/backend/production/service.py), [production views](C:/Users/alios/Downloads/framedex/backend/production/views.py), [cut_documents.py](C:/Users/alios/Downloads/framedex/backend/production/cut_documents.py), [cut_labels.py](C:/Users/alios/Downloads/framedex/backend/production/cut_labels.py), [cut_manifest.py](C:/Users/alios/Downloads/framedex/backend/production/cut_manifest.py), [field.py](C:/Users/alios/Downloads/framedex/backend/production/field.py).
- [conocimiento documental](C:/Users/alios/Downloads/framedex/docs/wiki/product/quotation-document.md), [corte](C:/Users/alios/Downloads/framedex/docs/wiki/product/cut-documents.md), [estaciones](C:/Users/alios/Downloads/framedex/docs/wiki/product/production-stations.md), [terreno](C:/Users/alios/Downloads/framedex/docs/wiki/product/field-work.md).

La lectura del código actual prevalece sobre afirmaciones históricas de aceptación. Ya hay preview borrador, tres plantillas comerciales, bloques editables, numeración y variantes de taller; completa y corrige sus recorridos en lugar de crear una versión paralela. Los cambios de API nacen en backend/serializadores; regenera OpenAPI y orval, nunca edites el cliente generado a mano.

## 2. Una entrada documental comprensible desde la obra

Dentro de Cotización organiza el trabajo en Documento y Revisión/Emisión, con precio y requisitos visibles. El documento ocupa la superficie principal; la configuración es contextual.

Cabecera: número/estado cuando existe, nombre de obra, revisión técnica/comercial y emisor. Acción principal del borrador: Guardar diseño. Acción de emisión solo en el paso de revisión/emisión, con resumen de qué se congela y los requisitos pendientes. Descargar borrador no se parece ni equivale a Emitir.

El preview usa el renderer canónico y el modelo real del proyecto, no datos locales aproximados. Una edición de composición puede actualizar con el debounce existente; conserva la última página mientras prepara la siguiente y muestra “Actualizando vista previa”. Si falla, dice que la preview es anterior e indica la causa. Nunca presenta un PDF viejo como si ya tuviera los cambios.

Controles: elegir composición mediante miniaturas legibles, ordenar/ocultar bloques permitidos, editar introducción/alcance/notas/condiciones que tengan fuente, mostrar/ocultar unitarios y elegir aceptación opcional. Posiciones y resumen comercial no se pueden ocultar. Hay Deshacer/Rehacer de composición, restaurar valores de empresa y guardar sobre obra. Una modificación del original de empresa no cambia retroactivamente emitidos ni borradores de obra con override explícito.

Muestra claramente el alcance de cada ajuste: “Solo esta obra” o “Predeterminado de la empresa”. No guardes silenciosamente un ajuste local en todas las futuras cotizaciones. El cambio de plantilla no descarta contenido compatible ni precio; si elimina un bloque de composición, se conserva su texto para recuperarlo cuando vuelva a estar disponible.

Numeración humana por empresa, con prefijo e inicio editables donde el rol lo permite. El borrador no consume número. Respeta la asignación transaccional e idempotente existente al preparar una emisión; un retry o render fallido no debe producir números repetidos, una segunda emisión o un cambio de número ya asignado. La revisión se presenta separada del número comercial.

## 3. Tres composiciones comerciales completas

Implementa tres composiciones realmente diferentes sobre el mismo snapshot, con Carta como papel inicial configurable y sin hacer caber todo mediante tipografía diminuta. Base editorial: márgenes 14 mm, texto principal 10–10,5 pt, datos secundarios no menores de 9,5 pt, Sans para comunicación/precio y Mono para dimensión/código. Ajusta saltos y distribución, no el tamaño hasta volverlo ilegible.

### Esencial

Documento directo para una oferta habitual:

1. Encabezado de marca del emisor a izquierda; “Cotización N.º …”, revisión y fecha a derecha.
2. Cliente/obra y contacto agrupados, sin confundir nombre libre con ficha vinculada.
3. Fichas de posiciones: código/ambiente, elevación de proporción fiel, vista declarada, medidas, cantidad, fabricante/serie, apertura, vidrio y acabado; precio unitario si está habilitado y total de línea.
4. Servicios/accesorios relevantes como sublíneas claramente asociadas, derivados del modelo o declarados con su autoridad.
5. Resumen neto, descuentos/ajustes explicables, impuesto y total; condiciones y vigencia cerca del cierre.
6. Aceptación/firma solo si está configurada o se solicita de forma explícita.

Evita párrafos técnicos largos por ventana cuando la misma serie/condición puede aparecer una vez con referencia inequívoca. No omitas diferencias reales entre posiciones para hacerla más corta.

### Proyecto

Documento para presentar una obra con varias soluciones:

1. Apertura editorial con nombre de obra, emisor, destinatario, alcance y dibujo/propuesta técnica pertinente; no foto genérica de un edificio ajeno.
2. Resumen de solución y condiciones que el cliente necesita entender.
3. Posiciones con elevaciones de mayor tamaño y agrupación por ambiente/piso cuando los datos existen.
4. Resumen comercial y calendario/condiciones configurados.
5. Anexos técnicos solo cuando aportan decisión: composición de vidrio, prestaciones con autoridad y alcance de montaje. No inventes certificaciones.

No añadas una portada vacía a Esencial para llamarla Proyecto. La distribución del espacio y la lectura deben cambiar de verdad. No insertes texto de marketing sobre lo “fácil” que es usar el software.

### Alternativas

Comparación de revisiones/opciones válidas:

1. Identifica la opción vigente y cada alternativa, su revisión, descripción y condición.
2. Alinea posiciones comparables y muestra diferencias reales de sistema, vidrio, acabado, prestación y precio.
3. Cada total conserva su moneda/base, vigencia y autoridad sellada. No sumar alternativas al total vigente.
4. Selección del cliente solo mediante el flujo de portal/aceptación existente; visualizar una alternativa no reescribe la obra.
5. Si no hay una alternativa válida, explica el estado y ofrece crear una revisión/comparación manual con permisos; no genera filas ficticias.

Conserva límite y reglas actuales de alternativas del mismo proyecto/tenant; no mezcles cotizaciones de otras obras. Evita alternativas recursivas.

### Reglas comunes

La marca principal es la empresa emisora. El pie “Generado con DEKOPEN” respeta configuración white-label; no domina la propuesta. Número, fecha, revisión y página son legibles. La huella de ingeniería completa permanece en registro y documentación técnica, sin invadir el cuerpo comercial.

No imprimas placeholders, campos vacíos, “completar garantía” ni plazos/anticipo calculados por lenguaje libre. Usa valores de empresa/obra con autoridad y pide resolver los obligatorios antes de emitir. Un dato opcional ausente se omite de forma coherente; un precio ausente no se imprime como $0. El catálogo sintético conserva marca DEMO en su circuito de laboratorio y nunca se rebautiza como fabricante real.

Aceptación/firma es opcional y no se introduce por defecto en todos los documentos. Cuando se activa, su alcance coincide con la revisión emitida. QR/enlace comercial es opcional y apunta a esa revisión/capacidad del portal; su revocación/expiración no borra ni altera el PDF histórico.

Centraliza estilos por función —título, sección, posición, especificación, importe, dimensión, condición y pie— para que las tres composiciones sean consistentes sin editar formato bloque a bloque. No añadas un procesador de textos libre. Los ajustes respetan el ámbito obra/empresa y la autoridad de los snapshots; cambiar un estilo o plantilla no regenera documentos históricos emitidos.

La revisión documental localiza cada problema detectado por página o posición y enlaza a su resolución. Distingue faltante de contenido, defecto de composición y bloqueo de emisión ya existente. Solo informa de lo que realmente se comprueba: no anuncia fuentes ausentes, baja resolución o desbordamiento si no tiene un detector válido. No inventa nuevos requisitos comerciales por seguir una referencia editorial.

Diseña el orden lógico del texto junto al layout: título, posiciones con sus importes y condiciones deben conservar sentido al seleccionar o extraer contenido. El PDF mantiene texto seleccionable, sin rasterizar toda la página. En 07 comprueba el archivo real, además de su apariencia y paginación. No anuncies PDF/UA, etiquetado accesible ni conformidad automática si el renderer no lo implementa y la comprobación no lo acredita.

## 4. Plano técnico: un documento de fabricación, no una screenshot

El plano representa la misma posición/ensamble de la revisión sellada. Lleva elevación dominante, vista interior/exterior declarada, dimensiones total/parciales relevantes, mano/sentido de apertura y códigos humanos. Agrega planta de carriles/acople y secciones cuando existan datos y resuelvan un montaje. Las vistas no se contradicen ni invierten color/cara.

Tabla técnica: sistema/serie, perfiles y funciones, vidrio/relleno, herrajes, medidas/fabricación y observaciones con fuente. No renderices un perfil concreto si solo existe una sección genérica; declara el límite y conserva el gate de fabricación.

Cajetín en todas las páginas técnicas: obra, posición/unidad, documento, número, revisión, fecha, página y huella de la autoridad congelada. El documento se puede relacionar con la OT real; no copia el precio comercial o datos privados de cliente al plano de operario si su proyección los excluye.

La geometría deja espacio a cotas y etiquetas; los símbolos permanecen legibles. Al exceder el papel se usan páginas/vistas adicionales o un formato configurado realmente soportado, sin cortar dibujos, superponer texto o reducir todo al 30 %. Carta/A4 de base y formato técnico adicional solo como salida completamente implementada en renderer y selector; ningún botón anuncia un formato que luego no renderiza.

La exportación de plano genérico PDF/DXF no certifica un posprocesador CNC. Los formatos genéricos y las salidas específicas de máquina conservan nombres, validaciones y permisos distintos. No añadas “listo para CNC” por existencia de un archivo descargable.

## 5. Materiales, preparación y compra con identidad

Materiales muestra requerimientos de la misma revisión: perfiles/refuerzos/junquillos, vidrio/paneles, herrajes/kits, accesorios y servicios separados. Cada partida indica unidad y procedencia; números desconocidos dicen Sin dato con causa. Las sumas proceden de la proyección del motor/servicio autorizado.

Distingue tres superficies:

- **Necesidad por obra:** qué hace falta, qué está reservado/disponible y qué falta abastecer.
- **Preparación de pedidos:** agrupación por proveedor y compatibilidad con las existencias reales; borrador para revisión.
- **Pedido a proveedor:** documento con emisor, destinatario, códigos, cantidad/unidad, condiciones y entrega, emitido/enviado con acción humana.

No cambies el título de una tabla interna para simular una orden de compra real. En código ya hay “Pedido por obra · preparación interna”; conserva esa advertencia hasta que se emite una OC mediante su servicio real.

Dos composiciones de pedido:

1. **Proveedor:** encabezado de OC, datos de proveedor/entrega, tabla de código comercial exacto, descripción/material/acabado, cantidad/unidad y precio si autorizado; totales/condiciones y revisión.
2. **Preparación por obra:** agrupación por material y destino/posición/OT, stock/retazo reservado y faltante. Es interna y no compromete al proveedor.

Las recepciones parciales y diferencias de confirmación tienen estado y acción propios. No aumentes stock por imprimir una OC ni marques comprado por preparar un borrador.

## 6. Corte: tres lecturas del mismo plan

La entrada Corte identifica obra, OT/posición, revisión, fecha de optimización y estado vigente/obsoleto. No puede parecer terminada si falta plan o hay piezas sin ubicar.

Para OWNER/WORKSHOP_MANAGER autorizados, la acción principal es Optimizar corte o Reoptimizar con explicación de qué invalidó el plan y qué reserva/cambio puede ocurrir. ESTIMATOR tiene lectura y una tarjeta de requisito: “Falta un plan de corte vigente. Lo prepara el dueño o jefe de taller”, abrir Resumen/orden y Actualizar. No le dejes una ilustración vacía que ordena hacer una acción que su rol no puede ejecutar.

Conserva un mismo plan para tres composiciones:

### Secuencia

Cada barra/lámina muestra código, suministro original, material/acabado, largo/formato, piezas numeradas en orden, medida y dirección/ángulos cuando corresponden. Para barras, el gráfico es proporcional, conserva la pérdida de corte y distingue pieza, proceso y sobrante. Para láminas, ejes/orientación/rotación están definidos; no reordenes la secuencia arbitrariamente por estética.

Al seleccionar una pieza se ilumina en diagrama y lista, y el detalle muestra código, ubicación/unidad, función, SKU, medida, ángulos, origen y destino siguiente. No hagas depender la identificación del color.

### Cortes idénticos

Agrupa solo cortes físicamente equivalentes bajo la misma autoridad, material, acabado, función/compatibilidad, largo y par de ángulos. Conserva la lista de identidades y posiciones que los componen. La cantidad agrupada no reemplaza el rastreo de cada pieza.

La composición resuelve preparación de sierra manual; no afirma ser la secuencia de cada barra ni modifica el plan sellado al ordenar una tabla.

### Por ventana

Reúne las piezas de cada posición/unidad para montaje. Encabezado con código/ambiente/dibujo pequeño, piezas con función, medida, ángulos, material, barra de origen y destino. Respeta acoples y múltiples hojas sin rebautizar las piezas.

### Retazos y estado físico

Un sobrante previsto tiene código/destino desde el plan, longitud/formato útil y estado “Previsto · alta al completar corte” si esa es la autoridad actual. Solo la confirmación física de corte por su servicio da de alta stock de retazo. Imprimir no crea existencias ni asigna otra identidad. Retry con la misma clave no duplica entradas/consumos.

Un retazo consumido conserva origen y reserva. Si el plan histórico carece de dirección física prevista, explica que requiere reoptimización humana; no inventes un rack, un código o medidas de lámina. Si no hay fuente/stock utilizable, declara el faltante de forma accionable.

La vista por obra puede reunir varias OT existentes para lectura/impresión, pero no crea una OT artificial ni altera la regla de una OT por posición sellada. Agregar no elimina unidad, pieza, origen o huella.

PDF, CSV, DXF, etiqueta y pantalla comparten códigos, medidas, ángulos y orden según el contrato vigente. Un cambio de composición no recalcula ingeniería. La fuente genérica sigue siendo genérica hasta validación específica de máquina.

## 7. Taller: estado real, siguiente acción y densidad propia

Conserva rutas y deep links actuales, incluidos section y piece; adapta la presentación sin romper enlaces impresos/históricos.

### Jefe de taller

Tablero con prioridad por compromiso, próxima estación y bloqueos reales. Filtros por obra, fecha, estación y requiere persona; el filtro deja visible su alcance y se limpia. No renderices cientos de tarjetas repetitivas como bienvenida; la lista/cola debe permitir encontrar trabajo y excepciones sin ocupar la pantalla con columnas vacías.

Cabecera de OT compacta: código, posición/unidad, revisión, compromiso y estado. Una acción principal según tarea. El stepper de ruta es distinto de la selección de sección. En anchos menores muestra estación actual y “1 de 6” con acceso a ruta completa, sin nueve pestañas apretadas.

Organiza el detalle en Resumen, Trabajo y Trazabilidad; dentro de Trabajo muestra la herramienta de la estación/selección y un selector claro para Piezas, Corte, Mecanizado, Vidrios, Herrajes, Calidad y Embalaje. Conserva todo acceso funcional anterior mediante enlaces/query compatibles. No dupliques datos entre nuevas pestañas y antiguas escondidas.

Estado de paso deriva del backend y requisitos actuales, no de la pestaña elegida. Presentaciones diferenciadas: Pendiente, Preparada para iniciar, En curso, Bloqueada con causa y Terminada. Si falta plan, “Sin plan vigente” prevalece como requisito; no uses “Listo” para significar seleccionado. Nunca cambies enums o una transición física para hacer cuadrar el copy.

Bloquear requiere motivo; desbloquear y control de calidad conservan permisos. Un rechazo/remake crea su OT idempotente y mantiene procedencia; no sustituye la BOM entera por una pieza ni altera la revisión original.

### Operario

La ruta de OPERATOR sigue usando su estación persistida y la cola que el servidor autoriza. Una pieza dominante: código ≥32 px, medida ≥28 px, instrucción, dibujo/ángulo si útil, destino y siguiente paso. Texto 16 px y controles ≥48 px, preferiblemente 56 px para Iniciar/Completar/Bloquear. El uso táctil no requiere hover ni gestos ocultos.

Escanear o ingresar código resuelve pieza/OT/estación. Conserva el puesto del operario y explica si la pieza no pertenece a su cola. No cambia la estación sin elección humana. Si hay coincidencias ambiguas, permite elegir entre resultados autorizados; no adivina.

Iniciar/Completar se habilita por requisitos reales: plan vigente, material y evidencia de operaciones cuando corresponda. Si no se puede iniciar, muestra qué falta y quién lo resuelve; Actualizar estación conserva pieza/selección cuando siguen vigentes. Las confirmaciones muestran resultado persistido y siguiente trabajo, no solo un toast efímero.

No mostrar coste, margen, dirección de cliente o información comercial que la proyección del backend excluye. No ampliar el endpoint para “completar la tarjeta”.

## 8. Etiquetas y QR por propósito y rol

Hay tres propósitos distintos; no uses el mismo QR para todos:

| Propósito | Datos al abrir | Autorización/comportamiento |
|---|---|---|
| Portal comercial de revisión | Propuesta/revisión y acciones del cliente configuradas | Capacidad/enlace del portal con vigencia/revocación; sin API de taller ni datos internos. |
| Etiqueta de pieza/unidad de taller | Identidad, medida, material, revisión, estación/tarea y trazabilidad permitida | Sesión/rol real y RLS; la etiqueta no concede autoridad para producir. |
| Identidad de stock/retazo | Material, medida útil, origen, ubicación, estado/reserva y movimientos permitidos | Rol de inventario/taller autorizado; no convertir lectura en ajuste de stock. |

Conserva el formato de identidad/deep link vigente y sus códigos históricos. No lo sustituyas por URLs construidas a mano desde un UUID corto ni por un token que expone datos de otro tenant. El código humano impreso acompaña al QR y permite lector USB/entrada manual. Una cámara no es requisito universal; solicita permiso solo al iniciar escaneo por decisión humana.

Etiqueta: código grande, pieza/unidad/posición, material/acabado, medida/ángulos necesarios, revisión/huella abreviada y próximo destino. Formatos existentes Carta/A4/rollo 100 × 50 mm conservan su autoridad; una página de rollo es una etiqueta. No cortar quiet zone del QR ni poner texto/ornamento sobre él. La legibilidad se verifica en el cierre común con render/escaneo donde haya dispositivo.

Matriz de experiencia sin ampliar permisos:

- OWNER: configura documentos y opera dentro de sus gates; puede revisar estados/causas.
- ESTIMATOR: crea/revisa/emite propuesta según autoridad documental, consulta fabricación permitida y entiende cómo solicitar resolución al jefe. No optimiza ni completa taller por un rediseño.
- WORKSHOP_MANAGER: prepara/libera/optimiza y gestiona bloqueos/taller donde ya lo autoriza el servidor; no recibe autorización comercial adicional por ver un PDF.
- OPERATOR: estación y piezas de su cola, transición/evidencia autorizada; sin datos comerciales privados.
- INSTALLER: visitas/entregas/instalaciones asignadas y evidencia de campo; no completa estaciones industriales por escanear una etiqueta.
- Cliente externo: solo la proyección sellada de su enlace y sus acciones habilitadas, sin acceso a organización/proyecto interno.

Backend es autoridad. La UI adapta texto/acciones al permiso efectivo; ocultar botones no reemplaza guards, RLS o validación de organización.

## 9. Terreno y cierre de la unidad

La ficha de campo abre obra/visita asignada, unidad, ubicación, fecha/compromiso y qué falta registrar. Foto, nota, medición, incidencia, entrega/firma y cierre siguen los contratos actuales. Evita pedir otra vez datos ya presentes en la obra.

Las medidas de vano y fabricación son conceptos distintos; un registro de terreno no modifica una revisión emitida. Una rectificación o remake conserva origen, motivo y nueva autoridad. No actualizar dimensiones selladas silenciosamente desde un formulario móvil o IA.

El estado de envío/sincronización debe ser real. Si la app no implementa cola offline robusta, no muestres “Guardado” durante una desconexión; conserva borrador local de forma explícita cuando exista, explica pendiente y ofrece reintentar sin duplicar. Un recibo o firma no aparece hasta confirmar su registro.

## 10. Estados, recuperación y detalle visual obligatorio

En documento, plano, corte, cola, escaneo y terreno implementa vacío inicial, vacío filtrado, carga, error, sin permiso, bloqueado, obsoleto y solo lectura donde apliquen. Cada uno explica objeto, causa y próxima acción permitida.

No uses el aviso genérico “revisa la conexión” para falta de catálogo, stock o rol. No marques todo verde por tener datos; color, texto e icono expresan la misma semántica. No uses naranja como botón principal universal.

La selección es contorno+tinte localizado, distinta del estado terminado. Foco visible 2 px y orden de Tab lógico. Los botones se reconocen sin hover. Una acción principal por región; menú Más para variantes no prioritarias. La preview y el documento no compiten con una columna IA.

En 1.440/1.280 px, documento/plano domina y el inspector tiene 320 px; a 1.024 px se puede cerrar el inspector y trabajar con preview útil. A 390 px, preview/documentos se consultan a ancho completo y los controles aparecen en panel de ancho disponible; taller/terreno mantienen objetivos táctiles y contenido sin recortes. La lectura técnica del CAD conserva su política actual y causa visible; no se convierte toda la aplicación en solo lectura.

Texto largo, muchas posiciones y códigos extensos deben provocar salto/reflujo coherente. No ocultar un dato decisivo bajo puntos suspensivos sin acceso. En PDF, encabezados de tablas se repiten y no quedan títulos huérfanos; fichas/diagramas no se cortan sin continuación declarada.

## 11. Referencias útiles y decisiones que no debes copiar literalmente

Usa el detalle de fuentes y límites del contrato visual. Referencias principales:

- Logikal: orientación declarada y modelo dominante; manual público, no prueba privada.
- V6 Drawing: elevación, secciones, herrajes y cajetín como vistas complementarias; no copiar medidas/unidades del ejemplo.
- Klaes: dibujo por posición junto a especificación/precio; captura histórica, no copiar ribbon.
- Winart: separación de familias de material en Plan de Ejecución; fotograma observado, no autoridad de cálculo.
- Matrix/FeneVision: datos mantenidos por proveedor/empresa y permisos/compensaciones explícitos.
- 3E: información por componente y evidencia de campo; NFC no es QR.
- Windowmaker: cambios globales/revisión/precio congelado y continuidad de operación; la demo de asistente no acredita autonomía.

No copiar activos protegidos al producto, fórmulas de otro software, cifras de ejemplo ni promesas de compatibilidad de maquinaria. Una imagen publicada sirve para estudiar composición y razón.

## 12. Qué dejas listo para el cierre común

Integra todos los caminos; elimina componentes/CSS sustituidos sin borrar capacidades, historia o enlaces impresos. Registra brevemente las decisiones relevantes en el ledger del encargo con tabla Before | After | Why y límites externos concretos.

Deja los casos significativos preparados para 07: una propuesta de pocas y muchas posiciones/nombres largos, tres composiciones, alternativa sellada, borrador sin número, retry de emisión, cambios de preferencias sin alterar históricos, rol sin permiso de optimización, plan obsoleto, piezas no ubicadas, corte/retazo previsto frente a físico, reimpresión sin movimiento, QR de cliente frente a QR de taller, lectura de estación sin datos comerciales y una incidencia/rectificación de terreno.

Son condiciones para comprobar **en la batería final del paquete**, no una aceptación por esta etapa. La evidencia antigua de fixture no sirve como aprobación de apariencia ni como catálogo fabricable. Un bloqueo externo real se registra con dato exacto, responsable y acción pendiente, mientras completas todo lo independiente. No lo ocultes con un demo ni marques toda la versión terminada si queda un flujo anunciado sin implementación.

