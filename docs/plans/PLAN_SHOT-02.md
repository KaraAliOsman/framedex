# PLAN SHOT-02 — DDL Supabase + RLS + Aislamiento Multi-Tenant

## 1. Estado y fuentes obligatorias

- **Branch de trabajo:** `shot-02`, creada desde `main` en `0496ffad1fff507d7f892afbe9ce81fa58c4f511`.
- **SHOT anterior:** SHOT-01 cerrado; tag `shot-01` en `8f16aca508092e44161146f94a4360247702893b`.
- **Constitución leída:** `docs/CONSTITUTION.md` v1.2 MASTER, reglas 0–22.
- **Gate leído:** `docs/PRD/PLAN_SHOTS.md`.
- **Contrato funcional leído:** `docs/PRD/PRD-02.md` completo.
- **Interfaces reales inspeccionadas:** configuración Django, dependencias Python y frontend, `Makefile`, `scripts/check_dod.py`, workflow CI, `.env.example` y estructura actual del repositorio.

Este plan es la memoria normativa del shot. Ninguna decisión marcada como
`[PENDIENTE-DECISIÓN]` puede resolverse inventando datos, políticas o excepciones.

## 2. Objetivo y condición de salida

Construir la base PostgreSQL 16/Supabase definida en PRD-02 con migración reproducible,
RLS verificable, seed global Demo 60 y pruebas de aislamiento, sin implementar todavía
las capas de aplicación de shots futuros.

El shot sólo puede considerarse terminado cuando se obtenga evidencia real de:

1. El SQL se aplica desde cero en una instancia Supabase limpia.
2. Un usuario de tenant A no puede leer ni mutar datos privados de tenant B.
3. El catálogo global Demo 60 es visible para ambos tenants conforme a la política aprobada.
4. Existen `payment_events`, `credit_ledger` y `hardware_kits` con sus restricciones y RLS.
5. `python scripts/check_dod.py all` termina con **exit code 0** y conserva todos los gates de SHOT-01.
6. El check `Database Gate` termina verde en CI y queda requerido en la protección de `main`.

## 3. Alineación con otros shots

### Entradas consumidas

- **SHOT-01:** monorepo, CI, tooling, checker fail-closed y protección de `main`.
- **PRD-02:** DDL canónico, tipos, relaciones, índices, restricciones y políticas RLS.
- **CONSTITUTION:** aislamiento por `org_id`, auditoría, determinismo numérico y prohibición de `float`.

### Consumidores futuros, sin implementarlos aquí

- Autenticación, membresías y autorización usarán `organizations`, `profiles` y
  `organization_members`.
- Catálogos, cálculo, cotización y producción consumirán los sistemas, artículos,
  junquillos, herrajes, precios, proyectos, órdenes y retazos definidos aquí.
- Facturación y billetera consumirán `billing_customers`, `subscriptions`, `payments`,
  `payment_events` y `credit_ledger`.
- Auditoría consumirá `price_audit_logs` y `ai_audit_logs`.

SHOT-02 sólo establece y demuestra los contratos de persistencia. No implementa esos
flujos de aplicación.

## 4. Alcance exacto

### 4.1 Crear

