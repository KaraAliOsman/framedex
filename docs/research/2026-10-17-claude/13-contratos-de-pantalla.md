# Contratos de pantalla y detalles de uso

Estas especificaciones completan los principios de los documentos 03–09. Definen qué debe lograr cada superficie y cómo se presenta su estado. Son propuestas de implementación, no capturas de una interfaz ya hecha.

## Regla común

Toda pantalla debe responder: dónde estoy, sobre qué trabajo, qué puedo hacer ahora, qué pasó con mi última acción y qué falta realmente. Si un texto no ayuda a responder nada de esto, valorar su retirada. Estado de guardado, carga, error y permisos deben distinguirse sin una explicación larga.

| Situación | Presentación común |
|---|---|
| Carga inicial | Mantener estructura estable y nombre del trabajo; estado local |
| Actualización de una parte | Conservar contenido útil y señalar la región que se actualiza |
| Sin contenido | Causa breve y una acción pertinente |
| Filtro sin resultados | Mantener filtro; ofrecer limpiarlo |
| Falta de permiso | Explicar la capacidad necesaria y alternativa útil; no error genérico |
| Guardando | No afirmar éxito; conservar entradas |
| Error al guardar | Indicar qué no se guardó y permitir reintento sin perder edición |
| Versión anterior | Mostrar conflicto y objeto afectado; no sobrescribir silenciosamente |
| Trabajo terminado | Resultado visible y siguiente acción opcional; sin celebración que interrumpa |

## Proyectos / inicio del trabajo

**Pregunta:** «¿Con qué obra continúo o cómo empiezo otra?» Cabecera con búsqueda y «Nueva cotización». Recientes con nombre, cliente, dibujo/resumen, fecha y estado comprensible. Una sección pequeña recoge decisiones que requieren al usuario, agrupadas por obra; no lista cada evento técnico.

La tarjeta/fila abre el proyecto; menú separado para acciones secundarias. No meter varios enlaces que navegan a destinos distintos dentro de una tarjeta completamente clicable sin delimitación. Mostrar precio solo si tiene sentido para el rol y existe cálculo.

El vacío ofrece crear la primera cotización e importar catálogo si lo necesita. La primera vista no debe obligar a crear una organización de mentira para probar. Los datos demo se identifican como tales en contexto.

**IA:** «Prepara una cotización» inicia un encargo; el contexto no debe fijarse a una obra distinta por haber sido la última consultada.

## Proyecto

**Pregunta:** «¿Qué ventanas tiene esta obra y qué entrego?» Cabecera: nombre, cliente, estado y acción según fase. Vistas Ventanas / Cotización / Materiales / Actividad. Sin una segunda barra permanente de pasos que repita las mismas áreas.

La colección enseña dibujo, identificación humana, medidas, cantidad, material/acabado y resultado comercial. Para muchas ventanas, tabla alternable con columnas elegidas. Selección múltiple visible, contador y barra de acciones solo al seleccionar.

Editar nombre/cliente en contexto, sin una ficha administrativa gigante antes de los dibujos. Cambios de cantidades mantienen sentido: tres unidades de una corredera de dos hojas no son seis ventanas. Al duplicar, conservar propiedades y permitir cambiar medida/nombre inmediatamente.

**IA:** alcance proyecto/selección visible. «Todas» afecta el conjunto que la persona entiende por la obra, respetando exclusiones explícitas y revisión/estado.

## Editor

**Pregunta:** «¿Cómo queda esta ventana y cómo cambio esta parte?» Lienzo central; ancho/alto sobre sus cotas y controles equivalentes accesibles; cantidad y tipología fáciles de localizar. Selección clara de marco, división, hoja o vidrio con propiedades aplicables.

Al entrar a editar una medida, seleccionar su valor y mostrar unidad sin duplicarla en la entrada. Enter aplica, Escape cancela la edición local. Interpretar coma/punto y unidad según el contrato vigente; preguntar cuando la entrada de lenguaje natural es ambigua, sin corregir silenciosamente una escala improbable.

No desplazar el dibujo al aparecer una advertencia. Acabado con muestra grande; vidrio con nombre comprensible y composición a demanda. Vista interior/exterior explícita. Deshacer/rehacer y estado guardado localizables. Una selección no debe desaparecer por abrir el asistente.

