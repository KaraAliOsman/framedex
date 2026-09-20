# PRD-14: CERTIFICADO DE FABRICABILIDAD Y DOBLE VERIFICADOR (v1.2)
**Estado:** Bloqueado / Congelado
**Versión:** 1.2 (Agent-Ready Bootstrap)
**Fase:** 3 (Garantía y Certificación)
**Bloquea a:** PRD-15

---

## 1. Misión del Certificado de Fabricabilidad

El Certificado de Fabricabilidad (Documento **DOC-08** y Tool **T8**) es una garantía técnica digital que valida que un proyecto cumple al 100% con las normas de resistencia mecánica al viento (NCh 432), seguridad en acristalamiento (NCh 132), límites dimensionales y capacidades de herrajes de los sistemas de perfiles utilizados.

---

## 2. Protocolo de Doble Verificación Cruzada (Tool T8 — 50 Créditos)

Para emitir el sello de certificación oficial sin quemar tokens innecesarios, el sistema ejecuta una auditoría de **doble ciego** entre dos arquitecturas independientes:

```
                  [ Árbol Paramétrico + BOM + Memoria de Cálculo ]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
      [ Modelo A: Dekopen Neural Core™ ]          [ Modelo B: Dekopen Vision CAD™ / Titan ]
         (Modelo A configurado en ai_routes)                      (Modelo B distinto, configurado en ai_routes)
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                             [ Árbitro Determinista ]
                                (Concordancia 100%)
                                         │
                     ┌───────────────────┴───────────────────┐
                     ▼                                       ▼
        [ 🟢 Coincidencia Total ]               [ 🔴 Discrepancia > 0.00 mm ]
        Sello DOC-08 + Hash + QR                Alerta Crítica + Bloqueo OT
```

---

## 3. Reglas Normativas de T8

1. **Auditoría Estándar (Default 50 créditos):** Cruza **Dekopen Neural Core™** con **Dekopen Vision CAD™**, usando modelos distintos y evaluaciones independientes de doble ciego.
2. **Modo Titan (opción explícita):** Si el usuario activa explícitamente el toggle de ultra-razonamiento, el segundo árbitro escala a **Dekopen Titan Engine™**, manteniendo un modelo distinto del evaluador A.
3. **Concordancia Matemática Obligatoria:** Cualquier desviación $> 0.00\text{ mm}$ en holguras o $> 0.1\text{ kg}$ en peso de hoja bloquea la emisión del certificado y alerta al taller.
4. **Sello Criptográfico:** Al aprobarse, genera el documento **DOC-08** con código QR público que resuelve el estado de fabricación sin exponer costos ni despiece confidencial del taller.

La independencia, el doble ciego, el árbitro determinista, los umbrales y el opt-in humano son
contratos de producto. Los proveedores, modelos concretos y métodos internos se resuelven por
`ai_routes` conforme a [PRD-13](./PRD-13.md) y [FUTURE_CAPABILITIES §3](./FUTURE_CAPABILITIES.md#3-principio-de-neutralidad-tecnológica-y-de-ia-ai-capability-neutral).
Cambiar un nombre de modelo no autoriza cambiar billing, auditoría, bloqueos ni emisión.
