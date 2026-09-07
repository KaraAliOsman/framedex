# PLAN_SHOT-07 — Resolución canónica y ejecución FASE 2

Base: `39005492b8dbd5f7a3b90f76876a0ad6e63f3714`. Rama: `shot-07`.
Owner: resolución `aade4165-9ade-4078-a90d-f32bb2ded1ed`, 2026-09-06.
PD-07-01…29 RESUELTAS. FASE 2 autorizada hasta PR protegido con cuatro checks verdes. NO MERGE.
Codex es único escritor. No SHOT-06B/08 ni G8/G9/G10/G11/G12.

## Contrato activo y precedencia

La resolución íntegra al final es autoridad sobre las propuestas históricas.
La auditoría anterior se conserva como historia, no como decisiones abiertas.
Flujo: request → geometría/peso/herraje SHOT-06 → facts exactos → Inspector puro → BFD puro → adapter/API → S07 modal.
El cálculo estricto y su hash no cambian; Inspector/BFD son derivados.

BFD: cada pieza consume un kerf, ambos trims una vez por barra nueva.
`usable = stock - head_trim - tail_trim`.
`piece_consumption = sum(lengths) + N * kerf`.
`remainder = stock - head_trim - tail_trim - sum(lengths) - N * kerf`.
Estas expresiones normalizan el bloque PD06 pegado con asteriscos, de acuerdo con
las definiciones explícitas PD03/04/08 y el ejemplo aritmético PD02; no cambian su significado.
Fixture Proline SINTÉTICO: 5800, cuatro piezas 1006 y dos 806, kerf 4, trims 15/15;
una barra, productive 5636, process 5690, remainder 110.
SKU taller PRO6004-FRAME-DEMO; compra DEMO-PROLINE-PRO6004-BAR-5800.
No son SKU reales del fabricante. DOC05 stock 6000 produce remainder 310.

Stock ProfileCut: longitud única en profile_articles.commercial_length_mm;
compra en profile_purchase_mappings. Acero: reinforcement_articles; peso sigue
profile_articles.steel_weight_kg_m. cutting_profiles aporta política de sierra.
Configuración 14/14 en inspector_rule_configs con precedencia tenant/global y
JSON Decimal. Nuevas columnas chamber_clearance_mm y carriage_capacity_kg.

R01 masa móvil total exacta; R02 dimensión terminada; R03 intersección sistema/kit;
R04 mono4 y DVH4-ANY-4, área exacta; R05 compara Ix contra requisito externo con
structural_basis, no solver ni certificación NCh432:2025; R06 retención glass/panel;
R07 coordenadas de drenajes y fix central; R08 gaps perimetrales con wrap;
R09 continuidad/WHITE (FOILED sólo pruebas puras); R10 medición WORKSHOP_QC,
N/A en DESIGN; R11 clearance explícita; R12 fixture puro 3L; R13 stays;
R14 fixture puro mono con capacidad por carro. Dispatcher Extended intacto.

Fix automático: únicamente R07 condicionado a dos drenajes, centro ausente y
requisito tres. ADD_BOTTOM_DRAIN_HOLE, preview, precondiciones, draft, calculate,
inspect, commit sólo si ambos success; rollback exacto e idempotencia sin duplicación.
R02/03/04/06/08/10/11/13 son SUGGESTION_ONLY. R01/05/09/12/14 bloqueados por
falta de autoridad o topología futura. R07 sin condición válida no inventa posiciones.

Cualquier finding RED bloquea production_allowed. Missing input usa severidad
de regla; R10 DESIGN es N/A. WorkshopReadiness además requiere BFD válido.
S07 modal de S06 con tabs Inspector/Corte 1D; pedido separado de taller.
TanStack conserva resultados remotos; Zustand inputs/annotations/preview.
API: /inspect/ y /optimize-cut/ separados, JWT/org/OWNER aal2/RLS, catálogo server.
calculate conserva exactamente sus siete claves y golden byte-identical.

## Secuencia y validación

Primero alinear fuentes activas y auditar Regla 0/20. Después nuevas migraciones,
RLS, loaders, BFD/tests, Inspector/tests, evaluador hardware compartido y preflight,
API/OpenAPI/Orval, S07/fix, suites y Checker completo. No alterar migraciones viejas.
Matriz obligatoria: todos los casos positivos, negativos, fronteras y ausencias
en la resolución íntegra, además de BFD determinista/barra/kerf/trims/SKU,
transacción de fix, API/auth/RLS, ambos temas, Canvas <300ms y regresiones previas.
Cuatro contexts: Lint & Typecheck; Test Suite; Frontend Build; Database Gate.
G1–G7 intactos; cinco xfails; golden sólo --check, sin regenerar.
No marcar implementación, tests ni gauntlet completos sin evidencia real.

## Registro de ejecución

- Resolución incorporada íntegramente; PRD01/02/06/07, ANIM, frontend/API y pantalla S07 alineados.
- Regla0/20: las28 pendientes previas quedan resueltas por owner. R10 ahora WORKSHOP_QC alinea también DOC06 a1.50, eliminando su antigua segunda tolerancia1.0.
- La frontera NCh432 es verificación de requisito externo, sin solver/certificación.
- Continuación owner 2026-09-07: `131adb4a-593d-4046-8a9b-befd707e4aed/pasted-text.txt`, leída íntegramente. Mantener working tree; completar FASE2 sin merge.
- HEAD sigue39005492; sin commits/push/PR. Migraciones históricas verificadas sin cambios canónicos. EXPECTED_DATABASE_TABLES tiene una sola declaración.
- BFD cutting.py existente extendido, no reescrito:20 tests PASS; Ruff y mypy engine (28 módulos) PASS. Purchase list ordenada por stock físico; ecuación intacta.
- Nuevas migraciones20260906000000/20260906000100 y seed sintético. pgTAP050 con85 aserciones; upgrade07 preserva catálogo06 y prueba activación/rollback de config sin clearance.
- CuttingRepository y pruebas de integración creados; selección de mapping tenant/global, acero explícito/default y cutting profile sin first-match.
- Gate DB ampliado07 previo a Inspector: exit0,213 aserciones pgTAP,26 integration; cadena limpia, seed, PostgreSQL16 y upgrade/rollback PASS.
- Facts compartidos y diagnóstico previo estricto implementados; R01–R14:51 tests PASS; engine completo164 PASS y5 xfails estrictos. Backend no integración90 PASS. Core mutations20/20 killed.
- API derivada, repositorios y modal con draft R07 implementados. OpenAPI anterior y endpoint calculate idénticos; regeneración reproducible. Ruff, ESLint, tsc, Prettier y mypy32 módulos PASS.
- Pruebas de modal cubren preview, rollback calculate/inspect, stale, idempotencia, error BFD y recomputación RED→RED/YELLOW/GREEN. E2E real Light/Dark incorporado; Gauntlet completo en ejecución, resultado pendiente.
- Existe worktree ajeno `.worktrees/normative-capability-cleanup`; no tocar ni agregar al commit.
- Golden y diferidos todavía sin cambios. No ejecutar goldgen para escritura.

<details>
<summary>Auditoría histórica FASE 1, sustituida por la resolución canónica</summary>

# PLAN_SHOT-07 — FASE 1: auditoría normativa y plan de ejecución

**Estado: PLAN SOLAMENTE — IMPLEMENTACIÓN DETENIDA POR REGLA 0 / REGLA 20.**

Autorización: `START SHOT-07`, adjunto del owner
`eddb07d5-f295-401d-b569-c9cbae558b1d/pasted-text.txt`, leído el 2026-09-06.
Este documento registra hechos comprobados, contratos expresos del owner y
propuestas para decisión. Una propuesta no equivale a autoridad aprobada.
No se ha implementado BFD, Inspector, UI, API ni DDL de SHOT-07.

## 1. Baseline y límites de escritura

- Base exigida y comprobada: `main @ 39005492b8dbd5f7a3b90f76876a0ad6e63f3714`.
- `main`, `origin/main` y la rama remota `main` coincidían; working tree limpio.
- Rama creada desde esa base: `shot-07`. HEAD permanece en la base, sin commits
  propios, push ni PR de SHOT-07.
- Único archivo nuevo autorizado: `docs/plans/PLAN_SHOT-07.md`. No se modifica
  `PLAN_SHOTS.md`, ni fuentes normativas, ni código durante FASE 1.
- SHOT-06 cerrado; tag `shot-06` corresponde al merge técnico
  `af623e43bf90db8199782c65e924a9a9dd6353ed`, no al cierre documental.
- Single Writer Rule: Codex es el único escritor; sin subagentes escritores.
- Comprobación de regresión existente durante esta auditoría:
  `python -m pytest engine/ -q -W error` → **93 passed, 5 xfailed**;
  `python -m engine.scripts.regenerate_golden --check` → **PASS, read-only**.
  No son pruebas de implementación de SHOT-07.
- Golden vigente: UUID `3067da09-3119-5ad0-a1d5-498cd2dfd753`, `POSTE-V`,
  siete claves de respuesta; `calculation_hash` =
  `sha256:562cdc97337a690f09db12590ee8a99b420ebc6b7dbf9c40a4d4755132d24f21`.
  No se ejecuta `make goldgen` ni se altera el snapshot en FASE 1.

## 2. Autoridad y evidencia leída

Orden de lectura: AGENTS → Constitución → PLAN_SHOTS → PRD-01 completo →
PRD-07 completo → animaciones → PRD-06 completo → pantallas S06/S07 →
PRD-FRONTEND completo → PRD-02 completo → runtime engine → adapter/API →
Canvas → tests G1–G7 y golden. Las búsquedas adicionales contrastaron DDL,
seed y referencias históricas; no convierten documentos históricos en autoridad.

| Fuente | Evidencia relevante |
|---|---|
| `AGENTS.md` §§2/4/5 | Maker/Checker, Regla 0/20, plan antes de implementar |
| `docs/CONSTITUTION.md` reglas 0–3, 6, 10–11, 14–15, 18–22 | Decimal, pureza, autoridad por sistema, lenguaje humano, clic humano, no retazos productivos |
| `docs/PRD/PLAN_SHOTS.md:50` | BFD + R01–R14 + panel; Proline 5800, compra distinta de corte, RED bloquea OT, diff real |
| `docs/PRD/PLAN_SHOTS.md:51` y filas SHOT-09/10/24 | Pricing, documentos, persistencia y retazos pertenecen a shots posteriores |
| `docs/PRD/PRD-01.md:24` | BFD con kerf y despuntes; no congela parámetros ni desempates |
| `docs/PRD/PRD-01.md` §§3.2–3.3, 4.3, 5, 6 | Hardware exacto, peso con kit/panel, BOM, 27 campos, regresiones; response SHOT-06 excluye Inspector/BFD |
| `docs/PRD/PRD-07.md:23` y tabla R01–R14 | Todas las constantes configurables por sistema; fórmula, severidad y propuesta de fix por regla |
| `docs/PRD/PRD-07.md` §3 | Semáforo y bloqueo de producción |
| `docs/PRD/PRD-ANIMATIONS-INTERACTIONS.md` §§3.1/4 | Canvas previo limitado a FIXED; fix destella 300 ms y semáforo 150 ms |
| `docs/PRD/PRD-06.md` §§1/2/5 | Hash documental posterior, compra/corte separados, ejemplo 6000 con despuntes 15/15 y kerf acumulado 24 |
| `docs/PRD/SCREENS_SPECIFICATION_S01_S28.md:17` y `:18` | S06 ruta de editor; S07 modal, ruta abreviada diferente |
| `docs/PRD/PRD-FRONTEND-APIS-COMPONENTS.md` §§1.1/1.2/2 | Hash exacto, discovery restringido, panel dockable de 320 px; no endpoint BFD/Inspector definido |
| `docs/PRD/PRD-02.md` §2 | PA.commercial_length_mm existe; no SKU comercial separado ni configuración R01–R14 |
| `supabase/migrations/20260901000000_initial_schema.sql:74` / `:110` / `:142` | DDL efectivo PS/PA/HK; stock 6000 por default, capacidades y cantidades de herrajes |
| Migraciones `20260902000000`, `20260905000000`, `20260905000100` y `supabase/seed.sql` | Matriz cut_add; autoridades SHOT-06; sólo catálogo DEMO_60 en seed |
| `engine/src/dekopen_engine/geometry.py:188` / `:219` / `:465` | SashGeometry interno; medidas terminadas; cálculo y selección de kit antes de devolver resultado |
| `engine/src/dekopen_engine/hardware.py:30`, `weight.py:24`, `panel.py`, `bom.py`, `snapshot.py` | Rechazo de kits, exactos internos/publicación cuantizada, panel independiente, BOM estable, hash puro |
| `engine/src/dekopen_engine/models.py:155` / `:185` / `:224` | 27 SystemParams; nodo no modela drenajes/diagonales/cierres; EngineResult no expone facts completos de inspección |
| `backend/engine_api/{repository,adapter,views,serializers}.py` | Loader RLS, WHITE, cálculo estricto, errores400/404/422, siete claves y hash |
| `frontend/src/features/canvas/canvasStore.ts`, `useEngineCalculation.ts`, `CanvasEditor2DView.tsx`, `CanvasTechnicalResults.tsx` | Store de inputs G1 literal; respuesta sólo TanStack; commit de dimensión transaccional; sin Inspector |
| `frontend/src/App.tsx` y `frontend/tests/e2e/canvas.spec.ts` | Ruta real demo/g1 y contrato <300ms con cinco medidas |
| `engine/tests/{test_gold_cases_core,test_shot06_core,test_snapshot,test_gold_cases_deferred,test_hardware_weight}.py` | Dimensiones congeladas, exactitud de masas, cinco xfails, golden y fallbacks |
| `docs/PRD/PRD-08.md:49` y biblias históricas equivalentes | Pro6004 privado, barra 5800; descripción, no fixture ejecutable ni SKU de pedido |
| `docs/PRD/PRD-16.md:58` | Ejemplo 4 mm/15 mm en retazos SHOT-24; no autoridad automática SHOT-07 |
| `scripts/check_dod.py:371` / `:433`, `.github/workflows/ci.yml` | Guards temporales aún prohíben Inspector; cuatro contexts existentes |

