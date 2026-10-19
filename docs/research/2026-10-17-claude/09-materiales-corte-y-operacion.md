# Materiales, corte y continuidad operativa

## Materiales como resultado del diseño

La lista de materiales se abre desde el proyecto o una ventana. No se debe confundir consumo de diseño, longitud de corte, unidad de compra y stock disponible. El motor y sus reglas generan necesidades; la presentación las organiza para una decisión humana.

La vista habitual combina dibujo/lista de ventanas y grupos de **Perfiles, Vidrios, Herrajes y Otros**. Una selección resalta la ventana o pieza relacionada. Cada fila muestra nombre, referencia útil, acabado, cantidad y unidad; detalles de regla/procedencia a un clic. Para un proyecto grande, usar tabla con búsqueda y agrupación, no un modal estrecho con un bloque enorme por SKU.

| Vista | Información que importa | Acciones |
|---|---|---|
| Por ventana | Qué piezas componen cada diseño | Abrir dibujo, revisar pieza, documento |
| Consolidado | Totales por referencia/acabado/unidad | Lista de pedido, corte y exportación |
| Abastecimiento | Necesidad frente a stock/reserva/tránsito | Preparar compra y elegir proveedor |
| Fabricación | Piezas, largos, ángulos y secuencia | Orden de corte y etiquetas |

No sumar barras y metros como si fueran una misma unidad ni ocultar redondeos de compra dentro del consumo. Los retazos y rendimientos se presentan con la autoridad de optimización; la IA puede explicarlos, no recalcularlos libremente.

## Acceso directo a orden de corte

Ubicaciones: acción visible dentro del proyecto y materiales; opción equivalente desde la ventana para un alcance pequeño. El texto es **«Orden de corte»**. No obligar a conocer «pack», estado de OT o pestaña de optimización para encontrar el resultado.

Recorrido propuesto:

1. El usuario pulsa «Orden de corte».
2. El sistema reúne el alcance, versión del diseño y preferencias de taller; prepara lo derivable.
3. Si puede calcular, muestra secuencia de barras/piezas y documento real con la plantilla habitual.
4. Si falta algo necesario, presenta una lista corta de causas localizadas y la acción para resolver cada una.
5. Descargar un borrador interno no debe confundirse con liberar una orden ejecutable. Cuando haya una consecuencia de fabricación, un botón específico permite revisar/liberar el resultado preparado.

No debilitar los estados de fabricación para conseguir un botón rápido. Antes de implementar, mapear servicios de factibilidad, orden, optimización y documento del código actual. Añadir orquestación reutilizable si la composición todavía solo existe en frontend.

## Preferencias de taller

Longitudes comerciales, disco/kerf, despuntes, mínimos de retazo, agrupación, stock/retazos utilizables y criterios de orden provienen de configuración autorizada. No proponer valores numéricos universales en este plan.

La primera vista muestra qué estrategia está usando. «Ajustar corte» despliega opciones y su efecto calculado. Cambiar una preferencia global requiere ese alcance; una excepción local no debe alterar otras órdenes. Mostrar si el resultado usa stock real, disponibilidad declarada o barras teóricas.

Cuando una medida cambia, marcar la orden anterior como desactualizada y preparar otra muestra. No permitir que un PDF antiguo parezca el corte actual solo porque conserva un nombre de archivo conocido.

## Orden de corte útil en planta

La secuencia visual de barras existente es una base valiosa. Mantener correspondencia estable entre pieza, dibujo, etiqueta y destino. Un código físico puede ser indispensable junto a la máquina aunque no deba dominar la oferta comercial.

Mostrar perfil/acabado, barra, cortes, ángulos, cantidad, retazo y orden de ejecución. Distinguir piezas visualmente iguales de destinos diferentes. Las referencias de orientación no pueden invertirse al elegir una vista interior/exterior de presentación.

Preparar las tres plantillas del documento 06 sobre los mismos hechos. No permitir que un cambio de estilo altere secuencia, unidades, agrupación calculada o cantidades. Etiquetas con contraste y tamaño adecuado; código legible y vínculo al destino. El código QR/barra no reemplaza nombre/dibujo cuando el operario necesita reconocer una pieza sin escanear.

## Compras e inventario

**Compras:** preparar lo que falta, agrupado por proveedor. Filas compactas con nombre, referencia, acabado, unidad comercial, cantidad sugerida y costo conocido. Mostrar consumo, stock disponible y tránsito en detalle o columnas escogidas según tarea. Conservar causas de falta de costo o proveedor como acciones concretas. Un borrador de compra puede elaborarse con IA; emitir/enviar mantiene el control humano.

**Inventario:** búsqueda por nombre/código/acabado; diferencia clara entre existencia, reservado y disponible. Longitud y ubicación importan para barras/retazos, composición para vidrio y unidad para herrajes. El historial está disponible sin ocupar la tabla inicial. No fusionar referencias repetidas solo porque comparten texto: pueden distinguir acabado, lote, proveedor o autoridad de costo.

