---
type: synthesis
status: active
updated: 2026-10-17
volatility: high
verified_ref: codex/v1-experiencia
sources:
  - docs/ux/2026-10-17/05-ia-catalogos.md
  - docs/redesign/P17-ACEPTACION.md
  - backend/tests/integration/test_assistant_presence.py
  - backend/tests/test_assistant_tool_continuity.py
  - frontend/src/features/assistant/useAssistantPresence.test.tsx
---

# Asistente, trabajos y presencia

**Construcción autorizada · 17-10-2026, rama `codex/v1-experiencia`:** una entrada
contextual, muestra antes de cambios amplios y detalle/fuentes plegados. La nueva
herramienta de cotización calcula con preferencias reales; la UI confirma el
precio y prepara PDF privado desde la conversación, revalidando proyecto,
posiciones e importes. La presentación de PDF/portal usa campos tipados,
preview/apply/state/undo, dueño/MFA, firmas e historial inmutable. Historial y dock
ofrecen los mismos pasos de cotización/presentación. Se conservan presupuesto,
política del servidor y acciones humanas para consecuencias externas.

[Implementación, campaña final y límites](../../ux/2026-10-17/10-implementacion.md).
Dos ejercicios reales con proveedor/worker completaron en unos 15 s sin preguntas
ni cambios/emisiones durante la preparación. No son un nuevo score del harness.
Un tercer ejercicio sobre `P-000016` aplicó el precio y preparó el PDF desde la
muestra; el API confirmó borrador, precio vigente, cero versiones y cero correos.
La revisión recuperada muestra el PDF real mediante un lector local y reserva
el clic explícito de emisión. Los antecedentes comerciales del caso se prepararon
por APIs de dominio; el ejercicio no prueba su creación autónoma por la IA.
No existe una transacción única diseño→precio→PDF ni edición de código arbitrario.
Los apartados P17 siguientes conservan sus fuentes históricas.

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
