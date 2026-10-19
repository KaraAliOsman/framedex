# Copiloto opcional y capacidades comerciales

Documento de dirección para Claude. Fecha: **18-10-2026**. Inspección estática de la rama **claude/v1-implementacion**, HEAD **6f78e329**, con cambios locales existentes. No se ejecutaron proveedores, pagos, tareas de IA ni pruebas de producto durante esta investigación.

## Decisión vigente del propietario

DEKOPEN debe ser un **cotizador y sistema de trabajo manual excelente por sí mismo**. El plan más barato es manual y no incluye IA; conserva precisión, calidad de diseño, documentos y capacidades manuales. El dueño confirmó **MiMo para todos los planes IA hasta que él decida cambiarlo**, y aclaró que se refería a créditos. La propuesta operativa de este paquete adopta un mismo núcleo/calidad y control, límites proporcionales y posibles extras profesionales explícitos. Esa matriz de funciones es nuestra propuesta, no una cita literal de identidad absoluta entre todas las funciones ni una nueva oferta comercial. No se vende una IA deliberadamente peor ni menos control al plan IA menor.

El copiloto es global, opcional e invocado por la persona. Se presenta en **popup no modal**, con **Chat** y **Trabajo**. No es una columna permanente de cotización, editor o proyecto. **Estudio** y **Mesa de obra** son dos presentaciones manuales elegibles del mismo estado de negocio: ninguna depende del copiloto ni crea una segunda versión de la obra.

Las tres políticas son **Solo proponer**, **Con aprobación** y **Omitir todo**. Cambiar de política no amplía el rol, catálogo autorizado o autoridad del motor. En Omitir todo, una tarea reversible ya delegada se ejecuta completa sin pedir confirmación por cada paso; el resultado y sus excepciones se presentan al final.

Esta dirección prevalece sobre las formulaciones anteriores “AI-native” en [PRODUCT](../../PRODUCT.md) y [owner-decisions](../../wiki/decisions/owner-decisions.md), y sobre el riel compartido de las secciones 5.6/5.11 de [CONSTITUCION](../../design/CONSTITUCION.md). La fase 01 debe conciliar las cláusulas que sigan afectadas, conservando la corrección que la wiki ya registre. No usar una frase histórica para revivir un riel o una IA central obligatoria. Este informe no modifica esas páginas compartidas.

## Adjuntos multimodales — ampliación explícita del dueño

El dueño añade documentos, imágenes y los demás archivos compatibles como entrada del copiloto. Es alcance funcional de esta candidata, tanto en Chat como en Trabajo; no se posterga como integración de producción. Adjuntar permite consultar la fuente; aplicar cambios sigue el modo, la política y el encargo. Todos los planes con IA comparten esta capacidad, con sus límites de consumo. La importación estructurada manual conserva su recorrido sin IA.

### Interacción y formatos

Desde el compositor del popup: botón Adjuntar, arrastrar archivos y pegar imágenes; en dispositivos compatibles, captura desde cámara mediante el selector del sistema. Admite varios archivos en un encargo. Antes de enviar, permite previsualizar, quitar y ver qué archivos se usarán. Al minimizar, navegar o recargar se conservan los adjuntos persistidos y su estado; una subida incompleta se identifica como pendiente y no se finge recuperada.

Mínimo de desarrollo: PDF con texto o escaneado; PNG/JPEG/WebP; XLSX/CSV; DOCX y TXT/Markdown. XLSX conserva hoja/celda/unidad; DOCX conserva párrafo/tabla y declara elementos no interpretables. No ejecutar macros, fórmulas externas ni contenido activo. Valores de planilla sin caché o con vigencia desconocida no son cálculos técnicos verificados. Formatos adicionales se habilitan mediante un registro único del servidor, solo con adaptador, alcance y verificación final reales. Audio, vídeo, CAD/BIM y documentos protegidos no se anuncian por el hecho de que el selector pueda elegirlos.

