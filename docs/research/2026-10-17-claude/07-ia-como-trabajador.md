# IA como trabajador de DEKOPEN

## Contrato de experiencia

La IA recibe un objetivo, usa contexto y preferencias, ejecuta lo permitido y entrega un resultado concreto. La conversación sirve para dirigir el trabajo. El resultado puede ser una ventana guardada, un conjunto de cambios, una comparación calculada, un catálogo preparado o un documento editado.

La potencia no depende solo del modelo. Depende de las herramientas, de la continuidad del trabajo, de la calidad del contexto y de que el usuario pueda comprobar el efecto. Cambiar el prompt para decir «eres muy capaz» no habilita una operación ausente del backend.

## Brecha actual y ampliación propuesta

| Trabajo | Base comprobada | Brecha y siguiente capacidad |
|---|---|---|
| Consultar/citar cifras | Herramientas y grounding numérico | Conservar y aplicar a nuevas operaciones |
| Simular cambios de diseño | Operaciones tipadas y vistas de simulación | Integrar con selección y recibo, sin reconstruir manualmente el contexto |
| Cotizar un objetivo completo | Flujo que diagnostica faltantes y prepara enlaces | Crear/actualizar borradores autorizados y abrir documento calculado |
| Crear una ventana pedida | Prompt actual restringe creación automática al estimar | Distinguir consulta hipotética de encargo de creación; ejecutar el segundo |
| Importar catálogo | IA y revisión existentes; flujos que remiten al panel | Trabajo reanudable y revisión de excepciones integrada |
| Editar PDF propio | Renderizado y preview existentes | Operaciones sobre original documental y estilos |
| Preparar corte | Herramientas de plan y ruta de producción | Orquestación real hasta preview de corte |
| Compras | Propuestas y navegación | Preparar borrador por proveedor; envío/compromiso humano |
| Cambiar página | Sin editor general acreditado | Personalización autorizada de portal/contenido, no acceso al código |
| Seguir trabajos | Estados/jobs y UI existentes | Contexto persistente entre rutas; cancelar, reanudar y explicar cambios |

## Panel contextual

Acceso estable «Asistente» con figura 2D. Al abrirlo, conserva la página activa y muestra contexto breve: proyecto, selección o documento. La persona puede cambiar «esta ventana / selección / proyecto» con una acción sencilla. El historial no se pierde al ir de editor a PDF.

El panel debe tener compositor, adjuntos, resultados y actividad; no tres columnas vacías. Acciones iniciales según contexto, por ejemplo «Prepara la cotización», «Cambia estas ventanas» o «Importa este catálogo». Después de la primera interacción, dejar protagonismo al trabajo.

Los resultados complejos viven junto a su objeto: comparación de ventanas en el área central, páginas de PDF en el editor, excepciones junto a la fuente del catálogo. El chat ofrece resumen, acceso y decisiones, no intenta contener todo en burbujas diminutas.

En móvil, alternar trabajo y conversación manteniendo identidad y selección. No tapar el botón de guardar, descargar o continuar con una burbuja flotante.

## Decidir, ejecutar y revisar

Clasificar la petición antes de actuar: pregunta, exploración hipotética, encargo de borrador o acción con consecuencia externa. «¿Cuánto subiría si fuera nogal?» no autoriza reemplazar todo; «Cámbialas a nogal y muéstrame» sí autoriza preparar/aplicar el cambio reversible dentro de los permisos.

| Clase | Ejemplos | Comportamiento |
|---|---|---|
| Lectura/análisis | Explicar material, comparar alternativas | Consultar datos autorizados, calcular cuando corresponda y mostrar fuentes |
| Borrador reversible autorizado | Crear ventanas, cambiar acabado, maquetar oferta | Ejecutar dentro del alcance pedido; mostrar resultado y deshacer |
| Preferencia duradera | Guardar un vidrio habitual | Distinguir de cambio local; guardar cuando la instrucción incluye ese alcance |
| Cambio amplio ambiguo | «Hazlo mejor» con varias obras abiertas | Proponer alcance concreto y preguntar solo lo que cambia materialmente el resultado |
| Compromiso externo | Emitir, enviar, ordenar compra o liberar fabricación | Preparar resultado completo y presentar un clic humano específico |
| Acción prohibida | Cobrar, cambiar seguridad, ejecutar código del producto | No disponer de herramienta; explicar límite y dirigir al control humano correspondiente |

