# PRD-07: INSPECTOR TÉCNICO DE TALLER Y REGLAS DE FABRICABILIDAD (v1.1)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 1 (Núcleo)  
**Bloquea a:** PRD-06, PRD-08, PRD-14

---

## 1. Misión y Filosofía del Inspector

El Inspector Técnico de Dekopen (`/engine/inspector.py` y Pantalla **S07**) actúa como el "Jefe de Taller Digital". Su objetivo es detectar incompatibilidades físicas, excesos de peso y fallas normativas en tiempo real durante el diseño 2D, antes de cortar un solo perfil.

### Regla Constitucional de Comunicación
Ningún hallazgo del inspector puede presentarse como un código de error crudo o traza técnica. Todo hallazgo debe expresarse en lenguaje claro de taller de PVC, indicando:
1. **Qué ocurre** (Diagnóstico claro).
2. **Por qué es un problema** (Riesgo físico: descuelgue de hoja, filtración, rotura de vidrio).
3. **Cómo solucionarlo en 1 Clic** (Acción correctiva automatizada).

---

## 2. Reglas canónicas SHOT-07 — resolución owner 2026-09-06

La resolución íntegra PD-07-01…29 en `../plans/PLAN_SHOT-07.md` sustituye las
fórmulas y acciones históricas de esta sección. Constantes configurables por
sistema en inspector_rule_configs; tenant antes de global. Las14 configs son
obligatorias, sin fallback hardcoded; JSON parseado con Decimal, modelo por R.
Malformed/ausencia de config es InspectorConfigurationError, no finding ficticio.

| Regla | Autoridad y condición | Severidad | Fix |
|---|---|---|---|
| R01 | ExactLeafWeight.total_weight_kg (PVC+acero+infill+hardware) > selected kit.max_leaf_weight_kg; no suma pública redondeada | RED | BLOCKED_MISSING_AUTHORITY, sin kit/división inventados |
| R02 | H/W exteriores terminados fuera de [0.4000,2.5000]; sugerido1.5000 | YELLOW | SUGGESTION_ONLY |
| R03 | Dimensiones terminadas fuera de intersección Inspector/kit: W mínimo max(350,kit.min_w), W máximo min(1600,kit.max_w), H mínimo kit.min_h, H máximo min(2400,kit.max_h) | RED | SUGGESTION_ONLY |
| R04 | Área exacta width*height/1000000; MONOLITHIC_4 >1.8000, DVH_4_ANY_4 >2.6000 cualquiera sea cámara; panel N/A; otras clases sin límite MISSING_INPUT | RED | SUGGESTION_ONLY |
| R05 | span>1800: actual Ix de reinforcement_articles.ix_cm4 < required_ix_cm4 externo aprobado, con structural_basis; falta requisito/dato requerido MISSING_INPUT; span<=1800 N/A | RED | BLOCKED_MISSING_AUTHORITY |
| R06 | Espesor infill no existe en glazing_bead_rules: glass_thickness_mm para vidrio, PanelRule.thickness_mm para panel; preflight antes del acceso estricto | RED | SUGGESTION_ONLY |
| R07 | Ancho nominal/opening>800 exige tres drenajes inferiores; WorkshopAnnotations.bottom_drain_holes_mm, coordenadas Decimal dentro del vano; observación ausente MISSING_INPUT | YELLOW | AUTO_FIXABLE sólo exactamente dos, centro ausente/válido y requisito3; agregar width/2. Otros casos sugerencia |
| R08 | closing_points_perimeter_mm, origen esquina superior izquierda, sentido horario, 0<=p<perimeter; ordenar y comparar todos los gaps incluido wrap; máximo>800; datos insuficientes MISSING_INPUT | YELLOW | SUGGESTION_ONLY |
| R09 | continuous_width_mm>4000 WHITE o >3000 FOILED y sin has_coupler; acabado foliado sólo tests puros, producción WHITE | RED | BLOCKED_MISSING_AUTHORITY |
| R10 | MEDICIONES measured_d1_mm/measured_d2_mm, abs(diff)>1.50; sólo WORKSHOP_QC; DESIGN N/A | RED | SUGGESTION_ONLY |
| R11 | profile_systems.chamber_clearance_mm fuera de expected12±1.50; DEMO12 explícito; sin ecuación con overlap8, que es sólo recomendación | RED | SUGGESTION_ONLY |
| R12 | Fixture puro SLIDING_3L, ancho>4500 exige Ix>=45.0000; no ejecutar geometría3L | RED | BLOCKED_MISSING_AUTHORITY |
| R13 | AWNING, altura exterior terminada>1200 y selected_kit.stay_arms_qty<2; negativo puro, sin nuevo kit | YELLOW | SUGGESTION_ONLY |
| R14 | Fixture puro mono con masa exacta>150 exige carriages_qty>=4 y carriage_capacity_kg>=80; capacidad ausente MISSING_INPUT; no geometría mono | RED | BLOCKED_MISSING_AUTHORITY |

