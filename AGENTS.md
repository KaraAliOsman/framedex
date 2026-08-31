# AGENTS.md — PROTOCOLO DE LOOP ENGINEERING & HARNESS PARA CODEX / CLAUDE / GPT-5.6

> **Para cualquier agente o LLM constructor:** Este archivo es el punto de entrada obligatorio antes de ejecutar cualquier tarea en Dekopen. Define la arquitectura, reglas constitucionales, la separación **Maker/Checker** y el protocolo de ejecución mediante el **Gauntlet Loop (Loop Engineering 2026)**.

---

## 1. Qué es Dekopen

Dekopen es el **primer sistema operativo de ingeniería, cálculo paramétrico, optimización de corte 1D y cotización comercial para talleres y fabricantes de ventanas de PVC y aluminio** en Chile y Latinoamérica.
- **Tolerancia Matemática Innegociable:** `0.00 mm`. Todo cálculo numérico proviene del motor determinista `/engine`, **jamás** de inferencias libres de un LLM.

---

## 2. Doctrina de Loop Engineering 2026 (Cherny / Osmani / Steinberger)

Para eliminar la alucinación, el "verifier theater" y los fallos en tareas de largo alcance:

1. **Separación Maker / Checker:** El agente que escribe el código (**Maker**) tiene estrictamente prohibido validar o darse el visto bueno a sí mismo. La validación la ejecuta un juez determinista e implacable (**Checker**: `scripts/check_dod.py`), configurado con **rechazo por defecto**.
2. **Condición de Parada Mecánica (Machine-Checkable Stop Condition):** Un shot no termina cuando el LLM dice que terminó. Termina única y exclusivamente cuando el Gauntlet devuelve `exit code 0` con 0 warnings, 0 float y $0.00\text{ mm}$ de error.
3. **Memoria Persistente en Archivo ("The Agent Forgets, the Repo Doesn't"):** La memoria entre sesiones no reside en el chat, sino en `docs/plans/PLAN_SHOT-XX.md` y `docs/PRD/PLAN_SHOTS.md`.
4. **Pruebas No-Vacías (Anti-Mutation Rule):** Todo test escrito en `/engine` debe ser sensible: si una fórmula varía en $\pm 0.01\text{ mm}$, el test **debe fallar**. Pruebas permisivas que aprueban código roto son eliminadas.

---

## 3. Matriz de Alineación Global (Visión 360° entre Shots)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               FLUJO GLOBAL DE DATOS EN DEKOPEN                                    │
└──────────────────────────────────┬───────────────────────────────────────────────────────────────┘
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
[ 1. Entrada de Datos ]    [ 2. Núcleo Matemático ]     [ 3. Capa de Negocio ]
  • S27 OCR (Gemini 3.7)     • Árbol Paramétrico (AST)    • Costos 5 Modos (SHOT-08)
  • S06 Canvas 2D (SVG)      • Despiece y Holguras        • Billetera y Ledger (SHOT-02/11)
  • S18 Inbound Email        • Corte 1D BFD (SHOT-07)     • Planes y Facturación
      │                            │                            │
      └────────────────────────────┼────────────────────────────┘
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
[ 4. Validación Gauntlet ] [ 5. Salidas Técnicas ]      [ 6. Certificación ]
  • Tolerancia 0.00 mm       • PDF Comercial (DOC-01)     • Sello T8 Doble Ciego (SHOT-21)
  • Reglas R01–R14           • Lista de Corte (DOC-03)    • QR de Fabricabilidad
  • Aislamiento RLS          • Visor 3D R3F (SHOT-19)     • Trazabilidad SHA-256
```

---

## 4. Reglas Constitucionales de Oro (CONSTITUTION.md v1.2)

1. **NÚMEROS:** Todo número en cotizaciones, cortes y OT sale de `/engine` o edición humana explícita. Prohibido float (`Decimal` en todo mm y dinero).
2. **MOTOR PURO:** `/engine` es independiente de Django, red, I/O o base de datos. Testeable con `pytest engine/`.
3. **RLS Y AISLAMIENTO:** Toda tabla de negocio lleva `org_id` + RLS con `current_user_org_ids()`. Un tenant jamás lee precios de otro.
4. **AUDITORÍA OBLIGATORIA:** Toda acción de IA en `ai_audit_logs` y todo cambio de precio en `price_audit_logs` ANTES de mutar estado.
5. **CASOS DE ORO (G1–G12):** Tolerancia `0.00 mm`. Ningún PR se aprueba con discrepancias en los casos de prueba.
6. **REGLA 20 (CERO SUPUESTOS):** Si un PRD tiene un vacío, **DETENTE** e inserta `[PENDIENTE-DECISIÓN]`. Nunca inventes reglas de negocio.
7. **REGLA 22 (GOLDEN SNAPSHOTS):** `golden_example.json` se genera con `make goldgen` desde `/engine`, jamás se edita a mano.

---

## 5. El Gauntlet Self-Healing Protocol (Ejecución por Shot)

Para ejecutar cualquier shot (de **SHOT-01** a **SHOT-24**):

1. **Crear Branch y Scaffold:** `make shot-XX` (inicializa la rama y crea `docs/plans/PLAN_SHOT-XX.md`).
2. **Alineación Global:** En `PLAN_SHOT-XX.md`, identificar qué módulos anteriores consume y qué módulos futuros dependerán de este código.
3. **Redactar Plan:** Completar el plan y esperar la aprobación del usuario.
4. **Implementar (Maker):** Escribir código limpio, modular, tipado y testeado.
5. **Ejecutar el Gauntlet (Checker):**
   ```bash
   make dod
   ```
   *Si algún filtro del Gauntlet falla (Ruff, Mypy, Pytest, Vitest, RLS, Anti-patrones), analiza la traza AST y repara el código de forma autónoma hasta que el Gauntlet devuelva 100% verde.*
6. **Regenerar Golden (si aplica):** `make goldgen` y verificar diff en snapshot.
7. **Cerrar Shot:** Commit convencional (`feat: ...`), PR, merge y tag `shot-XX`.
