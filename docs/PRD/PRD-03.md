# PRD-03: GESTIÓN DE TENANCY, AUTENTICACIÓN, FACTURACIÓN Y BILLETERA DE CRÉDITOS (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.2 (Congelada y Bloqueada tras Auditoría Final)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 0 (Fundacional)  
**Bloquea a:** PRD-05 a PRD-17

---

## 1. Arquitectura de Autenticación y Control de Acceso

Dekopen implementa una capa de autenticación delegada en **Supabase Auth** con mecanismos de inicio de sesión sin contraseña (Magic Link) y autenticación multifactor (MFA/TOTP) obligatoria para el rol `OWNER`.

```
+---------------+      1. SignIn OTP       +----------------+
|  Usuario      | -----------------------> | Supabase Auth  |
|  (Navegador)  | <----------------------- | (Magic Link)   |
|               |      2. Email con Link   +----------------+
|               |                                  |
|               |      3. Bearer JWT verificado    v
|               | -----------------------> +----------------------+
|               | <----------------------- | Django API          |
+---------------+   Auth + tenancy propio  | /api/v1/auth/me/    |
                                           +----------------------+
```

### 1.1. Identidad, JWT y contexto RLS

- La identidad técnica proviene exclusivamente de un JWT Supabase verificado. Los
  claims mínimos son `sub`, `exp`, `iss`, `aud` y `role`; `aal` ausente equivale a
  `aal1`.
- El único rol técnico aceptado para usuarios de la aplicación es
  `role=authenticated`. Se rechazan `anon`, `service_role`, firma/issuer/audience
  inválidos, tokens expirados y `sub` ausente o no UUID.
- `SUPABASE_JWT_VERIFY_MODE` admite exactamente `jwks` y `auth_server`. `jwks` valida
  localmente contra `${SUPABASE_URL}/auth/v1/.well-known/jwks.json`, issuer
  `${SUPABASE_URL}/auth/v1`, audience `authenticated` y allowlist `ES256`, `RS256`,
  `EdDSA`. `auth_server` valida mediante `GET ${SUPABASE_URL}/auth/v1/user` con
  `apikey` y Bearer, exige HTTP 200 y comprueba `JWT.sub == returned_user.id`.
- `org_id` y el rol organizacional jamás proceden del JWT. Se obtienen exclusivamente
  desde una fila activa de `tenancy_memberships` para `user_id=JWT.sub`.
- Toda consulta autenticada a tablas con RLS ocurre dentro de `transaction.atomic()`;
  antes de la primera consulta se ejecutan `set_config('request.jwt.claims',
  <VERIFIED_CLAIMS_JSON>, true)` y `SET LOCAL ROLE authenticated`. El contexto es local
  a la transacción y no puede sobrevivir a commit/rollback ni filtrarse entre requests.
- La organización activa añade un filtro de aplicación centralizado
  `org_id=active_organization.id`; no sustituye a RLS ni autoriza service role.

### 1.2. Organización activa

Los endpoints tenant-bound aceptan `X-Organization-ID: <uuid>` y revalidan membership y
rol en cada request:

- cero memberships activas: `403 no_active_membership`;
- una membership activa sin header: selección automática;
- más de una activa sin header: `409 organization_selection_required`;
- header malformado: `400 invalid_organization_id`;
- UUID ajeno o membership inactiva: `403 organization_access_denied`.

El frontend usa `/select-organization` y persiste sólo el UUID seleccionado en
`localStorage["dekopen.active_org.<user_id>"]`. Nunca persiste el rol como autoridad.

### 1.3. MFA/TOTP para OWNER

La autoridad MFA es exclusivamente el claim verificado `aal`. El campo histórico
`tenancy_memberships.totp_enabled` es **NO AUTORITATIVO PARA AUTORIZACIÓN**.

Una membership activa `OWNER` exige `aal2` en todo endpoint autenticado tenant-bound.
Con `aal1` responde `403 mfa_required`. La regla se evalúa por organización activa; los
roles no OWNER pueden operar con `aal1`. Enrollment, challenge y verify se delegan
exclusivamente a Supabase Auth; Dekopen no genera ni valida TOTP.

### 1.4. Contrato de `GET /api/v1/auth/me/`

La respuesta vigente de SHOT-04 es:

