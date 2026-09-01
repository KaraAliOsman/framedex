# STACK OFICIAL DE MODELOS Y AI ROUTER 2026 — DEKOPEN (v1.2)
**Fecha:** 30 de Agosto de 2026  
**Estado:** Bloqueado / Congelado  
**Filosofía:** Nombres de marca propios (White-label), 99% de operaciones sobre GPT 5.6 Luna xHigh-Max (eficiente y ultra-rápido), activación explícita ("Modo Titan / Ultra-Ingeniería") para modelos pesados (Sol / Kimi k3), y pasarela internacional vía **Creem (Merchant of Record - MoR)**.

---

## 1. Arquitectura del AI Gateway y Nombres Propios de Marca

El usuario final y los clientes de los talleres **jamás ven nombres comerciales de proveedores de IA** ("GPT", "Gemini", "OpenAI", "Kimi"). La interfaz expone la suite de marca propia de Dekopen con tres niveles de potencia:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                DEKOPEN AI INTELLIGENCE SUITE                                     │
├───────────────────────────────┬──────────────────────────────────┬───────────────────────────────┤
│ ⚡ DEKOPEN NEURAL CORE™       │ 👁️ DEKOPEN VISION CAD™           │ 🔬 DEKOPEN TITAN ENGINE™      │
│ (99% de las Operaciones)      │ (Visión y Planos Multimodal)     │ (Modo Ultra-Ingeniería / Opt) │
├───────────────────────────────┼──────────────────────────────────┼───────────────────────────────┤
│ Backend: GPT 5.6 Luna xHigh   │ Backend: Gemini 3.7 High/GLM 5.3 │ Backend: GPT 5.6 Sol / Kimi k3│
│ Consumo: 1x (Ultra eficiente) │ Consumo: 2x (Solo con imágenes)  │ Consumo: 5x–10x (Bajo demanda)│
│ Para: Comandos, diffs, cotizar│ Para: OCR planos PDF y cuadros   │ Para: Catálogos 100p / Mega QC│
└───────────────────────────────┴──────────────────────────────────┴───────────────────────────────┘
```

---

## 2. Matriz de Enrutamiento Inteligente (AI Router)

| Nombre de Marca en UI | Nivel de Potencia / Modo | Backend Real | Casos de Uso Exclusivos | Consumo de Créditos |
|---|---|---|---|:---:|
| **Dekopen Neural Core™** | **Estándar (Default 99%)** | `gpt-5.6-luna-xhigh-max` | Comandos NLP (T2/T3), árbol paramétrico, explicaciones de taller (T5), cálculo comercial, semáforo y cotizador rápido (T9). | **Bajo** (1 a 4 cr) |
| **Dekopen Vision CAD™** | **Visión Multimodal** | `gemini-3.7-high` / `glm-5.3` | Se invoca **exclusivamente** al subir archivos visuales: extracción de vanos en planos arquitectónicos (T1) y reconocimiento de perfiles. | **Medio** (10 cr / plano) |
| **Dekopen Titan Engine™** | **Ultra-Ingeniería (Max Effort)** | `gpt-5.6-sol` | **Solo activable por el usuario con toggle explícito** en UI ("Activar Razonamiento Titan") para resolver proyectos de extrema complejidad o estructuras especiales. | **Alto** (15 a 50 cr) |
| **Dekopen Matrix Reader™** | **Catálogos Masivos (Long Context)** | `kimi-k3` | **Solo con toggle explícito** al compilar catálogos técnicos de más de 50 páginas con cientos de matrices de junquillos. | **Por página** ($25 + 2\text{ cr/pág}$) |

---

## 3. Pasarelas de Pago Multi-Región

| Región | Pasarela | Rol | Moneda | Razón de Elección |
|---|---|---|---|---|
| **Chile** | **Flow.cl** | Pasarela Directa | **CLP** | Medios de pago chilenos (Webpay, Khipu, Servipag) y emisión obligatoria de DTE / Factura Electrónica. |
| **Internacional (Global)** | **Creem** | **Merchant of Record (MoR)** | **USD** | **Cero fricción fiscal:** Creem recauda, declara y paga automáticamente los impuestos (Sales Tax en EE. UU., IVA/VAT en Europa y LatAm). |

---

## 4. UI/UX: Selector de Potencia en el Canvas CAD

En la barra de estado superior del Canvas 2D (Pantalla S06) y en la configuración de la Billetera (S20):

```
+----------------------------------------------------------------------------------------------------+
| MOTOR DE IA: [ (•) Dekopen Neural Core (Rápido)  |  ( ) Modo Titan Ultra-Ingeniería (Max Effort) ]  |
| ⚡ Modo Neural activo: 99.4% precisión matemática • 1.420 créditos disponibles                     |
+----------------------------------------------------------------------------------------------------+
```

---

## 5. Protocolo de Protección contra Desperdicio de Tokens (Zero-Waste)

Para garantizar un consumo mínimo de tokens tanto en desarrollo (Codex) como en la aplicación en producción (SaaS):

1. **Cálculos Matemáticos a $0 Token:** Ningún corte, medida, vidrio o cálculo de rentabilidad pasa por un LLM. Todo es procesado en microsegundos por el motor en Python `/engine`.
2. **Bloqueo Preventivo de Saldo Cero:** El backend verifica y bloquea el saldo en `credit_ledger` *antes* de enviar cualquier request a la API de OpenAI/Google. Si el saldo es 0, no se realiza la llamada HTTP.
3. **Payloads Estrictos con `max_output_tokens`:** Las respuestas de las Tools (T1 a T12) están forzadas a JSON estructurado y conciso (e.g., T2 devuelve ~50 tokens de diff, jamás párrafos explicativos innecesarios).
4. **Gating Visual:** Modelos multimodales (`Gemini 3.7 High`) se invocan **únicamente** cuando se adjunta un archivo PDF/imagen; las peticiones de texto plano se enrutan a modelos ultralivianos.
5. **Anti-Loop Circuit Breaker:** Cualquier fallo en OCR o NLP tiene un límite estricto de **1 reintento**. Prohibidos los bucles de llamadas infinitas.
6. **En Desarrollo (Codex):** El agente utiliza contexto JIT (lee solo el PRD del shot actual, ~2k tokens) y realiza ediciones quirúrgicas de líneas específicas en lugar de reescribir archivos enteros.

---

## 6. Plantilla de Variables de Entorno (`.env.example`)

```env
# ==============================================================================
# DEKOPEN AI GATEWAY & BILLING 2026 — VARIABLES DE ENTORNO
# ==============================================================================

