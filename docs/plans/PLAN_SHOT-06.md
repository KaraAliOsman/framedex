# SHOT-06 — Plan actualizado y reauditoría Regla 0 / Regla 20

**Estado: FASE 2 AUTORIZADA EN EJECUCIÓN.**
**Regla 0 / Regla 20 revalidadas: cero contradicciones conocidas y cero pendientes abiertos.**
La autorización `APROBADO — EJECUTA FASE 2` es condicional a no encontrar nuevos vacíos
reales. PD-06-19/20 fueron resueltas explícitamente; fuentes activas actualizadas antes de construir.
Las PD numeradas a continuación siguen la numeración de la resolución del owner,
que sustituye la numeración temática del borrador inicial. Se conserva íntegra la
resolución recibida en el apéndice. El antiguo hallazgo del request (PD-18 inicial)
queda resuelto expresamente por PD-16 del owner.

## 1. Baseline y escritura autorizada

| Evidencia | Resultado |
|---|---|
| Repositorio | C:\Users\alios\Downloads\dekopen |
| Base | main @ fa3616fda9645bda5092e7c0cb9de80ecd8495b9 |
| Commit base | docs(shot-05): close execution status (#13) |
| Sync antes de rama | git fetch origin exitoso; HEAD/main/origin/main y ls-remote main idénticos |
| Estado inicial | git status --porcelain vacío, índice/árbol limpios |
| Rama | shot-06 creada desde SHA exacto mediante git switch -c; no existía local/origin |
| Single Writer | Codex único escritor; sin subagentes/checkouts adicionales |
| Fase 1 inicial | Creación exclusiva del plan |
| Autorización posterior | Incorporar resolución y corregir fuentes activas antes de Regla0 y Fase2 condicional |
| Archivos documentales actualizados | Este plan; docs/PRD/PRD-01.md, PRD-02.md, PRD-05.md, PRD-FRONTEND-APIS-COMPONENTS.md |
| Código/DDL ejecutable/seed/tests | Fase 2 en implementación; inventario y evidencia actuales en §13 |
| Commit/push/PR/merge/tag | Sin commits/push/PR todavía; NO MERGE |

## 2. Autoridad y lecturas, en orden

1. AGENTS.md completo.
2. docs/CONSTITUTION.md completo.
3. docs/PRD/PLAN_SHOTS.md, especialmente SHOT-06 §4; autoridad temporal.
4. docs/PRD/PRD-01.md completo (baseline493 líneas).
5. docs/PRD/PRD-02.md: principios, catálogos, autoridad y RLS.
6. docs/PRD/PRD-FRONTEND-APIS-COMPONENTS.md completo.
7. Runtime engine/src/dekopen_engine: models,geometry,glass,bom,__init__, completos.
8. Backend engine_api: adapter,repository,serializers,views completos.
9. Las dos migraciones existentes completas.
10. supabase/seed.sql completo.
11. engine/tests/GOLD_CASES_MANIFEST.json completo.
12. Tests core/deferred y conftest G1–G4 completos.

Después: contratos previos SHOT-03/04/05, PRD-04 árbol, F1, Makefile/scaffold,
Checker/CI y tests API/modelos/pureza/Canvas. Para resolución: PRD-05 completo.
No se buscó ficha de fabricante para sustituir autoridad ficticia DEMO_60.
Toda incorporación sintética se etiqueta DEMO_60 SYNTHETIC FIXTURE; no representa
ficha oficial Vorne/Roto/Winkhaus. El display name Vorne OB es mapping explícito del owner.

## 3. Core, Extended y arquitectura

Core: SLIDING_2L, AWNING, DOOR_ENTRY; hardware general y G3 real; peso/fallback;
primitives pricing; golden generado+hash+bytes. G5/G6/G7 a0.00 mm. G1–G4 geometría
intacta, Canvas G1/discovery/auth/RLS/Gauntlet preservados.
G8/G9/G11/G12 permanecen strict xfail hacia SHOT-06B; G10 manifest xfail→SHOT-24.
No Inspector/BFD (SHOT-07), no comercial SHOT-08, no cleanup/reapertura SHOT-05.
G10 no tiene un test pytest dedicado en baseline: su xfail existe en manifest/Checker;
no afirmar ejecución de un test inexistente.

Upstream: catálogo/RLS02, motor03, adapter/auth04, Canvas/discovery05.
Downstream: Inspector/BFD07 consume piezas y masas; comercial08 consume BOM/primitives;
09/10 consumen snapshots/hash para documentos/versiones;06B reutiliza contratos.

```text
HTTP/JWT/org/RLS → loader de autoridades Decimal → adapter de árbol
→ geometría pura → base de masa exacta por hoja sin kit
→ candidatos por finished W/H/opening/rail/SKU → masa exacta con cada kit
→ kit compatible único → BOM/panels/hardware/leaf_weights
→ hash puro(request, response sin hash) → response HTTP

Generador externo a runtime matemático: request+autoridades fixture → mismo motor
→ snapshot bytes. CI --check compara en memoria, nunca escribe.
```

Engine sin Django/DB/red/I/O/float. Writer en engine/scripts; módulos matemáticos en
engine/src/dekopen_engine (weight.py/pricing.py, conforme layout real).
SystemParams previsto27 campos:23 anteriores+3 PS+available_panel_rules por SKU.
Modelos: material en EffectiveProfileArticle/ProfileCut; rolTHRESHOLD; pesos autoridad
Optional; HardwareComponent/HardwareItem tipados anidados; PanelRule/PanelPiece;
LeafWeight; leaf_id nullable; ParametricNode.panel_article_sku obligatorio DOOR_ENTRY.
G5 leaf IDs <bay_id>:L1/L2 izquierda→derecha; hojas únicas conservan null donde no necesario.
Runtime baseline todavía23 campos: 27/27 es cobertura de diseño normativo, no implementación.

## 4. Resoluciones incorporadas y contratos

| PD owner | Contrato vigente |
|---|---|
| 01 | PS.sliding_glazing_deduction_width_mm/height_mm=20.00/20.00, totales por eje, NOT NULL; finished=cut-soldadura del artículo; baseglass840/1830 menos20→820/1810. No hardcode ni bead especial |
| 02 | G5 WHITE,2000×2100,SLIDING_2L,glass20/spec4-12-4 Float Incoloro,dual; dos hojas L1/L2; frame2006/2106; acero1970/2070; sash966/1956; acero930/1920; vidrio820×1810; beads829/1819. Qty2 H/V por hoja; frame qty2 H/V; hardware finished960×1950 |
| 03 | AWNING comparte primitive single_rectangular_sash_geometry TURN/TILT_TURN; G6 WHITE1200×800,glass20/spec4-12-4 Float Incoloro; frame1206/806/acero1170/770; finished1096×696; sash1102/702/acero1066/666; glass976×576; beads985/585 |
| 04 | KIT-AWNING-16, Kit Proyectante Compás16 pulgadas45kg; rangos y contents sintéticos exactos en apéndice/PRD01; stay arms2; weight2.50 |
| 05 | Puerta: cabezal dos extremos soldados, jambas uno; head956 qty1 45/45, jamb2153 qty2 45/90; acero920/2120; umbral830; PS.door_leaf_side_clearance7.00; leaf816×2048; sash822/2054 y acero786/2018; panel696×1928 |
| 06 | THRESHOLD; PA.material; UMBRAL-ALU aluminio/cara30/soldadura0/gap0/sin acero. ProfileCut material real; umbral no pesa en hoja |
| 07 | infill_articles y panel_article_sku; PANEL-SANDWICH-DEMO-24,24mm,10.0000kg/m² sintéticos; PanelPiece área exacta1.341888→1.3419 y masa13.41888→13.42 |
| 08 | KIT-DOOR-MULTIPOINT; límites/contents sintéticos; DEMO-LOCK-MULTIPOINT qty1 unit; peso2.50; no inventar más componentes |
| 09 | HardwareItem por kit/hoja, qty int1,unit kit,kit_sku,name,bay_id,leaf_id,contents HardwareComponent; qty componente Decimal; no flatten y orden persistido |
| 10 | Matching finished W/H+opening+rail; por candidato base exacta+kit; SKU explícito validado; cero→NoCompatibleHardwareKit; uno→seleccionar; múltiple→AmbiguousHardwareKit |
| 11 | KIT-TILT-TURN mismo SKU, display Kit Vorne OB100kg; G3 xfail debe resolverse. PD-19 corrige peso standalone a33.29, golden OB conserva26.55 |
| 12 | Masa SASH/cortes y acero con qty/peso lineal; infill exacto; kit candidato; total exacto para matching. LeafWeight outputs2 HALF_UP; no doble redondeo |
| 13 | Factor1.10 sólo fallback: PVC/steel; noPVC sin masa falla; panel sin masa falla; None en autoridad interna; no encima de persistido |
| 14 | HK.weight_kg nullable, todos cinco kitsDEMO2.50; NULL→2.50×1.10=2.75 y used_fallback=true |
| 15 | price_from_cost_and_margin=cost/(1-margin),cost>=0,0<=margin<1,output2 HALF_UP; gross_margin_pct=(price-cost)/price,output4;100000/35%→153846.15; sin DB/API/comercial |
| 16 | Request UUID real+POSTE-V; hash SHA256 request+response sin hash, JSON compacto ordenado, prefijo sha256:; snapshot envelope request/response indent2 LF; make goldgen escritor, --check CI sólo lectura |
| 17 | Response hash/profile_cuts/reinforcements/glasses/panels/hardware_items/leaf_weights; panels[] en golden; OB total26.55; sin inspector; OpenAPI/Orval; Extended intacto |

Tabla de pesos exactos/publicados, con SASH+acero+infill+kit (sin marco/mullion/umbral/beads):

| Caso | PVC | Steel | Infill | Kit | Total exacto | Publicado |
|---|---|---|---|---|---|---|
| G3 según fórmulas |5.2896|7.2488|18.25152|2.50|33.28992|33.29 aprobado |
| G5 por hoja |7.0128|9.6900|29.6840|2.50|48.8868|48.89 |
| G6 |4.3296|5.8888|11.24352|2.50|23.96192|23.96 |
| G7 |6.9024|9.5336|13.41888|2.50|32.35488|32.35 |
| Golden OB |4.7376|6.4668|12.84192|2.50|26.54632|26.55 |

## 5. Nueva auditoría Regla0/20

### PD-06-19 — RESUELTA: peso G3 y golden compuesto

G3 standalone: PVC5.2896+steel7.2488+glass18.251520+hardware2.500000=33.289920→33.29.
Golden compuesto bay_2: PVC4.7376+steel6.4668+glass12.841920+hardware2.500000=26.546320→26.55.
Tests independientes; comparación exacta con max100.00; KIT-TILT-TURN / Kit Vorne OB100kg.
La expectativa histórica26.55 para G3 queda revocada por la nueva resolución al final.

### PD-06-20 — RESUELTA: junquillos de panel G7

G7 sí lleva beads705.00/1937.00 qty2. Fórmula neutral infill_length+rule.cut_add_mm;
PanelRule.thickness_mm24.00 selecciona GB24/JQ-10 sin hardcode. Se conserva columna
histórica glass_thickness_mm con semántica espesor de infill retenido. Beads son
ProfileCut GLAZING_BEAD con bay_id/leaf_id; panel sigue PanelPiece sin glass_spec ni
densidad de vidrio. Beads no suman a masa de selección hardware32.35. No nueva columna.

Reauditadas las fuentes actualizadas contra la resolución: cero pendientes abiertos;
la diferencia de pesos y el montaje del panel quedan resueltos sin cambiar G1–G5.
Operadores puerta se desarrollan desde ejemplos numéricos explícitos aprobados.

## 6. Golden, CI y validación futura

Request exacto en apéndice/PRD-FRONTEND: DEMO_60 UUID3067da09-3119-5ad0-a1d5-498cd2dfd753,
1500×1400,WHITE,SPLIT_V750,POSTE-V,children fixed24/spec4-16-4 y OB20/spec4-12-4.
Hash de {request,response_without_calculation_hash}, UTF8,sort_keys,ensure_asciiFalse,
separators comma/colon sin espacios ni LF,arrays engine,Decimal strings; sha256:<hex64>.
Snapshot final {request,response con hash},indent2,sort_keys,ensure_asciiFalse,UTF8 LF,
exactamente un LF final. Writer sólo make goldgen; --check en memoria, CI no reescribe.
Orden piezas estable por roles/recorrido, H/V y hojas L1/L2; contents orden catálogo.
Misma función serializadora pura para generador/test/API; no redondear para esconder drift.

Checker actual exige G5–G7pending/G3xfail y prohíbe hash en OpenAPI: actualizar guard
acotadamente a SHOT-06 después de resolver normas, conservando auth/RLS/Canvas e
inspector prohibido. No basta cambiar manifest; debe exigir tests reales recogidos,
fallos ante mutación, snapshot generado y no modificarlo en CI. G1FIXED hardware[];
G2/G3/G4 sólo actualizan expectativa temporal hardware, nunca geometría.
Guard de23 campos y cardinalidad catálogo se actualizan a contrato real, no se eliminan.
El test422 que usaSLIDING_2L debe pasar a una tipología todavía diferida.

## 7. Matriz Gate → fórmula → autoridad → fixture → test → evidencia

Tests marcados nuevos son planificados; no se ejecutaron suites/Gauntlet en esta entrega.
Nombres son identificadores previstos dentro de engine/tests salvo ruta explícita.

| Gate | Fórmula/invariante | Autoridad | Fixture | Test | Evidencia requerida |
|---|---|---|---|---|---|
| G1 |1006/970,glass910²,bead919|PRD01§4/6|g1_node existente|test_g1_fixed_is_exactly_zero_mm|Existente leído; reejecutar0.00|
| G2 |sash702/1102,steel666/1066,glass576×976|PRD01|g2_node|test_g2_turn_is_exactly_zero_mm|Geometría intacta|
| G3 geometry |sash902/1302,glass776×1176|PRD01|g3_node|test_g3_tilt_turn_geometry_is_exactly_zero_mm|Mismas expectativas|
| G4 |poste1380/1370,glass830×1410+696×1276|PRD01|g4_node|test_g4_fixed_tilt_turn_with_mullion_is_exactly_zero_mm|Mismos IDs/qty/valores|
| G3 hardware |KIT-TILT-TURN/name/max100,total33.29|PD11+19|G3+kit real|Nuevo test_g3_hardware_contract|Prueba real de total exacto33.289920 y output33.29|
| G5 |contratoPD01/02,48.89 por hoja|Resolución owner|G5 completo|Nuevo test_g5_complete_bom_exact|Todas piezas/qty/IDs/ángulos/kit/peso0.00|
| G6 |contratoPD03/04,23.96|max45/owner|G6 completo|Nuevo test_g6_complete_bom_exact|Primitive común,herraje16 pulgadas|
| G7 |contratoPD05–08,32.35|Owner+PD20|G7/panel/threshold|Nuevo test_g7_complete_bom_exact|head/jamb extremos,material/no steel,panel no glass|
| Hardware normalize |mappings sin habilitar Extended|PD10|Tabla de tipos|Nuevo test_normalize_opening_type|Exact mapping|
| SKU explícito |validar todas restricciones|PD10|SKU válido/inexistente/incompatible|Nuevo test_explicit_hardware_set_sku|Success/failure deterministas|
| 0/1/>1 kits |no first-match|PD10|Catálogos permutados|Nuevo test_hardware_cardinality|NoCompatible/Ambiguous exactos|
| Límites kits |finished W/H,peso exacto con candidato|PD10|Fronteras dimensión/peso|Nuevo test_hardware_candidate_boundaries|Rechazo dimensiones/peso; inclusividad±0.01|
| Peso autoridad |persistido prevalece|PD12/13|Artículos de pesos distintos|Nuevo test_weight_authority_precedence|Sin fallback indebido|
| FallbackPVC/acero |sólo fallback×1.10|PD13|Autoridades None puras|Nuevo test_profile_steel_fallback|used_fallback true; noPVC falla|
| Peso kit |persistido2.50;NULL2.75|PD14|Kit masa2.50/None|Nuevo test_hardware_weight_fallback|Persistido prevalece;capacidad con candidato|
| Panel |área exacta×peso,ausenteFAIL|PD07/13|Panel masa10/None|Nuevo test_panel_weight_authority|13.41888→13.42;MissingWeightAuthority|
| No doble redondeo |sum exacta antesHALF_UP|PD12|Casos de frontera|Nuevo test_leaf_weight_no_double_rounding|Masa pública no usada para matching|
| Door extremos |head2/jamb1/threshold0|PD05/06|G7 y variante artículo|Nuevo test_door_welded_ends|No hardcode3,no steel umbral|
| Golden |engine→bytes iguales|PD16/17|Request exacto|Nuevo test_golden_bytes + --check|Segunda generación idéntica,árbol limpio|
| Mutación golden |cambio1byte falla|PD16|Copia temporal snapshot|Nuevo test_golden_byte_mutation|Exit no cero;CI no escritor|
| Hash |request+response sin hash|PD16|Cambios request/response|Nuevo test_calculation_hash|Ambos cambian hash;no self-hash;prefijo|
| Pricing puro |100000/(1-.35)|PD15/PRD05|Costo/margen explícitos|Nuevo test_pure_pricing|153846.15;rechazar1.0/negativo|
| DB mapping/RLS |N/N exacto,tenant/global|PRD02/owner|Reset limpio yorgA/B|SQL/loader/integration nuevos|Mismos params/fixtures;sin fuga|
| API/OpenAPI |7campos+nuevos tipos|PRD-FRONTEND|RequestsCore|backend/tests/test_engine_api.py+Orval|No drift;sin inspector|
| Canvas/auth |G1<300ms,discovery/RLS/aal2|SHOT05 cerrado|E2E real|canvas.spec.ts/auth.spec.ts|Regresión sin cambiosUI|
| G8 |strictxfail→06B|PLAN_SHOTS|Declaración actual|test_g8_sliding_3l_is_declared_deferred|Intacto|
| G9 |strictxfail→06B|PLAN_SHOTS|Declaración actual|test_g9_sliding_4l_is_declared_deferred|Intacto|
| G11 |strictxfail→06B|PLAN_SHOTS|Declaración actual|test_g11_double_door_is_declared_deferred|Intacto|
| G12 |strictxfail→06B|PLAN_SHOTS|Declaración actual|test_g12_large_fixed_is_declared_deferred|Intacto|
| G10 |manifestxfail→24|PLAN_SHOTS|Manifest actual|check_g_case_manifest|No inventar pytest existente|
| Purity/DoD |sinfloat/IO,mutación±0.01falla|Constitución/AGENTS|Runtime yfixtures|purity/mutation/check_dod all|Checker determinista,0warnings,exit0 real|

## 8. Secuencia y DB autorizadas

Fuentes activas actualizadas antes de implementación. PD19/20 cerradas:
PS añade tres autoridades; PA material y enumTHRESHOLD; HK.weight_kg nullable;
nueva infill_articles+RLS; seed añade umbral/panel/kits,renameOB/pesos2.50.
Migraciones NUEVAS para bases existentes, seed para reset limpio; nunca editar
20260901000000_initial_schema.sql ni20260902000000_add_glazing_bead_cut_add.sql.
Backfill explícito DEMO_60; no extrapolar valores sintéticos a otros sistemas.

Seguir secuencia completa recibida: DB Gate→Regla0→engine→G3/G5/G6/G7→pesos/hardware/
pricing→generador→make goldgen explícito→commit golden generado→--check→OpenAPI/Orval
→suites→python scripts/check_dod.py all→cuatro required CI→PR. NO MERGE.
Checks preservados: Ruff,mypy,pytest engine/backend con warnings error,Vitest/TS/build,
OpenAPI limpio,PostgreSQL16/Supabase/pgTAP/RLS,E2Eauth/Canvas. Sin relajar Checker para
obtener verde. Tests mutan fórmulas reales±0.01 contra expectativas independientes;
probar sólo helper assert no basta como sensibilidad de fórmula.

## 9. Riesgos y evidencia actual

Los bloqueos de la revisión previa quedaron resueltos; los bugs de implementación
se reparan autónomamente y no se convierten en pendientes normativos. G5 ya explica840→820 y1830→1810 por autoridades explícitas; no usar
constantes en engine. Identidad sintética no equivale a certificación comercial.
No mezclar panel/vidrio ni marco/masa móvil. No doble redondeo ni first-match.
Hash se calcula sobre datos explícitos, no sobre filesystem/HTTP; golden jamás manual.
API/Canvas regresión y RLS deben mantenerse al propagar nueva salida.

Evidencia ejecutada: git fetch/rev-parse/ls-remote/estado; lectura normativa; reproducción
Decimal independiente de G3 y goldenOB; edición sólo documental. Ningún test Core nuevo,
DB Gate,Gauntlet,CI,commit o PR ejecutado aún. Verificación final: perímetro de archivos,
whitespace y consistencia del documento. No se declara verde.

## 10. Matriz DB↔Engine normativa incorporada

La tabla siguiente copia la matriz activa de PRD-01 de esta revisión. Tipos/nulabilidad,
DEMO/fallback/fuente/modificador están explícitos. Detalles literales de artículos y
kits nuevos se conservan además en la resolución íntegra del apéndice.

## 5. Tabla Canónica de Correspondencia: Base de Datos ⟷ `/engine` (Regla Cero)

Para garantizar cero ambigüedad entre el esquema relacional PostgreSQL y las clases
Pydantic del motor, esta tabla define el mapeo exhaustivo de `SystemParams`. `DIRECTO`
significa columna persistida con correspondencia uno a uno; `DERIVADO` significa que el
loader obtiene el valor de filas relacionadas o transforma una autoridad persistida;
`FALLBACK` significa que no existe columna canónica y se usa el default tipado del motor.
Un fallback nunca prevalece sobre un valor persistido.

| Engine field | Origen DB | Tabla / columna | Unidad / tipo | Autoridad | Nullable | Quién modifica | DEMO_60 / fallback | Regla de derivación |
|---|---|---|---|---|:---:|---|---|---|
| `system_code` | DIRECTO | `profile_systems.code` | `str` ← `VARCHAR(50)` | Ficha fabricante | NO | Admin / Taller | `DEMO_60` | Copia exacta del sistema seleccionado. |
| `depth_mm` | DIRECTO | `profile_systems.depth_mm` | `Decimal`, mm ← `NUMERIC(10,2)` | Ficha fabricante | NO | Admin / Taller | `60.00` | Conversión exacta `NUMERIC` → `Decimal`; prohibido `float`. |
| `material` | DIRECTO | `profile_systems.material` | `MaterialType` ← `material_type` | Ficha fabricante | NO | Admin / Taller | `PVC` | Mapeo unívoco del enum PostgreSQL al enum del motor. |
| `effective_profile_articles` | DERIVADO como colección obligatoria; no persistido como agregado | Filas efectivas de `profile_articles` del sistema, indexadas por `role`; columnas `sku`, `role`, `material`, `face_width_mm`, `welding_loss_mm`, `reinforcement_gap_mm`, `weight_kg_m`, `steel_weight_kg_m`, `reinforcement_sku` | `Dict[ProfileRole, EffectiveProfileArticle]` | Cada fila `profile_articles`; soldadura, cara y gap pertenecen al artículo | NO | Taller mediante catálogo; adapter sólo mapea | FRAME cara/gap/soldadura `60.00/15.00/6.00`; SASH `75.00/15.00/6.00`; MULLION_V/H `80.00/5.00/0.00`; GLAZING_BEAD soldadura `0.00` | El adapter entrega un objeto distinto por artículo/rol efectivo. Geometría consume `face_width_mm` y `reinforcement_gap_mm` directamente del artículo; `welding_loss_per_end(article)` es derivado y nunca se almacena como scalar común. |
| `glazing_bead_rules` | DERIVADO como colección obligatoria; no persistido como agregado | `glazing_bead_matrix` unida con su `profile_articles` por `bead_article_id`; columnas `glass_thickness_mm`, `bead_width_mm`, `gasket_interior_mm`, `gasket_exterior_mm`, `cut_add_mm` y artículo efectivo | `Dict[Decimal, GlazingBeadRule]` | Fila de matriz + artículo GLAZING_BEAD referenciado | NO | Taller mediante catálogo; adapter sólo mapea | Cinco espesores `4/5/6/20/24`; `cut_add_mm=9.00` en todos | Indexar por `glass_thickness_mm`; `bead_cut_length = infill_length + rule.cut_add_mm`; prohibido hardcodear el suplemento. |
| `rebate_depth_mm` | FALLBACK; no persistido en SHOT-02 | — | `Decimal`, mm | Default tipado del motor hasta existir columna canónica | NO | Sistema / futura ficha aprobada | fallback `20.00` | Sin derivación DB; no inferir desde `depth_mm`, cara o junquillo. |
| `end_milling_overlap_mm` | FALLBACK; no persistido en SHOT-02 | — | `Decimal`, mm | Default tipado del motor hasta existir columna canónica | NO | Sistema / futura ficha aprobada | fallback `0.00` | Sin derivación DB; prohibido inferir desde `sash_overlap_mm`. |
| `sash_overlap_mm` | DIRECTO | `profile_systems.sash_overlap_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Catálogo técnico del sistema | NO | Taller | `8.00` | Copia exacta del sistema seleccionado. |
| `glass_clearance_white_mm` | DIRECTO | `profile_systems.glass_clearance_white_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de holgura del sistema | NO | Taller | `5.00`; fallback de clase `3.00` sólo sin catálogo | El valor persistido prevalece; seleccionar cuando `is_foiled = FALSE`. |
| `glass_clearance_foil_mm` | DIRECTO | `profile_systems.glass_clearance_foil_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de holgura del sistema | NO | Taller | `5.00`; fallback `5.00` | Seleccionar cuando `is_foiled = TRUE`. |
| `pulley_height_mm` | DIRECTO | `profile_systems.pulley_height_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de rodamientos del sistema | NO | Taller | `12.00` | Copia exacta del sistema seleccionado. |
| `central_overlap_mm` | DIRECTO | `profile_systems.central_overlap_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de traslape del sistema | NO | Taller | `40.00` | Copia exacta; valor canónico que produce G5 = `966.00 mm`. |
| `sliding_lateral_clearance_mm` | DIRECTO | `profile_systems.sliding_lateral_clearance_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de corredera del sistema | NO | Taller | `0.00` | Copia exacta del sistema seleccionado. |
| `sliding_end_add_mm` | DIRECTO | `profile_systems.sliding_end_add_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de corredera del sistema | NO | Taller | `6.00` | Copia exacta del sistema seleccionado. |
| `corner_bracket_loss_mm` | DIRECTO | `profile_systems.corner_bracket_loss_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha del sistema de aluminio | NO | Taller | `0.00` | Copia exacta; sólo participa en la rama de material ALUMINIUM. |
| `hook_depth_mm` | DIRECTO | `profile_systems.hook_depth_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha del sistema | NO | Taller | `0.00` | Copia exacta del sistema seleccionado. |
| `door_threshold_mm` | DIRECTO | `profile_systems.door_threshold_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de puerta del sistema | NO | Taller | `30.00` | Copia exacta del sistema seleccionado. |
| `door_bottom_clearance_mm` | DIRECTO | `profile_systems.door_bottom_clearance_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de puerta del sistema | NO | Taller | `20.00` | Copia exacta del sistema seleccionado. |
| `rail_type` | DIRECTO | `profile_systems.rail_type` | `RailType` ← `VARCHAR(10)` | Ficha de riel del sistema | NO | Taller | `dual` | Mapeo unívoco al enum; `hardware_kits.rail_type` se usa para matching, no como segunda autoridad del sistema. |
| `pvc_weight_kg_m` | DERIVADO por artículo | `profile_articles.weight_kg_m` del artículo seleccionado | `Decimal`, kg/m ← `NUMERIC(8,4)` | Ficha de peso del artículo | NO | Taller | `1.2000`; fallback `1.2000` | Resolver por artículo/rol; el peso persistido prevalece sobre el fallback de `SystemParams`. |
| `steel_weight_kg_m` | DERIVADO por artículo | `profile_articles.steel_weight_kg_m` del artículo seleccionado | `Decimal`, kg/m ← `NUMERIC(8,4)` | Ficha de refuerzo del artículo | NO | Taller | `1.7000`; fallback `1.7000` | Resolver por artículo/rol; no asumir el mismo refuerzo para artículos distintos. |
| `hardware_kit_weight_kg` | FALLBACK de sistema cuando hardware_kits.weight_kg es NULL | Sin columna PS; HK.weight_kg prevalece | `Decimal`, kg | Fallback tipado aprobado PD-06-14; HK.weight_kg prevalece | NO | Sistema / futura ficha aprobada | fallback `2.50` | Si HK.weight_kg es NULL: multiplicar este fallback por 1.10; no derivar desde contents ni capacidad. |
| `available_hardware_kits` | DERIVADO como colección | Filas de `hardware_kits` del `system_id` seleccionado; columnas `sku`, `name`, `opening_type`, límites, `rail_type`, cantidades, `contents` y `weight_kg` | `List[HardwareKitRule]` | Catálogo de herrajes visible por RLS | NO | Admin / Taller | 5 kits: `TURN`, `TILT_TURN`, `SLIDING`, `AWNING`, `DOOR`; `[]` no permite seleccionar hoja operable | Cargar sólo kits `is_active=TRUE` visibles para el tenant/globales y mapear cada columna sin inferencias. |

**Cobertura normativa SHOT-06:** `27/27` campos de SystemParams previstos: los 23
anteriores, tres parámetros PS y available_panel_rules. El runtime baseline aún tiene
23 campos; no se afirma que la implementación haya ocurrido. Se verificará N/N real
con modelos y tests una vez levantados los bloqueos Regla 0.

| Engine field nuevo | Origen DB | Tabla / columna | Unidad / tipo | Autoridad | Nullable | Quién modifica | DEMO_60 / fallback | Derivación |
|---|---|---|---|---|---|---|---|---|
| sliding_glazing_deduction_width_mm | DIRECTO | profile_systems.sliding_glazing_deduction_width_mm | Decimal mm, NUMERIC(10,2) | Resolución owner PD-01, sintético DEMO_60 | NO | Catálogo Admin/Taller autorizado | 20.00 / sin fallback | Deducción total W una vez por vidrio SLIDING |
| sliding_glazing_deduction_height_mm | DIRECTO | profile_systems.sliding_glazing_deduction_height_mm | Decimal mm, NUMERIC(10,2) | Misma autoridad | NO | Catálogo Admin/Taller autorizado | 20.00 / sin fallback | Deducción total H una vez por vidrio SLIDING |
| door_leaf_side_clearance_mm | DIRECTO | profile_systems.door_leaf_side_clearance_mm | Decimal mm, NUMERIC(10,2) | Resolución owner PD-05, sintético DEMO_60 | NO | Catálogo Admin/Taller autorizado | 7.00 / sin fallback | Dos lados de hoja puerta |
| available_panel_rules | DERIVADO | infill_articles visibles/activos del system | Dict[str,PanelRule] por SKU | Resolución owner PD-07 | Colección no nullable; masa sí | Catálogo Admin/Taller autorizado | PANEL-SANDWICH-DEMO-24; sin sustituto | Mapear SKU/name/kind/thickness/weight sin I/O engine |

Autoridades de submodelos añadidas/modificadas:

| Engine field | DB authority / tipo / unidad | Nullable | DEMO_60 | Fallback | Fuente / modificador |
|---|---|---|---|---|---|
| EffectiveProfileArticle.material / ProfileCut.material | profile_articles.material, material_type | NO | PVC existentes; UMBRAL-ALU ALUMINIUM | No material inferido | PD-06; catálogo autorizado |
| EffectiveProfileArticle.weight_kg_m | PA.weight_kg_m NUMERIC(8,4), kg/m | DB NO, modelo admite None | 1.2000 en artículos existentes | Sólo PVC: params.pvc_weight_kg_m*1.10 | PD-12/13; catálogo autorizado |
| EffectiveProfileArticle.steel_weight_kg_m | PA.steel_weight_kg_m NUMERIC(8,4), kg/m | DB NO, modelo admite None | 1.7000 | params.steel_weight_kg_m*1.10 si pieza lleva acero | PD-12/13; catálogo autorizado |
| HardwareKitRule.weight_kg | hardware_kits.weight_kg NUMERIC(8,2), kg | SÍ | 2.50 en los cinco kits | params.hardware_kit_weight_kg*1.10 =2.75 | PD-14; catálogo autorizado |
| PanelRule.sku/name/kind | infill_articles.sku/name/kind | NO | PANEL-SANDWICH-DEMO-24 / Panel Sándwich Demo 24mm / SANDWICH_PANEL | Ninguno | PD-07 sintético; catálogo autorizado |
| PanelRule.thickness_mm | infill_articles.thickness_mm NUMERIC(6,2), mm | NO | 24.00 | Ninguno | Misma autoridad |
| PanelRule.weight_kg_m2 | infill_articles.weight_kg_m2 NUMERIC(10,4), kg/m² | SÍ | 10.0000 | MissingWeightAuthority si usado sin peso | Misma autoridad |
| HardwareComponent.sku/name/qty/unit | hardware_kits.contents JSONB, qty Decimal | Shape requerido al usar contenido | AWNING: DEMO-STAY-16 / Compás a fricción 16 pulgadas /2/unit; DOOR: DEMO-LOCK-MULTIPOINT / Cerradura multipunto Demo /1/unit | No inventar componentes; conservar orden persistido | PD-04/08/09; catálogo autorizado |
| ParametricNode.panel_article_sku | Referencia request a infill_articles.sku del system | Obligatorio DOOR_ENTRY | PANEL-SANDWICH-DEMO-24 | Ninguno | PD-07; input humano/catálogo |
| leaf_id de piezas/pesos/hardware | Derivado BAY/hoja | SÍ | SLIDING :L1/:L2; null donde no necesario | Ninguno | PD-02; motor puro |


### 5.0.1. Mapping de reglas de hardware: 13/13 campos de HardwareKitRule

Valores de cinco kits en orden TURN / TILT_TURN / SLIDING / AWNING / DOOR;
HK=hardware_kits. Fuente: seed baseline para tres existentes y resolución sintética
PD-04/08/11/14 para modificaciones. Modificador: catálogo propio bajo RLS o admin global.
Ninguna restricción dimensional admite fallback.

| Engine field | DB authority / tipo | DEMO_60 en orden indicado | Fallback | Nullable |
|---|---|---|---|---|
| sku | HK.sku VARCHAR(100) | KIT-TURN / KIT-TILT-TURN / KIT-SLIDING / KIT-AWNING-16 / KIT-DOOR-MULTIPOINT | Ninguno | No |
| name | HK.name VARCHAR(255) | Kit Practicable Demo 60 / Kit Vorne OB 100kg / Kit Corredera Demo 60 / Kit Proyectante Compás 16" 45kg / Kit Puerta Entrada Multipunto Demo 60 | Ninguno; nombres literales §6 | No |
| opening_type | HK.opening_type VARCHAR(30) | TURN / TILT_TURN / SLIDING / AWNING / DOOR | Ninguno | No |
| min_leaf_width_mm | HK.min_leaf_width_mm NUMERIC(10,2), mm | 400 /450 /400 /400 /700 | Ninguno | No |
| max_leaf_width_mm | HK.max_leaf_width_mm NUMERIC(10,2), mm | 1200 /1400 /1500 /1200 /1200 | Ninguno | No |
| min_leaf_height_mm | HK.min_leaf_height_mm NUMERIC(10,2), mm | 500 /600 /500 /400 /1800 | Ninguno | No |
| max_leaf_height_mm | HK.max_leaf_height_mm NUMERIC(10,2), mm | 2400 /2400 /2500 /1000 /2400 | Ninguno | No |
| max_leaf_weight_kg | HK.max_leaf_weight_kg NUMERIC(6,2), kg | 80 /100 /120 /45 /120 | Ninguno; capacidad, no masa | No |
| rail_type | HK.rail_type VARCHAR(10) | Todos dual | Clase DUAL; DB prevalece | No |
| carriages_qty | HK.carriages_qty INT | 0 /0 /2 /0 /0 | Default DB2; fila aprobada prevalece | No |
| stay_arms_qty | HK.stay_arms_qty INT | 0 /1 /0 /2 /0 | Default DB1; fila aprobada prevalece | No |
| contents | HK.contents JSONB | [] /[] /[] /DEMO-STAY-16 qty2 unit /DEMO-LOCK-MULTIPOINT qty1 unit | No inventar componentes; orden persistido | No |
| weight_kg | HK.weight_kg NUMERIC(8,2), kg | Todos2.50 | params.hardware_kit_weight_kg*1.10 sólo NULL | Sí |

HardwareComponent mapea las cuatro claves SKU/name/qty/unit de cada elemento JSONB,
qty Decimal exacto; no float ni coerción desde float. JSONB array conserva orden.
HardwareItem hereda kit_sku/name de kit seleccionado; qty1/unit kit; bay_id del nodo,
leaf_id derivado; contents anidados. No otra autoridad ni expansión comercial.

### 5.0.2. Artículos efectivos y reglas de junquillo completos

Cada EffectiveProfileArticle contiene sku,role,material,face_width_mm,welding_loss_mm,
reinforcement_gap_mm,weight_kg_m,steel_weight_kg_m,reinforcement_sku:9/9 desde PA homónimos.
SKU/role/material no nullable; dimensiones NUMERIC(10,2) mm no nullable; masas lineales
NUMERIC(8,4) kg/m DB no nullable, Optional interno para fallback; reinforcement_sku
nullable. Fuente/edición: seed y resolución owner, catálogo autorizado bajo RLS.
Los siete artículos previos pesan1.2000/1.7000 por default DB y reinforcement_sku=NULL.
UMBRAL-ALU no participa en masa móvil ni genera acero; no inferir que otro NULL elimina acero.

| SKU PA | Rol | Material | Cara mm | Soldadura total mm | Gap mm | Autoridad / fallback |
|---|---|---|---|---|---|---|
| MARCO | FRAME | PVC |60.00|6.00|15.00|Seed baseline; sin fallback geométrico|
| HOJA | SASH | PVC |75.00|6.00|15.00|Seed baseline; sin fallback geométrico|
| POSTE-V | MULLION_V | PVC |80.00|0.00|5.00|Seed baseline; sin fallback geométrico|
| POSTE-H | MULLION_H | PVC |80.00|0.00|5.00|Seed baseline; sin fallback geométrico|
| JQ-24 | GLAZING_BEAD | PVC |24.00|0.00|15.00|Seed baseline; sin fallback geométrico|
| JQ-14 | GLAZING_BEAD | PVC |14.00|0.00|15.00|Seed baseline; sin fallback geométrico|
| JQ-10 | GLAZING_BEAD | PVC |10.00|0.00|15.00|Seed baseline; sin fallback geométrico|
| UMBRAL-ALU | THRESHOLD | ALUMINIUM |30.00|0.00|0.00|PD-06 sintético; sin fallback geométrico|

GlazingBeadRule:6/6 campos, de GB.glass_thickness_mm, bead_article_id→PA completo,
bead_width_mm,gasket_interior_mm,gasket_exterior_mm,cut_add_mm. Dimensiones GB son
NUMERIC(6,2) mm NOT NULL; sin fallback runtime; edición catálogo autorizado.

| Espesor total mm | Artículo | Ancho bead mm | Juntas int/ext mm | Cut add mm |
|---|---|---|---|---|
|4.00|JQ-24|24.00|3.00/3.00|9.00|
|5.00|JQ-24|24.00|2.50/2.50|9.00|
|6.00|JQ-24|24.00|2.00/2.00|9.00|
|20.00|JQ-14|14.00|3.00/3.00|9.00|
|24.00|JQ-10|10.00|3.00/3.00|9.00|

Loader: PS/PA/GB/HK/infill se restringen al system y organización activa, o global
visible bajo RLS. PS/HK/GB/infill deben estar activos; PA no tiene is_active en DDL.
PA.system_id e infill.system_id son NOT NULL; org_id nullable para global. HK.system_id
nullable en DDL, pero loader canónico sólo carga system exacto, no kits genéricos NULL.
PanelRule:5/5 sku/name/kind/thickness_mm/weight_kg_m2 desde infill homónimos;
kind SANDWICH_PANEL, espesor24.00, peso10.0000 sintético; sólo peso nullable y sin fallback.

## 11. Resolución íntegra recibida del owner

Transcripción histórica literal. PD-06-19/20 quedan corregidas por la resolución
más reciente del apéndice12. La antigua expectativa26.55 para G3 NO está vigente;
G3 standalone33.29 y goldenOB26.55. Los operadores mal formateados se desarrollan
en PRD activo desde los ejemplos explícitos. No contiene autorización para saltarse Regla0.

[RESOLUCIÓN CANÓNICA PD-06-01…PD-06-17 — SHOT-06]

La detención de FASE 1 fue correcta.

Quedan resueltas las PD-06-01…PD-06-17.

Primero incorpora íntegramente estas decisiones en:

`docs/plans/PLAN_SHOT-06.md`

y corrige las fuentes normativas activas afectadas.

Después ejecuta nuevamente Regla 0 / Regla 20.

Si no aparece un nuevo vacío normativo REAL:

APROBADO — EJECUTA FASE 2.

No implementes G8/G9/G11/G12.
No implementes G10.
No implementes Inspector/BFD.
No adelantes SHOT-08 comercial.

---

# PRINCIPIO DEMO_60

Cuando esta resolución introduce:

* SKU nuevo;
* kit nuevo;
* peso de panel;
* rango dimensional de kit;

y ese valor no existe previamente en una ficha de fabricante, queda definido como:

`DEMO_60 SYNTHETIC FIXTURE`

Es autoridad únicamente del sistema ficticio DEMO_60 y de los tests.

NO presentar esos valores como especificaciones reales de Vorne, Roto, Winkhaus ni otro fabricante.

---

# PD-06-01 — G5 840 → 820 Y ALTURA 1810

El “ajuste de cruce y junquillo” deja de ser texto ambiguo.

Se introducen dos autoridades técnicas del SISTEMA:

`sliding_glazing_deduction_width_mm`
`sliding_glazing_deduction_height_mm`

Unidad:
`mm`

Semántica:
deducción TOTAL por eje, aplicada una sola vez al vidrio de una hoja corredera después de resolver la dimensión terminada de la hoja y la geometría común de junquillo/rebate.

NO es valor por lado.

NO es `cut_add_mm`.

NO modifica la regla global de junquillo.

DEMO_60:

`sliding_glazing_deduction_width_mm = 20.00`
`sliding_glazing_deduction_height_mm = 20.00`

Persistencia:

nuevas columnas NOT NULL en `profile_systems`.

Nueva migración SHOT-06.
No reescribas migraciones anteriores.

## Dimensión terminada de hoja corredera

La longitud de corte pierde la soldadura al obtener dimensión física terminada:

`finished_width = sash_cut_width - sash_article.welding_loss_mm`

`finished_height = sash_cut_height - sash_article.welding_loss_mm`

Para G5:

`966.00 - 6.00 = 960.00`

`1956.00 - 6.00 = 1950.00`

## Fórmula vidrio SLIDING

Primero:

`base_glass_width = finished_width - 2*SASH.face_width + 2*rebate_depth - 2*clearance`

`base_glass_height = finished_height - 2*SASH.face_width + 2*rebate_depth - 2*clearance`

Después:

`glass_width = base_glass_width - sliding_glazing_deduction_width_mm`

`glass_height = base_glass_height - sliding_glazing_deduction_height_mm`

DEMO_60:

Width:

`960 - 150 + 40 - 10 = 840`
`840 - 20 = 820.00`

Height:

`1950 - 150 + 40 - 10 = 1830`
`1830 - 20 = 1810.00`

Con esto G5 queda explicado en ambos ejes sin hardcode.

Actualiza PRD-01 §6.3 eliminando la frase ambigua y sustituyéndola por estas ecuaciones.

---

# PD-06-02 — CONTRATO COMPLETO G5 SLIDING_2L

Fixture canónico:

* nominal `2000.00 × 2100.00`
* opening `SLIDING_2L`
* color `WHITE`
* `glass_thickness_mm = 20.00`
* `glass_spec = "4-12-4 Float Incoloro"`
* rail `dual`

Una BAY SLIDING_2L produce exactamente DOS hojas:

`leaf_id = "<bay_id>:L1"`
`leaf_id = "<bay_id>:L2"`

orden izquierda→derecha.

Añade `leaf_id: Optional[str]` a las piezas que pertenecen a una hoja:

* `ProfileCut`
* `ReinforcementPiece`
* `GlassPiece`
* `HardwareItem`
* `LeafWeight`

G1–G4 mantienen `leaf_id=null` donde no sea necesario.

## FRAME G5

PVC:

* H `2006.00`, qty 2
* V `2106.00`, qty 2

Acero FRAME:

* H `1970.00`, qty 2
* V `2070.00`, qty 2

## SASH POR HOJA

Cada hoja:

* H cut `966.00`, qty 2
* V cut `1956.00`, qty 2

Total G5:

* H: qty 4
* V: qty 4

Estos valores son LONGITUDES DE CORTE.

No declararlos dimensiones exteriores.

Dimensiones físicas terminadas usadas para hardware:

* width `960.00`
* height `1950.00`

## ACERO SASH

Usa la regla generalizada por extremos soldados:

`steel_cut = pvc_cut - welded_end_count*welding_loss_per_end(article) - 2*reinforcement_gap_mm`

Para una hoja rectangular soldada:
`welded_end_count = 2`

Por tanto:

* H `930.00`
* V `1920.00`

Cada hoja:
qty 2 H + qty 2 V.

## VIDRIO

Por hoja:

`820.00 × 1810.00`

Total:
qty 2.

## JUNQUILLO

Continúa usando exclusivamente:

`bead_cut = glass_length + glazing_bead_rule.cut_add_mm`

DEMO_60 `cut_add_mm=9.00`.

Por hoja:

* width bead `829.00`, qty 2
* height bead `1819.00`, qty 2

Total G5:
qty 4 de cada longitud.

No existe fórmula especial de bead para SLIDING.

---

# PD-06-03 — G6 AWNING

AWNING comparte la geometría de una hoja rectangular operable con TURN/TILT_TURN:

* sash overlap;
* transformación outer→cut mediante welding loss;
* reinforcement;
* glass;
* bead.

Lo que cambia es:

* `opening_type`;
* orientación funcional;
* hardware.

No copies código.

Extrae/usa una primitive interna común de:

`single_rectangular_sash_geometry`

para TURN / TILT_TURN / AWNING.

## Fixture G6

* nominal `1200.00 × 800.00`
* opening `AWNING`
* color WHITE
* glass thickness `20.00`
* glass spec `"4-12-4 Float Incoloro"`

FRAME:

* H `1206.00`, qty2
* V `806.00`, qty2

FRAME steel:

* H `1170.00`, qty2
* V `770.00`, qty2

SASH finished outer:

`1096.00 × 696.00`

SASH cuts:

* H `1102.00`, qty2
* V `702.00`, qty2

SASH steel:

* H `1066.00`, qty2
* V `666.00`, qty2

Glass:

`976.00 × 576.00`

Beads:

* `985.00`, qty2
* `585.00`, qty2

El Core Gold continúa exigiendo especialmente:

`1102.00 / 702.00`

y el kit 16"/45 kg.

Los demás valores quedan ahora congelados como fixture completo SHOT-06.

---

# PD-06-04 — KIT AWNING

Añade a DEMO_60:

SKU:

`KIT-AWNING-16`

Nombre:

`Kit Proyectante Compás 16" 45kg`

opening_type:

`AWNING`

Fixture sintético DEMO_60:

* min width `400.00`
* max width `1200.00`
* min height `400.00`
* max height `1000.00`
* max_leaf_weight `45.00`
* rail_type `dual`
* carriages_qty `0`
* stay_arms_qty `2`
* weight_kg `2.50`

`contents` mínimo:

* sku `DEMO-STAY-16`
* name `Compás a fricción 16"`
* qty `2`
* unit `unit`

Estos SKU/rangos son fixtures sintéticos DEMO_60, no ficha comercial.

---

# PD-06-05 — G7 DOOR_ENTRY

DOOR_ENTRY usa una topología distinta del frame rectangular soldado en cuatro esquinas.

## Topología de marco

* cabezal PVC soldado a ambas jambas;
* jambas PVC soldadas sólo en el extremo superior;
* extremo inferior de cada jamba unido mecánicamente al umbral;
* umbral aluminio, unión 90°, sin soldadura PVC.

Esto explica el Gold sin magic number.

### Cabezal

`head_cut = nominal_width + 2*frame_welding_loss_per_end`

G7:

`950 + 3 + 3 = 956.00`

qty1.

Ángulos:
`45 / 45`

### Jambas

`jamb_cut = nominal_height + frame_welding_loss_per_end`

G7:

`2150 + 3 = 2153.00`

qty2.

Ángulos:
`45 / 90`

La orientación física es espejada, pero la lista de corte puede agrupar ambas bajo la misma pareja de ángulos cuando la máquina interpreta cara/orientación por pieza.

### Acero FRAME

Generaliza la fórmula:

`steel_cut = pvc_cut - welded_end_count*loss_per_end - 2*reinforcement_gap`

Cabezal:
welded_end_count=2

`956 - 6 - 30 = 920.00`

Jamba:
welded_end_count=1

`2153 - 3 - 30 = 2120.00`

## Umbral

Ver PD-06-06.

Cut:

`nominal_width - 2*frame_face_width`

`950 - 120 = 830.00`

## Hoja DOOR_ENTRY

Introduce:

`door_leaf_side_clearance_mm`

autoridad del sistema.

Persistencia:
`profile_systems.door_leaf_side_clearance_mm`

DEMO_60:

`7.00`

Dimensión exterior terminada:

`door_leaf_outer_width = frame_clear_width - 2*door_leaf_side_clearance_mm`

`830 - 14 = 816.00`

Altura:

`door_leaf_outer_height =
nominal_height

* frame_face_width
* door_threshold_mm
* door_bottom_clearance_mm

- sash_overlap_mm`

DEMO:

`2150 - 60 - 30 - 20 + 8 = 2048.00`

Cortes SASH de la hoja:

* H `822.00`, qty2
* V `2054.00`, qty2

Acero SASH:

* H `786.00`, qty2
* V `2018.00`, qty2

## Panel

El panel usa el mismo pocket geométrico de la hoja:

`panel_width =
leaf_outer_width

* 2*SASH.face_width
  + 2*rebate_depth
* 2*clearance`

`816 -150 +40 -10 = 696.00`

`panel_height =
 leaf_outer_height
 -2*SASH.face_width
 +2*rebate_depth
 -2*clearance`

`2048 -150 +40 -10 = 1928.00`

Así G7 produce:

`696.00 × 1928.00`

sin glass ficticio.

---

# PD-06-06 — ARTÍCULO THRESHOLD

Añade:

`ProfileRole.THRESHOLD`

al contrato Python y al enum PostgreSQL mediante migración NUEVA.

Añade a `profile_articles`:

`material material_type NOT NULL DEFAULT 'PVC'`

Backfill:
todos los artículos existentes DEMO_60 = PVC.

Añade fixture DEMO:

SKU:
`UMBRAL-ALU`

Name:
`Umbral Aluminio Demo 60`

Role:
`THRESHOLD`

Material:
`ALUMINIUM`

face_width_mm:
`30.00`

welding_loss_mm:
`0.00`

reinforcement_gap_mm:
`0.00`

reinforcement_sku:
NULL

No genera refuerzo.

El umbral NO forma parte del peso de la hoja móvil usado para resolución de hardware.

No reutilices FRAME/SASH.

`ProfileCut` debe poder identificar el material real del artículo.

Añade `material: MaterialType`.

Para compatibilidad, los cortes G1–G6 serán PVC.

---

# PD-06-07 — PANEL SÁNDWICH

No modeles el panel como vidrio.

Añade tabla:

`infill_articles`

mínimo:

* id UUID
* system_id UUID
* org_id UUID nullable
* sku VARCHAR
* name VARCHAR
* kind VARCHAR CHECK (`SANDWICH_PANEL`)
* thickness_mm NUMERIC(6,2)
* weight_kg_m2 NUMERIC(10,4) nullable
* is_active BOOLEAN
* created_at

Unique:
`(system_id, sku)`

RLS igual al patrón de catálogos globales/tenant.

Añade al nodo:

`panel_article_sku: Optional[str]`

Para DOOR_ENTRY es obligatorio.

Modelo engine:

`PanelRule`
`PanelPiece`

`PanelPiece`:

* sku
* name
* bay_id
* leaf_id
* width_mm
* height_mm
* area_m2
* weight_kg

Área:
exacta en m², pública 4 decimales HALF_UP.

Peso:
`exact_area * weight_kg_m2`
y output a 2 decimales HALF_UP.

DEMO_60 fixture sintético:

SKU:
`PANEL-SANDWICH-DEMO-24`

Name:
`Panel Sándwich Demo 24mm`

kind:
`SANDWICH_PANEL`

thickness:
`24.00`

weight_kg_m2:
`10.0000`

Este peso es sintético DEMO_60, no ficha de fabricante.

G7 panel weight:

`1.341888 m² × 10.0000 = 13.41888 kg`

output:
`13.42 kg`

---

# PD-06-08 — KIT DOOR MULTIPUNTO

Añade fixture DEMO_60:

SKU:
`KIT-DOOR-MULTIPOINT`

Name:
`Kit Puerta Entrada Multipunto Demo 60`

opening_type:
`DOOR`

Rango sintético:

* min width `700.00`
* max width `1200.00`
* min height `1800.00`
* max height `2400.00`
* max_leaf_weight `120.00`
* rail_type dual
* carriages `0`
* stay_arms `0`
* weight_kg `2.50`

contents mínimo:

* sku `DEMO-LOCK-MULTIPOINT`
* name `Cerradura multipunto Demo`
* qty `1`
* unit `unit`

No inventes más componentes comerciales.

El Gold G7 exige multipunto; no exige una marca real.

---

# PD-06-09 — HARDWARE OUTPUT TIPADO

Elimina:

`List[Dict[str,str]]`

como contrato público.

Define:

`HardwareComponent`

campos:

* sku: str
* name: str
* qty: Decimal
* unit: str

Define:

`HardwareItem`

* kit_sku: str
* name: str
* qty: int = 1
* unit: `"kit"`
* bay_id: str
* leaf_id: Optional[str]
* contents: list[HardwareComponent]

`hardware_items` contiene UN HardwareItem por kit seleccionado por hoja.

No flattenees contents como artículos de costo separados.

El kit es la unidad comercial/BOM primaria.

`contents` describe su composición de taller.

El orden de `contents` debe ser el del catálogo persistido.

---

# PD-06-10 — RESOLUCIÓN DETERMINISTA DE HARDWARE

Conserva:

`normalize_opening_type`

Matching inicial:

* normalized opening_type;
* rail_type;
* finished leaf width;
* finished leaf height.

Después prueba peso candidato.

## Dimensiones para matching

Usa DIMENSIÓN TERMINADA EXTERIOR DE HOJA.

NO longitud de corte.

G3:
cut 902/1302 → finished 896/1296.

G5:
960/1950.

G6:
1096/696.

G7:
816/2048.

## Peso y circularidad

Primero calcula:

`base_leaf_weight`

SIN hardware.

Por cada kit candidato:

`candidate_total_weight =
 base_leaf_weight + effective_hardware_kit_weight(kit)`

y verifica:

`candidate_total_weight <= kit.max_leaf_weight_kg`

## `hardware_set_sku`

Si `ParametricNode.hardware_set_sku` está definido:

* filtra exclusivamente ese SKU;
* debe existir;
* debe cumplir opening/dim/rail/weight;
* si no cumple → error determinista.

Si NO está definido:

* 0 compatibles → `NoCompatibleHardwareKit`
* 1 compatible → seleccionar
* > 1 compatibles → `AmbiguousHardwareKit`

PROHIBIDO seleccionar “el primero”.

---

# PD-06-11 — G3 HARDWARE

La subaserción diferida G3 deja de ser xfail.

Canonical mapping DEMO_60:

SKU:
`KIT-TILT-TURN`

Name:
`Kit Vorne OB 100kg`

opening:
`TILT_TURN`

max:
`100.00 kg`

Renombra únicamente el display name del fixture existente.

El SKU sigue siendo:

`KIT-TILT-TURN`

No afirmes que otros datos sintéticos del fixture son ficha oficial Vorne.

G3 debe demostrar:

* geometry intacta;
* finished sash `896.00 × 1296.00`;
* glass `776.00 × 1176.00`;
* kit elegido `KIT-TILT-TURN`;
* name `Kit Vorne OB 100kg`;
* total leaf weight `26.55 kg`;
* `26.55 <= 100.00`.

El cálculo de `26.55` debe usar valores exactos internos y cuantizar sólo al final.

Actualiza GOLD_CASES_MANIFEST:

la aserción hardware de G3 pasa a `pass/resolved in SHOT-06`.

No debe seguir figurando como deferred xfail.

---

# PD-06-12 — MODELO DE PESO

Crea módulo puro:

`engine/weight.py`

No DB/I/O.

## Perfil PVC

Por pieza:

`weight_exact =
 (cut_length_mm / 1000) * qty * effective_profile_weight_kg_m`

La longitud usada es LONGITUD DE CORTE porque representa material físico consumido en esa hoja.

## Acero

`weight_exact =
(reinforcement_cut_mm / 1000)

* qty
* effective_steel_weight_kg_m`

## Glass

Usa el cálculo exacto PD-09 ya aprobado.

NO reutilizar `GlassPiece.weight_kg` cuantizado para el total interno.

## Panel

Usa área exacta × `weight_kg_m2`.

## Hardware

Usa peso efectivo del kit candidato.

## LeafWeight

Añade modelo:

* bay_id
* leaf_id
* pvc_weight_kg
* steel_weight_kg
* infill_weight_kg
* hardware_weight_kg
* total_weight_kg
* used_fallback: bool

Todos los outputs kg:
2 decimales `ROUND_HALF_UP`.

La autoridad para matching es el total EXACTO previo a cuantización.

---

# PD-06-13 — FALLBACK 1.1

`WEIGHT_FALLBACK_FACTOR = Decimal("1.10")`

queda definido como multiplicador CONSERVADOR únicamente de una autoridad fallback.

Nunca se aplica encima de un peso persistido válido.

## Profile PVC

Si `article.weight_kg_m` existe:
usar exactamente.

Si falta:
`params.pvc_weight_kg_m * 1.10`

Sólo permitido para `material=PVC`.

Para material no PVC sin peso:
`MissingWeightAuthority`.

## Steel

Si `steel_weight_kg_m` existe:
usar exactamente.

Si falta y la pieza realmente tiene refuerzo:

`params.steel_weight_kg_m * 1.10`

## Hardware

Ver PD-06-14.

## Panel

NO existe fallback genérico seguro.

Si `PanelRule.weight_kg_m2` falta y el panel participa en leaf weight:

`MissingWeightAuthority`

No uses vidrio como proxy.

## Tipo

Permite `None` en los modelos internos de weight authority.

El adapter puede seguir entregando valores persistidos positivos del esquema existente.

Test obligatorio del path fallback puro aunque DEMO_60 no lo necesite.

---

# PD-06-14 — HARDWARE KIT WEIGHT

Añade nueva columna:

`hardware_kits.weight_kg NUMERIC(8,2) NULL`

Añade al modelo:

`HardwareKitRule.weight_kg: Decimal | None`

Todos los kits DEMO_60:

`2.50`

incluidos TURN/TILT-TURN/SLIDING/AWNING/DOOR.

Si existe:
usar exactamente.

Si es NULL:

`params.hardware_kit_weight_kg * WEIGHT_FALLBACK_FACTOR`

DEMO fallback:

`2.50 × 1.10 = 2.75 kg`

y:

`used_fallback=true`

El fallback se prueba, pero los Gold Cases DEMO_60 usan peso persistido `2.50`, no fallback.

---

# PESOS CORE CONGELADOS

## G5 por hoja

PVC:

`7.0128 kg`

Steel:

`9.6900 kg`

Glass exact:

`29.6840 kg`

Hardware:

`2.5000 kg`

Total exact:

`48.8868 kg`

Output:

`48.89 kg`

KIT-SLIDING max:
`120.00`

## G6

PVC:
`4.3296`

Steel:
`5.8888`

Glass exact:
`11.24352`

Hardware:
`2.50`

Total:
`23.96192`

Output:
`23.96 kg`

KIT-AWNING-16 max:
`45.00`

## G7

PVC leaf:

cuts:
2×822 + 2×2054 = 5752 mm

`5.752 ×1.2 = 6.9024`

Steel:

2×786 + 2×2018 = 5608 mm

`5.608 ×1.7 = 9.5336`

Panel exact:
`13.41888`

Hardware:
`2.50`

Total exact:
`32.35488`

Output:
`32.35 kg`

KIT-DOOR-MULTIPOINT max:
`120.00`

---

# PD-06-15 — PRICING PURO

SHOT-06 NO implementa los cinco modos.

SHOT-08 sigue siendo dueño de:

* cost lists;
* pricing_rules lookup;
* FX;
* waste;
* labor;
* installation;
* Mode 1–5 routing;
* discounts;
* authorization;
* price_audit_logs.

SHOT-06 implementa únicamente las PRIMITIVES MATEMÁTICAS PURAS que PRD-05 ya define.

Crea:

`engine/pricing.py`

Mínimo:

`price_from_cost_and_margin(direct_cost, margin_pct)`

Formula:

`price_exact = direct_cost / (1 - margin_pct)`

Validación:

* direct_cost >= 0
* `0 <= margin_pct < 1`

Output:

`price_net`

2 decimales HALF_UP.

Y:

`gross_margin_pct(cost, price)`

Formula:

`(price - cost) / price`

Output:
4 decimales HALF_UP.

Test normativo:

cost `100000.00`
margin `0.3500`

price:

`153846.15`

No DB.
No currency conversion.
No API de pricing.
No integración con project_positions.

Esto satisface “pricing puro” sin invadir SHOT-08.

---

# PD-06-16 — GOLDEN SNAPSHOT / HASH

SHOT-06 introduce:

`engine/tests/golden_example.json`

SE GENERA.

JAMÁS edición manual.

El Makefile ya declara:

`make goldgen`

Mantén esa interfaz.

## Request exacto

Sistema DEMO_60 real:

`3067da09-3119-5ad0-a1d5-498cd2dfd753`

Request:

```json
{
  "system_id": "3067da09-3119-5ad0-a1d5-498cd2dfd753",
  "nominal_width_mm": "1500.00",
  "nominal_height_mm": "1400.00",
  "color": "WHITE",
  "parametric_tree": {
    "id": "root",
    "type": "SPLIT_V",
    "split_offset_mm": "750.00",
    "mullion_profile_sku": "POSTE-V",
    "children": [
      {
        "id": "bay_1",
        "type": "BAY",
        "opening_type": "FIXED",
        "glass_thickness_mm": "24.00",
        "glass_spec": "4-16-4 Float Incoloro"
      },
      {
        "id": "bay_2",
        "type": "BAY",
        "opening_type": "TILT_TURN_RIGHT",
        "glass_thickness_mm": "20.00",
        "glass_spec": "4-12-4 Float Incoloro"
      }
    ]
  }
}
```

No uses el UUID antiguo incorrecto.

No omitas `mullion_profile_sku`.

## Canonical serialization para hash

Construye objeto:

`{request, response_without_calculation_hash}`

Serializa:

* UTF-8
* `ensure_ascii=False`
* keys ordenadas lexicográficamente
* separators exactos `(",", ":")`
* sin whitespace
* arrays en orden canónico del motor
* Decimal → string
* nunca float

Calcula:

`sha256(canonical_payload_bytes).hexdigest()`

Public field:

`calculation_hash`

Formato:

`sha256:<64 lowercase hex>`

El hash NO se incluye dentro de los bytes que se hashean.

No existe self-hash.

## Snapshot file

Después de calcular hash:

snapshot final:

```json
{
  "request": {...},
  "response": {
    "calculation_hash": "...",
    ...
  }
}
```

Archivo:

* UTF-8
* LF
* indent=2
* sort_keys=True
* ensure_ascii=False
* exactamente un newline final

## Regeneración

`make goldgen`

es la única ruta autorizada que escribe el snapshot.

Añade modo:

`python -m engine.scripts.regenerate_golden --check`

que genera bytes EN MEMORIA y compara contra el archivo existente.

CI usa `--check`.

CI NUNCA reescribe el snapshot.

Drift:
FAIL.

---

# PD-06-17 — CONTENIDO DEL SNAPSHOT / EXTENDED GATES

El response SHOT-06 del snapshot contiene:

* `calculation_hash`
* `profile_cuts`
* `reinforcements`
* `glasses`
* `panels`
* `hardware_items`
* `leaf_weights`

NO contiene:

* `inspector`
* BFD
* pricing
* costs
* price
* audit
* OT

`panels=[]` para este golden request.

La hoja OB de `bay_2` ahora incluye:

* hardware kit resuelto;
* leaf weight.

Mantén los resultados geométricos históricos del composite:

FRAME:

* 1506 ×2
* 1406 ×2

MULLION_V:

* 1280 ×1

SASH bay_2:

* 672 ×2
* 1302 ×2

Beads:

* fixed 689 ×2 / 1319 ×2
* OB 555 ×2 / 1185 ×2

Reinforcements:

* FRAME 1470 ×2 /1370 ×2
* MULLION 1270 ×1
* SASH 636 ×2 /1266 ×2

Glasses:

* fixed `680×1310`, area `0.8908`, weight `17.82`
* OB `546×1176`, area `0.6421`, weight `12.84`

OB leaf total:

`26.55 kg`

Hardware:

`KIT-TILT-TURN / Kit Vorne OB 100kg`

No Inspector todavía.

## Public API

SHOT-06 sí añade `calculation_hash`, `panels` y `leaf_weights` al contrato `/engine/calculate/`.

Regenera:

* OpenAPI;
* Orval.

No añadas Inspector.

---

# EXTENDED

Mantén exactamente:

* G8 → SHOT-06B xfail
* G9 → SHOT-06B xfail
* G11 → SHOT-06B xfail
* G12 → SHOT-06B xfail
* G10 → SHOT-24 xfail

No implementes esas ramas.

El actual código parcial SLIDING_3L/4L y DOOR_DOUBLE no se convierte en gate SHOT-06.

No los “termines aprovechando”.

---

# DB CHANGES AUTORIZADOS SHOT-06

NUEVAS migraciones únicamente.

Como mínimo:

1. `profile_systems`

   * `sliding_glazing_deduction_width_mm`
   * `sliding_glazing_deduction_height_mm`
   * `door_leaf_side_clearance_mm`

2. `profile_articles`

   * `material material_type`
   * soporte enum `THRESHOLD`

3. `hardware_kits`

   * `weight_kg`

4. nueva:

   * `infill_articles`

5. RLS para `infill_articles`.

6. seed:

   * nuevas columnas DEMO_60;
   * UMBRAL-ALU;
   * PANEL-SANDWICH-DEMO-24;
   * KIT-AWNING-16;
   * KIT-DOOR-MULTIPOINT;
   * rename KIT-TILT-TURN display name;
   * weight 2.50 en kits existentes.

No reescribas migraciones SHOT-02/03.

---

# DB ↔ ENGINE

Actualiza la matriz PRD-01 exhaustivamente.

No mantengas “23/23” por nostalgia.

Reporta el N/N REAL resultante.

Toda autoridad nueva debe indicar:

* DB table/column;
* tipo/unidad;
* nullable;
* fuente;
* DEMO_60;
* fallback;
* modificador futuro.

---

# GATES CORE

Después de implementar deben pasar exactamente:

## G5

* frame 2006/2106
* sash cuts 966/1956
* sash steel 930/1920
* glass 820/1810
* bead 829/1819
* weight 48.89 por hoja
* KIT-SLIDING
* discrepancy 0.00

## G6

* sash 1102/702
* sash steel 1066/666
* glass 976/576
* bead 985/585
* KIT-AWNING-16
* total leaf weight 23.96
* max kit 45.00
* discrepancy 0.00

## G7

* head 956
* jamb 2153
* threshold 830
* panel 696/1928
* door leaf outer 816/2048
* door sash cut 822/2054
* door sash steel 786/2018
* KIT-DOOR-MULTIPOINT
* leaf weight 32.35
* discrepancy 0.00

## G3 deferred hardware

Debe pasar:

* KIT-TILT-TURN
* `Kit Vorne OB 100kg`
* leaf weight `26.55`
* max 100.00

Geometría G1–G4:
SIN CAMBIOS.

---

# TESTS OBLIGATORIOS

Además de Gold Cases:

Hardware:

* normalize mappings
* explicit hardware_set_sku success/failure
* zero candidates
* ambiguous candidates
* candidate rejected by dimensions
* candidate rejected by weight
* hardware weight fallback

Weights:

* article authority beats fallback
* PVC fallback ×1.10
* steel fallback ×1.10
* persisted hardware weight beats fallback
* panel without weight fails
* no double rounding

Door:

* one-weld-end jamb
* two-weld-end head
* threshold no weld/no steel
* panel not GlassPiece

Snapshot:

* `make goldgen` deterministic
* second generation byte-identical
* `--check` pass
* one-byte mutation fails
* request contains actual DEMO UUID
* request contains POSTE-V
* hash changes if request changes
* hash changes if response changes
* no self-hash
* no inspector

Pricing:

* 100000 / 35%
* invalid margin 1.0
* negative cost

Regression:

* G1/G2/G3 geometry/G4 remain exact
* SHOT-05 canvas still passes
* OpenAPI/Orval no drift

---

# SECUENCIA

1. Incorporar PD-06-01…17 al plan.
2. Actualizar PRD-01.
3. Actualizar PRD-05 sólo con nota de frontera SHOT-06/08 si hace falta.
4. Actualizar PRD-FRONTEND por response SHOT-06.
5. Crear migraciones nuevas.
6. Actualizar seed.
7. Database Gate.
8. Revalidar Regla 0.
9. Implementar engine.
10. Resolver G3 hardware.
11. G5/G6/G7.
12. Weight/hardware/pricing.
13. Gold generator.
14. `make goldgen` explícito.
15. Commit del snapshot GENERADO.
16. `--check`.
17. OpenAPI/Orval.
18. suites completas.
19. `python scripts/check_dod.py all`.
20. cuatro required CI.
21. PR.
22. NO MERGE.

Si aparece otra contradicción normativa REAL:
`[PENDIENTE-DECISIÓN]`
y detente.

No conviertas un bug ordinario de implementación en PD.

---

# ENTREGA FINAL

Reporta:

* commits;
* HEAD;
* PR;
* diff;
* nueva matriz DB↔Engine N/N;
* migraciones;
* seed;
* G3 hardware;
* G5;
* G6;
* G7;
* pesos exactos/publicados;
* fallback tests;
* hardware ambiguity tests;
* pricing pure tests;
* `golden_example.json`;
* hash;
* prueba byte-to-byte;
* prueba de mutación;
* OpenAPI/Orval;
* G1–G4 regression;
* Extended xfails intactos;
* pytest engine;
* backend/frontend;
* Database Gate;
* gauntlet;
* cuatro jobs;
* warnings;
* `[PENDIENTE-DECISIÓN]`;
* contradicciones conocidas sí/no;
* git status.

NO MERGE.

APROBADO — EJECUTA FASE 2.

## 12. Resolución final PD-06-19/20 del owner (vigente)

[RESOLUCIÓN CANÓNICA PD-06-19 / PD-06-20 — SHOT-06]

Ambas pendientes quedan RESUELTAS.

Incorpora estas correcciones en:

`docs/plans/PLAN_SHOT-06.md`

y en los PRD activos afectados.

Después revalida Regla 0 / Regla 20.

Si no aparece otra contradicción normativa REAL:

APROBADO — CONTINÚA FASE 2.

---

# PD-06-19 — PESO G3 STANDALONE VS GOLDEN COMPUESTO

La cifra:

`26.55 kg`

NO corresponde al G3 standalone.

Corresponde exclusivamente a la hoja OB de `bay_2` del `golden_example.json` compuesto.

La resolución anterior queda corregida en este punto.

## G3 STANDALONE CANÓNICO

G3:

* nominal: `1000.00 × 1400.00`
* sash cuts:

  * H `902.00`, qty2
  * V `1302.00`, qty2
* sash steel:

  * H `866.00`, qty2
  * V `1266.00`, qty2
* glass:

  * `776.00 × 1176.00`
* hardware:

  * `KIT-TILT-TURN`
  * `Kit Vorne OB 100kg`
  * hardware weight `2.50 kg`

### PVC exacto

Longitud:

`2×902 + 2×1302 = 4408 mm = 4.408 m`

Peso:

`4.408 × 1.2000 = 5.2896 kg`

### Acero exacto

Longitud:

`2×866 + 2×1266 = 4264 mm = 4.264 m`

Peso:

`4.264 × 1.7000 = 7.2488 kg`

### Vidrio exacto

Área:

`0.776 × 1.176 = 0.912576 m²`

Espesor neto DVH:

`8.00 mm`

Peso:

`0.912576 × 8 × 2.50 = 18.251520 kg`

### Hardware

`2.500000 kg`

### Total exacto

`5.2896 + 7.2488 + 18.251520 + 2.500000`

=

`33.289920 kg`

Output público:

`33.29 kg`

Por tanto:

G3 standalone:

`leaf_weight = 33.29 kg`

y:

`33.289920 <= 100.00`

Debe seleccionar:

`KIT-TILT-TURN / Kit Vorne OB 100kg`

## GOLDEN COMPUESTO

El golden compuesto tiene otra geometría.

Hoja OB `bay_2`:

* sash:

  * `672.00 ×2`
  * `1302.00 ×2`
* steel:

  * `636.00 ×2`
  * `1266.00 ×2`
* glass:

  * `546.00 ×1176.00`
* hardware:

  * `2.50 kg`

PVC:

`4.7376 kg`

Steel:

`6.4668 kg`

Glass exact:

`12.841920 kg`

Hardware:

`2.500000 kg`

Total exacto:

`26.546320 kg`

Output:

`26.55 kg`

Por tanto quedan congelados DOS valores distintos:

* G3 standalone → `33.29 kg`
* golden compuesto `bay_2` → `26.55 kg`

No deben compartir una expectation de peso.

## TESTS

Añade tests independientes.

### G3

Debe demostrar:

* geometry G3 intacta;
* KIT-TILT-TURN;
* `leaf_weight.total_weight_kg == 33.29`;
* exact internal total `33.289920`;
* kit max `100.00`.

### Golden compuesto

Debe demostrar:

* bay_2 geometry intacta;
* KIT-TILT-TURN;
* output `26.55`;
* exact internal total `26.546320`.

La diferencia es esperada y está causada por dimensiones distintas de hoja/vidrio.

No modifiques G3 para forzar 26.55.

No modifiques el golden compuesto para forzar 33.29.

---

# PD-06-20 — JUNQUILLOS DEL PANEL G7

G7 SÍ lleva junquillos de retención para el panel sándwich.

No se introduce una fórmula especial de puerta.

El panel usa el mismo contrato de retención perimetral por junquillo que cualquier infill alojado en el pocket de la hoja.

## REGLA

Para un infill con espesor compatible:

`bead_cut = infill_length + bead_rule.cut_add_mm`

DEMO_60:

Panel:

`696.00 × 1928.00`

Espesor:

`24.00 mm`

Regla DEMO_60:

`cut_add_mm = 9.00`

Por tanto:

Horizontal:

`696.00 + 9.00 = 705.00 mm`

qty:

`2`

Vertical:

`1928.00 + 9.00 = 1937.00 mm`

qty:

`2`

G7 queda congelado con:

* panel `696.00 × 1928.00`
* bead H `705.00`, qty2
* bead V `1937.00`, qty2

## SELECCIÓN DE REGLA

La selección del junquillo se realiza por ESPESOR DEL INFILL.

Para G7:

`PanelRule.thickness_mm = 24.00`

→ selecciona la regla de junquillo DEMO_60 correspondiente a `24.00 mm`.

No hardcodear SKU de bead dentro de DOOR_ENTRY.

## NORMALIZACIÓN SEMÁNTICA

El nombre histórico DB:

`glazing_bead_matrix.glass_thickness_mm`

se conserva por compatibilidad de esquema.

NO reescribas migraciones históricas sólo para renombrarlo.

Pero desde SHOT-06 su semántica normativa queda ampliada:

`thickness of retained infill`

es decir:

* vidrio;
* panel;
* otro infill futuro explícitamente soportado.

En el engine evita acoplar la selección a `GlassPiece`.

Puede existir helper neutral:

`resolve_bead_rule(infill_thickness_mm, params)`

o equivalente.

No dupliques:

`resolve_glass_bead_rule`
+
`resolve_panel_bead_rule`

si ambos implementan exactamente la misma tabla.

## OUTPUT

Los junquillos de panel siguen siendo:

`ProfileCut`

con role:

`GLAZING_BEAD`

y:

* `bay_id` de G7;
* `leaf_id` de la puerta.

No crear:

`PanelBeadPiece`

salvo que exista otro requisito normativo real.

## PANEL ≠ GLASS

Esta resolución NO convierte el panel en vidrio.

G7 continúa generando:

`PanelPiece`

y NO:

`GlassPiece`

para el panel.

La única infraestructura compartida es la regla física de junquillo.

No aplicar:

* densidad de vidrio;
* glass_spec;
* glass weight;
* GlassPiece;

al panel.

## G7 CORE ACTUALIZADO

G7 debe producir ahora:

FRAME:

* head `956.00`
* jamb `2153.00 ×2`

THRESHOLD:

* `830.00`

DOOR SASH:

* H `822.00 ×2`
* V `2054.00 ×2`

SASH STEEL:

* H `786.00 ×2`
* V `2018.00 ×2`

PANEL:

* `696.00 ×1928.00`

PANEL BEADS:

* `705.00 ×2`
* `1937.00 ×2`

HARDWARE:

* `KIT-DOOR-MULTIPOINT`

LEAF WEIGHT:

* `32.35 kg`

Los beads NO se suman al leaf weight aprobado en SHOT-06.

El peso de junquillos pertenece al BOM/material consumption, no al hardware-selection leaf weight del Core Gate actual.

No cambies `32.35 kg` por añadir bead weight.

---

# GOLDEN SNAPSHOT

PD-06-20 NO modifica el golden compuesto actual porque ese request no contiene panel.

PD-06-19 mantiene:

golden `bay_2`:

`26.55 kg`

No sustituirlo por G3 `33.29`.

---

# MANIFEST / DOCS

Actualiza cualquier texto que actualmente afirme:

`G3 leaf weight = 26.55`

a:

`G3 standalone = 33.29`

Y deja explícito:

`golden composite OB bay_2 = 26.55`

Actualiza G7 para incluir:

* panel beads `705 / 1937`.

No cambies los valores históricos de G1–G5.

---

# MATRIZ DB ↔ ENGINE

La matriz prevista continúa:

`27/27`

si no aparece otra autoridad nueva durante implementación.

PD-06-20 NO añade columna.

Reutiliza la matriz de junquillos existente mediante `24.00 mm`.

Runtime actual puede seguir en 23 hasta ejecutar las migraciones aprobadas de SHOT-06.

No declares 27/27 runtime antes de que dichas migraciones/models estén implementados y probados.

---

# CONTINUACIÓN

Después de incorporar estas dos resoluciones:

1. `git diff --check`
2. Regla 0
3. Regla 20
4. confirma que no existen `[PENDIENTE-DECISIÓN]` abiertas;
5. comienza migraciones NUEVAS;
6. Database Gate;
7. seed;
8. adapter;
9. engine;
10. G3 hardware;
11. G5;
12. G6;
13. G7;
14. weight;
15. hardware;
16. pricing pure;
17. golden generator;
18. snapshot generado;
19. OpenAPI/Orval;
20. regresión G1–G4;
21. Extended xfails;
22. suites;
23. `python scripts/check_dod.py all`;
24. PR protegido;
25. cuatro required checks.

NO MERGE.

Si aparece otra contradicción normativa REAL:

`[PENDIENTE-DECISIÓN]`

y detente.

APROBADO — CONTINÚA FASE 2.

## 13. Registro de ejecución Fase 2

- Fuentes activas actualizadas; Regla0/20 sin pendientes abiertos.
- Baseline conservado en `fa3616fda9645bda5092e7c0cb9de80ecd8495b9`; rama `shot-06`, sin commits/push/PR.
- Corrida limpia `scratch/database-resume-2.log`: EXIT CODE 0; cuatro migraciones (dos históricas intactas y dos nuevas), seed, DB lint sin errores, 114 pgTAP, 20 integration tests y PostgreSQL16 independiente.
- G3 hardware y G5/G6/G7 implementados; pruebas independientes congelan dimensiones, kits, pesos exactos y públicos.
- Checker de mutaciones: 20/20 mutantes ±0.01 mm muertos por assertions en copias temporales; nunca se modifica el checkout.
- Generador/hash puro y modo `--check` implementados. Snapshot aún NO generado; sólo se creará con `make goldgen` después de validar la conexión de catálogo.
- OpenAPI/Orval generados por sus herramientas; fixtures Canvas adaptados, TypeScript pasó. Sin UI nueva.
- G10 mantiene destino SHOT-24 y ahora tiene xfail estricto ejecutable; G8/G9/G11/G12 conservan SHOT-06B. Última suite: 76 passed + 5 xfailed, prueba de bytes aún no ejecutada porque falta generación autorizada.
- Campos de SystemParams: 27 tipados; prueba de paridad DB completa añadida y pendiente corrida. No se declara todavía consumo runtime 27/27.
- GNU Make 3.81 portable disponible en scratch ignorado; sin dependencia productiva ni binario a commitear.
- Pendientes: paridad DB final, generación golden, validaciones completas, gauntlet, commits, push/PR y cuatro checks. NO MERGE.


### Reanudación 2026-09-06 — evidencia adicional

- Se conservó íntegro el working tree de `shot-06`; ninguna migración histórica cambió.
- `scratch/database-catalog-parity-3.log`: Database Gate EXIT CODE 0, 128 pgTAP, 23 integration tests, PostgreSQL16 limpio, actualización DEMO de SHOT-05 poblado y rechazo/rollback de catálogo sin autoridades aprobadas.
- Paridad de todos los valores cargados con el fixture canónico: PASS; nuevos parámetros consumidos por G5/G6/G7 contra DB real. La interpretación de «27/27 consumidos» está consultada al owner: 22 campos participan en Core, 2 son metadatos (`system_code`, `depth_mm`) y 3 permanecen reservados (`sliding_lateral_clearance_mm`, `corner_bracket_loss_mm`, `hook_depth_mm`). No se inventan fórmulas para aumentar un contador.
- Backend unit/contract: 83 passed. Frontend Vitest: 44 passed; ESLint/TypeScript/Prettier/build pasaron. Se corrigió codificación de fixtures sin alterar texto normativo.
- `scripts/check_generated_api.py` ejecutado dos veces: ambas sin drift de bytes OpenAPI/Orval.
- `scratch/mutations-final.log`: 20/20 mutantes de fórmula muertos por assertions después del guard monoriel SHOT-24.
- G10 ahora tiene cobertura ejecutable estricta y destino SHOT-24; conteo real: 5 xfails (G8/G9/G11/G12 → SHOT-06B, G10 → SHOT-24).
- GNU Make 3.81 verificado y trasladado fuera del repo: `C:/Users/alios/AppData/Local/DekopenHostSetup/shot-06/make-portable/bin/make.exe`. `scratch/` confirmado ignorado. `make -n goldgen` resuelve al generador aprobado; snapshot aún no escrito.
- `.gitattributes` fija LF sólo para golden, OpenAPI y cliente generado, para conservar el contrato de bytes en Windows/Linux.
- GitHub confirmó `main` protegido, con checks obligatorios `Lint & Typecheck`, `Test Suite`, `Frontend Build`, `Database Gate`. No se alteró protección.
- Pendientes: aclaración del criterio de consumo antes del golden; E2E real en curso; generación canónica, byte-check completo, gauntlet, commits/push/PR y CI. NO MERGE.

### Continuación canónica 2026-09-06 — clasificación y golden

La instrucción del owner en `479763c5-9390-4469-b98e-cefe3bbef65c/pasted-text.txt`
resuelve la consulta anterior: DB↔Engine mapping **27/27**, Core consumption
**22/27**, metadata **2/27**, reserved **3/27**. No hay pendiente de decisión
abierta por este criterio. Las entradas anteriores son evidencia cronológica.

| Campo Core | Consumidor real |
|---|---|
| material | geometry.calculate_geometry: guard de material Core |
| effective_profile_articles | geometry._article; weight.base_leaf_weight |
| glazing_bead_rules | geometry.resolve_bead_rule |
| rebate_depth_mm | geometry._pocket_dimension y _append_bay |
| end_milling_overlap_mm | geometry._walk_node |
| sash_overlap_mm | geometry.single_rectangular_sash_geometry y _append_door |
| glass_clearance_white_mm | geometry.calculate_geometry |
| glass_clearance_foil_mm | geometry.calculate_geometry |
| pulley_height_mm | geometry._append_bay: G5 alto de hoja |
| central_overlap_mm | geometry._append_bay: G5 ancho de hoja |
| sliding_end_add_mm | geometry._append_bay: G5 ancho de corte |
| door_threshold_mm | geometry._append_door: alto exterior hoja |
| door_bottom_clearance_mm | geometry._append_door: alto exterior hoja |
| rail_type | hardware.resolve_hardware_kit; geometry._append_bay |
| pvc_weight_kg_m | weight.base_leaf_weight: fallback PVC |
| steel_weight_kg_m | weight.base_leaf_weight: fallback acero |
| hardware_kit_weight_kg | weight.with_hardware_weight: fallback kit |
| available_hardware_kits | hardware.resolve_hardware_kit |
| sliding_glazing_deduction_width_mm | geometry._append_leaf: G5 vidrio |
| sliding_glazing_deduction_height_mm | geometry._append_leaf: G5 vidrio |
| door_leaf_side_clearance_mm | geometry._append_door: ancho exterior hoja |
| available_panel_rules | geometry._append_leaf: panel G7 |

Metadata: `system_code`, `depth_mm`. Reserved: `sliding_lateral_clearance_mm`,
`corner_bracket_loss_mm`, `hook_depth_mm`. Los cinco están cubiertos por la
paridad completa DB/loader/model/fixture. `test_system_params_scope.py` congela
la partición, verifica los 22 consumidores y prueba cada reservado alterado
contra G3/G5/G6/G7 (12 combinaciones, salida completa idéntica).

- Baseline auditado: `shot-06`, HEAD `fa3616fda9645bda5092e7c0cb9de80ecd8495b9`,
  sin commits propios, rama remota ni PR. Inventario tras generar golden:
  40 archivos versionados con diff + 27 nuevos = 67; sujeto al inventario final.
- `.gitattributes` contiene sólo golden/OpenAPI/Orval: sin regla global, sin
  binarios ni normalización del resto del repo.
- `make goldgen` ejecutado con GNU Make del host, fuera del repositorio.
  Segunda ejecución produjo bytes idénticos. Snapshot nunca editado a mano.
- Golden: UUID `3067da09-3119-5ad0-a1d5-498cd2dfd753`, `POSTE-V`, request
  1500.00 × 1400.00, SPLIT_V 750.00, bay_1 FIXED, bay_2 TILT_TURN_RIGHT.
  Respuesta con exactamente siete claves, panels vacío y OB 26.55 kg.
- calculation_hash: `sha256:562cdc97337a690f09db12590ee8a99b420ebc6b7dbf9c40a4d4755132d24f21`.
- Snapshot tests: 7 PASS. UTF-8/LF, un newline final, orden de claves,
  Decimal→string, sensibilidad de hash a request/response/arrays, exclusión
  de self-hash y mutación de un byte rechazada sin escritura. Canónico intacto.
- `snapshot.py` auditado: serialización y hash puros. I/O sólo en generador/tests.
- Mutaciones dirigidas: 20/20 killed por assertions, sin fallos de colección.
- Fallo E2E anterior: 313–346 ms; traza mostró espera HTTP predominante.
  Construir el contexto TLS en cada auth request costaba 208–276 ms en Windows.
  Se reutiliza exclusivamente la configuración TLS del verificador; cada token
  sigue consultando al servidor. Test verifica certificados obligatorios,
  hostname, headers por petición y rechazo de una segunda respuesta 401.
- Primera comprobación E2E de la corrección fue interferida por la regeneración
  Orval que disparó recargas Vite; no se acepta como evidencia de rendimiento.
  La corrida final secuencial verificará el límite original de 300 ms.
- Suites unitarias actuales: 177 PASS, 5 xfailed. Lint y tipos estrictos PASS
  tras anotar explícitamente el mapa de consumidores. Pendiente gauntlet total,
  auditoría final, commits por subsistema, PR y cuatro checks. NO MERGE.

### Gauntlet final local — 2026-09-06

`python scripts/check_dod.py all` terminó con **EXIT CODE 0**; evidencia local
en `scratch/gauntlet-final.log` (ignorada, sin credenciales productivas).

| Gate | Resultado |
|---|---|
| Ruff / ESLint / Prettier / TypeScript | PASS, sin warnings |
| mypy engine estricto | PASS, 26 archivos |
| Django check | 0 issues, 0 silenced |
| Engine completo | 93 PASS + 5 xfails canónicos |
| Backend completo | 107 PASS, incluidos 23 integration DB |
| Vitest | 44 PASS / 8 archivos |
| Playwright Chromium real | 3 PASS |
| Canvas commit→paint, cinco medidas | 67.300 / 67.500 / 66.700 / 65.900 / 66.200 ms |
| Supabase limpio / DB lint | PASS, cuatro migraciones + seed, sin warnings |
| pgTAP | 128 PASS / 5 archivos |
| PostgreSQL 16 independiente | PASS |
| Upgrade SHOT-05 DEMO poblado | PASS, datos históricos preservados |
| Catálogo sin autoridades | Rechazo explícito y rollback atómico PASS |
| Golden read-only / OpenAPI spectacular + Orval | PASS, sin drift |
| Mutation checker | 20/20 killed por assertions Core |
| Build producción | PASS, 141 módulos |

| Caso | Dimensiones congeladas mm | Kit | Peso exacto → público kg |
|---|---|---|---|
| G3 | sash 902/1302; steel 866/1266; glass 776×1176 | KIT-TILT-TURN | 33.289920 → 33.29 |
| G5 | frame 2006/2106; sash 966/1956; steel 930/1920; glass 820×1810; bead 829/1819; dos hojas | KIT-SLIDING ×2 | 48.8868 → 48.89 por hoja |
| G6 | frame 1206/806; sash 1102/702; steel 1066/666; glass 976×576; bead 985/585 | KIT-AWNING-16 | 23.96192 → 23.96 |
| G7 | head 956; jamb 2153; threshold 830 ALUMINIUM; frame steel 920/2120; leaf outer 816×2048; sash 822/2054; steel 786/2018; panel 696×1928; bead 705/1937 | KIT-DOOR-MULTIPOINT | 32.35488 → 32.35 |

- Hardware: SKU explícito, incompatibilidad, cero/uno/ambigüedad, límites
  inclusivos de ancho/alto/peso y peso propio de cada kit probados.
- Weight: exactitud previa a cuantización, prioridad del peso persistido,
  fallback PVC/acero/kit, panel sin densidad rechazado y ausencia de doble
  redondeo probados. Junquillos excluidos de masa móvil según autoridad.
- Pricing exclusivamente puro: 100000 / (1 - 0.3500) = 153846.15; margen 1
  y costo negativo rechazados. Sin integración comercial añadida.
- G1–G4: assertions dimensionales originales intactas; sólo se actualizaron
  expectativas de hardware resuelto. Tolerancia 0.00 mm.
- G8 = strict xfail → SHOT-06B. G9 = strict xfail → SHOT-06B.
  G10 = strict xfail ejecutable → SHOT-24. G11 = strict xfail → SHOT-06B.
  G12 = strict xfail → SHOT-06B. Destinos preservados individualmente.
- Los hashes de los 70 archivos con cambios permanecieron idénticos durante
  gauntlet y mutaciones. Tras verificarlo se restauró únicamente CRLF nativo
  en tres archivos no generados para evitar avisos Git; sin cambio semántico.
- Auditoría: UTF-8 válido, sin archivos binarios, sin patrones de credenciales
  en cambios, sin scratch ni tooling del host a versionar; migraciones
  históricas byte-equivalentes a HEAD, nuevas migraciones separadas.
- Cero warnings de las suites finales, cero pendientes de decisión activos,
  cero contradicciones conocidas. Las PD históricas resueltas se conservan.
- Autorización vigente: commits por subsistema y PR a main protegido;
  verificar los cuatro required checks. **NO MERGE**, sin tag de cierre.
