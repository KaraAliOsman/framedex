# PLAN DE EJECUCIÓN SHOT-01 → SHOT-24 — DEKOPEN (v1.2 MASTER)

> **Nota de nomenclatura:** Los shots se numeran **SHOT-01…SHOT-24** (mayúscula + guion) para no colisionar con las pantallas S01–S28. Este documento es la tercera y última pieza de la biblia: PRD v1.1.0 (contrato) → Biblia v1.2 MASTER (especificación) → **este plan (ejecución)**. A partir de aquí, ninguna decisión se toma en caliente: si el builder encuentra un vacío, aplica la Regla 20 (`[PENDIENTE-DECISIÓN]`), nunca improvisa.

---

## 1. Principios Operativos (No Negociables)

1. **Un shot a la vez, en orden.** Prohibido adelantar shots. Cada shot consume su PRD fuente bloqueado y nada más.
2. **El shot no cierra sin su gate completo.** Si el gate falla, se corrige dentro del shot — la deuda técnica no viaja al siguiente shot.
3. **Demo semanal al fundador.** El fundador es el usuario real: cada viernes, flujo funcionando en su máquina. Si no se puede demostrar, el shot no avanzó.
4. **Un PR por shot, tag `shot-XX`.** El merge requiere el DoD de la Regla 19 (Constitución) + el gate específico del shot.
5. **Los checkpoints de negocio (SHOT-12, SHOT-18, SHOT-21) requieren decisión explícita del fundador** para abrir el cobro. La IA nunca abre un plan.

---

## 2. Pre-requisitos del Fundador (Antes del SHOT-01, Día 0)

| # | Requisito | Por qué |
|---|---|---|
| **P1** | Cuentas: GitHub, Supabase Pro, Railway, Vercel, Linear, Cloudflare R2, PostHog, Intercom/Fin, Resend | Infraestructura base del stack D8–D28 |
| **P2** | Cuenta Flow.cl + credenciales sandbox | SHOT-11 |
| **P3** | Dominios: `dekopen.com`, `app.dekopen.com`, `dekopenmail.com` + DNS | D25 |
| **P4** | Iniciar trámite **SpA Chile** (contador) | D4 — antes del primer cobro, no bloquea build |
| **P5** | Ficha técnica Pro6004 + perfil físico + calibrador + balanza | Sign-off G-Pro1 (SHOT-12) |
| **P5-bis** | Cuenta Paddle sandbox (crear pre-semana 15) | SHOT-18 |
| **P6** | Este documento + Biblia v1.2 MASTER cargados en Notion y como fuente de Fin | Base de conocimiento |
| **P7** | **Tarea Fundador Semanas 8–9 (No-Code):** Landing en Framer con pricing v1.1 + waitlist + página de términos legales "humano aprueba" (con abogado, en paralelo a SpA) | Aterriza Go/No-Go 8 antes de SHOT-11 y SHOT-18 |

---

## 3. Insight de Resiliencia y Ruta Crítica

> [!TIP]
> **Ruta Crítica Resiliente:** El plan Starter solo necesita **G1 a G7**. Los casos complejos G8, G9, G11 y G12 (correderas 3-4H, puerta doble, gran formato) pueden deslizar a Fase 2 sin bloquear el ingreso de dinero en Semana 10.
> **Ruta Crítica:** `SHOT-01 → SHOT-02 → SHOT-03 (G1-G4) → SHOT-04 → SHOT-05 → SHOT-06 (SLIDING_2L/DOOR/AWNING + G5-G7) → SHOT-07 → SHOT-08 → SHOT-09 → SHOT-10 → SHOT-11 → SHOT-12`. Si una semana se complica, se recorta primero G9/G11/G12 de SHOT-06, pero **jamás** G5/G6/G7 ni la resolución de `hardware_kits`.

---

## 4. Tabla Maestra de Shots (v1.2 MASTER)

