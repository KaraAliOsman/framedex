# Fase 05 - Copiloto global opcional en popup

Implementa esta fase sobre el estado actual de C:/Users/alios/Downloads/framedex, preservando los cambios locales de Claude y el propietario. Este archivo es un prompt ejecutable completo. No rediseñes la estrategia comercial ni implementes cobros. El desarrollo de todas las fases precede a la campaña común de PRUEBAS.

## Resultado requerido y autoridad

DEKOPEN funciona de manera excelente sin IA. El cotizador manual, Estudio y Mesa de obra contienen el trabajo y son dos presentaciones del mismo estado. El copiloto se abre solo porque la persona pulsa Asistente o delega una tarea. Es un popup no modal, movible, redimensionable, minimizable y ampliable. No es una columna fija ni reemplaza el inspector, la cotización o la navegación.

Lee primero AGENTS.md, docs/research/2026-10-18-direccion-final/03-copiloto-y-planes.md y el prompt maestro de este directorio. Usa la dirección elegida por el dueño. La corrección posterior “cotizador excelente, IA opcional” prevalece sobre las frases históricas AI-native/core interface y riel compartido. La wiki ya registra esa corrección y 01 debe conciliar PRODUCT/CONSTITUCION. Conserva esa conciliación; no revivas las frases anteriores para mantener un riel.

## Puntos de entrada reales

- frontend/src/app/AppShell.tsx y frontend/src/features/assistant/AskDekopen.tsx.
- frontend/src/features/assistant/AgentBody.tsx, AssistantWorkspacePage.tsx, AiPresence.tsx, useAssistantPresence.ts, assistantContext.tsx y assistant.css.
- frontend/src/features/canvas/AssemblyEditor.tsx y AssistantPanel.tsx; elimina la duplicación de copiloto dentro del inspector.
- backend/ai_gateway/assist.py, agent.py, context.py, jobs.py, handlers.py, views.py, serializers.py y engine_tools.py.
- backend/projects/project_ops.py y los servicios manuales propietarios de cada mutación.
- backend/ai_gateway/service.py y usage.py para conservar idempotencia, presupuesto y medición.
- supabase/migrations y políticas existentes ai_backend/org/usuario.

Inspecciona el código actual con rg antes de editar. Los nombres y los hechos del informe son evidencia del 18-10-2026, no una autorización para sobreescribir cambios posteriores.

## 1. Una ventana global que deja trabajar

Sustituye el comportamiento del dock por una sola instancia de popup en el shell. Al abrirla no cambies columnas, márgenes o inspector del editor. Retira los efectos data-assistant-open que estrechan app-body y ocultan assembly-side. Elimina la segunda conversación AssistantPanel en el editor; sus acciones explícitas deben abrir el mismo popup con contexto. Las alternativas que tengan operación manual propia siguen disponibles sin IA.

Cabecera: Asistente, selector Chat/Trabajo, acceso a historial, minimizar, ampliar/restaurar y cerrar. Usa tokens del sistema, tipografía legible, color de estado con significado y botones con nombre accesible; no una colección de chips sugeridos que compita con el trabajo.

Escritorio: tamaño inicial 420 × 600 px, mínimo útil 340 × 420, máximos y posición limitados al viewport. Permite arrastre por cabecera y redimensión por bordes. Ofrece controles accesibles de mover/redimensionar sin ratón: entrar al ajuste desde menú, flechas para ajustar, Enter para guardar, Escape para abandonar. Mantén siempre recuperables cabecera y restaurar posición. Corrige geometría al cambiar tamaño, zoom u orientación.

No modal: sin scrim ni focus trap, no deshabilites el contenido manual, no interceptes los atajos del editor cuando el foco esté fuera. Usa semántica de diálogo no modal y devuelve foco al invocador al ocultar cuando siga presente. Respeta composición IME y menús internos antes de tratar Escape.

Minimizar y cerrar conservan hilo, borrador y job; no cancelan. Detener trabajo es otra acción identificada. Ampliar/restaurar conserva la geometría previa y el mismo hilo. Móvil adapta la presentación al viewport y permite regresar al trabajo manual, sin simular controles de arrastre imposibles. Un resultado no roba el foco mientras se escribe.

