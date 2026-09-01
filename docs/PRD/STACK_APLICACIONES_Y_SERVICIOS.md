# STACK OFICIAL DE APLICACIONES, SERVICIOS Y RECURSOS — DEKOPEN (v1.2)
**Estado:** Bloqueado / Congelado  
**Regla de Oro:** **Separación Estricta Producto vs Herramientas Internas.** Las herramientas personales de desarrollo se usan **exclusivamente para gestión interna**; la infraestructura de cara al cliente es **100% multi-tenant y escalable** con $0 gasto de bolsillo gracias a los beneficios Founder/Insider.

---

## 1. Infraestructura de Producto Multi-Tenant (Producción / Clientes)

Servicios escalables que atienden a los talleres, cotizaciones y usuarios en producción:

| Servicio / Infraestructura | Plan / Beneficio Real | Rol en la Plataforma Dekopen | Integración en Shot |
|---|---|---|:---:|
| 🐘 **Supabase Pro** | 1 año en créditos | Base de Datos PostgreSQL 16 con RLS multi-tenant, Auth por Magic Link, Storage de planos, PDFs y respaldos diarios. | **SHOT-02 / SHOT-04** |
| 🚂 **Railway** | 1 año Hobby / Deploy | Hosting de la API Django (DRF), colas asíncronas Huey y health checks continuos. | **SHOT-04 / SHOT-11** |
| 🦔 **PostHog Scale** | 1 año con 2x límites ($16.5k) | Telemetría global de usuarios, Session Replays en el Canvas 2D y embudos de conversión. | **SHOT-04 / SHOT-23** |
| 🤖 **Intercom + Fin AI** | 1 año (5 seats + $100/mo) | Agente de IA para soporte 24/7 a clientes y onboarding guiado de carpintería. | **SHOT-04 / SHOT-23** |
| ✉️ **Customer.io** | 1 año Essentials ($1.2k) | Automatización de ciclo de vida, emails de onboarding y reactivación de cotizaciones. | **SHOT-11 / SHOT-18** |
| 📬 **Resend** | 1 año Transactional Pro | Envío masivo y transaccional de cotizaciones PDF (DOC-01), Magic Links y alertas. | **SHOT-04 / SHOT-09** |
| 🍓 **Jam.dev** | 1 año Team (10 seats) | Widget de reporte visual de bugs en la app (graba pantalla y consola si el Canvas falla). | **SHOT-04 / SHOT-10** |
| ⚡ **n8n Cloud** | 1 año Starter | Orquestación visual de webhooks, sincronización CRM y alertas a administradores. | **SHOT-11 / SHOT-17** |
| 🖥️ **Framer Pro** | 1 año Framer Pro | Landing page comercial pública para captación y onboarding de los primeros 50 talleres. | **SHOT-18** |
| 🌐 **Cloudflare** | Plan Gratuito de por vida | Proxy CDN global, protección contra ataques DDoS y certificados SSL automáticos. | **SHOT-04 / SHOT-11** |
| 🇨🇱 **Flow.cl** | Pasarela Directa (Chile) | Cobro nativo en Pesos Chilenos (CLP) por Webpay Plus, Khipu, Servipag y emisión obligatoria de Factura Electrónica DTE con RUT. | **SHOT-11** |
| 🌎 **Paddle** | Merchant of Record (MoR) | Cobro mundial en Dólares (USD) con retención y liquidación automática de impuestos internacionales (Sales Tax / IVA). | **SHOT-18** |

---

## 2. Suite Interna de Desarrollo y Operaciones (Uso Exclusivo del Fundador / Equipo)

Herramientas para acelerar la construcción, diseño y gestión del proyecto sin acoplamiento con la app de clientes:

| Herramienta | Beneficio Real | Uso Exclusivo en Desarrollo y Operaciones |
|---|---|---|
| 📐 **Linear Business** | 1 año gratis (5 seats) | Gestión del backlog técnico, sprints y seguimiento de los 24 shots. |
| 📱 **Mobbin Team** | 1 año gratis (10 seats) | Referencia UI/UX para diseño de componentes técnicos en Figma y pantallas S01–S28. |
| 💻 **Cursor Pro & Warp Build** | 1 año gratis cada uno | Entornos de desarrollo asistidos por IA y terminal agentic para construcción rápida. |
| 🌐 **Google AI Pro** | 1 año gratis (5 TB Storage) | Modelos Gemini y 5 TB de almacenamiento seguro para respaldos locales del equipo. |
| 📝 **Notion Business** | 1 año gratis | Base de conocimiento interna, minutas y documentación privada del equipo. |
| 🏦 **Mercury Personal** | 2 años gratis | Operaciones financieras y recepción de fondos internacionales del fundador. |
| 🎙️ **ElevenLabs & Supercut** | 1 año gratis cada uno | Creación de videos tutoriales, demos de producto y onboarding en audio/video. |

---

## 3. Arquitectura del AI Router Dinámico (`ai_routes`)

El backend desacopla los modelos de la lógica de negocio mediante la tabla `ai_routes` en PostgreSQL y variables de entorno:

| Nivel de Carga | Configuración Técnica | Modelo Asignado | Casos de Uso Exclusivos | Consumo de Créditos |
|---|---|---|---|:---:|
| **Principal NLP (99% de tareas)** | `AI_MODEL_PRIMARY` / `OPENAI_API_KEY` | `gpt-5.6-luna-xhigh-max` | Comandos de diseño NLP (T2/T3), árbol paramétrico, explicaciones técnicas (T5), cotizador rápido y cálculo de rentabilidad. | **Bajo** (~1 a 4 cr) |
| **Visión Multimodal** | `AI_MODEL_VISION` / `GOOGLE_AI_API_KEY` | `gemini-3.7-high` | Extracción de cuadros de vanos en planos arquitectónicos PDF (T1) y reconocimiento de cotas milimétricas. | **Medio** (~10 cr / plano) |
| **Doble Verificador T8** | `AI_MODEL_DUAL_AUDIT` / `OPENAI_API_KEY` | `gpt-5.6-sol` | Arbitraje independiente de doble ciego para la emisión del Certificado de Fabricabilidad (DOC-08). | **Fijo** (~50 cr) |
| **Catálogos Extensos** | `AI_MODEL_CATALOG` / `KIMI_API_KEY` | `kimi-k3` | Ingestión masiva de catálogos técnicos de 50+ páginas con tablas matriciales complejas de junquillos. | **Por página** (~$25 + 2\text{ cr/pág}$) |

---

## 4. Gobernanza y Medición de Tokens

1. **Cálculos Matemáticos a $0 Token:** Ningún corte, medida, vidrio o cálculo de rentabilidad pasa por un LLM. Todo es procesado en microsegundos por el motor en Python `/engine`.
2. **Bloqueo Preventivo de Saldo Cero:** El backend verifica y bloquea el saldo en `credit_ledger` *antes* de enviar cualquier request a la API de IA. Si el saldo es 0, no se realiza la llamada HTTP.
3. **Payloads Estrictos con `max_output_tokens`:** Las respuestas de las Tools (T1 a T12) están forzadas a JSON estructurado y conciso (e.g., T2 devuelve ~50 tokens de diff, jamás párrafos explicativos innecesarios).
4. **Gating Visual:** Modelos multimodales se invocan **únicamente** cuando se adjunta un archivo PDF o imagen; las peticiones de texto plano se enrutan al modelo principal.
5. **Anti-Loop Circuit Breaker:** Cualquier fallo en OCR o NLP tiene un límite estricto de **1 reintento**. Prohibidos los bucles de llamadas infinitas.