| Shot | Fase / Sem | PRD Fuente | Entrega Principal | Gate de Cierre |
|---|---|---|---|---|
| **SHOT-01** | 0 · s1 | PRD-00 | Monorepo + CI + Constitución aplicada | Pipeline verde sobre stubs: ruff + mypy + pytest + vitest + build en CI, branch protection |
| **SHOT-02** | 0 · s1–2 | PRD-02 (+Enm. 1 & F1) | **CERRADO** — DDL completo + `hardware_kits` + RLS + tests aislamiento (Supabase CLI en CI) | SQL aplica en Supabase limpio; test tenant-A≠tenant-B pasa; seed Demo 60 visible global; `payment_events`/`credit_ledger`/`hardware_kits` existen |
| **SHOT-03** | 0 · s2–3 | PRD-01 §2–4 (+M9, M5) | Engine núcleo: models, geometry FIXED/TURN/TILT_TURN/MULLION, BOM base | `pytest engine/`: **G1, G2, G3, G4 en 0.00**; G8/G9/G11/G12 en xfail declarado |
| **SHOT-04** | 0 · s3 | PRD-03 §1, PRD-19 §3 | Auth + tenancy + API skeleton DRF/JWT/OpenAPI + PostHog base + shell app ADOBE dual | Magic link E2E; TOTP owner; OpenAPI $\rightarrow$ TS client autogenerado en CI; PostHog captura eventos base; shell navegable claro/oscuro |
| **SHOT-05** | 0 · s3 | PRD-04, ADOBE, ANIM | Canvas 2D mínimo (fijo + cotas) | Dibuja G1 en pantalla = números del engine (<300 ms); cota editable por teclado; snapping |
| **SHOT-06** | 1 · s4–5 | PRD-01 completo, F1 | Engine total: SLIDING_2L, DOOR_ENTRY, AWNING, resolución `hardware_kits`, peso+fallback, pricing puro | **Core Gate Obligatorio:** G5, G6, G7 pasan $0.00\text{ mm}$ + test CI de `golden_example.json` bit a bit. *(Extended Gate: G8, G9, G11, G12 diferibles a SHOT-06B; G10 en Fase 4)* |
| **SHOT-07** | 1 · s5–6 | PRD-01 §6, PRD-07, ANIM | Corte 1D BFD + Inspector R01–R14 + panel inspector | **G7 (puerta multipunto) en 0.00**; test optimizador: pedido Proline barras 5.800m con SKU comercial $\ne$ lista corte taller; inspector bloquea OT en rojo; fix-1-clic aplica diff |
| **SHOT-08** | 1 · s6–7 | PRD-05, PRD-02 (audit) | Precios 5 modos + listas costo + `price_audit_logs` | 5 modos con tests; gobernanza descuentos (margen negativo bloqueado); **cada mutación de precio genera fila de auditoría (test)** |
| **SHOT-09** | 1 · s7–8 | PRD-06, S19 | DOC-01…DOC-07 (WeasyPrint + openpyxl) + Pantalla S19 (Pedidos proveedor) | PDF/Excel/OT/corte/checklist/informe con **BOM hash idéntico entre todos**; storage firmado 3600 s; S19 renderiza lista de compra |
| **SHOT-10** | 1 · s8–9 | PRD-02, S02–S05, S08, S12, S13, S15, S16 | Flujo proyectos + versiones + clonación + **catálogos manuales (S02, S12, S13, S15, S16)** | Autómata de estados; freeze REV-A congela snapshot; editar enviada $\rightarrow$ REV-B; CRUD manual de series, junquillos y kits de herraje funcional para el fundador |
| **SHOT-11** | 1 · s9–10 | PRD-03 §2–5, PRD-19 §2, Enm. 1 | Billing Flow + créditos + trial + **deploy producción + Uptime alerts** | Checkout sandbox Flow; webhook idempotente (reintento$\ne$doble); débito transaccional ledger; trial 7d/500 cap; **dump cifrado Supabase Storage + simulacro restauración documentado (GNG-10)**; alertas Railway activas |
| **SHOT-12** | 1 · s10 | Todo Fase 1 | **Starter end-to-end + validación fundador** | **Gate-N:** fundador cotiza 10 trabajos reales en paralelo a NuveraPro sin perder en cortes ni pedido Proline $\rightarrow$ **sign-off G-Pro1 (GNG-PILOT-SIGN-OFF)**. Checkpoint: se abre cobro Starter |
| **SHOT-13** | 2 · s11 | PRD-13, PRD-03 §4, F7 | AI Gateway + router `ai_routes` + semáforo + auditoría IA (costos recalibrados T6/T8/T9) | Toda tool audita ANTES de aplicar (payload, hash, retención); débito con cap; semáforo 90/70; fallback de modelo probado; T6=25+2, T8=50, T9=30+2 |
| **SHOT-14** | 2 · s11–12 | PRD-08 (+M1) | Compilador T6 + preguntas T4 + G sintéticos | **Los 4 fixtures (VEKA/Aluplast/Rehau/Proline) parsean a ficha v1 y validan contra engine 0.00**; serie nueva exige G-case mínimo antes de uso |
| **SHOT-15** | 2 · s12–13 | PRD-09 | OCR T1 + pantalla S27 split-screen | **PDF 8 vanos $\rightarrow$ borrador revisable < 5 min humanos**; anclas bidireccionales; celdas rojas bloquean importación |
| **SHOT-16** | 2 · s13–14 | PRD-10 | Comandos T2/T3/T5 + modal diff + undo sagrado | "20% ganancia" recalcula con preview antes/después; Cmd+Z revierte; **T3 jamás escribe número** (solo diff $\rightarrow$ engine) |
| **SHOT-17** | 2 · s14–15 | PRD-11 | Plantillas PDF 3 slots + bloques protegidos | Re-estiliza sin reescribir números (test: totales intactos tras CSS loco); restaurar original 1 clic; CSP |
| **SHOT-18** | 2 · s15–16 | PRD-18, PRD-03 | Paddle Global (USD MoR) + página pricing + Founding 50 | Checkout USD sandbox Paddle; toggle anual default; **checkpoint: Profesional se abre a cobro** tras verificar go/no-go canónicos |
| **SHOT-19** | 3 · s17–18 | PRD-12 | Enlace Web en Vivo (`/view/`) + Exportador CAD 2D (`.dxf`) | Enlace público read-only **sin costos ni despiece en el bundle**; exportador DXF funcional con capas normalizadas (3D WebGL diferido a V2) |
| **SHOT-20** | 3 · s18–20 | PRD-13, S28 | Catálogo global + cola admin (Pantalla S28) | Flujo solicitud $\rightarrow$ revisión $\rightarrow$ publicación sin precios; **test: admin no puede consultar costos ajenos** (blindaje) |
| **SHOT-21** | 3 · s20–22 | PRD-14 | Certificado T8 doble ciego + DOC-08 + QR | Modelos distintos obligatorios; árbitro 100% concordancia $\rightarrow$ sello; discrepancia $\rightarrow$ flag; **checkpoint: Business y Business 2x abren cobro** |
| **SHOT-22** | 3 · s22–24 | PRD-15 parcial, PRD-17 parcial | Comparador T10 + bandeja email | V1 vs V2 diff correcto; email $\rightarrow$ inbound_request $\rightarrow$ Huey $\rightarrow$ borrador |
| **SHOT-23** | 4 · m7 | PRD-15, PRD-19 §4 | Autopilot Max T9 + Fin + PostHog | Salida SIEMPRE DRAFT (test de contención); **Fin responde las 20 preguntas**; embudos PostHog activos |
| **SHOT-24** | 4 · m7–9 | PRD-16, PRD-17, PRD-01, S26 | Retazos QR + WhatsApp + **G10 monoriel completo** + PT-BR + Pantalla S26 (Vista instalador) | G10 0.00 (sale de xfail); ciclo retazo completo (RESERVED $\rightarrow$ CONSUMED); i18n pt-BR; portal S26 en solo lectura para instalador |