Nuevo inicio de sesión: cerrado. Durante navegación de la sesión conserva el estado solicitado por la persona. Guarda solo geometría/preferencias no sensibles por usuario, organización y dispositivo; no mensajes, precios o documentos en localStorage.

## 1.1. Personaje de referencia e interacción

Implementa [06 · Grok Bot: personaje y movimiento](../06-grok-bot-personaje-y-movimiento.md) como parte de esta fase. El dueño confirmó que se refiere principalmente al personaje animado, con alta fidelidad en silueta, ojos, poses, ritmo y transiciones. El estilo de conversación toma solo lo compatible con DEKOPEN; no reproduzcas una lista de bots, ordenador remoto, rutinas o voz por aparecer en la referencia.

Revisa Companion.tsx/companion.css y el mapeo existente de jobs. Conserva sus contratos útiles y sustituye la figura actual de placa facial, brillo y aro por la gramática del personaje oficial. Usa una única primitiva vectorial local con tamaño óptico, animación interrumpible, pausa cuando no se ve y reduced motion equivalente. No importes el bundle externo ni añadas llamadas a Grok para animarlo. Los ciclos expresivos pueden durar segundos; el tope breve de transiciones de controles no los aplana a 280 ms.

Conecta gesto a job/subtarea real: reposo, cola, pensamiento, trabajo, espera, revisión, éxito, fallo/cancelación y falta de disponibilidad. Texto y recibo conservan la verdad. Un gesto no acredita progreso, no inicia una llamada, no repite éxito al recargar y no abre popup robando foco. Preparar catálogo interno de estados con reloj controlable para revisar en 07; no es una nueva pantalla del SaaS ni sustituye la integración. Conserva la geometría modeless y el trabajo manual descritos arriba.

## 2. Chat y Trabajo con tres políticas reales

Introduce interaction_mode=chat|work, sin confundirlo con el mode=new|resume que ya usa el lifecycle del worker. Chat responde y prepara propuestas, sin mutar dominio. Trabajo ejecuta un objetivo delegado. Una orden de cambios escrita en Chat ofrece Hacer en Trabajo transfiriendo el contenido y contexto en el mismo hilo; no aplica por sorpresa.

Mantén los valores compatibles de autonomy y añade el tercero:
- propose = Solo proponer. Cero mutaciones del dominio.
- approve = Con aprobación. Preparar el conjunto coherente y aplicar tras una aprobación del resultado.
- draft = Omitir todo. Ejecutar todos los cambios reversibles ya autorizados, encadenar lo necesario, verificar y presentar el recibo al final.

Con aprobación no obliga a confirmar cada consulta, hoja o componente. Omitir todo no pide “¿continúo?” entre pasos rutinarios ni termina con instrucciones para que el usuario haga lo delegado. Las tres políticas pertenecen al trabajo habilitado, no a distintos niveles de seguridad por plan. Sella política efectiva por ejecución; un cambio de preferencia solo gobierna nuevas tareas.

Emisión, envío externo, cobro, compra comprometida, publicación de catálogo y liberación física mantienen la acción humana que exige el dominio. Prepara todo lo revisable antes de esa acción. La IA no obtiene herramientas para cambiar planes, credenciales, roles, pagos o código.

## 3. Hilo continuo y destino inequívoco

Separa thread, contexto de lectura, selección y destino de escritura. Cambiar ruta o elegir otra hoja no crea otro hilo, no borra el borrador y no redirige una tarea en curso. Evita la clave surface/refs de AgentBody como identidad de conversación.

Antes de enviar, muestra obra y posición/selección de lectura y el destino cuando sea distinto. El usuario puede quitar o cambiar alcance mediante controles locales. Enviar el encargo sella IDs estables, versión/fingerprint, adjuntos, política y alcance. Una referencia de otro tenant nunca se acepta aunque venga del cliente o del modelo.

Si el usuario pide trabajar sobre otra obra, resuelve ese destino bajo sus permisos y nómbralo. Navegar por la app después no cambia el destino sellado. Las herramientas trabajan por API y servicios tipados; no necesitan obligar a navegar por cada página. Abrir resultado usa un enlace real, y seguir visualmente una ejecución es opcional.

En edición concurrente, relee y vuelve a simular cuando mantenga la intención delegada. Si el conflicto cambia el significado, conserva la edición humana, completa lo independiente y presenta el conflicto concreto. No pierdas identidad de hojas, no hagas last-write-wins sobre geometría ajena y no inventes dimensiones.

