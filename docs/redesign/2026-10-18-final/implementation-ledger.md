# Registro de implementación — dirección final 18-10-2026

Encargo: [prompt maestro](../../research/2026-10-18-direccion-final/prompt-maestro.md) con sus seis contratos y siete prompts. Este registro es el estado real del árbol de trabajo; no sustituye el desarrollo ni acredita pruebas. Las pruebas formales se concentran en la fase 07.

## Punto de partida (18-10-2026)

- Rama `claude/v1-implementacion`, HEAD `6f78e3299d93816991fb7c2fe2a2044458fc5e7a` + cambios locales de la implementación v1 previa: 265 modificados, 87 nuevos, 7 borrados; 185 archivos con diff, +10 419/−4 739.
- Huellas preservadas: `engine/tests/golden_analytics.json` (SHA-256 `f6a97beb…8b3`, cambio ajeno).
- Stack REVIEW del dueño en ejecución (`framedex-review-*`, imágenes construidas ~8 h antes). Se reutilizará en 07; reconstruir no borra la DB.
- Estado previo detallado en [estado-implementacion.md](../../research/2026-10-17-claude/estado-implementacion.md): etapas v1 01–09 desarrolladas y etapa 10 parcial.
  - 18 pruebas de frontend pendientes (`ProjectPages`, editor).
  - Dos goldens del motor ya fallaban en HEAD (I20).

## Contraste con el encargo actualizado

| Área del encargo | Ya existe (aprovechar) | Diferencia o pendiente |
|---|---|---|
| 01 Fundamentos | Constitución enmendada 2026-10 v1 (tema claro, tokens, controles, `Icon`, `Loading`) | Faltaba conciliarla con la decisión final: IA opcional en popup, Mesa/Estudio, catálogo real/DEMO en laboratorio y excepción de animación del personaje. **Hecho en 01.** |
| 02 Dos vistas | `ProjectPages` (cuatro destinos), `PositionCollection` (galería/tabla, lote), `PositionWorkspace` (editor real), `useProjectOperations` | No hay `view=mesa\|estudio`, ni un contenedor de UI de obra, ni Estudio con el mismo editor. El buffer del borrador usa `org:position\|copy\|new`. |
| 03 Editor y catálogo | `AssemblyEditor`, `OpeningPalette` desde capabilities, `FinishSelector`, muestras propias, importación PDF por lotes, plantillas de corte Proline | `AssistantPanel`/`AlternativesPanel` siguen dentro del editor. El catálogo es una lista plana; falta fabricante → serie. DEMO aparece en el recorrido normal. Faltan las fichas reales de Proline/Indalum/Winhouse con estado honesto y el diagnóstico de aperturas. |
| 04 Documentos y operación | Tres composiciones DOC-01, numeración, borrador sin número, editor de documento, cuatro variantes DOC-05, Materiales y corte, «Orden de corte» | Pendientes: base editorial (14 mm, 10–10,5 pt); alcance «Solo esta obra / empresa»; texto conservado al ocultar un bloque; plano técnico; tarjeta del estimador sin plan de corte; detalle de OT en Resumen/Trabajo/Trazabilidad; QR por propósito. |
| 05 Copiloto | `AgentBody` con autonomía draft/propose, `apply` reversible, `document_layout`, contexto de materiales | Hoy es un dock que estrecha la app; debe pasar a popup global. Faltan `ai_threads`, `interaction_mode`, la autonomía «Con aprobación», postcondiciones, adjuntos (DOCX/MD ausentes), los tres recorridos A11–A13 y el personaje fiel a Grok. |
| 06 Planes | Billetera, lotes, ledger, lifecycle, `usage` | Faltan `/capabilities/`, el registro común de capacidades, las reservas duraderas de wallet, la política `legacy_route_v1` sellada y la página de planes «Manual completo / La misma IA, más capacidad». |
| 07 Cierre | — | Campaña completa, MiMo real, stack reconstruido, `acceptance.md`, `production-handoff.md`, PR solo si el dueño la autoriza (instrucción global vigente: sin commit/PR sin pedido explícito). |

