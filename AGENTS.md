# AGENTS.md — PROTOCOLO OPERATIVO DEL BUILDER Y MAPA DE AUTORIDADES

> **Para cualquier agente o LLM constructor (Astra, Claude, Codex, Gemini, Antigravity):**
> Este archivo es el punto de entrada y mapa obligatorio antes de ejecutar cualquier tarea en Dekopen.
> `AGENT FILES REFERENCE THE CONSTITUTION; THEY DO NOT FORK IT.`

---

## 1. Qué es Dekopen

Dekopen es el **primer sistema operativo de ingeniería, cálculo paramétrico, optimización de corte 1D y cotización comercial para talleres y fabricantes de ventanas de PVC y aluminio** en Chile y Latinoamérica.
- **Tolerancia Matemática Innegociable:** `0.00 mm`. Todo cálculo numérico proviene del motor determinista puro `/engine`, **jamás** de inferencias o texto libre de un LLM.
- **Invariantes del Sistema:** Tipado `Decimal` para dimensiones y dinero (cero `float`), aislamiento multi-tenant estricto vía PostgreSQL RLS con `current_user_org_ids()`, auditoría previa obligatoria (`ai_audit_logs`, `price_audit_logs`), e interfaz Studio Light / Dark Graphite basada en tokens CSS semánticos (cero hex crudo).

---

## 2. Mapa de Autoridades y Precedencia Normativa

