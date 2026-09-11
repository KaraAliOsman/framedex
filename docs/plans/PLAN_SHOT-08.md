# PLAN_SHOT-08 — cierre local verificado; integración no iniciada

## Owner merge review — commercial INSERT guard correction (2026-09-11)

The Owner rejected PR #21 at `0caefc755d26c9f8e1a120590495ed633cfdfabe` for one material defect: `guard_commercial_write()` returned early for any NULL actor, allowing privileged nonzero commercial INSERTs without the UPDATE-only pricing audit triggers. This finding supersedes the previous zero-known-blockers audit for that HEAD. Constitution Rule 21 and PLAN_SHOTS GNG-07-AUDIT govern the correction; no PD or pricing design was reopened.

The only functional change removes `OR auth.uid() IS NULL` in the new SHOT-08 migration. The explicit exception remains solely `pricing_backend`. Maintenance sessions may still insert zero-valued drafts; NULL-actor postgres/service_role and authenticated OWNER/ESTIMATOR cannot directly INSERT any of the four project totals or three position cost/price/discount fields with nonzero values. RLS, grants, pricing_backend architecture and historical migrations are unchanged.

Real PostgreSQL evidence:
- SHOT-08 pgTAP: 38/38 PASS, including zero project/position INSERTs and rejection of all seven nonzero fields for postgres and service_role (`42501`, `pricing_service_required`).
- SHOT-08 pricing integration: 17 passed. The four-role regression checks all seven fields and confirms rejected rows are absent; zero drafts survive. Existing five-mode, tenant/RBAC, approval and stale-input tests remain green.
- Authorized pricing_backend application is witnessed by a second BEFORE trigger on projects and project_positions: matching old/new/actor/reason audit evidence must already exist. A forced failure at operation finalization rolls back prices, state and audit rows; removing that test-only failure permits the operation and its three audit records.
- PostgreSQL 16 clean installation and populated migration upgrade/rollback: PASS. Focused logs: `scratch/shot08-owner-fix-focused.log` (pgTAP) and `scratch/shot08-owner-fix-focused-retry.log` (integration/upgrade). The initial integration run found a test-setup role issue while installing the witness trigger; test setup was corrected before the final gate.

One execution of `python scripts/check_dod.py all` after the focused gates: EXIT 0, official Python 3.12.10 and operational Docker 29.7.2 linux. Engine 216 pass + 5 canonical xfails; Backend 153 pass; Vitest 66 pass; real Playwright 6 pass; pgTAP 251/251; PostgreSQL 16 upgrade/rollback PASS; lint/types/OpenAPI/build PASS; Core mutations 20/20. Full local log: `scratch/shot08-owner-fix-all.log`.

Golden remains byte-identical: calculation hash `sha256:562cdc97337a690f09db12590ee8a99b420ebc6b7dbf9c40a4d4755132d24f21`; complete-file SHA-256 `c21c88d66e7ee2e0049ff01f4007cdd168383595d5b2f0f001fccf743ac5bff6`. H6 unchanged; G1–G7 pass, G8/G9/G11/G12 remain SHOT-06B xfail, G10 remains SHOT-24 xfail. No executable edits after the successful full gate.

The sole Owner blocker is corrected locally. Publication remains on `codex/shot-08` / PR #21 for a second Owner merge review after the new HEAD receives all four required CI successes. NO MERGE, no roadmap closure, no SHOT-09.

## Estado vigente — 2026-09-10

Las resoluciones owner finales sustituyen los residuos PD-08-04/05. RULE 0 = ZERO KNOWN MATERIAL CONTRADICTIONS. RULE 20 = ZERO MATERIAL GAPS al iniciar implementación. No se reabre ninguna PD cerrada. Reauditoría realizada sobre la base 14e535a42b9356d90865a72408377a45895cb70b y las autoridades JIT ya referidas abajo.

| PD | Estado vigente |
|---|---|
| PD-08-01 | RESOLVED_BY_OWNER |
| PD-08-02 | RESOLVED_BY_OWNER |
| PD-08-03 | RESOLVED_BY_EXISTING_AUTHORITY |
| PD-08-04 | RESOLVED_BY_OWNER |
| PD-08-05 | RESOLVED_BY_OWNER |
| PD-08-06 | RESOLVED_BY_OWNER |
| PD-08-07 | RESOLVED_BY_EXISTING_AUTHORITY |
| PD-08-08 | RESOLVED_BY_OWNER |
| PD-08-09 | RESOLVED_BY_OWNER |
| PD-08-10 | RESOLVED_BY_OWNER |
| PD-08-11 | RESOLVED_BY_OWNER |
| PD-08-12 | RESOLVED_BY_OWNER |
| PD-08-13 | RESOLVED_BY_EXISTING_AUTHORITY |

10 OWNER + 3 EXISTING_AUTHORITY + 0 PENDING = 13. FASE 2 cerrada localmente por evidencia del Gauntlet. Integración no iniciada; NO PUSH / PR / MERGE. H6, Golden y migraciones históricas intactos. SHOT-09 no iniciado.

## Cierre local final — 2026-09-11

Ejecución real bajo Python 3.12.10 oficial, Docker 29.7.2 linux, Supabase CLI 2.116.0. Comando `python scripts/check_dod.py all`; evidencia local completa `scratch/shot08-all-final.log`. Veredicto literal:

```text
[PASS] SHOT-08 checker target 'all' completed with exit code 0
```

| Gate final | Evidencia |
|---|---|
| Guards, lint, formato, tipos | PASS; 0 warnings de lint/build; mypy 34 archivos |
| OpenAPI y TypeScript generado | Reproducibles |
| Engine | 216 pass + 5 xfail canónicos |
| Backend | 148 pass, incluidos 41 tests de integración real (12 comerciales) |
| Vitest | 66 pass, 10 archivos |
| Playwright real | 6 pass en 26,4 s; Auth/MFA, S09, creación de borrador, precio aplicado y recargado, regresión canvas/inspector Light/Dark |
| pgTAP | 233/233; 7 archivos |
| Lint DB | No schema errors found; results=[] |
| PostgreSQL 16 | Instalación limpia, upgrades poblados SHOT-06/07/08 y rollback ante rechazo PASS |
| Build | PASS, sin warning de chunks; principal 490,91 kB; pricing diferido 17,69 kB |
| Canvas | 105,7 / 82,7 / 101,3 / 88,4 / 85,5 ms |
| Golden | Byte-identical, `--check` PASS |
| Mutaciones Core | 20/20 abatidas |

Cinco modos: oráculos independientes en `engine/tests/test_commercial_pricing.py` y aplicación contra BOM/DB real en `backend/tests/integration/test_shot08_pricing.py`. Modo 1/4 fixture CLP500 neto/95 impuesto; Modos 2/3/5 fixture CLP2000/380. Gates adicionales: residuos/ties/permutaciones/pisos de no pérdida, cantidad/descuento antes de redondeo, impuesto agregado, vidrio diferencial y foil separados, FX antes del diferencial, matriz sin fallback.

RBAC: OWNER administra/aprueba; ESTIMATOR sólo derivados y gobernanza permitida, sin lectura de columnas/listas/auditorías de costo; manager lee costos sin editarlos; installer sin costo. Tenant ajeno rechazado; `pricing_backend` NOLOGIN/NOBYPASSRLS, sin membresía del rol público. Auditoría previa por trigger, actor/motivo/old/new, rechazo de edición/borrado directo y rollback comercial/XLSX comprobados. La guarda de escritura comercial usa SECURITY DEFINER con search_path vacío para consultar identidad, conservando RLS del cálculo.

Migración añadida: `supabase/migrations/20260910000000_shot_08_pricing.sql`. Histórico SQL sin diff. Actualización de inventarios de tablas/rutas y gates aditivos según delta aprobado; ninguna aserción/gate omitida. El cambio de acceso del test heredado ESTIMATOR aplica PD-08-10, que prohíbe también el costo del tenant propio.

Golden: calculation_hash canónico `sha256:562cdc97337a690f09db12590ee8a99b420ebc6b7dbf9c40a4d4755132d24f21`; SHA-256 del archivo completo `c21c88d66e7ee2e0049ff01f4007cdd168383595d5b2f0f001fccf743ac5bff6`. Son identificadores distintos. G1–G7 pass; G8/G9/G11/G12 → SHOT-06B xfail; G10 → SHOT-24 xfail. H6 intacto.

RULE 0: ZERO KNOWN MATERIAL CONTRADICTIONS. RULE 20: ZERO MATERIAL GAPS. Blockers locales restantes: 0. Alcance técnico WHITE heredado conservado; no habilita nuevas geometrías/colores de shots cerrados. No emite cotizaciones/project_versions fuera del workflow futuro.

Branch `codex/shot-08`; HEAD local `14e535a42b9356d90865a72408377a45895cb70b`. Implementación conservada en working tree sin commit, sin stage, sin push, sin PR y sin merge. `git diff --check` EXIT 0. Este cierre es local, no estado CERRADO/PROVEN por CI protegido en el roadmap. Los registros de avance siguientes son históricos y quedan sustituidos por este cierre.

