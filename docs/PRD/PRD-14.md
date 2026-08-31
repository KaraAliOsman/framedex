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

## 2. Protocolo de Doble Verificación Cruzada (Tool T8 — 50 Créditos)

Para emitir el sello de certificación oficial sin quemar tokens innecesarios, el sistema ejecuta una auditoría de **doble ciego** entre dos arquitecturas independientes:

```
                  [ Árbol Paramétrico + BOM + Memoria de Cálculo ]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [ Modelo A: Dekopen Neural Core™ ]           [ Modelo B: Dekopen Vision CAD™ ]
        (GPT 5.6 Luna xHigh-Max)                      (Gemini 3.7 High / GLM 5.3)
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

### Reglas Normativas de T8
1. **Auditoría Estándar (Default 50 créditos):** Cruza **Dekopen Neural Core™ (GPT 5.6 Luna)** con **Dekopen Vision CAD™ (Gemini 3.7 High)**. No consume tokens de modelos masivos.
2. **Opción Ultra-Ingeniería (Modo Titan):** Si el usuario activa explícitamente el toggle *"Auditoría Titan (Max Effort)"*, el segundo árbitro escala a **Dekopen Titan Engine™ (GPT 5.6 Sol)**.
3. **Concordancia Matemática:** Cualquier desviación $> 0.00\text{ mm}$ en holguras o $> 0.1\text{ kg}$ en peso de hoja bloquea la emisión del certificado y alerta al taller con frase de inspección.