| Archivo | Propósito | Aporte directo al gate |
|---|---|---|
| `supabase/config.toml` | Configuración local mínima del proyecto Supabase, sin secretos. | Permite levantar y reiniciar una instancia limpia de forma reproducible. |
| `supabase/.gitignore` | Excluir estado temporal y artefactos locales generados por Supabase CLI. | Evita que el gate dependa de estado no versionado. |
| `supabase/migrations/20260901000000_initial_schema.sql` | Migración única inicial con extensiones, funciones, enums, tablas, claves, índices, restricciones, RLS y políticas autorizadas por PRD-02. | Es el SQL que debe aplicar limpiamente desde cero y contener las tres tablas nominales del gate. |
| `supabase/seed.sql` | Seed idempotente/determinista del catálogo global Demo 60, sólo con valores expresamente aprobados. | Demuestra que Demo 60 queda cargado y visible globalmente tras un reset limpio. |
| `supabase/tests/database/000_schema.test.sql` | Pruebas pgTAP de estructura, tipos numéricos, restricciones, tablas requeridas y RLS habilitado. | Falla si falta DDL, aparece un tipo flotante o una tabla de negocio queda sin RLS. |
| `supabase/tests/database/010_rls_isolation.test.sql` | Fixtures A/B y pruebas positivas/negativas de SELECT/INSERT/UPDATE/DELETE bajo identidad autenticada. | Demuestra mecánicamente `tenant-A != tenant-B`; una política ausente o permisiva debe romper el test. |
| `supabase/tests/database/020_global_catalog.test.sql` | Prueba de visibilidad de Demo 60 y sus registros globales desde ambos tenants, más ocultamiento de catálogos privados ajenos. | Demuestra el componente “seed Demo 60 visible global” sin convertir el test en una mera comprobación de existencia. |
| `supabase/tests/database/030_billing_idempotency.test.sql` | Pruebas de unicidad/idempotencia de eventos y pagos, saldo no negativo, aislamiento del ledger y acceso de servicio a eventos. | Verifica los contratos críticos de `payment_events` y `credit_ledger`. |
| `supabase/compat/postgres16_bootstrap.sql` | Stubs mínimos de roles y funciones `auth` que Supabase aporta, sólo para el contenedor PostgreSQL 16 limpio de CI. | Permite aplicar el mismo DDL fuera de la imagen Supabase sin falsear sus dependencias de autenticación y queda fuera del discovery pgTAP. |
| `supabase/compat/postgres16_verify.sql` | Asserts fail-closed de versión, 21 tablas, RLS y seed global sobre PostgreSQL 16. | Demuestra compatibilidad exacta con la versión canónica de PRD-02 sin ejecutarse como suite TAP. |

La migración contendrá las 21 tablas del DDL completo de PRD-02, agrupadas así:

- Tenancy: `organizations`, `profiles`, `organization_members`.
- Catálogo: `profile_systems`, `articles`, `glazing_beads`, `hardware_kits`.
- Costos y pricing: `cost_lists`, `cost_list_items`, `pricing_rules`, `price_audit_logs`.
- Proyectos y operación: `projects`, `project_items`, `orders`, `offcut_inventory`,
  `ai_audit_logs`.
- Billing: `billing_customers`, `subscriptions`, `payments`, `payment_events`,
  `credit_ledger`.

### 4.2 Modificar

| Archivo o configuración | Modificación permitida | Aporte directo al gate |
|---|---|---|
| `scripts/check_dod.py` | Generalizar el checker sin debilitar SHOT-01 y añadir un target `database` fail-closed que compruebe herramientas/archivos, aplique la base limpia y ejecute lint/tests SQL. Debe limpiar la instancia local en `finally` sin ocultar el exit code original. | Hace que `python scripts/check_dod.py all` incluya el gate de base de datos y rechace verificaciones omitidas. |
| `.github/workflows/ci.yml` | Añadir un job llamado exactamente `Database Gate`, con versión exacta y verificada de Supabase CLI y ejecución del checker de base de datos en el runner con Docker. Mantener intactos los tres jobs de SHOT-01. | Ejecuta el gate reproducible en CI y produce el contexto que exigirá branch protection. |
| `Makefile` | Añadir comandos mínimos para el gate SQL y mantener `dod` como entrada al checker completo. | Ofrece el mismo flujo verificable local/CI sin duplicar lógica. |
| `README.md` | Documentar prerrequisitos locales, reset, pruebas SQL y gauntlet completo. | Permite reproducir la evidencia del gate sin conocimiento implícito. |
| `docs/plans/PLAN_SHOT-02.md` | Mantener decisiones, alcance y posteriormente evidencias reales del shot. | Memoria persistente Maker/Checker y trazabilidad del cierre. |
| Protección de branch de GitHub `main` | Después del primer `Database Gate` exitoso, agregar ese contexto a los checks requeridos, sin retirar los checks de SHOT-01 ni desactivar la protección de administradores. | Impide integrar cambios futuros que rompan DDL/RLS. |
| `docs/PRD/PLAN_SHOTS.md` | Sólo en el cierre formal autorizado: marcar SHOT-02 como `CERRADO`. | Registra el estado final; no se modifica durante construcción ni antes del gate verde. |

No se prevé modificar `.env.example`: ya expone los placeholders Supabase requeridos y
no se versionarán secretos.

