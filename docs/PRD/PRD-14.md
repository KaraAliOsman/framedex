# PRD-14: CERTIFICADO DE FABRICABILIDAD Y DOBLE VERIFICADOR (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (Agent-Ready Bootstrap)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 3 (Garantía y Certificación)  
**Bloquea a:** PRD-15

---

## 1. Misión del Certificado de Fabricabilidad

El Certificado de Fabricabilidad (Documento **DOC-08** y Tool **T8**) es una garantía técnica digital que valida que un proyecto cumple al 100% con las normas de resistencia mecánica al viento (NCh 432), seguridad en acristalamiento (NCh 132), límites dimensionales y capacidades de herrajes de los sistemas de perfiles utilizados.

---

## 2. Protocolo de Doble Verificación Cruzada (Tool T8 — ~50 Créditos Estimados)

Para emitir el sello de certificación oficial sin quemar tokens innecesarios, el sistema ejecuta una auditoría de **doble ciego** entre dos arquitecturas de LLM independientes:

```
                  [ Árbol Paramétrico + BOM + Memoria de Cálculo ]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
      [ Modelo A: Principal NLP ]                     [ Modelo B: Verificador Cruzado ]
        (GPT 5.6 Luna xHigh-Max)                        (Gemini 3.7 High / GPT 5.6 Sol)
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

1. **Auditoría Estándar (~50 créditos estimados por tokens):** Cruza el Modelo Principal NLP (`gpt-5.6-luna-xhigh-max`) con el Modelo Visión/Auditor (`gemini-3.7-high`).
2. **Modo Auditoría Avanzada (Opt-in):** Si el usuario activa explícitamente el toggle de máxima verificación, el segundo árbitro escala a `gpt-5.6-sol`.
3. **Concordancia Matemática Obligatoria:** Cualquier desviación $> 0.00\text{ mm}$ en holguras o $> 0.1\text{ kg}$ en peso de hoja bloquea la emisión del certificado y alerta al taller.
4. **Sello Criptográfico:** Al aprobarse, genera el documento **DOC-08** con código QR público que resuelve el estado de fabricación sin exponer costos ni despiece confidencial del taller.
