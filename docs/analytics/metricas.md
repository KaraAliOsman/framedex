# Analítica para decidir

Los números se calculan en `engine/src/dekopen_engine/analytics.py` sobre las
consultas versionadas de `backend/analytics/sql/`. Los conteos describen filas
del sistema; nunca estimaciones del asistente. El CSV conserva el decimal
exacto, su moneda, la definición, la causa y cada origen. La presentación redondea
con los formateadores comunes, sin cambiar la autoridad.

## Período, fuentes y permisos

El período incluye ambos días en la zona horaria de la organización. El inicial
es 30 días hasta hoy, configurable entre 1 y 366 en Ajustes › Analítica por el
dueño. El selector admite fechas explícitas. No hay conversión monetaria implícita.

Ventas y margen usan **cohorte de emisión**. Una revisión emitida cuenta una vez,
independientemente de sus enlaces. Una aprobación pertenece al ofrecimiento,
pero el costo cotizado corresponde a la revisión que el cliente eligió. El
estado y la decisión son los existentes al consultar; no se reconstruye un
saldo histórico al último día. Producción usa fecha de creación/liberación
de OT. Instalación usa fecha planificada; incidencias, fecha de registro.

OWNER y WORKSHOP_MANAGER pueden consultar costos; únicamente OWNER cambia
el período inicial. HTTP, RLS y la proyección estrecha de decisiones comprueban
organización y membresía activa. Esa proyección no incluye RUT, firma,
consentimiento ni datos de pago. Los otros roles no reciben este workspace.

## Definiciones y consultas SQL

Cada consulta devuelve la evidencia de la métrica: la agregación financiera
permanece en el motor puro. Los filtros `org`, `start`, `end` son parámetros,
no interpolación de texto. Los tests siguientes ejecutan esas mismas consultas,
no un mock ni una copia de sus resultados.