---

## 5. Matriz Canónica de Mapeo Go/No-Go → Shots

| ID Canónico | Criterio de Aceptación | Hito de Cierre y Verificación |
|---|---|---|
| `GNG-01-GOLDEN` | Tolerancia 0.00 mm en Casos de Oro Core (G1–G7) | SHOT-03 (G1–G4) + SHOT-06 (G5–G7) |
| `GNG-02-TENANCY` | Aislamiento RLS multi-tenant absoluto (cero filtración de precios) | SHOT-02 (DDL & RLS) + SHOT-04 (API) |
| `GNG-03-PAYMENTS` | Idempotencia estricta en webhooks de pago (Flow / Paddle) | SHOT-11 (Flow CLP) + SHOT-18 (Paddle USD) |
| `GNG-04-ZERO-BALANCE` | Inmunidad de la plataforma ante saldo 0 de créditos IA | SHOT-11 (Billing) + SHOT-13 (Gateway) |
| `GNG-05-IMMUTABILITY` | Inmutabilidad documental con hash SHA-256 congelado | SHOT-09 (DOC-01 a DOC-07) + SHOT-10 (Versiones) |
| `GNG-06-HUMAN-UX` | Lenguaje humano de taller (cero trazas crudas) | SHOT-07 (Inspector R01–R14) |
| `GNG-07-AUDIT` | Auditoría previa inmutable (`price_audit_logs` / `ai_audit_logs`) | SHOT-08 (Precios) + SHOT-13 (AI Gateway) |
| `GNG-08-LEGAL-FOUNDING`| Landing legal con pricing, disclaimers y Founding 50 | SHOT-18 (GTM & Landing) |
| `GNG-09-CHECKOUT-E2E` | Checkouts funcionales de extremo a extremo en sandbox | SHOT-11 (Chile CLP) + SHOT-18 (Global USD) |
| `GNG-10-DISASTER-RECOVERY` | RPO $\le 1\text{h}$, RTO $\le 2\text{h}$, backup cifrado y simulacro probado | SHOT-11 (`scripts/restore_drill.sh`) |
| `GNG-PILOT-SIGN-OFF` | Validación humana en taller real (10 trabajos paralelos) | SHOT-12 (Sign-off físico G-Pro1) |

---

## 6. Prompt Canónico Universal (Protocolo 2026)

```text
[DEKOPEN OS v1.2 MASTER — PROTOCOLO DE SHOT — 23 Reglas Supremas (Regla 0 a 22)]

Actúas como Ingeniero Principal de Dekopen. Antes de escribir código:

LECTURA OBLIGATORIA (en orden, sin supuestos):
1. docs/CONSTITUTION.md (23 Reglas Supremas)
2. docs/PRD/PLAN_SHOTS.md — gate textual de este shot
3. docs/PRD/PRD-XX.md — el PRD indicado en la tabla para este shot
4. Interfaces reales de los módulos ya construidos (lee el repo, no la memoria)

FASE 1 — PLAN: escribe docs/plans/PLAN_SHOT-XX.md.
DETENTE y espera mi "APROBADO — EJECUTA".

FASE 2 — CONSTRUCCIÓN: solo el plan aprobado. Cero float en /engine, cero hex fuera de variables CSS, dependencias cerradas PRD-00 §6.

FASE 3 — GAUNTLET: python scripts/check_dod.py all hasta EXIT CODE 0 real.

FASE 4 — CIERRE: push a shot-XX y espera orden de merge.
```
