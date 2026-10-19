---
type: synthesis
status: active
updated: 2026-10-18
volatility: high
verified_ref: 6f78e3299d93816991fb7c2fe2a2044458fc5e7a
sources:
  - docs/operations/ACTIVACION.md
  - docs/operations/PRODUCTION_RECOVERY.md
  - backend/config/production.py
  - official provider documentation consulted 2026-10-18
---

# Servicios y dependencias de lanzamiento

Inspección estática del 18-10-2026 en `claude/v1-implementacion`, HEAD indicado
más cambios locales extensos. Es inventario de conexión y recomendación; no
acredita cuentas activas, precios aprobados, despliegue ni pruebas productivas.
Se conserva el [límite del dueño](../sources/owner-launch-boundary-2026-10-18.md).

## Base comprobada en el repositorio

Los archivos Railway definen API, frontend, worker persistente y dos tareas
programadas: reconciliación de cobros y copia de base. Son servicios del mismo
proyecto, no cinco proveedores nuevos. [production.py](../../../backend/config/production.py)
exige `REDIS_URL`; [throttling.py](../../../backend/config/throttling.py) y
[health.py](../../../backend/config/health.py) usan Redis. Puede provisionarse
junto con el despliegue Railway, sin requerir otra cuenta de caché.

El [índice de activación](../../operations/ACTIVACION.md) incluye Supabase
Postgres/Auth/Storage, Flow, correo SMTP y MiMo. Distingue credenciales Flow de
la plataforma para suscripciones/créditos de las integraciones privadas de
cada taller para cobrar sus obras. No mezclarlas.

El [runbook de recuperación](../../operations/PRODUCTION_RECOVERY.md) prevé
Railway Pro y Supabase Pro, Small y PITR. Son dirección histórica del runbook,
no una cotización vigente ni contratación realizada en esta consulta. Antes
de activar, revisar capacidad, recuperación y costo con el dueño.

## Información externa comprobada

- [Railway: red saliente](https://docs.railway.com/networking/outbound-networking):
  SMTP disponible desde Pro; Free/Trial/Hobby requieren un transporte HTTPS.
  El correo actual usa SMTP: Hobby implica adaptar código, no solo cambiar llaves.
- [Supabase: SMTP](https://supabase.com/docs/guides/auth/auth-smtp): el correo
  predeterminado es para pruebas, restringido; acceso/invitaciones necesitan
  SMTP propio para usuarios reales. Un mismo proveedor puede servir Auth y Django.
- [Resend: SMTP](https://resend.com/features/smtp-service): opción compatible;
  verificar dominio/remitentes. Es recomendación, no proveedor contratado.
- [Supabase: backups](https://supabase.com/docs/guides/platform/backups): los
  respaldos de base no incluyen los objetos de Storage. Definir y probar también
  recuperación de documentos/imágenes y custodia de claves de cifrado.
- [Cloudflare Free](https://www.cloudflare.com/plans/free/): candidato inicial
  para DNS, TLS y protección del sitio. Dominio y hosting conservan sus costos;
  no se infiere que sus productos adicionales estén incluidos sin límites.
- [Flow: suscripciones](https://developers.flow.cl/docs/suscripciones/integration-flow):
  planes, cliente, registro de tarjeta y suscripción son pasos diferenciados.
  Verificar servicio de cargos automáticos habilitado, credenciales y callbacks;
  no confundir pago único con renovación recurrente comprobada.

## Inventario operativo recomendado

Dominio y DNS/HTTPS; Railway con servicios, Redis y tareas programadas;
Supabase con base/auth/archivos y recuperación; comercio Flow; cuenta API MiMo
con saldo; proveedor de correo con dominio verificado. Configurar remitentes,
retornos de acceso/pago, webhooks y secretos según el índice de activación.
El dominio puede tener `app` y web pública como subdominios del mismo registro.

Antes de lanzar, activar alertas de fallos/costos, comprobar recuperación y
recorrer alta/acceso, cotización, adjuntos, IA y pago/renovación en el entorno
destino. Sentry, analítica de producto y uptime externo son opciones, no cuentas
obligatorias inferidas del código. La emisión tributaria dentro de DEKOPEN
requiere su activación SII/DTE específica; no asumirla conectada por usar Flow.
Esta consulta no activa proveedores, pagos, DNS ni infraestructura.
