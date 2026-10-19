# Traspaso a producción — candidata definitiva 18-10-2026

Estado: **candidata completa para revisión del dueño**. La aprobación del dueño y la habilitación de producción están **pendientes**. Nada de este documento se ha ejecutado contra Railway, Supabase de producción ni proveedores de pago. No contiene secretos: solo nombres de variables.

- Rama: `claude/v1-implementacion` · base `6f78e329` + cambios locales sin commit (ver `implementation-ledger.md`).
- Comprobado localmente: `make lint` (salvo 4 artefactos locales no versionados en `frontend/.run/`), `make typecheck`, pruebas de backend (1617) y frontend (1126), `make test-mutations` (28/28), `make build`, golden byte check. Ver `acceptance.md` para lo bloqueado.

## 1. Servicios (Railway)

Los manifiestos ya existen en la raíz y no cambian con esta entrega:

| Servicio | Manifiesto | Arranque | Salud |
|---|---|---|---|
| API Django | `railway.toml` (`Dockerfile`) | imagen por defecto (gunicorn) | `/health/ready/` |
| Worker de trabajos | `railway.worker.toml` | `python backend/manage.py runjobs` | renovación de lease cada 120 s |
| Web (SPA + proxy `/api`) | `railway.frontend.toml` (`frontend/Dockerfile`) | Node/estático, `PORT`, `BACKEND_ORIGIN` | `/` |
| Conciliación de cobros | `railway.billing.toml` | `reconcile_billing` cada 15 min | cron |
| Respaldo cifrado | `railway.backup.toml` | `backup_database.py scheduled` 03:00 | cron |

El copiloto **requiere el worker**: todas las tareas IA se ejecutan en `runjobs`. Sin worker, el popup abre y lee historial, pero las tareas quedan «En cola».

## 2. Variables por servicio (sin valores)

Referencia completa: `.env.example`. Nuevas o relevantes para esta entrega:

| Variable | Servicio | Nota |
|---|---|---|
| `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_VERIFY_MODE` | API, worker, billing | El worker usa la misma conexión con cambio de rol (`ai_backend`, `billing_backend`, `documentary_backend`). |
| `SUPABASE_STORAGE_BUCKET_DOCS=documents` | API, worker | Los adjuntos del copiloto se guardan en este bucket bajo `ai-attachments/{org}/{user}/…` (prefijo validado por `CHECK` en `ai_attachments`). |
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | Web (build args) | Únicas variables públicas. |
| `AI_GATEWAY_MIMO_API_KEY`, `AI_GATEWAY_MIMO_BASE_URL`, `AI_GATEWAY_MIMO_MODEL` | API, worker | Selección vigente MiMo 2.6 Pro para todos los planes IA; sin fallback. Si faltan, el resolvedor devuelve `provider_missing` y el popup lo explica. |
| `AI_GATEWAY_MIMO_TIMEOUT_S` | API, worker | Tope por petición (1–600). |
| `AI_AGENT_TOTAL_TIMEOUT_S` | worker | Nuevo valor por defecto 420 s (medido: 20–47 s por ronda MiMo, hasta 6 rondas). Máx. 600. |
| `AI_GATEWAY_MOCK_ENABLED` | — | Debe quedar **sin definir** en producción. |
| `FLOW_*`, `BILLING_CALLBACK_ORIGIN`, `BILLING_FRONTEND_ORIGIN`, `FLOW_MERCHANT_TIMEZONE` | API, billing | Flow (CLP). |
| `PADDLE_*` | API | Paddle (USD), si se activa. |
| `RELEASE_SHA` | API | Normalmente `RAILWAY_GIT_COMMIT_SHA`. |
| `REDIS_URL` | API, worker | Exigido por la configuración de producción (ver [conexiones de lanzamiento](../../wiki/quality/production-connections.md)). |
| `RESEND_API_KEY`, `DEFAULT_FROM_EMAIL` + SMTP de Supabase Auth | API, Auth | Enlaces mágicos y correos; Railway Hobby no permite SMTP saliente (usar envío HTTPS o plan Pro). |
| `BACKUP_DATABASE_URL`, `RESTORE_DATABASE_URL`, `BACKUP_ENCRYPTION_KEY` | backup | Custodia de la clave separada de los respaldos. |

## 3. Orden de conexión

