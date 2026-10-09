---
type: state
status: active
updated: 2026-10-09
volatility: high
verified_ref: codex/P03-shell-hoy
sources:
  - docs/redesign/P03-ACEPTACION.md
  - engine/src/dekopen_engine/work_queue.py
  - backend/analytics/today.py
  - frontend/src/app/navigation.ts
  - frontend/scripts/verify-p03.mjs
---

# Trabajo de Hoy y direcciones de flujo

## Hechos verificados

La navegación refleja capacidades del backend por rol y agrupa ventas,
ingeniería, operación, asistente y ajustes. Inventario y cotizaciones tienen
índices propios; producción conserva sus direcciones. Solo el operario entra
automáticamente al taller. Todos pueden abrir su cola explícita.

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
