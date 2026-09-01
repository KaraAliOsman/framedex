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
> **Precedencia de Diseño:** `PRD-DESIGN-SYSTEM-ADOBE.md` (v1.2, Dual Claro/Oscuro) es el documento CANÓNICO e inapelable para tokens de color, contrastes, tipografía y temas. El archivo `UI_UX_DESIGN_SYSTEM.md` queda **SUPERSEDED** salvo en las especificaciones anatómicas de sus componentes (§4), las cuales deben re-expresarse usando exclusivamente los tokens de `PRD-DESIGN-SYSTEM-ADOBE.md` (cero código hexadecimal hardcodeado).

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
| **PRD-12** | Visor 3D Esquemático | React Three Fiber, cinemática de apertura | — | 3 |
| **PRD-13** | Catálogo Global | Publicación comunitaria sin precios privados | — | 3 |
| **PRD-14** | Certificado Fabricabilidad | Doble ciego Tool T8, NCh 432 / NCh 132 (Chile v1) | — | 3 |
| **PRD-15** | Autopilot Max | Cotización desasistida con espera humana obligatoria | — | 3 |
| **PRD-16** | Inventario de Retazos | Códigos QR térmicos, reserva en órdenes | — | 4 |
| **PRD-17** | Bandeja Omnicanal | Captura automática Email y WhatsApp | — | 4 |
| **PRD-18** | Go-To-Market (GTM) | Copy landing, cold outreach completo, Founding 50 | — | 0–1 |
| **PRD-19** | NFR y Seguridad | RPO $\le 5\text{ min}$, RTO $\le 60\text{ min}$, Dumps Supabase Storage | Todo | 0 |

---

## 4. Plan Maestro de Ejecución por Shots (SHOT-01 → SHOT-24)

*(Ver detalle de gates y pre-requisitos en [`PLAN_DE_EJECUCION_SHOTS.md`](file:///c:/Users/alios/Documents/antigravity/vibrant-hertz/docs/PLAN_DE_EJECUCION_SHOTS.md))*

- **SHOT-01:** Monorepo + CI + Constitución aplicada.
- **SHOT-02:** DDL completo + `hardware_kits` + RLS + tests de aislamiento (Supabase CLI).
- **SHOT-03:** Engine núcleo (G1–G4 en 0.00).
- **SHOT-04:** Auth + tenancy + API skeleton DRF/JWT/OpenAPI + PostHog base + shell app ADOBE dual.
- **SHOT-05:** Canvas 2D mínimo (fijo + cotas).
- **SHOT-06:** Engine total (SLIDING, DOOR, AWNING, `hardware_kits` $\rightarrow$ G5–G12 en 0.00 + golden test).
- **SHOT-07:** Corte 1D BFD + Inspector R01–R14 (G7 puerta en 0.00 + test optimizador barras 5.8m).
- **SHOT-08:** Precios 5 modos + listas de costo + `price_audit_logs`.
- **SHOT-09:** Documentos WeasyPrint & openpyxl + Pantalla S19 (Pedidos proveedor).
- **SHOT-10:** Flujo proyectos + versiones + **catálogos manuales (S02, S12, S13, S15, S16)**.
- **SHOT-11:** Billing Flow + créditos + trial + deploy prod con alertas de uptime.
- **SHOT-12:** **Starter end-to-end + validación fundador (Sign-off G-Pro1).**
- **SHOT-13:** AI Gateway + router `ai_routes` + semáforo + auditoría IA (costos T6/T8/T9).
- **SHOT-14:** Compilador T6 + preguntas T4 + G sintéticos (4 fixtures 0.00).
- **SHOT-15:** OCR T1 + pantalla S27 split-screen.
- **SHOT-16:** Comandos T2/T3/T5 + modal diff + undo sagrado.
- **SHOT-17:** Plantillas PDF 3 slots + bloques protegidos.
- **SHOT-18:** Paddle global + landing legal en Framer (w8-9) $\rightarrow$ **Profesional a cobro**.
- **SHOT-19:** 3D R3F + link `/view/`.
- **SHOT-20:** Catálogo global + cola admin.
- **SHOT-21:** Certificado T8 doble ciego + DOC-08 + QR $\rightarrow$ **Business a cobro**.
- **SHOT-22:** Comparador T10 + bandeja email (Resend / Inbound).
- **SHOT-23:** Autopilot Max T9 + Fin + PostHog.
- **SHOT-24:** Retazos QR + WhatsApp + **G10 monoriel** + PT-BR + Vista instalador (S26).

---

## 5. Los 10 Criterios Go/No-Go del Negocio

1. **Tolerancia Cero en Casos de Oro:** Casos G1–G12 (excepto G10) con discrepancia de $0.00\text{ mm}$ en CI.
2. **Aislamiento Multi-Tenant Certificado:** Cero filtraciones de precios o datos entre organizaciones.
3. **Idempotencia de Pagos:** Ningún webhook duplicado puede cobrar o acreditar doble saldo.
4. **Motor Inmune a Saldo Cero:** Agotar créditos de IA jamás bloquea el motor 2D ni la exportación de PDFs.
5. **Inmutabilidad Documental:** Todo PDF comercial emitido queda congelado con hash SHA-256 inmutable.
6. **Lenguaje Humano de Taller:** Cero excepciones no controladas o trazas crudas mostradas al usuario.
7. **Trazabilidad Integral:** Toda acción de IA en `ai_audit_logs` y todo cambio de precio en `price_audit_logs`.
8. **Términos Legales Publicados:** Landing Framer con pricing y disclaimer "humano aprueba" activo.
9. **Checkout Funcional:** Integración de pasarelas Flow y Paddle probada de extremo a extremo.
10. **Débito de Créditos Idempotente:** Reintento de webhook/red jamás duplica saldo ni créditos.
