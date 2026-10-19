# Documentos profesionales y editor integrado

## Producto documental

Un documento debe convencer porque permite comprender el proyecto, sus ventanas, su alcance y su precio. Evitar la portada inflada, la repetición de condiciones y los bloques de trazabilidad que parecen más importantes que la oferta. La firma no debe hacer que toda vista previa parezca un compromiso definitivo.

El pedido más específico del dueño se traduce en **ocho diseños iniciales: tres cotizaciones, dos listas/pedidos y tres órdenes de corte**. Es una concreción de su referencia aproximada a varios diseños, no ocho cambios de color de una misma plantilla.

## Familias de plantilla

| Familia / diseño | Composición y propósito | Contenido dominante |
|---|---|---|
| Cotización · Esencial | Documento compacto, sin portada separada obligatoria | Empresa/cliente, ventanas con dibujo, especificación breve y total |
| Cotización · Proyecto | Composición visual para una obra que necesita explicación | Grupos por ambiente o conjunto; dibujos mayores y condiciones bien separadas |
| Cotización · Alternativas | Comparación de soluciones calculadas | Diferencias entre opciones, alcance y total por alternativa; elección explícita |
| Pedido · Por proveedor | Lista operativa preparada para enviar al proveedor | Identidad del material, acabado, unidad, cantidad de compra y observaciones |
| Pedido · Por obra | Preparación interna y revisión del abastecimiento | Necesidad por obra, material disponible/pendiente y agrupación clara |
| Corte · Secuencia | Trabajo junto a la tronzadora | Barra, orden de piezas, largos/ángulos, retazo y etiqueta de destino |
| Corte · Por ventana | Taller pequeño y armado | Dibujo, piezas de cada ventana, cantidad, orientación y referencias |
| Corte · Lista compacta | Lotes amplios y papel limitado | Filas densas legibles, agrupación de perfiles y vínculo a etiquetas |

La lista interna por obra no es una orden enviada a un proveedor. La UI distingue claramente preparar, emitir y enviar. Plantillas de etiquetas y producción existentes continúan siendo salidas profesionales y se adaptan al sistema común sin crear un editor separado para cada una.

## Detalle de una cotización bien resuelta

Cabecera compacta con marca, emisor, cliente, número y fecha. La primera página debe mostrar contenido de la oferta, no gastar casi toda su altura en un título. Ventanas con dibujo proporcionado, nombre/ubicación, medidas, cantidad y especificación que el cliente pueda entender.

Precios alineados, subtotal/impuestos/total jerarquizados y moneda inequívoca. Servicios y exclusiones en una sección propia, con condiciones una sola vez. No introducir valores térmicos, pesos o prestaciones que carezcan de fuente. Un dato no disponible no obliga a imprimir una fila «Sin dato» si no forma parte del alcance presentado; si es decisivo, debe resolverse o explicarse.

Mantener juntos dibujo, identificación y precio de la misma ventana. Gestionar saltos de página, cabeceras de tablas repetidas, bloques que no se parten y pies discretos. El diseño compacto no debe reducir letra hasta hacerse ilegible. La plantilla visual tampoco debe producir diez páginas para una oferta sencilla sin necesidad.

La huella, ID técnico y trazabilidad siguen en el registro y en un detalle técnico exportable; su presencia en la oferta comercial debe ser discreta y justificada. QR opcional con enlace breve, espacio suficiente y propósito claro. Evitar URL largas atravesando el margen.

## Firma y aprobación

Configurar en Empresa una política: sin aceptación, aprobación por portal o documento con bloque de firma. La cotización habitual puede verse y descargarse sin ese bloque. «Solicitar aceptación» abre una muestra del documento/portal que recibirá el cliente y el modo elegido.

No confundir firma dibujada, aceptación de propuesta y firma electrónica con efectos legales específicos. El plan no incorpora una certificación jurídica inexistente. Si el negocio necesita firma regulada, se evalúa un proveedor y se describe su alcance real.

En un documento ya emitido, activar posteriormente la aceptación no puede mutar silenciosamente el PDF sellado. Puede generar una revisión, un documento de aceptación relacionado o una operación de portal versionada que conserve el original, según el contrato documental implementado.

## Numeración comercial

Predeterminado visible: **Cotización 1** o **N.º 1** dentro de un documento cuyo título ya indica Cotización. Preferir el segundo para evitar repetición. Empresa puede cambiar prefijo, próximo número y formato permitido, por ejemplo `N.º 1000`.

La consulta `company_numbering` actual solo expone secuencias técnicas P/OC/RT/REC. No se debe duplicar ese servicio a ciegas ni afirmar que ya configura las cotizaciones. Añadir la numeración comercial en la autoridad de negocio adecuada, con aislamiento por empresa, asignación atómica y registro de cambios.

