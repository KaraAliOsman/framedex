---
type: concept
status: active
updated: 2026-10-11
volatility: medium
verified_ref: 412029ac1ea688a0f5bf1d560ba9b2e99871fae6
sources:
  - P21 PR https://github.com/KaraAliOsman/framedex/pull/146, CI 4/4 sobre 50a00fe9e509338cdee706459c17395119e036a8, corrida https://github.com/KaraAliOsman/framedex/actions/runs/38110211964, squash 412029ac1ea688a0f5bf1d560ba9b2e99871fae6, 2026-10-11.
  - docs/cola/prompts/P21-proyecto-hub.md
  - docs/redesign/P21-ACEPTACION.md
  - backend/tests/integration/test_project_workspace.py
---

# Centro de trabajo del proyecto

El proyecto comparte una lectura por organización e identidad. Su encabezado
identifica cliente, dirección, revisión, vigencia y precio aplicado; siete
pestañas exponen posiciones, cotización, precio, cobranza, producción,
documentos y actividad. La próxima acción refleja fase, permisos, enlace
vigente y calendario de cobros. Un anticipo parcial sigue pendiente hasta
completar su primer hito sellado. La consulta pendiente no se interpreta como
un cobro de cero pesos.

Las posiciones usan la elevación real en vista interior. Lista y grilla
conservan filtros, selección, cantidad, caras, vidrio y fuente comercial.
Piso, recinto y eje son metadatos opcionales; su ausencia no se completa con
una ubicación inventada. El precio de cada fila viene del resultado comercial
aplicado de la revisión, no de la cifra indicativa de una propuesta.

Las nuevas operaciones tipadas agregan una receta de la biblioteca, duplican,
eliminan, reordenan o cambian metadatos en lote. UI y asistente comparten
preview, firma de concurrencia, clave de reintento y deshacer. El orden visual
no renumera la dirección física. La metadata conserva la BOM y mediciones;
copiar una posición no copia el levantamiento de su vano físico ni su precio.
Una revisión cerrada o con precio aplicado rechaza las escrituras también en
Postgres.

La biblioteca usa las recetas del editor y sus selecciones de catálogo.
Cada diseño nuevo pasa por el motor. La caché de un lote vive únicamente
dentro de su operación atómica y reutiliza resultados de entradas idénticas;
cada destino conserva la reserva de autoridad del catálogo. La lectura de
mediciones usa una consulta por lote, con el mismo binding que la lectura
individual. Las cien posiciones se virtualizan sin perder Home/End ni foco.

La importación conserva el flujo existente de documento y plano con revisión
humana. Producción filtra las OT en el servidor por proyecto, antes del límite
de lectura. Los documentos se abren mediante acceso firmado, por revisión.
Los borradores de emisión, cobros e importación se mantienen al cambiar de
pestaña y se descartan al cambiar de identidad u obra.

Uw sigue «Sin dato» si falta autoridad térmica. El catálogo y precio
sintéticos conservan DEMO. El centro de trabajo no acredita fabricación,
certificación térmica ni un cobro productivo de un proveedor sandbox.
