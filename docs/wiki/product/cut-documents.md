---
type: concept
status: active
updated: 2026-10-10
volatility: medium
verified_ref: 7066f28175750fb510d9bb2c831d95d10bb52587
sources:
  - P13 PR https://github.com/KaraAliOsman/framedex/pull/140, CI 4/4 y squash 7066f28175750fb510d9bb2c831d95d10bb52587, 2026-10-10
  - backend/production/cut_manifest.py
  - backend/production/cut_documents.py
  - backend/production/cut_labels.py
  - backend/inventory/sheet_formats.py
  - backend/tests/test_cut_documents_v2.py
  - docs/redesign/P13-ACEPTACION.md
---

# Corte, papel y dirección física

## Hechos verificados

Una OT conserva una posición de una revisión emitida. P13 no crea una OT
artificial con todas las posiciones: su prueba de escala recorre las 113 OT
de revisiones de 1, 12 y 100 posiciones.

La secuencia común es barra/orden de corte y después lámina/Y/X. PDF, CSV,
DXF, etiquetas y QR comparten los códigos físicos de P02. La agrupación manual
conserva autoridad, color, función, largo y ángulos; ordena por primera aparición
y mantiene las direcciones de todas las piezas.

El pack apaisado tiene tres barras por página, cierre Decimal exacto y sección
de padres/refuerzos/junquillos y vidrios. Las etiquetas usan Carta, A4 o rollo
100 × 50 mm; una página de rollo equivale a una etiqueta. La estación siguiente
se obtiene de la ruta real y la rama material de la pieza. La huella figura en
todas las hojas/etiquetas.

Optimizar reserva códigos RT de identidades UUID5 derivadas del plan. Imprimir
solo lee; no asigna códigos ni da de alta stock. Corte completado inserta las
identidades previstas con su rack; un replay evita otra inserción. El recorrido
local comprueba cinco RT con los mismos códigos/destinos, y dos retazos originales
consumidos, mediante material de fixture declarado DEMO.

Los formatos de lámina son declaraciones con proveedor, medidas y fuente.
Crearlas agrega una variante de inventario sin movimiento de stock. Solo dueño
y jefe de taller escriben mediante la autoridad documentary/RLS existente.
Declarar una variante afecta una reoptimización humana, no el plan ya sellado.
Si un histórico no tiene fuente, se muestra Sin dato; si falta formato, se abre
la declaración real en Catálogo › Formatos de lámina.

La revisión de cierre protege el código comercial de suministro usado por el
ledger: un formato físicamente incompatible requiere otro código; variantes
con igual área se ordenan por dimensiones y autoridad de manera determinista.
Su verificación PostgreSQL final pasa junto con los 467 tests de integración.

CSV y DXF son formatos genéricos. DXF AC1021 usa UTF-8 y conserva precisión de
origen; el parser fijado comprueba español y coordenadas. Ver
[especificación genérica](../../production/FORMATOS-CORTE.md).

## Intención y límites

La intención del dueño es que el cortador trabaje solo con papel o pantalla,
sin cambiar de nombre al trasladar una pieza entre artefactos. La evidencia
local usa catálogo/suministro sintéticos con marca DEMO, no certifica una
máquina y no afirma un postprocesador propietario.

Los planes históricos sin dirección RT prevista requieren reoptimización
explícita antes de Corte. Una impresión no reescribe esa historia. Los valores
iniciales configurables son Carta y Recepción de retazos; no se asignan medidas
de lámina silenciosas.