**Recepción:** recorrer pedido → recibido → diferencia → ubicación, con evidencias cuando haga falta. No dar por recibido porque exista un comprobante subido por IA; proponer conciliación y confirmar en la operación autorizada.

## Producción y estación de operario

| Persona | Primera vista | Detalle bajo demanda |
|---|---|---|
| Responsable de taller | Obra, avance, cantidad y bloqueo que requiere decisión | Orden, piezas, cobertura y documentos |
| Operario | Pieza actual, dibujo/orientación, acción y siguiente paso | Material, instrucción y motivo de excepción |
| Compras | Faltantes por proveedor y obra afectada | Reservas, costos y reglas de compra |
| Dueño | Riesgo de plazo/costo y decisiones | Trazabilidad y análisis |

Las tarjetas de producción no deben ser todas iguales con una OT como único identificador. Añadir nombre de obra, dibujo útil y siguiente acción. Agrupar bloqueos de la misma causa; no generar una alarma por cada pieza si una sola decisión resuelve todo el lote.

En planta: controles grandes, contraste, uso con guantes donde aplica y confirmación de eventos físicos de riesgo. Una interfaz viva no necesita animaciones decorativas durante escaneo o validación de pieza. Conservar rechazo/incidencia, repetición y trazabilidad de calidad.

## CNC: alcance honesto y útil

La salida comprobada en `backend/production/cnc.py:943–965` es `NEUTRAL_INTERCHANGE`. Hay validación, perfiles de máquina y control de vigencia; no se ha acreditado una conexión ni calibración con máquina física. La UI debe nombrar esa salida con precisión.

| Nivel | Entrega | Evidencia necesaria |
|---|---|---|
| Preparación | Operaciones y piezas normalizadas, con orientación | Reglas y fuentes completas |
| Intercambio neutro | Archivo y manifiesto de versión | Concordancia con operaciones autorizadas |
| Adaptador de máquina | Formato específico de controlador/postprocesador | Especificación y muestras verificadas |
| Compatibilidad homologada | Herramientas, mordazas, ejes y límites resueltos | Revisión técnica y prueba controlada en máquina |
| Operación de planta | Transferencia y ejecución bajo procedimiento | Registro real del taller y controles del operador |

La integración debe usar contrato de adaptador, fixtures de formatos y metadatos de versión. No llamar «compatible con marca X» a un archivo genérico ni prometer G-code universal. El modelo puede ayudar a preparar configuraciones y explicar faltantes; no autorizar colisiones, elegir herramientas no declaradas ni saltar revisión de programa obsoleto.

La pantalla CNC aparece al equipo que la usa: máquina, preparación, bloqueos y programa. El vendedor que cotiza una ventana no debe configurar mordazas. La v1 puede entregar intercambio neutro de calidad y una integración concreta homologada cuando existan máquina, documentación y acceso; sin ellos, declarar el límite pendiente.

## Despacho, terreno y postventa

Unificar el hilo de obra: qué debe salir, a dónde, con qué equipo, qué falta y qué se registró. Evitar que una ventana se vuelva un código irreconocible al cambiar de módulo.

En móvil, agenda y detalle de visita con ubicación/contacto autorizados, dibujos, carga e instrucciones. Indicar si los datos están guardados localmente, pendientes de sincronizar o confirmados por servidor. La sincronización no debe duplicar eventos por reintento. No prometer trabajo offline completo sin comprobar qué operaciones están soportadas.

Postventa enlaza incidencia con la ventana y revisión entregadas. Fotos/notas no sustituyen identificación técnica. Mostrar estado, responsable y siguiente acción, con historial para investigación del problema cuando haga falta.

## Clientes, portal, analítica y ajustes

**Clientes:** ficha clara con proyectos, contacto habitual y direcciones reutilizables. Crear desde el trabajo activo y evitar duplicar el mismo cliente por pequeñas variaciones del nombre. No exigir una agenda de contactos completa para una propuesta preliminar.

**Portal:** la oferta y su contenido primero. Alternativas, alcance, precio y condiciones legibles en móvil. Aceptación, firma y pago aparecen solo cuando el negocio activa esos pasos; el asistente no opera pagos. Documento y portal identifican la misma revisión.

**Analítica:** responder preguntas del negocio con datos trazables: qué requiere decisión, dónde cambia el costo o qué retrasa una obra. No introducir cifras sintéticas ni paneles de KPI por decorar. Las fuentes actuales no bastan para rediseñar toda la analítica como si ya hubiera sido observada en vivo; completar esa visita antes de cerrar su composición.

**Ajustes:** Empresa, Ventas, Documentos, Taller, Catálogos e Integraciones, con permisos y diferencias entre valor habitual y excepción. El proveedor de IA, la seguridad y los registros técnicos se ubican para su rol; no forman parte de cotizar una ventana.

## Aceptación final

Una obra debe recorrer diseño → cotización → materiales → corte → preparación de compra/taller sin reingresar los mismos datos. Comprobar que cambiar una ventana invalida o actualiza las salidas correspondientes, que cada documento tiene alcance y versión reconocibles y que los permisos se conservan aunque la navegación sea más sencilla.
