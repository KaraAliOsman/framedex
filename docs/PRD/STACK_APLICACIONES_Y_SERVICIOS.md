# STACK DE APLICACIONES Y SERVICIOS — DEKOPEN

**Autoridad:** índice operativo. Los PRD de dominio y la Constitución gobiernan el producto;
solo los guardrails de §4 conservan requisitos de producto propios de este documento.
La separación es estricta: herramientas personales sirven al equipo; infraestructura de
clientes conserva aislamiento multi-tenant. Una promoción no determina arquitectura.

## 1. Baseline de producto y fuentes

Esta tabla reúne selecciones actuales y planificadas; no afirma que todos los servicios estén
desplegados. La [dirección de producto](../PRODUCT.md) determina cuándo se introducen.

| Servicio / baseline | Rol | Fuente contractual |
|---|---|---|
| Supabase PostgreSQL 17, Auth, Storage | Datos, RLS, Magic Link, archivos firmados | PRD-02, PRD-03, PRD-19; PD-11-04; Constitución |
| Railway, Django, Huey/Redis | API, workers, despliegue y salud | PRD-00, PRD-19 |
| PostHog | Telemetría y embudos | PRD-19; SHOT-04/23 |
| Intercom/Fin | Soporte | roadmap |
| Customer.io | Baseline operativa de ciclo de vida | Sin gate adicional por esta mención |
| Resend | Baseline de correo transaccional | El contrato de cada flujo de correo gobierna |
| Jam.dev | Reporte de errores en SPA | PRD-19 §4 |
| n8n Cloud | Baseline de orquestación interna | No sustituye pagos, auditoría ni idempotencia |
| Framer | Landing | PRD-18 |
| Cloudflare | Perímetro y CDN | PRD-19 |
| Flow.cl / Paddle | Pagos Chile / internacionales | PRD-03 |

Las sustituciones estratégicas siguen la Regla 15. Este índice no autoriza reemplazar servicios
fijados por un PRD, cambiar arquitectura ni adelantar shots.

## 2. Herramientas internas y beneficios temporales — no normativos

Linear, Mobbin, Cursor/Warp, Google AI Pro, Notion, Mercury, ElevenLabs y Supercut son referencias
de trabajo interno. Las promociones de créditos, duración, seats y descuentos son condiciones
comerciales temporales, sin garantía de disponibilidad ni autoridad sobre arquitectura o gates.
Sus detalles históricos permanecen en Git y en las compilaciones históricas.

## 3. Selección de IA — configuración operativa

[PRD-13](./PRD-13.md) define capacidades y enrutamiento dinámico mediante `ai_routes` y variables
de entorno; [PRD-14](./PRD-14.md) conserva doble ciego entre modelos distintos y opt-in Titan.
Los nombres de modelos, proveedores, cuotas de tráfico y métodos internos no se congelan aquí.
La configuración existente, incluida `.env.example`, no cambia por esta clasificación.
Billing y las estimaciones de consumo se rigen por [PRD-03 §4](./PRD-03.md#4-billetera-y-consumo-de-créditos-de-ia-medición-dinámica-por-tokens-reales).

## 4. Guardrails de producto conservados

- Cálculos de corte, medidas, vidrio y rentabilidad: `/engine`, según la Constitución.
- Saldo y bloqueo previo, salida JSON tipada y auditoría: PRD-13. Los límites concretos de
  `max_output_tokens` son configuración; ejemplos como «50 tokens» no son requisitos.
- Gating visual: las llamadas de visión se usan cuando se adjunta PDF o imagen; las peticiones
  de texto plano se enrutan a la capacidad de texto, sin fijar proveedores.
- Circuit breaker OCR/NLP: máximo **1 reintento**; se conserva este límite contractual.

Las instrucciones de desarrollo viven en [AGENTS.md](../../AGENTS.md), no en el stack de producto.