La auditoría de DB es sobre las cuatro migraciones versionadas y seed: no se
arrancó ni mutó una base de datos para completar este plan. No se consultó una
ficha externa ni se declaró conformidad NCh 432. Se comprobó la falta de sus
inputs y fórmula en las autoridades locales, sin inventar una norma.

## 3. Scope congelado y alineación

Entrega SHOT-07: **Corte 1D BFD + Inspector R01–R14 + panel inspector**.
Consume las longitudes técnicas, masas y catálogo resueltos por SHOT-06, el
adapter/auth/RLS de SHOT-04 y el Canvas de SHOT-05. Inspector valida; BFD
empaqueta; ninguno inventa o altera longitudes de despiece.

Futuros consumidores: SHOT-08 puede consumir información de uso/merma sin que
SHOT-07 haga pricing; SHOT-09 emitirá documentos/OT desde listas distintas;
SHOT-10 persistirá posiciones/versiones; SHOT-24 gestionará retazos y monoriel.
Los contratos nuevos deben poder ser consumidos después sin activar esos flujos.

Fuera de alcance: G8/G9/G11/G12 y SHOT-06B; G10/monoriel; pricing comercial,
auditoría de precios nueva, OT/documentos reales, proyectos/versiones/fixes
persistidos, billing, IA, OCR, DXF, offcut_inventory/QR. No iniciar SHOT-08.
G1–G7 no se modifican para satisfacer Inspector. G-Pro1 sigue pendiente de
sign-off físico SHOT-12; una prueba BFD no equivale a certificar Proline.

## 4. Inventario de autoridades disponibles y faltantes

| Dato | Existe hoy | Falta para SHOT-07 |
|---|---|---|
| Identidad técnica | PA.id/system_id/sku/role/material; ProfileCut.sku | Identidad de compra distinta y relación aprobada con artículo técnico |
| Longitud comercial | PA.commercial_length_mm NUMERIC(10,2), default 6000 | El loader no la selecciona; no está en EffectiveProfileArticle; Proline no está en seed |
| Proline 5800 | Gate y descripción privada en PRD-08 | SKU técnico, comercial, proveedor, color, unidad y conjunto de piezas de prueba |
| Fabricante/proveedor | cost_lists.supplier_name y orders.supplier_name | Ningún vínculo técnico PA→proveedor/fabricante; no usar pricing/órdenes como autoridad implícita |
| Color | Request.color; API admite sólo WHITE; columnas futuras interior/exterior | Stock físico por color/acabado y su correspondencia; no inferir desde el nombre del SKU |
| Unidad compra | cost_list_items.unit en dominio comercial futuro | Unidad de la oferta de stock y conversión aprobada; no asumir barra/metro intercambiables |
| Acero | ReinforcementPiece con parent SKU y reinforcement_sku nullable | SKU de compra/stock del refuerzo; material_type sólo PVC/ALUMINIUM; no tratar NULL como SKU del PVC |
| Kerf y trims | Sólo referencias narrativas/ejemplos | Autoridad persistida, valores, frecuencia y ecuación; no usar welding_loss ni reinforcement_gap |
| Config Inspector | Enum inspector_status, findings JSONB futuros; HK límites/cantidades; GB | No tabla/columnas de thresholds R02–R14 ni precedencia/overrides por sistema |
| Peso hoja | ExactLeafWeight incluye kit e infill; LeafWeight público redondeado | Transporte del exacto al Inspector y resolución de masa R01/R14 |
| Medida terminada | SashGeometry interno | Transporte directo, sin reconstrucción desde corte por el Inspector |
| Vidrio | Nodo glass_spec/espesor total; GlassPiece neto/área pública | Clasificación validada y área exacta original para fronteras R04; no confundir panel |
| Inercia/viento | No autoridad computable encontrada | Ix, Ireq, sección/espesor, solicitación/soportes, norma/versión y parámetros de cálculo |
| Drenajes/cierres/couplers/diagonales/holgura cámara | No facts computables completos en nodo/resultado | Modelo, procedencia, unidades y cobertura; quantities no son posiciones |

Nuevas autoridades, si el owner las aprueba, requieren DDL NUEVO, NUMERIC exacto,
org_id/RLS, permisos de edición y fixture de catálogo explícito. No se congela
una tabla inventada en FASE 1. Propuesta de separación a resolver en PD-07-01/10:
relación de stock técnico↔comercial y configuración tipada de inspección por
sistema. No reutilizar `pricing_rules`, `cost_list_items` o `offcut_inventory`.
Reglas derivadas de HK/GB deben referenciarlas; no duplicar sus capacidades/matriz.
Definir también overrides, valores ausentes, scope global/tenant y versionado.

## 5. Arquitectura BFD propuesta — bloqueada por decisiones 01–08

Flujo puro propuesto:

```text
EngineResult SHOT-06 + identidad de request + catálogo de stock validado
  → proyección de piezas lineales exactas (qty expandida con identidad estable)
  → grupos de stock físico compatibles
  → Best-Fit Decreasing con política de corte explícita
  → BfdResult {purchase_list, workshop_cut_plan}
```

El adapter carga catálogo bajo RLS; el motor recibe valores tipados Decimal.
No lectura DB/HTTP/archivos dentro de BFD. No lookup de precios. Cada corte
mantiene `length_mm`, ángulos, rol, SKU técnico, bay/leaf y cantidad de origen.
Soldadura YA está incorporada en las longitudes SHOT-06; no volver a añadirla.
Paneles/vidrios no son piezas lineales. Qué grupos de refuerzos se optimizan
queda pendiente de stock identificable; no desaparecerlos silenciosamente.

### 5.1. SKU y longitud

`workshop_profile_sku` identifica la pieza de taller. `commercial_sku` identifica
la barra que se solicita al proveedor. No son alias por defecto; el gate
Proline exige desigualdad real. La lista de compra consolida barras; el plan de
taller enumera cortes. Una no sustituye a la otra.

**5800.00 mm tiene autoridad como requisito del gate**, no como constante de
algoritmo ni valor DEMO_60. PA.commercial_length_mm puede transportar longitud
por artículo, pero no proporciona por sí sola una oferta de compra completa.
El fixture Pro6004 de PRD-08 es una descripción privada/histórica: búsqueda en
engine/backend/supabase/tests y corpus no encontró una fixture activa con ambos
SKU y piezas. No crear desigualdad artificial ni renombrar cortes DEMO a Proline.

### 5.2. Kerf, despuntes y conservación

Contrato parcial sustentado: hay kerf, despunte de cabeza y de cola; todos son
Decimal independientes. **Valores y conteo no resueltos**. Para explicitar la
decisión pendiente, no para adoptar una fórmula:

```text
L = stock_length_mm; h = head_trim_mm; t = tail_trim_mm; k = kerf_mm
U = L - h - t
P = sum(exact_cut_length_mm)
K = k * N_cuts(policy, number_of_pieces, last_cut, trims)
consumed_inside_usable = P + K
remaining = U - consumed_inside_usable
fit ⇔ consumed_inside_usable <= U
L = h + t + P + K + remaining
```

`N_cuts` no está definido todavía. `n*k` y `(n-1)*k` difieren incluso para una
sola pieza: no seleccionar una en silencio. Aclarar si trims ya incluyen sus
cortes y qué pasa con ajuste exacto que no necesita separar remanente. Cada
barra nueva requiere la política aprobada de cabeza/cola. No hay entrada de
retazos en SHOT-07; aplicarles trims se decidirá en SHOT-24.

No derivar k=4 de las seis piezas/24mm del ejemplo DOC-05 ni heredar 4/15 de
PRD-16. El ejemplo de PRD-06 §5 además no conserva longitud: con sus números,
4×1006 + 2×806 = 5636; 6000−5636−24−15−15 = **310**, mientras imprime 320.
Es evidencia de inconsistencia del ejemplo, no una nueva expectation del motor.
DOC-04 habla de 6000 genérico; no reemplaza la longitud 5800 específica del gate.

### 5.3. Orden determinista propuesto, pendiente PD-07-05

1. Canonicalizar grupos por identidad física aprobada (PD-07-07).
2. Orden primario de piezas: longitud DESC.
3. Empates: propuesta concreta de clave ascendente
   `(position_id, bay_id, leaf_id, collection_kind, role, workshop_sku,
   angle_start_deg, angle_end_deg, copy_ordinal)`. IDs ausentes llevan un
   discriminante explícito antes del valor; strings se ordenan por bytes UTF-8,
   ángulos por Decimal y ordinales por entero. Antes de expandir qty se suman
   cantidades de registros con identidad y dimensiones idénticas; se asignan
   ordinales desde 1 hasta qty dentro de cada identidad. Así no se usa un índice
   incidental del BOM para distinguir copias indistinguibles. El adapter debe
   proporcionar una identidad de posición estable cuando agrupe varios
   cálculos; no se inventa persistencia de proyectos. PD05 debe aprobar esta
   propuesta y su correspondencia exacta con campos reales.
4. Entre barras que admiten la pieza, elegir el menor residual tras ubicarla.
5. Empate entre barras: menor índice de apertura canónico propuesto.
6. Abrir barra nueva sólo si ninguna existente admite la pieza. Pieza que no
   cabe en una barra nueva: fallo tipado, sin plan/pedido parcial ficticio
   (política de salida pendiente PD-07-08/29).
7. Output por grupo canónico, luego índice de barra; cortes en orden de
   asignación BFD, sin reordenado incidental posterior.

El owner debe aprobar esa clave/orden antes de congelar expected bytes.
BFD es la heurística solicitada; no se declarará un mínimo global de barras
sin prueba. No depender de sets/hash iteration, collation local ni row order DB.

### 5.4. Agrupación física propuesta

Auditar identidad de sistema/artículo técnico, material real, color/acabado,
commercial SKU, proveedor/fabricante, stock length y orientación si altera la
barra utilizable. Un SKU sin system no garantiza identidad global. No mezclar
PVC/ALUMINIUM/acero ni junquillos distintos. No usar parent_profile_sku para
comprar acero. Varias ofertas/longitudes del mismo artículo no se seleccionan
por orden de DB: requiere política explícita, pendiente PD-07-07.

### 5.5. Modelos puros propuestos, sin código ni schema definitivo

| Modelo | Campos y semántica a aprobar |
|---|---|
| StockAuthority | system/article identity, workshop_profile_sku, commercial_sku, supplier/manufacturer, material, color, purchase_unit, stock_length_mm, política k/h/t |
| LinearPiece | piece_id estable, source/bay/leaf, workshop SKU, rol, material, color, length_mm exacta, ángulos, ordinal qty |
| BarCut | Referencia de pieza original y longitud/ángulos intactos; posición/secuencia sin inferir geometría |
| StockBarPlan | commercial/workshop SKU, bar_index, stock_length_mm, usable_length_mm, cuts, kerf_total_mm, trims_total_mm, used_length_mm, remainder_mm |
| PurchaseLine | commercial SKU, proveedor, material/color, stock_length_mm, unidad y qty_bars entero; sin precio ni acto de compra |
| WorkshopCutPlan | Barras ordenadas con SKU técnico, cortes/IDs/ángulos; no aplanado en PurchaseLine |
| BfdResult | purchase_list y workshop_cut_plan separados; métricas de uso/merma según PD-07-08 |

