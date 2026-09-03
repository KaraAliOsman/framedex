# Plan de Implementación — SHOT-04: Auth, tenancy, API y shell ADOBE dual

## 1. Identificación, baseline y estado de fase

- **Shot:** `SHOT-04` — Supabase Auth, tenancy, API skeleton DRF/JWT/OpenAPI,
  PostHog base y shell de aplicación ADOBE dual.
- **Fase actual:** implementación y gauntlet local verificados; PD-01…PD-14 resueltas.
  Pendiente publicación/CI del PR protegido y aprobación humana de merge (§25).
- **Branch:** `shot-04`.
- **Base canónica verificada:**
  `main@040d818c22ffd4d1f86105242025e50b606d1e8a`.
- **Estado inicial del repositorio:** `main` limpio, sincronizado con `origin/main`; la
  branch fue creada directamente desde el SHA anterior.
- **Upstream cerrado:** SHOT-02 (DDL/RLS) y SHOT-03 (engine G1–G4) están cerrados.
- **Stop condition:** el alcance aprobado debe superar
  `python scripts/check_dod.py all` con exit code real `0` y los cuatro required checks.

Este archivo es la memoria persistente de SHOT-04. Las doce decisiones identificadas en
FASE 1 quedaron resueltas explícitamente en §19; no queda un
`[PENDIENTE-DECISIÓN]` abierto al iniciar la construcción.

## 2. Autoridad normativa leída

Se leyó, en el orden exigido:

1. `AGENTS.md`.
2. `docs/CONSTITUTION.md` v1.2 MASTER.
3. `docs/PRD/PLAN_SHOTS.md`, fila SHOT-04.
4. `docs/PRD/PRD-03.md` §1.
5. `docs/PRD/PRD-19.md` §3.
6. `docs/PRD/PRD-FRONTEND-APIS-COMPONENTS.md`.
7. Interfaces reales de `backend/`, `frontend/` y `engine/`.
8. Contratos y schema de SHOT-02/03: migraciones, RLS, pruebas pgTAP,
   `PLAN_SHOT-02.md`, `PLAN_SHOT-03.md` y la interfaz pública del engine.

También se inspeccionaron, únicamente donde una regla vigente los referencia:

- `docs/PRD/PRD-00.md` §2 y §6: precedencia de diseño y lista cerrada de dependencias.
- `docs/PRD/SCREENS_SPECIFICATION_S01_S28.md`: rutas/roles publicados.
- `docs/PRD/STACK_APLICACIONES_Y_SERVICIOS.md`: asignación de servicios por shot.
- `docs/PRD/PRD-DESIGN-SYSTEM-ADOBE.md`: el archivo señalado por PRD-00 como
  autoridad visual.
- `.env.example`, `supabase/config.toml`, `.github/workflows/ci.yml`, `Makefile` y
  `scripts/check_dod.py`.

La documentación oficial de Supabase y drf-spectacular se consultó sólo para comprobar
capacidades técnicas actuales (JWKS, claim `aal`, Mailpit y generación de schema). No
se usa como autoridad para completar decisiones de negocio ausentes.

No se usó `docs/archive/` ni los duplicados históricos fuera de `docs/PRD/` como fuente
funcional.

## 3. Gate canónico y objetivo exacto

La fila de SHOT-04 exige:

1. Magic Link E2E.
2. TOTP obligatorio para `OWNER`.
3. OpenAPI → cliente TypeScript autogenerado en CI.
4. PostHog capturando eventos base.
5. Shell navegable con modo claro/oscuro ADOBE dual.

La entrega se limita a la infraestructura mínima de autenticación, tenancy y API que
demuestre esos cinco puntos. No autoriza lógica de proyectos, canvas, pricing, billing,
documentos, IA ni nuevas fórmulas.

## 4. Estado real de las interfaces consumidas en el baseline

| Superficie            | Estado verificado                                                                                                      | Consecuencia para SHOT-04                                                                                                                            |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Django                | Bootstrap mínimo; `INSTALLED_APPS=[]`, `MIDDLEWARE=[]`, sin configuración DB ni DRF                                    | SHOT-04 debe crear el primer límite HTTP real sin duplicar el DDL Supabase.                                                                          |
| Dependencias backend  | Django, DRF y drf-spectacular ya declarados                                                                            | Falta un mecanismo permitido para validar criptográficamente JWT Supabase; `psycopg`, CORS y `posthog` están en la lista cerrada pero no instalados. |
| Frontend              | React/Vite/Tailwind mínimo; `App` vacío; sin router, Auth SDK, PostHog SDK ni DOM test environment                     | Magic Link, sesión, navegación y telemetría no tienen interfaz existente que extender.                                                               |
| Dependencias frontend | Sólo React, ReactDOM, Vite, Tailwind, Vitest, ESLint y Prettier                                                        | Los paquetes normalmente usados para Supabase, cliente OpenAPI, PostHog y E2E no aparecen en PRD-00 §6.                                              |
| Supabase local        | Auth habilitado; `site_url=http://127.0.0.1:3000`; frontend real usa Vite; no hay contrato de callback ni fixture Auth | El Magic Link E2E no es reproducible todavía.                                                                                                        |
| Tenancy DB            | `tenancy_memberships(user_id, org_id, role, totp_enabled, is_active)` permite varias memberships por usuario           | No existe una organización activa singular ni una regla de selección.                                                                                |
| RLS                   | `private.current_user_org_ids()` deriva todas las organizaciones activas desde `auth.uid()`                            | Django debe preservar claims/rol en cada consulta o usar una vía que aplique RLS; consultar como service role y filtrar manualmente queda prohibido. |
| Engine                | `calculate_geometry(root, params, is_foiled=False) -> EngineResult`; requiere `SystemParams` y artículos efectivos     | El request HTTP publicado sólo aporta `system_id`; necesita un adapter/loader externo al engine o un stub definido expresamente.                     |
| CI                    | Cuatro jobs protegidos: lint/typecheck, tests, frontend build y database gate                                          | SHOT-04 debe ampliar estos jobs sin eliminar ni volver opcional ningún gate.                                                                         |

## 5. Alcance autorizado

### 5.1. Backend

- Activar DRF y drf-spectacular en el monolito modular.
- Implementar autenticación Bearer para JWT emitidos por Supabase, después de resolver
  algoritmo, claves, claims y dependencia en PD-04-01.
- Derivar `user_id` exclusivamente del claim verificado `sub`.
- Resolver `org_id` y rol exclusivamente desde una membership activa en
  `public.tenancy_memberships`; nunca confiar en `user_metadata` ni en un rol de
  organización aportado directamente por el cliente.