### 4.3 PROHIBIDO en SHOT-02

- Crear modelos o migraciones Django que dupliquen el DDL de Supabase.
- Implementar APIs, vistas, serializers, UI, autenticación, cotización, producción,
  optimización, pagos, webhooks o consumo del ledger.
- Implementar comportamiento operativo de `offcut_inventory`; sólo corresponde su contrato SQL.
- Añadir módulos pertenecientes a shots futuros aunque las tablas ya existan.
- Añadir dependencias de producto Python o npm. Supabase CLI es herramienta externa de
  verificación y su versión de CI quedará fijada explícitamente.
- Introducir `FLOAT`, `REAL` o `DOUBLE PRECISION` en datos de negocio; se conservarán
  los `NUMERIC(p,s)` definidos por PRD-02.
- Introducir números calculados por IA, fórmulas de `/engine` o tocar golden snapshots.
- Añadir colores hex fuera del sistema de tokens.
- Copiar features desde `docs/archive/DESCARTES`.
- Aplicar migraciones sobre una instancia remota o de producción durante este shot.
- Debilitar, saltar o convertir en opcionales los checks heredados de SHOT-01.
- Crear políticas, fixtures, roles o excepciones no autorizadas para rellenar vacíos del PRD.
- Hacer merge a `main` sin autorización expresa posterior del usuario.

## 5. Contratos de implementación

### 5.1 Migración reproducible

- La migración será la fuente de verdad SQL de SHOT-02.
- Se ejecutará sobre una base limpia mediante el flujo local de Supabase CLI.
- Las operaciones se ordenarán por dependencias: extensiones/funciones, enums, tablas,
  claves/índices, triggers, RLS y políticas.
- Se mantendrán nombres, tipos, defaults y restricciones de PRD-02 salvo resolución
  explícita de un `[PENDIENTE-DECISIÓN]`.
- `current_user_org_ids()` se implementará con las propiedades de seguridad indicadas
  por PRD-02 y las pruebas comprobarán su efecto, no sólo su existencia.

### 5.2 Pruebas RLS no vacías

Las pruebas se ejecutarán bajo roles e identidades equivalentes a llamadas reales y no
como propietario de las tablas. Para cada familia de negocio cubierta:

1. Tenant A puede operar sobre su propio registro cuando la política lo permite.
2. Tenant A no puede ver el registro privado equivalente de tenant B.
3. Tenant A no puede insertar o mutar un registro adjudicado a tenant B.
4. Tenant B conserva acceso a sus propios registros.
5. Ambos tenants pueden leer registros globales autorizados.

El diseño debe ser sensible a mutaciones: eliminar una policy, convertir el filtro de
`org_id` en una condición verdadera o cambiar una columna `NUMERIC` a `REAL` debe causar
al menos un fallo del gauntlet.

### 5.3 Billing e idempotencia

- Se probará la unicidad de `(provider, provider_event_id)` en `payment_events`.
- Se probará la unicidad del identificador externo de `payments` definido por PRD-02.
- Se probará que el balance de `credit_ledger` no acepta estados negativos cuando así lo
  exige el DDL.
- El acceso a `payment_events` se probará bajo el rol autorizado por la decisión del dueño;
  no se simulará un flujo de webhook de un shot futuro.

## 6. Secuencia de construcción tras aprobación

1. Resolver y documentar todas las decisiones bloqueantes de la sección 9.
2. Verificar la versión vigente de Supabase CLI y fijarla en CI/configuración.
3. Crear configuración local, migración y seed.
4. Crear pruebas pgTAP de esquema, aislamiento, catálogo global y billing.
5. Integrar el target de base de datos en checker, `Makefile` y CI.
6. Ejecutar primero los checks SQL específicos y corregirlos sin ampliar alcance.
7. Ejecutar `python scripts/check_dod.py all` hasta obtener exit code 0 real.
8. Si una misma causa falla tres veces, detener reparación automática y entregar MODO
   DIAGNÓSTICO con tres trazas, hipótesis y opciones para decisión del usuario.
9. Crear commits convencionales atómicos por contrato coherente.
10. Hacer push de `shot-02`, presentar la salida real de cada comando del gate y esperar
    autorización de merge.

## 7. Comandos previstos de verificación