**IA:** «Esta ventana» y «Esta parte» tienen identidad comprobable. La muestra conserva la selección y las cotas relevantes.

## Cotización y precios

**Pregunta:** «¿Qué voy a ofrecer y por cuánto?» Documento o resumen comercial principal; precio, condiciones heredadas y acción de entrega. Costo y margen accesibles al rol autorizado sin competir con el contenido del cliente.

Si falta un costo, indicar material, unidad y origen esperado. Si necesita autorización comercial, mostrar solicitud y decisión concreta; no trasladar el formulario entero de políticas a la oferta. Cambios de descuento exponen efecto calculado y quién puede aplicarlo.

Guardar borrador, emitir y enviar son acciones diferentes. El mismo botón no debe cambiar de significado sin etiqueta. Mostrar «Borrador» hasta emisión y número comercial después. Comparaciones mantienen referencia a sus alternativas; no presentar un precio aislado sin qué compra.

**IA:** prepara oferta completa y deja decisión final concreta. No cambia margen fuera del permiso del usuario para lograr un precio deseado.

## Documento / editor

**Pregunta:** «¿Qué verá el cliente y cómo lo ajusto?» Página real desde el inicio, selector de plantilla con miniaturas legibles y «Editar». Los controles de composición aparecen al seleccionar un bloque. El panel de IA comparte ese contexto.

Mostrar si se cambia «Este documento» o «Diseño para futuros documentos». Deshacer y restaurar sección. Una sección oculta no se elimina definitivamente del cálculo. Explicar el vínculo de un total a los datos mediante su acción de negocio, sin exponer nombres internos del binding.

Firma desactivada no deja líneas vacías ni un hueco reservado. QR desactivado tampoco deja un bloque ornamental. Una revisión emitida abre como documento histórico con acción «Crear revisión», conservando acceso al original.

## Asistente

**Pregunta:** «¿Qué le encargo y qué está haciendo?» Compositor accesible, contexto corto y actividad de trabajos. Historial compartido al pasar de editor a documento. No pedir el nombre de un flujo de agente.

Entrada enviada muestra recepción; etapa real muestra actividad y «Detener». Si falta una decisión, una pregunta con opciones y respuesta libre. Si hay un resultado, abrirlo donde se pueda revisar: dibujo, comparación o páginas.

No hacer scroll automático si el usuario está leyendo mensajes anteriores. No llenar el panel de llamadas a herramientas; agrupar actividad técnica detrás de un detalle. La salida principal explica qué cambió, qué está guardado y qué falta, con acceso al objeto. Los errores no se ocultan dentro de una burbuja exitosa.

## Catálogos

**Pregunta:** «¿Qué sistemas tengo listos y cómo cargo otro?» Biblioteca por sistema/serie con estado de uso resumido, búsqueda y «Subir catálogo». La ficha muestra perfiles/familias reconocibles, fuentes y versiones a demanda.

Durante importación conservar archivo y progreso real. Al terminar, enseñar entidades y capacidades utilizables. Las dudas se agrupan; al abrir una, fuente a un lado e interpretación al otro. Permitir continuar con lo ya preparado sin esconder limitaciones de fabricación.

Añadir otro PDF a una línea inicia comparación, no un duplicado automático. El rol que no puede publicar ve preparar/solicitar revisión, sin un botón que promete una acción denegada.

## Perfil y acabado

**Pregunta:** «¿Es esta la pieza o material que necesito?» Nombre, código original, familia, imagen o sección y datos pertinentes. Una pestaña técnica puede mostrar detalles declarados; no repetir todos los campos de todos los tipos.

La representación se identifica como ilustrativa si no es exacta. Foto aportada y sección técnica tienen roles diferentes. Al elegir acabado se muestra la textura sobre un producto, no solo una bolita de color. Cambios visuales de imagen no deben alterar el costo por asignación accidental.

## Materiales y corte

**Pregunta:** «¿Qué necesito y qué corto?» Agrupación por perfiles/vidrios/herrajes, vínculo al dibujo y botones «Lista de pedido» y «Orden de corte». Elegir alcance ventana/proyecto con nombres claros.

El corte abre una vista real o faltantes concretos. Preferencias de taller resumidas; ajustes al solicitar. Distinguir borrador, plan vigente y orden liberada. Cambios de diseño invalidan lo necesario sin borrar el plan anterior.

