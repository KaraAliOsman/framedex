# DEKOPEN — BIBLIA DE EJECUCIÓN Y SUITE MAESTRA DE ESPECIFICACIONES TÉCNICAS (v1.1.2)
**Versión:** 1.1.2 (Congelada y Bloqueada tras Micro-Parche Final)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fecha de Congelación:** 30 de Agosto de 2026  
**Autor:** Arquitectura Técnica de Dekopen  
**Estado:** Documento Maestro Definitivo (Merge de Enmiendas A, B, C, Parches P1–P3, F1–F7, H1–H3 y Plan SHOT-01..24)

---

## ÍNDICE GENERAL DE LA BIBLIA DE EJECUCIÓN

1. **Constitución del Builder (Leyes Normativas 1 a 21)**
2. **Precedencia de Diseño y Tokens Duales (PRD-DESIGN-SYSTEM-ADOBE)**
3. **Mapa Completo de Documentos PRD-00 a PRD-19 y Pantallas S01–S28**
4. **Decisiones Arquitectónicas Cerradas (D1 a D30)**
5. **Especificación del Motor Técnico `/engine` (PRD-01)**
6. **Modelo de Datos y DDL PostgreSQL 16 con RLS, Kits, Billing y Plataforma (PRD-02)**
7. **Tenancy, Auth, Facturación y Billetera de Créditos (PRD-03)**
8. **Diseñador 2D en Canvas SVG Puro (PRD-04)**
9. **Motor de Precios y Rentabilidad (PRD-05)**
10. **Documentos de Salida: PDF, Excel, OT y Corte 1D (PRD-06)**
11. **Inspector Técnico y Reglas de Fabricabilidad R01–R14 (PRD-07)**
12. **Compilador Asistido de Catálogos (PRD-08)**
13. **Intérprete Multimodal de Planos S27 (PRD-09)**
14. **Comandos en Lenguaje Natural y Diff Antes/Después (PRD-10)**
15. **Plantillas PDF Personalizadas (PRD-11)**
16. **Visor 3D Esquemático (PRD-12)**
17. **Catálogo Global y Moderación Admin S28 (PRD-13)**
18. **Certificado de Fabricabilidad y Doble Verificador (PRD-14)**
19. **Autopilot Max (PRD-15)**
20. **Inventario de Retazos (PRD-16)**
21. **Bandeja Omnicanal Email / WhatsApp (PRD-17)**
22. **Assets Go-To-Market y Precios Landing (PRD-18)**
23. **NFR, Seguridad y Recuperación ante Desastres (PRD-19)**
24. **APÉNDICE A — ENMIENDAS v1.1.2 (Normativa Precedente)**
25. **APÉNDICE B — GATES DE NEGOCIO, MÉTRICAS Y RIESGOS**
26. **PLAN DE EJECUCIÓN SHOT-01 → SHOT-24**

---

## 1. CONSTITUCIÓN DEL BUILDER (v1.1.2)

```
# DEKOPEN — CONSTITUCIÓN DEL BUILDER (no negociable, lee antes de escribir código)

1. NÚMEROS: si un número aparece en un documento de salida, salió de /engine o de un
   campo editado por humano. JAMÁS del texto libre de un LLM.
2. engine/ es puro: sin I/O, sin Django, sin HTTP. Testeable con `pytest engine/`.
3. Decimal para todo mm y dinero. Prohibido float. CLP sin decimales; USD con 2 decimales.
4. Toda tabla de negocio lleva org_id + política RLS + test de aislamiento. Un tenant
   jamás lee precios de otro. Catálogos globales legibles por todos los usuarios.
5. Escritura de IA → fila en ai_audit_logs ANTES de aplicar el diff. Sin excepciones.
6. Parámetros de serie viven en profile_systems (desde ficha). Cero hardcoded en UI.
   Cambiar una fórmula = PR con caso de oro nuevo. Nunca "ajuste de prompt".
7. Casos de Oro (Gold Cases G1–G12 excepto G10 en Fase 1.5; G-Pro1 con sign-off físico).
   Ningún PR se completa con discrepancia > 0.00 mm.
8. Un cambio de fórmula es un PR con caso de oro, no un ajuste de prompt.
9. Monolito modular (apps Django por dominio). Prohibido microservicios.
10. Error del inspector = frase de taller + botón de corrección. Nunca un log crudo.
11. Enviar a cliente, mandar a fábrica, comprar material: requieren clic humano
    explícito. Estados lo modelan; nada automático.
12. project_versions congela números en cada emisión. Cambiar precio enviado = revisión nueva.
13. Webhooks y pagos: idempotencia obligatoria (UNIQUE provider+event_id,
    provider_payment_id). Un retry jamás cobra dos veces.
14. Código/comentarios/DB en inglés. UI solo vía claves i18n ES-CL.
15. Dependencias: SOLO la lista cerrada (PRD-00 §10). Nuevo dep = decisión explícita del owner.
16. Archivos: Supabase Storage con path org_id/… y URLs firmadas con expiración.
17. Prohibido inventar U_w / R_w. Solo desde ficha certificada o no se muestra.
18. offcut_inventory: schema existe, producción prohibida hasta Fase 4.
19. Cada PR cierra con: pytest ✓ · vitest ✓ · ruff ✓ · mypy engine ✓ · checklist DoD.
20. Si el spec tiene un hueco: DETENTE y añade [PENDIENTE-DECISIÓN]. No rellenes con supuestos.
21. AUDITORÍA DE PRECIOS: todo cambio de precio genera fila en price_audit_logs antes de aplicarse.
```