`used_length_mm` debe aclarar si incluye trims o sólo P+K. `waste_pct` necesita
denominador, inclusión de remanente/trims/kerf, porcentaje versus fracción y
escala/ROUND_HALF_UP aprobados; no reutilizar waste_factor_pct comercial.
La recomendación es exponer sumandos exactos además de cualquier presentación.
No fijar campos comerciales mediante defaults desconocidos.

PD-07-09 resuelta dentro del alcance autorizado: conservar **remainder_mm**,
campo expresamente permitido por el owner, y presentarlo como **remanente**
para la longitud no consumida. Es una denominación neutral de este plan;
no se atribuye al owner una clasificación aprobada como desperdicio o retazo
reutilizable. No afirmar que es inventario reutilizable,
reservarlo, consumirlo o crear QR. Calcular una métrica waste futura no autoriza
a registrar offcuts; su semántica queda en PD-07-08.

## 6. InspectorInput y obtención de facts — propuesta PD-07-25

```text
Geometría/masas existentes → facts exactos + BOM (misma ejecución)
Catálogo RLS → configuración y autoridades de Inspector
Mediciones/taller explícitos autorizados → facts externos con procedencia
                     ↓
          inspect(input, config) puro
                     ↓
       findings ordenados + semáforo + bloqueo
```

Propuesta de `InspectorInput` tipado: referencia al request/cálculo y sistema;
BOM; facts por bay/leaf de apertura, W/H terminados, masa exacta, infill
(discriminante glass/panel), spec/área exacta, kit solicitado/seleccionado y sus
capacidades; facts de tramo/refuerzo/viento, drenajes, cierres ordenados, ancho
continuo/coupler, diagonales observables y superficies de holgura. Sólo se
incorporan facts cuya autoridad quede resuelta; `None` no equivale a cero.

La geometría YA calcula W/H terminados y ExactLeafWeight, pero sólo publica
cortes y masas a 2 decimales. Inspector no puede reconstruirlos usando fórmulas propias
ni sumar LeafWeight público: se perdería exactitud. Ejemplo real existente:
G6 pesa 23.96192 exacto, publicado 23.96; el test de capacidad rechaza 23.96.
Área exacta también debe salir de su cálculo original, no del area_m2 publicado a 4 decimales.
La forma de transportar facts sin alterar el response/hash aprobado está
pendiente; posible envoltorio interno distinto de EngineResult, sin cambiar
fórmulas, sólo si se autoriza.

Bloqueo de materialización: `resolve_hardware_kit` rechaza peso/rangos antes de
retornar BOM; `resolve_bead_rule` rechaza un infill no mapeado. Por tanto R01,
parte de R03 y R06 negativos no llegan naturalmente a un Inspector que sólo
recibe el EngineResult exitoso. No eliminar esos guards ni atrapar el error y
fabricar un resultado parcial. Se necesita contrato explícito de diagnóstico
de solicitudes inválidas y sus facts; tests sintéticos no sustituyen ese gate
de integración.

Aplicabilidad/cobertura por regla debe distinguir evaluación completa, no
aplicable y autoridad faltante. No afirmar GREEN porque una colección vacía
ocultó R05/R07/R10 sin datos. Propuesta: validar integridad del input antes de
evaluar; falta de autoridad devuelve diagnóstico tipado bloqueante, no un PASS.
La representación pública y relación con production_allowed siguen PD-07-25/29.

## 7. Matriz exhaustiva R01–R14

Estado de implementación de **cada regla: NO IMPLEMENTADA**. Las condiciones
numéricas siguientes transcriben PRD-07; su uso requiere configuración por
sistema y resolver inputs/precedencias. Los nombres de tests son contratos
futuros, no archivos creados. «Positivo» significa regla satisfecha, «negativo»
infracción de esa regla, independientemente de otras reglas aplicables.

| Regla | Input → fórmula de fallo | Autoridad DB existente / faltante | Severidad y finding humano previsto | Fix: viabilidad actual | Prueba positiva / negativa y bloqueo |
|---|---|---|---|---|---|
| R01 | masa hoja y capacidad kit → P>capacidad; definición de P en conflicto | HK.max_leaf_weight_kg existe; ExactLeafWeight incluye kit/panel; fuente PRD-07 omite ambos | RED: hoja supera la carga del herraje; riesgo de descuelgue | BLOCKED_MISSING_AUTHORITY: no kit de 130 kg aprobado ni división automáticamente autorizada | `test_r01_weight`: P=capacidad / P=capacidad+0.01; caso exacto que redondea a capacidad. PD11/25 |
| R02 | W/H de hoja → H/W>2.5 o <0.4; W>0 | Faltan thresholds y definición de W/H Inspector; SashGeometry los tiene internamente | YELLOW: hoja demasiado alta/estrecha; funcionamiento deficiente | SUGGESTION_ONLY: objetivo 1:1.5 no define qué eje/división mover | `test_r02_ratio`: W=400, H=1000 y W=1000, H=400 / H=1000.01 y H=399.99 respectivamente. PD10/12/28 |
| R03 | W<350 o W>1600 o H>2400; comparar también límites kit según decisión | HK min/max existe; límites genéricos Inspector no persistidos ni precedencia | RED: hoja fuera de dimensiones permitidas | SUGGESTION_ONLY: redimensionar requiere objetivo/eje y diff paramétrico aprobado | `test_r03_dimensions`: bordes 350/1600/2400 / W=349.99, W=1600.01, H=2400.01; caso que pasa serie pero falla kit y viceversa. PD10/13/25 |
| R04 | clase vidrio y área exacta → mono 4 mm, A>1.80; DVH 4-12-4 A>2.60 | Nodo spec y GB total; no clasificación/config límites; net 8 no identifica DVH 4-12-4 | RED: cristal demasiado grande para su composición; riesgo de rotura | BLOCKED_MISSING_AUTHORITY para cambio automático: no catálogo de vidrio templado/certificación; GB de 6 mm no certifica templado | `test_r04_glass_area`: A=1.8000/2.6000 / A=1.8001/2.6001; otras specs y panel requieren aplicabilidad explícita. PD10/14/25 |
| R05 | luz>1800 e Ix<Ireq | No Ix ni Ireq; no espesor/sección/solicitación/zona/exposición/altura/soportes/ecuación NCh432 | RED: refuerzo insuficiente para el viento | BLOCKED_MISSING_AUTHORITY; RF-HEAVY sólo texto, no catálogo | `test_r05_wind`: luz 1800 y caso aprobado Ix=Ireq / luz 1800.01 e Ix menor; expected normativo aún IMPOSIBLE sin ficha y fórmula. PD15 |
| R06 | espesor infill ausente de matriz vigente del sistema | GB y helper neutral únicos; rechaza antes del resultado; panel 24 usa misma matriz por PD06-20 | RED: no hay junquillo compatible con el relleno | Candidato AUTO_FIXABLE condicionado: selección humana de espesor/spec existente; hoy BLOCKED_MISSING_AUTHORITY por camino diagnóstico/diff/editor | `test_r06_bead`: 20/24 con regla / 25 ausente; panel 24 positivo; probar error humano y matriz compartida. PD16/25/28 |
| R07 | ancho vano>800 y nº drenajes inferiores<3 | No desagües, posición ni separación; threshold no persistido | YELLOW: desagüe insuficiente; riesgo de acumulación/filtración | BLOCKED_MISSING_AUTHORITY: añadir centro requiere coordenadas y modelo, sin perforar BOM implícitamente | `test_r07_drains`: W=800 o W=800.01,n=3 / W=800.01,n=2; ubicación inferior debe demostrarse. PD10/17 |
| R08 | separación de cierres consecutivos>800 | HK.contents tiene qty, no coordenadas/path ni regla de cierre de ciclo | YELLOW: cierre demasiado separado; sellado deficiente | BLOCKED_MISSING_AUTHORITY: no inferir reenvíos/posiciones desde qty | `test_r08_closures`: gap 800 /800.01; orden y tramo último→primero requieren decisión. PD10/18 |
| R09 | continuo>4000 WHITE o >3000 foliado y sin acople | Request WHITE; no continuidad/acople computables; rol COUPLER por sí solo no prueba presencia | RED: conjunto necesita junta de dilatación | BLOCKED_MISSING_AUTHORITY: topología/acople/catálogo no disponibles | `test_r09_expansion`: WHITE 4000 /4000.01 sin acople; foliado 3000 /3000.01 sólo fixture puro autorizado; acople verdadero elimina infracción. PD10/19 |
| R10 | abs(D1-D2)>1.50 | No segunda diagonal observable; ortogonal teórico es tautología; DOC-06 publica control físico<=1.0 | RED: marco fuera de escuadra | BLOCKED_MISSING_AUTHORITY: no corregir mediciones físicas mediante geometría ficticia | `test_r10_diagonals`: delta 1.50 /1.51, con observables aprobados; no sqrt(W²+H²) dos veces. PD10/20 |
| R11 | gap fuera de [10.50,13.50] | Falta definición de superficies y derivación; PS.sash_overlap_mm=8 no es gap 12 | RED: separación hoja/marco fuera de tolerancia | BLOCKED_MISSING_AUTHORITY: poner 8 no demuestra corregir gap 12 | `test_r11_clearance`: 10.50/13.50 /10.49/13.51; fixture debe identificar superficies. PD10/21 |
| R12 | SLIDING_3L, ancho>4500, Ix<45cm⁴ | No Ix/catálogo; geometría 3L difiere a SHOT-06B | RED: refuerzo insuficiente en corredera triple | BLOCKED_MISSING_AUTHORITY; sin inventar RF-HEAVY | `test_r12_three_leaf`: W=4500 o W=4500.01, Ix=45 / W=4500.01, Ix=44.99; sólo input puro si autorizado. PD10/22 |
| R13 | AWNING, H>1200 y no compás doble | HK.stay_arms_qty existe; falta semántica doble/eje H/override; DEMO kit ya 2 y max H=1000 | YELLOW: proyectante alta requiere soporte adicional | BLOCKED_MISSING_AUTHORITY para auto: no kit alto compatible; no incrementar qty a mano en contents | `test_r13_awning`: H=1200 o H=1200.01 con doble / H=1200.01 sin doble; significado qty=2 pendiente. PD10/23 |
| R14 | MONO, P>150, sin 4 carros con capacidad>=80kg/rueda | HK.carriages_qty y max_leaf_weight existen; falta capacidad por rueda y vínculo carro/rueda; G10 difiere a SHOT-24 | RED: carros insuficientes para la carga | BLOCKED_MISSING_AUTHORITY: no kit monoriel cuádruple canónico | `test_r14_mono`: P=150 y caso P=150.01, qty=4, capacidad=80 / P=150.01, qty=3, capacidad=80 y P=150.01, qty=4, capacidad=79.99; sólo input puro autorizado. PD10/24 |

Todas las fronteras se calculan con Decimal; no comparar áreas/pesos
redondeados. Las pruebas deben demostrar la regla real, no sólo que existe un
enum Rxx. Para R05 no se sustituye el cálculo normativo faltante por el simple
test de un operador `<`. Su fixture aprobado debe demostrar Ireq independiente.
Fixtures de reglas no habilitan dispatcher Extended, colores productivos ni
catálogos ficticios. Los G-cases continúan siendo pruebas geométricas: un
finding de Inspector no autoriza a cambiar sus dimensiones.

## 8. Semáforo, finding y bloqueo

Contrato expreso del owner, respaldado por PRD-07 §3, para evaluación completa:

| Hallazgos | Estado | Efecto mínimo |
|---|---|---|
| Ninguno | GREEN | Sin bloqueo de Inspector |
| Sólo YELLOW | YELLOW | Advertencia; permite cotizar; no emitir OT aquí |
| Cualquier RED, aunque haya YELLOW | RED | `production_allowed=false`; botón de aprobación bloqueado |

`production_allowed` es señal derivada para el futuro consumidor, no permiso
para crear órdenes ni un estado persistido de proyecto. Ni GREEN ni un fix
envían a fábrica/compran material: Constitución, regla 11 exige clic humano explícito.
Falta definir relación con inputs incompletos/error BFD (PD25/29). No mapear
fallos de carga o reglas no evaluadas a una lista vacía GREEN.

Propuesta de `InspectorFinding`: rule_id R01…R14, severity, title/diagnosis/risk
mediante claves i18n ES-CL y argumentos tipados, target bay/leaf/component,
fix taxonomy, texto de solución y `diff` legible por máquina separado del texto.
Orden propuesto por número R01…R14 y target estable; identificador estable por
regla/target/condición, independiente del texto traducido. PD28 debe congelarlo.
No traceback, exception ni error DB en el mensaje principal. Las pantallas
actuales muestran códigos validation_error; adaptar presentación de Inspector
no obliga a cambiar el contrato HTTP de errores heredado sin decisión.

