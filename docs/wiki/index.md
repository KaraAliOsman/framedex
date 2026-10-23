# DEKOPEN Wiki Index

Content-oriented map of durable project knowledge.

## Route a task

Choose the affected row before reading domain pages. Paths below are relative
to the repository root. Frontend tests are colocated `*.test.ts(x)` plus
`frontend/tests/`; HTTP tests live in `backend/tests/` and its `integration/`
subdirectory. SQL/RLS changes also use `supabase/tests/`. Read the applicable
specification and the linked domain pages, then inspect current code.

| Task | Source entry points | Test entry points | Domain knowledge / specification |
|---|---|---|---|
| Calculation, geometry, physical authority | `engine/src/dekopen_engine/`, `backend/engine_api/` | `engine/tests/`, `backend/tests/` | [Catalog authority](product/catalog-authority.md), [openings](product/physical-openings.md), [glass](product/glass-composition.md); [PRD-01](../PRD/PRD-01.md), [domain v3](../PRD/PRD-20-domain-v3.md) |
| Catalog import and publishing | `backend/catalogs/`, `frontend/src/features/catalogs/` | `backend/tests/test_catalog_*.py`, colocated UI tests | [Catalog authority](product/catalog-authority.md); [PRD-08](../PRD/PRD-08.md), [PRD-20](../PRD/PRD-20.md) |
| Projects, canvas, inspector and 3D | `backend/projects/`, `frontend/src/features/{projects,canvas,glass,inspector}/` | `backend/tests/`, `engine/tests/`, colocated UI tests | [Workspace](product/project-workspace.md), [editor](product/editor-canvas.md), [3D](product/physical-3d.md); [PRD-04](../PRD/PRD-04.md), [PRD-07](../PRD/PRD-07.md), [PRD-12](../PRD/PRD-12.md) |
| Price, quotation, PDF and client agreement | `backend/{pricing,documents,portal}/`, `frontend/src/features/{pricing,quotations,portal}/` | `backend/tests/`, `engine/tests/`, colocated UI tests | [Price](product/price-workspace.md), [quotation](product/quotation-document.md), [agreement](product/customer-proposals.md); [PRD-05](../PRD/PRD-05.md), [PRD-06](../PRD/PRD-06.md), [PRD-11](../PRD/PRD-11.md) |
| AI proposals, operations and jobs | `backend/{ai_gateway,jobs}/`, `engine/src/dekopen_engine/design_operations.py`, `frontend/src/features/{assistant,jobs}/` | `backend/tests/test_ai_*.py`, `engine/tests/`, colocated UI tests | [Assistant](product/assistant-work.md), [provider](product/ai-provider.md), [operation contract](../ai/OPERACIONES.md); [PRD-10](../PRD/PRD-10.md), [PRD-13](../PRD/PRD-13.md) |
| Production, cutting, labels and CNC | `backend/production/`, `backend/documents/`, `frontend/src/features/production/`, `engine/src/dekopen_engine/` | `engine/tests/`, `backend/tests/`, colocated UI tests | [Stations](product/production-stations.md), [cut documents](product/cut-documents.md), [CNC](product/cnc-authority.md) |
| Purchasing and inventory | `backend/{purchasing,inventory}/`, `frontend/src/features/purchasing/` | `backend/tests/`, colocated UI tests | [Purchasing / inventory](product/purchasing-inventory.md); [PRD-16](../PRD/PRD-16.md) |
| Payments, company, roles and security | `backend/{billing,authentication}/`, `frontend/src/features/{billing,settings}/`, `supabase/migrations/` | `backend/tests/`, `supabase/tests/`, colocated UI tests | [Collections](product/collections.md), [company / customers](product/company-customers.md); [PRD-03](../PRD/PRD-03.md), [PRD-02](../PRD/PRD-02.md), [PRD-19](../PRD/PRD-19.md) |
| Dispatch, installation and post-sale | `backend/production/`, `frontend/src/features/field/` | `backend/tests/integration/test_field_work.py`, colocated UI tests | [Field work](product/field-work.md) |
| SaaS subscription, AI credits and usage | `engine/src/dekopen_engine/billing.py`, `backend/billing/`, `backend/ai_gateway/{service,usage}.py` | `backend/tests/integration/test_shot11_lifecycle.py`, `backend/tests/integration/test_ai_provider_operations.py` | [Subscription / credits](product/subscription-credits.md), [latest owner clarification](sources/owner-credits-and-grokbot-2026-10-18.md); [PRD-03](../PRD/PRD-03.md) |
| Analytics, Today and search | `backend/{analytics,search}/`, `frontend/src/features/analytics/`, `frontend/src/app/navigation.ts` | `backend/tests/`, colocated UI tests | [Analytics](product/decision-analytics.md), [Today](product/today-workflow.md) |
| Local stack and repository maintenance | `scripts/review_stack.py`, `scripts/local_gates.py`, `scripts/dev_fixture.py` | Inspect affected script and ownership guards | [Stack skill](../../.agents/skills/testing-framedex/SKILL.md), [workspace](../operations/WORKSPACE.md), [review guide](../GUIA-REVISION.md) |

