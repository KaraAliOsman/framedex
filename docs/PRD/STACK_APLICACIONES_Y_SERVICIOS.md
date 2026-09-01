# STACK OFICIAL DE MODELOS Y AI ROUTER — DEKOPEN (v1.2)
**Estado:** Bloqueado / Congelado  
**Filosofía:** AI Gateway desacoplado, motor determinista a $0 tokens en `/engine`, y pasarelas de pago Flow.cl (Chile CLP) y Paddle (Global USD MoR).

---

## 1. Arquitectura del AI Gateway

El usuario final y los talleres operan sobre la interfaz de Dekopen con tres perfiles de procesamiento configurables vía variables de entorno:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                DEKOPEN AI INTELLIGENCE SUITE                                     │
├───────────────────────────────┬──────────────────────────────────┬───────────────────────────────┤
│ ⚡ MODELO PRINCIPAL NLP       │ 👁️ MODELO DE VISIÓN Y PLANOS     │ 🔬 VALIDADOR DE DOBLE CIEGO   │
│ (99% de las Operaciones)      │ (Extracción Multimodal)          │ (Certificación DOC-08 T8)     │
├───────────────────────────────┼──────────────────────────────────┼───────────────────────────────┤
│ Backend: OpenAI / LLM Estándar│ Backend: Google Gemini Vision    │ Backend: Proveedor Secundario │
│ Consumo: 1x (Ultra eficiente) │ Consumo: 2x (Solo con imágenes)  │ Consumo: 5x (Solo en T8)      │
│ Para: Comandos, diffs, cotizar│ Para: OCR planos PDF y cuadros   │ Para: Doble verificación T8   │
└───────────────────────────────┴──────────────────────────────────┴───────────────────────────────┘
```

---

## 2. Matriz de Enrutamiento Inteligente (AI Router)

| Nivel de Potencia | Backend Configurado | Casos de Uso Exclusivos | Consumo de Créditos |
|---|---|---|:---:|
| **Estándar NLP (Default 99%)** | `OPENAI_API_KEY` (GPT-4o / compatible) | Comandos NLP (T2/T3), árbol paramétrico, explicaciones de taller (T5), cálculo comercial y semáforo. | **Bajo** (1 a 4 cr) |
| **Visión Multimodal** | `GOOGLE_AI_API_KEY` (Gemini Vision) | Extracción de vanos en planos arquitectónicos PDF (T1), cuadros de medidas y fotos de cuadernos de obra. | **Medio** (10 cr / plano) |
| **Doble Verificador T8** | Proveedor Independiente Cruzado | Arbitraje independiente para la emisión del Certificado de Fabricabilidad (DOC-08). | **Fijo** (50 cr) |

---

## 3. Pasarelas de Pago Multi-Región

| Región | Pasarela | Rol | Moneda | Razón de Elección |
|---|---|---|---|---|
| **Chile** | **Flow.cl** | Pasarela Directa | **CLP** | Medios de pago chilenos (Webpay, Khipu, Servipag) y emisión obligatoria de DTE / Factura Electrónica. |
| **Internacional (Global)** | **Paddle** | **Merchant of Record (MoR)** | **USD** | **Cero fricción fiscal:** Paddle recauda, declara y paga automáticamente los impuestos (Sales Tax e IVA internacional). |

---

## 4. Protocolo de Protección contra Desperdicio de Tokens (Zero-Waste)

1. **Cálculos Matemáticos a $0 Token:** Ningún corte, medida, vidrio o cálculo de rentabilidad pasa por un LLM. Todo es procesado en microsegundos por el motor en Python `/engine`.
2. **Bloqueo Preventivo de Saldo Cero:** El backend verifica y bloquea el saldo en `credit_ledger` *antes* de enviar cualquier request a la API de IA. Si el saldo es 0, no se realiza la llamada HTTP.
3. **Payloads Estrictos con `max_output_tokens`:** Las respuestas de las Tools (T1 a T12) están forzadas a JSON estructurado y conciso (e.g., T2 devuelve ~50 tokens de diff, jamás párrafos explicativos innecesarios).
4. **Gating Visual:** Modelos multimodales se invocan **únicamente** cuando se adjunta un archivo PDF o imagen; las peticiones de texto plano se enrutan a modelos estándar.
5. **Anti-Loop Circuit Breaker:** Cualquier fallo en OCR o NLP tiene un límite estricto de **1 reintento**. Prohibidos los bucles de llamadas infinitas.
6. **En Desarrollo (Codex):** El agente utiliza contexto JIT (lee solo el PRD del shot actual, ~2k tokens) y realiza ediciones quirúrgicas de líneas específicas en lugar de reescribir archivos enteros.
