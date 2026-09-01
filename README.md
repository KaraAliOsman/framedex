# Dekopen — OS de Ingeniería y Cotización para Carpinterías de PVC

> **Tolerancia Cero en PVC:** Sistema operativo paramétrico, motor de optimización 1D y cotizador comercial con tolerancia matemática garantizada de `0.00 mm`.

---

## ⚡ Quickstart

Para comenzar o validar el estado completo del repositorio:

```bash
# Validar el Definition of Done completo (Regla 19 de la Constitución)
make dod

# Ejecutar tests unitarios (Engine, Backend, Frontend)
make test

# Validar linters y reglas constitucionales (sin float en engine, sin hex en UI)
make lint

# Chequeo estricto de tipos (mypy strict + tsc)
make typecheck
```

---

## 🗺️ Mapa de Documentación y Arquitectura

Toda la documentación técnica normativa vive en `/docs/` y está dividida en módulos:

| Documento | Ubicación | Propósito |
|---|---|---|
| **Protocolo de Agentes** | [`/AGENTS.md`](./AGENTS.md) | Bootstrap obligatorio para Codex, Claude Code y agentes de desarrollo |
| **Constitución del Builder** | [`/docs/CONSTITUTION.md`](./docs/CONSTITUTION.md) | 22 reglas inviolables de calidad, tipado y determinismo |
| **Playbook de Sesión** | [`/docs/PLAYBOOK_SHOTS.md`](./docs/PLAYBOOK_SHOTS.md) | Guía paso a paso para planificar, ejecutar y cerrar cada shot |
| **Especificaciones Técnicas (PRDs)** | [`/docs/PRD/`](./docs/PRD/) | Módulos funcionales del sistema (PRD-00 a PRD-19) |
| **Catálogo de Pantallas** | [`/docs/PRD/SCREENS_SPECIFICATION_S01_S28.md`](./docs/PRD/SCREENS_SPECIFICATION_S01_S28.md) | Especificación de las 28 pantallas de la aplicación |
| **Plan Maestro de Shots** | [`/docs/PRD/PLAN_SHOTS.md`](./docs/PRD/PLAN_SHOTS.md) | Secuencia inmutable de los 24 shots y gates de cierre |

---

## 📊 Estado de Ejecución de Shots (SHOT-01 → SHOT-24)

| Shot | Fase | Descripción | Gate de Cierre | Estado |
|---|---|---|---|:---:|
| **SHOT-01** | 0 | Monorepo + CI + Tooling Fundacional | Pipeline verde sobre stubs (`make dod`) | ⏳ Pendiente |
| **SHOT-02** | 0 | DDL completo + `hardware_kits` + RLS | SQL aplica en Supabase; tests aislamiento pasan | ⏳ Pendiente |
| **SHOT-03** | 0 | Engine núcleo (fórmulas fijas + OB + BOM) | `pytest engine/`: G1–G4 en 0.00 mm | ⏳ Pendiente |
| **SHOT-04** | 0 | Auth + tenancy + API DRF + Shell ADOBE | Magic link E2E; OpenAPI $\rightarrow$ TS; PostHog base | ⏳ Pendiente |
| **SHOT-05** | 0 | Canvas 2D mínimo SVG (fijo + cotas) | Dibuja G1 en pantalla (<300 ms) | ⏳ Pendiente |
| **SHOT-06** | 1 | Engine total (correderas, puertas, herrajes) | G5–G12 en 0.00 mm; snapshot `golden_example.json` | ⏳ Pendiente |
| **SHOT-07** | 1 | Corte 1D BFD + Inspector R01–R14 | G7 en 0.00; optimizador barras 5.8m; bloqueo OT | ⏳ Pendiente |
| **SHOT-08** | 1 | Precios 5 modos + `price_audit_logs` | 5 modos con tests; auditoría en cada mutación | ⏳ Pendiente |
| **SHOT-09** | 1 | Salidas DOC-01..07 (PDF/Excel) + S19 | BOM hash idéntico en todos los documentos | ⏳ Pendiente |
| **SHOT-10** | 1 | Versiones + Catálogos manuales (S02, S12, S13, S15, S16) | Freeze REV-A; CRUD manual funcional | ⏳ Pendiente |
| **SHOT-11** | 1 | Facturación Flow + Deploy Prod + Alertas | Checkout sandbox; webhook idempotente; backup R2 | ⏳ Pendiente |
| **SHOT-12** | 1 | **Starter End-to-End + Validación Fundador** | **Sign-off G-Pro1** (Apertura comercial Starter) | ⏳ Pendiente |
| **SHOT-13** | 2 | AI Gateway + Router + Auditoría IA | Auditoría previa obligatoria; semáforo 90/70 | ⏳ Pendiente |
| **SHOT-14** | 2 | Compilador de Catálogos T6 | 4 fixtures (VEKA, Aluplast, Rehau, Proline) 0.00 | ⏳ Pendiente |
| **SHOT-15** | 2 | OCR Multimodal de Planos S27 | PDF 8 vanos $\rightarrow$ borrador revisable < 5 min | ⏳ Pendiente |
| **SHOT-16** | 2 | Comandos NLP + Diff Preview + Sacred Undo | Preview antes/después; Cmd+Z revierte | ⏳ Pendiente |
| **SHOT-17** | 2 | Plantillas PDF 3 slots + CSP | Re-estiliza sin alterar totales numéricos | ⏳ Pendiente |
| **SHOT-18** | 2 | Creem Global + Landing Legal | **Apertura comercial Profesional** | ⏳ Pendiente |
| **SHOT-19** | 3 | Visor 3D Esquemático React Three Fiber | PNG + enlace público sin costos en bundle | ⏳ Pendiente |
| **SHOT-20** | 3 | Catálogo Global + Cola Admin S28 | Aprobación comunitaria; costos privados blindados | ⏳ Pendiente |
| **SHOT-21** | 3 | Certificado Fabricabilidad Doble Ciego | **Apertura comercial Business / Business 2x** | ⏳ Pendiente |
| **SHOT-22** | 3 | Comparador Planos + Bandeja Omnicanal | V1 vs V2 diff; inbound email $\rightarrow$ borrador | ⏳ Pendiente |
| **SHOT-23** | 4 | Autopilot Max T9 + Fin Intercom | Salida DRAFT protegida; 20 preguntas onboarding | ⏳ Pendiente |
| **SHOT-24** | 4 | Retazos QR + WhatsApp + G10 Monoriel | G10 en 0.00; ciclo retazo completo; i18n pt-BR | ⏳ Pendiente |
