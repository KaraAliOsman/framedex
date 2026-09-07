# PRD-00: CONTRATO MAESTRO, ARQUITECTURA Y PLAN DE EJECUCIÓN S1–S24 (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.2 (Congelada y Bloqueada tras Enmienda F1)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 0 (Fundacional)  
**Bloquea a:** Todo el proyecto

---

## 1. Misión del Producto y Tesis de Valor

Dekopen es el **primer sistema operativo de ingeniería, cálculo paramétrico, optimización de corte y cotización comercial para talleres y fabricantes de ventanas de PVC y aluminio** en Chile y Latinoamérica.

> **Tesis Central:** En carpintería de PVC, un error de $1.00\text{ mm}$ destruye el margen de un taller o descalza una obra completa. Dekopen garantiza tolerancia matemática de `0.00 mm` mediante un motor determinista en Python (`/engine`), despiece exacto de perfiles y vidrios, listas de corte optimizadas y generación instantánea de cotizaciones formales.

---

## 2. Precedencia Normativa de Diseño (Parche P1-6)

> [!IMPORTANT]
> **Precedencia de Diseño (Constraint System, Not a Fixed Mockup):** `PRD-DESIGN-SYSTEM-ADOBE.md` (Dual Claro/Oscuro) es la autoridad normativa para **tokens semánticos de color, contrastes WCAG AAA, semántica de temas y línea base tipográfica** (cero valores hexadecimales hardcodeados fuera de variables CSS `--theme-*`).
> No ejerce autoridad rígida ni congelada sobre layout, composición espacial, densidad de paneles, navegación o arquitectura UX. Los desarrolladores y agentes de IA tienen libertad para innovar en la ergonomía y disposición de la interfaz siempre que preserven la accesibilidad, coherencia visual, tokens y estados del sistema. El archivo `UI_UX_DESIGN_SYSTEM.md` permanece **SUPERSEDED** en tokens.

La especificación móvil/OCR/QR que antes ocupaba por error esa ruta vive, sin pérdida de
contenido ni cambio de autoridad propia, en `PRD-WEB-MOBILE-ESSENTIAL.md`.

---

## 3. Mapa Completo de Documentos PRD-00 a PRD-19

| ID | Documento | Contenido Principal | Bloquea a | Fase |
|---|---|---|---|---|
| **PRD-00** | Contrato Maestro | Arquitectura, D1–D30, Plan SHOT-01..24, Criterios Go/No-Go | Todo | 0 |
| **PRD-01** | Motor Técnico `/engine` | Fórmulas, dispatcher, `hardware_kits`, BFD 1D, Casos G1–G12 | 4,5,6,7 | 1 |
| **PRD-02** | Modelo de Datos DDL | PostgreSQL 16, RLS, `hardware_kits`, billing, auditoría | Todo | 0 |
| **PRD-03** | Tenancy y Facturación | Planes Starter/Pro/Business, Trial 7d/500cr, Ledger | 5–11 | 0 |
| **PRD-04** | Diseñador 2D SVG | Árbol paramétrico JSON, Canvas React, Atajos 8, 9, 0 | 6,7 | 1 |
| **PRD-05** | Precios y Rentabilidad | 5 Modos de precio, listas de costo, FX buffer 5% | 6 | 1 |
| **PRD-06** | Documentos de Salida | WeasyPrint PDF, Excel openpyxl, OT de taller, BOM Hash | — | 1 |
| **PRD-07** | Inspector Técnico | Reglas R01–R14, semáforo, fixes en 1-clic | 6 | 1 |
| **PRD-08** | Compilador de Catálogos | OCR Gemini multimodal, semáforo 90%, fixtures | 9,10 | 2 |
| **PRD-09** | Intérprete de Planos (S27) | Extracción de cuadros de vanos, bounding boxes | 10 | 2 |
| **PRD-10** | Comandos de Diseño NLP | Diff paramétrico antes/después, Sacred Undo | — | 2 |
| **PRD-11** | Plantillas PDF | 3 slots configurables, bloques protegidos | — | 2 |
| **PRD-12** | Live View, CAD 2D & 3D | Portal /view/, exportador CAD DXF, visor 3D técnico y cinemática | — | 3 |
| **PRD-13** | AI Gateway y Enrutamiento | Router agnóstico ai_routes, fallback de proveedores y auditoría | — | 2 |
| **PRD-14** | Certificado Fabricabilidad | Doble ciego Tool T8, NCh 432 / NCh 132 (Chile v1) | — | 3 |
| **PRD-15** | Autopilot Max | Cotización desasistida con espera humana obligatoria | — | 3 |
| **PRD-16** | Inventario de Retazos | Códigos QR térmicos, reserva en órdenes | — | 4 |
| **PRD-17** | Bandeja Omnicanal | Captura automática Email y WhatsApp | — | 4 |
| **PRD-18** | Go-To-Market (GTM) | Copy landing, cold outreach completo, Founding 50 | — | 0–1 |
| **PRD-19** | NFR y Seguridad | RPO $\le 5\text{ min}$, RTO $\le 60\text{ min}$, Dumps Cloudflare R2 | Todo | 0 |

