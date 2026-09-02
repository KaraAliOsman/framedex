# Dekopen — OS de Ingeniería y Cotización para Carpinterías de PVC

> **Tolerancia Cero en PVC:** Sistema operativo paramétrico, motor de optimización 1D y cotizador comercial con tolerancia matemática garantizada de `0.00 mm`.

---

## ⚡ Quickstart

Requisitos: Python 3.12+, Node.js 20.19+ y npm. El gate SQL real requiere además
Docker y Supabase CLI 2.116.0; son herramientas de verificación, no dependencias del
producto. Supabase local usa PostgreSQL 17 y CI aplica el mismo DDL adicionalmente sobre
`postgres:16-alpine` para verificar el contrato de PRD-02.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --requirement requirements-dev.txt
cd frontend && npm ci && cd ..

# Gauntlet canónico multiplataforma
python scripts/check_dod.py all

# Migración, seed, lint SQL y pgTAP sobre una stack Supabase limpia
make database
```

El checker rechaza herramientas o suites ausentes, warnings, tipos SQL flotantes, tablas
sin RLS y cualquier comando con retorno no cero. La fuente de verdad vive en
`supabase/migrations/`; el seed global determinista `DEMO_60` vive en
`supabase/seed.sql`. Ningún comando del shot enlaza ni modifica una instancia remota.

## 🔒 Branch protection de `main`

La protección debe exigir pull request y los cuatro checks exactos `Lint & Typecheck`,
`Test Suite`, `Frontend Build` y `Database Gate`, sin bypass ni force pushes. Cada shot
se publica en `shot-XX` y espera la orden explícita `MERGE` del owner.

---

## 🗺️ Mapa de Documentación y Arquitectura

Toda la documentación técnica normativa vive en `/docs/` y está dividida en módulos:

| Documento | Ubicación | Propósito |
|---|---|---|
| **Protocolo de Agentes** | [`/AGENTS.md`](./AGENTS.md) | Bootstrap obligatorio para Codex, Claude Code y agentes de desarrollo |
| **Constitución del Builder** | [`/docs/CONSTITUTION.md`](./docs/CONSTITUTION.md) | 23 reglas inviolables de calidad, tipado y determinismo |
| **Playbook de Sesión** | [`/docs/PLAYBOOK_SHOTS.md`](./docs/PLAYBOOK_SHOTS.md) | Guía paso a paso para planificar, ejecutar y cerrar cada shot |
| **Especificaciones Técnicas (PRDs)** | [`/docs/PRD/`](./docs/PRD/) | Módulos funcionales del sistema (PRD-00 a PRD-19) |
| **Catálogo de Pantallas** | [`/docs/PRD/SCREENS_SPECIFICATION_S01_S28.md`](./docs/PRD/SCREENS_SPECIFICATION_S01_S28.md) | Especificación de las 28 pantallas de la aplicación |
| **Plan Maestro de Shots** | [`/docs/PRD/PLAN_SHOTS.md`](./docs/PRD/PLAN_SHOTS.md) | Secuencia inmutable de los 24 shots y gates de cierre |

---

## 📊 Estado de Ejecución de Shots (SHOT-01 → SHOT-24)

> El alcance, dependencias, entregables y gates de cada SHOT se definen exclusivamente en [`docs/PRD/PLAN_SHOTS.md`](./docs/PRD/PLAN_SHOTS.md). Esta tabla solo refleja estado de ejecución y no constituye una fuente normativa; no debe duplicar el roadmap.

| Shot | Estado |
|---|:---:|
| **SHOT-01** | ✅ Cerrado |
| **SHOT-02** | ✅ Cerrado |
| **SHOT-03** | ⏳ Pendiente |
| **SHOT-04** | ⏳ Pendiente |
| **SHOT-05** | ⏳ Pendiente |
| **SHOT-06** | ⏳ Pendiente |
| **SHOT-07** | ⏳ Pendiente |
| **SHOT-08** | ⏳ Pendiente |
| **SHOT-09** | ⏳ Pendiente |
| **SHOT-10** | ⏳ Pendiente |
| **SHOT-11** | ⏳ Pendiente |
| **SHOT-12** | ⏳ Pendiente |
| **SHOT-13** | ⏳ Pendiente |
| **SHOT-14** | ⏳ Pendiente |
| **SHOT-15** | ⏳ Pendiente |
| **SHOT-16** | ⏳ Pendiente |
| **SHOT-17** | ⏳ Pendiente |
| **SHOT-18** | ⏳ Pendiente |
| **SHOT-19** | ⏳ Pendiente |
| **SHOT-20** | ⏳ Pendiente |
| **SHOT-21** | ⏳ Pendiente |
| **SHOT-22** | ⏳ Pendiente |
| **SHOT-23** | ⏳ Pendiente |
| **SHOT-24** | ⏳ Pendiente |