## Avance por fase

### 01 · Fundamentos — hecho (verificación en 07)

| Área | Estado | Archivos | Resultado observable |
|---|---|---|---|
| Dirección de producto | Hecho | `docs/PRODUCT.md` | El texto «AI-native / core interface» se sustituye por manual primero, Mesa/Estudio y copiloto opcional con tres autonomías y clic humano. |
| Constitución | Hecho | `docs/design/CONSTITUCION.md` | Enmienda 2026-10-18 y cláusulas modificadas: §3.5 (excepción de ciclos del personaje), §5.1, §5.3, §5.4, §5.11, §6 y §11. |

| Before | After | Why |
|---|---|---|
| §5.4 riel compartido inspector + asistente | Inspector dedicado a la selección; el asistente no desplaza columnas | Decisión del dueño: IA opcional en popup, el trabajo manual primero. |
| §5.11 compañero circular con placa facial | Personaje de ojos negativos fiel a Grok Bot, gestos ligados a jobs reales | Referencia concreta pedida por el dueño (contrato 06). |
| §11 catálogo DEMO por defecto | Catálogo real; DEMO en laboratorio | El recorrido normal no puede depender de datos sintéticos. |
| Resolvedor de capacidades | Hecho (adelantado de 06) | `backend/billing/capabilities.py`, `capabilities_views.py`, `config/urls.py`, migración `20270201000000_credit_holds_capabilities.sql` | `GET /api/v1/capabilities/` es lectura pura (no llama al proveedor ni reconcilia). Distingue derecho IA, soporte, permiso y disponibilidad con su `reason_code`; incluye saldos y presupuesto solo para OWNER, y las versiones `plans-2026-09-prd03`/`allowances-legacy-v1`/`legacy_route_v1`. |
| Shell sin IA | Hecho | `app/AppShell.tsx`, `features/plans/useCapabilities.ts` | El botón «Asistente», la presencia y el popup solo se montan con derecho IA confirmado por el servidor. |
| Preferencias de UI | Hecho | `app/workPreferences.ts` | Vista de obra y geometría del popup con clave versionada `user:org` y memoria si el almacenamiento está bloqueado; sin datos privados. |

### 02 · Dos vistas — hecho (verificación en 07)

| Área | Estado | Archivos | Resultado observable |
|---|---|---|---|
| Ruta-layout de obra | Hecho | `App.tsx` | `/projects/:id`, `positions/new` y `positions/:posId/edit` comparten una sola instancia de shell y de obra. Abrir o cerrar el editor no remonta formularios ni sesión. |
| Estado de UI de obra | Hecho | `ProjectWorkspaceState.tsx` | Prioridad de la vista: query → preferencia → Mesa. `position` validada contra la obra; una inválida se normaliza con `replace`. Sesión de edición separada de la posición activa. Ruta de retorno interna (`workPath`). |
| Selector y Estudio | Hecho | `StudioStrip.tsx`, `studio.css`, `ProjectPages.tsx` | Selector textual «Mesa de obra · Estudio» en la cabecera. Estudio: franja plegable (160/56 px) + el mismo `AssemblyEditor`. Las demás secciones son los mismos paneles de Mesa. |
| Una sesión, tres presentaciones | Hecho | `ProjectPositionEditor.tsx` (`PositionEditorHost`, `editLockCause`) | La sesión se presenta en Estudio, en el editor amplio u oculta en Mesa sin recargar `loadDesign` ni perder el undo. Ctrl+S solo en la sesión visible. |
| Guardas | Hecho | `app/UnsavedChangesGuard.tsx` | Navegar dentro de la misma sesión no pregunta. Cambiar de posición o salir de la obra ofrece Guardar / Descartar / Cancelar; Guardar navega solo tras confirmación del servidor. |
| Borrador local v2 | Hecho | `positionDraft.ts` | Identidad usuario+org+obra+posición o id de creación estable, con baseline y revisión. Solo se lee el formato antiguo con id de posición demostrable. |
| Conflicto 409 | Hecho | `ProjectPositionEditor.tsx` | Conserva la edición en el buffer y ofrece «Cargar la versión guardada». Al restaurar avisa si el borrador se tomó sobre otra versión. |
| Bloqueos de edición | Hecho | `editLockCause` | Causa distinta para revisión emitida, sellada o precio aplicado, cada una con su camino («Ir a Cotización» / «Ir a Precio y margen»). |
| Mesa | Hecho | `PositionCollection.tsx` | Botón textual «Abrir editor» por ficha, «Añadir ventana» y alcance de lote con las elegidas fuera del filtro. La cabecera muestra la revisión y «Borrador · precio aplicado». |

