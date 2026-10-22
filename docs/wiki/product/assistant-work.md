---
type: synthesis
status: active
updated: 2026-10-22
volatility: high
verified_ref: d5500d69bbc843162a9c189805a00d8904d11264
sources:
  - backend/ai_gateway/origins.py
  - backend/ai_gateway/undo_all.py
  - backend/tests/test_ai_request_origins.py
  - frontend/tests/e2e/agent.spec.ts
  - docs/redesign/P17-ACEPTACION.md
  - backend/tests/integration/test_assistant_presence.py
  - backend/tests/test_assistant_tool_continuity.py
  - frontend/src/features/assistant/useAssistantPresence.test.tsx
---

# Asistente, trabajos y presencia

## Solicitud → obra con origen · 22-10-2026 · rama `claude/dk2-p08-agente`

Verificado en la rama (no en main todavía):

- Cada `add_position` que el agente lee de una solicitud cita su frase. El
  servidor la ubica en el pedido o en el texto de un adjunto y exige que ancho,
  alto y cantidad estén escritos ahí (mm, cm, metros, «1.800», números en
  palabras). Sin frase válida la ventana no se crea; si el modelo no cita, el
  servidor busca la cláusula más corta que las contiene. Las herramientas del
  motor aceptan esas mismas lecturas de unidades.
- Nunca se supone una medida: falta una → el agente pregunta. Los supuestos son
  no numéricos (apertura, serie, vidrio, color) y los calcula el servidor; lo
  habitual de la empresa se agrupa aparte.
- `POST /api/v1/ai/jobs/{id}/undo-all/` deshace las operaciones guardadas del
  trabajo (de la más nueva a la más antigua) y elimina la obra borrador que el
  trabajo creó si quedó vacía; una edición humana posterior detiene la cadena.
- UI: Ctrl K ofrece «Pedir a DEKOPEN» (prefija, no envía); el asistente se
  acopla como panel lateral (`VITE_AGENTE_PANEL_LATERAL`); la propuesta muestra
  el mensaje con frases numeradas, supuestos y «Deshacer todo».
- Límite conocido: el trabajador corre con `aal1`; un OWNER con «Omitir todo»
  no puede crear la obra (la base exige `aal2`). Decisión del dueño pendiente.

## Adjuntos compatibles · 18-10-2026 · alcance por implementar