| Situación | Comportamiento |
|---|---|
| Borrador | Mostrar «Borrador»; no consumir folios por cada preview |
| Primera emisión | Asignar el próximo número de la empresa una sola vez |
| Reintento de emisión | Recuperar la misma emisión mediante idempotencia |
| Revisión de la oferta | Conservar vínculo y número comercial con revisión visible, según política definida |
| Cambiar prefijo/inicio | Afectar nuevas asignaciones; impedir colisiones; conservar emitidos |
| Anular | Conservar número e historial; no reutilizarlo como si nunca hubiera existido |
| Migrar oferta antigua | Mantener folio original; no renumerar documentos ya entregados |

Usar un ID técnico independiente y estable. No permitir que editar un rótulo en el editor cambie accidentalmente la identidad del documento.

## Dos niveles de edición

**Editar diseño de plantilla:** afecta futuros documentos de esa familia. Controles de marca, tipografía, colores, cabecera/pie, columnas, tamaño de dibujos, secciones opcionales, condiciones y paginación. Guardar versiones, duplicar y restaurar.

**Editar este borrador:** afecta solo esa oferta o lista. Cambiar textos, orden, visibilidad, tamaños y composición; añadir imágenes/notas y mover bloques dentro de reglas de página. Una acción diferenciada permite guardar esos cambios como plantilla si el usuario lo desea.

Al editar una revisión emitida, ofrecer crear nueva revisión con el documento anterior como base. La libertad editorial no implica reescribir el archivo histórico.

## Experiencia del editor

La entrada normal muestra una vista de impresión real y la plantilla actual. «Editar» habilita selección sobre la página. El panel contextual muestra únicamente las propiedades del bloque seleccionado. Las herramientas adicionales aparecen a demanda; no enseñar un procesador de texto completo a quien solo quiere descargar.

Acciones esenciales: seleccionar/mover, editar texto, insertar bloque/imagen, cambiar estilo, ocultar/restaurar sección, deshacer/rehacer, vista de páginas y guardar. Añadir alineación, guías, duplicación y control de salto de página sin exigir maquetación profesional. Soportar texto largo y crecimiento de tablas; el contenido no puede salir por debajo de la página sin aviso.

La IA opera en el mismo editor: «Quita la portada», «Haz el dibujo mayor», «Resume las condiciones sin quitar obligaciones», «Usa el diseño compacto», «Muestra esta oferta sin firma». Debe producir un cambio de estructura/estilo revisable y poder deshacerlo. No devolver instrucciones para que el usuario lo haga fuera.

## Arquitectura recomendada

Crear un original documental estructurado y versionado, con bloques, estilos permitidos, reglas de página y enlaces a datos. Cada documento guarda la versión de plantilla, las modificaciones locales, el snapshot de datos y activos, y la versión del renderizador.

| Capa | Responsabilidad |
|---|---|
| Datos sellados | Ventanas, medidas, cantidades, precios y condiciones de la revisión |
| Enlaces | Relacionar campos del documento con datos/expresiones autorizadas |
| Estructura | Bloques, tablas, agrupaciones y secciones |
| Presentación | Fuentes, escala, color, espacio y activos |
| Operaciones de edición | Cambios tipados, reversibles y sujetos a permisos |
| Render | Vista previa/exportación con el mismo contrato de impresión |

No permitir JavaScript, acceso al servidor ni HTML arbitrario del modelo como mecanismo de plantilla. Sanear contenido y limitar recursos. El editor modifica el original; el PDF exportado es una salida. No intentar reconstruir el original de cada PDF propio mediante OCR.

**Cifras:** se pueden cambiar sus valores mediante operaciones de precio o diseño autorizadas que vuelvan a calcular y actualizar el documento. El editor puede cambiar formato, etiqueta o visibilidad, pero no inventar un total ajeno al motor. Si una acción de ocultar vuelve engañosa la oferta, mostrar el efecto y mantener coherencia del alcance.

## PDF externos

El dueño pide trabajar dentro de DEKOPEN. La edición completa de un PDF externo es un problema distinto de editar el original de una cotización propia: texto puede estar fragmentado, convertido en curvas o dentro de una imagen.

PDF.js es una base de visualización; anotaciones o un rectángulo blanco encima del texto no equivalen a editar contenido. Apryse y Nutrient son candidatos a evaluar para edición de contenido existente. No se ha elegido licencia ni validado integración. Preparar una decisión concreta con documentos de muestra, edición real, fuentes, privacidad, exportación y costo de licencia, sin rehacer el resto del editor alrededor de un SDK antes de esa evaluación.

Para PDF escaneados, distinguir OCR/redacción de texto de edición exacta de un original. Conservar original y copia editada, explicar limitaciones reales de forma contextual y nunca alterar una revisión sellada. La v1 debe completar primero la edición integral de sus propios documentos; un editor externo completo se considera entregado solo con evidencia de edición y exportación, no con anotaciones rebautizadas.

## Aceptación final

Revisar las ocho plantillas con el mismo caso sencillo y otro extenso; marca clara y oscura, nombres largos, condiciones amplias, varias monedas admitidas, imágenes, firma activada/desactivada y cambio de revisión. Comparar manual/IA en una misma edición. Comprobar que preview y archivo exportado conservan composición, cifras, activos y número. Mantener una muestra real de cada familia como evidencia del cierre.