No ocultar unidades, largos o ángulos para parecer limpio. Eliminar ruido administrativo; conservar información que evita cortar una pieza equivocada.

## Compras y existencias

**Pregunta:** «¿Qué falta y cómo lo consigo?» Proveedor y material como ejes, cantidad de compra calculada y motivos del faltante. Datos por unidad coherentes. Vínculo a obra/orden sin hacer de su código el nombre del producto.

Un pedido preparado no está enviado. El destino y documento se revisan antes de enviar. Un costo desconocido conserva estado pendiente; no se usa cero para completar el total. Existencias muestran diferencia entre reservado y disponible, y detalle de ubicación/lote cuando ayuda.

## Taller y CNC

**Pregunta:** «¿Qué hago ahora y con qué?» Responsable ve obra/avance/causa; operario ve pieza/dibujo/acción. Escaneo y botones accesibles con uso físico. Una incidencia conserva la pieza y contexto; no reinicia todo el trabajo.

CNC muestra máquina, estado de preparación y tipo real de salida. Un archivo neutro se llama así. Programas desactualizados no se presentan junto a vigentes con el mismo estado. Herramientas, mordazas y orientación viven en el detalle del equipo preparado por su responsable, no en el cotizador.

## Portal, terreno y cliente

**Portal:** oferta, ventanas, alcance y total primero. Alternativas y acciones según política de la empresa. Vencida/reemplazada debe identificar el motivo y permitir consultar el documento legítimo correspondiente. No usar un QR de otra revisión para que el enlace «funcione».

**Terreno:** visita, obra, ubicación/contacto, carga, dibujos y registro. Estado offline/pendiente/sincronizado visible. No convertir el vacío en «pide a alguien una ruta» si el rol puede planificarla; ofrecer la acción permitida.

**Clientes:** historial de obras y cotizaciones con ficha ligera; contactos y direcciones reutilizables. Buscar antes de crear duplicado. Datos personales se usan dentro del permiso y destino del trabajo, no se envían a fuentes externas por una investigación del asistente.

## Empresa y analítica

Preferencias organizadas por tarea; mostrar qué cambia para futuras operaciones y qué solo afecta a un proyecto. Seguridad, integraciones y proveedor IA en el rol apropiado. Una opción técnica no gana valor por añadirle un tooltip largo: retirarla del recorrido si el sistema puede gestionarla.

Analítica debe relacionar cifra, período, origen y acción posible. Un dato desconocido no es cero. No duplicar paneles del inicio o introducir un gráfico sin una pregunta de negocio.

## Acceso, portada y recuperación

El acceso actual por enlace y MFA conserva sus garantías. Presentar correo, envío y estado siguiente con claridad; permitir corregir correo/reintentar según límites y volver al destino legítimo que inició el acceso. Explicar enlace caducado, ausencia de membresía y verificación pendiente sin detalles internos de seguridad. No trasladar estos controles al asistente.

La portada pública debe enseñar el trabajo y sus resultados reales, con una acción principal y continuidad de marca. No añadir testimonios inventados, cifras sin fuente, una comparativa de superioridad no medida ni nuevos planes comerciales. Las superficies de recuperación conservan salida útil y diagnóstico técnico en detalle, evitando dejar una página vacía tras un fallo de ruta.

Correo reúne destinatario, documento exacto, muestra y botón de envío. El estado «entrega sin confirmar» requiere reconciliación; no debe convertirse en un reenvío automático potencialmente duplicado. La IA puede preparar contenido comercial permitido, con envío humano. Correo y acciones vinculadas a pagos quedan fuera de sus herramientas de operación de pagos.

## Detalles transversales para el pase final

Comprobar targets, foco, etiquetas, selección de texto, unidades, tabulación, Escape, capas, truncado de nombres con acceso al completo, guardado, cancelación, reintento y vuelta al punto anterior. Confirmar que al abrir un menú no se pierde un borrador; al cambiar una vista no se descarta una selección; al cerrar un panel no se cancela inadvertidamente un trabajo de IA.

En pantalla pequeña, plegar herramientas conservando una acción principal y el objeto. No encoger toda la interfaz de escritorio. Ofrecer búsqueda/filtros con estado recordado por contexto, sin filtros ocultos que hagan parecer que desaparecieron proyectos.