Brace notation groups directories; pass actual paths to PowerShell commands.
For navigation/auth entry points use `frontend/src/App.tsx`,
`frontend/src/PrivateApplication.tsx` and `backend/config/urls.py`.
The [constitution](../design/CONSTITUCION.md) applies to every product surface.
Generated API/OpenAPI, golden JSON, completed queue prompts and historical
payloads are omitted from broad ripgrep discovery; read them by explicit path
when the task needs them. The dated [v1 acceptance](../redesign/acceptance-2026-10-12.md)
and [current reality](state/current-reality.md) orient integration work.

The owner's [complete functional report · 12-10-2026](../reports/DEKOPEN-FUNCIONALIDAD-2026-10-12.md)
is a dated snapshot with 57 chapters and contract inventories. Read it only
when the task needs a full report; it is excluded from broad search and is
not part of the default bootstrap. Its static inspection and historical
acceptance claims keep separate refs; newer code always requires verification.

## Operating rules

- [Wiki README](README.md) — purpose and authority boundaries.
- [Schema / agent protocol](SCHEMA.md) — ingest, query, lint and session-bootstrap rules.
- [Change log](log.md) — append-only chronology.
- [Workspace maintenance](../operations/WORKSPACE.md) — safe cleanup, persistent local state and evidence retention.

- [Design constitution](../design/CONSTITUCION.md) - mandatory UI/product quality source for v1 work.

## Product direction

- [Owner decisions](decisions/owner-decisions.md) — durable product and engineering decisions extracted from project conversations.
- [Dirección final · 18-10-2026](research/final-direction-2026-10-18.md) — Mesa + Estudio, base manual completa y copiloto opcional en popup; [encargo vigente para Claude](../research/2026-10-18-direccion-final/prompt-maestro.md).
- [Product vision](product/vision.md) — what DEKOPEN is trying to become and what it is explicitly not.
- [Fenestration + UX principles](product/fenestration-and-ux.md) — domain/interaction rules that prevent visually plausible but physically wrong software.
- [Lenguaje de la interfaz](product/interface-language.md) — glosario global, detector de textos y distinción entre documento, dato físico y evidencia histórica.
- [Catalog authority by family](product/catalog-authority.md) — exact rules, historical migration, reviewed import and synthetic authority boundaries.
- [Glass composition](product/glass-composition.md) — structured recipes, sourced safety, exact billing and sealed supplier orders.
- [Physical openings](product/physical-openings.md) — sourced motion, active/passive compositions, handles and immutable legacy transport.
- [Advanced openings](product/advanced-openings.md) — sourced HST/PSK/folding/pivot/vertical-slide recipes, exact cuts/BOM/kits and motor-derived plan.
- [Opening drawings](product/opening-drawings.md) — single DIN grammar, declared travel/view, exact contours and dimension gutters.
- [Representación física 3D](product/physical-3d.md) — poses rígidas, hojas independientes, bicolor sellado y render común con límites explícitos.
- [Hardware classes](product/hardware-classes.md) — exact component expansion, handles/options, sealed picking and declared machining gaps.
- [Color finishes](product/color-finishes.md) — sourced room/street faces, exact surcharges, color-specific stock and sealed rendering.
- [Accessories and services](product/accessories-services.md) — geometry-derived quantities, real extra BOM/cuts and revision-bound commercial sublines.
- [Opening measurements](product/opening-measurements.md) — sourced mounting, exact fabrication, immutable surveys, revision sale and production confirmation.
- [Autoridad térmica](product/thermal-authority.md) — áreas visibles, informes ligados al espécimen, OGUC y anexo sellado.