## 9. Fix taxonomy, diff y transacción de editor

Taxonomía requerida:

- AUTO_FIXABLE: destino existente, autoridad completa, modificación tipada
  reproducible y recalculable. No significa «ya implementado».
- SUGGESTION_ONLY: recomendación que necesita elegir eje, topología o alternativa;
  no mostrar botón que aparente haberla aplicado.
- BLOCKED_MISSING_AUTHORITY: falta catálogo, medición, fórmula o target; debe
  indicarse en lenguaje de taller, sin completar datos por intuición.

Clasificación por regla en §7. Actualmente **ningún fix está listo para
implementarse sin resolver PD**. Candidato de menor ampliación: R06 con elección
humana de una pareja coherente espesor/spec canónica (20mm/4-12-4 o
24mm/4-16-4) existente en DEMO. No seleccionar 20 versus 24 por orden del catálogo.
Se deben aprobar fixture inicial, elección y diff exactos en PD28; no atribuir
prestación térmica/templado a un string. R01 kit de 130 kg y R05/R12 RF-HEAVY no son
alternativas disponibles. R13 no autoriza mutar composición del kit.

Propuesta de `FixDiff` declarativo, pendiente aprobación:

```text
fix_id, rule_id, target_id
base_request_identity / precondiciones del estado inspeccionado
operations ordenadas: target estable, field permitido, expected_old, new_value tipado
preview humano antes/después
```

No path arbitrario de DB ni script ejecutable. No mutar config de sistema desde
un fix de diseño. Una allowlist debe limitar cada regla a campos autorizados.
Concurrencia: confirmar que las precondiciones siguen vigentes antes de aplicar;
revisión/hash del diseño no debe confundirse con calculation_hash de BOM.

Secuencia propuesta a congelar:

1. Construir y mostrar diff completo antes del clic.
2. Aplicar en copia del estado paramétrico local; jamás mutar DB/engine internals.
3. Reejecutar engine y luego Inspector con autoridades vigentes; si corresponde,
   BFD del mismo resultado. No borrar el finding por acción de UI.
4. Confirmar inputs/resultados de forma coherente sólo si el recálculo requerido
   fue válido. Error, timeout o precondición obsoleta: conservar estado anterior.
5. Segunda aplicación del mismo diff no debe acumular el cambio; definir rechazo
   stale o no-op explícito e idéntico en PD28. No decidir silenciosamente ambos.
6. Findings desaparecen/cambian sólo por reevaluación. Un RED restante conserva
   bloqueo. Animación 300ms del target y transición de 150 ms respetan tokens/tema;
   no forzar GREEN como literalmente sugiere ANIM §4 si hay otro RED.

## 10. UI S07 y frontera de API/hash

S06 real: `/projects/:id/positions/:posId/edit`, restringida por la vista a
`demo/g1`. S07 según pantallas: modal en `/positions/:id/edit`; según componentes:
DockableInspectorPanel con AccordionInspector y WorkshopApprovalBar. No existe
una ruta S07 autónoma canónica. **PD27: decidir modal, panel o ambos y la ruta
contenedora**, sin inventar otra navegación ni habilitar proyectos SHOT-10.

Propuesta: reutilizar controller/TanStack del Canvas, pasar la misma referencia
de resultado a presentación y asociar derivadas a su identidad. Zustand mantiene
inputs/preview/UI, no una segunda copia de EngineResult. Roles OWNER/ESTIMATOR,
auth/RLS y MFA existentes; Light Studio/Dark Graphite, tokens y mensajes ES-CL.
El store actual tiene árbol FIXED con vidrio 4 mm literal y sólo acceptDimension:
cualquier fix de vidrio/kit/topología necesita ampliación explícita PD28, no un
setter genérico con poderes sobre todo el proyecto. No añadir apertura 3L/monoriel.

API actual: sólo cálculo y discovery para engine. Discovery NO devuelve
configuración completa. Ninguna fuente define un endpoint BFD/Inspector ni su
ubicación en el response SHOT-07. Alternativas pendientes PD26:

| Alternativa | Impacto normativo |
|---|---|
| A: ampliar calculate | Choca con siete claves y exclusión expresa del hash SHOT-06; requiere decisión de versionado/snapshot |
| B: endpoints de derivadas separados | Puede preservar cálculo/golden, pero falta ruta, request/response, validación y vínculo seguro con autoridades |
| C: funciones puras detrás del adapter | Válido como frontera interna; por sí solo no entrega datos al panel HTTP; debe definirse transporte |

Recomendación, **no decisión adoptada**: mantener intacto cálculo/BOM/hash
SHOT-06 y asociar resultados derivados mediante referencia al cálculo; decidir
transporte separado. No aceptar BOM/client config como autoridad sin validación
del adapter ni reutilizar datos de otro tenant. Si el server recalcula para
verificar un request, eso lo hace engine; nunca geometría dentro de Inspector.

La preimagen vigente es `{request,response_without_calculation_hash}`;
snapshot tiene `{request,response}`. Los tests afirman exactamente siete claves.
Inspector depende además de configuración/mediciones y BFD de stock/política de
sierra: ninguna fuente congela que deban entrar en esa identidad. **No cambiar
preimagen, golden o siete claves antes de resolver PD26.** El BOM_HASH documental
de PRD-06 incluye proyecto/revisión: es otro contrato futuro, no este hash.

## 11. Matriz Gate → input → authority → formula → expected → test

Los expected marcados pendientes no son tests vacíos aceptables. Deben quedar
numéricamente congelados con autoridad independiente antes de FASE 2. Las
filas R01–R14 de §7 completan esta matriz con 28 pruebas mínimas y fronteras.

| Gate / test futuro | Input | Autoridad / fórmula | Expected verificable |
|---|---|---|---|
| BFD-01 `test_bfd_proline_purchase_vs_workshop` | Pedido Proline exacto por aprobar | Gate de 5800 mm, catálogo PD01/02, ecuación PD06 | Barras de 5800 mm; SKU compra distinto; mismos cortes originales; qty_bars y distribución pendientes de fixture |
| BFD-02 `test_bfd_same_input_same_bytes` | Mismo multiconjunto con inputs/permutaciones de filas/orden DB | Clave y empate PD05 | Bytes/orden de grupos, barras y cortes idénticos; distinguir orden semántico autorizado |
| BFD-03 `test_bfd_kerf_one_and_many` | Una pieza y varias | k y N_cuts aprobados PD03 | K exacto incluyendo o excluyendo último corte según decisión; no multiplicador inventado |
| BFD-04 `test_bfd_head_tail_each_new_bar` | Dos barras nuevas; h distinto de t | PD04; U=L-h-t | Descontar cada extremo una vez según política; no usar stock entero por error |
| BFD-05 `test_bfd_capacity_boundary` | P+K=U; U+0.01; U-0.01 | PD03/04/06 | Exacto cabe; exceso no cabe; menor cabe; ninguna tolerancia float |
| BFD-06 `test_bfd_equal_piece_and_bar_ties` | Longitudes repetidas, dos residuales iguales | PD05 | Pieza y barra elegidas por claves aprobadas, no por inserción casual |
| BFD-07 `test_bfd_physical_groups` | SKUs/sistemas/colores/materiales/stock distintos | PD07 | No mezcla incompatible; refuerzos no adoptan parent SKU como compra |
| BFD-08 `test_bfd_conservation_and_outputs` | Barras completas y con remanente | L=h+t+P+K+remaining; PD08 | Sumas exactas; piezas/qty sin pérdida/duplicación; purchase_list distinta del cut plan |
| BFD-09 `test_bfd_no_offcut_side_effect` | BOM y stock puro | Constitución, regla 18 + instrucción owner | Mismo resultado sin DB; sin consulta/reserva/consumo/QR offcut_inventory |
| BFD-10 `test_bfd_invalid_or_oversize_stock` | SKU sin stock, L<=0, trimming incompatible, pieza mayor que barra | PD01/08/29 | Diagnóstico exacto; ninguna compra falsa ni partial success silencioso |
| INS-01…14 | Positivos/negativos y fronteras de §7 | Config por sistema + facts; PD10…25 | Finding de regla/severidad/target exactos; ausencia sólo cuando evaluada/satisfecha |
| SEM-01 `test_empty_complete_inspection_green` | Sin findings, evaluación completa | Owner / PRD07§3 | GREEN |
| SEM-02 `test_yellow_only` | Uno/varios YELLOW | Misma autoridad | YELLOW |
| SEM-03 `test_any_red_dominates` | RED mezclado con YELLOW y orden inverso | Misma autoridad | RED; production_allowed=false |
| SEM-04 `test_missing_authority_not_green` | Config/fact requerido ausente | PD25/29 | No GREEN por omisión; contrato de diagnóstico a aprobar |
| FIX-01 `test_fix_preview_apply_recalculate` | Fixture R06 u otro aprobado en PD28 | Target real+diff exacto | Preview sin mutar; clic cambia input; engine/Inspector reevaluados; finding cambia determinísticamente |
| FIX-02 `test_fix_failed_apply_rolls_back` | Error de recálculo/precondición | Transacción local PD28 | Inputs/resultados previos intactos; sin escritura DB |
| FIX-03 `test_fix_idempotent_or_stale` | Mismo diff dos veces | Semántica elegida PD28 | No segundo cambio ni cantidades acumuladas |
| FIX-04 `test_one_fix_leaves_other_red` | Dos RED; fix resuelve uno | PRD07 bloqueo / PD28 | RED restante mantiene bloqueo; no animación de éxito global falsa |
| UI-01 E2E Inspector | Mismo cálculo, ambos temas, teclado/clic | S07 resuelto PD27 | Finding humano, preview, aplicación real; sin segunda copia de EngineResult |
| UI-02 E2E bloqueo | RED y aprobación de taller | Semáforo | Control bloqueado; ninguna llamada a endpoint OT/órdenes |
| API-01 transporte y RLS | TenantA/B, inválido, catálogo faltante | PD26 + auth/RLS vigentes | Tipado Decimal, aislamiento, errores humanos; OpenAPI/Orval reproducibles |
| API-02 identidad | Mismo request/BOM con deriva de config/política | PD26 | Identidades separadas o versión aprobada; golden de SHOT-06 intacto por defecto |
| REG-01 G1–G7 | Fixtures actuales sin editar | PRD01 / tests existentes | Dimensiones con error 0.00 mm, kits/weights exactos; G7 incluye panel y umbral |
| REG-02 golden/hardware | Golden06 y tests de peso/fallback | Hash vigente / SHOT06 | Bytes idénticos; check read-only; 20/20 mutaciones Core anteriores |
| REG-03 diferidos | Manifest + tests strict xfail | PLAN_SHOTS | G8/G9/G11/G12→06B; G10→24; cinco xfails, sin reinterpretarlos como PASS |
| REG-04 Canvas/auth | E2E actual y fixtures adaptados sólo por contrato aprobado | SHOT04/05 | Cinco commits <300ms, snapping, rollback, MFA/RLS; no skip |

Pruebas nuevas de fórmulas deben matar perturbaciones ±0.01 mm en kerf/trims,
capacidad y thresholds pertinentes por assertions, no por SyntaxError/import.
Las expectations no se obtienen llamando a la misma implementación bajo test.
Comparar cortes BFD contra el multiconjunto de piezas exactas de entrada con
identidades aprobadas, no sólo count de barras. No se acepta «enum existe» como
cobertura Rxx ni esconder datos faltantes en xfails nuevos de SHOT-07.

## 12. Registro completo de decisiones

**28 pendientes activas**: PD-07-01…08 y PD-07-10…29.
**1 candidata resuelta por el alcance autorizado**: PD-07-09. Ninguna PD-06 se reabre.
«PENDIENTE» detiene construcción, no impide terminar esta auditoría solicitada.
Las referencias abreviadas PD01…PD29 de las matrices corresponden a PD-07-01…29.

