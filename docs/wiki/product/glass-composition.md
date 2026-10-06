---
type: concept
status: active
updated: 2026-10-05
volatility: medium
verified_ref: codex/D02-vidrios-compuestos
sources:
  - engine/src/dekopen_engine/glass_composition.py
  - engine/tests/test_gold_cases_glass_products.py
  - backend/tests/integration/test_glass_products.py
  - supabase/migrations/20261230000000_glass_composition_and_rules.sql
  - scripts/check_glass_upgrade.py
  - docs/redesign/captures/vidrios-compuestos/aceptacion.md
---

# Composición y autoridad de vidrio

## Hechos verificados

El producto ordena láminas, interláminas y cámaras de exterior a interior. Los
tipos, colores, caras de capa, códigos de proveedor, gas, separador y sellante
pertenecen a esa receta. El parser acepta notaciones comerciales y el formateador
las devuelve sin perder la estructura expresable. La densidad del PVB no se
deduce de su nombre: requiere dato y fuente. Un espesor desconocido impide
presentar un corte a escala; un peso desconocido impide certificar la capacidad.

El motor calcula espesor total/neto, masa, sección, corte, mínimo facturable y
recargos. Las propiedades Ug, g, transmisión y clase necesitan fuente del
proveedor. Un aviso de seguridad cita la regla de la organización; solo una regla
obligatoria bloquea. El catálogo DEMO no acredita una regla oficial. La
compatibilidad usa junquillo por espesor total y masa completa de la hoja contra
la capacidad declarada del herraje.

La posición guarda la receta completa y un identificador de autoridad inmutable.
El backend compara ambos con su mapping visible por RLS; cambiar solamente el
nombre, la fuente, una propiedad o la composición no permite falsificarla. Una
serie global congelada admite un SKU nuevo de una organización, pero no permite
sustituir un SKU anterior ni editar su receta. La publicación requiere revisión
del diff y el clic de un dueño o encargado de taller. Seleccionar el producto usa
la operación tipada `set_glass`, con deshacer/rehacer.

La migración agrega metadatos a los mappings existentes. No vuelve a calcular
posiciones, precios, revisiones, documentos ni hashes. La notación que no se
puede probar queda UNKNOWN con su causa; `3+3` sin PVB conserva la ausencia de
espesor y densidad. El verificador de upgrade comprueba filas previas, BOM/hash y
una revisión histórica legítima.

El pedido por OT o lote lee el BOM sellado y las identidades de infill de la
revisión. PDF, CSV y etiquetas tienen la misma medida y cantidad. Los QR apuntan
a la pieza real y requieren la sesión y permisos del taller. Si el motor entregó
decimales, se conservan y se solicita aceptación de precisión al proveedor;
redondearlos por presentación violaría la tolerancia de 0,00 mm. Un templado se
pide a medida exacta. Un contorno necesita su plano sellado.

## Intención del dueño y datos pendientes

El básico permite elegir un producto compatible sin escribir su notación. El
avanzado muestra su sección a escala, la procedencia de los números y los
procesos. El aviso vive en la bahía afectada y ofrece un vidrio compatible a un
clic. La norma oficial NCh 135/2 y las fichas de proveedor las aporta el dueño;
los ejemplos de zonas de riesgo son sintéticos, desactivados hasta revisión.

La plantilla actual agrega una décima hoja, **Reglas de vidrio**, al flujo D01 de
candidatos, fuentes, diff y publicación. El historial permite deshacer una
publicación de reglas sin borrar las versiones anteriores. La integración D04
ampliará la autoridad de herrajes; D02 usa la capacidad ya declarada, sin crear
valores de carga nuevos. Los datos de activación están en
[ACTIVACION](../../operations/ACTIVACION.md).

## Compatibilidad de escrituras históricas

La notación histórica conserva su contrato y el BOM emitido. No otorga una clase
de seguridad. Al guardar o volver a cotizar se evalúan las reglas obligatorias
actuales de la organización, aunque el cliente omita `glass_product`. Un SKU
publicado con receta estructurada exige esa receta completa, evitando que se
elimine para omitir límites o recargos. Esta validación no reescribe documentos,
precios ni revisiones anteriores. La prueba de integración intenta guardar un
paño lateral antiguo con regla obligatoria y comprueba 422 y ausencia de escritura.
