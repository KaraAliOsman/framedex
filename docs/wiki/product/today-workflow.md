---
type: state
status: active
updated: 2026-10-22
volatility: high
verified_ref: gpt/dk2-p05c-hoy
sources:
  - docs/redesign/P03-ACEPTACION.md
  - engine/src/dekopen_engine/work_queue.py
  - backend/analytics/today.py
  - frontend/src/app/navigation.ts
  - frontend/src/app/DashboardPage.tsx
  - frontend/src/app/todaySummary.ts
  - frontend/tests/e2e/today.spec.ts
  - frontend/scripts/verify-p03.mjs
---

# Trabajo de Hoy y direcciones de flujo

## Hechos verificados

P05a dispone Hoy · Obras · Taller · Catálogo · Empresa en ese orden, ocultando
los destinos que cada rol no puede leer. Hoy es el inicio de los cinco roles;
operario e instalador conservan acceso directo a taller y agenda. Clientes
continúa en `/clients` y la búsqueda de oficina. Informes y Funciones avanzadas
viven en Empresa. El índice antiguo de cotizaciones mantiene su ruta y filtros
hasta integrar las etapas de la lista única en P05.

Diez E2E con sesiones reales, cinco roles y 1440/390 px comprueban navegación,
clientes en la paleta y límites de acceso. Véase la [aceptación P05a](../../redesign/captures/dk2-p05a/aceptacion.md).
El contenido nuevo de Hoy y las etapas todavía no forman parte de P05a.

P05c presenta saludo, fecha del calendario recibido y hasta tres recuentos
pertinentes al rol. Los recuentos salen de tareas reales, deduplicadas por
código; «Aceptadas por coordinar» no afirma una semana que la API no mide.
Los ceros desaparecen. La tarjeta de preparadas abre solo borradores guardados
y verificados del propio usuario; revisar y navegar no emite ni envía nada.
«Nueva cotización» crea con un clic humano y comparte el mismo comportamiento
en Hoy y Obras. Un resultado tardío de otra organización no navega.

La cola mantiene decisiones de precio, recordatorios, saldos y origen bajo
desplegables; orden y paginación de 50 conservan el contrato existente. Venta
por etapa queda plegada y conserva sus enlaces exactos de fase/moneda.
Diez recorridos reales por rol y dos flujos completos de Hoy cubren escritorio
y móvil; incluyen 1.000 acciones sintéticas, 320 px y texto al 200 %.
Véase la [aceptación P05c](../../redesign/captures/dk2-p05c/aceptacion.md).
El editor móvil actual sigue siendo de lectura por debajo de 1024 px; ampliar
su edición corresponde a P06, no se presenta como capacidad de P05c.

P05b incorpora la proyección de etapas, compartición comprobada y las obras
que el asistente guardó con ventanas para el usuario que consulta. Un PDF
con enlace DOCUMENT sin vistas no cuenta como envío. Una sucesora vuelve a
Cotizando; órdenes y pagos se contrastan con la solución elegida vigente.
La instalación completa más saldo real pendiente lleva a Por cobrar;
instalación más saldo cubierto por pagos reales lleva a Cerrada. Sin total
comprobable queda Instalada. No se modifica el estado persistido al leer.

El motor ordena compromisos vencidos, bloqueos, trabajo del día y seguimiento.
El backend lee bajo RLS revisión actual, solicitudes/recibos de precio, ledger
de cobros, reservas de cada OT y agenda. No modifica autoridad sellada. Saldos
y venta por fase usan Decimal en el motor y se separan por moneda; sin fecha
no declara un cobro vencido. Un conjunto en borrador se evalúa para mostrar
su bloqueo sin persistir otra BOM.

Hoy y campana observan una consulta por organización, usuario y rol. Abrirla
no reconoce decisiones. El dueño revisa, confirma y decide inline; el
solicitante marca leído. La allowlist de venta del estimador sigue sin costos,
utilidad ni margen privado.

Búsqueda por códigos humanos dirige a proyecto, cotización, compra, OT y
retazo. Cambio de organización/selección cancela consultas y comandos
capturados. Paleta, ayuda y drawer contienen y restauran foco. Stock muestra
especificaciones declaradas, nunca identidades internas del catálogo.

## Intención y límites

El dueño pide saber qué hacer y por qué al iniciar la jornada. P03 no certifica
DEMO ni rediseña estaciones, compras o retazos. Instalación se deriva solo del
estado explícito de entrega/OT. Inmutabilidad y autorización dominan atajos
visuales. Véanse [precios](price-workspace.md), [direcciones humanas](human-addresses.md)
y [realidad actual](../state/current-reality.md).