## Current state

- [Analítica para decidir](product/decision-analytics.md) — cohortes, cierres inmutables de costos, F6 y desvíos con causa exacta.

- [Despacho, terreno y postventa](product/field-work.md) — unidades selladas, cola privada, recepción inmutable, rectificación y decisiones trazables.

- [Empresa y clientes](product/company-customers.md) — fichas auditadas, obras, saldos por moneda, MFA e invitaciones y PDF vivo.

- [Propuesta y acuerdo del cliente](product/customer-proposals.md) — elección sellada, evidencia privada, líneas con IVA y retorno de pago verificado.

- [Centro de trabajo del proyecto](product/project-workspace.md) — elevaciones, lote revisado, orden físico, precio aplicado y fases con autoridad.

- [Autoridad física CNC](product/cnc-authority.md) — origen, sección/montaje, confirmación y evidencia inmutable.

- [Cobranza y documentos de cobro](product/collections.md) — calendario sellado, recibos, enlaces verificados, simulación fiscal y recordatorio humano.

- [Compras e inventario](product/purchasing-inventory.md) — necesidades por OT, recepción útil, OC/REC, retazos físicos y correo humano.

- [Conjuntos y acoples](product/coupled-assemblies.md) — autoridad angular, cotas exactas, planta sincronizada y venta por módulo.

- [Asistente y trabajos](product/assistant-work.md) — presencia privada por contexto, artefactos del motor, decisiones y deshacer auditables.

- [Producción por estación](product/production-stations.md) — cola privada, QR físico, detalle escalable y decisiones de calidad idempotentes.

- [Trabajo de Hoy y flujo](product/today-workflow.md) — cola por consecuencia, decisiones humanas, navegación por rol y búsqueda de entidades.

- [Editor centrado en el lienzo](product/editor-canvas.md) — operaciones, precio indicativo, interacción y límites por tamaño.

- [Design system](product/design-system.md) — constitution tokens, technical primitives, exact presentation and regression guardrails.
- [Human addresses](product/human-addresses.md) — immutable tenant codes, physical label reconciliation, QR and exact presentation.
- [Brand and sender identity](product/brand-identity.md) — profile-section signature, sealed manufacturer identity, onboarding and human-controlled mail recovery.
- [Quotation document](product/quotation-document.md) — sealed preferences, exact commercial projections, revision alternatives and revocable PDF QR.
- [Cotización guiada](product/guided-quotation.md) — PDF privado revisado, emisión canónica, recibo y ciclo de vida del acceso.
- [Corte y etiquetas](product/cut-documents.md) — secuencia física común, papel compacto, declaración de láminas y dirección RT antes/después de Corte.
- [Price workspace](product/price-workspace.md) — exact cascades and frozen replay, private purchase authority, margin approval and requester receipts.

- [Current reality](state/current-reality.md) — volatile map of implementation state; must always carry a verification ref/date.
- [v1 acceptance](../redesign/acceptance-2026-10-12.md) — final scope and limits; [evidence map](../redesign/captures/README.md) separates retained acceptance from historical captures.

## Quality

- [Revisión local de los cambios de Claude · 19-10-2026](quality/review-2026-10-19.md) — REVIEW actualizado sin reset; cuatro PDF rápidos descargados, popup contextual visible y 72 tests dirigidos aprobados.

- [Revisión local de la candidata · 18-10-2026](quality/review-2026-10-18.md) — pantallas abiertas, aperturas y PDF ejercitados; incidencias del checklist/visor y límites de catálogo real.

- [Conexiones de producción](quality/production-connections.md) — dominio/Cloudflare, Railway/Redis, Supabase, Flow, MiMo, SMTP y recuperación de archivos; inventario estático y condiciones verificadas de proveedores.

- [Suscripción SaaS y créditos](product/subscription-credits.md) — MiMo común, cupos/paquetes/presupuesto, divergencia PRD/código y propuesta de límites sin activación comercial.

- [AI provider and authority](product/ai-provider.md) — real transport, tenant settings, budget, physical usage and verified limits.

- [Known risks and audit targets](quality/known-risks.md) — recurring failure modes and areas that require paranoid testing.
- [AI outcome baseline](quality/ai-outcome-baseline.md) — 26 owner requests, rollback harness, real-provider measurement and fixture limits.

## Research

