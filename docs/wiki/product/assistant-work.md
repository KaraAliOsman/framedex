---
type: synthesis
status: active
updated: 2026-10-09
volatility: high
verified_ref: 7d29a6aa6be776e2409ddc209991cd85680b3f27
sources:
  - docs/redesign/P17-ACEPTACION.md
  - backend/tests/integration/test_assistant_presence.py
  - backend/tests/test_assistant_tool_continuity.py
  - frontend/src/features/assistant/useAssistantPresence.test.tsx
---

# Asistente, trabajos y presencia

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