1. **Supabase producción**: proyecto con Auth, Storage (bucket `documents` privado) y PostgreSQL 16. Respaldo previo verificado.
2. **Migraciones** (sección 4) con `supabase db push` contra el proyecto enlazado; luego `supabase db lint` y la batería pgTAP (`make test-db` en un stack limpio antes de tocar producción).
3. **API + worker** en Railway con las variables; comprobar `/health/ready/`, `manage.py check --deploy` y que el worker reclama un trabajo de prueba.
4. **Web** con `BACKEND_ORIGIN` apuntando a la API privada.
5. **Proveedor IA**: credenciales MiMo en API y worker; desde Empresa › Inteligencia artificial, el dueño ejecuta «Probar conexión» (con MFA) y fija presupuesto.
6. **Pagos**: Flow en modo sandbox; webhook/retorno a `BILLING_CALLBACK_ORIGIN`; conciliación cron. Solo tras aprobar precios (sección 6).
7. **Respaldo**: cron de respaldo y una restauración de prueba en `RESTORE_DATABASE_URL` (`docs/operations/PRODUCTION_RECOVERY.md`). El respaldo de base **no incluye objetos de Storage** (PDF emitidos, importaciones y adjuntos del copiloto): planificar su copia aparte.

## 4. Migraciones de esta entrega

Nuevas respecto del commit base (todas idempotentes con `IF NOT EXISTS`/`DROP … IF EXISTS` donde aplica):

| Versión | Contenido |
|---|---|
| `20270130000000_design_defaults` | Valores habituales por empresa/obra. |
| `20270130000100_finish_references` | Referencias de acabado. |
| `20270130000200_catalog_import_progress` | Progreso de importación de catálogos. |
| `20270130000300_commercial_documents` | Documentos comerciales. |
| `20270130000400_v1_project_read_grants` | Permisos de lectura de obra. |
| `20270201000000_credit_holds_capabilities` | `credit_holds` (RLS `billing_backend`), `ai_audit_logs.consumption_policy`. |
| `20270201000100_document_layout_plano` | Diseño `PLANO` para DOC-03. |
| `20270201000200_ai_threads_attachments` | `ai_threads`, `ai_attachments`, `thread_id`/`interaction_mode`/`autonomy`/`receipt` en `ai_jobs`; enlace idempotente de la historia anterior. |

**Divergencia conocida del entorno REVIEW** (no de producción): su base registra `20270130000000 presentation_changes`, `20270130000001 review_design_defaults_compat` y `20270131000000 catalog_visual_references`, que no existen en el repositorio, y las migraciones de esta entrega se aplicaron allí manualmente. **No copiar el historial de REVIEW a producción**: aplicar únicamente las migraciones del repositorio, en orden, sobre una base respaldada.

Recuperación: cada migración es aditiva salvo `document_layout_plano` (reemplaza un `CHECK`). Ante un fallo, restaurar el respaldo previo según `PRODUCTION_RECOVERY.md`; no editar `supabase_migrations.schema_migrations` a mano en producción.

## 5. Comprobaciones pendientes en el entorno de lanzamiento

- Arranque, healthchecks y worker reclamando trabajos; reinicio sin perder trabajos (lease).
- Auth (enlace mágico/MFA del dueño), RLS por organización, Storage privado y lectura de adjuntos desde la API.
- Copiloto con MiMo de producción: los tres recorridos (A11–A13), recibo con postcondiciones, retenciones liquidadas y conciliación de una retención `UNCERTAIN` (función `billing.holds.conciliate`, solo operador/dueño).
- Plan manual sin botón ni sondeo IA; plan IA con el popup.
- Suscripción/webhook/créditos en sandbox; cron de conciliación; idempotencia ante webhook duplicado.
- Respaldo y restauración de prueba.

## 6. Bloqueos de activación comercial (decisión del dueño)

- **Precios y cuotas**: los cupos vigentes (0/2000/6000/12000; prueba 500) son legado no proporcional. La política `proportional-v1` (Q = m × U) está preparada e **inactiva**; requiere tabla aprobada, términos versionados y migración comercial.
- **Fórmula de consumo**: se mantiene `legacy_route_v1` (costo fijo por ruta). `metered_cost_v1` (tokens × tarifa) es propuesta pendiente.
- **Grandfathering** de `founding_member`: diferencia registrada entre PRD y código; sin conciliar.
- **Proveedor IA futuro**: «DeepSeek Flash 4.1» solo mencionado; no configurado ni validado.
- No se crearon productos, precios, enlaces de pago ni suscripciones en Flow/Paddle.