## Inventario final de archivos afectados (53)

- backend/config/settings.py
- backend/config/urls.py
- backend/openapi.yaml
- backend/pricing/__init__.py
- backend/pricing/repository.py
- backend/pricing/serializers.py
- backend/pricing/service.py
- backend/pricing/urls.py
- backend/pricing/views.py
- backend/pricing/xlsx_import.py
- backend/requirements.txt
- backend/tests/integration/test_rls_context_integration.py
- backend/tests/integration/test_shot08_pricing.py
- backend/tests/test_database_contract.py
- backend/tests/test_openapi.py
- backend/tests/test_pricing_contract.py
- docs/plans/PLAN_SHOT-08.md
- engine/src/dekopen_engine/commercial.py
- engine/tests/test_commercial_pricing.py
- frontend/src/App.tsx
- frontend/src/api/apiMutator.ts
- frontend/src/api/generated/dekopen.ts
- frontend/src/api/generated/models/adminResponse.ts
- frontend/src/api/generated/models/adminResponseItemsItem.ts
- frontend/src/api/generated/models/adminWriteRequest.ts
- frontend/src/api/generated/models/adminWriteRequestValues.ts
- frontend/src/api/generated/models/applyRequest.ts
- frontend/src/api/generated/models/currencyEnum.ts
- frontend/src/api/generated/models/decimalSeparatorEnum.ts
- frontend/src/api/generated/models/draftPositionRequest.ts
- frontend/src/api/generated/models/draftProjectRequest.ts
- frontend/src/api/generated/models/draftResponse.ts
- frontend/src/api/generated/models/importRequestRequest.ts
- frontend/src/api/generated/models/index.ts
- frontend/src/api/generated/models/lineResponse.ts
- frontend/src/api/generated/models/priceRequestRequest.ts
- frontend/src/api/generated/models/priceResponse.ts
- frontend/src/api/generated/models/pricingModeEnum.ts
- frontend/src/api/generated/models/segmentEnum.ts
- frontend/src/api/generated/models/stateEnum.ts
- frontend/src/app/AppShell.tsx
- frontend/src/features/pricing/PricingPage.test.tsx
- frontend/src/features/pricing/PricingPage.tsx
- frontend/src/features/pricing/pricing.css
- frontend/src/i18n/es-CL.ts
- frontend/tests/e2e/auth.spec.ts
- frontend/tests/e2e/canvas.spec.ts
- scripts/check_dod.py
- scripts/check_shot08_upgrade.py
- scripts/local_gates.py
- supabase/config.toml
- supabase/migrations/20260910000000_shot_08_pricing.sql
- supabase/tests/database/060_shot_08_pricing.test.sql

## Avance verificable — 2026-09-11 (NO CERRADO)

Branch `codex/shot-08`, base `14e535a42b9356d90865a72408377a45895cb70b`. Sin commit/push/PR/merge.

- Implementación en curso: migración nueva `20260910000000_shot_08_pricing.sql`, engine comercial puro, repositories/API, importador XLSX, S09 y flujo de operaciones separado para OWNER/ESTIMATOR.
- Evidencia progresiva: engine + contratos de importación/API **233 pass, 5 xfail**; diez tests comerciales sobre PostgreSQL 16 real **10 pass**; siete tests React de permisos, StrictMode, tenant, respuesta tardía y revisión/rechazo **7 pass**. Esto no sustituye los gates completos.
- Docker 29.7.2 linux y Supabase CLI 2.116.0 iniciaron correctamente; reset completo con todas las migraciones y seed **EXIT 0**. Tras el reinicio del entorno, Docker quedó detenido: nuevo `check_dod.py test` **EXIT 1** por daemon ausente (`scratch/shot08-test.log`). Se reinició Docker; pendiente repetir.
- `check_dod.py all` pasó guards/lint/tipos/OpenAPI; se detuvo por inventario de tablas anterior a SHOT-08. Se añadieron exactamente las cuatro tablas comerciales al inventario esperado y declaraciones RLS explícitas; se mantiene rechazo de tablas inesperadas y todos los gates existentes.
- Ajuste reversible local: puertos Supabase 25320–25326 en lugar de 54320–54326, porque Windows reserva 54260–54359. Mismos servicios, versiones y verificadores. No se alteraron reservas ni permisos del host. No cambia contratos comerciales ni despliegue productivo.
- Pendiente: completar cobertura API/Auth y navegador comercial real, pgTAP, upgrade/rollback de la nueva migración, revisión final de aislamiento/confidencialidad y Gauntlet `all` EXIT 0. Golden, H6 y migraciones históricas permanecen read-only.

### Evidencia incremental posterior

- Stack Supabase real: engine **216 pass + 5 xfail**, backend **146 pass**, Vitest **66 pass**; Golden `--check` PASS; Core mutations **20/20**. Luego se añadieron pruebas DB de importación y restricciones, pendientes de la siguiente ejecución completa.
- pgTAP **233/233 PASS**; lint DB sin warnings. PostgreSQL 16 independiente: upgrade poblado SHOT-08 y rollback por vigencia inválida **PASS / EXIT 0**, además de upgrades heredados.
- Playwright heredado **5/5 PASS**. El escenario comercial nuevo descubrió una falta real de permiso del trigger al consultar `auth.uid()` después del arranque de Supabase. Corregido con trigger de guarda SECURITY DEFINER/search_path vacío, sin hacer privilegiado el rol calculador. Pendiente confirmar el flujo completo por HTTP y `all` tras esta corrección.
- Dependencias parser fijadas: openpyxl 3.1.5 (MIT, baseline), et-xmlfile 2.0.0 (MIT, transitiva) y defusedxml 0.7.1 (PSFL, defensa XML). Consulta directa OSV `/v1/query`, PyPI y versión exacta el 2026-09-11: sin vulnerabilidades retornadas para las tres. Runtime instalado conjunto 2.157.918 bytes; importación fría medida 309,35 ms; no añade bundle frontend. Parser con límites 5 MB/30 MB expandido/5000 filas/100 columnas y rechazo de fórmulas. No proveedor ni servicio productivo nuevo.

## Resolución final PD-08-04/05 — autoridad literal

[RESOLUCIÓN CANÓNICA FINAL PD-08-04 / PD-08-05 — SHOT-08]

Las dos pendientes residuales quedan RESUELTAS.

No reabras ninguna PD ya cerrada.

## PD-08-04 — RESOLVED_BY_OWNER

### Cuantización comercial y reconciliación determinista

Se aprueba el enfoque recomendado, con este contrato exacto:

### A. Precisión intermedia

Todo cálculo monetario intermedio usa `Decimal` exacto.

NO cuantizar prematuramente:

* costos parciales;
* FX intermedio;
* waste;
* labor;
* installation;
* márgenes;
* precio unitario intermedio;
* descuentos intermedios;
* distribución del Modo 4.

No usar `float`.

### B. Frontera monetaria de posición

La autoridad monetaria comercial de una posición es su **neto total de línea después de `quantity` y descuento**.

NO cuantizar primero un precio unitario y después multiplicarlo por `quantity`.

Secuencia conceptual:

`exact_line_net = exact_unit_price × quantity × discount_effect`

y recién entonces:

`line_net = quantize_currency(exact_line_net)`

La representación de precio unitario puede derivarse para UX/API cuando sea necesaria, pero no sustituye la autoridad del total de línea ni introduce doble redondeo.

### C. Cuantización

Usar siempre `ROUND_HALF_UP`.

Quantum:

* CLP: `Decimal("1")`
* USD: `Decimal("0.01")`

No cambiar las primitives históricas H6 de SHOT-06; siguen siendo su contrato puro independiente.

### D. Total proyecto e impuesto

`project_net = Σ line_net`

El impuesto se calcula sobre el neto agregado:

`exact_tax = project_net × tax_rate`

`project_tax = quantize_currency(exact_tax)`

`project_gross = project_net + project_tax`

No sumar impuestos redondeados independientemente por línea como autoridad del proyecto.

### E. Modo 4 — reconciliación

Primero calcular con precisión completa:

`C = Σ C_i`

`P_exact = C / (1 - target_margin)`

`P_i_exact = P_exact × (C_i / C)`

Luego:

`P_target = quantize_currency(P_exact)`

La suma final de posiciones DEBE cumplir:

`Σ P_i_final == P_target`

Resolver el residuo mediante método de **mayores restos** sobre unidades mínimas de moneda.

Desempate obligatorio y estable:

`position_index ASC`

No usar orden accidental de DB.

### F. Restricción de no pérdida

Ninguna posición final puede quedar:

`P_i_final < C_i_exact`

Para calcular el mínimo comercial permitido de cada posición, elevar su costo exacto a la mínima unidad monetaria suficiente:

* CLP → siguiente peso necesario;
* USD → siguiente centavo necesario.