- Crear el contrato `/auth/me/` en la ruta exacta que se apruebe.
- Crear el límite HTTP de `/api/v1/engine/calculate/` conforme a la resolución de
  PD-04-07, sin modificar `/engine`.
- Publicar y validar un schema OpenAPI mediante drf-spectacular.
- La telemetría de PD-09 se implementa exclusivamente en frontend (§14); no se crea un
  módulo PostHog backend.
- Aplicar controles de seguridad de aplicación realmente pertenecientes al shot una vez
  resuelta PD-04-11.

### 5.2. Frontend

- Implementar S01 `/login` y callback Magic Link mínimo según PD-04-02/PD-04-05.
- Mantener una sesión Supabase y adjuntar `Authorization: Bearer <JWT>` a la API.
- Consumir exclusivamente el cliente TypeScript generado para endpoints tipados.
- Implementar un contexto auth/tenancy que represente los estados aprobados: cargando,
  anónimo, autenticado, sin membership, MFA pendiente y listo.
- Implementar shell navegable mínimo, sin contenido funcional de pantallas futuras.
- Implementar selector claro/oscuro únicamente desde tokens canónicos resueltos.
- Capturar sólo los eventos PostHog expresamente aprobados.

### 5.3. Harness y CI

- Mantener los cuatro jobs actuales con sus nombres exactos.
- Hacer fail-closed la generación/validación OpenAPI y el cliente TypeScript.
- Ejecutar el Magic Link E2E contra una stack Supabase local aislada, si ésa es la
  semántica aprobada.
- Añadir pruebas de autenticación, autorización, tenancy, MFA, telemetría y shell.
- Actualizar el checker de SHOT-04 sin debilitar los gates de SHOT-01–03.

## 6. Fuera de alcance / PROHIBIDO

- Modificar `/engine`, sus fórmulas, G-cases, BOM o Golden snapshots.
- Implementar canvas de SHOT-05 o cualquier geometría/hardware de SHOT-06.
- Implementar proyectos/versiones, onboarding persistente o CRUD de SHOT-10.
- Implementar Inspector, pricing, costos, facturación, Flow, Paddle, wallet o créditos.
- Implementar documentos, Storage, IA, Intercom, Jam.dev o Resend por asociación de
  roadmap.
- Implementar Cloudflare, TLS/WAF, Redis, despliegue Railway o infraestructura de
  producción. El gate no los exige y la orden del owner prohíbe inferirlos.
- Implementar rate limiting distribuido; PRD-19 lo dibuja sobre Redis, pero el owner lo
  excluyó de inferencias de SHOT-04.
- Añadir tablas, migraciones, policies RLS, triggers o cambios al seed sin una expansión
  explícita del alcance.
- Usar service role en el navegador, versionar secretos o aceptar JWT sin verificar.
- Derivar `org_id` o rol desde datos no validados del request.
- Crear manualmente un cliente TypeScript que se presente como “autogenerado”.
- Simular un Magic Link sólo con mocks y presentarlo como E2E.
- Inventar nombres de eventos PostHog, respuesta de endpoints, rutas o tokens visuales.
- Usar contenido de `docs/archive/` o del archivo ADOBE duplicado no canónico para
  resolver silenciosamente la contradicción visual.

## 7. Arquitectura aprobada

```text
Browser
  ├─ Supabase Auth adapter ── Magic Link / callback / MFA ── Supabase Auth
  ├─ AuthSessionProvider ── verified access token
  ├─ TenantContext ── X-Organization-ID validado
  └─ GeneratedApiClient ── Authorization Bearer + X-Organization-ID
                                      │
                                      ▼
                            Django / DRF monolith
                              ├─ SupabaseJWTAuthentication
                              ├─ TenantContextResolver
                              ├─ OwnerMFA permission
                              ├─ GET auth/me
                              ├─ POST engine/calculate
                              ├─ OpenAPI schema
                              └─ TelemetryPort
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
          RLS transaction-local adapter            /engine package
          (claims + role authenticated)            (sin cambios)
                    │
                    ▼
          PostgreSQL/Supabase + RLS
```

Principios no condicionados:

- La identidad primaria es `sub` de un JWT válido.
- El rol `authenticated` del JWT es rol PostgreSQL, no rol del taller.
- El rol del taller sale de `tenancy_memberships.role`.
- `SUPERADMIN` permanece diferido a SHOT-20.
- El backend nunca toma `org_id`, `role` o `totp_enabled` del cuerpo del request.
- El engine permanece puro y recibe objetos tipados ya cargados por el adapter.
- Telemetría es best-effort: un fallo de PostHog no modifica el resultado ni la
  autorización de una petición.

## 8. Flujo JWT → Django → tenancy → RLS

### 8.1. Hechos canónicos

1. El navegador obtiene un access token de Supabase Auth mediante Magic Link.
2. La API recibe `Authorization: Bearer <Supabase_JWT>`.
3. Django debe verificar firma y claims antes de construir usuario/contexto.
4. `sub` se convierte en `user_id` únicamente después de la verificación.
5. Las memberships activas se buscan por `user_id`.
6. El `org_id` seleccionado debe pertenecer a una membership activa del usuario.
7. El rol efectivo se lee de esa misma fila.
8. Las consultas de negocio deben seguir sujetas a las policies de SHOT-02.

### 8.2. Claims que valida el verificador

- firma con algoritmo permitido explícitamente;
- `iss` exacto del proyecto/stack autorizada;
- expiración `exp`;
- `sub` UUID válido;
- `role == authenticated` para sesiones de usuario;
- `aud == authenticated`;
- rechazo de tokens `anon`, `service_role`, algoritmo `none`, claves desconocidas o
  claims ausentes.

### 8.3. Propagación RLS aprobada

Cada request autenticado que consulte tablas protegidas usa `transaction.atomic()` y,
antes de la primera query, ejecuta `set_config('request.jwt.claims',
<VERIFIED_CLAIMS_JSON>, true)` y `SET LOCAL ROLE authenticated`. Los claims proceden sólo
del token ya verificado. El contexto es transaction-local y se prueba que no sobrevive a
commit/rollback ni cruza requests/conexiones. Todas las queries tenant-bound añaden el
filtro central `org_id=active_organization.id`, incluso si RLS permite varias memberships.
Service role y bypass RLS quedan prohibidos para requests normales.

## 9. Contrato de usuario sin membership y múltiples memberships