Los nombres exactos se confirmarán contra la versión fijada de la CLI, sin sustituir el
gauntlet obligatorio:

```text
supabase start
supabase db reset
supabase db lint
supabase test db
python scripts/check_dod.py database
python scripts/check_dod.py all
```

El checker completo seguirá ejecutando, además, los gates heredados:

```text
ruff
mypy
pytest
vitest
frontend build
```

La evidencia de cierre incluirá comando, exit code y salida real relevante. No se aceptará
“todo pasó” como resumen.

## 8. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación dentro del alcance |
|---|---|---|
| Las pruebas se ejecutan como propietario y eluden RLS. | Falso verde de aislamiento. | Cambiar explícitamente de rol/JWT y demostrar accesos positivos y negativos. |
| Divergencia local/CI de Supabase CLI. | SQL que pasa en un entorno y falla en otro. | Fijar una versión exacta verificada y documentarla. |
| Seed no idempotente o dependiente de UUID aleatorio. | `db reset` no reproducible. | UUID y datos deterministas aprobados, inserts ordenados y prueba de contenido. |
| Políticas incompletas en una tabla con RLS. | Acceso bloqueado o fuga futura al conceder privilegios. | Pruebas por familia de tablas y catálogo de policies esperado. |
| Política global demasiado amplia. | Lectura anónima no autorizada. | Resolver explícitamente el contrato de autenticación antes de codificar. |
| Checker deja procesos/volúmenes o encubre fallos al limpiar. | Runs inestables o falso verde. | Limpieza controlada en `finally`, preservando el primer exit code no cero. |
| Dependencia local inexistente. | No se puede satisfacer el stop condition local. | Resolver el entorno antes de construcción; no declarar verde sólo por CI. |
| La CLI Supabase vigente no ofrece PostgreSQL 16 local. | El gate Supabase usa PostgreSQL 17 y no prueba por sí solo la versión canónica. | Aplicar el mismo DDL/seed adicionalmente sobre `postgres:16-alpine` en `Database Gate`. |
| Cambio manual del golden. | Violación de Regla 22. | No se toca `/engine` ni golden; si el diff apareciera, detenerse y diagnosticar. |

## 9. Decisiones del dueño

### [RESUELTA 2026-09-01, PARCIAL] Datos canónicos de Demo 60

El dueño aprobó el sistema global `DEMO_60` con `org_id = NULL`, nombre, profundidad,
material, cámaras y parámetros exactos; siete artículos de perfiles, tres kits y cinco
entradas de matriz. Los identificadores técnicos serán UUID deterministas.

Persisten dos vacíos de negocio en columnas obligatorias sin default:

- Cada kit necesita `min_leaf_width_mm`, `max_leaf_width_mm`, `min_leaf_height_mm`,
  `max_leaf_height_mm` y `max_leaf_weight_kg`.
- Cada entrada de `glazing_bead_matrix` necesita indicar si referencia al junquillo de
  18 mm o al de 24 mm. La lista de espesores por sí sola no define esa relación.

Estos datos alimentan directamente el matching de herrajes y la Regla R06; no se pueden
deducir como simples valores técnicos.

### [RESUELTA 2026-09-01] Policies ausentes en costos/pricing

Se autorizó `FOR ALL`, con `USING` y `WITH CHECK` basados en
`current_user_org_ids()`, para `cost_lists`, `cost_list_items`, `pricing_rules` y
`price_audit_logs`.

### [RESUELTA 2026-09-01] `payment_events` sin `org_id`

Se autorizó `org_id UUID NULL` con FK opcional. La tabla es un log de ingesta crudo y su
única policy será `FOR ALL` para JWT `service_role`.

### [RESUELTA 2026-09-01] Lectura global autenticada

La rama global de cada policy exigirá `auth.uid() IS NOT NULL`. Visitantes anónimos no
podrán consultar catálogos; los miembros seguirán accediendo al catálogo de su organización.

### [RESUELTA 2026-09-01] Entorno local del gauntlet SQL

Se autorizó un suite Python aislado dentro de los pytest existentes para el gate local,
sin dependencias de producto nuevas. La aplicación real de migraciones sobre Supabase
limpio se conserva como `Database Gate` de CI.

### [RESUELTA 2026-09-01] SUPERADMIN