La matriz de soporte distingue formato aceptado, contenido legible, tarea aplicable y restricciones. Tamaño, páginas, resolución, hojas y cantidad de archivos se validan contra el pipeline completo y presupuesto; no se copian límites comerciales del proveedor. Informa límites efectivos antes de procesar y cobertura real al terminar. Una lectura parcial enumera páginas/hojas/elementos pendientes. Nunca «leído completo» por procesar solo el principio.

### De archivo a trabajo verificable

- Estados por archivo: Subiendo, Preparando, Listo para consultar, Lectura parcial y Error. «Listo» no significa validado para fabricar.
- Adjuntar, previsualizar o volver a abrir no inicia llamadas pagadas. Enviar una consulta o delegar habilita el procesamiento necesario bajo los límites vigentes. Reutilizar extracciones seguras por hash/versión del adaptador dentro de su ámbito autorizado, sin cobrar otra vez por recuperar lo ya producido.
- Preservar original, hash, nombre, tipo real, autor, organización, permisos, versión de extracción y cobertura. Relaciones tipadas con turno/tarea; no una URL temporal como identidad del archivo.
- La extracción conserva evidencia navegable: PDF/página/región, imagen/región, planilla/hoja/celda o documento/párrafo/tabla. Abrir la cita muestra la fuente correcta bajo permisos actuales. Una cita acredita procedencia, no exactitud.
- Combinar texto y visión cuando el documento lo requiera. Extraer de forma determinista cuando baste; usar MiMo para interpretar. Un PDF con texto puede contener información visual relevante.
- Resolver contradicciones por autoridad y versión explícitas, sin elegir por fecha de subida. Ante una decisión material ausente, señalar ambos valores y agrupar la pregunta; continuar lo independiente. Una foto sin cotas no aporta medidas de fabricación. Motor y catálogo revisado conservan su autoridad.
- Adjuntar a un hilo no publica en catálogo ni comparte con la empresa. Incorporar una fuente a una obra o biblioteca compartida exige alcance explícito y permiso. Los documentos son datos, nunca instrucciones para ampliar herramientas o autorización.

**Base inspeccionada, no función completa acreditada.** [extract.py](../../../backend/ingest/extract.py) reconoce PDF, XLSX/XLSM, imágenes y CSV, y TXT/EML en rutas con `allow_text`; no incluye lector DOCX ni Markdown declarado. [multimodal.py](../../../backend/ai_gateway/multimodal.py) procesa PDF mediante texto y ciertas páginas con imagen, con límites propios; [providers.py](../../../backend/ai_gateway/providers.py) construye partes de imagen en rutas existentes. No prueban un uploader global completo. Claude debe integrar y completar esa experiencia.