Es decir, usar un `ceil` al quantum monetario para el piso de no-pérdida, no `ROUND_HALF_UP` sobre el costo.

Si:

`Σ minimum_non_loss_i > P_target`

el Modo 4 debe fallar con error tipado.

PROHIBIDO:

* reducir silenciosamente un costo;
* modificar silenciosamente el target;
* permitir margen negativo;
* crear dinero mediante redondeos ocultos.

La asignación de mayores restos debe respetar primero estos pisos de no pérdida.

### G. Gates PD-08-04

Añadir oráculos independientes para:

* half-unit CLP;
* half-cent USD;
* qty > 1;
* descuento;
* suma exacta de líneas;
* impuesto agregado;
* bruto = neto + impuesto;
* Modo 4 multi-position;
* residuos;
* empate de residuos;
* permutation/determinism;
* `position_index` tie-break;
* costo justo en frontera;
* rounding que intentaría dejar una posición bajo costo;
* target incompatible con mínimos de no pérdida;
* primitivas H6 sin regresión.

---

## PD-08-05 — RESOLVED_BY_OWNER

### Vidrio base incluido en tarifa Modo 2

Se aprueba la referencia persistida de vidrio base por tarifa.

Cada autoridad tarifaria de:

`PRICE_PER_M2_BY_TYPOLOGY`

debe identificar explícitamente el vidrio base incluido en esa tarifa.

La referencia es configuración comercial tenant-scoped administrada por OWNER.

NO usar automáticamente:

`project_positions.glass_spec` default

como supuesto del vidrio incluido.

NO inventar vidrio base.

### Fórmula canónica

Resolver primero ambos costos bajo la misma autoridad comercial:

* misma fecha efectiva;
* misma moneda final;
* misma política de cost-list;
* FX ya resuelto cuando corresponda;
* misma área del vano/vidrio utilizada por este contrato.

Luego:

`differential_unit_cost = selected_glass_unit_cost - base_glass_unit_cost`

`glass_cost_differential = differential_unit_cost × area_m2`

`special_glass_surcharge = glass_cost_differential × Decimal("1.40")`

El multiplicador `1.40` se aplica exactamente una vez.

### Casos

Si:

`selected == base`

o el diferencial es exactamente cero:

`surcharge = 0`

Si:

`differential > 0`

aplicar el surcharge normativo.

Si:

`differential < 0`

FAIL CLOSED con error de configuración.

NO convertirlo en crédito.
NO clamp silencioso a cero.
NO descontar precio.

Si falta:

* referencia de vidrio base;
* costo del vidrio base;
* costo del vidrio seleccionado;
* autoridad de moneda/FX;
* autoridad de lista aplicable;

FAIL CLOSED.

### Foliado

El `+25%` normativo por color/foil se aplica al precio base de carpintería.

NO aplicar el 25% nuevamente al surcharge de vidrio.

NO aplicar `1.40` al componente de foliado.

### Gates PD-08-05

Probar:

* base = selected;
* diferencial positivo;
* diferencial negativo;
* referencia base ausente;
* costo base ausente;
* costo selected ausente;
* misma área;
* misma moneda;
* USD→CLP resuelto antes de comparar;
* ×1.40 exactamente una vez;
* foliado +25% exactamente una vez;
* combinación foil + special glass;
* ausencia/ambigüedad de cost list;
* aislamiento tenant;
* configuración sólo por OWNER;
* reproducibilidad al recargar.

---

## ESTADO ESPERADO DE PD

Actualiza `PLAN_SHOT-08.md`.

La matriz vigente debe terminar en:

* PD-08-01 RESOLVED_BY_OWNER
* PD-08-02 RESOLVED_BY_OWNER
* PD-08-03 RESOLVED_BY_EXISTING_AUTHORITY
* PD-08-04 RESOLVED_BY_OWNER
* PD-08-05 RESOLVED_BY_OWNER
* PD-08-06 RESOLVED_BY_OWNER
* PD-08-07 RESOLVED_BY_EXISTING_AUTHORITY
* PD-08-08 RESOLVED_BY_OWNER
* PD-08-09 RESOLVED_BY_OWNER
* PD-08-10 RESOLVED_BY_OWNER
* PD-08-11 RESOLVED_BY_OWNER
* PD-08-12 RESOLVED_BY_OWNER
* PD-08-13 RESOLVED_BY_EXISTING_AUTHORITY

Conteo esperado:

`10 OWNER + 3 EXISTING_AUTHORITY + 0 PENDING = 13`

No conviertas detalles reversibles de implementación en nuevas PD.

## RULE 0 / RULE 20

Incorpora estas dos resoluciones y ejecuta una última reauditoría material.

Si aparece una CONTRADICCIÓN MATERIAL NUEVA, concreta y no cubierta por las 13 PD:
STOP y repórtala con autoridad exacta.

No vuelvas a pedir decisión por una PD ya resuelta.

Si no aparece ninguna contradicción material nueva:

`RULE 0 = ZERO KNOWN MATERIAL CONTRADICTIONS`

`RULE 20 = ZERO MATERIAL GAPS`

y:

# FASE 2 QUEDA AUTORIZADA

Continúa inmediatamente y de forma autónoma con la implementación production-grade de SHOT-08 según el plan y la autorización anterior.

No te detengas después de actualizar el plan sólo para informar que hay cero blockers.

Continúa con:

1. migraciones nuevas y contratos DB/RLS/audit;
2. engine pricing puro 5 modos;
3. repositories/backend pricing service;
4. API/OpenAPI;
5. S09;
6. XLSX;
7. integración project/project_positions;
8. targeted verification progresiva;
9. Gauntlet canónico final.

Mantén:

* Golden READ-ONLY;
* primitives H6 intactas;
* migraciones históricas intactas;
* Decimal-only;
* Single Writer;
* cero fallbacks falsos;
* cero weakening de gates.

Al cierre local exige todos los gates previamente ordenados.

NO PUSH.
NO PR.
NO MERGE.

Detente únicamente cuando SHOT-08 esté localmente cerrado o aparezca una contradicción material nueva real.


<details><summary>Resoluciones anteriores y antecedentes; estados residuales sustituidos arriba</summary>
# PLAN_SHOT-08 — Resolución owner y auditoría residual

## Estado activo — 2026-09-10

Base local: `main`, HEAD `14e535a42b9356d90865a72408377a45895cb70b`. Se incorpora la resolución owner recibida en esta sesión. Reemplaza las propuestas anteriores sólo en lo que determina expresamente. La orden autoriza FASE 2 cuando no queden blockers materiales y exige detener antes de push/PR/merge funcional. No se inició implementación: quedan **dos pendientes residuales**, PD-08-04 y PD-08-05. No son contradicciones nuevas ni se reabren contratos cerrados.

## Matriz vigente de las PD existentes

