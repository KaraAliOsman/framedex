# Plan de Implementación — SHOT-03: Engine núcleo G1–G4

## 1. Identificación y condición de entrada

- **Shot:** `SHOT-03` — Engine núcleo: models, geometry
  `FIXED`/`TURN`/`TILT_TURN`/`MULLION` y BOM base.
- **Branch:** `shot-03`.
- **Base canónica verificada:**
  `main@990cc2a2e86930e207afea1215cce50417e0aee0`.
- **Fuentes normativas:** `docs/PRD/PRD-01.md` §§2–4, §5.1 y §6 sólo
  G1–G4; `docs/PRD/PRD-04.md` §2 sólo para el árbol paramétrico; y
  `docs/PRD/PRD-FRONTEND-APIS-COMPONENTS.md` §1.1 sólo para compatibilidad
  de salida/BOM. Las referencias `M9`/`M5` fueron resueltas como residuo
  inválido y no autorizan pricing, billing ni API.
- **Gate textual:** `pytest engine/` demuestra G1, G2, G3 y G4 con
  discrepancia exacta `0.00 mm`; G8, G9, G11 y G12 quedan declarados
  `xfail`.
- **Stop condition final:** `python scripts/check_dod.py all` devuelve un
  exit code real `0`, seguido por los cuatro jobs protegidos de CI en
  `completed/success`.
- **Estado de esta fase:** FASE 2 reanudada. PD-01…PD-09 están formalmente
  resueltas; no queda un bloqueo normativo conocido antes de implementar.

## 2. Lecturas y contratos inspeccionados

Se leyeron antes de planificar, en el orden obligatorio:

1. `AGENTS.md`.
2. `docs/CONSTITUTION.md`.
3. `docs/PRD/PLAN_SHOTS.md`.
4. `docs/PRD/PRD-01.md` completo.
5. Interfaces reales existentes en `engine/`:
   `engine/pyproject.toml`, `engine/src/dekopen_engine/__init__.py`,
   `engine/tests/test_package.py` y
   `engine/tests/GOLD_CASES_MANIFEST.json`.
6. Contratos producidos por SHOT-02 relevantes para el motor:
   `docs/PRD/PRD-02.md`, la migración SQL, `supabase/seed.sql`,
   `backend/tests/test_database_contract.py` y
   `docs/plans/PLAN_SHOT-02.md`.
7. Harness real: `scripts/check_dod.py`, `Makefile`, configuración de mypy,
   dependencias y `.github/workflows/ci.yml`.

No se usaron documentos de `docs/archive/` como fuente funcional.

## 3. Objetivo exacto

Construir un paquete Python puro,
determinista y estrictamente tipado que:

1. represente con `Decimal` el árbol mínimo y los parámetros necesarios para
   G1–G4;
2. preserve artículos efectivos distintos por rol y derive siempre
   `welding_loss_per_end(article) = article.welding_loss_mm / Decimal('2')`;
3. calcule marco, refuerzo de marco, fijo, hoja practicable,
   oscilobatiente, poste/travesaño y sus vidrios únicamente con fórmulas
   canónicas aprobadas;
4. emita el BOM base mediante un contrato explícito, sin precios,
   optimización 1D ni I/O;
5. demuestre los cuatro G-cases con comparaciones exactas, no tolerancias
   permisivas;
6. mantenga las tipologías diferidas fuera del dispatcher implementado y
   visibles como `xfail` estrictos.

## 4. Alineación global

### 4.1. Upstream consumido

- **SHOT-01:** paquete `engine`, Python 3.12, pytest, ruff, mypy estricto,
  checker fail-closed y cuatro jobs de CI.
- **SHOT-02:** enums y columnas de `profile_systems`/`profile_articles`, seed
  `DEMO_60`, roles `FRAME`, `SASH`, `MULLION_V`, `MULLION_H` y
  `GLAZING_BEAD`, y autoridad exclusiva
  `profile_articles.welding_loss_mm`.
- **PRD-01 §5.1 congelado:** artículos efectivos separados por rol; no se
  introduce un scalar global de soldadura ni un loader con DB/I/O dentro de
  `/engine`.

### 4.2. Downstream que dependerá de este contrato

- **SHOT-04:** adaptador API, fuera del motor puro.
- **SHOT-05:** canvas 2D consume geometría, sin recalcular números.
- **SHOT-06:** extiende el dispatcher con SLIDING/AWNING/DOOR, resolución de
  hardware, pesos y golden snapshot generado.