Toda decisión técnica en Dekopen se rige por la siguiente jerarquía estricta de fuentes:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ NIVEL 1: CONSTITUCIÓN DEL BUILDER (v1.3 MASTER — 23 REGLAS SUPREMAS)   │
│ Archivo: docs/CONSTITUTION.md — Única Norma Suprema Inapelable           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ NIVEL 2: PLAN MAESTRO DE SHOTS (ROADMAP V1)                             │
│ Archivo: docs/PRD/PLAN_SHOTS.md — Secuencia de 24 Shots y Gates         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ NIVEL 3: ESPECIFICACIONES TÉCNICAS ACTIVAS DE DOMINIO                   │
│ Directorio: docs/PRD/*.md (PRD-00 a PRD-20)                             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ NIVEL 4: PLANES Y REGISTROS DE SHOTS ACTIVOS / CERRADOS                 │
│ Directorio: docs/plans/PLAN_SHOT-XX.md                                  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ NIVEL 5: GUÍA OPERATIVA Y MAPA DE CALIDAD (NO NORMATIVOS)               │
│ Archivos: docs/AGENT_OPERATING_MODEL.md y docs/QUALITY_SCORE.md         │
└─────────────────────────────────────────────────────────────────────────┘
```

- **Archivos en Raíz:** Los archivos `docs/PRD-*.md` son exclusivamente punteros normativos que redirigen a `docs/PRD/`.
- **Archivo Histórico:** `docs/archive/**` es `HISTORICAL / NON-NORMATIVE`. No tiene autoridad para vetar ni bloquear desarrollo activo.
- **Biblias Compiladas:** `DEKOPEN_BIBLIA_*.md` son `NON-NORMATIVE VIEW` (vistas de solo lectura para consulta humana). Ante cualquier discrepancia, gobiernan los archivos individuales de `docs/PRD/` y la Constitución.

---

## 3. Modelo de Contexto JIT ("Repo As Memory")

```
REPO = MEMORY
AGENTS = MAP
PROMPT = GOAL + DELTA + SUCCESS CRITERIA + STOP CONDITION
```

El historial del chat es efímero; el repositorio es la memoria persistente. Al iniciar o retomar una tarea, carga únicamente el contexto necesario según la **Escalera JIT**:
1. [`AGENTS.md`](./AGENTS.md) (este mapa).
2. [`docs/CONSTITUTION.md`](./docs/CONSTITUTION.md) (las 23 Reglas Supremas).
3. [`docs/PRD/PLAN_SHOTS.md`](./docs/PRD/PLAN_SHOTS.md) (gate contractual del shot).
4. `docs/plans/PLAN_SHOT-XX.md` del shot activo (decisiones aprobadas).
5. Únicamente los PRDs específicos y archivos de código afectados.

*Prohibido cargar por defecto la Biblia completa, todos los PRDs o transcripts históricos.*

---

## 4. Precedencia Temporal de Shots

```
GLOBAL FLEXIBILITY DOES NOT RETROACTIVELY DESTABILIZE AN ACTIVE OR CLOSED SHOT CONTRACT.
```

- Las decisiones técnicas de shots cerrados (SHOT-01 a SHOT-06) son contratos históricos consolidados.
- Si una decisión quedó formalmente congelada en un `PLAN_SHOT` activo mediante una propuesta aprobada (ej: `PD-07-27` definiendo S07 como modal en S06 durante SHOT-07), sigue siendo la ley contractual de ese shot y no se altera retroactivamente por flexibilidades futuras.

---

## 5. Protocolo de Escritor Único (Single Writer)

- **Un Solo Agente Escribe:** Solo el agente raíz modifica el árbol de trabajo canónico.
- **Paralelismo de Solo Lectura:** Se permite invocar subagentes concurrentes exclusivamente para tareas de lectura, auditoría (DB, frontend, seguridad) e investigación en el repositorio.
- **Integración:** El agente raíz consolida los hallazgos y resuelve bajo la Regla 0.

---

## 6. Condición de Parada Mecánica y Regla 0

El agente tiene **autonomía completa** (bias toward action) para resolver decisiones no materiales (layout flexible, composición interna, naming interno, refactorizaciones reversibles y adición de tests).

El agente debe **DETENERSE INMEDIATAMENTE** únicamente ante:
1. **Contradicción MATERIAL bajo Regla 0:** Discrepancia entre normas que modifique dimensiones, matemática, dinero, RLS, permisos, auditoría, datos certificados, hardware, stock, purchase list, cut plan, API contracts, persistence schemas o comportamiento observable determinista.
2. **Vacío Material (Regla 20):** Si la especificación omite un aspecto material, detenerse e insertar `[PENDIENTE-DECISIÓN]`.
3. **Acción Irreversible no Autorizada:** Operaciones destructivas o pushes/merges a ramas protegidas sin PR y CI.

*Reporte de Provenza:* Si una instrucción del repositorio detiene al agente, debe reportar por separado `RULE SAYS` (texto literal) de `AGENT INTERPRETS` (interpretación técnica).

---

## 7. Separación Maker / Checker Determinista

```
THE MAKER MAY EXECUTE EVERY DETERMINISTIC CHECKER AND REPAIR FAILURES AUTONOMOUSLY.
THE MAKER DOES NOT DEFINE, WEAKEN OR OVERRIDE THE CHECKER'S VERDICT.
PROTECTED CI PROVIDES THE INDEPENDENT INTEGRATION VERDICT.
```

- **Maker:** Escribe código, ejecuta tests focalizados, corre el Gauntlet y repara fallos de forma autónoma.
- **Checker:** El juez determinista (`scripts/check_dod.py`) configurado con rechazo por defecto.
- **Invariante:** El Maker no puede darse el visto bueno mediante texto libre, ni debilitar aserciones o filtros del checker para simular éxito.
- **Cero Verifier Theater:** No se requiere un segundo agente artificial cuando el Gauntlet determinista y el CI protegido certifican el resultado mecánicamente.

---

## 8. Verificación Progresiva y Reuso de Evidencia

```
NEVER REDUCE MATERIAL VERIFICATION COVERAGE.
ELIMINATE ONLY REDUNDANT VERIFICATION.

CORRECTNESS COMES FROM TARGETED PROOF + TRACEABLE EVIDENCE,
NOT FROM REPEATING THE SAME PROOF WITHOUT A RELEVANT DELTA.
```

- **Prueba Ligada a SHA:** Todo resultado de verificación es evidencia asociada a un SHA de commit exacto, al gate/test/revisión ejecutado, a su resultado y a la superficie de prueba cubierta. Un commit posterior **no** invalida automáticamente la evidencia previa: solo se invalidan las superficies de prueba que el delta puede afectar realmente.
- **Nivel 1 (Cambio Local):** Tests unitarios focalizados (`pytest engine/tests/test_x.py`, `ruff check .`).
- **Nivel 2 (Estabilización):** Suite del módulo afectado (`pytest engine/ -q`, `npm run test`).
- **Nivel 3 (Integración):** Tests relevantes de base de datos (`supabase test db`), RLS y navegador real (Playwright).
- **Nivel 4 (Cierre de Shot):** Gauntlet canónico completo (`python scripts/check_dod.py all`) — **obligatorio sobre el head material final de implementación del SHOT**.

**Selección por superficie de prueba:** la verificación se elige según la superficie que el delta toca, no porque exista otro commit:
- *Delta solo-documental* → consistencia/formato de documentación. No invalida engine, Golden, DB/RLS, backend, frontend, Playwright ni hashes matemáticos.
- *Delta frontend* → tests de componentes afectados, lint/typecheck, build de producción y E2E del flujo afectado.
- *Delta engine/matemática* → regresión focalizada, suite engine, Golden `--check` y mutaciones de las fórmulas/contratos tocados.
- *Delta DB/RLS/migraciones* → migraciones, pgTAP, tests RLS/integración y backend afectado.
- *Delta cross-cutting/material* → gates focalizados afectados primero y luego Gauntlet canónico antes de la aceptación final.

**Regla de Decisión para Gates Costosos:** antes de cualquier gate costoso, revisión completa, subagente o llamada de modelo de alto costo, preguntar: *¿qué nueva incertidumbre resuelve esta ejecución?* Si la respuesta es «ninguna; solo reconfirma evidencia vigente de la misma superficie de prueba», **no ejecutarlo**. Si el impacto es incierto, verificar: la calidad tiene prioridad sobre el ahorro de tokens.

> [!IMPORTANT]
> El Gauntlet canónico sigue siendo obligatorio para el head material final de un SHOT, pero **no** se requiere tras cada commit intermedio, ni porque el SHA material aprobado se haya mergeado limpiamente, ni tras commits de cierre solo-documentales. Los 4 contextos de CI protegido permanecen obligatorios e intactos como veredicto independiente de integración.

---

## 9. Finalización Basada en Evidencia y Política Golden

- **Condición de Parada Mecánica:** El head material final de implementación de un SHOT concluye única y exclusivamente cuando el Gauntlet devuelve `exit code 0` con 0 warnings, 0 float, $0.00\text{ mm}$ de error y 22/22 mutaciones abatidas. Para deltas acotados (p. ej. solo-documentales), la tarea concluye cuando la evidencia requerida para la superficie de prueba afectada está en verde y la evidencia SHA-bound previa sigue vigente.
- **Revisión Adversarial Única:** Una revisión adversarial completa del head material final es suficiente. Hallazgo → fix focalizado → test de regresión → gates afectados. No se reinicia la revisión de arquitectura completa salvo nuevo código material, nueva preocupación concreta o cambio de contrato afectado. *Revisión limpia + evidencia canónica vigente + CI requerido = STOP.*
- **Merge de Head Probado:** Si el head del PR es el SHA aprobado exacto con CI protegido en verde, mergear normalmente, verificar que el head aprobado es ancestro del merge y verificar CI de `main`. **No** repetir el Gauntlet local solo porque Git produjo un merge commit limpio; resolución de conflictos o ediciones funcionales manuales constituyen un nuevo delta material y se verifican según su superficie.
- **Commits Solo-Documentales:** No invalidan prueba técnica salvo que modifiquen un contrato normativo que cambie el comportamiento ejecutable esperado. Marcadores de cierre, actualizaciones de estado, typos, registros de evidencia y aclaraciones de prosa sin cambio de contrato **no** disparan verificación engine/DB/frontend/Playwright/Golden. Un cambio normativo de contrato PRD sí puede invalidar evidencia relevante y se trata según la superficie afectada.
- **Política Golden:** `GOLDEN = READ-ONLY` por defecto (verificación con `--check`). La regeneración con `make goldgen` está prohibida salvo cambio material de fórmula expresamente autorizado en el shot activo con diff auditado.

---

## 10. Doctrina Operativa del Agente

Para las directrices detalladas sobre:
- Doctrina *Production-Grade Increment* (`INCREMENTAL SCOPE != PROTOTYPE QUALITY`).
- Doctrina de *Token Efficiency* (ahorro de contexto sin pérdida de calidad).
- Matriz de *Reasoning Escalation* (Low a Max según tipo de problema).
- Neutralidad Tecnológica y de Proveedores (Clasificación de Tiers A a E).
- Registro de capacidades probadas.

👉 Consultar la guía operativa canónica: [`docs/AGENT_OPERATING_MODEL.md`](./docs/AGENT_OPERATING_MODEL.md) y el mapa de calidad [`docs/QUALITY_SCORE.md`](./docs/QUALITY_SCORE.md).