| PD | Estado vigente | Resolución / residuo |
|---|---|---|
| PD-08-01 | RESOLVED_BY_OWNER | C=sum(cost_i); P=C/(1-margin); price_i=P*(cost_i/C). El costo es proxy de complejidad/consumo; NO complexity score separado. Conservación exacta del total final requerida; cuantización pendiente sólo en PD-08-04. C=0 queda fuera del dominio de la división, sin resultado inventado. |
| PD-08-02 | RESOLVED_BY_OWNER | Backend resuelve/persiste snapshot tipado: base_currency, quote_currency, observed_rate, observed/effective_date, source, captured_at. USD→CLP observed_rate*1.05. Sin I/O engine ni tasa inventada/fallback ante ausencia; snapshot reproducible y auditable por operación. Una entrada humana explícita trazable es admisible por Constitución R1; no se autoriza proveedor externo nuevo ni arrastre silencioso. |
| PD-08-03 | RESOLVED_BY_EXISTING_AUTHORITY | PRD-05 Modo 1 y autoridades H6/H7 conservadas: BOM, kit único, conversiones exactas, merma 8%, labor, instalación y cost/(1-margin). |
| PD-08-04 | OWNER_DECISION_REQUIRED | Owner exige reconciliación determinista y preservar target salvo cuantización contractual. No fija modo ni momento de cuantización monetaria comercial, ni desempate de residuos. CLP0/USD2 está definido; eso no determina reparto y totales finales. |
| PD-08-05 | OWNER_DECISION_REQUIRED | Owner congela tarifa persistida tenant-scoped, area*rate, +25% y glass_cost_differential*1.40, error por tarifa ausente/ambigua. No identifica vidrio incluido en tarifa ni confirma diferencial monetario explícito introducido por humano en lugar de derivarlo. Subsiste sólo esta referencia del diferencial. |
| PD-08-06 | RESOLVED_BY_OWNER | Matriz tenant-scoped por contexto/typology, width×height, dominio 600–2400 paso 200. Nodo exacto o bilineal Decimal con cuatro vecinos requeridos; celda faltante/out-of-domain falla, sin extrapolación ni cambio de modo. |
| PD-08-07 | RESOLVED_BY_EXISTING_AUTHORITY | Modo 5 y segmentos PRD-05 permanecen; un único descuento explícito sometido al workflow owner de PD-08-09. |
| PD-08-08 | RESOLVED_BY_OWNER | is_active; valid_from<=effective_date; valid_to NULL o >=effective_date; candidata de mayor valid_from. Empate final de autoridades para SKU falla por ambigüedad; ausencia error tipado; no prioridad accidental ni costo cero. La antigua propuesta de selección humana frente a cualquier solape queda sustituida. |
| PD-08-09 | RESOLVED_BY_OWNER | 0–10 ESTIMATOR/OWNER inmediato; >10–20 OWNER aplica, ESTIMATOR solicita PENDING hasta aprobación; >20 sólo OWNER con confirmación humana. Precio<costo siempre bloquea. Se sustituye expresamente la lectura anterior que exigía pending al OWNER en >10–20. |
| PD-08-10 | RESOLVED_BY_OWNER | OWNER administra listas/config/import/approval/audits; MANAGER sólo lectura de costos en su flujo; ESTIMATOR sin raw supplier costs, sí derivados/descuentos autorizados; INSTALLER sin costos ni pricing administrativo. S09 OWNER. RLS/backend/API sin fuga. |
| PD-08-11 | RESOLVED_BY_OWNER | Mandato de fortalecer auditoría de toda mutación material con old/new/actor/reason antes de escritura, misma transacción y rollback completo si falla. Append-only. Conservar old/new exactos exige eliminar pérdida de precisión: delta mecánico propuesto NUMERIC(16,4), preservando rango entero anterior y escala de unit_cost; migración nueva bajo autorización de DB/audit, nunca truncar costos a dos cifras. No se añade política de retención ni borrado de organización. |
| PD-08-12 | RESOLVED_BY_OWNER | Persistencia tipada tenant-scoped de tarifas/matriz, snapshot FX y workflow comercial separado con state/actor/request/approval/reason auditados. NO añadir PENDING_OWNER_APPROVAL a project_status. Integración projects/project_positions autorizada para SHOT-08; no iniciar emisión/SHOT-09. Detalles de tablas/clases se diseñan respetando estas semánticas. |
| PD-08-13 | RESOLVED_BY_EXISTING_AUTHORITY | XLSX con mapping/validación humana, unicidad, Decimal y transacción auditada; no formatos ambiguos convertidos a precios por adivinación ni sobrescritura silenciosa. |

Resumen vigente: **8 resueltas por owner + 3 por autoridad existente + 2 pendientes = 13**. La auditoría anterior y sus propuestas se conservan abajo sólo como historial. Su conteo 6/0/7 y sus defaults no son el estado actual.

## PD-08-04 — [PENDIENTE-DECISIÓN] Cuantización comercial

Fuente ya revisada: Constitución R3 (CLP0/USD2), PRD-05 frontera PD-06-15 y PRD-01 §3.4 (primitivas HALF_UP2/4 explícitamente separadas de emisión), resolución owner §5 (sumatoria final y target).

Falta seleccionar la frontera por unidad/línea/proyecto y algoritmo de residuo. Determinista no significa único: dos algoritmos estables pueden asignar importes diferentes. La nueva resolución no aprueba expresamente ninguno de los defaults anteriores.

**Default recomendado para aprobación:** Decimal intermedio sin cuantización monetaria; HALF_UP al neto de línea después de quantity/descuento; neto proyecto=sum(líneas); impuesto HALF_UP sobre neto agregado y tasa contractual; bruto=neto+impuesto. Modo 4 cuantiza target y asigna unidades mínimas por mayores restos, empate por position_index; ninguna posición bajo costo. Si no existe asignación compatible con costo mínimo y target cuantizado, error tipado en vez de modificar target o permitir pérdida.

**Alternativa:** cuantizar precio unitario antes de multiplicar quantity; cambia totales y requiere reconciliación específica del objetivo global.

**Gate:** medios pesos/centavos, qty>1, suma final idéntica, empate/permutación estable, bloqueo bajo costo tras cuantización, regresión de primitivas H6. No se ejecuta un test con expected inventado para declarar aprobado el default.

## PD-08-05 — [PENDIENTE-DECISIÓN] Referencia del diferencial de vidrio

Fuente ya revisada: PRD-05 Modo 2, PRD-02 project_positions.glass_spec y resolución owner §3. El multiplicador 1.40 y tarifa tenant-scoped están cerrados. Ninguna fuente afirma qué vidrio está incluido en la tarifa; el default de glass_spec en una posición no determina una inclusión comercial.

**Default recomendado para aprobación:** referencia persistida a vidrio base por tarifa, elegida por OWNER; diferencial=costo del vidrio elegido menos costo del base para la misma área, ambos con autoridades comerciales resueltas. Referencia/costo ausente bloquea. Configuración con diferencial negativo no genera crédito/clamp inventado.

**Alternativa:** diferencial total explícito introducido por OWNER y auditado para la operación, sin lookup de vidrio base. Es admisible como dato humano, pero seleccionarla como contrato automático de este flujo sería escoger la alternativa pendiente; la resolución recibida no lo dice expresamente.

**Gate:** diferencial conocido, cero/positivo/negativo, base ausente, misma área/moneda, ×1.40 y foliado +25% aplicados una vez según PRD. No expandir geometría/colores cerrados por este contrato comercial.

## Rule 0 / Rule 20 y evidencia

RULE SAYS — Constitución R20: «PROHIBIDO rellenar vacíos materiales con supuestos de la IA.» La orden recibida condiciona FASE 2 a cero blockers y pide confirmar que no quede gap material.

AGENT INTERPRETS: las dos omisiones anteriores afectan dinero y salida determinista; no puedo confirmar cero sin una elección. No se trata de permisos faltantes para implementar DB, imports o controles ya definidos. Se congela todo lo resuelto y se detiene únicamente por esos dos residuos anteriores.

No cambios funcionales, migraciones, commit, push, PR ni merge. Golden READ-ONLY; primitivas H6 preservadas. No se ejecuta Gauntlet de producto en esta pasada documental. La petición completa se conserva literalmente a continuación como resolución owner, sin convertir las alternativas históricas en autoridad aprobada.

## Resolución owner recibida — texto literal

<details>
<summary>Instrucción canónica recibida el 2026-09-10</summary>

CONTINÚA SHOT-08 DESDE EL ESTADO ACTUAL DEL WORKSPACE.

NO reconstruyas SHOT-01…07.
NO reabras contratos cerrados.
NO empieces SHOT-09.

Autoridad JIT:

1. `AGENTS.md`
2. `docs/CONSTITUTION.md`
3. `docs/PRD/PLAN_SHOTS.md`
4. `docs/PRD/PRD-05.md`
5. `docs/PRD/PRD-02.md`
6. `docs/PRD/SCREENS_SPECIFICATION_S01_S28.md` — S09
7. `docs/plans/PLAN_SHOT-08.md`
8. interfaces reales existentes únicamente cuando sean necesarias

MAIN REMOTO DE REFERENCIA:

`14e535a42b9356d90865a72408377a45895cb70b`

SHOT-01→07, v1.3 y Agent Harness están CLOSED/PROVEN.

SHOT-06 pricing primitives son upstream congelado:

* `price_from_cost_and_margin`
* `gross_margin_pct`

Presérvalas semánticamente.

Golden permanece READ-ONLY:

`sha256:562cdc97337a690f09db12590ee8a99b420ebc6b7dbf9c40a4d4755132d24f21`

## RESOLUCIÓN OWNER — GAPS MATERIALES SHOT-08

Congela estas decisiones en `PLAN_SHOT-08.md` con IDs PD existentes equivalentes. No dupliques PD si el plan ya contiene una que representa la misma decisión.

### 1. RESOLUCIÓN DE COST LIST

Para una fecha efectiva y SKU:

* considerar únicamente listas `is_active=true`;
* `valid_from <= effective_date`;
* `valid_to IS NULL OR effective_date <= valid_to`;
* seleccionar la candidata con `valid_from` más reciente;
* si después de aplicar la precedencia quedan dos autoridades igualmente válidas para el mismo SKU, FAIL CLOSED con error de ambigüedad;
* jamás elegir por orden accidental de DB;
* lista inexistente = error tipado, no costo 0 y no fallback silencioso.

### 2. FX

El engine NO realiza I/O ni HTTP.

El backend resuelve y persiste un FX snapshot tipado con al menos:

* base currency;
* quote currency;
* observed rate;
* observed/effective date;
* source;
* captured_at.

USD→CLP:

`effective_fx_rate = observed_rate * 1.05`

El 5% es autoridad PRD-05.

No inventar tasa ante ausencia/fallo.

El snapshot usado debe quedar reproducible/auditable para la operación comercial correspondiente.

### 3. MODE 2 — PRICE_PER_M2_BY_TYPOLOGY

Las tarifas no serán hardcode authority dentro del engine.

Persistir configuración tenant-scoped tipada.

Fórmula:

`base_price = area_m2 × typology_rate_per_m2`