---

## 4. Plan Maestro de Ejecución por Shots (SHOT-01 → SHOT-24)

*(Ver detalle de gates y roadmap canónico en [`PLAN_SHOTS.md`](./PLAN_SHOTS.md))*

- **SHOT-01:** Monorepo + CI + Constitución aplicada.
- **SHOT-02:** Modelo de Datos DDL + RLS multi-tenant + Seed determinista DEMO_60.
- **SHOT-03:** Motor Técnico `/engine` puro + Casos de Oro Core (G1–G4).
- **SHOT-04:** API Django REST + Auth JWT Supabase + OpenAPI spec sincronizado.
- **SHOT-05:** Canvas 2D interactivo (SVG puro) + integración de cálculo en tiempo real.
- **SHOT-06:** Casos de Oro G5, G6, G7 a 0.00 mm + hardware_kits en DB + DDL complementario.
- **SHOT-07:** Optimizador 1D Best Fit Decreasing (BFD) + Inspector de 14 Reglas (R01–R14).
- **SHOT-08:** Motor de Costos de 5 Modos + Márgenes y Auditoría de Precios.
- **SHOT-09:** Documentos oficiales de salida (DOC-01 a DOC-07) + hash inmutable.
- **SHOT-10:** Inmutabilidad y Versionado de Proyectos (`project_versions`).
- **SHOT-11:** Facturación Chile (Flow.cl CLP) + Ledger de Créditos IA.
- **SHOT-12:** Starter end-to-end + Sign-off físico G-Pro1 en taller.
- **SHOT-13:** AI Gateway + enrutamiento `ai_routes` + semáforo y auditoría.
- **SHOT-14:** Compilador asistido de catálogos + fixtures de fabricantes.
- **SHOT-15:** OCR Multimodal (Tool T1) + Pantalla S27 split-screen.
- **SHOT-16:** Comandos T2/T3/T5 + modal diff + undo sagrado.
- **SHOT-17:** Plantillas PDF 3 slots + bloques protegidos.
- **SHOT-18:** Paddle global + landing legal en Framer (w8-9) $\rightarrow$ **Profesional a cobro**.
- **SHOT-19:** Live View (`/view/`) + Exportador CAD 2D (`.dxf`) + Visor 3D Técnico & Cinemática.
- **SHOT-20:** Catálogo global + cola admin (Pantalla S28).
- **SHOT-21:** Certificado T8 doble ciego + DOC-08 + QR $\rightarrow$ **Business a cobro**.
- **SHOT-22:** Comparador T10 + bandeja email (SendGrid).
- **SHOT-23:** Autopilot Max T9 + Fin + PostHog.
- **SHOT-24:** Retazos QR + WhatsApp + **G10 monoriel** + PT-BR + Vista instalador (S26).

---

## 5. Matriz Canónica de Criterios Go/No-Go (IDs Únicos Permanentes)

Para evitar duplicidad o ambigüedades entre documentos, todo hito de cierre se evalúa contra estos identificadores canónicos:

| ID Canónico | Criterio de Aceptación Innegociable | Verificación / Gate |
|---|---|---|
| `GNG-01-GOLDEN` | Tolerancia matemática de $0.00\text{ mm}$ en los Casos de Oro exigidos por el Shot (Core G1–G7 en Fase 1). | `pytest engine/` + Snapshot bit a bit |
| `GNG-02-TENANCY` | Aislamiento RLS multi-tenant absoluto. Tenant A jamás lee costos, cotizaciones o clientes de Tenant B. | Test PostgreSQL multi-tenant con RLS |
| `GNG-03-PAYMENTS` | Idempotencia estricta en webhooks de pago (Flow.cl en Chile y Paddle MoR internacional). Reintentos de red jamás duplican cobros. | Test replay de webhook con UNIQUE |
| `GNG-04-ZERO-BALANCE` | Inmunidad de la plataforma ante saldo 0 de créditos IA: motor 2D, optimizador 1D, cotizador manual y exportación PDF siguen 100% operativos. | Test de corte manual con `credits_balance = 0` |
| `GNG-05-IMMUTABILITY` | Inmutabilidad documental: cada PDF o Excel emitido congela su snapshot de BOM y hash SHA-256 en base de datos. | Hash SHA-256 inmutable en `project_versions` |
| `GNG-06-HUMAN-UX` | Lenguaje de taller profesional: el inspector R01–R14 muestra frases humanas con botón de corrección; cero trazas crudas. | Test de interfaz y mensajes tipados |
| `GNG-07-AUDIT` | Auditoría previa obligatoria: toda mutación de precio genera fila en `price_audit_logs` y toda llamada IA en `ai_audit_logs` antes de aplicar cambios. | Test transaccional de auditoría |
| `GNG-08-LEGAL-FOUNDING`| Términos legales, disclaimers técnicos y contrato Founding 50 (precio congelado de por vida en BD) publicados en landing. | Check de schema y flags comerciales |
| `GNG-09-CHECKOUT-E2E` | Checkouts funcionales de extremo a extremo en sandbox (Flow CLP con DTE y Paddle USD global). | Test E2E de compra y activación |
| `GNG-10-DISASTER-RECOVERY` | Protocolo de recuperación de desastres: RPO $\le 1\text{h}$, RTO $\le 2\text{h}$, dump cifrado diario a Supabase Storage y simulacro de restauración probado. | `scripts/restore_drill.sh` en instancia limpia |
| `GNG-PILOT-SIGN-OFF` | Validación humana en taller real: sign-off físico G-Pro1 con 10 trabajos cotizados en paralelo sin fallos antes de abrir cobro Starter. | Acta firmada con taller en SHOT-12 |