La organización activa no vive en el JWT. Los endpoints tenant-bound aceptan
`X-Organization-ID`; el backend valida el UUID contra una membership activa del `sub`.
Cero memberships responde `403 no_active_membership`; una se autoselecciona; varias sin
header responden `409 organization_selection_required`; header malformado responde
`400 invalid_organization_id`; organización ajena/inactiva responde
`403 organization_access_denied`. El frontend persiste sólo el ID en
`localStorage["dekopen.active_org.<user_id>"]`, lo borra si deja de ser válido y nunca
persiste el rol como autoridad. Onboarding permanece diferido.

## 10. TOTP obligatorio para OWNER

Supabase representa el nivel de garantía en el claim verificado `aal`: Magic Link produce
`aal1` y una sesión con segundo factor verificado produce `aal2`. `aal` ausente equivale
a `aal1`. `tenancy_memberships.totp_enabled` es histórico y no autoriza acceso.

Después de PD-04-04, la solución deberá probar al menos:

1. OWNER con sesión `aal1` no accede a recursos protegidos como OWNER.
2. OWNER con TOTP verificado y JWT `aal2` sí accede.
3. ESTIMATOR/WORKSHOP_MANAGER/INSTALLER siguen la política aprobada sin heredar por error
   la obligación OWNER.
4. Un claim `aal2` falsificado o sin firma válida es rechazado.
5. El enforcement ocurre en backend; una redirección frontend no cuenta como control.
6. En usuario multi-org, la obligación se evalúa contra el rol de la membership activa,
   no contra otra fila elegida implícitamente.

El frontend usa las APIs MFA de Supabase para listar/enrolar TOTP, challenge y verify;
Dekopen nunca genera ni valida códigos. Tras verify obtiene/refresca una sesión `aal2` y
repite `/auth/me/`. Un OWNER en `aal1` recibe el envelope canónico `403 mfa_required`.

## 11. Contratos backend congelados

| Superficie                  | Contrato SHOT-04                                                                                                                                          |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/api/v1/auth/me/`          | `GET`; Bearer obligatorio; header org opcional durante bootstrap; devuelve `user`, `aal`, `active_organization` y memberships propias. Sin saldo/billing. |
| `/api/v1/engine/calculate/` | `POST`; adapter funcional DB→engine; auth, org activa y MFA OWNER; responde sólo BOM actual.                                                              |
| OpenAPI                     | `backend/openapi.yaml`, generado/validado por drf-spectacular; Orval `fetch` genera `frontend/src/api/generated/`.                                        |
| Auth errors                 | Envelope único `{"error":{"code":"machine_code","detail":"human readable detail"}}` con los siete códigos aprobados.                                      |

No se expondrán endpoints de proyectos, billing, wallet, AI, orders o storage aunque
aparezcan en el inventario REST de PRD-FRONTEND.

## 12. Límite del endpoint `/engine/calculate/`

La interfaz HTTP y la interfaz real de SHOT-03 no coinciden directamente:

```text
HTTP: system_id + nominal dimensions + color + parametric_tree
Engine: ParametricNode + SystemParams + is_foiled
```

El adapter funcional implementa, fuera de `/engine`:

1. autorizar `system_id` mediante RLS;
2. cargar `profile_systems`, artículos efectivos y matriz de junquillos;
3. mapear columnas/fallbacks a `SystemParams` con `Decimal`;
4. validar que las dimensiones top-level coincidan con la raíz del árbol;
5. ejecutar `WHITE` como color normativamente especificado; otro color válido pero sin
   mapping canónico es contrato diferido y responde `422 unsupported_engine_contract`;
6. llamar `calculate_geometry` y serializar `EngineResult` sin recalcular.

La contradicción de PRD-FRONTEND §1.1 queda corregida: `calculation_hash` e `inspector`
no forman parte de la respuesta SHOT-04 y permanecen diferidos a SHOT-06/07.

## 13. Flujo OpenAPI → cliente TypeScript

La parte definida es:

```text
DRF serializers/views
       │
       ▼
manage.py spectacular --file backend/openapi.yaml --validate
       │
       ▼
orval@8.27.0 (cliente fetch)
       │
       ▼
frontend/src/api/generated/
       │
       ▼