Aplicar exactamente los recargos PRD-05:

* foil/color: +25% sobre carpintería;
* special glass: `glass_cost_differential × 1.40`.

Ausencia/ambigüedad de tarifa requerida = fail closed.

### 4. MODE 3 — FIXED_PRICE_MATRIX_DIMENSIONAL

Persistir matriz tenant-scoped por contexto comercial/typology y celdas width×height.

Dominio canónico PRD:

* 600–2400 mm
* pasos de 200 mm.

Punto exacto usa celda exacta.

Punto intermedio usa interpolación bilineal Decimal determinista con las cuatro celdas vecinas.

Si falta una celda requerida:
FAIL CLOSED.

Fuera del dominio:
NO extrapolar.

No cambiar automáticamente a otro modo.

### 5. MODE 4 — TARGET_GROSS_MARGIN_PROJECT

Autoridad matemática:

`project_direct_cost = Σ position_direct_cost`

`target_project_price = project_direct_cost / (1 - target_margin)`

Cada posición recibe:

`position_price = target_project_price × (position_direct_cost / project_direct_cost)`

Equivalente a aplicar el mismo factor de margen al costo directo.

Los residuos derivados de rounding deben reconciliarse determinísticamente para que:

`Σ final_position_price == final_project_price`

sin alterar el target comercial más allá de la cuantización contractual.

No inventar complexity score separado en SHOT-08.

El costo directo existente es el proxy canónico de consumo/complejidad para esta fase.

### 6. MODE 5 / DISCOUNT APPROVAL

NO añadir `PENDING_OWNER_APPROVAL` al enum general `project_status`.

La aprobación comercial es un workflow separado.

Reglas:

* 0%–10%: ESTIMATOR u OWNER, inmediata;
* > 10%–20%:

  * OWNER puede aplicar;
  * ESTIMATOR crea solicitud PENDING y no puede emitir/aplicar definitivamente hasta aprobación OWNER;
* > 20%:

  * sólo OWNER;
  * confirmación humana explícita;
* price < direct cost:

  * siempre prohibido;
  * ninguna aprobación puede saltarlo.

Persistir estado/actor/request/approval/reason de forma auditada.

### 7. RBAC COST/PRICING

Matriz canónica:

OWNER:

* read/write cost lists;
* read/write pricing rules/config;
* import;
* approve discounts;
* view audits.

WORKSHOP_MANAGER:

* read raw costs cuando lo requiera su flujo;
* NO modificar pricing comercial ni listas desde S09.

ESTIMATOR:

* NO recibir raw supplier costs;
* puede consumir pricing derivado/autorizado;
* puede descuentos según governance anterior.

INSTALLER:

* sin costos ni pricing administrativo.

S09 administración:
OWNER.

RLS/backend/API deben demostrar esta política sin fuga cross-tenant.

No usar un fallback que exponga costos a ESTIMATOR.

## AUDITORÍA

`price_audit_logs` es PRE-MUTATION.

Toda mutación material de pricing/config/cost/discount debe ejecutar:

1. registrar audit con old/new/actor/reason;
2. aplicar mutación;
3. commit;

dentro de UNA transacción atómica.

Si audit falla:
ROLLBACK completo.

Fortalece `price_audit_logs` como append-only:
UPDATE/DELETE no autorizados.

No debilites RLS.

## AHORA

Primero:

1. Reaudita las PD actuales contra estas resoluciones.
2. Incorpora estas decisiones en `PLAN_SHOT-08.md`.
3. Ejecuta Rule 0 / Rule 20.
4. Confirma que no queda ningún gap MATERIAL.

Si queda una contradicción MATERIAL NUEVA no cubierta arriba:
STOP y reporta únicamente esa contradicción.

Si el resultado es 0 blockers:

FASE 2 QUEDA AUTORIZADA.

Continúa autónomamente con implementación production-grade de SHOT-08.

Orden recomendado:

A. migraciones nuevas / DB contracts / RLS / audit
B. modelos y funciones puras `/engine` para cinco modos
C. repositories/backend pricing service
D. API + OpenAPI
E. S09 frontend
F. XLSX import
G. integración projects/project_positions
H. targeted tests progresivos
I. canonical closure

No edites migraciones históricas.

No uses float.

No metas HTTP/DB/Django en `/engine`.

No regen Golden.

No cambies checker para conseguir verde.

No uses mocks/stubs/fallbacks falsos en production paths.

No sacrifiques calidad para ahorrar tokens.

Antes de considerar SHOT-08 localmente cerrado exige:

* 5 pricing modes verdes;
* discount governance verde;
* negative margin blocked;
* FX tests;
* cost-list temporal/ambiguity tests;
* RLS/RBAC tests;
* audit-before-mutation tests;
* audit rollback tests;
* XLSX import tests;
* backend/API;
* frontend/S09;
* OpenAPI reproducible;
* Golden byte-identical;
* core mutations 20/20;
* G1–G7 regression intacta;
* canonical xfails intactos;
* `python scripts/check_dod.py all` EXIT 0.

Cuando cierre localmente:

NO push.
NO PR.
NO merge.

Reporta:

* PD resolution matrix;
* files changed;
* migrations added;
* five-mode evidence;
* RBAC evidence;
* audit evidence;
* test/gate evidence;
* Golden hash;
* Rule 0 result;
* remaining blockers;
* final local HEAD;
* git status.

DETENTE antes del push funcional.

</details>

## Historial de reauditoría anterior — sustituido por la matriz vigente

<details>
<summary>Auditoría previa, propuestas no aprobadas salvo resolución posterior expresa</summary>

# PLAN_SHOT-08 — Reauditoría FASE 1 de PD-08-01…13

## Estado de esta revisión

Base inspeccionada: `main`, HEAD `14e535a42b9356d90865a72408377a45895cb70b`. El plan ya era un archivo untracked al empezar esta pasada. Orden owner vigente: reauditar las trece PD, resolver por autoridad o autonomía lo que corresponda, no implementar mientras C > 0, no commit y no push.

Resultado: **13 originales = 6 RESOLVED_BY_EXISTING_AUTHORITY + 0 AGENT_DECISION_NON_MATERIAL + 7 OWNER_DECISION_REQUIRED**. Este registro sustituye íntegramente la clasificación anterior de trece pendientes. Una PD mixta recibe C sólo por su residuo material, identificado abajo; sus partes ya normadas se retiran de la solicitud al owner. No se inventan PD adicionales ni se cuenta dos veces el redondeo del Modo 4: lo resuelve exclusivamente PD-08-04.

Los nombres internos de clases/módulos, layout y ergonomía reversibles se deciden por el agente bajo Regla 20. No constituyen ninguna de las trece PD originales completas y no se crea una B artificial para cambiar los totales.

## Autoridades comprobadas JIT

| Ref | Archivo y sección exacta | Autoridad aplicable |
|---|---|---|
| C | [CONSTITUTION.md](../CONSTITUTION.md), reglas 0, 1–4, 9, 12, 14, 20–22 | Materialidad; entrada humana o engine; Decimal; escala CLP/USD; RLS; monolito; inmutabilidad de emisión; autonomía no material; auditoría previa; Golden. |
| S | [PLAN_SHOTS.md](../PRD/PLAN_SHOTS.md), §4 filas SHOT-08/09/10, §5 GNG-07-AUDIT, §6 protocolo | Cinco modos, listas, descuentos, bloqueo bajo costo y auditoría previa inmutable. Documentos y workflow completo corresponden a shots posteriores. |
| P5 | [PRD-05.md](../PRD/PRD-05.md), §1 principios 1–3, frontera PD-06-15, §2 Modos 1–5, §3, §4 | Fórmulas, tarifas, FX 5%, merma 8%, listas, importación y gobernanza. |
| P2 | [PRD-02.md](../PRD/PRD-02.md), §1.4–1.5; §2 DDL bloques 3 y 4; bloque de RLS «Costos y Reglas Comerciales» | Campos, tipos, unicidad, moneda, precios por posición, versiones y estado de proyecto. |
| H6 | [PLAN_SHOT-06.md](PLAN_SHOT-06.md), resolución canónica PD-06-09 «HARDWARE OUTPUT TIPADO» y PD-06-15 «PRICING PURO» | Kit como unidad comercial primaria; no valorar contents otra vez. HALF_UP2/4 sólo en primitivas, no emisión comercial. |
| H7 | [PLAN_SHOT-07.md](PLAN_SHOT-07.md), resolución canónica PD-07-01 «AUTORIDAD COMERCIAL BFD», PD-07-07 «AGRUPACIÓN FÍSICA», PD-07-26 «API / HASH» | SKU técnico separado de comercial, longitud de barra existente, precedencia tenant/global de mapping y errores de ausencia/ambigüedad; derivados sin cambiar Golden. |
| P1 | [PRD-01.md](../PRD/PRD-01.md), §§3.1–3.4 y enmiendas SHOT-06/07 | Área exacta frente a representación pública; kit sin líneas de costo descompuestas; redondeo comercial expresamente reservado a capa posterior. |
| UI | [SCREENS_SPECIFICATION_S01_S28.md](../PRD/SCREENS_SPECIFICATION_S01_S28.md), S09 | Gestión de costos OWNER; ruta actual `/pricing/cost-lists`; composición flexible; auditoría previa. Consultada sólo para la superficie afectada. |
| DB | [20260901000000_initial_schema.sql](../../supabase/migrations/20260901000000_initial_schema.sql), bloques cost lists/pricing/audit, projects, políticas y grants; [20260906000000_shot_07_authorities.sql](../../supabase/migrations/20260906000000_shot_07_authorities.sql), mappings de compra/refuerzo | Evidencia de implementación contractual ya existente. No sobreescribe reglas superiores ni convierte carencia de funcionalidad futura en decisión del owner. |