- **SHOT-07:** optimización de corte e inspector consumen piezas de BOM.
- **SHOT-08/09/10:** pricing, documentos y versiones consumen el BOM sin
  alterar geometría.

Los modelos públicos de SHOT-03 deben ser suficientemente explícitos para
esos consumidores, pero no implementarán ninguna de esas capas futuras.

## 5. Alcance de archivos

### 5.1. Crear

| Archivo | Propósito | Aporte al gate |
|---|---|---|
| `engine/src/dekopen_engine/models.py` | Enums y modelos tipados aprobados para artículos efectivos, parámetros, nodo/árbol, piezas y resultado. Todos los valores dimensionales son `Decimal`. | Hace representables los inputs y outputs exactos de G1–G4 sin scalar global de soldadura. |
| `engine/src/dekopen_engine/geometry.py` | Funciones puras de soldadura por artículo y geometría aprobada para FRAME, FIXED, TURN, TILT_TURN y MULLION. | Produce las dimensiones que compara `pytest engine/`. |
| `engine/src/dekopen_engine/glass.py` | Derivar `thickness_net_mm` y construir `GlassPiece` desde área exacta, densidad `2500 kg/m³` y cuantización final `ROUND_HALF_UP`. | Mantiene vidrio/peso de G1–G4 determinista, sin `float` ni doble redondeo. |
| `engine/src/dekopen_engine/bom.py` | Ensamble determinista del BOM base conforme al modelo y reglas que apruebe el owner. | Expone las piezas críticas de G1–G4 para aserciones exactas. |
| `engine/tests/conftest.py` | Fixtures puras del catálogo efectivo DEMO_60; no consulta SQL ni red. | Reproduce el contrato SHOT-02 como inputs explícitos. |
| `engine/tests/test_models.py` | Validación de `Decimal`, enums, artículos por rol y separación FRAME/SASH. | Prueba el contrato DB↔Engine y evita regresión a un scalar ambiguo. |
| `engine/tests/test_gold_cases_core.py` | Casos G1–G4 y pruebas anti-mutación con igualdad exacta. | Gate directo G1/G2/G3/G4 = `0.00 mm`. |
| `engine/tests/test_gold_cases_deferred.py` | Declaraciones `xfail(strict=True)` de G8/G9/G11/G12 con razón normativa y ejecución contra tipos no soportados, una vez definidos sus inputs mínimos. | Demuestra el diferimiento sin implementar SHOT-06. |
| `engine/tests/test_purity.py` | Guardas contra imports de Django, DB, red e I/O externo y contra uso de `float`. | Hace verificable la pureza constitucional. |
| `supabase/migrations/20260902000000_add_glazing_bead_cut_add.sql` | Añadir `glazing_bead_matrix.cut_add_mm NUMERIC(6,2) NOT NULL` sin reescribir SHOT-02; backfill sólo DEMO_60 y fallo cerrado si existen filas sin autoridad. | Hace persistente el `+9.00 mm` canónico del junquillo. |

### 5.2. Modificar