---

## 2. PRECEDENCIA DE DISEÑO

> **Precedencia de Diseño:** `PRD-DESIGN-SYSTEM-ADOBE` (v1.2) es **canónico** para todos los tokens de color, temas dual (Light Studio / Dark Graphite) y layout CAD. `UI_UX_DESIGN_SYSTEM` (v1.0) queda **SUPERSEDED** en tokens; sus §4 (specs de componentes: WorkshopApprovalButton, SVGCotaAnnotation, InspectorFindingCard) permanecen vigentes pero **deben re-expresarse con los tokens ADOBE** (prohibido hex hardcodeado — usar variables `--theme-*`). Ante conflicto visual, gana ADOBE.

---

## APÉNDICE A — ENMIENDAS v1.1.2

> **INSTRUCCIÓN DE INTEGRACIÓN:** Este apéndice tiene **precedencia normativa sobre cualquier texto anterior en caso de conflicto**. Nada fuera de este apéndice se modifica.

### ENMIENDA 1 — DDL DE HARDWARE_KITS, BILLING, LEDGER Y ROLES (F1, P1-1 & H3)

- **Kits de Herrajes:** Tabla `hardware_kits` incorporada con unicidad `(system_id, sku)`, RLS y matching por tipología normalizada, rail_type y peso.
- **Roles:** `SUPERADMIN` es rol de plataforma (`auth.jwt() -> 'app_metadata' ->> 'is_superadmin' = 'true'` — editable únicamente vía service_role / Admin API de Supabase, o tabla `platform_admins`) y no forma parte del enum `org_role`.
- **Precedencia de Pesos:** `profile_articles.weight_kg_m` prevalece sobre `SystemParams.pvc_weight_kg_m` (fallback).
- **Semilla de Acero y Herraje:** `steel_weight_kg_m = 1.7000` y `hardware_kit_weight_kg = 2.50`.

```sql
-- Kits de Herraje Canónicos (Enmienda F1)
CREATE TABLE hardware_kits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    system_id UUID REFERENCES profile_systems(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    opening_type VARCHAR(30) NOT NULL,
    min_leaf_width_mm NUMERIC(10,2) NOT NULL,
    max_leaf_width_mm NUMERIC(10,2) NOT NULL,
    min_leaf_height_mm NUMERIC(10,2) NOT NULL,
    max_leaf_height_mm NUMERIC(10,2) NOT NULL,
    max_leaf_weight_kg NUMERIC(6,2) NOT NULL,
    rail_type VARCHAR(10) NOT NULL DEFAULT 'dual',
    carriages_qty INT NOT NULL DEFAULT 2,
    stay_arms_qty INT NOT NULL DEFAULT 1,
    contents JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_kit_system_sku UNIQUE (system_id, sku)
);
```

---

### ENMIENDA 2 — EJEMPLO GOLDEN Y DERIVACIÓN DE ESPESOR NETO (P1-7 & H1)

> **Regla de Generación Automatizada:** El snapshot `engine/tests/golden_example.json` se **GENERA** ejecutando `/engine` sobre el request con `glass_spec` en el SHOT-06. La regla de derivación suma exclusivamente los paños de cristal (`4-16-4` $\rightarrow 8.00\text{ mm}$; `4-12-4` $\rightarrow 8.00\text{ mm}$; `6-12-6` $\rightarrow 12.00\text{ mm}$; monolítico $\rightarrow$ espesor propio).

---

## APÉNDICE B — GATES DE NEGOCIO, MÉTRICAS Y RIESGOS

### B.1 Métricas de Negocio
- **North Star Metric:** Tiempo mediano de solicitud cliente $\rightarrow$ cotización lista para enviar (< 5 min con IA, < 20 min manual).
- **Negocio Año 1:** 15 talleres pagando a mes 6; 40 a mes 12 · Churn mensual < 6% · Conversión trial $\rightarrow$ pago > 25% · Costo modelos < 25% del revenue Pro/Business · CAC $\approx$ 0.