El dueño añade [documentos, imágenes y demás archivos compatibles](../sources/owner-attachments-and-innovation-2026-10-18.md)
como entrada del popup en Chat/Trabajo. El [contrato actualizado](../../research/2026-10-18-direccion-final/03-copiloto-y-planes.md#adjuntos-multimodales--ampliación-explícita-del-dueño)
exige múltiples archivos, preview, persistencia, cobertura real, citas navegables,
permisos y la misma autoridad de motor/catálogo. Archivo adjunto no equivale a
dato validado ni autorización de compartir/publicar. La matriz inicial incluye
PDF, imágenes, planillas, DOCX y texto; es trabajo exigido, no capacidad acreditada.

Inspección estática del 18-10 en `claude/v1-implementacion`, HEAD `6f78e329`
más cambios locales: ingestión ya reconoce PDF/XLSX/CSV/imágenes y ciertas rutas
TXT/EML; preparación multimodal y transporte de imagen existen. Faltan lectores
de la matriz propuesta y no se acredita un flujo global completo. MiMo documenta
visión para 2.6 Pro, pero no se probó la cuenta configurada. Ver [fuentes, paths
y límites](../../research/2026-10-18-innovacion/06-archivos-y-mejoras-con-sentido.md).

La biblioteca entre conversaciones, contradicciones transversales y anotaciones
visuales son refinamientos recomendados, no capacidades verificadas ni módulos
nuevos comprometidos. Pruebas de adjuntos: A15–A17 en la campaña final 07.

## Aclaración de modelo y personaje · 18-10-2026 · por implementar

El dueño confirma MiMo para todos los planes con IA hasta cambio explícito;
la diferencia es consumo/créditos. La [fuente reciente](../sources/owner-credits-and-grokbot-2026-10-18.md)
también precisa que la fidelidad a Grok Bot se centra en el personaje animado,
con estilos de conversación adaptados cuando encajen. El [contrato de figura,
gestos y estados](../../research/2026-10-18-direccion-final/06-grok-bot-personaje-y-movimiento.md)
documenta observación de demo y análisis REA estático parcial; el lanzamiento
REA de runtime fue bloqueado por WAF. No se operó el producto privado.

Construir una primitiva local ligada al job real, con movimiento interrumpible,
pausa oculta, tamaño óptico y reduced motion. La placa facial/brillo/órbita del
Companion actual no satisface por sí sola la referencia. El personaje no llama
al proveedor para animar ni transforma el cotizador en una app de bots.
Ver [créditos y límites](subscription-credits.md) para el contrato de planes.

## Revisión del dueño y evidencia local · 18-10-2026

La [corrección final](../sources/owner-final-direction-2026-10-18.md) exige un
**popup global opcional**, no un panel fijo dentro de cotización/editor ni un
reemplazo del inspector. El usuario trabaja y puede delegar a la IA. Chat/Trabajo,
historial/espacio propio voluntario y conversación continua al navegar se conservan.
El dueño confirma **Omitir todo**, ejecución reversible sin pausas y recibo final.
El [contrato vigente](../../research/2026-10-18-direccion-final/03-copiloto-y-planes.md)
separa modo, autonomía, permisos, capacidades de plan y destino sellado del job.
Los efectos externos conservan clic humano y el motor no pierde validación.
La base manual funciona sin IA, proveedor ni crédito; los planes superiores
aportan delegación, no exclusividad sobre Mesa/Estudio o validación técnica.

En la app local del 18-10, rama `claude/v1-implementacion`, HEAD `6f78e329` más
cambios locales de Claude, `/assistant` sí tiene historial. El panel se reasocia
por contexto; no debe confundirse esa fricción con ausencia de persistencia.
Se observó un job Completado con ventanas pendientes y obra de cero posiciones.
El cierre por postcondiciones, hilo persistente y reanudación son trabajo futuro,
no capacidad acreditada por P17. Ver [evidencia y reproducción](../../research/2026-10-18-revision-profunda/auditoria-dekopen.md).
Las afirmaciones posteriores de P17 conservan su ref histórico.

## Intención posterior del dueño · no implementada

El encargo de investigación del 17-10 pide una IA trabajadora contextual, con
preferencias guardadas, pocas preguntas y una muestra breve de lo realizado.
El [contrato propuesto](../../research/2026-10-17-claude/07-ia-como-trabajador.md)
separa borradores reversibles autorizados de emisión/envío/compromisos humanos,
y excluye herramientas de pagos, código y seguridad. La auditoría del ref
`6f78e329` encuentra varios flujos que preparan enlaces en lugar de ejecutar el
objetivo; cambiar solo su prompt no basta. Grok Bot y Dots son las referencias
confirmadas. Este apartado es intención/propuesta; la evidencia P17 siguiente
conserva su ref histórico y no acredita esa ampliación.

P17 liga el Orb al último trabajo de la persona en su organización y contexto
exacto. La selección transitoria del editor no cambia la conversación.
`GET /ai/presence/` busca por referencias estables; no depende de las últimas
treinta filas del workspace. Las pruebas reales PostgreSQL cubren más de
treinta trabajos intermedios, otro usuario, otro tenant y permiso de instalador.
Los vínculos humanos resuelven entidades dentro de la organización, sin
convertir una referencia de un job en autorización de lectura.

El dock de 400 px muestra artefactos con el renderer real y las cifras del
motor. Queries y restricciones extensas quedan plegadas. La UI distingue
propuesta, aplicación y deshacer; una respuesta del modelo no significa que
el diseño haya cambiado. Los fallos repetidos se agrupan con detalles técnicos.
Trabajos presenta objeto, actor, duración y resultado. Solo el endpoint
privado de IA puede reintentar una conversación con su lifecycle y dueño;
el reintento genérico del worker la rechaza.

El bridge del editor aplica las mismas operaciones tipadas y ofrece deshacer
solo mientras se conservan las identidades de inputs e historial. Una edición
posterior se preserva. Las operaciones del proyecto tienen estado duradero e
idempotente. `undone` exige un `applied` previo y se deduplica; `apply_failed`
no resuelve una aprobación pendiente. El registro de outcome es una petición
separada: si falla, la UI informa que hay que verificar la auditoría.

La continuidad o auditoría tardía no sustituye un job recién enviado ni vuelve
a asociar una conversación abandonada con Nuevo. Las herramientas
normalizan referencias implícitas antes de cachear una simulación; la consulta
para el artefacto reutiliza el resultado verificado sin ampliar el presupuesto.
Se devuelve una copia para que el consumidor no modifique la cache.

La aceptación usa un proveedor de prueba explícito en tenant aislado y MiMo
real en el tenant principal. El flujo real Low-E cambia exactamente las dos
posiciones del segundo piso, conserva la cocina, restaura los diseños y
audita ambas decisiones. El Uw sigue Sin dato cuando falta autoridad térmica
de marco, vidrio y borde; DEMO no certifica rendimiento ni fabricación.
La matriz oficial tiene 48 vistas sin hallazgos nuevos. Véase la
[aceptación](../../redesign/P17-ACEPTACION.md) para evidencia, rúbrica y límites.