| Archivo | Cambio limitado | Aporte al gate |
|---|---|---|
| `engine/src/dekopen_engine/__init__.py` | Exportar únicamente la API pública aprobada del núcleo. | Define una interfaz estable para tests y shots consumidores. |
| `engine/pyproject.toml` | Declarar Pydantic con el rango autorizado por PRD-00 §6 si los modelos normativos continúan siendo `BaseModel`. | Permite materializar exactamente el pseudomodelo de PRD-01. |
| `requirements-dev.txt` | Instalar el paquete `engine` editable para que CI resuelva sus dependencias declaradas, sin agregar paquetes fuera de la lista cerrada. | Igualdad entre entorno local y CI. |
| `engine/tests/GOLD_CASES_MANIFEST.json` | Cambiar G1–G4 al estado final aprobado y G8/G9/G11/G12 a `xfail`; conservar G5–G7 pendientes y G10 diferido. | El manifiesto deja de declarar falsamente que todo cálculo sigue pendiente. |
| `scripts/check_dod.py` | Endurecer el contrato del manifiesto y requerir los módulos/tests de SHOT-03; conservar todos los gates anteriores. | Evita un verde falso si faltan G1–G4 o los `xfail` obligatorios. |
| `docs/plans/PLAN_SHOT-03.md` | Registrar resoluciones, commits y evidencia real del cierre. | Memoria persistente Maker/Checker. |
| `docs/PRD/PLAN_SHOTS.md` | Eliminar el residuo `(+M9, M5)` de la fuente de SHOT-03. | Deja el alcance textual sin referencias inexistentes. |
| `docs/PRD/PRD-01.md` | Formalizar artículos/gaps por rol, reglas de mullion/junquillo, árbol consumido, BOM y `SystemParams` real. | Elimina contradicciones DB↔Engine antes de implementar. |
| `docs/PRD/PRD-04.md` | Añadir `glass_spec`/`glass_thickness_mm`, normalización top-level y dimensiones BAY derivadas. | Congela la entrada de G1–G4. |
| `docs/PRD/PRD-FRONTEND-APIS-COMPONENTS.md` | Delimitar el subconjunto puro de salida/BOM de SHOT-03, sin API/hash/inspector. | Mantiene compatibilidad downstream sin adelantar shots. |
| `supabase/seed.sql` | SASH cara `75.00`; MULLION cara `80.00`/gap `5.00`; FRAME/SASH gap `15.00`; matriz `cut_add_mm=9.00`. | Alinea fixtures efectivos con G1–G4. |
| `backend/tests/test_database_contract.py` y `supabase/tests/database/*.sql` | Probar columna, tipos, nulabilidad y seed exacto. | Evita drift estático y en PostgreSQL real. |
| `supabase/compat/postgres16_verify.sql` | Verificar los valores DEMO_60 actualizados sobre PostgreSQL 16. | Mantiene el Database Gate independiente. |
| `.github/workflows/ci.yml` | Aplicar también la nueva migración en el contenedor PostgreSQL 16 del Database Gate. | El gate limpio verifica el esquema acumulado real. |

### 5.3. PROHIBIDO

- Modificar lógica backend/frontend, RLS, la migración histórica de SHOT-02 o
  el tag `shot-02`. Sólo se autorizan el contrato DB estático, la nueva
  migración acumulativa, seed y Database Gate enumerados en §5.2.
- Importar Django, ORM, psycopg, sockets, HTTP, filesystem o variables de
  entorno desde `/engine`.
- Introducir `float`, redondeos implícitos o números de negocio no presentes
  en una resolución canónica.
- Implementar adapters que consulten DB; los tests entregan valores ya
  cargados al límite puro del motor.
- Implementar SLIDING_2L/3L/4L, AWNING, DOOR_ENTRY, DOOR_DOUBLE, hardware
  matching, pesos, pricing, BFD, inspector, API, canvas o documentos.
- Implementar G5–G12, salvo las declaraciones `xfail` exigidas para
  G8/G9/G11/G12.
- Crear o editar manualmente `golden_example.json`; su generación está
  programada para SHOT-06 y actualmente no existe un snapshot que regenerar.
- Consumir features de `docs/archive/` o resolver un vacío mediante valores de
  ejemplo no autorizados.

## 6. Arquitectura propuesta, condicionada a las decisiones

```text
inputs tipados + artículos efectivos por rol
                    │
                    ▼
          geometry.py (puro)
         ┌──────────┼───────────┐
         ▼          ▼           ▼
      perfiles    aceros      vidrios
         └──────────┼───────────┘
                    ▼
               bom.py (puro)
                    │
                    ▼
          resultado determinista
```

- `geometry.py` no selecciona catálogo ni conoce UUIDs/organizaciones.
- Cada cálculo que use soldadura recibe el artículo efectivo correspondiente.
- FRAME y SASH conservan variables distintas en la misma ejecución.
- MULLION_V y MULLION_H conservan identidad separada.
- El BOM no recalcula geometría: sólo ensambla las piezas devueltas por el
  núcleo conforme al contrato aprobado.

El nodo se basa exclusivamente en PRD-04 §2 y las precisiones de PD-04. El
resultado puro contiene `profile_cuts`, `reinforcements`, `glasses` y
`hardware_items=[]`; no incorpora API, hash ni inspector.

## 7. Trazabilidad de los G-cases

| Caso | Evidencia obligatoria | Resultado normativo | Estado del plan |
|---|---|---|---|
| G1 | Marco H/V, acero H/V, vidrio H/V y junquillo | `1006.00`, `970.00`, `910.00 × 910.00`, junquillo `919.00` mm | Contrato completo; implementación obligatoria. |
| G2 | Hoja H/V, acero H/V y vidrio DVH 24 mm | `702.00 / 1102.00`, `666.00 / 1066.00`, `576.00 × 976.00` mm | Contrato completo; implementación obligatoria. |
| G3 | Hoja H/V y vidrio DVH 20 mm | `902.00 / 1302.00`, `776.00 × 1176.00` mm | Geometría obligatoria; hardware queda en `xfail(strict=True)` para SHOT-06. |
| G4 | Poste, acero poste, vidrio fijo y vidrio OB | `1380.00`, `1370.00`, `830.00 × 1410.00`, `696.00 × 1276.00` mm | Contrato completo; implementación obligatoria. |