| Before | After | Why |
|---|---|---|
| Editor en otra ruta con su propio shell | Ruta-layout: el mismo árbol presenta Mesa, Estudio y el editor amplio | Cambiar de vista no puede perder trabajo ni recargar el diseño. |
| Galería/tabla presentadas como «vistas» | Galería/tabla son formatos locales de la colección; Mesa/Estudio, el selector de la obra | Contrato 01: no confundir formatos con vistas de producto. |
| Guardia genérica «¿Salir?» en toda navegación | Pregunta solo al salir de la sesión, con Guardar/Descartar/Cancelar | Evita confirmaciones redundantes y no guarda por sorpresa. |

**Pendiente de verificación final (07):** continuidad del borrador y del undo; Atrás/Adelante; selección en lote; conflicto de guardado; cambio de identidad; flujo sin IA; restricciones de revisión; anchos 1440/1280/1024.

### 03 · Editor y cotización — hecho con bloqueo de aceptación real (verificación en 07)

| Área | Estado | Archivos | Resultado observable |
|---|---|---|---|
| Copiloto fuera del inspector | Hecho | `canvas/AssemblyEditor.tsx`; eliminados `AssistantPanel.tsx`, `AlternativesPanel.tsx` y sus pruebas | El inspector solo edita la selección. «Preguntar al asistente» delega al popup global con `position_id` y selección (`copilotBridge.tsx`); sin derecho IA no aparece ninguna affordance. |
| Aperturas compatibles | Hecho | `canvas/OpeningPalette.tsx`, `AssemblyEditor.tsx` | La paleta usa estrictamente `compatible_openings` del servidor; estados cargando/error/sin declarar visibles en lugar de una lista universal. |
| Series de la empresa y laboratorio | Hecho | `ProjectPositionEditor.tsx` | El selector de sistema separa «Series de la empresa» de «Laboratorio · DEMO». |
| Referencias profesionales | Hecho | `catalogs/reference_series.json`, `reference_views.py`, `catalogs/ReferenceSeries.tsx`, `CatalogPage.tsx`, `catalogs.css` | `GET /api/v1/catalogs/references/`: Proline (PRO6004, PROSLIDE-70, PRO5003, PRO7005, PRO-8106, PROSLIDE-84), Indalum Superba 33/44 RPT, Winhouse Diamond 60/Opal 70, Deceuninck Chile y «Vinhaus» (identidad pendiente). Cada ficha declara fuente (SHA-256 del PDF del dueño o URL pública), hechos con página, artículos, faltantes e incidencias; **nunca** cotizable, fabricable ni CNC. «Preparar esta serie en mi catálogo» precarga solo identidad verificada. Estante «Fabricantes · Laboratorio». |
| Importación sin IA | Hecho | `catalogs/CatalogImportsPanel.tsx` | Sin derecho IA la plantilla XLSX/CSV es el camino principal; la lectura de PDF/imagen aparece solo como «Lectura con el asistente». |
| Alcance del diseño de cotización | Hecho | `projects/QuotationDocument.tsx` | «Guardar diseño · solo esta obra» y «Guardar como predeterminado de la empresa» separados. |
| Documento comercial | Hecho | `documents/quotation.py` | Márgenes 14/14/25 mm y pie al ancho útil; cuerpo editorial 10 pt. |

