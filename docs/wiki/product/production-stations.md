---
type: synthesis
status: active
updated: 2026-10-09
volatility: medium
verified_ref: 3c3a78bebf898f668814742f8c94a2144d86fb9f
sources:
  - backend/production/stations.py
  - backend/production/quality.py
  - backend/production/pieces.py
  - supabase/migrations/20270112000000_operator_station.sql
  - frontend/scripts/verify-p12-flow.mjs
  - docs/redesign/P12-ACEPTACION.md
---

# Producción por estación

El tablero sitúa cada OT en su primer paso abierto. Las columnas provienen de
la ruta real; muestran obra/cliente al jefe, unidades, compromiso y motivos de
bloqueo. El detalle usa un stepper y nueve pestañas. Piezas reutiliza la tabla
virtualizada; las medidas y direcciones físicas vienen del plan sellado.

El operario elige un puesto persistido por usuario y tenant con RLS. La API de
cola devuelve solo su estación y pasos que pueden trabajarse. Los endpoints
comerciales y las proyecciones de dirección/cliente quedan fuera del rol.
La selección no amplía permisos: otras operaciones mantienen sus gates.

Un QR físico sitúa la pieza, su medida y el siguiente paso sin cambiar el puesto.
La cámara es opcional según capacidad real del navegador; el lector USB/input
permite el mismo recorrido. Bloquear requiere motivo y lo vuelve visible en
el tablero y en Hoy. Actualizar estación vuelve a cargar el detalle, incluso
si el jefe desbloqueó la misma OT desde otra sesión.

Una medición fallida solo bloquea con la elección explícita del operario.
El rechazo del jefe crea un remake en una transacción y un retry con la misma
clave devuelve la misma OT. El selector de la pieza permanece disponible con
QC bloqueado. El remake conserva el conjunto y la pieza como procedencia;
no sustituye el BOM por una pieza ni altera la revisión emitida.

La proyección de direcciones limita los índices de mecanizado a las posiciones
del plan. Los códigos se calculan sobre el snapshot completo para conservar
las direcciones secuenciales históricas. El plan y su fingerprint no cambian.

La intención del dueño es taller táctil y órdenes grandes navegables. La
evidencia de P12 usa 100 posiciones confirmadas y suministro sintético declarado
DEMO; no certifica un catálogo ni la autoridad de un proveedor. Corte avanzado,
CNC y retazos continúan sus encargos P13/P14/P15.

El gate correctivo completo pasa 1.218 pgTAP, 441 integraciones RLS, 17 E2E
y diez actualizaciones pobladas PG16. Su bootstrap crea la clave de usuario
que Supabase proporciona; la FK real rechaza usuarios inexistentes y limpia
su estación al eliminarlos. El fixture de esta verificación se revierte.