```json
{
  "user": {"id": "<uuid>", "email": "user@example.com"},
  "aal": "aal1",
  "active_organization": {
    "id": "<uuid>",
    "name": "Taller",
    "role": "ESTIMATOR"
  },
  "memberships": [
    {
      "organization_id": "<uuid>",
      "organization_name": "Taller",
      "role": "ESTIMATOR"
    }
  ]
}
```

`active_organization` puede ser `null` únicamente durante selección requerida. El
endpoint no devuelve saldo, créditos, billing ni suscripciones; `saldo` se difiere al
shot de wallet/billing. Todos los errores usan
`{"error":{"code":"machine_code","detail":"human readable detail"}}` y los códigos
canónicos `authentication_required`, `invalid_token`, `invalid_organization_id`,
`no_active_membership`, `organization_access_denied`, `mfa_required` y
`organization_selection_required`.

### 1.5. Gate local de Magic Link y TOTP (SHOT-04)

El gate usa Supabase Auth real y el capturador local de email de Supabase CLI
(**Mailpit en CLI `2.116.0`**, resolución PD-04-14). No usa mocks de Auth ni correo
externo. Antes del E2E, `GET http://127.0.0.1:54324/readyz` debe devolver `200`.

La prueba crea usuario/membership locales, solicita Magic Link desde `/login`, busca el
destinatario único de la corrida mediante `/api/v1/messages`, recupera el body real
mediante `/api/v1/message/{ID}` y navega al link extraído. El ID y el token nunca se
hardcodean. Se exigen callback, sesión Supabase y Bearer real contra Django; el polling
es finito y falla si falta cualquier eslabón. El ciclo OWNER incluye enrollment TOTP
real, `aal2`, logout y un segundo Magic Link que exige verificar el factor existente.

La configuración pública de CLI puede conservar el nombre histórico `inbucket`; el
servicio runtime y la API canónicos de SHOT-04 son Mailpit. No se usa la antigua ruta
`/api/v1/mailbox/...` ni se cambia el pin de CLI para recuperar Inbucket.

---

## 2. Facturación y Pasarelas de Pago Multi-Región

- **Chile (CL):** **Flow.cl** (Suscripciones nativas con Webpay Plus, Servipag y Khipu). Moneda de cobro local CLP ajustada por tipo de cambio con buffer del 5% e IVA incluido.
- **Internacional (US/EU/Resto):** **Paddle** (Merchant of Record - MoR que gestiona automáticamente Sales Tax, VAT y facturación internacional sin carga impositiva para el taller). Moneda ancla oficial: **USD**.
- **LatAm Expansión (MX, CO, PE, AR):** MercadoPago (Fase 2+).

---

## 3. Planes de Suscripción Oficiales

| Parámetro | Trial | Starter | Profesional ⭐ | Business | Business 2x |
|---|---|---|---|---|---|
| **Mensual** | — | USD 39 | USD 69 | USD 129 | USD 149 |
| **Anual (billed annually)** | — | USD 35/mo | USD 59/mo | USD 99/mo | USD 129/mo |
| **Total anual** | — | USD 420 | USD 708 | USD 1.188 | USD 1.548 |
| **Usuarios Incluidos** | 1 | 2 | 3 | 5 | 5 |
| **Créditos IA / mes** | 500 (techo total trial) | 0 | 2.000 | 6.000 | 12.000 |
| **Motor 0.00 mm, 2D SVG, BOM, corte 1D, PDF/OT/Excel, pedido** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **OCR planos, compilador, comandos, plantillas PDF** | — | — | ✓ | ✓ | ✓ |
| **Certificado doble ciego (v1.5), Autopilot (v2), comparador, soporte prioritario** | — | — | — | ✓ | ✓ |
| **Diferenciador** | Prueba completa 7 días | El motor completo. Sin IA, por elección. | **MÁS POPULAR** | Todo el producto | Solo 2× créditos. Nada más. |

- **Trial:** 7 días sobre Profesional completo, sin tarjeta, techo duro de 500 créditos totales. Signup directo a Starter = 0 créditos. Al expirar el trial, downgrade automático a Starter (*el motor de cálculo nunca se bloquea*).
- **Usuario Extra:** USD 12/mes (USD 10/mes en ciclo anual), en todos los planes pagos.
- **Cláusula de Grandfathering Estándar:** Todo cambio futuro en precios de lista garantiza precio congelado por 12 meses para suscriptores activos.
- **Founding 50 (Excepción de Precio de por Vida):** Los primeros 50 suscriptores anuales (`founding_member = TRUE`) congelan su tarifa de por vida (`price_locked = TRUE`), protegida contra incrementos futuros de tarifa o reajustes por IPC. Respaldada en `tenancy_organizations.founding_member` y `subscriptions.founding_member`.