| ID | Estado / evidencia / decisión necesaria |
|---|---|
| PD-07-01 | **[PENDIENTE-DECISIÓN]** PA tiene SKU técnico y commercial_length, no identidad/oferta de compra. Aprobar mapping, proveedor/fabricante, material/color/unidad, scope y autoridad de stock 5800. Aclarar DOC04 genérico 6000. |
| PD-07-02 | **[PENDIENTE-DECISIÓN]** Pro6004 sólo descripción privada/histórica; no fixture activo/SKU comercial/pedido. Entregar ficha o resolución literal con ambos SKU, piezas, política, resultado y aislamiento. Si sólo fixture de packing, delimitarlo sin certificar G-Pro1 ni copiar autoridades geométricas DEMO. |
| PD-07-03 | **[PENDIENTE-DECISIÓN]** Aprobar k, fuente, mm/precisión y N_cuts: por pieza/corte/entre piezas/último/trim/una pieza. PRD16 no aporta autoridad automática. |
| PD-07-04 | **[PENDIENTE-DECISIÓN]** Aprobar h y t por separado, aplicación a cada barra nueva e interacción con cortes; retazos fuera de SHOT-07. |
| PD-07-05 | **[PENDIENTE-DECISIÓN]** Aprobar sorting y todas las claves de empate/identidad, orden de grupos/barras/cortes, expansión qty. Propuesta en §5.3. |
| PD-07-06 | **[PENDIENTE-DECISIÓN]** Congelar ecuación usando PD03/04, convención used/usable/remaining y exact fit ±0.01; resolver ejemplo DOC05 de 310 versus 320. |
| PD-07-07 | **[PENDIENTE-DECISIÓN]** Congelar agrupación física y selección de oferta; cobertura acero y refuerzos con SKU NULL, color, sistema, orientación y stock. No mezclar categorías. |
| PD-07-08 | **[PENDIENTE-DECISIÓN]** Aprobar modelos separados compra/taller, índices, unidades/escala, fórmula waste_pct y error/oversize/empty input; sin partial success inventado. |
| PD-07-09 | **RESUELTA POR ALCANCE AUTORIZADO:** conservar remainder_mm permitido y usar la denominación neutral «remanente», sin inventario/QR/consulta de retazos. Clasificación y métrica waste siguen pendientes en PD-07-08. |
| PD-07-10 | **[PENDIENTE-DECISIÓN]** Aprobar modelo DB/config de todas las constantes R01–R14, defaults explícitos, overrides/prioridad por sistema, RLS/versionado y comportamiento cuando faltan. Reusar HK/GB, no duplicar. |
| PD-07-11 | **[PENDIENTE-DECISIÓN]** Resolver masa R01: PRD07 PVC+acero+vidrio versus SHOT06 PVC+acero+infill+kit exactos. Recomendación: consumir el exacto canónico de SHOT-06; no cambiarlo sin decisión. |
| PD-07-12 | **[PENDIENTE-DECISIÓN]** Elegir W/H únicos de R02 y política del target 1:1.5. Recomendación: finished exterior de geometría, nunca corte; transporte depende de PD25. |
| PD-07-13 | **[PENDIENTE-DECISIÓN]** Prioridad de límites R03 por sistema versus kit, dominios de apertura/medidas e infracciones previas al resultado. No reemplazar límites de kit ni duplicarlos sin semántica. |
| PD-07-14 | **[PENDIENTE-DECISIÓN]** Clasificación R04 monolítico/DVH/otras specs, área exacta, casos sin regla, paneles y alternativas de vidrio legítimas. thickness_net no basta. |
| PD-07-15 | **[PENDIENTE-DECISIÓN]** Autoridad completa R05: Ix y unidades, refuerzo/sección/espesor, luz/apoyos, presión/exposición/zona/altura, versión/fórmula NCh432/Ireq y expected independiente. Sin RF-HEAVY inventado. |
| PD-07-16 | **[PENDIENTE-DECISIÓN]** Matriz única ya identificada; falta contrato de finding R06 cuando helper falla antes de BOM y alcance de infill/panel bajo la regla. Selección de spec coherente para fix, sin segunda matriz. |
| PD-07-17 | **[PENDIENTE-DECISIÓN]** Input legítimo R07 de drenajes: ancho usado, qty inferior, posiciones/espaciado y fuente de medición/diseño. No inferir ausencia desde campo inexistente ni agregar BOM. |
| PD-07-18 | **[PENDIENTE-DECISIÓN]** Input R08 de posiciones ordenadas/path perimetral, distancia y cierre del ciclo. HK.contents.qty no aporta coordenadas. |
| PD-07-19 | **[PENDIENTE-DECISIÓN]** R09: ancho continuo/ensamble, presencia/tipo de acople y color/acabado. Autorizar o rechazar fixtures puros foliados sin ampliar API WHITE. |
| PD-07-20 | **[PENDIENTE-DECISIÓN]** R10: diseño versus medición real, dos observables y responsable; reconciliar 1.50 de Inspector con <=1.0 de DOC06 según dominio. Prohibido test tautológico. |
| PD-07-21 | **[PENDIENTE-DECISIÓN]** R11: dos superficies del gap 12±1.5 y derivación desde autoridad; demostrar si restablecer solape 8 resuelve ese gap. |
| PD-07-22 | **[PENDIENTE-DECISIÓN]** R12: autorizar input puro sintético 3L con Ix real/fixture aprobado independiente del dispatcher. G8 permanece en SHOT-06B; decidir aplicabilidad productiva sin geometría 3L. |
| PD-07-23 | **[PENDIENTE-DECISIÓN]** R13: H terminada/nominal, semántica compás doble versus stay_arms_qty, threshold por sistema y test negativo alcanzable con kit DEMO max H=1000. No crear kit alto. |
| PD-07-24 | **[PENDIENTE-DECISIÓN]** R14: fixture puro MONO sin G10, masa, número mínimo de carros, ruedas por carro, capacidad por rueda y catálogo requerido; no usar max_leaf_weight como capacidad por rueda. |
| PD-07-25 | **[PENDIENTE-DECISIÓN]** Contexto de facts exactos y diagnóstico antes de errores de kit/matriz; aplicabilidad por regla/datos faltantes. No recomputar geometría en Inspector, no redondeos públicos ni bypass de guards de SHOT-06. |
| PD-07-26 | **[PENDIENTE-DECISIÓN]** Elegir frontera API/hash A/B/C, modelos/errores, validación de autoridad y vínculo a cálculo/config. No cambiar golden de SHOT-06 sin decisión explícita. |
| PD-07-27 | **[PENDIENTE-DECISIÓN]** Resolver S07 modal versus panel dockable, contenedor/ruta y exposición BFD en UI sin S19/OT09 ni proyectos de SHOT-10. Conservar una navegación y un resultado compartido. |
| PD-07-28 | **[PENDIENTE-DECISIÓN]** Aprobar Finding/FixDiff, allowlist, precondiciones, orden, idempotencia/rollback y un fixture AUTO_FIXABLE de extremo a extremo. Resolver ANIM que fuerza GREEN tras cualquier fix frente a RED restante. |
| PD-07-29 | **[PENDIENTE-DECISIÓN]** Definir bloqueo ante config/facts faltantes y fallo/oversize BFD; relación con semáforo y production_allowed, y si BFD se calcula informativamente en RED. No inventar nueva R15 ni OT. |

## 13. Contradicciones conocidas y riesgos

**Sí hay contradicciones conocidas; construcción detenida.**

1. R01 omite kit/panel frente a la masa exacta aprobada en SHOT-06 (PD11).
2. «Todos los casos negativos de Inspector después de EngineResult» no es
   alcanzable con los rechazos actuales de hardware/matriz; contrato nuevo
   necesita resolver ese conflicto de flujo (PD16/25).
3. S07 modal/ruta abreviada versus dockable en jerarquía Canvas (PD27).
4. ANIM§4 fuerza transición a GREEN/desbloqueo tras un fix, pero cualquier RED
   restante debe bloquear según PRD07 y owner (PD28).
5. Ejemplo DOC05 no conserva longitud por 10 mm. Además, DOC04 describe barras
   de 6000 mm y el gate Proline exige 5800 mm: la longitud específica del gate
   prevalece; el formato documental no fija una longitud universal de BFD.
   El ejemplo no sirve como expectation sin resolver el balance (PD01/06).
6. R10 «diferencia teórica» no tiene segunda diagonal observable en rectángulos
   ortogonales; además control físico DOC06 tiene otra tolerancia (PD20).

Vacíos distintos de contradicción: fixture Proline incompleto, política de
sierra/empates, configuración DB, R05 sin fórmula NCh, R07/R08/R11 sin facts,
R12/R14 fuera del dispatcher actual, transporte/hash y fixes sin target válido.
No se levantan esos vacíos porque exista una fórmula textual o un enum.

Riesgos de integración: aceptar stale input, mezclar tenancies/SKU, devolver
GREEN incompleto, contabilizar soldadura dos veces, perder precisión al tomar
LeafWeight/área publicada, inventar refuerzo por SKU NULL, y superar 300 ms al
añadir cálculo/red. Cada riesgo tiene prueba en §11; ninguno justifica reducir
los gates históricos.

Anotaciones históricas de fuentes SHOT-06 (p.ej. PRD01 «runtime 23») no describen
el baseline actual: runtime/tests prueban 27 y el plan de SHOT-06 registra la resolución
27/22/2/3. Se trata como texto histórico de Fase 1, sin reabrir PD06 ni usarlo
para cambiar el modelo. Biblias/copias en `docs/` no sustituyen `docs/PRD/`.
El ejemplo de exportación Excel de PRD-06 §4 convierte Decimal a float, en
conflicto con la Constitución. Corresponde a documentos de SHOT-09; no se
reutiliza ese patrón ni se modifica esa fuente durante este plan de SHOT-07.

## 14. Secuencia propuesta para FASE 2, aún NO autorizada

1. Recibir resolución formal de las 28 PD activas y autorización
   **`APROBADO — EJECUTA`**. Completar todos los expected/fixtures pendientes y
   alinear las fuentes normativas afectadas antes de construir.
2. Congelar modelos de stock/config/facts/API y un fixture Proline legítimo;
   acordar el AUTO_FIXABLE y estrategia para diagnósticos de inputs inválidos.
3. Si el owner aprobó nueva autoridad DB, crear sólo migraciones nuevas y
   fixtures autorizados; test RLS, reset y upgrade/rollback. No tocar catálogo
   SHOT-06 para acomodar datos Proline ni añadir defaults geométricos ficticios.
4. Implementar proyección de facts exactos y piezas desde el cálculo existente,
   sin cambiar fórmulas ni identidad de SHOT-06 salvo decisión expresa.
5. BFD puro + contratos separados compra/taller + tests de capacidad/orden.
6. Inspector puro con una positiva/negativa real por R01…R14 y semáforo.
7. Adapter/API definido en PD26, OpenAPI→Orval generado, sin edición manual.
8. Panel/modal S07 resuelto y diff preview/apply/recalc/rollback sobre editor,
   ambos temas; ningún side effect de compras/OT/proyectos.
9. Ajustar exclusivamente guards TEMPORALES que prohíben literal `inspector`
   en OpenAPI/Canvas (`check_dod.py:371/433`) al alcance aprobado de SHOT-07. Mantener
   prohibiciones de hardcode G1, UUID discovery, duplicar resultado, float,
   skip/fail-open y todas las verificaciones de auth/golden de SHOT-06.
10. Extender Checker para matriz de SHOT-07 sin quitar las pruebas de SHOT-06, mutaciones 20/20,
    DB upgrade/RLS ni cinco diferidos. No declarar cierre por juicio del Maker.
11. Ejecutar gauntlet completo y cuatro contexts existentes hasta EXIT CODE 0
    real, sin warnings de suites. Commit/PR conforme a futura autorización;
    merge requiere orden humana específica.

## 15. CI y condición de parada de esta FASE 1

Conservar exactamente los contexts `Lint & Typecheck`, `Test Suite`,
`Frontend Build`, `Database Gate`; no quinto required context. Ruff/mypy/pytest,
Vitest, Playwright real, ESLint/TS/Prettier/build, golden read-only,
OpenAPI/Orval, clean Supabase, DB lint/pgTAP/integration/PostgreSQL 16 y upgrade
seguirán siendo checks reales de FASE 2. No se ejecutó gauntlet con generación
de artefactos para este plan; no se declara SHOT-07 aprobado ni cerrado.

Salida esperada de Git al entregar FASE 1:

```text
## shot-07
?? docs/plans/PLAN_SHOT-07.md
```

No commit, push, PR, código funcional, migración ni otro archivo normativo
modificado. Las únicas ejecuciones fueron lecturas/auditoría y regresión
existente sin cambios de fuentes. **DETENERSE aquí.** Esperar resolución de
Regla 0/20 y la orden humana **`APROBADO — EJECUTA`**.

</details>

## Resolución owner íntegra (fuente preservada)