| Clave | Fórmula y filtros | SQL y columnas fuente | Nulos y ausencia |
|---|---|---|---|
| `emitted` | Revisiones emitidas en cohorte | `emissions.sql`: `project_versions.id, emitted_at` | Sin emisión: Sin datos suficientes; no se cuentan enlaces |
| `approved`, `rejected` | Emisiones con decisión aprobada/rechazada del ofrecimiento | `emissions.sql`: `quote_decisions.kind, offering_version_id`; fallback histórico `customer_approvals.status` | Pendiente no es rechazo; cohorte existente permite cero decisiones |
| `conversion` | Aprobadas ÷ todas las emitidas | `emissions.sql`: decisión por ofrecimiento, una fila por versión | Denominador cero: sin dato; pendientes y cambios siguen en denominador |
| `conversion_estimator` | Aprobadas ÷ emitidas del autor sellado | `emissions.sql`: `snapshot_json.pricing.requested_by`; nombre de miembro vía `private.field_people` | Sin autor reconocido forma grupo visible Sin dato, sin repartir a otro |
| `conversion_typology` | Aprobadas ÷ emitidas con esa tipología | `emissions.sql`: tipologías distintas en `snapshot_json.positions` | Mixta aparece una vez en cada grupo; no se suman grupos como total; tipología ausente explícita |
| `decision_time` | Media de decisión − emisión en horas | `emissions.sql`: `decided_at`, `emitted_at`; solo aprobadas/rechazadas | Una fecha ausente/invertida invalida la media completa |
| `rejection_reason` | Rechazos por motivo literal | `emissions.sql`: `quote_decisions.evidence.note` o `customer_approvals.decided_note` | Falta motivo: grupo «Sin motivo declarado»; no clasificación por IA |
| `pipeline` | Suma bruta por fase actual y moneda, una revisión vigente por obra emitida en cohorte | `emissions.sql`: `projects.current_revision, status`; `snapshot_json.project.total_price_gross, currency` | Neto no reemplaza bruto; falta monto/moneda invalida grupo; no son cobros |
| `quoted_margin` | (Neto elegido − costo cotizado) ÷ neto elegido | `emissions.sql`: revisión seleccionada; `pricing.result.workspace.cascade.net, cost` (fallback histórico explícito) | Neto cero: indefinido; ausencia de costo/neto: Sin dato |
| `real_margin` | (Neto elegido − costo real de todas las OT originales y reposiciones) ÷ neto | `orders.sql` + `materials.sql` + `steps.sql` + `remnants.sql`: cierre vigente, cantidades, tarifas y horas | Todas las posiciones deben tener OT; una OT incompleta o cierre invalidado impide margen parcial |
| `delta_profit` | Costo cotizado − costo real | Las mismas consultas del margen | Conserva signo y moneda; no aproxima un subconjunto |
| `driver_materials`, `driver_waste`, `driver_labor`, `driver_other` | Componente cotizado − componente real de OT originales | Cascada elegida + `production_actual_reports.evidence_json`; cantidades de ledger y retazos | Composición histórica que no cierra: Sin dato; no se inventa un residuo |
| `driver_remake` | −costo de todas las OT de reposición | `orders.sql`: `payload_json.remake_of`; consumos/estaciones/cierre de esas OT | Reposición sin costo invalida puente; no se mezcla en merma de original |
| `driver_discount` | Descuento sellado ya incluido en el neto elegido; contexto sin restarlo nuevamente del desvío | `emissions.sql`: `workspace.cascade.steps.discount.amount` | Históricos sin descuento en cascada conservan Sin dato |
| `deviation_typology` | Suma de costo cotizado de cada posición − costo de sus OT y reposiciones, por tipología y moneda | `emissions.sql`: `workspace.positions.cascade`, posición; otras cuatro consultas de costo | No reparte cargos globales sin autoridad; una posición sin composición/cierre invalida grupo |
| `planned_waste` | Largo perdido previsto total ÷ largo total de entrada | `orders.sql`: `optimization.bars.metrics.process_waste_mm`, `workshop_cut_plan.stock_length_mm` | Sin plan o piezas sin colocar: Sin dato; barras de retazo cuentan como entrada |
| `actual_waste` | Pérdida real total ÷ entrada real total | `orders.sql`: cierre vigente `evidence_json.bars` | Toda OT debe tener medición completa confirmada y balance exacto; no se compara solo subconjunto |
| `utilization` | Largo de piezas útiles real ÷ entrada real | Misma consulta y evidencia de barras | Retazo recuperable no es pieza útil ni pérdida; no incluye láminas |
| `remnant_use` | Instancias realmente consumidas por OT de cohorte | `remnants.sql`: `status='CONSUMED', consumed_order_id` | Reservas/plan no cuentan; cohorte sin consumo acredita cero, sin OT es Sin dato |
| `station_time` | Media de finished_at − started_at de pasos terminados por estación | `steps.sql`: timestamps, `status='DONE', label` | Una estación terminada sin tiempo válido invalida su media; incluye esperas y no valora trabajo |
| `orders_on_time` | OT completadas hasta fecha prometida ÷ OT no canceladas de cohorte | `orders.sql`: `expected_at`, primer `production_step_events.WO_COMPLETED` | Promesa o finalización ausente: Sin dato; no desaparecen las pendientes |
| `remake_cause` | OT de reposición en cohorte por causa literal | `orders.sql`: `payload_json.remake_of, remake_reason.note` | Sin causa forma grupo declarado; no infiere responsabilidad |
| `installations_on_time` | Recepciones hasta fecha planificada ÷ instalaciones no canceladas agendadas en cohorte | `visits.sql`: `planned_on, kind, status`, primer `field_events.RECEIVE` | Servicio no es instalación; recepción ausente invalida puntualidad completa |
| `incidents_kind` | Incidencias de cohorte por tipo declarado | `incidents.sql`: `field_incidents.kind, created_at` | Un caso cuenta una vez |
| `incidents_typology` | Incidencias por tipología de posición sellada | `incidents.sql`: `position_id, unit_index`, versión de visita y `snapshot_json.positions`; fallback contexto sellado | Grupo «Sin tipología reconocida» conserva faltantes, sin asignación inventada |
| `open_warranties` | Garantías creadas en cohorte cuyo estado actual no es cerrado | `incidents.sql`: `kind='WARRANTY', status, created_at` | Etiqueta dice «del período todavía abiertas»: no pretende saldo histórico ni de todos los años |