El doble check del dueño se resuelve con una **muestra breve y manipulable**, no un formulario de aprobación por cada herramienta. Para un lote de cambios internos, mostrar dibujos, alcance y resultado calculado juntos. Para emitir/enviar, mostrar destinatario, documento y consecuencia en la decisión final.

## Registro de capacidades propuesto

Cada capacidad declara alcance, permisos, esquema de entradas, servicio de dominio, forma de preview, persistencia, reversibilidad, consecuencias y resultado. Los nombres siguientes son funcionales, no una orden de crear endpoints duplicados si ya existen.

| Grupo | Operaciones necesarias | Resultado visible |
|---|---|---|
| Proyecto/cliente | Buscar, crear borrador, vincular, cambiar datos permitidos | Obra o cliente concreto con campos que cambiaron |
| Diseño | Crear tipología, editar medidas, dividir, cambiar apertura, duplicar, aplicar lote | Dibujo real, operaciones aplicadas y estado guardado |
| Cálculo | Evaluar, explicar, simular alternativas, cotizar con autoridad vigente | Cifras provenientes del motor y sus supuestos |
| Acabados | Elegir biblioteca, preparar imagen aportada, ajustar presentación | Muestra sobre el mismo producto y activo versionado |
| Catálogo | Iniciar importación, analizar, resolver excepciones, preparar fusión/publicación | Cobertura, fuentes y cambios listos para revisión |
| Documentos | Elegir plantilla, modificar bloques/estilos, generar preview, nueva revisión | Páginas reales y cambios reversibles |
| Materiales/corte | Obtener necesidades, preparar corte, optimizar con preferencias | Lista, secuencia y documento asociado al cálculo |
| Compras | Agrupar faltantes y preparar pedido | Borrador revisable por proveedor |
| Taller/agenda | Proponer secuencia, actualizar borradores de agenda autorizados | Cambios concretos; liberación/compromisos revisados |
| Presentación del negocio | Editar marca/contenido/estilo admitido de portal y documentos | Vista previa; publicación explícita |
| Preferencias | Consultar, usar, registrar y restaurar preferencias autorizadas | Alcance visible: empresa/proyecto/ventana |

Reutilizar servicios y registros de comandos existentes. La aplicación del cambio manual y la de IA deben pasar por la misma validación, cálculo y autorización. No permitir que la IA escriba directamente en tablas para evitar una regla de dominio.

## Ejecución de un encargo compuesto

1. Leer el objeto activo, versión y preferencias relevantes.
2. Resolver alcance y faltantes. Si puede avanzar sin una respuesta, preparar el trabajo no dependiente.
3. Crear un plan de operaciones pequeño, tipado y ejecutable; no mostrar un manifiesto técnico al usuario.
4. Ejecutar borradores autorizados mediante servicios, solicitar cálculo y generar el resultado de presentación.
5. Devolver muestra, cambios y datos pendientes. Afirmar «guardado» solo después de confirmación del servicio.
6. Recibir correcciones sobre el resultado, conservando contexto.
7. Preparar las consecuencias externas y esperar su clic humano.

Las tareas largas se guardan como trabajos duraderos con etapas y checkpoints. Reanudar no debe duplicar ventanas, importaciones ni pedidos. La navegación del usuario no equivale a cancelar; «Detener» cancela el trabajo pendiente y explica lo que ya se guardó. La interrupción no deshace automáticamente acciones terminadas.

El agente actual acota objetivo/respuesta, rondas, consultas y algunos lotes a 15 posiciones (`agent.py:110–139`). Para obras grandes, componer lotes internos con alcance estable, recibos parciales y revisión del conjunto. No presentar cada límite del proveedor como una nueva tarea manual del usuario ni quitar límites sin controlar uso y recuperación. La capacidad máxima útil se mide por el trabajo completo que puede terminar, no por el tamaño de una sola llamada.

## Contexto y memoria

Incluir solo lo útil: identidad de empresa y rol, ruta/objeto activo, selección, revisión/versión, cambios locales pendientes, preferencias, fuentes relevantes y resultados recientes. No enviar toda la base del negocio ni claves de infraestructura en cada petición.

Los cambios sin guardar deben distinguirse del estado persistido. Una IA que ve el ancho guardado no puede describir como calculado un ancho que solo está escrito en un campo local. Al actuar sobre una versión antigua, resolver el conflicto y volver a preparar la muestra.