Estos son los valores DEMO de configuración autorizados, no constantes ocultas.
R01/R06 no duplican umbrales de catálogo. R14 usa capacidad por carro según
resolución PD24; sustituye el ambiguo texto histórico por rueda.

### R05: frontera estructural

Referencia owner: NCh432:2025 — Diseño estructural - Cargas de viento.
SHOT07 NO implementa solver de viento: required_ix_cm4 procede de autoridad
estructural externa/usuario/proyecto aprobada y structural_basis documenta su
base. No derivar de zona/altura/heurística/prompt. Comparar Ix NO certifica
cumplimiento NCh432. Ausencia: “Falta la exigencia estructural de viento para
verificar este travesaño.” Sin RF-HEAVY ni sustitución automática.

### Facts y cálculo estricto

evaluate_hardware_candidates puro compartido devuelve opening_match,
rail_match, width_match, height_match, exact_total_weight, weight_match.
resolve_hardware_kit es wrapper estricto y conserva selección/error SHOT06.
Candidato opening/rail/dim que falla sólo peso permite diagnóstico R01;
límites dimensionales permiten R03. Múltiples compatibles son error de
configuración/AmbiguousHardwareKit, no finding del usuario. R06 preflight.
Inspector reutiliza geometría/peso exactos; no los recalcula. No fabricar
EngineResult exitoso si el cálculo estricto falla.

## 3. Estados, hallazgos y bloqueo

RuleEvaluationStatus: PASS, FAIL, NOT_APPLICABLE, MISSING_INPUT.
InspectorFinding: rule_id R01…14, severity YELLOW/RED, title, diagnosis, risk,
recommendation, fixability, bay_id/leaf_id nullable, fix nullable. Lenguaje humano.
InspectorResult: status GREEN/YELLOW/RED, production_allowed, evaluations,
findings, source_calculation_hash nullable.
Sin findings GREEN; sólo YELLOW → YELLOW; cualquier RED → RED.
MISSING_INPUT de regla aplicable genera finding con severidad de esa regla;
R10 DESIGN es N/A. production_allowed es FALSE con RED, TRUE GREEN/YELLOW.
WorkshopReadiness además exige cut_optimization.ok. Config inválida, stock
faltante/ambiguo o pieza que no cabe hacen readiness false sin falsear semáforo.
“Aprobar para Taller” sólo gate UI, sin orden/OT/project status/version.

## 4. Corrección real y transacción

InspectorDiff: diff_id, rule_id, target, preconditions, operations discriminadas.
SHOT07 permite ADD_BOTTOM_DRAIN_HOLE, con target/old_value/new_value. No JSON
Patch arbitrario. Fixture width1000, exactamente dos posiciones válidas y centro
ausente: preview agrega500. Clic, precondiciones, draft, POST calculate, POST
inspect; commit local sólo si ambos success; error rollback exacto. Reaplicar
no duplica; precondiciones obsoletas fallan sin mutar. R07 desaparece por
reevaluación, hash geométrico idéntico. Nada de DB/proyectos/OT.
Pulso300ms, semáforo previous→recomputed en150ms, nunca forced GREEN/unlock.

## 5. Pruebas y alcance

Cada R requiere PASS/FAIL y fronteras/ausencias aplicables. Matriz numérica
completa y pruebas BFD/API/UI/fix en resolución íntegra del plan SHOT07.
R12/R14 sólo fixtures puros; G8/G9/G11/G12→06B y G10→24 siguen cinco xfails.
G1–G7, cálculo/hash/golden, pesos/herrajes, auth/RLS y Canvas<300ms intactos.