La gestión SUPERADMIN queda diferida a SHOT-20. SHOT-02 sólo modelará la lectura del flag
JWT `auth.jwt() -> 'app_metadata' ->> 'is_superadmin'`; no concederá nuevas policies.

### [RESUELTA 2026-09-01] Valores obligatorios de los kits Demo 60

- `TURN`: ancho `400.00..1200.00`, alto `500.00..2400.00`, peso máximo `80.00`,
  `carriages_qty=0`, `stay_arms_qty=0`.
- `TILT_TURN`: ancho `450.00..1400.00`, alto `600.00..2400.00`, peso máximo `100.00`,
  `carriages_qty=0`, `stay_arms_qty=1`.
- `SLIDING`: ancho `400.00..1500.00`, alto `500.00..2500.00`, peso máximo `120.00`,
  `carriages_qty=2`, `stay_arms_qty=0`. Corredera 2H/3H/4H se normaliza a `SLIDING`.

### [RESUELTA 2026-09-01] Relación vidrio–junquillo Demo 60

- `4.00` mm → `JQ-24`, ancho `24.00`, juntas `3.00/3.00`.
- `5.00` mm → `JQ-24`, ancho `24.00`, juntas `2.50/2.50`.
- `6.00` mm → `JQ-24`, ancho `24.00`, juntas `2.00/2.00`.
- `20.00` mm (`4-12-4`) → `JQ-14`, ancho `14.00`, juntas `3.00/3.00`.
- `24.00` mm (`4-16-4`) → `JQ-10`, ancho `10.00`, juntas `3.00/3.00`.

### [RESUELTA 2026-09-01] Rol del artículo Poste

El enum permanece intacto. Se crean `POSTE-V` con `MULLION_V` y `POSTE-H` con
`MULLION_H`, ambos con cara de `60.00` mm.

### [RESUELTA 2026-09-01] Ubicación de `welding_loss_mm`

Permanece exclusivamente en `profile_articles`: `6.00` para `FRAME` y `SASH`; `0.00`
para postes y junquillos.

### [RESUELTA 2026-09-01] Traslape central y contrato de consumo de soldadura

El catálogo `DEMO_60` persiste `central_overlap_mm = 40.00`, consistente con G5 =
`966.00 mm`. `profile_articles.welding_loss_mm` es la única autoridad editable:
`6.00` para `FRAME` y `SASH`, y `0.00` para `MULLION_V`, `MULLION_H` y
`GLAZING_BEAD`. Los consumidores futuros deberán resolver la pérdida por artículo/rol;
no podrán asumir que `FRAME` y `SASH` comparten siempre el mismo valor.

### [RESUELTA 2026-09-01] Helper RLS en schema privado

`private.current_user_org_ids()` será `SECURITY DEFINER`, tendrá `search_path` vacío y
referencias calificadas a `public.tenancy_memberships`. Sólo `authenticated` recibirá
`USAGE` del schema y `EXECUTE` de la función; `PUBLIC` queda revocado. Todas las policies
invocarán el nombre calificado. Los catálogos globales no concederán privilegios a `anon`.

### [RESUELTA 2026-09-01] Alineación Regla Cero del schema canónico

El DDL conserva los nombres canónicos `credits_balance` e `is_demo`, fija la holgura
blanca por defecto en `5.00` y usa índices únicos parciales separados para códigos de
sistemas globales y de tenant, conforme al PRD-02 vigente.

## 10. Referencias técnicas externas verificadas

- Flujo local oficial: <https://supabase.com/docs/guides/local-development/cli-workflows>
- Testing y lint SQL oficial: <https://supabase.com/docs/guides/local-development/cli/testing-and-linting>
- Pruebas de RLS/JWT: <https://supabase.com/docs/guides/local-development/testing/overview>
- Acción oficial para fijar Supabase CLI en CI: <https://github.com/supabase/setup-cli>

Estas referencias sólo definen el harness técnico. PRD-02 y la Constitución siguen siendo
la autoridad para reglas de negocio y datos.

## 11. Criterio de aprobación de este plan

La respuesta `APROBADO — EJECUTA` autoriza únicamente el alcance anterior y debe incluir
las resoluciones de las decisiones bloqueantes. Hasta entonces no se escribirá DDL, seed,
tests SQL, checker ni CI de SHOT-02.