También se buscaron referencias de FX, ponderación, redondeo, diferencial de vidrio y aprobación en los PRD activos. El HALF_UP de PRD-ANIMATIONS-INTERACTIONS §3.1 pertenece al snapping SHOT-05: no autoriza extenderlo silenciosamente a dinero. Se distinguieron las resoluciones finales H6/H7 de las propuestas históricas que permanecen en esos mismos archivos.

## Clasificación completa

| PD | GAP LITERAL | AUTHORITY FOUND | MATERIALITY | FINAL STATUS | RATIONALE |
|---|---|---|---|---|---|
| PD-08-01 | «ponderando su complejidad y consumo de insumos» no define pesos ni reparto. | P5 §2 Modo 4 fija el objetivo; H6 PD-06-15 sólo primitiva; H7 no implementa precios. | MATERIAL: precio por posición. | OWNER_DECISION_REQUIRED | Falta la función de complejidad/reparto. El redondeo se trata una sola vez en PD-08-04. |
| PD-08-02 | Fuente y fecha de validez del «tipo de cambio observado». | P5 §1.2 fija buffer 5%; C1 admite datos humanos; P2 cost_lists fija moneda, no tasa FX. | MATERIAL: costo convertido. | OWNER_DECISION_REQUIRED | El 5% se aplica sin nueva decisión. No hay autoridad que seleccione tasa humana/proveedor, fecha ni arrastre de tasa anterior. |
| PD-08-03 | Base BOM, merma, unidades comerciales y kit vs componentes. | P5 §2 Modo 1; P2 cost_list_items.unit; H6 PD-06-09; H7 PD-07-01/07; P1 enmiendas de área/BOM. | MATERIAL, ya normada. | RESOLVED_BY_EXISTING_AUTHORITY | Metros y áreas del BOM por su costo unitario, merma normativa, labor e instalación; kit una vez. BAR→m usa longitud de stock autorizada; BFD no sustituye el costo proporcional por compra de barras enteras. No crear precios ni mappings faltantes. La precisión de aplicación comercial pertenece a PD-08-04. |
| PD-08-04 | Momento y unidad de redondeo comercial y reparto de residuo. | C3 fija Decimal y escala monetaria; P5 Modo 1 fija fórmula; H6 PD-06-15/P1 §3.4 limitan HALF_UP a primitiva histórica. | MATERIAL: dinero y totales. | OWNER_DECISION_REQUIRED | Escala no determina redondear por unidad, línea o proyecto. HALF_UP dimensional/puro no congela ese orden. |
| PD-08-05 | Referencia del «Diferencial Costo Vidrio» del Modo 2. | P5 §2 Modo 2 fija cinco tarifas, +25% y ×1.40; P2 project_positions.glass_spec tiene default, sin declararlo vidrio incluido en tarifa. | MATERIAL: recargo monetario. | OWNER_DECISION_REQUIRED | Se retiran tarifas, porcentaje, cobertura y layout de la solicitud. Sólo falta qué vidrio está incluido en la tarifa para calcular el diferencial. Un default de columna no demuestra esa inclusión comercial. |
| PD-08-06 | Matriz, bilineal, fuente de celdas y dominio. | P5 §2 Modo 3; C1–3. | MATERIAL, ya normada. | RESOLVED_BY_EXISTING_AUTHORITY | Grilla 600–2400 paso 200 y bilineal obligatorias. Precios de celdas son datos humanos, no constantes que debe inventar el owner para programar. No extrapolar fuera de dominio ni interpolar sin las celdas necesarias. Representación persistente conjunta: PD-08-12. |
| PD-08-07 | Intervalos de descuento del Modo 5 supuestamente sin valor único. | P5 §2 Modo 5 y §4; P2 project_positions.quantity/discount_pct; C1. | MATERIAL, ya normada. | RESOLVED_BY_EXISTING_AUTHORITY | Un intervalo admite selección explícita de descuento; no obliga a inventar algoritmo que escoja uno. 0%, 8–12%, 18–25% para >50 ventanas; quantity aporta el número de unidades, no count de filas. §4 se aplica al mismo descuento, no a una segunda rebaja acumulada. |
| PD-08-08 | Selección cuando más de una lista activa cubre la fecha y el SKU. | P5 §3.1–3.2; P2 cost_lists/cost_list_items; H7 PD-07-01 selecciona mapping de stock, no vigencia de costos. | MATERIAL: precedencia de costo. | OWNER_DECISION_REQUIRED | valid_from/valid_to, activo y fecha actual están resueltos. Falta la resolución de listas simultáneas; proveedor del mapping puede ser nullable y no desempata revisiones del mismo proveedor. |
| PD-08-09 | Gobernanza y estado de aprobación supuestamente indefinidos. | P5 §4, P2 project_status, C12. | MATERIAL, ya normada en conducta. | RESOLVED_BY_EXISTING_AUTHORITY | Aplicar literalmente ≤10 instantáneo; >10–20 PENDING_OWNER_APPROVAL y alerta, sin excepción implícita para owner; >20 sólo owner con confirmación; precio<costo bloqueado. Una aprobación no autoriza otro importe. La representación persistente ausente queda una sola vez en PD-08-12, sin reabrir los roles/umbrales. |
| PD-08-10 | Visibilidad de costo, acceso manager/estimator y controles RLS. | P5 §1.1 y §4; C4; UI S09. | MATERIAL, ya normada. | RESOLVED_BY_EXISTING_AUTHORITY | OWNER/MANAGER ven costos; ESTIMATOR sólo precios y márgenes autorizados; S09 sólo OWNER. Grants generales no habilitan violar esa confidencialidad. Logs con costos requieren el mismo blindaje. Implementar roles y RLS es cumplimiento; no pedir una segunda matriz comercial. |
| PD-08-11 | Log old/new NUMERIC(14,2) frente a unit_cost NUMERIC(14,4). | C21, S §5 GNG-07-AUDIT fijan previo/inmutable; P2 §2 bloque 3 y DB fijan tipos divergentes. | MATERIAL: exactitud y contrato de auditoría. | OWNER_DECISION_REQUIRED | No se consulta si auditar, cuándo, ni si permitir editar el log. El residuo es reconciliar el contrato persistente para no perder las últimas dos cifras del valor auditado. |
| PD-08-12 | Persistencia de configuración modos 2–5 y aprobación comercial ausente del DDL contractual. | P2 §2 bloques 3/4 proporciona cost_lists, pricing_rules, project_positions y project_versions; P5 §1.3/§2/§4; S §4 fija fronteras 08/09/10. | MATERIAL: schema contractual y workflow durable. | OWNER_DECISION_REQUIRED | No falta decidir nombres de clases/API interna ni reautorizar persistencia existente. Falta un delta contractual para guardar matrices/listas y PENDING_OWNER_APPROVAL sin reutilizar campos con otra semántica ni extender silenciosamente project_status. |
| PD-08-13 | Importación XLSX, parsing, duplicados y auditoría. | P5 §3.3; P2 §2 cost_list_items UNIQUE(cost_list_id,sku), unit_cost>=0 y unit; C1/4/21. | MATERIAL, requisitos ya normados; ergonomía interna autónoma. | RESOLVED_BY_EXISTING_AUTHORITY | Importar valores humanos con mapeo explícito, tipos y unicidad existentes; errores de formato no autorizan adivinar precios. No sobrescritura silenciosa: cualquier sustitución debe ser una edición humana explícita auditada. Parser, preview y transacción son implementación de esos invariantes. |

## Resoluciones A registradas — sin pendientes nuevos