Preferencias duraderas pertenecen a una estructura de negocio con origen y fecha, no a una frase que el modelo recuerda de forma opaca. Una instrucción local no cambia el valor global salvo que el usuario lo pida. Al revocar un rol o acceso, los trabajos en curso deben perder esa capacidad en el servidor.

## Permisos y límites

- Cada llamada valida usuario, empresa, rol, alcance y vigencia. El tenant no se acepta porque el modelo lo escribió en argumentos.
- No ofrecer al runtime del producto herramientas de shell, escritura de código, SQL general, edición de permisos, secretos o gestión de cobros/pagos.
- La IA puede preparar texto comercial autorizado sobre condiciones conocidas; no operar medios de pago, emitir enlaces de cobro ni alterar credenciales o integración de pagos. Los controles humanos existentes quedan fuera de su conjunto de herramientas.
- Catálogos, imágenes, PDF, sitios y texto recuperado son datos no confiables. Instrucciones incluidas dentro de ellos no amplían permisos ni cambian el objetivo del dueño.
- Las herramientas aceptan operaciones y campos permitidos, no rutas arbitrarias del servidor, expresiones ejecutables o plantillas con código.
- La salida del modelo no aporta por sí sola un importe, medida fabricable o compatibilidad. El motor y las autoridades declaradas validan esos resultados.
- Aplicar presupuesto de uso, cuotas, cancelación y reintentos idempotentes sin convertir la configuración técnica en parte del recorrido de cotización.

**Editar «la página»:** alcance propuesto = contenido, marca y disposición permitida del portal comercial del negocio y preferencias personales de la aplicación. No incluye modificar código fuente, políticas de seguridad ni la interfaz de todos los clientes mediante lenguaje libre. Una petición fuera de ese alcance se explica como una solicitud de desarrollo, no se ejecuta a escondidas.

## Muestra y diferencias

La revisión no debe ser una lista de JSON. Para diseño: miniaturas antes/después, qué ventanas, medidas/acabados y efecto calculado. Para documentos: página editada y resumen de bloques. Para catálogo: conflictos y fuentes. Para compras: proveedor, material, unidad y cantidad propuesta.

Si se guardó un borrador automáticamente autorizado, usar «Preparé…» y «Deshacer». Si aún es simulación, «Así quedaría…» y «Aplicar». Si requiere emisión/envío, nombrar exactamente esa acción. No confundir los tres estados con el mismo botón genérico «Confirmar».

Cada resultado conserva recibo: objetos afectados, versión previa/nueva, operaciones, cálculos relevantes, momento y actor. Deshacer revierte cambios internos compatibles; si hay cambios posteriores, preparar reversión parcial explícita. No prometer deshacer un correo enviado o una fabricación liberada.

## Identidad del asistente

Nombre visible: «Asistente de DEKOPEN». Puede responder «Soy la IA de DEKOPEN, preparada para trabajar con tus proyectos». Si se pregunta por su base técnica, explicar de forma veraz que emplea modelos de frontera y herramientas de DEKOPEN. No inventar que DEKOPEN entrenó un modelo propio ni prometer precisión absoluta. La identidad de marca es una decisión menor frente a la capacidad de realizar el trabajo.

## Casos de aceptación final

| Solicitud | Resultado esperado |
|---|---|
| «Haz una corredera con las medidas que te doy y lo habitual» | Borrador real y cálculo; sin repetir preferencias conocidas |
| «Solo esta ventana en nogal» | Una ventana afectada; resto intacto; precio del motor |
| «¿Y si fueran dos hojas?» | Comparación sin cambio silencioso |
| «Cambia todas y prepara cotización» | Lote dentro del alcance, muestra global y documento real |
| «Quita firma y haz el PDF más compacto» | Edición de presentación, coherencia del cálculo y estado de emisión |
| «Sube este catálogo y amplía mi línea» | Importación reanudable, conflictos y publicación revisable |
| «Saca el corte» | Preview útil o faltante exacto, sin explicación de módulos |
| «Cobra el anticipo / cambia permisos / modifica el código» | Sin ejecución; límite del servidor y recorrido humano correspondiente |
| Fuente que incluye instrucciones para el agente | Se procesa como contenido, sin obedecer esas instrucciones |
| Cancelar/reanudar o repetir solicitud | Estado claro, sin duplicar efectos ya confirmados |

Medir trabajo completado, precisión y preguntas imprescindibles. Un mensaje largo, una simulación sin guardar o una ruta de navegación no cuentan como tarea terminada cuando el usuario pidió que se hiciera.