Cada valor se comparará mediante igualdad de `Decimal`. La discrepancia se
calculará como `abs(actual - expected)` y deberá ser exactamente
`Decimal('0.00')`; no se usará epsilon.

## 8. Estrategia Maker/Checker

1. Implementar primero contratos y funciones puras tras la resolución humana.
2. Añadir tests dirigidos por cada salida crítica, no sólo un test agregado.
3. Verificar que cambios de `0.01 mm` en una expectativa crítica hagan fallar
   el test correspondiente.
4. Ejecutar `python -m pytest engine/ -q -rxX` y conservar en el reporte las
   cuatro pruebas core y los cuatro `xfail` exigidos.
5. Ejecutar `python scripts/check_dod.py all` hasta exit code real `0`.
6. Commits convencionales y atómicos; push a `shot-03`; PR protegido sin
   merge autónomo.
7. Esperar los cuatro jobs: `Lint & Typecheck`, `Test Suite`,
   `Frontend Build` y `Database Gate` en `completed/success`.

## 9. Riesgos y mitigaciones

| Riesgo | Consecuencia | Mitigación |
|---|---|---|
| Ajustar fixtures para que coincidan con el Golden ignorando el catálogo | Verifier theater y ruptura DB↔Engine | Resolver primero los valores contradictorios; fixtures deben reflejar una única autoridad. |
| Definir silenciosamente un árbol o BOM | API inventada que bloquea shots futuros | Owner aprueba el contrato mínimo antes de implementar. |
| Reutilizar pérdida de soldadura entre roles | Catálogos asimétricos incorrectos | Artículo efectivo por rol y derivación por artículo, probada con FRAME/SASH distintos. |
| Mantener un checker que diga “calculation cases remain deferred” | Gauntlet verde sin G1–G4 | Endurecer el manifiesto/checker dentro del shot aprobado. |
| Implementar hardware o tipologías futuras para satisfacer una línea del PRD | Adelanto de SHOT-06 | Resolver el límite de G3; dejar dispatcher futuro no implementado. |
| Introducir Pydantic sólo en local | CI falla por dependencia ausente | Declararlo en el paquete y hacer que el bootstrap existente instale el paquete. |
| Confundir manifest con golden snapshot | Edición manual prohibida o estado falso | Modificar sólo estados del manifest; no crear/editar snapshots de cálculo. |

## 10. Registro de decisiones normativas

### PD-01 — RESUELTA: referencias M9/M5

`(+M9, M5)` es un residuo inválido y se elimina de `PLAN_SHOTS.md`. Las
autoridades quedan limitadas a PRD-01 §§2–4, §5.1 y G1–G4 de §6; PRD-04 §2
para el árbol; y PRD-FRONTEND §1.1 sólo para compatibilidad de salida/BOM.

### PD-02 — RESUELTA: SASH DEMO_60

`HOJA / SASH.face_width_mm = 75.00`; FRAME permanece `60.00`. Seed, tabla
DB↔Engine y contratos deben coincidir.

### PD-03 — RESUELTA: MULLION DEMO_60

MULLION_V/H usan cara `80.00` y gap `5.00`; FRAME/SASH usan gap `15.00`.
Así G4 deriva bays `800.00 × 1380.00`, poste `1380.00` y acero `1370.00`.

### PD-04 — RESUELTA: árbol y G4

Se usa `ROOT | SPLIT_H | SPLIT_V | BAY` de PRD-04 §2. El top-level puede ser
BAY/SPLIT o wrapper ROOT. `split_offset_mm` mide hasta el eje local del
mullion desde izquierda (`SPLIT_V`) o arriba (`SPLIT_H`). Los BAY reciben
`glass_spec`/`glass_thickness_mm`; sus dimensiones efectivas son derivadas.
G4 usa SPLIT_V `1800×1500`, offset `900`, POSTE-V, `bay_fixed` FIXED 24 mm
`4-16-4` y `bay_ob` TILT_TURN_RIGHT 20 mm `4-12-4`.

### PD-05 — RESUELTA: MULLION y junquillo