CI regenera y falla si git diff no está limpio
```

El artefacto generado se commitea y nunca se edita manualmente. Un mutator manual fuera
de `generated/` inyecta Bearer y `X-Organization-ID`. CI regenera schema y cliente y exige
diff vacío en ambos paths.

## 14. Estrategia PostHog

El diseño será un puerto pequeño e inyectable:

- configuración exclusivamente por entorno;
- implementación no-op cuando la clave no exista en desarrollo/test;
- transporte falso en tests, sin red ni secretos;
- `distinct_id` derivado de `user_id` sólo tras autenticar;
- propiedades de tenancy limitadas a identificadores/rol aprobados;
- prohibición de payloads JWT, email, contenido de proyectos o datos de cliente;
- errores de captura aislados del flujo principal.

La implementación frontend usa `posthog-js@1.422.5`, es no-op sin key, desactiva
autocapture/pageview/session recording y emite sólo: `auth_magic_link_requested`,
`auth_signed_in`, `organization_selected`, `mfa_enrollment_started`, `mfa_verified`,
`shell_route_viewed` y `theme_changed`. Sólo admite `role`, `aal`, `route_name` y `theme`;
la lista de PII/secrets de PD-09 queda prohibida. Tests usan facade falsa y cero red.

## 15. Shell, navegación y tema

Las rutas funcionales son `/login`, `/auth/callback`, `/auth/mfa`,
`/select-organization` y `/dashboard`. El shell permite únicamente placeholders
de `/projects`, `/catalogs/systems` y `/settings/general`. `/` redirige a `/login` sin
sesión y a `/dashboard` con contexto listo. No existe namespace `/app`.

La implementación aprobada es:

- límite público de login/callback;
- guard de sesión y MFA;
- layout autenticado con navegación sólo a destinos autorizados como placeholders;
- indicador de organización/rol basado en `/auth/me/`;
- switch accesible de un clic entre Light Studio y Dark Graphite;
- tokens semánticos centralizados; componentes sólo consumen `var(--theme-*)`;
- preferencia y default conforme a la decisión del owner;
- test de navegación, foco, etiqueta accesible y persistencia aprobada.

La autoridad única ya normalizada es `docs/PRD/PRD-DESIGN-SYSTEM-ADOBE.md`. SHOT-04
implementa sólo §§1–3. El contenido móvil/OCR/QR se conserva en
`docs/PRD/PRD-WEB-MOBILE-ESSENTIAL.md`; la copia duplicada fuera de `docs/PRD/` se elimina.
El tema usa `data-theme=light|dark`, `dekopen.theme` y, sin preferencia persistida,
`prefers-color-scheme`.

## 16. Archivos de FASE 2 tras las resoluciones aprobadas

Este inventario materializa los límites aprobados en PD-01…PD-14. No modifica esas
decisiones ni añade módulos futuros; los nombres concretos reflejan el working tree.

### 16.1. Crear

| Archivo/grupo                                      | Propósito                                                                                 | Gate                         |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------- | ---------------------------- |
| `backend/authentication/`                          | Clase DRF de JWT Supabase, contexto tenancy, permisos MFA, serializers/views/URLs de auth | JWT, `/auth/me/`, TOTP OWNER |
| `backend/engine_api/`                              | Serializer y adapter HTTP alrededor de la interfaz pública de SHOT-03                     | API skeleton y OpenAPI       |
| `backend/tests/test_jwt_authentication.py`         | JWT válido/inválido, firma, claims y algoritmos                                           | Seguridad auth               |
| `backend/tests/test_tenancy.py`                    | Memberships, selección activa y matriz OWNER/non-OWNER con AAL                            | Tenancy y TOTP OWNER         |
| `backend/tests/test_rls_context.py`               | Orden de propagación de claims verificados y rol transaction-local                       | RLS                          |
| `backend/tests/integration/test_rls_context_integration.py` | Auth/JWT/PostgreSQL reales, aislamiento, active-org, no-leak y G1/G4                | RLS real y adapter           |
| `backend/tests/factories.py`                      | Fixtures unitarias sin secretos reales ni nueva autoridad de fórmulas                     | Tests backend                |
| `backend/tests/test_auth_me.py`                    | Schema y autorización exactos del endpoint                                                | `/auth/me/`                  |
| `backend/tests/test_engine_api.py`                 | Auth, serializer, límites del stub/adapter y cero recálculo                               | `/engine/calculate/`         |
| `backend/tests/test_openapi.py`                    | Paths, security scheme y cero warnings                                                    | OpenAPI                      |
| `backend/tests/test_gate_harness.py`              | Rechazo de drift, herramientas ausentes, comandos fallidos y Mailpit no saludable         | Checker fail-closed          |
| `backend/openapi.yaml`                            | Schema generado y validado con fail-on-warn                                              | OpenAPI                      |
| `frontend/tests/e2e/auth.spec.ts` | Flujo real contra Auth local/Mailpit aprobado por PD-04-14                          | Magic Link E2E               |
| `frontend/tests/e2e/support/` y `tests/contracts/mailpit.test.ts` | Entorno validado, extracción real de correo y pruebas negativas de Mailpit       | E2E fail-closed              |
| `frontend/src/auth/`                               | Adapter Supabase, sesión, callback y auth/tenancy context                                 | Magic Link y guards          |
| `frontend/src/api/apiMutator.ts` y su test         | Bearer actual y `X-Organization-ID`, fuera del cliente generado                          | Auth y OpenAPI → TS          |
| `frontend/src/api/generated/`                      | Cliente generado desde OpenAPI; nunca editado manualmente                                 | OpenAPI → TS                 |
| `frontend/src/app/`                                | Shell, router/navegación mínima y guards                                                  | Shell navegable              |
| `frontend/src/theme/` y `frontend/src/styles/tokens.css` | Theme provider/toggle y única fuente de tokens                                      | Claro/oscuro                 |
| `frontend/src/i18n/es-CL.ts`                       | Diccionario local del shell y auth, conforme a Regla 14                                  | Shell accesible              |
| `frontend/src/telemetry/`                          | Adapter PostHog del canal aprobado                                                        | Captura base                 |
| `frontend/src/**/*.test.tsx`                       | Login, callback, guards, navegación y tema                                                | Gate frontend                |
| `frontend/orval.config.ts`                        | Generación fetch reproducible y mutator externo                                          | Drift CI                     |
| `frontend/playwright.config.ts`                   | Chromium, ejecución serial real sin retries ni mocks                                     | E2E                          |
| `scripts/check_generated_api.py`                  | Regeneración schema/cliente y comparación byte a byte                                     | Drift CI                     |
| `scripts/local_gates.py` y `scripts/check_auth_e2e.py` | Stack limpia, servidores E2E, teardown, Mailpit y PostgreSQL 16                        | Gates reales                 |

### 16.2. Modificar

| Archivo                                         | Cambio limitado                                                   | Gate                      |
| ----------------------------------------------- | ----------------------------------------------------------------- | ------------------------- |
| `backend/config/settings.py`                    | Apps, DRF, spectacular, DB/auth/CORS/security/env                 | API/Auth/OpenAPI          |
| `backend/config/urls.py`                        | Sólo rutas SHOT-04 y schema aprobado                              | API navegable             |
| `backend/requirements.txt`                      | Sólo dependencias de la lista cerrada más excepciones aprobadas   | Runtime reproducible      |
| `frontend/package.json` / lock                  | Scripts y sólo paquetes expresamente autorizados                  | Auth/client/tests/PostHog |
| `frontend/src/App.tsx`, `main.tsx`, `index.css` | Componer providers, shell y tokens aprobados                      | Shell dual                |
| `frontend/src/react-shim.d.ts`                  | Retirar/extender según decisión de typings React                  | Typecheck                 |
| `frontend/eslint.config.js`, `tsconfig.json`, `vite.config.ts`, `src/test/setup.ts` | ESLint JS más TypeScript estricto, DOM y contratos/E2E tipados | Tooling y tests |
| `.gitignore`, `frontend/.prettierignore`         | Excluir reportes/trazas E2E y artefactos de ejecución               | Seguridad y diff limpio   |
| `pyproject.toml`                               | Marker RLS y rutas de imports idénticas con pytest/module         | Tests reproducibles       |
| `backend/tests/test_bootstrap.py`, `frontend/src/App.test.tsx` | Reemplazar sólo expectativas del scaffold por contratos implementados | Regresión |
| `supabase/config.toml`                          | Callback, email local y MFA estrictamente necesarios para E2E     | Magic Link/TOTP           |
| `.env.example`                                  | Variables públicas/privadas separadas, sin valores reales         | Seguridad/configuración   |
| `.github/workflows/ci.yml`                      | Generación OpenAPI→TS y E2E dentro de los cuatro jobs             | Gate CI                   |
| `scripts/check_dod.py`                          | Paths/contratos SHOT-04 fail-closed, sin rebajar checks heredados | Gauntlet                  |
| `docs/plans/PLAN_SHOT-04.md`                    | Resoluciones y evidencia real                                     | Memoria persistente       |
| `docs/PRD/PRD-00.md`, `PRD-03.md`, `PRD-19.md`, `PRD-FRONTEND-APIS-COMPONENTS.md` | Formalizar exclusivamente las PD aprobadas | Regla 0 |
| `docs/PRD/PRD-DESIGN-SYSTEM-ADOBE.md`, `PRD-WEB-MOBILE-ESSENTIAL.md`, antigua copia raíz | Normalización aprobada con conservación íntegra de cuerpos | Autoridad ADOBE única |

No se prevé modificar DDL, RLS, seed, migraciones, `/engine` ni snapshots.

## 17. Estrategia de pruebas y seguridad

### 17.1. Unitarias

- Parser Bearer: ausente, formato inválido y tokens múltiples.
- Verificador JWT: firma, algoritmo, `iss`, `exp`, `sub`, `role`, `aal` y key id.
- Resolver tenancy: membership activa/inactiva, org ajena y casos cero/uno/múltiples.
- Permiso OWNER MFA: matriz rol × AAL.
- `/auth/me/`: respuesta exacta y ausencia de datos de otro tenant.
- Engine adapter: valida Decimal/string, no modifica `/engine`, no inventa hash/inspector.
- Telemetría: evento exacto, propiedades permitidas, no-op y fallo del transporte.
- Theme reducer/provider: alternancia y persistencia conforme a contrato.

### 17.2. Integración

- PostgreSQL/Supabase real: Tenant A no resuelve membership/org de Tenant B desde Django.
- RLS: una consulta emitida por el adapter no puede ver filas ajenas aun manipulando el
  selector de organización.
- Auth local: JWT real emitido por Supabase aceptado; token alterado/expirado rechazado.
- OpenAPI: comando con `--validate --fail-on-warn`, security scheme Bearer y paths exactos.

### 17.3. E2E

El flujo local aprobado será:

1. levantar Supabase limpio;
2. solicitar Magic Link a Auth real;
3. obtener el mensaje desde Mailpit local, sin correo ni secretos externos;
4. consumir el enlace/token una sola vez;
5. obtener un access token firmado por la stack local;
6. invocar Django con ese Bearer;
7. demostrar el estado de membership/MFA aprobado;
8. comprobar que un token manipulado o un segundo uso no produce sesión válida;
9. ejecutar en navegador real con `@playwright/test@1.62.1` el ciclo OWNER aal1→TOTP→aal2
   y el challenge del factor existente tras un nuevo Magic Link.

### 17.4. Pruebas anti-verifier-theater

- Cambiar el `sub` por Tenant B debe romper la expectativa A.
- Cambiar `aal2` a `aal1` debe bloquear OWNER.
- Cambiar un target/path OpenAPI debe producir diff del cliente y fallar CI.
- Eliminar una captura PostHog esperada debe fallar el test del adapter.
- Eliminar uno de los dos temas o el control de navegación debe fallar Vitest/E2E.
- Ninguna prueba E2E puede aprobar si Supabase Auth/Mailpit fue omitido.

## 18. Cambios esperados de CI y trazabilidad gate → evidencia

Se conservarán los cuatro jobs protegidos; no se propone un quinto required context.

| Gate                 | Evidencia/test verificable                                                                  | Job previsto                         |
| -------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------ |
| Magic Link E2E       | Playwright contra Supabase Auth + Mailpit + Django, sin mocks ni tokens hardcodeados       | Test Suite con stack real            |
| TOTP OWNER           | Tests AAL1 rechazado/AAL2 aceptado con JWT válido y rol DB OWNER                            | Test Suite + integración Auth        |
| OpenAPI → TS         | `spectacular --validate --fail-on-warn`; regeneración; `git diff --exit-code` del artefacto | Lint & Typecheck                     |
| PostHog base         | Tests de eventos/taxonomía aprobados con fake transport; cero red                           | Test Suite                           |
| Shell navegable      | Tests de rutas/guards + tema Light/Dark + build de producción                               | Test Suite + Frontend Build          |
| RLS/tenancy heredado | Tenant A≠Tenant B desde límite Django y pgTAP existente                                     | Database Gate                        |
| DoD global           | `python scripts/check_dod.py all` exit code `0`                                             | Todos los jobs según responsabilidad |

Los cuatro nombres protegidos permanecen exactamente:

- `Lint & Typecheck`
- `Test Suite`
- `Frontend Build`
- `Database Gate`

## 19. Resoluciones canónicas PD-04-01…PD-04-12

1. **JWT:** `SupabaseJWTAuthentication`; `SUPABASE_JWT_VERIFY_MODE=jwks|auth_server`;
   claims mínimos `sub/exp/iss/aud/role`, `aal` ausente=`aal1`; sólo rol
   `authenticated`; JWKS con `ES256/RS256/EdDSA` o validación real `/auth/v1/user`.
   Dependencias: `PyJWT[crypto]==2.13.0`, `cryptography==50.0.1`, `httpx==0.28.1`.
2. **Supabase SPA:** `@supabase/supabase-js@2.112.4`, cliente único con refresh,
   persistencia y detección URL; `signInWithOtp({shouldCreateUser:false})`; callback
   `<frontend-origin>/auth/callback`; ningún token duplicado en otro store.
3. **Active org:** header `X-Organization-ID`, membership activa revalidada en cada
   request y matriz exacta 400/403/409 de §9; sólo ID persistido en localStorage.
4. **OWNER MFA:** autoridad exclusiva `JWT.aal`; OWNER tenant-bound exige `aal2`;
   `totp_enabled` no autoritativo; enrollment/challenge/verify sólo con Supabase MFA.
5. **E2E (actualizada por PD-04-14):** Supabase CLI `2.116.0` real y su capturador
   local de Auth email, Mailpit en `54324`; health `/readyz=200`, consulta
   `/api/v1/messages`, destinatario único, ID obtenido de la API y body real mediante
   `/api/v1/message/{ID}`. Playwright exige click/callback/sesión/Bearer reales,
   `/auth/me/` y ciclo TOTP OWNER nuevo/existente. Polling finito y fail-closed.
6. **Auth me:** `GET /api/v1/auth/me/`, schema exacto de PRD-03 §1.4, sin saldo/billing,
   envelope y códigos de error canónicos.
7. **Engine API:** `POST /api/v1/engine/calculate/`, adapter fino DB→`SystemParams`→engine
   puro; salida sólo `profile_cuts/reinforcements/glasses/hardware_items`; 400/404/422
   canónicos; sin hash, Inspector, pricing, BFD ni resolución de hardware.
8. **OpenAPI/TS:** `backend/openapi.yaml`; drf-spectacular; `orval@8.27.0` fetch a
   `frontend/src/api/generated/`; mutator manual externo; regeneración y diff fail-closed.
9. **PostHog:** `posthog-js@1.422.5`, no-op sin key, autocapture/pageview/recording off;
   siete eventos y cuatro propiedades de allowlist definidos en §14; cero PII/secrets.
10. **ADOBE:** autoridad única `docs/PRD/PRD-DESIGN-SYSTEM-ADOBE.md`; móvil/OCR/QR se
    conserva como `PRD-WEB-MOBILE-ESSENTIAL.md`; SHOT-04 implementa sólo §§1–3 en tokens
    CSS y theme persistido/system preference.
11. **RLS/CORS:** `transaction.atomic()` + claims verificados transaction-local +
    `SET LOCAL ROLE authenticated`; filtro active-org central; tests de no-leak;
    `django-cors-headers==4.9.0`, allowlist de orígenes y headers, sin credentials.
12. **Shell/tooling:** rutas exactas de §15 y placeholders sin funcionalidad; pins runtime
    y test exactos registrados en PRD-00 §6; cuatro required contexts sin quinto job.

No queda un `[PENDIENTE-DECISIÓN]` abierto después de esta resolución.

## 20. Riesgos y mitigaciones

| Riesgo                                | Consecuencia                         | Mitigación exigida                                         |
| ------------------------------------- | ------------------------------------ | ---------------------------------------------------------- |
| Aceptar JWT sólo decodificado         | Suplantación total                   | Verificación criptográfica y matriz adversarial de claims. |
| Consultar DB como service role        | Bypass real de RLS                   | Elegir y probar un adapter RLS-preserving.                 |
| Elegir primera membership             | Fuga o acción en taller equivocado   | Selección explícita, validada y determinista.              |
| Confiar en `totp_enabled` sin AAL     | OWNER accede sin segundo factor real | Enforcement backend sobre prueba MFA emitida por Auth.     |
| Bloquear OWNER AAL1 sin enrollment    | Lockout irreversible                 | Congelar ciclo MFA completo o endpoints permitidos.        |
| Mockear Magic Link                    | Gate verde falso                     | Auth y buzón local reales; mocks sólo unitarios.           |
| Cliente TS escrito a mano             | Drift silencioso API/frontend        | Generación reproducible y diff fail-closed en CI.          |
| Eventos PostHog inventados/PII        | Analítica inútil o fuga              | Taxonomía y allowlist de propiedades aprobadas.            |
| Usar tokens del duplicado no canónico | Violación Regla 0                    | Resolver primero la fuente ADOBE.                          |
| Placeholders ejecutan lógica futura   | Adelanto de shots                    | Sólo navegación/empty states autorizados.                  |
| Añadir paquetes fuera de PRD-00       | Violación Regla 15                   | Resolución expresa y actualización normativa previa.       |
| Debilitar CI para acomodar E2E        | Verifier theater                     | Mantener cuatro jobs y fallar si falta servicio/test.      |

## 21. Secuencia autorizada de FASE 2

1. Formalizar PD-04-01…PD-04-12 en este plan y en las fuentes normativas correspondientes.
2. Revalidar Regla 0; detenerse sólo si aparece otro vacío normativo real.
3. Ajustar exclusivamente dependencias aprobadas y configuración sin secretos.
4. Implementar verificador JWT y adapter RLS con tests adversariales primero.
5. Implementar resolución de tenancy, MFA y `/auth/me/` según contrato congelado.
6. Implementar el límite `/engine/calculate/` sin tocar `/engine`.
7. Configurar drf-spectacular y generación TypeScript fail-closed.
8. Implementar Magic Link real y su E2E aislado.
9. Implementar telemetría base aprobada.
10. Implementar shell/navegación/tema desde la fuente ADOBE reparada.
11. Endurecer checker y CI conservando los cuatro jobs.
12. Ejecutar pruebas dirigidas y luego `python scripts/check_dod.py all` hasta exit `0`.
13. Commits convencionales atómicos, push a `shot-04`, PR protegido y espera de los cuatro
    checks.
14. Entregar evidencia; no mergear sin orden humana.

Tres fallos por la misma causa activarán MODO DIAGNÓSTICO con tres trazas, hipótesis y
opciones; no se continuarán intentos ciegos.

## 22. Condición de ejecución

Las doce decisiones están resueltas y `APROBADO — EJECUTA FASE 2` fue recibido. La
construcción continúa sólo dentro de este plan; cualquier nuevo vacío normativo real
reactiva Regla 0 y se registra antes de proseguir.

## 23. Auditoría de reanudación y bloqueo previo al cierre

Se conservó el working tree de `shot-04`, sin reset ni descarte. `HEAD` continúa en
`040d818c22ffd4d1f86105242025e50b606d1e8a`; la comprobación de ascendencia de esa base
devolvió exit code `0`. `/engine` y Golden snapshots no tienen diff ni archivos nuevos.

Los 40 paths ajenos al alcance que aparecían modificados sin patch después del formatter
se compararon por hash Git con `HEAD`: todos son idénticos. Se refrescó únicamente su
información de índice, sin crear cambios staged ni alterar su contenido.

Conservación documental comprobada:

- El móvil conserva las 61 líneas del antiguo
  `docs/PRD/PRD-DESIGN-SYSTEM-ADOBE.md` en
  `docs/PRD/PRD-WEB-MOBILE-ESSENTIAL.md`; sólo cambia el título. Comparación del cuerpo
  línea por línea: idéntico.
- El sistema dual conserva las 98 líneas de la antigua copia raíz en su path canónico;
  sólo se sincronizó el título a `v1.2 MASTER` y se retiró whitespace final de una línea
  para satisfacer `git diff --check`. La copia raíz ya no existe. Las copias selladas en
  `docs/archive/` son históricas y no son otra autoridad activa.
- `git diff --check` devuelve exit code `0` después de esa corrección.

### PD-04-13 — RESUELTA: dependencias de tipado React

La auditoría detectó que el working tree añadió `@types/react@18.3.28` y
`@types/react-dom@18.3.7` como dependencias directas de desarrollo sin aprobación previa.
El owner autorizó posteriormente esos dos pins exactos, sin `^` ni `~`, y su inclusión
en PRD-00 §6. El tipado real reemplaza el shim mínimo de SHOT-01.

PD-04-13 queda RESUELTA. Esta autorización no permite actualizar React, ReactDOM,
TypeScript ni otras dependencias. PD-01…PD-12 permanecen sin cambios.

### Entorno local autorizado — gates reales pendientes

La inspección inicial no encontró Docker ni Supabase CLI en PATH ni Docker Desktop en su
ubicación estándar. `wsl --list --verbose` informa que WSL no está instalado. No existe
un motor Docker Linux local identificado para ejecutar Supabase/Inbucket/pgTAP.

El owner autorizó habilitar WSL 2 por el mecanismo oficial de Windows, incluyendo
privilegios administrativos y reinicio si el instalador lo exige; Docker Desktop con
backend WSL 2, sin Kubernetes; y Supabase CLI estable fijada en `2.116.0`. Son
herramientas locales del host, no funcionalidad del producto ni configuración a commitear.
No se ejecutará `supabase init` ni se omitirá ningún health check.

No se consideran aprobados RLS real, Magic Link/TOTP E2E, Database Gate ni el gauntlet
completo hasta ejecutarlos realmente con el stack saludable. Se mantienen prohibidos
commits/push/PR hasta completar las pruebas, y merge sin orden humana. No queda una
decisión normativa pendiente tras esta resolución.

## 24. Entorno real verificado y PD-04-14

La habilitación autorizada del host se ejecutó sin reset, cambios al engine ni snapshots:

- WSL `2.7.12.0`, kernel `6.18.33.2`; instalación oficial exit `0`, sin reinicio
  requerido. `wsl --status` informa versión predeterminada `2`; después de instalar
  Docker, `wsl -l -v` muestra `docker-desktop`, `Running`, versión `2`.
- Docker Desktop estable `4.89.0.238018`, instalación por usuario y backend WSL 2;
  firma Authenticode de Docker Inc válida y checksum oficial coincidente. Instalación
  exit `0`; `docker version`/`docker info` responden con Engine `29.7.2`,
  `linux/amd64`, contexto `desktop-linux`, kernel WSL2. No se habilitó Kubernetes.
- Supabase CLI estable `2.116.0`, `draft=false`, `prerelease=false`; checksum SHA256
  oficial verificado; `supabase --version` devuelve exactamente `2.116.0`.
- Se prepararon runtimes locales aislados Python `3.12.10` y Node `24.15.0` para
  ejecutar las versiones de framework existentes y satisfacer el requisito de engine
  de `jsdom@30.0.1`. No se actualizó ninguna dependencia del producto.
- `supabase start` se ejecutó con el config existente, sin `init`, sin
  `--ignore-health-check`, y terminó con exit `0`. Aplicó las dos migraciones existentes
  y `supabase/seed.sql`. PostgreSQL, Auth, REST, Kong, Realtime y correo local arrancaron.
- `git diff --check` sigue en exit `0`; `/engine` y snapshots siguen sin diff.

### PD-04-14 — RESUELTA: Mailpit canónico para CLI 2.116.0

El arranque real emitió:

```text
WARN: config section [inbucket] is deprecated. Please use [local_smtp] instead.
supabase_inbucket_dekopen | public.ecr.aws/supabase/mailpit:v1.30.2 | healthy
SUPABASE_START_EXIT=0
```

Pruebas HTTP diagnósticas contra el servidor real en puerto `54324`:

| Recurso | Resultado real |
| --- | --- |
| `/readyz` | `200` |
| `/api/v1/mailbox/shot04-audit` (contrato Inbucket del E2E) | `404`, `text/plain` |
| `/api/v1/messages` (API Mailpit) | `200`, `application/json` |

El nombre histórico del contenedor y el alias `INBUCKET_URL` no significan que ejecute
Inbucket. La imagen efectiva y la API corresponden a Mailpit. La resolución original
PD-05 exigía Inbucket y su REST; esa exigencia queda sustituida por la resolución del
owner: **Supabase CLI 2.116.0 utiliza Mailpit como capturador local de Auth email**.

Fuentes primarias verificadas para ese pin:

- [Servicio Mailpit de CLI v2.116.0](https://github.com/supabase/cli/blob/v2.116.0/packages/stack/src/services/mailpit.ts).
- [Configuración histórica inbucket de CLI v2.116.0](https://github.com/supabase/cli/blob/v2.116.0/packages/config/src/inbucket.ts), que referencia explícitamente Mailpit.
- [API REST oficial de Mailpit](https://mailpit.axllent.org/docs/api-v1/).

El contrato del gate es `Supabase Auth real → correo local capturado → recuperación
programática del mensaje → Magic Link real → sesión real`. Se conserva CLI `2.116.0`,
sin downgrade ni contenedor alternativo. La configuración pública histórica
`[inbucket]` se conserva: CLI la acepta como alias y arranca Mailpit. El warning de
deprecación se reporta, no se oculta ni se resuelve con una migración cosmética.

Antes del E2E, `/readyz` debe devolver `200`. Se consultan `/api/v1/messages` y el body
del ID devuelto por Mailpit; no se usan rutas `/api/v1/mailbox/...`, IDs/token/link
hardcodeados, mensajes de otras corridas ni skips. Cada corrida usa destinatario único
y excluye los IDs ya consumidos. El polling tiene timeout finito; health, destinatario,
body, link, callback, sesión, Bearer Django y elevación TOTP son aserciones obligatorias.
Los requisitos OWNER `aal1→403`, enrollment/challenge/verify real `aal2→200`, logout y
segundo Magic Link con factor existente permanecen intactos. PD-04-14 queda RESUELTA.

El entorno quedó operativo y el stack local levantado; eso NO aprueba retrospectivamente
Magic Link/TOTP, integración RLS, pgTAP ni el gauntlet completo. Esas suites siguen
pendientes al resolver PD-04-14 y se ejecutarán antes de publicar. No se crearon commits,
push, PR ni merge durante la habilitación del entorno.

## 25. Verificación final local — 2026-09-03

Se reanudó el mismo working tree, sin reset ni nueva FASE 1. La base continúa siendo
`040d818c22ffd4d1f86105242025e50b606d1e8a`. No se reescribieron las resoluciones
PD-01…PD-14; §16 refleja los paths efectivos y la telemetría exclusivamente frontend
que PD-09 ya había autorizado.

### Gates ejecutados nuevamente

| Comando/gate | Salida real de esta reanudación |
| --- | --- |
| `pytest backend/tests/test_gate_harness.py backend/tests/test_openapi.py -q -W error` | `8 passed in 0.11s` |
| `python -m ruff check .` | `All checks passed!` |
| `python -m mypy engine/` | `Success: no issues found in 13 source files` |
| `python backend/manage.py check` | `System check identified no issues (0 silenced).` |
| `pytest backend/ -q -W error`, con entorno Supabase real | `83 passed`; incluye los 17 casos RLS, sin skips |
| `pytest backend/tests/integration/ -vv -W error`, con entorno Supabase real | `17 passed in 6.62s` |
| `pytest engine/ -v -W error` | `22 passed, 5 xfailed in 0.56s`; G1–G4 sin cambios, error `0.00 mm` |
| `npm run typecheck` | `tsc --noEmit`, exit `0` |
| `npm run lint` | `eslint . --max-warnings 0 && tsc --noEmit`, exit `0` |
| `npm run format:check` | `All matched files use Prettier code style!` |
| `npm run test` | `Test Files 5 passed (5)`, `Tests 32 passed (32)` |
| `python scripts/check_auth_e2e.py` | `2 passed (26.8s)`, exit `0`; teardown confirmó logs cerrados y puertos 8000/5173 libres |
| `python scripts/check_generated_api.py`, dos corridas consecutivas | `OpenAPI and generated TypeScript client are reproducible` en ambas; incluye spectacular `--validate --fail-on-warn` y Orval |
| `supabase db lint --level warning --fail-on warning` | `No schema errors found`, exit `0` |
| `supabase test db` | `Files=4, Tests=90`, `All tests successful.`, `Result: PASS` |
| PostgreSQL `16-alpine` independiente | Bootstrap, ambas migraciones, seed y verify: exit `0`; contenedor de prueba retirado |
| `npm run build` | Vite `8.2.2`, `127 modules transformed`, build exit `0` |
| `python scripts/check_dod.py all` | `[PASS] SHOT-04 checker target 'all' completed with exit code 0`; `GAUNTLET_EXIT_CODE=0` |

El gauntlet volvió a recrear Supabase, ejecutó las suites completas y ambos E2E
(`2 passed (19.2s)`), verificó SQL/pgTAP/PostgreSQL 16, cerró Supabase y construyó el
frontend. No reutilizó como PASS las corridas incompletas de sesiones anteriores.

### Evidencia de seguridad y contrato

- JWT verificado por Auth real antes de inyectar `request.jwt.claims`; consultas de
  aplicación bajo `SET LOCAL ROLE authenticated`, no `service_role`. Firma manipulada,
  `sub/aal` adulterados, membership ajena/inactiva y selección de org inválida se rechazan.
- RLS real prueba `auth.uid()`, aislamiento de proyectos/costos A/B, active-org A para
  miembro A+B, catálogo global, commit/rollback, conexiones separadas y requests
  consecutivos. G1/G4 se calcularon mediante Bearer real, Django y loader de artículos.
- Magic Link procede del body Mailpit real para destinatario único; callback, sesión,
  `/auth/me/`, enlace consumido rechazado, OWNER `aal1→403`, enrollment/challenge/verify
  `aal2→200`, logout y nuevo link con challenge del factor existente están comprobados.
- OpenAPI incluye `X-Organization-ID`, security Bearer y errores PD-06. Schema y cliente
  no contienen `calculation_hash` ni `inspector`; las dos regeneraciones fueron idénticas.
- El facade PostHog permite sólo los siete eventos/cuatro propiedades aprobados. Su
  filtro final también elimina URLs/referrers, propiedades de persona y datos sensibles
  que el SDK pudiera añadir; conserva únicamente identidad UUID/protocolo necesarios
  para `identify`/`group`. Pruebas negativas verifican PII/tokens/TOTP y fallo de transporte,
  sin red PostHog. No se habilitaron funcionalidades remotas adicionales.
- Búsqueda de secretos en código de aplicación y bundle: sin credenciales privadas,
  JWT literal, `service_role`, `SERVICE_ROLE`, `JWT_SECRET` ni `DATABASE_URL`. La clave de
  servicio sólo se obtiene en memoria para fixtures locales de tests, nunca en `src`.
- Los checks rápidos de strings son guardas complementarias: no sustituyen pytest,
  Supabase, Playwright, pgTAP ni build reales. Se conservaron exactamente los cuatro
  nombres CI; ningún job/step tiene condición de omisión, `continue-on-error`, `|| true`,
  `allow_fail` ni `allow-fail`. Tests negativos exigen error por herramienta ausente,
  comando fallido, drift o Mailpit no saludable.

### Auditoría de conservación y warnings

- Inventario previo a commit: **103 paths** (28 tracked modificados/eliminados + 75
  nuevos), incluyendo archivos generados y tests; no se fuerza el conteo histórico de 40.
  Backend 34; frontend 52; documentación 8; scripts 4; configuración raíz/CI/Supabase 5.
- Documento móvil: **61/61 líneas**, cuerpo exacto salvo el título renombrado. SHA256 del
  cuerpo unido por LF: `c9fd00f8e13ae6b27b22e6ea82140574fa2a5eb8a7884a1fab14f4db7a776d4c`.
- ADOBE dual: **98/98 líneas**, cuerpo exacto salvo título y whitespace final ya descrito.
  SHA256 del cuerpo normalizado sólo por whitespace final/LF:
  `324858b3c1d5447c0b4ce764c05bf229b4be41091e15ef780962d13c3ed1f813`.
  No existe la copia raíz; archivos históricos no se alteraron.
- `/engine`, snapshots, DDL, RLS, migraciones, seed y pgTAP heredados: sin diff.
  `git diff --check` exit `0`; no reportes/logs, archivos del host ni residuos del
  formatter en el diff. No se ejecutó goldgen porque no se modificaron fórmulas.
- Warning conocido y explícito: CLI `2.116.0` conserva el alias público `[inbucket]`
  aceptado pero deprecado; el servicio real es Mailpit (PD-04-14). No se oculta el warning.
  Los `NOTICE` de pgTAP sobre `CREATE EXTENSION IF NOT EXISTS` no son tests omitidos.
- En esta reanudación Docker no arrancaba por sockets IPC residuales del host. Se
  apartaron exclusivamente directorios temporales con sockets de cero bytes, de forma
  recuperable, y se verificó Engine `29.7.2` antes de ejecutar los gates; no se tocaron
  imágenes, volúmenes, datos, credenciales ni seguridad de Windows.

No hay nuevo `[PENDIENTE-DECISIÓN]` ni contradicción normativa conocida. Esto es evidencia
local, no aprobación automática de merge: falta registrar el PR y los cuatro checks
reales del HEAD publicado. No se inicia SHOT-05 ni se cierra SHOT-04 por iniciativa del
Maker.