| Before | After | Why |
|---|---|---|
| Segunda conversación dentro del inspector | Un solo copiloto global; el inspector edita | Contrato 01/05: el asistente no duplica superficies ni roba el inspector. |
| Paleta con aperturas universales como reserva | Solo las declaradas por la serie | Una apertura no declarada no puede cotizarse por omisión. |
| Catálogo con 45 series DEMO como única oferta | Fabricantes reales como referencia con fuente; DEMO en laboratorio | Contrato 05: referencias verificables sin fingir autoridad de fabricación ni precios. |

**Bloqueo para aceptación real (no de desarrollo):** ninguna serie real tiene aún autoridad de fabricante, reglas de corte completas ni costos privados de la empresa; el recorrido manual con serie real («puerta 6») queda preparado (preparar serie → completar catálogo → cotizar) pero no puede aceptarse con números reales hasta que el dueño cargue esos datos. Discrepancia registrada en PROSLIDE-70 (profundidad).

### 04 · Operación y documentos — hecho (verificación en 07)

| Área | Estado | Archivos | Resultado observable |
|---|---|---|---|
| DOC-03 PLANO | Hecho | `documents/workshop_layouts.py` (`technical_plan`), `renderers.py`, `artifacts.py`, `serializers.py`, migración `20270201000100_document_layout_plano.sql` | Plano técnico por posición: dibujo con cotas, tabla de producto, sistema, medida, cantidad, apertura/mano, perfiles por función, vidrio y herrajes, cajetín de revisión. Se genera desde Compras (`purchasing.doc03Plan`) y el panel de documentos. |
| Taller / OT | Hecho | `production/ProductionPage.tsx`, `production.css` | Pestañas Resumen · Trabajo · Trazabilidad y selector de trabajo (códigos de sección conservados). Sin permiso de escritura se ve el requisito «Falta un plan de corte vigente…»; los bloqueos explican la causa por rol. |
| Capacidades en catálogo | Corregido | `billing/capabilities.py` | Las rutas IA se leen bajo `billing_backend` (antes 409 por permiso en `ai_routes` desde el rol de la petición). |

| Before | After | Why |
|---|---|---|
| DOC-03 solo listado | Listado + plano técnico | Contrato 04: el taller necesita el dibujo acotado con la revisión. |
| OT con botones sin causa | Requisito y causa por rol visibles | Ningún botón muerto ni bloqueo mudo. |

**Hallazgos para 07:** `GET /api/v1/catalogs/systems/` tarda ≈10 s con 45 series (N+1 de `catalog_readiness`, preexistente en HEAD). La base REVIEW tiene historia de migraciones divergente (`20270130000000` presentation_changes, `20270130000001`, `20270131000000` no existen en el repositorio); se documentará en el traspaso a producción.

### 05 · Copiloto global — hecho en código (verificación y llamadas MiMo en 07)