# Core Backend
ENVIRONMENT=development
SECRET_KEY=django-insecure-change-this-in-production-key-seed-dekopen-2026
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,api.dekopen.com,backend-production.up.railway.app
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://app.dekopen.com

# Supabase Pro (PostgreSQL 16 con RLS + Auth + Storage)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...anon_key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...service_role_key
SUPABASE_JWT_SECRET=supabase-jwt-signing-secret-here

# Supabase Storage Buckets
SUPABASE_STORAGE_BUCKET_DOCS=dekopen-documents
SUPABASE_STORAGE_BUCKET_PLANS=dekopen-blueprints
SUPABASE_STORAGE_BUCKET_CATALOGS=dekopen-catalogs

# AI Gateway 2026 (99% Default: GPT 5.6 Luna xHigh-Max / Vision: Gemini 3.7 / Opt-in: Sol & Kimi)
OPENAI_API_KEY=sk-proj-your-openai-key-here
AI_MODEL_PRIMARY_NEURAL=gpt-5.6-luna-xhigh-max
AI_MODEL_TITAN_SOL=gpt-5.6-sol

GOOGLE_AI_API_KEY=AIzaSy-your-google-ai-key-here
AI_MODEL_VISION_CAD=gemini-3.7-high
GLM_API_KEY=glm-your-key-here
AI_MODEL_FALLBACK_VISION=glm-5.3

KIMI_API_KEY=kimi-your-key-here
AI_MODEL_TITAN_CATALOG=kimi-k3

AI_DEFAULT_EFFORT_LEVEL=neural_standard

# Payments: Flow.cl (Chile - CLP)
FLOW_API_KEY=flow_sandbox_api_key
FLOW_SECRET_KEY=flow_sandbox_secret_key
FLOW_API_URL=https://sandbox.flow.cl/api
FLOW_WEBHOOK_SECRET=flow_webhook_secret

# Payments: Creem Global MoR (USD - Taxes/VAT automatizado)
CREEM_ENVIRONMENT=sandbox
CREEM_API_KEY=creem_sandbox_api_key
CREEM_WEBHOOK_SECRET=creem_sandbox_webhook_secret
CREEM_CLIENT_TOKEN=creem_sandbox_client_token

# Mailing & Telemetry
RESEND_API_KEY=re_your_resend_api_key
DEFAULT_FROM_EMAIL=notificaciones@dekopen.com
CUSTOMERIO_SITE_ID=customerio_site_id
CUSTOMERIO_API_KEY=customerio_api_key

VITE_POSTHOG_KEY=phc_public_project_api_key
VITE_POSTHOG_HOST=https://us.i.posthog.com
VITE_FIN_INTERCOM_APP_ID=intercom_app_id
JAM_PROJECT_ID=jam_project_token
N8N_WEBHOOK_URL=https://dekopen.app.n8n.cloud/webhook/...
```
