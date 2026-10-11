---
type: state
status: active
updated: 2026-10-11
volatility: high
verified_ref: c0d12cd8ca8ad7c391ba8bbb350c2971418fd800
sources:
  - P23 código c0d12cd8ca8ad7c391ba8bbb350c2971418fd800, gates completos, navegador y PostgreSQL propio, 2026-10-11
  - backend/production/field.py
  - backend/purchasing/field_purchase.py
  - supabase/migrations/20270125000000_field_work.sql
  - backend/tests/integration/test_field_work.py
  - docs/redesign/P23-ACEPTACION.md
---

# Despacho, terreno y postventa

Verificado con Auth/Supabase propios, motor y navegador real. El SHA y la CI
de integración se registran en current-reality al cerrar el PR.

## Hechos verificados

La oficina agenda visita por día, franja y equipo desde una revisión elegida
o una OT embalada. Terreno registra unidades y evidencia; no autoriza compras
ni fabricación. Cada visita conserva contexto sellado de cliente, obra,
posición, unidad, perfil, vidrio, herraje y piezas. Códigos VIS/INC/ACT son
secuenciales por organización; UUID permanece técnico.

RLS valida membresía/segundo factor vivos. INSTALLER solo ve su asignación.
Los eventos, assets, recibos y fuentes de casos son inmutables; tampoco
admiten TRUNCATE. La cola usa UUID/payload estable y un recibo transaccional
para replay; los bytes de un acta ya emitida se conservan.

Una incidencia enlaza posición/unidad/piezas y foto. El jefe diagnostica y
decide RM, OC adicional o servicio. El adicional tiene capacidad propia,
sin usar ni liberar claims de fabricación originales. Cerrar exige evidencia
del resultado. Medición alimenta D07 y abre borrador correctivo con diff del
motor cuando la fuente aprobada ya está fabricada.

Garantía conserva días/inicio de la revisión aprobada y la elección P10.
Entrega/instalación toman el primer hecho firmado por unidad; un servicio
no inicia instalación. Lo no declarado muestra Sin dato. Hoy proyecta visitas,
incidencias y fechas de garantía desde esas autoridades.

## Decisiones y límites

La preferencia inicial de garantía es Sin dato. El emisor declara días e
inicio en Comercial antes de aprobar; no se interpreta texto libre.
La copia local se limita a actor+organización y se elimina al salir/cambiar
de actor. El service worker guarda solo recursos públicos; evidencia y
sesión no entran en su caché. Sin señal, el teléfono conserva su última
asignación descargada; el servidor vuelve a validar antes de sincronizar.

HTTPS, Storage privado, roles y autoridad real de catálogo se conectan según
[ACTIVACION](../../operations/ACTIVACION.md). DEMO permanece sintético.
[Aceptación](../../redesign/P23-ACEPTACION.md) distingue PDFs históricos del
ensayo, acta final, prueba sin red y límites de revocación de una copia local.