| Área | Estado | Archivos | Resultado observable |
|---|---|---|---|
| Popup no modal único | Hecho | `assistant/CopilotWindow.tsx`, `copilot.css`, `app/AppShell.tsx`; eliminados `AskDekopen.tsx`, `AiPresence.tsx` y su prueba | 420 × 600 inicial, mínimo 340 × 420, limitado al viewport; arrastre por cabecera y redimensión por bordes con captura 1:1; ajuste por teclado (flechas/Mayús+flechas, Enter, Esc); minimizar y cerrar conservan hilo, borrador y trabajo; ampliar/restaurar; hoja completa en móvil con «Volver al trabajo». Sin scrim ni trampa de foco; devuelve el foco al invocador. Retirados los efectos `data-assistant-open` que estrechaban `app-body` y ocultaban el inspector. |
| Chat / Trabajo y tres políticas | Hecho | `copilotPrefs.ts`, `AgentBody.tsx`, `ai_gateway/serializers.py`, `agent.py`, `prompts/agent-v2.md` | `interaction_mode=chat|work` (distinto del `mode=new|resume` del worker). Chat nunca muta; ofrece «Hacer en Trabajo» en el mismo hilo. `propose`/`approve`/`draft` = Solo proponer / Con aprobación / Omitir todo, sellada por turno y en `ai_jobs.autonomy`; cambiar la preferencia solo gobierna tareas nuevas. «Con aprobación» puede abrir la obra borrador vacía de una cotización nueva; sus ventanas esperan la aprobación única (`POST /api/v1/ai/jobs/{id}/approve/`). |
| Hilos e historial | Hecho | migración `20270201000200_ai_threads_attachments.sql`, `ai_gateway/threads.py`, `copilot_views.py` | `ai_threads` privado por org/persona (RLS + `ai_backend`), `thread_id` en `ai_jobs` y `ai_ask_turns`. Migración idempotente: cada trabajo antiguo enlazado a su hilo trazable (`legacy_key job:<id>`) y los turnos de chat agrupados por su identidad exacta. Historial: buscar, abrir, renombrar, archivar/desarchivar, Nueva; línea de tiempo paginada con cursor estable. Leer historial nunca llama al modelo. |
| Adjuntos | Hecho | `ai_gateway/attachments.py`, `Attachments.tsx`, `providers.py`, `service.py` | PDF (texto/escaneado por página), PNG/JPEG/WebP, XLSX/CSV, DOCX (párrafos y tablas), TXT/Markdown; matriz del servidor (`GET /api/v1/ai/attachments/`). Subir, ver y reabrir no consumen IA. Hash SHA-256, cobertura declarada, citas por página/hoja!celda/fila/párrafo/tabla; el original se reabre desde la API (sin URL que caduque). Al enviar se sellan id+hash; el worker revalida propiedad y hash. Los valores literales cuentan como evidencia; una imagen no produce medidas. |
| Recibo y postcondiciones | Hecho | `ai_gateway/postconditions.py`, `Receipt.tsx`, `jobs.py` | Completo/Parcial/Propuesta/Bloqueado/Respuesta decidido releyendo objetos guardados (posiciones, cantidades, obra, documento). Objetos con Abrir resultado y causa; verificación y consumo plegados. Se recalcula tras aprobar, rechazar o deshacer. |
| Recorridos A11/A12/A13 | Hecho en código | `agent.py` (`quote_draft`), `quote_flow.py`, prompt | A11: documento adjunto → posiciones (project_ops) → precio con reglas vigentes y PDF «Borrador» con la sesión real de la persona (MFA del dueño); en «Omitir todo» el popup continúa la cadena. A12: cambios por lote existentes (`apply_to_positions`, `batch_ops`) bajo las tres políticas. A13: comparación de dos versiones como artefacto `comparison` con altas/bajas/cambios y origen anterior/nuevo; bajas solo si la nueva versión las declara. |
| Personaje | Hecho | `Companion.tsx`, `companion.css`, `CompanionCatalog.tsx`, tokens `--companion-*` | Cuerpo redondo claro y dos ojos oscuros en píldora vertical (sin placa, brillo ni aro). Reloj local que escribe atributos SVG, clips de 1,3–6,4 s con variantes, pausa fuera de vista/pestaña oculta, reduced motion estático, éxito sin repetición al recargar. Estado del botón «Asistente» = tarea real del hilo (no la ruta, sin polling). Catálogo interno con reloj: `/assistant?poses=1`. |

| Before | After | Why |
|---|---|---|
| Dock lateral que estrechaba la página y plegaba el inspector | Popup no modal movible | El trabajo manual no cede espacio al asistente. |
| Conversación ligada a `surface/refs` | Hilo como identidad; contexto de lectura y destino separados | Navegar no crea otro hilo ni redirige una tarea. |
| Casilla «Hacer los cambios» (2 estados) | Chat/Trabajo + tres políticas selladas | Contrato 03. |
| «Hecho» por recibir texto | Recibo con postcondiciones | No declarar éxito sin objetos verificados. |

