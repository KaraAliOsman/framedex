---
type: concept
status: active
updated: 2026-10-12
volatility: medium
verified_ref: bab0df93149e1373b78efd00e17b3120cf092e6d
sources:
  - engine/src/dekopen_engine/analytics.py
  - backend/analytics/sql/
  - supabase/migrations/20270128000000_analytics_evidence.sql
  - docs/analytics/metricas.md
  - docs/redesign/P24-ACEPTACION.md
---

# Analítica con evidencia de decisiones

**Hecho de repo verificado:** cuatro preguntas reúnen ventas, margen, planta y
terreno. Las consultas SQL versionadas resuelven evidencia de la organización;
el motor puro deriva importes, razones, promedios y causas con Decimal. F6 abre
la definición y sus obras, OT y movimientos. El CSV conserva valor exacto,
moneda, fórmula, causa y origen, con protección contra fórmulas de planilla.

El inventario acredita cantidades y los eventos acreditan tiempo transcurrido.
Ninguno acredita tarifas ni horas remuneradas. El cierre por OT añade evidencia
humana revisada de cada consumo, devolución, pérdida, retazo, estación y servicio.
Un cero requiere declaración; un campo ausente conserva Sin dato. Las correcciones
añaden revisiones inmutables. Replay devuelve su recibo original; un movimiento
posterior invalida el cierre anterior hasta una nueva revisión.

La obra compara el costo de la revisión realmente elegida con todas sus OT y
reposiciones. La suma de material útil/valoración, merma, horas, otros y reposiciones
cierra el desvío exacto. El descuento ya está incluido en el neto cotizado y no se
resta nuevamente. No se distribuyen cargos globales a tipologías sin autoridad.
Sin cobertura completa de posiciones, moneda o costos no se publica un margen parcial.

**Intención del dueño:** llegar del número a la causa en dos clics y decidir dónde
se gana o pierde. El período inicial de treinta días se configura en Ajustes.
Los costos solo están disponibles a dueño y jefe de taller, con HTTP y RLS.

**Límites actuales:** ventas/margen usan cohorte de emisión, producción la creación
de OT, instalación la agenda e incidencias el registro. Decisiones y estados son
los existentes al consultar, sin reconstrucción histórica silenciosa. El oráculo
DEMO prueba la matemática, pero no acredita contabilidad ni tarifas de una fábrica.
No hay FX implícito, inferencia de salarios ni copia del corte previsto como hecho real.

No se necesitó investigación externa para estas fórmulas: cada definición,
consulta y resultado manual vive en [metricas.md](../../analytics/metricas.md).