MULLION_V corta `parent_clear_height + 2×end_milling_overlap_mm` y MULLION_H
usa el ancho equivalente. Su acero resta `2×article.reinforcement_gap_mm`.
El junquillo selecciona `GlazingBeadRule` por espesor y suma el nuevo
`glazing_bead_matrix.cut_add_mm`; DEMO_60 congela `9.00` en cinco filas.

### PD-06 — RESUELTA: salida/BOM base

El resultado puro contiene `profile_cuts`, `reinforcements`, `glasses` y
`hardware_items`. Cortes y refuerzos preservan identidad, rol, longitud,
cantidad y `bay_id`; perfiles incluyen ángulos. `hardware_items=[]` en este
shot. No se implementan pricing, BFD, inspector, API ni hash.

### PD-07 — RESUELTA: gap y cara por artículo

`profile_articles.reinforcement_gap_mm` es la única autoridad del gap. Se
eliminan `steel_gap_corner_mm` y `steel_gap_mullion_mm` de `SystemParams`.
Cara, soldadura y gap se consumen desde cada `EffectiveProfileArticle`, sin
scalars globales que colapsen roles distintos.

### PD-08 — RESUELTA: hardware G3

G3 geométrico es gate obligatorio. La resolución del kit se difiere a SHOT-06
en una prueba separada `xfail(strict=True,
reason="SHOT-06: hardware_kits resolution")`; no hay lookup ni kit simulado.

### PD-09 — RESUELTA: área y peso de `GlassPiece`

- `area_m2_exact = (width_mm × height_mm) / Decimal('1000000')`; permanece
  sin cuantizar durante cálculos derivados.
- `GlassPiece.area_m2` cuantiza al final a `Decimal('0.0001')` con
  `ROUND_HALF_UP`.
- `FLOAT_GLASS_DENSITY_KG_M3 = Decimal('2500')` y su equivalencia
  `GLASS_WEIGHT_FACTOR_KG_M2_PER_MM = Decimal('2.50')` son constantes físicas
  del motor, nunca campos de `SystemParams`.
- El peso usa exclusivamente `thickness_net_mm`, derivado desde `glass_spec`
  sumando paños; no usa espesor total del DVH, cámara, gas ni separador.
- `weight_kg_exact = area_m2_exact × thickness_net_mm × Decimal('2.50')` y
  `GlassPiece.weight_kg` cuantiza una sola vez a `Decimal('0.01')` con
  `ROUND_HALF_UP`.
- Queda prohibido calcular peso leyendo el `area_m2` público ya cuantizado.
- Fixtures obligatorios: `680×1310 / 4-16-4 → 0.8908 / 17.82` y
  `546×1176 / 4-12-4 → exact 0.642096, publicado 0.6421 / 12.84`, más una
  prueba anti-doble-redondeo.

## 11. Condición de reanudación satisfecha

PD-01…PD-09 cuentan con resolución formal y la FASE 2 está autorizada. Antes
del cierre se repetirá Regla 0; cualquier vacío nuevo se registrará como
`[PENDIENTE-DECISIÓN]` y detendrá el trabajo sin inventar comportamiento.

## 12. Registro de construcción y verificación local

- Contrato normativo: `SystemParams` cubierto `23/23`; no existen scalars
  globales de cara, gap o soldadura.
- Implementación: `models.py`, `glass.py`, `geometry.py` y `bom.py` puros,
  sin Django, DB, red, I/O externo ni `float`.
- GlassPiece: densidad `2500 kg/m³`, factor `2.50 kg/m²/mm`, área exacta para
  peso y cuantización pública única `ROUND_HALF_UP`; fixtures A/B y prueba
  anti-doble-redondeo pasan.
- Casos core: G1, G2, G3 geométrico y G4 pasan mediante igualdad Decimal con
  discrepancia exacta `0.00 mm`; una mutación de `0.01 mm` es rechazada.
- Diferidos: G3 hardware y G8/G9/G11/G12 aparecen como cinco
  `xfail(strict=True)` con razón normativa.
- `python -m pytest engine/ -q -rxX`: `22 passed, 5 xfailed`.
- `python scripts/check_dod.py all`: exit code real `0`; Ruff, mypy, pytest,
  Vitest, build y contrato DB pasaron.
- Golden snapshot: no existe en SHOT-03 y no fue creado ni modificado; su
  generación canónica permanece en SHOT-06.
- `[PENDIENTE-DECISIÓN]` restante: ninguno.
- Contradicciones normativas conocidas tras la revalidación: ninguna.