---

## 6. Manifiesto de Dependencias Base Aprobadas y Gobernanza de Dependencias (Regla 15)

El repositorio se rige por la **Política de Dependencias de Dos Niveles** establecida en la Constitución (Regla 15):
- **A) DEV/TOOLING LOW-RISK:** Dependencias de tooling, linters o testing pueden ser incorporadas por desarrolladores y agentes mediante PR siempre que tengan licencia compatible (MIT/Apache-2.0/BSD), proyecto activamente mantenido, sin duplicación injustificada, lockfile reproducible y tests verdes.
- **B) PRODUCTION RUNTIME:** La incorporación de dependencias en producción requiere análisis de impacto y justificación técnica. Aprobación del Owner obligatoria exclusivamente para frameworks principales, bases de datos, proveedores cloud críticos o cambios arquitectónicos mayores.

### Dependencias Base Aprobadas (Approved Baseline):

### Backend & Núcleo (`/backend` y `/engine`)
* `python >= 3.12`
* `django >= 5.0, < 6.0` (Arquitectura Django 5.2 LTS ready)
* `djangorestframework >= 3.15`
* `django-cors-headers >= 4.3`
* `pydantic >= 2.7` & `pydantic-settings >= 2.2` (Esquemas tipados y settings validados)
* `psycopg[binary] >= 3.1` (Conector nativo PostgreSQL 16)
* `weasyprint >= 62.0` (Generación de PDFs DOC-01 a DOC-08)
* `openpyxl >= 3.1` (Generación de listas de corte en Excel DOC-03)
* `drf-spectacular >= 0.27` (Autogeneración OpenAPI 3.0 / TypeScript client)
* `structlog >= 24.1` (Observabilidad y logs estructurados en JSON)
* `whitenoise >= 6.6` (Servido de archivos estáticos)
* `huey >= 2.5` & `redis >= 5.0` (Cola de tareas asíncronas ligeras)
* `posthog >= 3.5` (Telemetría de producto)
* **Pins SHOT-04:** `PyJWT[crypto]==2.13.0`, `cryptography==50.0.1`,
  `httpx==0.28.1`, `django-cors-headers==4.9.0`.
* **Tooling Backend:** `pytest >= 8.0`, `pytest-django >= 4.8`, `ruff >= 0.4`, `mypy >= 1.10`.

### Frontend (`/frontend`)
* `node >= 20`
* `react >= 18.3` & `react-dom >= 18.3`
* `typescript >= 5.4`
* `vite >= 5.2`
* `tailwindcss >= 3.4` (con variables semánticas `--theme-*`)
* `lucide-react >= 0.370` (Iconografía técnica)
* **Runtime SHOT-04:** `@supabase/supabase-js@2.112.4`,
  `react-router-dom@7.18.3`, `@tanstack/react-query@5.102.8`,
  `zustand@5.0.15`, `posthog-js@1.422.5`.
* **Tooling SHOT-04:** `orval@8.27.0`, `@playwright/test@1.62.1`,
  `@testing-library/react@16.3.3`, `@testing-library/dom@10.4.1`,
  `@testing-library/jest-dom@7.0.1`, `jsdom@30.0.1`, `otpauth@9.5.1`.
* **Tipos React (PD-04-13 resuelta):** `@types/react@18.3.28`,
  `@types/react-dom@18.3.7` como devDependencies exactas; no autoriza upgrades de
  React, ReactDOM ni TypeScript.
* **Tooling Frontend:** `vitest >= 1.6`, `eslint >= 8.57`, `prettier >= 3.2`.

