# PLAYBOOK POR SHOT — PROTOCOLO DE SESIÓN CON ALINEACIÓN GLOBAL (v1.2)

> Este documento define el flujo de trabajo estándar e inmutable para cada una de las 24 sesiones de construcción (**SHOT-01** a **SHOT-24**). Garantiza que el agente mantenga siempre una visión holística de cómo encaja su código en el sistema global sin perderse ni trabajar de forma aislada.

---

## 1. Flujo de Trabajo Paso a Paso

```
[ 1. Iniciar Shot ] ──► make shot-XX (Crea branch y scaffold con upstream/downstream)
       │
[ 2. Contexto JIT ] ──► Leer AGENTS.md + CONSTITUTION.md + docs/PRD/PRD-{XX}.md
       │
[ 3. Redactar Plan ]──► Completar docs/plans/PLAN_SHOT-XX.md (esperar OK de usuario)
       │
[ 4. Ejecución TDD ]──► Escribir código + tests unitarios + contratos de datos
       │
[ 5. El Gauntlet ]  ──► python scripts/check_dod.py all (Auto-reparación hasta 100% verde)
       │
[ 6. Golden Check ] ──► make goldgen (si tocó fórmulas; commit diff snapshot)
       │
[ 7. Cierre ]       ──► Commit convencional + PR + merge squash + tag shot-XX
```

---

## 2. Plantilla Obligatoria de `docs/plans/PLAN_SHOT-XX.md`

Antes de escribir código en cualquier sesión, el agente debe redactar y guardar el plan en `docs/plans/PLAN_SHOT-XX.md` utilizando exactamente esta estructura:

```markdown
# Plan de Implementación — SHOT-XX: [Nombre del Shot]

## 1. Contexto y Visión Global del Sistema
- **Shot ID:** `SHOT-XX`
- **PRD Fuente:** `/docs/PRD/PRD-{XX}.md`
- **Gate de Cierre Innegociable:** [Texto exacto del gate en PLAN_SHOTS.md]
- **Objetivo Principal:** [Resumen de 1-2 párrafos]

### 1.1. Conexión y Alineación con otros Shots (Cero Desconexión)
- **Módulos Anteriores que Consume (Upstream):** [Qué modelos o contratos de shots previos usa este código]
- **Módulos Futuros que Consumirán este Código (Downstream):** [Qué shots futuros dependerán de esta implementación]

## 2. Archivos a Crear y Modificar
- `[NEW] ruta/del/archivo.py` — Propósito específico y dependencias.
- `[MODIFY] ruta/del/archivo.ts` — Cambios puntuales a realizar.
- `[PROHIBIDO]` — Módulos o funcionalidades explícitamente fuera de este shot.

## 3. Estrategia de Pruebas y Validación Gauntlet
- Tests unitarios a escribir en `engine/tests/` o `backend/apps/`.
- Casos de oro G-cases evaluados (Tolerancia 0.00 mm).
- Comando exacto: `python scripts/check_dod.py all` (o `make dod`).

## 4. Riesgos y [PENDIENTE-DECISIÓN]
- Identificación de cualquier ambigüedad en el PRD. Si existe, aplicar Regla 20.
```

---

## 3. Criterios de Calidad Inviolables

1. **Sin float en /engine:** Solo `Decimal` para dimensiones milimétricas y montos de dinero.
2. **Sin hex crudo en Frontend:** Usar exclusivamente tokens semánticos `--theme-*`.
3. **Aislamiento Multi-Tenant:** Toda consulta de negocio incluye `org_id` y respeta políticas RLS.
4. **Trazabilidad:** Toda acción de IA registra fila en `ai_audit_logs`; todo cambio de precio en `price_audit_logs`.
5. **Idempotencia:** Webhooks y pagos protegidos con restricciones `UNIQUE` contra reintentos.