```text
[RESOLUCIÓN CANÓNICA PD-07-01…PD-07-29 — SHOT-07]

La detención de FASE 1 fue correcta.

Quedan resueltas:

PD-07-01…08
PD-07-10…29

PD-07-09 permanece resuelta tal como fue documentada.

Incorpora íntegramente estas decisiones en:

`docs/plans/PLAN_SHOT-07.md`

y actualiza únicamente las fuentes normativas activas afectadas.

Después ejecuta nuevamente:

* Regla 0
* Regla 20
* `git diff --check`

Si no aparece otra contradicción normativa REAL:

APROBADO — EJECUTA FASE 2.

No implementar SHOT-06B.
No implementar SHOT-08.
No tocar G8/G9/G10/G11/G12.

---

# PRINCIPIO GENERAL SHOT-07

SHOT-07 NO recalcula geometría.

Flujo:

`request`
→ SHOT-06 geometry/weights/hardware
→ facts exactos
→ Inspector puro
→ BFD puro
→ adapter/API
→ S07

Inspector y BFD:

* Python puro;
* Decimal;
* deterministas;
* cero DB;
* cero Django;
* cero HTTP;
* cero filesystem.

DB sólo vive en adapter/repository.

---

# PD-07-01 — AUTORIDAD COMERCIAL BFD

NO crear una segunda autoridad de longitud de barra para perfiles.

Ya existe:

`profile_articles.commercial_length_mm`

Ésa permanece como autoridad única de:

`stock_length_mm`

para ProfileCut.

Añade tabla NUEVA:

`profile_purchase_mappings`

mínimo:

* id UUID
* profile_article_id UUID FK
* org_id UUID nullable
* commercial_sku VARCHAR
* manufacturer_name VARCHAR
* supplier_name VARCHAR nullable
* purchase_unit VARCHAR CHECK (`BAR`)
* is_active BOOLEAN
* created_at

Semántica:

# `profile_articles.sku`

SKU técnico / taller.

# `profile_purchase_mappings.commercial_sku`

SKU de compra/pedido.

Deben ser campos conceptualmente independientes.

No exigir que sean distintos para todo catálogo, pero el fixture gate de SHOT-07 DEBE demostrar:

`commercial_sku != workshop_sku`

Precedencia:

1. mapping tenant activo;
2. mapping global;
3. 0 mappings → `MissingStockAuthority`;
4. > 1 mappings efectivos → `AmbiguousStockAuthority`.

No first-match.

Material:

`profile_articles.material`

Color:

request técnico actual.

SHOT-07 productivo continúa únicamente WHITE donde el cálculo actual lo permite.

No habilitar foliados para BFD.

---

# REINFORCEMENT STOCK

Añade tabla NUEVA:

`reinforcement_articles`

mínimo:

* id UUID
* system_id UUID
* org_id UUID nullable
* parent_profile_article_id UUID
* sku VARCHAR
* commercial_sku VARCHAR
* name VARCHAR
* manufacturer_name VARCHAR nullable
* supplier_name VARCHAR nullable
* stock_length_mm NUMERIC(10,2)
* thickness_mm NUMERIC(6,2) nullable
* ix_cm4 NUMERIC(12,4) nullable
* purchase_unit VARCHAR CHECK (`BAR`)
* is_default BOOLEAN
* is_active BOOLEAN
* created_at

Esta tabla sirve para:

1. autoridad comercial del acero;
2. BFD de refuerzos;
3. `Ix` real de R05/R12.

NO mover la autoridad de masa de SHOT-06.

`profile_articles.steel_weight_kg_m`

sigue siendo autoridad de peso.

No crear una segunda masa en `reinforcement_articles`.

Un `ReinforcementPiece` sin `reinforcement_sku` puede resolverse mediante:

`parent_profile_article → reinforcement_articles.is_default`

sin modificar el EngineResult SHOT-06 ni su golden.

0 default:
`MissingStockAuthority`

> 1 default:
> `AmbiguousStockAuthority`

---

# PD-07-02 — FIXTURE PROLINE

El dato fuente confirmado es:

Proline Pro6004:
`stock_length = 5800.00 mm`

Los identificadores siguientes son FIXTURES INTERNOS SINTÉTICOS.

NO afirmar que son SKU reales del fabricante.

Fixture:

manufacturer:
`Proline`

workshop SKU:
`PRO6004-FRAME-DEMO`

commercial SKU:
`DEMO-PROLINE-PRO6004-BAR-5800`

supplier:
`DEMO-SUPPLIER`

material:
`PVC`

color:
`WHITE`

purchase unit:
`BAR`

stock:
`5800.00`

Piezas:

* 1006.00 ×4
* 806.00 ×2

Con contrato de kerf/trims aprobado abajo:

sum pieces:

`5636.00`

kerf:

`6 × 4.00 = 24.00`

trims:

`15.00 + 15.00 = 30.00`

consumed:

`5636 + 24 + 30 = 5690.00`

remainder:

`5800 - 5690 = 110.00`

Resultado canónico:

* purchase list → 1 barra
* commercial SKU → `DEMO-PROLINE-PRO6004-BAR-5800`
* workshop plan → `PRO6004-FRAME-DEMO`
* remainder → `110.00`

Test obligatorio que pruebe explícitamente que ambos SKU son distintos.

---

# PD-07-03 — KERF

Autoridad runtime:

`CuttingProfile.kerf_mm`

DEMO fixture:

`4.00 mm`

Regla:

cada pieza terminada consume EXACTAMENTE un kerf.

Por tanto:

`kerf_total = piece_count * kerf_mm`

Incluye:

* una sola pieza;
* última pieza de barra.

No existe kerf cero implícito.

Todos Decimal.

No hardcodear `4.00` dentro de BFD.

---

# PD-07-04 — DESPUNTES

Autoridad:

`CuttingProfile.head_trim_mm`
`CuttingProfile.tail_trim_mm`

DEMO:

`15.00`
`15.00`

Cada barra comercial NUEVA consume ambos exactamente una vez.

SHOT-07 NO consume offcuts.

Por tanto no existe todavía política diferente para retazo.

Eso pertenece a SHOT-24.

---

# CUTTING PROFILE DB

Añade tabla NUEVA:

`cutting_profiles`

mínimo:

* id UUID
* org_id UUID nullable
* code VARCHAR
* name VARCHAR
* kerf_mm NUMERIC(10,2)
* head_trim_mm NUMERIC(10,2)
* tail_trim_mm NUMERIC(10,2)
* is_default BOOLEAN
* is_active BOOLEAN
* created_at

Selección determinista.

Si se solicita code explícito:
debe existir exactamente uno visible.

Sin code:
exactamente un default efectivo.

0:
`MissingCuttingProfile`

> 1:
> `AmbiguousCuttingProfile`

No fallback oculto.

---

# PD-07-05 — BFD DETERMINISTA

Antes de empaquetar, expandir qty en unidades individuales con `piece_id` estable.

Orden Decreasing:

1. `length_mm` DESC;
2. `workshop_sku` ASC;
3. `source_position_id` ASC;
4. `bay_id` ASC;
5. `leaf_id` ASC;
6. `role` ASC;
7. `piece_id` ASC;
8. `unit_index` ASC.

Null:
cadena vacía únicamente para ordering.

Para cada pieza:

1. evaluar todas las barras abiertas compatibles;
2. calcular remainder DESPUÉS de insertar;
3. elegir el menor remainder no negativo;
4. empate → menor `bar_index`.

Si ninguna admite la pieza:
abrir barra nueva.

Orden final:

* barras por `bar_index`;
* cortes dentro de la barra por orden de inserción BFD.

NO depender de:

* set;
* hash;
* orden DB;
* dict incidental.

---

# PD-07-06 — ECUACIÓN EXACTA DE CAPACIDAD

Para una barra:

`usable_stock =
stock_length

* head_trim
* tail_trim`

Para N piezas:

`piece_consumption =
Σ(piece_length)

* N*kerf`

Cabe si:

`piece_consumption <= usable_stock`

Equivalentemente:

`remainder =
stock_length