## 3.1. Adjuntar documentos e imágenes desde el popup

Implementa el contrato de [adjuntos multimodales](../03-copiloto-y-planes.md#adjuntos-multimodales--ampliación-explícita-del-dueño). Es alcance de la candidata, común a todos los planes IA: PDF con texto/escaneado, PNG/JPEG/WebP, XLSX/CSV, DOCX y TXT/Markdown. Integra los adaptadores existentes; completa los ausentes. Otros formatos se anuncian solo con adaptador real y tarea declarada, mediante matriz del servidor, sin cambiar modelo/proveedor para fingir soporte.

Compositor con Adjuntar, drag/drop y pegado de imagen; selector/cámara donde exista soporte. Varias fuentes por turno con preview, retirada antes de enviar, estado individual y límites efectivos visibles. Usa miniaturas o filas compactas y detalle ampliable; conserva espacio para el dibujo y el trabajo manual. Subir/ver/reabrir no consume IA por sí solo.

Persiste archivos privados y vínculos a turno/job con IDs, hash, versión, permisos y cobertura. Reabrir conserva adjuntos ya subidos sin nueva llamada; no simules persistencia de una subida incompleta. Revalida acceso al leer y reanudar. Retirar del compositor no borra evidencia de una tarea histórica; aplica la política de conservación existente.

Conserva página/región, hoja/celda o párrafo/tabla hasta la propuesta y el objeto creado. Abrir la cita funciona aunque caduque una URL temporal. Usa texto y visión según el contenido, lotes y checkpoints. Declara páginas, hojas o elementos no procesados; un recorte no puede figurar como lectura completa. No ejecutes macros ni contenido activo.

Ante valores contradictorios, muestra fuentes y autoridad sin escoger por orden de subida; continúa lo independiente. No conviertas una imagen en medidas válidas ni una planilla en reglas de fabricación. Adjuntar no publica ni otorga memoria compartida. El contenido del archivo nunca autoriza herramientas. El costo sigue reserva/recibo existentes; no crees otro cobro por archivo ni cambies cuotas.

La reutilización general entre conversaciones, el comparador transversal de contradicciones y las anotaciones sobre el dibujo son recomendaciones en la nota de innovación, no tres módulos obligatorios nuevos. Sí son obligatorios origen por campo, conflictos del encargo y continuidad de sus adjuntos.

## 4. Persistencia sin perder historia

Añade ai_threads como identidad privada por org/persona, y thread_id a ai_jobs y ai_ask_turns mediante migración compatible. Reutiliza transcripts, artefactos y outcomes existentes. No crees un segundo motor de jobs o una nueva billetera.

El thread conserva título editable, modo/política preferidos, archivado y timestamps. El destino pertenece al turno/tarea, no a una ruta fija del thread. El timeline presenta mensajes de Chat, tareas y recibos con cursor estable y paginación; conserva también errores y cancelaciones.

Migra la historia existente sin reescribir auditoría: cada job anterior queda enlazado de manera trazable a un thread y los grupos antiguos de ai_ask_turns permanecen recuperables como conversaciones anteriores. No fusiones por heurística conversaciones privadas ni elimines fechas o resultados. La migración es idempotente y los vínculos con origen se conservan.

Historial: buscar, abrir, renombrar, archivar/desarchivar y crear Nuevo. Nuevo no elimina el anterior. Cargar historial, reabrir el hilo o recuperar el estado persistido no consulta al modelo. Continuar una ejecución puede requerir llamadas nuevas, siempre bajo autorización, capacidad y presupuesto vigentes; no confundir recuperación de interfaz con reanudación de trabajo. Un downgrade o saldo cero no borra ni oculta historia propia permitida. Un administrador de consumo no recibe por ello acceso automático a conversaciones privadas.

Al cambiar usuario u organización, limpia las cachés y referencias locales correspondientes y cierra el popup. La RLS y backend siguen siendo autoridad; el ID de thread no concede acceso.

## 5. Trabajo verificable y recuperación

Define postcondiciones tipadas del encargo antes de cerrar una ejecución. No uses SUCCEEDED por haber recibido texto del proveedor. Para crear posiciones, comprueba objetos guardados, medidas/aperturas validadas y cantidad esperada; para preparar cotización, comprueba cálculo y borrador/documento solicitado. En Solo proponer el éxito corresponde a una propuesta completa, sin decir Aplicado.

Recibo final con: resultado, objetos reales cambiados, aplicado/pendiente/bloqueado con causa, versión anterior/posterior, consumo medido y acciones Abrir resultado/Deshacer cuando proceda. Los detalles de herramientas y diagnóstico van plegados. No expongas cadena de pensamiento.

Si hay parcialidad, muestra Parcial y el checkpoint para continuar; no “Completado” con ventanas pendientes y obra vacía. Hacer una pregunta solo si falta algo material que no pueda leerse o decidirse dentro del alcance autorizado; agrupa las ambigüedades, continúa lo independiente y no inventes dato físico o comercial.

Reutiliza operación idempotente por paso y ciclo de observe/plan/execute/verify. Reintento consulta primero el estado persistido; una respuesta ya pagada se reutiliza. Fallo, cierre del popup y pérdida de red no duplican tarea, posiciones, llamadas o débitos.

Cancelación es cooperativa; informa lo que sí ocurrió. Conserva el registro físico del proveedor aunque se revierta una propuesta de dominio. Deshacer protege ediciones posteriores y documentos emitidos: si no puede revertir con seguridad, presenta comparación/restauración como nueva revisión.

Revalida rol, membresía y permisos al ejecutar, aplicar, reanudar y antes de cada efecto relevante. MiMo 2.6 Pro es la selección vigente para todos los planes IA hasta una decisión futura expresa del dueño. No cambies por tier o ante un fallo, ni uses fallback silencioso. «DeepSeek Flash 4.1» es solo un candidato futuro mencionado por él: no lo valides ni configures ahora. No cambies tarifas o credenciales desde este trabajo.

## 6. Tres recorridos obligatorios que justifican el copiloto

Estos tres flujos son alcance de desarrollo de esta versión. No basta registrar sus IDs con supported=false, devolver navegación o dejarlos como futuras promesas premium. La disponibilidad de otros extras puede ser honesta y limitada; estos recorridos deben quedar implementados y verificarse en 07. Las condiciones comerciales se resuelven por 06 sin activar ofertas ni asignar tarifas nuevas.

### 6.1 Documento a posiciones y cotización reales

Admite los formatos e interacción de 3.1 para documentos/listados e imágenes con cotas y etiquetas explícitas. Conserva archivo/hash y evidencia de cada campo —página, hoja/celda, párrafo o región de origen—. Usa el pipeline de ingestión existente, procesamiento por lotes y checkpoints; no omitas páginas en silencio ni pidas al dueño dividir manualmente el archivo para esconder un límite del proveedor. Declara cualquier límite de formato/tamaño antes de iniciar y conserva lo procesado.

Resuelve serie, vidrio, acabado y valores habituales desde catálogo revisado y preferencias autorizadas. No obtengas una medida fabricable de píxeles sin escala/cotas ni inventes precios. Agrupa solo los faltantes imprescindibles, continúa lo independiente y distingue candidato extraído de posición validada.

Vincula cliente/obra reales según el encargo; crea las posiciones sin duplicación; ejecuta el motor, BOM y precio cuando estén disponibles los datos; prepara la cotización y el PDF canónico **de borrador**, sin emitir ni consumir número definitivo por sorpresa. El recibo comprueba IDs, cantidad de posiciones válidas, resultados vigentes y borrador accesible. Un artefacto con texto o un enlace a un formulario vacío no satisface el flujo. Reutiliza ingestión, project operations y quotation_draft_preview donde corresponda; corrige el flujo DOC_DRAFT_SYSTEM si todavía solo propone navegación.

### 6.2 Cambios sobre ventanas por encargo

Sobre una posición o selección explícita, permite medidas, aperturas compatibles, vidrio, acabado y cantidad mediante las operaciones del sistema. Sella IDs/versiones/destino. Obtén diferencia por objeto con dibujo real, BOM y efecto económico calculado cuando exista autoridad de precios; si no la hay, describe el cambio técnico sin inventar delta.

En Solo proponer queda sin aplicar; en Con aprobación reúne el lote revisable; en Omitir todo ejecuta lo reversible delegado sin aprobación intermedia. La misma modificación aparece en Mesa y Estudio. Navegar no redirige el cambio y deshacer conserva cambios manuales posteriores mediante el control de versión existente.

### 6.3 Comparar revisiones y propagar diferencias

Recibe dos versiones de un listado/plano compatible del alcance anterior. Empareja ventanas por identificadores/etiquetas explícitos y permite resolver correspondencias ambiguas sin inventarlas. Presenta altas, bajas y cambios de medidas, cantidad, apertura o material; cada diferencia vuelve a evidencia anterior y nueva. Ausencia de dato no significa orden de borrar.

Aplica las diferencias seleccionadas/delegadas a un borrador editable o prepara una revisión sucesora usando el contrato existente. La IA no modifica emitidos ni crea una sucesora con efectos externos sin el clic requerido. Recalcula con el motor y conserva vínculo origen, before/after, actor y reversión segura. Una coincidencia visual probabilística no autoriza reemplazar la identidad de una ventana.

Deja fuera de esta promesa la comprensión universal de planos sin cotas, pronósticos sin oráculo y compatibilidad de máquinas no homologadas. Para los formatos admitidos el flujo debe terminar con resultados reales; un límite externo concreto bloquea su aceptación, no se convierte en una función entregada.

## 7. Relación con capacidades

El prompt 06 establece el resolvedor común de capacidades y límites, siguiendo [04: planes, créditos y límites](../04-planes-creditos-y-limites.md). Prepara el consumidor para esa única autoridad; no introduzcas un catálogo comercial propio en el popup. La propuesta operativa es el mismo núcleo/calidad MiMo y control en todos los planes IA, diferenciados por uso proporcional y posibles extras profesionales explícitos. No es una oferta nueva ni una cita literal de que todas las funciones sean idénticas. Los tres recorridos de esta fase, Chat/Trabajo y las tres autonomías pertenecen al núcleo común; ningún tier recibe una IA deliberadamente inferior o que no termina. La coordinación necesaria para esos recorridos no se convierte en un extra.

Iniciar trabajo nuevo requiere rol, derecho IA común o extra legítimo, soporte y saldo/presupuesto/proveedor disponibles. Saldo cero o proveedor ausente no ocultan el historial ni los resultados propios permitidos: deshabilitan la acción nueva con su causa. Ninguna capacidad, crédito o multiplicador se otorga solo porque el usuario escribió una instrucción. Una cuota mayor amplía uso; no cambia modelo, verificación, privacidad, autonomía o destino de la tarea.

Hasta integrar el contrato común, conserva los gates existentes del servidor y su comportamiento; no inventes una oferta ni habilites IA en Starter para mostrar la ventana. Tras la integración, el plan base no monta popup, presencia ni polling de IA. Abrir una ventana o cambiar ruta nunca dispara llamada pagada.

## Contratos y cierre de desarrollo

Las migraciones preservan org_id + RLS y los roles backend existentes. Si cambia API, genera OpenAPI y cliente orval; no edites frontend/src/api/generated a mano. Usa los mismos servicios de motor y dominio que la UI manual. No cambies fórmulas, goldens, precios congelados o cobros.

No ejecutes ahora suites, E2E, auditoría de navegador, llamadas MiMo ni pagos. La campaña común de PRUEBAS se realiza al final de todas las fases. Implementa el código, los contratos y las migraciones y deja los escenarios siguientes preparados para esa campaña, sin afirmar aceptación realizada.

Escenarios que debe cubrir PRUEBAS: popup y ambos layouts sin cambios de estado; abrir/mover/redimensionar/minimizar/ampliar/cerrar sin perder foco o borrador; navegación y selección sin perder thread o redirigir destino; historia más larga que una página y recuperación de legado; las tres políticas con idéntico permiso; tarea reversible completa; postcondición incompleta; concurrencia y deshacer seguro; cancelación y reintento sin duplicación; otro usuario/tenant; revocación de rol; saldo cero; proveedor ausente; cero llamadas de IA al usar el manual.

Entrega al terminar: archivos cambiados, contratos/migraciones introducidos, decisiones técnicas, compatibilidad conservada y escenarios pendientes de la campaña común. Continúa con el siguiente prompt de desarrollo; no detengas toda la implementación para pedir aprobación rutinaria.

