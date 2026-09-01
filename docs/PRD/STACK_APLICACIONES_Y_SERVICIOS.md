# STACK OFICIAL DE MODELOS Y AI ROUTER 2026 — DEKOPEN (v1.2)
**Estado:** Bloqueado / Congelado  
**Filosofía:** Enrutador de IA 2026 de alta gama: 99% de operaciones sobre **GPT 5.6 Luna xHigh-Max** (ultra-rápido y económico), **Gemini 3.7 High** para extracción visual de planos, y activación bajo demanda (**GPT 5.6 Sol Max / Kimi k3**) para tareas de alta complejidad.

---

## 1. Arquitectura del AI Gateway (Enrutamiento Inteligente)

El router de IA enruta dinámicamente cada petición al modelo óptimo según el tipo de tarea y payload:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                DEKOPEN AI INTELLIGENCE SUITE                                     │
├───────────────────────────────┬──────────────────────────────────┬───────────────────────────────┤
│ ⚡ MODELO PRINCIPAL NLP       │ 👁️ MODELO DE VISIÓN Y PLANOS     │ 🔬 MODO ULTRA-INGENIERÍA / QC │
│ (99% de las Operaciones)      │ (Extracción Multimodal)          │ (Certificación DOC-08 T8)     │
├───────────────────────────────┼──────────────────────────────────┼───────────────────────────────┤
│ Backend: GPT 5.6 Luna xHigh   │ Backend: Gemini 3.7 High         │ Backend: GPT 5.6 Sol / Kimi k3│
│ Consumo: 1x (Ultra eficiente) │ Consumo: 2x (Solo con imágenes)  │ Consumo: 5x–10x (Bajo demanda)│
│ Para: Comandos, diffs, cotizar│ Para: OCR planos PDF y cuadros   │ Para: Doble verificación T8   │
└───────────────────────────────┴──────────────────────────────────┴───────────────────────────────┘
```

---

## 2. Matriz de Enrutamiento por Modelo (AI Router)

| Nivel de Potencia | Backend Configurado | Casos de Uso Exclusivos | Consumo de Créditos |
|---|---|---|:---:|
| **Principal NLP (Default 99%)** | `gpt-5.6-luna-xhigh-max` | Comandos de diseño NLP (T2/T3), árbol paramétrico, explicaciones técnicas (T5), cotizador rápido y cálculo de rentabilidad. | **Bajo** (1 a 4 cr) |
| **Visión Multimodal** | `gemini-3.7-high` | Extracción de cuadros de vanos en planos arquitectónicos PDF (T1) y reconocimiento de cotas milimétricas. | **Medio** (10 cr / plano) |
| **Doble Verificador T8** | `gpt-5.6-sol` | Arbitraje independiente de doble ciego para la emisión del Certificado de Fabricabilidad (DOC-08). | **Fijo** (50 cr) |
| **Catálogos Extensos** | `kimi-k3` | Ingestión masiva de catálogos técnicos de 50+ páginas con tablas matriciales complejas de junquillos. | **Por página** ($25 + 2\text{ cr/pág}$) |

---

## 3. Pasarelas de Pago Multi-Región

| Región | Pasarela | Rol | Moneda | Razón de Elección |
|---|---|---|---|---|
| **Chile** | **Flow.cl** | Pasarela Directa | **CLP** | Medios de pago chilenos (Webpay, Khipu, Servipag) y emisión obligatoria de Factura Electrónica DTE con RUT. |
| **Internacional (Global)** | **Paddle** | **Merchant of Record (MoR)** | **USD** | **Cero fricción fiscal:** Paddle recauda, declara y liquida automáticamente los impuestos (Sales Tax en EE. UU. e IVA internacional). |

---

## 4. Protocolo de Protección contra Desperdicio de Tokens (Zero-Waste)

1. **Cálculos Matemáticos a $0 Token:** Ningún corte, medida, vidrio o cálculo de rentabilidad pasa por un LLM. Todo es procesado en microsegundos por el motor en Python `/engine`.
2. **Bloqueo Preventivo de Saldo Cero:** El backend verifica y bloquea el saldo en `credit_ledger` *antes* de enviar cualquier request a la API de IA. Si el saldo es 0, no se realiza la llamada HTTP.
3. **Payloads Estrictos con `max_output_tokens`:** Las respuestas de las Tools (T1 a T12) están forzadas a JSON estructurado y conciso (e.g., T2 devuelve ~50 tokens de diff, jamás párrafos explicativos innecesarios).
4. **Gating Visual:** Modelos multimodales (`Gemini 3.7 High`) se invocan **únicamente** cuando se adjunta un archivo PDF o imagen; las peticiones de texto plano se enrutan a `GPT 5.6 Luna`.
5. **Anti-Loop Circuit Breaker:** Cualquier fallo en OCR o NLP tiene un límite estricto de **1 reintento**. Prohibidos los bucles de llamadas infinitas.
6. **En Desarrollo (Codex):** El agente utiliza contexto JIT (lee solo el PRD del shot actual, ~2k tokens) y realiza ediciones quirúrgicas de líneas específicas en lugar de reescribir archivos enteros.