* head_trim
* tail_trim
* Σ(piece_length)
* N*kerf`

Debe cumplirse:

`remainder >= 0`

Exact fit:

# `0.00`

PASS.

Overflow:

# `-0.01`

FAIL.

Under:

# `+0.01`

PASS.

---

# CORRECCIÓN DOCUMENTAL DOC-05 / PRD-06

El ejemplo publicado:

* 4×1006
* 2×806
* kerf acumulado 24
* head trim15
* tail trim15
* stock6000

produce:

`6000 -5636 -24 -15 -15 = 310`

Por tanto:

`Retazo Sobrante: 320 mm`

es un error aritmético documental.

Corrige a:

`310 mm`

No cambies la fórmula para producir 320.

No uses magic +10.

---

# PD-07-07 — AGRUPACIÓN FÍSICA

Una barra sólo puede compartir piezas con la MISMA autoridad física de stock.

Group key canónico:

* commercial_sku
* stock_length_mm
* material
* color
* cutting_profile_id

Workshop SKU permanece dentro de cada cut.

Dos workshop SKU distintos pueden compartir barra ÚNICAMENTE si el catálogo los mapea explícitamente al mismo stock comercial físico.

No inferir compatibilidad por:

* nombre;
* longitud;
* role;
* mismo sistema.

PVC ≠ ALUMINIUM ≠ STEEL.

Junquillos sólo comparten stock si su autoridad comercial lo dice explícitamente.

Refuerzos utilizan `reinforcement_articles`.

---

# PD-07-08 — OUTPUT BFD

Define modelos puros.

## CutPiece

* piece_id
* source_kind
* workshop_sku
* material
* color
* length_mm
* source_position_id nullable
* bay_id nullable
* leaf_id nullable
* role
* unit_index

## StockRule

* stock_authority_id
* workshop_sku
* commercial_sku
* manufacturer_name
* supplier_name nullable
* purchase_unit
* material
* color
* stock_length_mm

## CutPlacement

* piece_id
* workshop_sku
* sequence
* length_mm

## CutBar

* bar_index
* commercial_sku
* stock_length_mm
* head_trim_mm
* tail_trim_mm
* kerf_mm
* cuts
* kerf_total_mm
* productive_length_mm
* process_consumed_mm
* remainder_mm
* waste_mm
* yield_pct
* waste_pct

Definitions:

`productive_length = Σ cuts`

`process_consumed =
productive_length + kerf_total + head_trim + tail_trim`

`remainder =
stock_length - process_consumed`

`waste_mm =
stock_length - productive_length`

Así waste incluye:

* trims;
* kerf;
* remainder.

`yield_pct =
productive_length / stock_length * 100`

`waste_pct =
100 - yield_pct`

Outputs porcentuales:
4 decimales HALF_UP.

## PurchaseLine

* commercial_sku
* manufacturer
* supplier nullable
* stock_length_mm
* unit
* qty_bars

## CutOptimizationResult

* purchase_list
* workshop_cut_plan

NO mezclar ambas listas.

Errores tipados:

* MissingStockAuthority
* AmbiguousStockAuthority
* MissingCuttingProfile
* AmbiguousCuttingProfile
* PieceLongerThanUsableStock
* InvalidCutContract

Nada de string error crudo al usuario.

---

# PD-07-09 — REMANENTE

Confirmada.

`remainder_mm`

se presenta como:

`Remanente`

No:

* offcut inventory;
* QR;
* AVAILABLE;
* RESERVED;
* CONSUMED.

SHOT-24 mantiene toda esa semántica.

---

# PD-07-10 — CONFIGURACIÓN R01–R14

Añade tabla:

`inspector_rule_configs`

mínimo:

* id UUID
* system_id UUID
* org_id UUID nullable
* rule_id VARCHAR CHECK R01…R14
* params JSONB
* is_active BOOLEAN
* created_at
* updated_at

Unique por scope/system/rule.

Precedencia:

1. tenant;
2. global;
3. ninguno → `InspectorConfigurationError`.

Nunca hardcoded fallback silencioso en `inspector.py`.

Repository lee:

`params::text`

y parsea JSON con:

`parse_float=Decimal`
`parse_int=Decimal`

Define Pydantic model específico para cada R.

14/14 configs son obligatorias para un sistema apto para Inspector.

Malformed config:
FAIL CLOSED.

RLS patrón catálogo global/tenant existente.

---

# CONFIG DEMO R01–R14

## R01

No threshold duplicado.

Usa:
`selected_hardware.max_leaf_weight_kg`

## R02

* min ratio `0.4000`
* max ratio `2.5000`
* suggested ratio `1.5000`

## R03

* system min W `350.00`
* system max W `1600.00`
* system max H `2400.00`

## R04

* monolithic_4 max area `1.8000`
* DVH_4_ANY_4 max area `2.6000`

## R05

* span trigger `1800.00`

## R06

Sin threshold duplicado.
Usa glazing matrix.

## R07

* width trigger `800.00`
* required bottom drains `3`

## R08

* max closing point spacing `800.00`

## R09

* WHITE limit `4000.00`
* FOILED limit `3000.00`

## R10

* diagonal tolerance `1.50`

## R11

* expected chamber clearance `12.00`
* tolerance `1.50`
* suggested sash overlap `8.00`

## R12

* width trigger `4500.00`
* minimum Ix `45.0000 cm4`

## R13

* height trigger `1200.00`
* required stay arms `2`

## R14

* weight trigger `150.00 kg`
* required carriages `4`
* min carriage/wheel capacity `80.00 kg`

---

# INSPECTOR MODELS

Define:

`InspectorRuleId`
R01…R14.

`InspectorSeverity`
YELLOW / RED.

`RuleEvaluationStatus`

* PASS
* FAIL
* NOT_APPLICABLE
* MISSING_INPUT

`Fixability`

* AUTO_FIXABLE
* SUGGESTION_ONLY
* BLOCKED_MISSING_AUTHORITY

`InspectorFinding`

mínimo:

* rule_id
* severity
* title
* diagnosis
* risk
* recommendation
* fixability
* bay_id nullable
* leaf_id nullable
* fix nullable

`InspectorResult`

* status GREEN/YELLOW/RED
* production_allowed
* evaluations
* findings
* source_calculation_hash nullable

No raw exception en finding.

---

# PD-07-11 — R01 PESO

La fórmula antigua de PRD-07 queda sustituida por la autoridad ya congelada en SHOT-06.

Usa peso TOTAL MÓVIL EXACTO:

`ExactLeafWeight.total_weight_kg`

incluye:

* PVC;
* acero;
* vidrio/panel;
* hardware.

NO usar suma de componentes públicos redondeados.

NO excluir hardware.

Comparación:

`exact_total > selected_kit.max_leaf_weight_kg`

→ R01 RED.

Esto alinea Inspector con hardware resolver y elimina doble autoridad.

---

# PD-07-12 — R02 ASPECT RATIO

Usa:

DIMENSIÓN EXTERIOR TERMINADA DE HOJA.

Nunca:

* longitud de corte;
* vidrio;
* nominal global.

`ratio = finished_height / finished_width`

Si:

`ratio > max`
o
`ratio < min`

→ YELLOW.

Fix:

`SUGGESTION_ONLY`

No redimensionar arquitectura automáticamente.

La proporción 1:1.5 es recomendación, no mutación.

---

# PD-07-13 — R03 DIMENSIONES

Usa las mismas dimensiones exteriores terminadas.

Límite efectivo:

INTERSECCIÓN entre:

1. límites Inspector/system;
2. límites del kit seleccionado.

Para mínimos:

más restrictivo = máximo.

Para máximos:

más restrictivo = mínimo.

Ejemplo W:

`effective_min_w =
max(inspector_min_w, kit.min_w)`

`effective_max_w =
min(inspector_max_w, kit.max_w)`

H:

kit.min_h permanece autoridad de mínimo H.

`effective_max_h =
min(inspector_max_h, kit.max_h)`

Violación:
RED.

No copiar valores de hardware dentro de config Inspector.

---

# PD-07-14 — R04 VIDRIO

Área:

EXACTA:

`width_mm * height_mm / 1_000_000`

No usar `GlassPiece.area_m2` redondeada.

Panel:
NO participa.

Clasificación SHOT-07:

### MONOLITHIC_4

un único paño:
`4.00 mm`

limit:
`1.8000 m2`

### DVH_4_ANY_4

DVH con:

* pane1 4.00
* pane2 4.00

independientemente de chamber:

por ejemplo:

* 4-12-4
* 4-16-4

limit:
`2.6000 m2`

Esto es una decisión owner SHOT-07 para evitar que el chamber cree una segunda autoridad estructural de espesor.

Otro glass class sin límite configurado:

`MISSING_INPUT / BLOCKED_MISSING_AUTHORITY`

y NO se declara seguro silenciosamente.

RED para production readiness.

Fix:
SUGGESTION_ONLY.

No inventar catálogo de vidrio.

---

# PD-07-15 — R05 NCh432 / Ix

La referencia vigente pasa a:

`NCh432:2025 — Diseño estructural - Cargas de viento`

SHOT-07 NO implementa un solver de NCh432.

No tiene datos suficientes para calcular viento normativamente.

R05 es VERIFICADOR de un requisito estructural ya calculado.

Inputs:

* span_mm
* reinforcement_ix_cm4
* required_ix_cm4
* structural_basis

`reinforcement_ix_cm4`

proviene de:

`reinforcement_articles.ix_cm4`

`required_ix_cm4`

debe venir de una autoridad estructural externa/usuario/proyecto aprobada.

No derivarla desde:

* zona;
* altura;
* heurística;
* prompt.

Si:

`span <= trigger`

→ NOT_APPLICABLE.

Si:

`span > trigger`
y `required_ix_cm4` falta

→ MISSING_INPUT
→ RED
→ production_allowed=false.

Si:

`actual_ix < required_ix`

→ RED.

No afirmar:

`Cumple NCh432`

si sólo se comparó Ix sin cálculo estructural completo.

Texto humano:

“Falta la exigencia estructural de viento para verificar este travesaño.”

NO `RF-HEAVY` automático.

Fix:
BLOCKED_MISSING_AUTHORITY.

---

# PD-07-16 — R06 JUNQUILLO / INFILL

R06 se convierte en regla de compatibilidad de RETENCIÓN DE INFILL.

Aplica a:

* GlassPiece/request glass;
* PanelPiece/request panel.

Usa exclusivamente:

`glazing_bead_rules`

ya existente.

No segunda matriz.

Para vidrio:
usa `glass_thickness_mm` contractual del nodo.

Para panel:
usa `PanelRule.thickness_mm`.

Si no existe rule:

R06 RED.

Debe poder detectarse en preflight ANTES de que strict calculation termine en error.

Fix:

SUGGESTION_ONLY.

No cambiar automáticamente glass_spec sin catálogo de opciones.

---

# PD-07-17 — R07 DRENAJES

Input legítimo:

`WorkshopAnnotations.bottom_drain_holes_mm`

lista Decimal de coordenadas horizontales dentro del vano.

Regla:

si nominal/opening width:

`> width_trigger`

requiere:

`count >= required_bottom_drains`

Si datos no fueron proporcionados:

MISSING_INPUT YELLOW.

No bloquea producción por sí solo porque R07 es YELLOW.

## AUTO-FIX CANÓNICO SHOT-07

R07 será el fixture REAL de fix-1-clic.

Auto-fix sólo cuando:

* requiere 3;
* existen exactamente 2;
* no existe hole en center;
* `center = width / 2` es válido.

Diff:

`ADD_BOTTOM_DRAIN_HOLE(center)`

Después:

* apply local;
* recalculate engine;
* recalculate Inspector;
* R07 desaparece;
* calculation_hash geométrico permanece idéntico.

Si faltan 0 o 1:
SUGGESTION_ONLY.

No inventar posiciones laterales.

---

# PD-07-18 — R08 CERRADEROS

Input:

`closing_points_perimeter_mm`

coordenadas curvilíneas Decimal sobre perímetro de hoja.

Origen:

0 en esquina superior izquierda.

Sentido:

horario.

Rango:

`0 <= p < perimeter`.

Ordenar para evaluación.

Calcular todos los gaps consecutivos, incluido wrap-around:

`last → perimeter → first`.

Si max gap:

`> configured_max`

→ YELLOW.

Si no existen datos suficientes:

MISSING_INPUT YELLOW.

No derivar posiciones desde qty de hardware.

Fix:
SUGGESTION_ONLY.

No añadir herraje automáticamente.

---

# PD-07-19 — R09 DILATACIÓN

Input:

* `continuous_width_mm`
* `finish_class`
* `has_coupler`

# `continuous_width_mm`

ancho horizontal continuo no interrumpido por acople.

WHITE:

limit4000.

FOILED:

limit3000.

El producto SHOT-07 sigue fail-closed WHITE.

FOILED sólo puede usarse en tests puros de Inspector.

No habilitar cálculo foliado.

Si:

width > limit
y no coupler

→ RED.

Fix:
BLOCKED_MISSING_AUTHORITY.

Insertar un coupler modifica topología y queda fuera.

---

# PD-07-20 — R10 DIAGONAL

Se corrige la contradicción de “diagonal teórica”.

Una geometría ortogonal teórica no puede detectar una desviación real.

R10 pasa a significar:

`Tolerancia de diagonales MEDIDAS de marco`

Inputs:

`measured_d1_mm`
`measured_d2_mm`

Regla:

`abs(d1-d2) > tolerance`

→ RED.

R10 pertenece a:

`WORKSHOP_QC`

No al pre-cut DESIGN Inspector.

En DESIGN:

`NOT_APPLICABLE`

No fabricar una diferencia artificial desde geometry.

No afecta el gate pre-OT de SHOT-07.

Se implementa y prueba como rule pura para futura etapa de taller.

Fix:
SUGGESTION_ONLY.

---

# PD-07-21 — R11 HOLGURA DE CÁMARA

NO derivar desde `sash_overlap_mm`.

Añade autoridad explícita:

`profile_systems.chamber_clearance_mm`

NUMERIC(10,2)
NOT NULL para sistemas con Inspector.

DEMO synthetic:

`12.00`

R11 compara:

`chamber_clearance_mm`

contra:

`expected ± tolerance`

DEMO:

`12.00 ±1.50`

<10.50 o >13.50:
RED.

`8.00 sash overlap`

queda únicamente como recomendación textual.

No existe ecuación aprobada clearance↔overlap.

Por tanto fix:
SUGGESTION_ONLY.

---

# PD-07-22 — R12 SIN G8

R12 se implementa sobre `InspectorInput` puro.

Puede construirse fixture:

* opening_type=SLIDING_3L
* width=4600
* reinforcement_ix=44

sin ejecutar `calculate_geometry(SLIDING_3L)`.

Regla:

if width>4500
and ix<45

→ RED.

Positive:

ix=45 exact
→ PASS.

No tocar:

* G8
* geometry SLIDING_3L
* dispatcher.

Fix:
BLOCKED_MISSING_AUTHORITY.

---

# PD-07-23 — R13 AWNING

Usa:

finished leaf outer height.

Actual hardware fact:

`selected_kit.stay_arms_qty`

Si:

AWNING
and H>1200
and stays<2

→ YELLOW.

H=1200 exact:
PASS.

Current G6 sigue intacto.

Negative test:
InspectorInput puro.

No añadir nuevo kit.

Fix:
SUGGESTION_ONLY salvo que futuro catálogo tenga alternativa inequívoca.

---

# PD-07-24 — R14 SIN G10

No implementar monoriel geometry.

InspectorInput puro puede contener:

* rail_type=mono
* exact_leaf_weight_kg
* carriages_qty
* carriage_capacity_kg

Añade a hardware catalog/model:

`hardware_kits.carriage_capacity_kg`

NUMERIC nullable.

Para kits actuales dual:
NULL permitido.

R14 sólo exige valor cuando se activa.

Regla:

if mono
and weight>150:

* carriages >=4
* carriage_capacity >=80

Ambas deben cumplirse.

Si capacity falta:
MISSING_INPUT RED.

Pure tests:

* 150 exact → PASS
* 150.01 +3 carriages → FAIL
* 150.01 +4×79.99 → FAIL
* 150.01 +4×80 → PASS.

No G10.

Fix:
BLOCKED_MISSING_AUTHORITY.

---

# PD-07-25 — DIAGNÓSTICO ANTES DE RECHAZO

No debilitar strict calculate.

`/calculate/`

continúa fallando exactamente como SHOT-06 cuando el contrato es inválido.

Pero Inspector necesita diagnosticar algunos casos antes.

Refactoriza hardware a una función pura compartida:

`evaluate_hardware_candidates(...)`

que devuelve evaluaciones tipadas de cada kit:

* opening_match
* rail_match
* width_match
* height_match
* exact_total_weight
* weight_match

`resolve_hardware_kit()`

se convierte en wrapper STRICT sobre esa evaluación.

Así:

* calculation strict conserva comportamiento;
* Inspector reutiliza los mismos facts;
* no duplica matemática.

Cuando no hay kit:

si existe candidato opening/rail/dim pero falla sólo peso:
→ R01.

Si falla límites dimensionales:
→ R03.

Si existe >1 compatible:
`InspectorConfigurationError / AmbiguousHardwareKit`

NO fingir finding de usuario.

R06 se ejecuta en preflight antes de acceso estricto a bead.

Errores que no pertenecen R01–R14 siguen siendo errores de contrato HTTP tipados.

Nunca traceback al frontend.

---

# PD-07-26 — API / HASH

NO modificar:

`POST /api/v1/engine/calculate/`

Su response SHOT-06 continúa EXACTAMENTE:

* calculation_hash
* profile_cuts
* reinforcements
* glasses
* panels
* hardware_items
* leaf_weights

No inspector.
No BFD.

Añade:

`POST /api/v1/engine/inspect/`

y:

`POST /api/v1/engine/optimize-cut/`

Misma política:

* JWT
* org
* OWNER aal2
* RLS
* server authoritative catalog.

## Inspect

Puede recibir:

* mismo calculation request;
* workshop annotations;
* structural inputs;
* mode DESIGN / WORKSHOP_QC.

Si geometry resulta:

response incluye:

`source_calculation_hash`

igual al hash de calculate.

Si preflight bloquea antes:
nullable.

## Optimize-cut

Backend:

1. recibe calculation request;
2. calcula server-side;
3. carga purchase mappings/reinforcement stock/cutting profile;
4. convierte EngineResult → CutPiece;
5. BFD.

NO confiar en lista de cortes enviada por navegador.

Response incluye:

`source_calculation_hash`

No modifica el hash.

---

# CALCULATION HASH

`calculation_hash`

continúa identificando:

request técnico
+
geometry/BOM SHOT-06.

Inspector y BFD son DERIVADOS.

NO forman parte de su preimage.

NO crear nuevo golden.

`golden_example.json`

debe permanecer byte-identical.

Hash esperado durante SHOT-07:

`sha256:562cdc97337a690f09db12590ee8a99b420ebc6b7dbf9c40a4d4755132d24f21`

salvo que una regresión real demuestre un bug, en cuyo caso STOP antes de tocarlo.

---

# PD-07-27 — S07

La Screen Specification ya resuelve esto.

S07 es:

MODAL

dentro de:

`/projects/:id/positions/:posId/edit`

No crear route `/inspector`.

En demo actual:
usar la superficie de editor vigente SHOT-05.

Modal S07 con dos secciones/tabs:

1. `Inspector`
2. `Corte 1D`

## Inspector

* semáforo
* findings
* diagnosis
* risk
* recommendation
* fix CTA cuando aplica.

## Corte 1D

Separar visualmente:

`Pedido`
de
`Plan de corte de taller`

Mostrar:

* commercial SKU en pedido;
* workshop SKU en cortes;
* barras;
* cuts;
* kerf;
* trims;
* remanente.

No mezclar stores.

TanStack Query:
remote Inspector/BFD.

Zustand:
únicamente estado editable local:

* technical inputs;
* annotations;
* preview diff.

No duplicar EngineResult.

---

# CORRECCIÓN PRD-ANIMATIONS §4

La especificación actual fuerza:

RED → GREEN
y desbloquea siempre el botón.

Eso es incorrecto cuando quedan otros findings.

Sustituir por:

1. fix aplicado → pulso visual 300ms;
2. engine + Inspector se recalculan;
3. semáforo anima:
   `previous_status → recomputed_status`;
4. puede quedar:

   * RED
   * YELLOW
   * GREEN;
5. botón depende exclusivamente de `WorkshopReadiness`.

PROHIBIDO forced GREEN.

PROHIBIDO forced unlock.

---

# PD-07-28 — FIX / DIFF

Define:

`InspectorDiff`

* diff_id
* rule_id
* target
* preconditions
* operations

Operations son discriminated union.

NO generic arbitrary JSON Patch sobre todo el proyecto.

SHOT-07 mínimo permite:

`ADD_BOTTOM_DRAIN_HOLE`

para R07.

Cada op contiene:

* target
* old_value
* new_value

Flow:

1. Inspector genera fix;
2. frontend preview;
3. usuario clic explícito;
4. validar preconditions contra estado vigente;
5. aplicar a draft local;
6. POST calculate;
7. POST inspect;
8. si ambos success:
   commit local;
9. si cualquiera falla:
   rollback exacto.

Idempotencia:

reaplicar el mismo diff:
no duplica drain hole.

Si precondition dejó de cumplirse:
FAIL y cero mutación.

No DB.

No project persistence.

No OT.

---

# FIX TAXONOMY SHOT-07

## AUTO_FIXABLE

R07:
condicional al fixture exacto aprobado.

## SUGGESTION_ONLY

* R02
* R03
* R04
* R06
* R08
* R10
* R11
* R13

## BLOCKED_MISSING_AUTHORITY / FUTURE TOPOLOGY

* R01 cuando requiere kit superior/división
* R05
* R09
* R12
* R14

Esta clasificación puede ser más conservadora que el texto histórico.

Eso es intencional.

NO inventar catálogo para habilitar botones.

---

# PD-07-29 — BLOQUEO DE PRODUCCIÓN

Inspector:

GREEN:
no FAIL.

YELLOW:
sólo findings YELLOW.

RED:
al menos un finding RED.

`production_allowed`:

FALSE si existe RED.

TRUE para GREEN/YELLOW conforme PRD-07.

Pero el estado global del editor necesita además BFD.

Define:

`WorkshopReadiness`

conceptualmente:

`inspector.production_allowed`
AND
`cut_optimization.ok`

Si:

* stock authority missing;
* cutting profile missing;
* piece cannot fit;
* stock ambiguity;
* Inspector configuration invalid;

entonces:

`WorkshopReadiness=false`

sin cambiar artificialmente el semáforo Inspector.

SHOT-07:

“Aprobar para Taller”

es únicamente GATE DE UI.

NO crea:

* order;
* WORKSHOP_OT;
* project status;
* version.

Persistencia real futura conserva sus shots.

---

# MISSING INPUT SEMANTICS

Para regla RED aplicable:

required input missing
→ MISSING_INPUT
→ finding RED
→ production_allowed=false.

Excepto R10:
en DESIGN es NOT_APPLICABLE porque pertenece WORKSHOP_QC.

Para regla YELLOW:

missing observational input
→ MISSING_INPUT YELLOW.

No bloqueo duro.

---

# DB CHANGES AUTORIZADOS SHOT-07

Migraciones NUEVAS únicamente.

No modificar históricas.

Como mínimo:

1. `profile_purchase_mappings`

2. `reinforcement_articles`

3. `cutting_profiles`

4. `inspector_rule_configs`

5. `profile_systems.chamber_clearance_mm`

6. `hardware_kits.carriage_capacity_kg`

7. RLS global/tenant correspondiente.

No tocar:

* price tables;
* orders;
* offcuts.

---

# SEED

DEMO_60 puede recibir:

* chamber_clearance 12.00;
* 14 inspector configs;
* cutting profile DEMO 4/15/15;
* synthetic purchase mappings para artículos existentes;
* synthetic reinforcement stock mappings.

Todo nuevo dato sin ficha:

`DEMO_60 SYNTHETIC FIXTURE`

No presentarlo como fabricante real.

El fixture Proline del gate puede vivir en tests/integration fixture.

NO publicarlo como catálogo real de Proline.

---

# G1–G7

Todos siguen EXACTAMENTE iguales.

Inspector/BFD no pueden modificar:

* cut lengths;
* glass;
* panel;
* hardware selection;
* exact weight;
* calculation_hash.

G7 continúa 0.00 mm.

---

# R01–R14 TEST MATRIX

Cada regla necesita:

* PASS
* FAIL

y cuando aplique:

* exact boundary;
* missing input.

## R01

max exact pass / +0.01 fail.

## R02

0.4 exact pass
2.5 exact pass
fuera fail yellow.

## R03

system vs kit intersection.

## R04

area exact boundary.

## R05

span1800 exact N/A/pass;
1800.01 with missing Ireq red;
Ix exact equal pass;
-0.0001 fail.

## R06

glass supported/pass;
glass missing/fail;
panel supported/pass;
panel missing/fail.

## R07

width800 exact no requirement;
800.01 +2 holes fail;
one-click center → pass.

## R08

800 exact pass;
800.01 fail.

## R09

4000 white exact pass;
4000.01 white no coupler fail;
3000 foil exact pass in pure fixture.

## R10

DESIGN N/A;
WORKSHOP QC d1/d2 diff1.50 pass;
1.51 fail.

## R11

10.50 pass;
13.50 pass;
10.49/13.51 fail.

## R12

4500 exact N/A;
4500.01 ix45 pass;
44.9999 fail.

## R13

1200 exact no double requirement;
1200.01 stays1 fail;
stays2 pass.

## R14

150 exact no requirement;
150.01 3 cars fail;
4×79.99 fail;
4×80 pass.

---

# BFD TESTS

Obligatorios:

* Proline5800 fixture → one bar, remainder110;
* commercial SKU != workshop SKU;
* deterministic repeated run;
* shuffled input produces same canonical output;
* exact fit;
* +0.01 overflow;
* -0.01/space available;
* one piece = one kerf;
* last piece consumes kerf;
* trims once per bar;
* best-fit choice;
* tie lowest bar index;
* no material mixing;
* no color mixing;
* separate PVC/ALUMINIUM/STEEL;
* MissingStockAuthority;
* AmbiguousStockAuthority;
* PieceLongerThanUsableStock;
* purchase list distinct from cut plan;
* no offcut mutation.

---

# FIX TEST

Fixture:

width:
`1000.00`

existing drains:
exactly 2 valid positions.

center absent.

Inspector:
R07 YELLOW.

Preview:
one `ADD_BOTTOM_DRAIN_HOLE(500.00)`.

Apply.

Re-run calculate:
same calculation_hash.

Re-run Inspector:
R07 PASS.

Second apply:
no duplicate / precondition fails safely.

Failure in calculate/inspect:
rollback original two holes.

---

# API / FRONTEND TESTS

Inspect:

* auth/org/aal2;
* RLS;
* human errors;
* source hash.

Optimize:

* server calculates cuts;
* client cannot forge cut length;
* purchase vs workshop SKU.

S07:

* modal, not route;
* Light/Dark;
* RED remains RED after fix if another red exists;
* RED→YELLOW valid;
* RED→GREEN valid only if truly recomputed;
* approve button derives WorkshopReadiness;
* no raw exception.

---

# GOLDEN / HASH

Mandatory regression:

`make goldgen` NO debe ejecutarse para reescribir snapshot.

Usar:

`--check`

Debe seguir byte-identical.

Hash:

`sha256:562cdc97337a690f09db12590ee8a99b420ebc6b7dbf9c40a4d4755132d24f21`

---

# DEFERRED

Mantener:

G8 → SHOT-06B xfail
G9 → SHOT-06B xfail
G10 → SHOT-24 xfail
G11 → SHOT-06B xfail
G12 → SHOT-06B xfail

R12/R14 unit fixtures NO cambian esos estados.

---

# CI

Exactamente cuatro contexts:

* Lint & Typecheck
* Test Suite
* Frontend Build
* Database Gate

No quinto required context.

Integra Inspector/BFD tests dentro de los existentes.

---

# IMPLEMENTATION ORDER

1. incorporar estas PD al plan;
2. actualizar PRD-01;
3. actualizar PRD-07;
4. corregir PRD-06 320→310;
5. actualizar ANIM forced-GREEN;
6. actualizar FRONTEND/API boundary;
7. Rule 0;
8. migraciones nuevas;
9. RLS/DB gate;
10. loaders/models;
11. BFD puro;
12. BFD tests;
13. Inspector models/config;
14. R01–R14;
15. hardware candidate evaluator shared;
16. preflight R06;
17. API inspect;
18. API optimize-cut;
19. OpenAPI/Orval;
20. S07 modal;
21. R07 typed fix;
22. regression G1–G7;
23. golden --check;
24. five xfails;
25. mutation/targeted guards appropriate;
26. full suites;
27. `python scripts/check_dod.py all`;
28. commits;
29. PR protegido;
30. four required CI;
31. NO MERGE.

---

# STOP CONDITIONS

Detente únicamente si aparece una contradicción normativa NUEVA real.

No crear nuevas PD por:

* bug ordinario;
* import;
* formatting;
* typing;
* selector CSS;
* fixture roto;
* test implementation issue.

Si aparece una verdadera ausencia de autoridad:

`[PENDIENTE-DECISIÓN]`

y detente.

---

# ENTREGA FASE 2

Reporta:

* HEAD;
* commits;
* PR;
* migrations;
* RLS;
* BFD Proline result;
* purchase SKU vs workshop SKU;
* kerf/trims;
* DOC-05 310 correction;
* stock/reinforcement authority;
* R01…R14 individual;
* NCh432 verification boundary;
* missing-input behavior;
* semaphore;
* production_allowed;
* WorkshopReadiness;
* R07 fix diff;
* rollback/idempotence;
* S07 modal;
* animation recomputed status;
* API inspect/optimize;
* hash boundary;
* golden unchanged;
* G1–G7;
* five xfails;
* backend;
* engine;
* frontend;
* Playwright;
* DB Gate;
* gauntlet;
* four CI jobs;
* warnings;
* active `[PENDIENTE-DECISIÓN]`;
* contradictions known;
* git status.

NO MERGE.

APROBADO — EJECUTA FASE 2.
```