### B.2 Matriz de Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Motor inexacto | Mortal | Casos de oro G1–G12 0.00 mm; no lanzar IA sobre serie en rojo |
| IA alucina una medida y se fabrica | Mortal | Semáforo + bloqueo OT + ancla visual (R01–R14) |
| Taller espera "todas las series" día 1 | Alto | Una serie perfecta (Demo 60) + compilador asistido |
| Costo de API se dispara | Alto | Caps de créditos, router, techo 500 en trial |
| Subida de precio de visión | Medio | Gateway agnóstico; conversión privada ajustable |
| Pasarela/entidad Chile | Alto | Flow + SpA en Fase 0 (D1/D4) |

### B.3 Los 10 Criterios Go/No-Go de Lanzamiento
1. G1–G12 (excepto G10) en verde con sign-off del fundador contra fabricación real.
2. 5 proyectos reales cotizados y fabricados sin desvío de vidrio ni de perfil.
3. PDF, Excel, OT, pedido a proveedor, corte y costos con BOM Hash idéntico.
4. Un usuario nuevo completa una cotización moderada sin llamada de soporte.
5. El cap de créditos funciona: un loop de OCR no puede exceder el saldo.
6. Fin responde las 20 preguntas de onboarding.
7. Un backup se restauró al menos una vez en ensayo (Gate 7 de PRD-19).
8. Términos legales de "humano aprueba" publicados en Framer (Semanas 8–9).
9. Checkout sandbox Flow y Creem funcional.
10. Débito de créditos 100% idempotente (`payment_events` + `credit_ledger` verificados).

---

## PLAN DE EJECUCIÓN SHOT-01 → SHOT-24 (Resumen)

*(Ver especificación completa con gates y pre-requisitos en [`PLAN_DE_EJECUCION_SHOTS.md`](file:///c:/Users/alios/Documents/antigravity/vibrant-hertz/docs/PLAN_DE_EJECUCION_SHOTS.md))*

- **SHOT-01:** Monorepo + CI + Constitución aplicada.
- **SHOT-02:** DDL completo + `hardware_kits` + RLS + tests aislamiento (Supabase CLI en CI).
- **SHOT-03:** Engine núcleo (G1–G4 en 0.00).
- **SHOT-04:** Auth + tenancy + API skeleton DRF/JWT/OpenAPI + PostHog base + shell app ADOBE dual.
- **SHOT-05:** Canvas 2D mínimo (fijo + cotas).
- **SHOT-06:** Engine total (SLIDING, DOOR, AWNING, resolución `hardware_kits` $\rightarrow$ G5–G12 en 0.00 + golden test generado).
- **SHOT-07:** Corte 1D BFD + Inspector R01–R14 (G7 puerta 0.00 + test optimizador barras 5.8m).
- **SHOT-08:** Precios 5 modos + listas de costo + `price_audit_logs`.
- **SHOT-09:** Documentos WeasyPrint & openpyxl + Pantalla S19 (Pedidos proveedor).
- **SHOT-10:** Flujo proyectos + versiones + **catálogos manuales (S02, S12, S13, S15, S16)**.
- **SHOT-11:** Billing Flow + créditos + trial + deploy prod con alertas de uptime y PITR R2.
- **SHOT-12:** **Starter end-to-end + validación fundador (Sign-off G-Pro1).**
- **SHOT-13:** AI Gateway + router `ai_routes` + semáforo + auditoría IA (costos T6/T8/T9).
- **SHOT-14:** Compilador T6 + preguntas T4 + G sintéticos (4 fixtures 0.00).
- **SHOT-15:** OCR T1 + pantalla S27 split-screen.
- **SHOT-16:** Comandos T2/T3/T5 + modal diff + undo sagrado.
- **SHOT-17:** Plantillas PDF 3 slots + bloques protegidos.
- **SHOT-18:** Creem global + landing legal en Framer (w8-9) $\rightarrow$ **Profesional a cobro**.
- **SHOT-19:** 3D R3F + link `/view/`.
- **SHOT-20:** Catálogo global + cola admin (Pantalla S28).
- **SHOT-21:** Certificado T8 doble ciego + DOC-08 + QR $\rightarrow$ **Business a cobro**.
- **SHOT-22:** Comparador T10 + bandeja email (SendGrid).
- **SHOT-23:** Autopilot Max T9 + Fin + PostHog.
- **SHOT-24:** Retazos QR + WhatsApp + **G10 monoriel** + PT-BR + Vista instalador (S26).