---

## 4. Billetera y Consumo de Créditos de IA (Medición Dinámica por Tokens Reales)

### 4.1. Algoritmo de Cálculo y Débito Dinámico por Tokens
El sistema **NO cobra tarifas fijas hardcodeadas**. Cada llamada a una herramienta de IA (Tools T1 a T12) se debita en tiempo real según los **tokens reales consumidos** devueltos por el proveedor (`tokens_in` y `tokens_out`):

1. **Cálculo del Costo API Real (USD):**
   $$\text{Costo API} = (\text{tokens\_in} \times \text{precio\_in}) + (\text{tokens\_out} \times \text{precio\_out})$$
2. **Conversión a Créditos Dekopen (con Margen 2x de Ganancia):**
   $$\text{Créditos a Debitar} = \lceil \text{Costo API en USD} \times 200 \rceil$$
   *(Equivalencia: \$1 USD de costo API = 100 créditos base. Con margen comercial 2x = 200 créditos por cada \$1 USD de costo API).*
3. **Saldo Cero:** Al agotarse los créditos, las funciones de IA se pausan. **El motor de cálculo `/engine`, diseñador 2D, cotizador manual, corte 1D y exportación de PDFs siguen 100% operativos** (*retención, no castigo*).

### 4.2. Packs de Recarga de Créditos (Margen Comercial 2x)
| Pack | Precio al Cliente | Costo API Real | Créditos Incluidos |
|---|---|---|---|
| **Top-up 1.000** | USD 15 | ~$5 USD | 1.000 créditos |
| **Top-up 3.000** | USD 40 | ~$15 USD | 3.000 créditos |
| **Top-up 7.500** | USD 90 | ~$37.5 USD | 7.500 créditos |

### 4.3. Tabla de Consumo Promedio Estimado (Referencial para Marketing)
*Nota técnica: Los siguientes valores son promedios referenciales de consumo típico para comunicación al cliente. El débito en base de datos (`credit_ledger`) siempre se calcula de forma dinámica según los tokens reales.*

| Tool ID | Función | Operación Realizada | Consumo Promedio Estimado | Modelo Asignado |
|---|---|---|---|---|
| `T1` | `extract_positions(file)` | OCR multimodal de plano PDF y extracción de vanos | **~10 créditos** / plano | Dekopen Vision CAD™ (Gemini 3.7) |
| `T2` | `propose_window_command(text)` | Interpretación NLP de instrucción de diseño geométrico | **~4 créditos** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T3` | `apply_pricing_command(mode,params)` | Cálculo y preview de ajuste comercial por comando | **~3 créditos** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T4` | `missing_questions(ctx)` | Diagnóstico de variables faltantes para cotización | **~2 créditos** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T5` | `explain_item(bom_line)` | Explicación técnica de taller de una partida de material | **~1 crédito** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T6` | `compile_catalog(file)` | Compilación completa de catálogo técnico desde PDF | **~25 + 2 cr / pág** | Dekopen Matrix Reader™ (Kimi k3) |
| `T7` | `propose_compatibility_edge(a,b)` | Sugerencia de compatibilidad perfil-herraje | **~2 créditos** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T8` | `cross_verify_certificate(pos)` | Doble verificación cruzada con modelo alternativo | **~50 créditos** | Doble Verificador (Luna vs Sol) |
| `T9` | `draft_autopilot(request)` | Generación integral de cotización borrador desasistida | **~30 + 2 cr / pág** | Pipeline completo multimodal |
| `T10` | `compare_plans(v1,v2)` | Análisis de diferencias entre dos versiones de plano | **~8 créditos** | Dekopen Vision CAD™ (Gemini 3.7) |
| `T11` | `margin_alert(ctx)` | Detección preventiva de márgenes comerciales negativos | **~1 crédito** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T12` | `forecast_materials(h)` | Pronóstico de compra de barras según histórico | **~5 créditos** | Dekopen Neural Core™ (GPT 5.6 Luna) |