La [documentación oficial MiMo](https://mimo.mi.com/docs/en-US/quick-start/usage-guide/multimodal-understanding/image-understanding), consultada el 18-10-2026, incluye `mimo-v2.6-pro` y entrada de imágenes por URL o Base64. DEKOPEN puede enviarlas desde su backend sin hacer público el archivo. Esto no acredita la cuenta/ruta configurada ni entrada nativa de binarios Office/PDF: requieren adaptador y verificación en 07. No introducir otro proveedor silenciosamente.

Ver [desarrollo 05](prompts/05-copiloto.md) y [nota de innovación](../2026-10-18-innovacion/06-archivos-y-mejoras-con-sentido.md), que separa este requisito de las ampliaciones recomendadas.

## Qué dicen las fuentes de planes

El [brief original](C:/Users/alios/.codex/attachments/b8dca4f1-0c32-4aa3-824c-68bad9f2bf23/Texto%20pegado.txt) contiene varias iteraciones, no una sola tabla final:

| Evidencia | Contenido | Interpretación válida ahora |
|---|---|---|
| Primeras ideas y resumen intermedio | Sin IA USD 30, Normal USD 50, Max cercano a USD 120, bolsas de consumo y recargas | Contexto histórico. No catálogo de lanzamiento confirmado. |
| Propuesta posterior del mismo texto | Sin IA USD 39 manual completo; Normal USD 69 con documentos y asistencia; Max cercano a USD 149 con delegación y flujos avanzados | Mantener la separación por valor, sin convertir estos números o nombres en aprobación comercial nueva. |
| [PRD-03](../../PRD/PRD-03.md), sección 3 | Trial, Starter, Profesional, Business y Business 2x; precisión, 2D, BOM, cortes y PDF comunes | Documento vigente en el repositorio, con otra evolución de planes. Sus cifras no se cambian desde estos prompts. |
| [Motor billing](../../../engine/src/dekopen_engine/billing.py), líneas 46–60 | Códigos STARTER/PRO/BUSINESS/BUSINESS_2X y términos congelados | Hecho de implementación. No inferir que la nueva propuesta ya autoriza migrar suscriptores o contratos. |
| Última decisión del dueño | Base sin IA excelente; superiores con valor mucho mayor | Autoridad de experiencia. Preparar capacidades ahora y dejar contratación/cobros para una fase comercial explícita. |

La orientación más reciente del dueño conduce a sustituir el corte entre asistencia y delegación para las capacidades principales: proponemos núcleo/calidad común, límites de uso proporcionales y extras profesionales concretos. «Pagar 2x para disponer de 2x límite» y la pequeña referencia «anual 30/49/99/149» no son precios, cuotas o migraciones aprobados. El [contrato de planes, créditos y límites](04-planes-creditos-y-limites.md) distingue decisión explícita, contratos reales y propuesta de implementación, sin atribuir una identidad absoluta de todas las funciones como cita del dueño.

También existen diferencias sobre medición: PRD-03 describe débito por tokens; **service.invoke** toma actualmente **route.credits_cost** para el débito, mientras **usage.py** registra medición y costo físico por separado. La propuesta no debe vender una conversión monetaria ficticia ni cambiar silenciosamente este contrato financiero.

## Arquitectura actual comprobada

| Superficie o contrato | Hecho en el código leído | Consecuencia |
|---|---|---|
| [AppShell](../../../frontend/src/app/AppShell.tsx), línea 104 | La presencia y botón se habilitan por rol OWNER/ESTIMATOR/WORKSHOP_MANAGER | El plan base puede recibir UI de IA aunque el proveedor vaya a rechazarla. Falta composición con entitlement. |
| [AskDekopen](../../../frontend/src/features/assistant/AskDekopen.tsx), líneas 31–47, 88–89 | Guarda apertura en sessionStorage; monta AgentBody con clave surface/refs | Cambiar de pantalla reasocia la conversación. No es un hilo global estable. |
| [assistant.css](../../../frontend/src/features/assistant/assistant.css), inicio | Panel fijo de 384 px; estrecha la app y oculta el inspector | Contradice popup opcional y continuidad manual. Hay que retirar esos efectos de layout. |
| [AssistantPanel](../../../frontend/src/features/canvas/AssistantPanel.tsx) y AssemblyEditor | Asistente y alternativas dentro del inspector con endpoint de diseño propio | Debe converger al popup global; alternativas manuales útiles permanecen manuales. |
| [assistantContext](../../../frontend/src/features/assistant/assistantContext.tsx), líneas 42–145 | Proyecta ruta y referencias; selección volátil no cambia referencias estables | Reutilizar la separación selección/objeto, separando también hilo y destino de escritura. |
| [assist.py](../../../backend/ai_gateway/assist.py), líneas 321–393 | ai_ask_turns persiste por usuario/surface/refs; restaura las últimas 50 | Sí existe historia. Es segmentada y acotada; se debe migrar/conservar, no borrarla. |
| [jobs.py](../../../backend/ai_gateway/jobs.py) | ai_jobs conserva transcript, plan, artefactos, outcomes y claves idempotentes | Base aprovechable para tareas y recibos. Un job no debe seguir siendo la identidad del hilo global. |
| [serializers](../../../backend/ai_gateway/serializers.py), líneas 114–243 | Solo admite autonomía propose/draft | No existen todavía tres políticas explícitas ni modo Chat/Trabajo contractual completo. |
| [agent.py](../../../backend/ai_gateway/agent.py), líneas 178, 1545–1600 | Draft permitido a OWNER/ESTIMATOR; estado final depende de preguntas/propuestas pendientes | No basta cambiar etiquetas: terminar debe comprobar las postcondiciones del encargo. |
| [handlers](../../../backend/ai_gateway/handlers.py), líneas 20–157 | Worker revalida membresía y rol antes de ejecutar | Preservar y ampliar a permiso/capacidad efectiva por operación y en reanudación. |
| [service.invoke](../../../backend/ai_gateway/service.py), líneas 232–357 | Replay idempotente; bloquea STARTER/inactivo; reserva presupuesto; pasa por proveedor; audita/débita | Puerta central de gasto reutilizable. El gate actual no distingue niveles de capacidades IA. |
| [wallet.summary](../../../backend/billing/wallet.py), líneas 117–130 | ai_available combina plan, activo y saldo | No distingue contratación, capacidad, presupuesto, proveedor ni causa operativa. |
| [usage.py](../../../backend/ai_gateway/usage.py) y [configuration](../../../backend/ai_gateway/configuration.py) | Presupuesto mensual, reservas, medición física, tarifas declaradas y rutas por organización | Conservar costo desconocido como desconocido y comprobar cupo antes de cada nueva llamada. |
| [ACTIVACION](../../operations/ACTIVACION.md) y [offers.py](../../../backend/billing/offers.py) | Adaptador de plataforma Flow existente y activación diferida; ofertas provisionadas por operador | No empezar una integración Stripe, ni publicar ofertas o modificar FX, pagos o renovaciones en esta fase. |

Los hechos anteriores son estáticos, no una aceptación de funcionamiento ni de los resultados históricos de la wiki.

## Contrato del popup

### Presencia, tamaño y accesibilidad

- Inicio de sesión con popup cerrado. Abrir desde el botón Asistente o una acción explícita “Delegar”; ninguna página genera una llamada de IA al montar, navegar, seleccionar, cambiar Estudio/Mesa o abrir el popup.
- Una sola instancia global por sesión y organización. Abrirla de nuevo trae la misma conversación al frente.
- No modal: sin scrim, sin bloquear clics ni teclado del editor, sin secuestrar el foco ni cerrar el inspector. La app manual conserva sus columnas.
- Estado flotante inicial propuesto: 420 × 600 px en escritorio, limitado al viewport, con mínimo útil de 340 × 420. Son parámetros de diseño, no capacidades comerciales. En espacio menor se adapta al viewport con cabecera recuperable y cuerpo desplazable.
- Cabecera con título, Chat/Trabajo, historial, minimizar, ampliar/restaurar y cerrar. Arrastre desde cabecera y redimensión desde bordes; alternativa accesible mediante controles de mover/redimensionar y flechas, Enter para confirmar y Escape para abandonar el ajuste.
- Posición/tamaño se recuerdan por persona, organización y dispositivo; se corrigen al cambiar viewport, zoom u orientación. No guardar mensajes, planos, precios o credenciales en localStorage.
- Minimizar conserva tarea y borrador; cerrar oculta la ventana y tampoco cancela. **Detener trabajo** es acción distinta. Un trabajo iniciado por la persona puede mostrar estado compacto en el lanzador, sin animación continua ni robo de foco.
- Ampliar usa el espacio de la app para revisar conversación/resultados; restaura la geometría anterior. Una ruta de historial puede abrirse explícitamente, conservando el mismo thread y sin convertir la IA en pantalla obligatoria.
- Escape respeta menús y campos en composición; después oculta/minimiza el popup, nunca cancela un job silenciosamente. Al cerrar se devuelve foco al invocador si sigue montado. Abrir resultados no roba el foco durante escritura.
- En móvil no fingir arrastre de escritorio. Presentación adaptada con minimizar/restaurar, áreas táctiles y acceso claro al contenido manual; sin diálogo de confirmación por cada reacomodo.

### Chat, Trabajo y políticas

| Control | Significado |
|---|---|
| Chat | Responde y explica con fuentes. No cambia dominio, emite documentos ni transforma preguntas en mutaciones. Puede preparar una propuesta sin aplicarla. |
| Trabajo | Acepta un objetivo delegado, planifica brevemente, consulta contexto autorizado, ejecuta herramientas y verifica resultado. |
| Solo proponer | Produce diferencias/artefactos y explica efecto. Cero mutaciones del dominio. El cambio posterior requiere delegación explícita o aprobación. |
| Con aprobación | Prepara el conjunto coherente y presenta una aprobación del resultado, con detalle expandible. Evita aprobaciones por tornillo o por consulta. |
| Omitir todo | Aplica lo reversible autorizado, encadena pasos necesarios y verifica antes de cerrar. No introduce confirmaciones nuevas por decisiones rutinarias. |

Las tres políticas están disponibles para todo trabajo habilitado; no se vende menor seguridad o mayor fricción según plan. La política efectiva viaja con cada tarea y queda en el recibo. Un cambio durante una ejecución no reinterpreta retroactivamente la autorización del job en curso.

Desde Chat, una orden que requiere cambios ofrece “Hacer en Trabajo”, transfiriendo texto, contexto y archivos en el mismo hilo. No se aplica por sorpresa. Desde una acción explícita Delegar se abre Trabajo con el destino indicado; el envío del encargo es la autorización para el trabajo reversible dentro de ese alcance.

### Conversación, selección y destino

Separar cuatro conceptos: **thread** (continuidad), **contexto de lectura** (lo que observa), **selección** (elementos actuales) y **destino de escritura** (objeto/versiones autorizados).

La ruta cambia el contexto disponible para un nuevo mensaje, no el hilo ni el objetivo de una tarea ya iniciada. Antes de enviar, una línea compacta nombra obra, posición/selección y destino; permite quitar o cambiar el alcance sin consultar al modelo. Un encargo explícito sobre otro proyecto usa su identificador autorizado y lo muestra como destino. Navegar después no redirige escrituras.

Cada turno sella referencias, versión/fingerprint, adjuntos y política efectiva. Los índices visuales no identifican hojas ni posiciones. Si cambia el objeto, una relectura y nueva simulación pueden continuar con la misma intención cuando el efecto sigue dentro del alcance delegado. Si hay conflicto semántico, conservar edición humana, completar lo independiente y presentar el conflicto concreto; nunca sobrescribir por último escritor.

Las herramientas leen o mutan objetos autorizados por ID. No hace falta conducir al usuario por pantallas para ejecutar cada paso. La navegación ofrece abrir el resultado y solo cambia de pantalla durante el trabajo cuando la persona lo pidió o aceptó seguirlo.

## Persistencia y ejecución propuestas

Agregar **ai_threads** como identidad privada por org/persona y asociar los **ai_jobs** existentes mediante thread_id. Conservar ai_ask_turns y transcripts históricos: migración idempotente con vínculo al origen, sin pérdida de fechas, outcomes o claves. La lectura unifica historial paginado; no inventar otra conversación en cada ruta ni limitar la historia visible a las últimas 30/50 entradas.

Campos lógicos del thread: identidad, organización, persona propietaria, título editable, modo preferido, política preferida, archivado y timestamps. Tarea: thread_id, objetivo, contexto/destino sellados, versión, política, capacidades requeridas, entradas, postcondiciones, pasos, resultado y recibo. La implementación debe aprovechar columnas/contratos existentes y añadir solo lo ausente; no recrear todo el gateway.

El estado de la ventana es local; el hilo y el job son duraderos. Otra persona no ve conversaciones privadas aunque tenga rol superior. Un registro administrativo de consumo no expone prompts o respuestas sin un contrato de privacidad explícito. Al cambiar de organización se limpia la caché y se cierra el popup, sin adoptar tareas del tenant anterior.

**Postcondiciones antes de Completado.** Para “crea las posiciones y prepara la cotización”, comprobar que las posiciones esperadas existen con geometría válida, que se calcularon mediante el motor y que el borrador pedido existe. Una respuesta convincente, un enlace o un job sin excepciones de transporte no prueban éxito.

Recibo final: objetivo; objetos y cantidades cambiados provenientes del motor/DB; aplicados, omitidos o bloqueados y causa; versión antes/después; costo/créditos medidos; abrir resultado; deshacer aplicable. Estado “Parcial” si queda trabajo solicitado sin completar, con checkpoint para continuar. No maquillar omisiones como éxito.

## Fallos, reintentos, versiones y costo

| Situación | Comportamiento esperado |
|---|---|
| Timeout/pérdida de respuesta | Consultar job/intercambio existente antes de reintentar. Misma clave y resultado ya pagado no generan otra llamada ni débito. |
| Falla parcial | Conservar checkpoints y cambios confirmados; rollback o compensación según contrato del servicio. Recibo distingue lo aplicado de lo pendiente. |
| Cancelación | Cooperativa entre pasos; no promete deshacer llamadas ya realizadas. Reportar estado persistido y consumo físico real. |
| Rol revocado/tenant cambiado | Revalidar antes del siguiente efecto y al reanudar. Bloquear lo no autorizado conservando acceso solo a información permitida. |
| Crédito/presupuesto agotado | Parar nuevas llamadas, guardar trabajo y permitir continuar manualmente. No bloquear motor, PDFs, cortes ni vistas manuales. |
| Proveedor no configurado | Explicar causa y vía administrativa dentro del copiloto; ningún banner obligatorio sobre el cotizador. |
| Versiones concurrentes | Comparar estado esperado, releer y simular; no restaurar una versión anterior encima de cambios ajenos. |
| Deshacer | Revertir el cambio propio si sigue siendo seguro. Si hubo edición posterior, ofrecer comparación/restauración como nueva revisión; no borrar historial emitido. |
| Costo desconocido | Mostrar Sin dato. Distinguir créditos cobrados, reservas y costo monetario del proveedor; no tratarlos como equivalentes. |
| IA propone dato sin fuente | Mantener pendiente; no completar mm, precio, compatibilidad, Uw o CNC desde lenguaje probabilístico. |

MiMo 2.6 Pro es la selección vigente del dueño para todos los planes IA, hasta una decisión futura expresa suya. Conservar rutas seguras configuradas en servidor y la credencial fuera del navegador; no cambiar por tier, falta de saldo, timeout o fallback silencioso. «DeepSeek Flash 4.1» es solo un candidato futuro mencionado por el dueño: no se valida su nombre/disponibilidad ni se configura ahora. No fijar una tarifa pública obtenida de internet como costo contractual del taller.

## Capacidades comunes y límites proporcionales

La dirección operativa para construir queda resuelta: base manual y **un mismo núcleo/calidad IA**, con límites proporcionales y extras profesionales explícitos. La tarifa de lanzamiento, sus cuotas y la migración comercial siguen separadas. No mantener la recomendación anterior de reservar la capacidad de trabajar o el comparador al plan IA caro.

| Capacidad o resultado | Base manual | Todos los planes con IA |
|---|---|---|
| Catálogos, clientes, proyectos, Estudio/Mesa y motor | Completo según permiso/autoridad | El mismo manual |
| Edición 2D/3D, aperturas, precio, documentos/PDF, cortes y operación manual | Completo según permiso/autoridad | La misma calidad y recuperación |
| Chat/Trabajo, modelo y política de herramientas | Sin llamadas IA | Mismo núcleo; MiMo 2.6 Pro vigente hasta cambio expreso del dueño |
| Documento compatible → posiciones/borrador canónico | Entrada manual equivalente | Incluido en el núcleo común |
| Cambios por encargo sobre ventanas/selección | Manual completo | Incluido en el núcleo común |
| Comparación de revisiones compatibles y propagación reversible | Comparación/edición manual | Incluido en el núcleo común |
| Preparación de catálogo y pasos encadenados necesarios para terminar tareas comunes | Herramientas manuales disponibles | Mismo núcleo bajo su autoridad real |
| Solo proponer / Con aprobación / Omitir todo | No depende de un agente | Las tres disponibles; ninguna exclusiva del nivel caro |
| Historial, privacidad, fuentes, checkpoints, recibo y deshacer seguro | Historia manual y acceso propio permitido | Mismo estándar en todos los planes IA |
| Créditos incluidos y capacidad de uso | Sin crédito IA incluido | Cuota del contrato; futuras unidades proporcionales, sin degradar la operación individual |
| Extras profesionales futuros de coordinación/operación | Según contrato real | Solo alcances adicionales específicos; no control, precisión o una IA que termina mejor |

**Mínimo de esta versión para todos los planes IA:** (1) documento/listado o plano con cotas explícitas → posiciones y borrador canónico; (2) cambios por encargo sobre ventanas/selección mediante operaciones compartidas; (3) comparar dos revisiones compatibles y propagar diferencias a un borrador o preparar una sucesora; su emisión conserva clic humano. Los tres se implementan en el prompt 05 y se verifican con proveedor real en 07. No basta marcarlos supported=false y cerrar el paquete ni reservar uno al plan IA superior. Desarrollarlos no publica nuevas tarifas.

**Valor adicional sujeto a soporte real:** varias obras a necesidades consolidadas sin duplicación e incidencia a pieza/evidencia. Medir resultado cumplido, pasos humanos evitados, correcciones necesarias y consumo real. No prometer porcentajes de ahorro sin medición ni comprensión universal de planos sin cotas.

Implementar IDs estables y resolución de permisos, núcleo común y límites efectivos. Mantener importes, cuotas, períodos y saldo contratados hasta una migración explícita. La nueva decisión corrige el recorte de capacidades principales por precio, sin convertir 2.000/6.000/12.000 en una tabla proporcional a los precios actuales: no lo es. No quitar derechos o créditos ya concedidos para fabricar la diferencia.

La propuesta es cuota Q = m × U por ventana de servicio, con unidad común y multiplicador de una versión comercial autorizada. El ejemplo de unidades no reemplaza PLAN_ALLOWANCES. Anualidad significa cobro anual y entregas mensuales, no doce cupos gastables al inicio. Los créditos comprados no vencen; la cuota incluida no es otro techo que los inutiliza. El presupuesto del dueño tiene su propia ventana y no aumenta por elegir un plan mayor. Detalles, divergencias y compatibilidad en [04](04-planes-creditos-y-limites.md).

### Gates necesarios ahora

Crear un resolvedor de capacidades del servidor. IDs comunes propuestos: **copilot.chat**, **copilot.task**, **ai.document_extract**, **ai.catalog_draft**, **ai.batch_transform**, **ai.plan_compare**. Son identidades técnicas, no precios ni modelos; no forman una escalera de calidad según precio. **ai.workflow_delegate** y **ai.operational_analysis** pueden identificar extras de coordinación profesional o análisis especializado con alcance adicional real, si se aprueban. No pueden bloquear los pasos necesarios para completar los tres recorridos comunes.

Para habilitar una operación se intersectan: organización/membresía + permiso de dominio + entitlement de capacidad + política delegada + autoridad de datos + disponibilidad de presupuesto/proveedor. Los endpoints y el worker verifican; la UI solo refleja la misma resolución. Una compra de créditos no concede por sí sola una capacidad o rol.

La respuesta distingue derecho IA común, soporte, permiso y disponibilidad momentánea: reason_code, scope, cuota/ventana, saldo por origen, reservado/gastable y presupuesto con su ventana. No reducir todo a ai_available. Leer historial propio y recuperar documentos propios no requiere crédito ni una llamada IA, incluso tras downgrade; las mutaciones manuales continúan por su permiso normal. En base manual, ese historial anterior sigue accesible desde la cuenta o el área de trabajos sin montar un lanzador de IA. Recuperar el estado de una conversación no consulta al modelo; continuar su ejecución puede requerir llamadas nuevas y vuelve a comprobar permisos, capacidades y presupuesto. Un downgrade entre planes IA no retira el núcleo que ambos comparten.

Preservar el débito actual por ruta como política legacy identificada y medir el costo físico aparte. La reserva actual de usage controla presupuesto, no retiene el saldo de la billetera: la fase 06 debe corregir esa distinción y la admisión concurrente, sin activar por inferencia la fórmula de tokens del PRD. Reservas, redondeo, ciclos y posible política futura medida se especifican en 04.

### Contratación y cobros futuros

No crear productos/planes en Flow, Stripe o Paddle; no emitir cobros, tocar suscripciones reales, precios, FX, impuestos, bolsas o renovación. La activación comercial futura necesita tabla aprobada, términos de uso medidos, mapeo de clientes existentes y entorno sandbox. Esa fase es distinta de hacer funcionar gates ahora.

El base no monta widgets de IA ni consulta al proveedor. Un acceso de descubrimiento puede vivir en Empresa/Planes, sin ventanas de upgrade, chips bloqueados o mensajes de “activa IA” dentro del trabajo cotidiano. Tener un plan con IA tampoco obliga a abrirla.

## Benchmark oficial de copilotos

Consultado el **18-10-2026**. Evidencia documental pública; no se usaron cuentas ni se observaron estas funciones en sesión. No demuestra que DEKOPEN ya las tenga.

| Referencia | Qué está documentado | Lección y límite |
|---|---|---|
| [Notion Agent](https://www.notion.com/en-gb/help/notion-agent), secciones Switch chat mode / Chat history / How to work | Ventana flotante o sidebar, contexto de página/selección, historial buscable y permisos del usuario | Referencia directa para popup e independencia del hilo. No se verificaron mover/redimensionar ni recuperación real. |
| [Microsoft Copilot en Excel FAQ](https://support.microsoft.com/en-us/excel/copilot/frequently-asked-questions-about-copilot-in-excel), modos/limitaciones/historial | Separa chat, plan y edición; permite cambios directos, undo/versiones y acceso a conversaciones según disponibilidad | Separar respuesta y trabajo; no copiar fórmulas generadas como autoridad del motor. Plataforma y licencia limitan funciones. |
| [Atlassian Rovo: tools](https://support.atlassian.com/rovo/docs/agent-actions/), permisos y ejecución | Herramientas con efecto concreto, permisos de la persona y confirmación para acciones consecuentes | Herramientas por contrato y auditoría. Sus confirmaciones no obligan a pedir aprobación por cada borrador en DEKOPEN. |
| [Acrobat: citas](https://helpx.adobe.com/knowledge-base/web/user-guide-getting-started/ai-assistant-and-insights/chat-citations.html) y [chats](https://helpx.adobe.com/knowledge-base/web/user-guide-getting-started/ai-assistant-and-insights/find-chats.html) | Citas enlazadas al contenido de origen y conversaciones guardadas/localizables | Cada dato de catálogo o plano debe volver a su evidencia; una cita no certifica exactitud física. Citas: actualización publicada 23-09-2026. |

No se evaluaron rendimiento, precio competitivo, protección de datos por contrato o equivalencia funcional a ingeniería de cerramientos. El popup móvil/redimensionable de DEKOPEN sigue siendo una especificación propia.

## Entrega de implementación

- [Prompt 05: copiloto popup](prompts/05-copiloto.md).
- [Prompt 06: capacidades y planes](prompts/06-planes.md).

Ambos son fases de desarrollo. Las suites, E2E, recorridos visuales, MiMo real y aceptación comercial se ejecutan **al final en la fase común de PRUEBAS**, con su evidencia. Estos documentos dejan criterios concretos y no declaran pruebas realizadas.