**Decisiones técnicas:** el paso de precio/PDF no corre en el worker (exige transacción durable y MFA del dueño), sino en la aprobación con la sesión real. La continuación automática de «Omitir todo» ocurre al abrir el hilo si el popup estuvo cerrado.

### 06 · Planes, créditos y límites — hecho en código (verificación en 07)

| Área | Estado | Archivos | Resultado observable |
|---|---|---|---|
| Resolvedor único | Ampliado | `billing/capabilities.py`, `capabilities_views.py` | `entitled()` única regla para resolvedor, gateway y billetera (Starter sin IA; prueba vigente con derecho). Límites con versión de política, unidad, ventana y fuente; tabla de planes con cupos legado; saldos por origen, reservas (incluye UNCERTAIN), gastable y presupuesto con fechas (solo OWNER). |
| Cuotas | Preparado | `billing/quota_policy.py` | Activa `allowances-legacy-v1` (0/2000/6000/12000; prueba 500 totales). `proportional-v1` (Q = m × U, enteros, desde términos persistidos) preparada e inactiva: ningún valor nuevo, ninguna oferta. |
| Retenciones duraderas | Hecho | `billing/holds.py`, `ai_gateway/service.py`, `handlers.py`, migración `20270201000000` | Admisión en transacción breve independiente con lock consultivo por organización (sin esperar el lock de la propia transacción del agente): gastable = saldo − ACTIVE/UNCERTAIN. Liquidación junto al débito; liberación sin débito (fallo del proveedor, réplica, salida rechazada, rollback de dominio); `UNCERTAIN` ante timeout bloquea repetir la misma operación hasta conciliar; barrido de huérfanas; conciliación por operador. `legacy_route_v1` sellado en `ai_audit_logs.consumption_policy`. |
| Planes | Hecho | `plans/PlansOverview.tsx`, `BillingPage.tsx`, `billing.css` | «Manual completo» y «La misma IA, más capacidad de uso»: mismo núcleo, modelo y control; cupos por plan; uso de IA (cupo, próxima entrega, gastable, reservado, presupuesto, lotes con vencimiento). |
| Plan manual | Verificado en código | `AppShell.tsx`, `AssistantWorkspacePage.tsx` | Sin derecho IA no se montan botón, popup, personaje ni polling; el historial propio se lee sin iniciar tareas. |

**Divergencias comerciales registradas:** cupos legado no proporcionales a sus importes; PRD-03 describe `ceil(costo USD × 200)` y el código debita costo fijo por ruta (`legacy_route_v1`, vigente); grandfathering de `founding_member` no implementado en su totalidad. Ninguna se modifica en esta fase.

### 07 · Campaña de pruebas y entrega — hecha (ver `acceptance.md` y `production-handoff.md`)

Checks: lint, typecheck, backend, frontend (1126), mutaciones (28/28) y build en verde; motor con 2 golden preexistentes en rojo (sin cambios en `engine/src`); `test-db` bloqueado por el stack REVIEW en uso. Recorridos con MiMo real: A01–A03, A05–A07, A09, A11 (PDF bloqueado por condiciones comerciales, decisión humana), A12 y A13 en verde. La campaña encontró y corrigió un defecto **crítico** (seguimiento que escribía en la obra abierta en vez del destino sellado) y nueve altos/medios: postcondiciones de obra vacía y de altas, límites de rondas/consultas para MiMo, continuidad de adjuntos, borrador al minimizar, guardia de sección, columnas de `get_job`, recibo precio+PDF, refresco tras «Omitir todo». Nuevo comando de operador `grant_review_credits` (solo REVIEW, auditado). Imágenes REVIEW reconstruidas desde el árbol final.