- **03:** respetar fórmula de P5, usar cada kit como unidad comercial (H6), y las longitudes/mappings únicos de H7. No recalcular masas ni modificar corte. Las conversiones dimensionales exactas no requieren decisión comercial; la selección de lista y redondeo ya tienen sus PD residuales. Insumo sin costo no se sustituye por cero. La ausencia de un valor de catálogo necesario es validación de entrada, no una nueva decisión normativa.
- **06:** tabla completa del dominio especificado con valores humanos; bilineal en interior, nodo exacto en nodo; no fallback numérico para matriz incompleta. No pedir al owner inventar las 100 celdas antes de definir el módulo.
- **07:** un único discount_pct de entrada sujeto simultáneamente al segmento y a §4; no inferir descuento por historial ni elegir el extremo de un rango automáticamente. No extender el segmento >50 a una cantidad menor. No añadir motor nuevo de descuentos acumulables.
- **09:** conservar el comportamiento literal, incluso estado pendiente para solicitudes en el rango >10–20 realizadas por owner, hasta aprobación explícita. Sólo un cambio en esa conducta necesitaría nueva autoridad. Precio=costo no es precio<costo: la prohibición de margen negativo no prohíbe por sí sola el margen cero. La primitiva gross_margin_pct sigue sin admitir precio cero.
- **10:** lectura de costos no concede editar S09 ni aplicar descuentos. Los roles no enumerados en §4 no reciben autorización de descuentos por inferencia. La implementación deberá demostrar confidencialidad en API y acceso DB, incluidos logs, sin usar privilegios de servicio para esquivar RLS. No se cambia en esta auditoría ninguna política.
- **13:** el humano mapea columnas/unidades y ve valores decimales antes de aplicarlos. No ejecutar fórmulas Excel ni elegir separador ambiguo por adivinación: pedir corrección/mapeo del archivo es validación operativa, no decisión al owner del producto. Rechazar duplicados conflictivos conforme a la unicidad; una edición expresa de una fila existente usa el contrato normal auditado. Atomicidad, errores por fila en preview, layout y organización del parser se resuelven como ingeniería. No se redefine política comercial de vigencia mediante el importador.

## C residuales: opciones para resolución conjunta

Las opciones/defaults siguientes son PROPUESTAS NO APROBADAS. Cada sección contiene el gap residual, prueba de ausencia, alternativas, impactos, recomendación y gate. La regla ya encontrada no aparece como opción. Las PD no se resuelven por el texto de este plan.

### PD-08-01 — [MARCADOR HISTÓRICO — consultar estado vigente] Reparto del Modo 4

**Gap:** significado calculable de complejidad y su ponderación con consumo. P5 §2 Modo 4 no define coeficiente ni ecuación; H6 limita su fórmula a una primitiva, sin distribución de proyecto. H7 sólo entrega cantidades técnicas.

**Opción 1 — recomendada/default:** para cada posición, costo directo total C_i (incluye quantity) y coeficiente humano positivo k_i, explícito y trazable. Total objetivo P=sum(C_i)/(1-m). Distribuir sólo beneficio B=P-sum(C_i), con w_i=C_i*k_i: P_i=C_i+B*w_i/sum(w_i). Conserva el costo por posición y hace intervenir complejidad y consumo. El owner introduce k_i; no se infiere desde nombre/tipología ni se asigna un valor invisible. Si sum(C_i)=0, el margen global es indefinido y se rechaza este modo; C_i=0 con total positivo tiene peso cero. Redondeo únicamente PD-08-04. Impacto: exige coeficiente comercial visible, pero evita que una posición de bajo peso reciba menos que su costo.

**Opción 2:** margen uniforme por posición, P_i=C_i/(1-m); considerar que toda complejidad ya está recogida en el costo de mano de obra. Impacto: configuración más simple, pero exige resolver explícitamente que «complejidad» no añade ponderador independiente y limita la diferenciación comercial.

**Tests/gates:** oráculo manual multi-posición con costos distintos y k distintos; misma suma objetivo; nunca P_i<C_i; sensibilidad a k; quantity; costo cero; margen fuera de dominio; permutación estable; residuo según PD-08-04. Tests puros + integración con configuración persistente real.

### PD-08-02 — [MARCADOR HISTÓRICO — consultar estado vigente] Autoridad y fecha FX

**Gap:** qué tasa observada se acepta y a qué fecha corresponde. El 5% está fijado en P5 §1.2. Ni cost_lists ni pricing_rules guardan tasa/fecha/fuente FX, y C1 permite dato humano pero no selecciona fuente ni caducidad.

**Opción 1 — recomendada/default para SHOT-08:** registro humano OWNER de CLP por USD observado, positivo, con fuente textual y fecha efectiva explícita; tasa para la fecha comercial seleccionada en PD-08-08, sin arrastre implícito. Si no existe tasa para esa fecha, solicitarla y bloquear conversión. Congelar el registro usado, aplicar ×1.05 una vez. Impacto: operación manual diaria, sin dependencia externa ni precio silenciosamente actualizado; la ausencia es visible.

**Opción 2:** fuente oficial automática de tasa observada, con registro de fecha de publicación y regla aprobada de último día hábil para fines de semana/feriados. Impacto: menor carga humana, añade integración y política de indisponibilidad/caducidad que debe quedar explícita. No se elige un proveedor mediante investigación externa en esta auditoría del contrato.

**Tests/gates:** misma entrada/tasa produce mismo costo; CLP no convierte; USD aplica buffer una vez; tasa nula/cero/negativa/fecha ausente; versión anterior permanece congelada; actor no autorizado rechazado; persistencia de fuente/fecha y auditoría del cambio.

### PD-08-04 — [MARCADOR HISTÓRICO — consultar estado vigente] Redondeo monetario comercial

**Gap:** frontera por unidad/línea/proyecto y residuo. C3 determina Decimal, CLP0 y USD2; el ejemplo P5 no distingue secuencias en casos límite. H6 PD-06-15 y P1 §3.4 dicen expresamente que la salida pura a dos decimales no es emisión CLP. HALF_UP del snapping no aplica a dinero.

**Opción 1 — recomendada/default:** cálculos intermedios Decimal sin cuantizar a moneda, quantity y descuento sobre importe de la línea; HALF_UP al neto final de cada línea, suma de netos para proyecto, impuesto HALF_UP sobre neto agregado y tasa contractual, bruto=neto+impuesto. Mantener la primitiva histórica separada para evitar doble redondeo. En Modo 4, redondear el objetivo total y distribuir unidades mínimas mediante mayores restos, desempate por position_index. Restricción dura: ninguna línea queda bajo su costo exacto. Si el total redondeado no alcanza la suma de costos elevados a unidad monetaria, bloquear en vez de cambiar el objetivo. Al asignar restos se respetan esos mínimos antes de repartir el saldo. Impacto: concilia total y líneas; no confunde unit price mostrado con autoridad de total.

**Opción 2:** HALF_UP al precio unitario, multiplicar por quantity y aplicar descuento/impuesto en las fronteras comerciales definidas de esa política. Impacto: precio unitario impreso multiplicable, pero puede producir un total distinto de la opción 1 y necesita reconciliación adicional para objetivo global.

**Tests/gates:** medios pesos/centavos; quantity>1; repetición y permutación; suma de líneas igual neto; neto+impuesto igual bruto; residuo estable; precio justo bajo costo antes/después de redondear bloqueado; objetivo Modo 4 incompatible con mínimos rechazado; primitivas H6 byte-contractuales sin cambio.

### PD-08-05 — [MARCADOR HISTÓRICO — consultar estado vigente] Vidrio incluido en tarifa Modo 2

**Gap:** respecto a qué costo se mide el diferencial. P5 da ×1.40 pero no identifica vidrio base; P2 glass_spec default '4-12-4 Float Incoloro' representa la especificación de una posición, no afirma qué está incluido en todas las tarifas. Las cinco tarifas y foliado +25% siguen fijos, sin nueva elección.

**Opción 1 — recomendada/default:** cada tarifa identifica un SKU de vidrio base incluido, elegido explícitamente por OWNER; diferencial = costo de vidrio especial de la posición menos costo de ese vidrio base para la misma área. Si falta esa referencia/costo, bloquear el recargo; no tomar el default de posición como equivalencia comercial. Aplicar el ×1.40 normativo. Para un resultado negativo, bloquear configuración del recargo hasta corregir autoridad, sin inventar crédito o clamp silencioso. Impacto: reproducible, requiere sólo la referencia comercial que falta.

**Opción 2:** diferencial total explícito introducido por OWNER para esa posición y conservado como dato humano auditado, sin deducirlo de dos SKU. Impacto: admite excepciones de taller, pero pierde trazabilidad automática entre la tarifa y su vidrio incluido y aumenta edición manual.

**Tests/gates:** base/especial con costos conocidos y área idéntica; diferencial cero/positivo; referencia ausente; diferencia negativa; foliado +25% sobre base sin multiplicarlo otra vez sobre el diferencial; USD resuelto antes de comparar; sin habilitar nuevas geometrías/colores técnicos de SHOT-06/07 por esta capacidad comercial.

### PD-08-08 — [MARCADOR HISTÓRICO — consultar estado vigente] Más de una lista vigente

**Gap:** precedencia de costo entre listas simultáneas y fecha comercial coherente. P5 §3 ya manda activa y vigente a fecha actual; P2 no tiene exclusión de solapes ni prioridad. H7 fija precedencia de mappings físicos, no ordena revisiones de precios ni listas de proveedores.