## Costos reales y balance físico

El ledger acredita cantidades, no pesos. El cierre añade costo neto por la
misma unidad, pérdida incluida en cada consumo, horas efectivas y tarifa por
estación, otros servicios y crédito respaldado por retazos producidos. Vacío
es desconocido; cero debe ser **declarado** y respaldado por una fuente.

`Costo = Σ(consumos + pérdidas adicionales − devoluciones + retazos consumidos)
× tarifa + Σ(horas de personas × tarifa) + otros − crédito reutilizable`.
La parte perdida dentro de un consumo distribuye ese costo entre material útil
y merma; no lo añade otra vez. Un movimiento SCRAP es material destruido adicional
y se atribuye entero a merma. RETURN siempre tiene parte perdida cero. El crédito
no puede exceder el material útil ni existir sin retazos producidos registrados.

Se revisa antes del clic de registro. Las correcciones añaden revisiones
inmutables; una clave repetida devuelve el recibo original incluso después de
otra corrección. El fingerprint conserva cantidades, estaciones y retazos:
evidencia posterior invalida el cierre anterior hasta revisar otra vez.
OT sin terminar admite evidencia parcial, conserva Sin dato y no admite cierre.

La medición real de barras declara entrada, piezas, pérdida y retazo recuperable
con la fuente y confirmación de **todas** las barras. Entrada = piezas + pérdida +
retazo recuperable exactos. Sin esa cobertura explícita no se publica una razón.
No se copia el plan como hecho real. Sierra y despuntes son pérdida; material
reutilizable es stock. La tarifa y las horas son evidencia humana, nunca
timestamps tratados como remuneración ni números del LLM.

El puente de utilidad separa material útil/valoración, merma, horas, otros y
reposiciones. La suma de causas cierra exactamente en el desvío; cada causa
abre monto cotizado y movimientos reales firmados. **El descuento ya está en
el neto cotizado**: se muestra como contexto, no se descuenta nuevamente.

## Oráculo manual y verificación

`backend/tests/integration/analytics_fixture.py` crea un tenant aislado con
historia PRE_SHOT09 marcada DEMO. La prueba parametrizada
`test_versioned_sql_metric_manual_oracle` ejecuta un test SQL por clave de la
tabla; `test_sql_typology_pipeline_and_incident_groups` prueba los grupos restantes.
No reescribe ningún sello: las suspensiones de triggers están confinadas a la
creación del oráculo histórico y se restauran antes de los cierres productivos.

Cuatro emisiones; una aprobación que elige B, un rechazo, dos pendientes.
Conversión 1/4; Fijo 1/3, Corredera 0/1. Decisiones 48 h y 72 h: media 60 h.
Pipeline elegido $1.071 aprobado y $1.428 cotizado, una revisión por obra.
Neto B $900/costo cotizado $500: original 42×10 +3×20 +20 = $500;
reposición 3×10 +0,5×20 = $40 (retazo con valor cero declarado).
Costo real $540, utilidad $360, margen 40 %, desvío −$40;
causas +$10, +$10, −$10, −$10, −$40. Descuento −$100 incluido antes.

Barras: plan 700/9.000, pérdida real 600/9.000, útil 8.000/9.000.
Estaciones 1 h y 3 h: media 2 h, distinta de las horas laborales.
Puntualidad OT e instalaciones 1/2; un retazo consumido; dos garantías,
una abierta, y un daño. Casos adicionales prueban fuente ausente, posición
sin OT, cierre invalidado, moneda ausente, RLS B≠A, permisos y revocación,
preview/confirmación/replay/corrección/inmutabilidad y CSV.

`engine/tests/golden_analytics.json` se genera únicamente mediante `make goldgen`.
El test compara bytes/datos y repite el oráculo con precisión ambiente reducida.
`supabase/tests/database/246_analytics_evidence.test.sql` verifica RLS, grants
y guardas; la integración prueba el aislamiento efectivo. Los tests de UI
prueban F6, fuente exacta, recuperación, ausencia de cero ficticio y dos clics
para registrar. Las capturas en `docs/redesign/captures/analitica/` son evidencia
de presentación; no convierten el oráculo DEMO en contabilidad certificada.
