---
type: concept
status: active
updated: 2026-10-06
volatility: medium
verified_ref: 94f9f5e773cfd227bca820460011ada77ce95baa
sources:
  - engine/src/dekopen_engine/finish_models.py
  - engine/src/dekopen_engine/finishes.py
  - engine/tests/golden_finishes.json
  - supabase/migrations/20270102000000_finish_authority.sql
  - supabase/migrations/20270102000100_demo_finish_catalog.sql
  - scripts/check_finish_upgrade.py
  - docs/redesign/captures/colores-acabados/aceptacion.md
---

# Colores, caras y autoridad de compra

## Hechos verificados en D05

Una combinación comercial identifica interior, exterior y base de PVC. La carta
declara proceso, código del fabricante, canales RGB lineales exactos, fuente,
aproximación y condición sintética. PVC admite masa, foliado y coextrusión;
aluminio, lacado RAL, anodizado y efecto madera. No se infieren una textura,
certificación ni límites de una muestra visual.

El diseño conserva una identidad de combinación en `color`. La carta y las caras
resueltas se sellan en el BOM. El motor aplica holgura de vidrio, límites de
posición/hoja, refuerzo obligatorio y colores de manilla compatibles. El recargo
usa Decimal y su regla por metro de perfil, porcentaje de costo de perfiles o
importe por posición. Sin moneda compatible, costo o regla comercial no hay
precio ficticio. El delta neto toma la primera combinación como referencia y
explica su fuente. Comparte la autoridad de precio de la cotización y usa el modo
predeterminado y moneda de la organización, sin descuento y en contexto
predeterminado. Matriz/lista pueden tener delta cero aunque suba el costo. Un
margen objetivo de proyecto o una conversión ausente explica Sin dato, sin
fabricar un incremento de precio. La resta firmada exacta se calcula en el motor.

Los perfiles por combinación requieren SKU comercial y autoridad de stock/corte
propia. El acero conserva su identidad independiente. Compras, reservas,
remantes y optimización consumen estas identidades; el color comercial de una
ventana no permite sustituir una barra física incompatible. El stock ausente o
con otra combinación continúa bloqueando el flujo.

El editor elige caras y ofrece igual en ambas. Cambiar/deshacer mantiene la
evaluación actual, aun al volver a un resultado cacheado. Guardar espera el nuevo
cálculo. CSS convierte lineal a sRGB; THREE mantiene canales lineales y materiales
por normales: +z interior, −z exterior, canto de base. Portal y PDF consumen la
carta sellada; la vista queda declarada y el documento nombra ambas caras.
Inspección, layout y cálculo estricto comparten la entrada de geometría con esa
carta; siete regresiones doradas y dos HTTP conservan BOM/hash. La proyección
pública del portal entrega muestras por cara y omite los códigos internos de
compra de perfiles, sin reescribir la autoridad emitida.

Catálogo manual e importación comparten la carta tipada. La publicación requiere
diff y revisión humana; deshacer respeta referencias de autoridad. Las nuevas
series DEMO v5 son aditivas y no reescriben v1–v4, precios aplicados, BOM/hashes o
revisiones emitidas. Readiness comprueba todas las combinaciones declaradas y
sus identidades independientes de acero, aun si la carta no ofrece blanco.
Sistemas antiguos omiten los campos opcionales nuevos en su
transporte histórico.

## Intención y límites

La intención del dueño es ver el acabado que se compra y conocer en el mismo
lugar sus restricciones, plazo y variación de precio. Las cartas DEMO usan datos
sintéticos sin certificación. Su fuente no sustituye la ficha/muestra física del
fabricante. Los pasos para aportar autoridad productiva están en
[activación](../../operations/ACTIVACION.md). P04/P09/P19 continúan el rediseño del
editor, la paginación documental y el espacio 3D; D05 no los declara terminados.
