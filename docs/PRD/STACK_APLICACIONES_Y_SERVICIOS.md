# STACK DE APLICACIONES Y SERVICIOS — DEKOPEN (v1.3)

> **Estado:** inventario operativo no normativo.
> Los contratos de producto viven en los PRD activos, la Constitución y las migraciones. Esta
> página distingue infraestructura de producto, beneficios temporales del fundador y rutas de
> IA; no congela promociones, proveedores ni instrucciones para agentes como arquitectura.

## 1. Infraestructura de producto

Estas son las integraciones actuales del despliegue. El contrato funcional y de seguridad de
cada una pertenece al PRD que la introduce; una sustitución compatible se decide allí.

| Servicio | Rol de producto | Shot de integración |
|---|---|---|
| Supabase | PostgreSQL, RLS, Auth y Storage multi-tenant | SHOT-02 / SHOT-04 |
| Railway | API Django, workers y health checks | SHOT-04 / SHOT-11 |
| PostHog | Telemetría y embudos | SHOT-04 / SHOT-23 |
| Intercom/Fin | Soporte y onboarding | SHOT-04 / SHOT-23 |
| Customer.io o servicio equivalente | Automatización de ciclo de vida | SHOT-11 / SHOT-18 |
| Servicio de correo transaccional | Magic Links, cotizaciones y alertas | SHOT-04 / SHOT-09 |
| n8n o servicio equivalente | Orquestación operativa | SHOT-11 / SHOT-17 |
| Framer o servicio equivalente | Landing pública | SHOT-18 |
| Cloudflare | Proxy, CDN y protección perimetral | SHOT-04 / SHOT-11 |
| Flow.cl | Cobro local y DTE | SHOT-11 |
| Paddle | Merchant of Record internacional | SHOT-18 |

La disponibilidad, retención, RLS, almacenamiento firmado, backups y recuperación se rigen por
PRD-02, PRD-03 y PRD-19. Los nombres de planes o beneficios de terceros no son requisitos de
producto.

## 2. Herramientas internas y beneficios temporales

Estas herramientas sirven para desarrollo, diseño, documentación u operaciones del fundador.
Son una línea base temporal y no una dependencia de runtime ni una obligación para el producto:

- Linear, Mobbin, Figma, editores asistidos y terminales de desarrollo;
- Notion y herramientas de documentación privada;
- servicios de referencia o almacenamiento personal;
- herramientas de captura de bugs, tutoriales y demos.

Una mención aquí no autoriza acceso a datos de clientes ni cambia la arquitectura multi-tenant.

## 3. Capacidades de IA y rutas de runtime

La interfaz de producto expone capacidades lógicas, no proveedores crudos. El gateway resuelve
cada capacidad con ai_routes; proveedor, modelo, límites y fallback son configuración
operativa versionada junto al runtime.

| Capacidad | Ruta lógica | Uso |
|---|---|---|
| Asistencia de texto y comandos | text-command / text-assist | T2, T4, T5, T7, T11, T12 |
| Extracción y comparación multimodal | multimodal-extraction / multimodal-comparison | T1, T10 |
| Compilación técnica | catalog-compilation | T6 |
| Asistencia comercial | pricing-assist | T3 |
| Doble verificación | dual-verification | T8 |
| Pipeline multimodal de borrador | multimodal-pipeline | T9 |

Las rutas pueden cambiar o incorporar fallbacks sin cambiar el contrato de negocio. Deben
conservar auditoría previa, aislamiento RLS, validación tipada, revisión humana donde aplique y
recalculo determinista en /engine. La configuración concreta vigente se mantiene en runtime
(por ejemplo, variables de entorno y registros de rutas), no en este documento.

## 4. Guardrails observables

1. Los cálculos de medidas, corte, BOM y rentabilidad se ejecutan en /engine, sin IA.
2. El saldo se bloquea antes de una invocación y el consumo se registra con tokens reales.
3. Las respuestas de herramientas usan esquemas tipados y límites configurables.
4. Una entrada multimodal solo usa una ruta multimodal; un fallo tiene reintentos acotados.
5. Ninguna ruta de IA escribe números técnicos finales ni evita auditoría, RLS o revisión humana.