**Opción 1 — recomendada/default:** resolver identidad comercial y proveedor autorizado; aplicar activo y fecha comercial de la organización, inicialmente America/Santiago para el ámbito CLP actual, extremos de fecha inclusivos y valid_to NULL sin fin. Si hay exactamente una lista aplicable, usarla automáticamente. Si hay varias, exigir selección humana OWNER de lista/proveedor para ese cálculo, persistida como autoridad explícita; si falta, bloquear. Ningún latest/cheapest implícito. Impacto: evita elegir un costo no aprobado, con intervención sólo ante ambigüedad.

**Opción 2:** dentro del proveedor resuelto, seleccionar mayor valid_from no futuro; empate exige selección humana. Impacto: resuelve revisiones frecuentes automáticamente, pero puede elegir un costo distinto de la lista que esperaba el taller. La ambigüedad entre proveedores sigue necesitando elección humana; no se ordena por nombre.

**Tests/gates:** fechas en límite, NULL, inactiva, solape mismo proveedor, empate, dos proveedores, ausencia de mapping/costo, organización cruzada, instante alrededor de medianoche comercial, conservación de lista escogida en snapshot. No reutilizar la precedencia tenant/global de H7 como desempate de costos.

### PD-08-11 — [MARCADOR HISTÓRICO — consultar estado vigente] Precisión del contrato del log

**Gap:** unit_cost permite cuatro decimales y old_value/new_value sólo dos, en P2 y migración contractual. Una mutación en la tercera/cuarta cifra puede persistir como valores idénticos en el log. C21 y GNG-07 fijan auditoría previa inmutable; no dictan una de las dos extensiones de almacenamiento exacto siguientes.

**Opción 1 — recomendada/default:** migración nueva de old_value/new_value a NUMERIC(16,4), conservando los doce dígitos enteros existentes de NUMERIC(14,2) y las cuatro cifras de unit_cost. Impacto: un único par exacto, cambia de forma explícita el tipo contractual y serializer de auditoría; sin pérdida del rango histórico. Mantener representaciones monetarias finales según C3, pues el log guarda valores de campos, no es una emisión CLP.

**Opción 2:** conservar old_value/new_value y añadir payload exacto tipado de valor anterior/nuevo con escala y campo; el payload es autoridad para costos de cuatro decimales. Impacto: compatibilidad de campos antiguos, pero dos representaciones que deben mantenerse coherentes y nuevo contrato de lectura exacta.

En ambas opciones la implementación debe ser previa, transaccional, append-only y con actor verificado; no son alternativas al cumplimiento. La retención/borrado de organizaciones no se abre como nueva funcionalidad de SHOT-08, ni se habilita borrado de logs. No se alteran cascadas históricas silenciosamente en esta auditoría.

**Tests/gates:** cambio sólo en cuarta cifra deja old/new distintos y exactos; rango histórico conservado en upgrade; fallo del insert impide mutación; rollback; UPDATE/DELETE del log rechazado a roles de aplicación; actor no falsificable; aislamiento tenant y confidencialidad por rol en SQL/API.

### PD-08-12 — [MARCADOR HISTÓRICO — consultar estado vigente] Delta persistente comercial mínimo

**Gap:** las tablas contractuales existentes no guardan una matriz de precios comerciales, la configuración específica de Modo 4/5 ni la solicitud/aprobación de descuento. pricing_rules tiene escalares del Modo 1 y un selector. project_status no incluye PENDING_OWNER_APPROVAL. P5 exige esas capacidades, pero no determina el delta persistente. H6/H7 excluyeron expresamente estas escrituras comerciales. El alcance de listas/precios es de SHOT-08; no se vuelve a pedir permiso para él, ni para nombres de módulos.

**Opción 1 — recomendada/default:** mantener projects/project_positions como identidad del borrador y los campos comerciales ya definidos; añadir autoridades comerciales tenant-scoped y versionadas para tarifas/matriz/lista y parámetros necesarios según PD-08-01/02/05. Añadir solicitud comercial de descuento separada, ligada a project_id, position_id cuando aplique, actor, precio/descuento exactos y revisión de entrada; estado pendiente/aprobado/rechazado e invalidación al cambiar el objeto aprobado. PENDING_OWNER_APPROVAL se expone como estado de la solicitud comercial sin añadirlo al enum del ciclo productivo. Guardar referencia de configuración y entradas resueltas para reproducir la cotización; no emitir project_versions ni documentos antes de su workflow autorizado. Impacto: delta aditivo y separación del estado de producción; requiere acordar este contrato durable. Tablas vs composición interna no se presentan como segunda decisión: el builder detallará constraints, columnas y serializers conservando la semántica aprobada.

**Opción 2:** extender project_status con PENDING_OWNER_APPROVAL y guardar versión comercial/configuración estructurada dentro de un nuevo snapshot comercial del proyecto. Impacto: menos separación de entidades, pero altera el workflow contractual compartido con SHOT-10 y requiere reglas explícitas para recuperar el estado anterior y no confundir aprobación de descuento con APPROVED productivo.

La precisión del log pertenece sólo a PD-08-11; el algoritmo/autoridad de cada modo pertenece a su PD correspondiente. Esta PD selecciona integración persistente y significado del estado, no reabre umbrales, roles ni inmutabilidad al emitir. La opción 1 es el default recomendado para evitar adelantar el autómata de SHOT-10.

**Tests/gates:** editar/recargar conserva configuración real; aprobación se liga a valores/revisión y no autoriza otra mutación; pending no equivale a producción aprobada; modificar lista no reescribe una versión emitida existente; relaciones no cruzan tenant; upgrade de datos SHOT-07 y tests de regresión API/Golden. Sin mock de guardado ni uso de campos existentes con semántica distinta.

## Plan de implementación condicionado a las C

1. Incorporar resoluciones owner únicamente para 01, 02, 04, 05, 08, 11 y 12; registrar deltas normativos necesarios antes de implementación. No convertir los defaults de este documento en aprobación implícita.
2. Preservar `engine/src/dekopen_engine/pricing.py` y tests de primitivas H6. Añadir cálculo comercial puro y tests de oráculo independiente con entradas humanas/catalogadas; no I/O ni reloj en engine.
3. Nueva migración incremental para delta aprobado; no editar migraciones históricas. Completar controles RLS/RBAC y auditoría exigidos por autoridad, probándolos en PostgreSQL real, sin reabrir A.
4. App de pricing en el monolito, autenticación/MFA/contexto RLS existentes, resolución server-side y DTOs sin filtración de costos. Generar OpenAPI/cliente y preservar calculate/inspect/optimize-cut.
5. S09 y flujo comercial real, i18n/tokens Light/Dark; layout, clases, módulos y ergonomía a criterio profesional. Importación tipada con preview, error claro y escritura auditada, sin crear decisiones de producto por parser/organización de clases.
6. Verificación progresiva seguida del checker canónico completo con Python 3.12, Docker operativo, tests reales integración/Playwright/pgTAP, upgrade/rollback PostgreSQL 16, OpenAPI reproducible y lint/types/build. Conservar los seis filtros y cuatro required contexts; ningún gate se debilita.

Regresión obligatoria futura: G1–G7 pass, G8/G9/G11/G12→SHOT-06B xfail, G10→SHOT-24 xfail, Core mutations 20/20, Golden byte-identical, BFD e Inspector SHOT-07 sin cambios contractuales. No se atribuye ningún nuevo resultado de tests a esta auditoría documental.

## Evidencia de la pasada y parada

Sólo se modifica este plan. No código funcional, migraciones, fuentes normativas, Golden, commit ni push. Verificación ejecutada: tabla con 13 filas y conteos 6/0/7; `git diff --exit-code` y `git diff --cached --exit-code` retornaron 0. `git status --short --branch`: `## main...origin/main` y únicamente `?? docs/plans/PLAN_SHOT-08.md`.

Golden byte-identical a HEAD: `git hash-object --no-filters` del archivo y `git rev-parse HEAD:engine/tests/golden_example.json` coinciden en blob `bd93f8b70b78892c9aeda0b9a59ac8c79ce3d7e5`. SHA-256 del archivo completo: `c21c88d66e7ee2e0049ff01f4007cdd168383595d5b2f0f001fccf743ac5bff6`. El `response.calculation_hash` embebido permanece `sha256:562cdc97337a690f09db12590ee8a99b420ebc6b7dbf9c40a4d4755132d24f21`; es un hash de cálculo, distinto del hash del archivo. No se ejecutó Gauntlet en esta auditoría sin cambios funcionales.

**RULE SAYS — Constitución, Regla 20:** «PROHIBIDO rellenar vacíos materiales con supuestos de la IA.»

**AGENT INTERPRETS:** siete residuos concretos carecen de autoridad suficiente, después de retirar obligaciones ya fijadas. Bajo la orden vigente se detiene antes de implementar porque C > 0. No se pregunta por A/B ni se presenta la implementación existente incompleta como motivo para que el owner vuelva a aprobar reglas ya normadas.

</details>

</details>