- [DEKOPEN 2 · dirección y prompts · 21-10-2026](../research/2026-10-21-competencia/00-README.md) — auditoría medida, competencia (30+ productos, REA), estrategia, catálogo con valores sugeridos, agente, 9 mockups y 11 fases para GPT; propuestas pendientes del dueño marcadas.
- [Innovación y oportunidades · 18-10-2026](research/innovation-2026-10-18.md) — veinte fuentes, capacidades actuales contrastadas, veinticuatro mejoras y seis apuestas; recomendaciones exploratorias, no ampliación aprobada del lanzamiento.
- [Dirección final y prompts · 18-10-2026](research/final-direction-2026-10-18.md) — corrección posterior del dueño e integración de tres revisiones especializadas; [paquete final](../research/2026-10-18-direccion-final/README.md).
- [Revisión profunda y tres direcciones · 18-10-2026](research/revision-profunda-2026-10-18.md) — quince familias, rúbrica común, evidencia visual/REA y auditoría local; la elección posterior sustituye la propuesta acoplada; [dossier](../research/2026-10-18-revision-profunda/README.md).
- [Competitor capability map](research/competitor-map.md) — sector references and what DEKOPEN should learn from them.
- [Research and Claude handoff · 17-10-2026](../research/2026-10-17-claude/README.md) — dated source audit, public competitor research, proposed UX/AI/catalog/PDF reconstruction and unexecuted staged prompts.

## Sources

- [Planteamiento original recuperado · 19-10-2026](sources/owner-original-recovered-2026-10-19.md) — procedencia de los dos adjuntos iniciales, voz literal del dueño y aclaraciones históricas; compilación completa privada en `.run/`.

- [Adjuntos y criterio de innovación · 18-10-2026](sources/owner-attachments-and-innovation-2026-10-18.md) — documentos e imágenes en el popup como requisito; refinamientos con valor, sin inflar el lanzamiento. [Análisis adicional](../research/2026-10-18-innovacion/06-archivos-y-mejoras-con-sentido.md).

- [Ambición del producto · 19-10-2026](sources/owner-ambition-brief-2026-10-19.md) — versión ordenada por el dueño: un diseño para todo, MiMo, catálogos, documentos, 3D del oficio y nivel Apple; quitar lo inservible.

- [Encargo de innovación · 18-10-2026](sources/owner-innovation-review-2026-10-18.md) — investigar mejoras y adiciones con criterio gerencial y pensamiento abierto.
- [Versión definitiva y conexiones finales · 18-10-2026](sources/owner-launch-boundary-2026-10-18.md) — todo el alcance funcional listo; solo Railway, Supabase y pagos de producción pendientes, con pruebas de lanzamiento después de la aprobación.
- [Créditos, MiMo y personaje Grok Bot · 18-10-2026](sources/owner-credits-and-grokbot-2026-10-18.md) — aclaración posterior de modelo común, límites, referencias profesionales y fidelidad centrada en el personaje animado.

- [Dirección final del dueño · 18-10-2026](sources/owner-final-direction-2026-10-18.md) — conserva Mesa/Estudio, IA popup opcional, base sin IA, delegación y desarrollo primero con pruebas al final.
- [Nueva revisión del dueño · 18-10-2026](sources/owner-revision-profunda-2026-10-18.md) — rechazo de la experiencia actual, Chat/Trabajo, Omitir todo, catálogos reales e investigación previa a elegir diseño.
- [Karpathy — LLM Wiki](sources/karpathy-llm-wiki.md) — canonical pattern used for this knowledge system.
- [Owner context — September 2026](sources/owner-context-2026-09.md) — durable synthesis of owner instructions and project direction from recent conversations.
- [Owner research handoff — October 2026](sources/owner-research-handoff-2026-10.md) — latest research-only scope, simplification, AI worker, editable documents and final-test preference after rollback.

## Pages to add as knowledge accumulates

Expected future domains include:

- architecture/system-map;
- ProductModel and assemblies;
- editor/canvas/commands;
- renderer/2D/3D;
- catalog/provenance/readiness;
- pricing/quotation/revisions;
- manufacturing/inventory/cutting;
- machining/CNC/postprocessors;
- AI runtime/tools/jobs/Orb;
- security/RLS/RBAC;
- testing/golden workflows;
- decision records for major architecture changes.

Do not create empty pages merely to fill this list.
