# P12e · Un taller de una persona pasa de la aprobación a la OT

Verificación local del 25-10-2026 en `claude/dk3-p12e-medidas`, con el stack
aislado `dekopen-ci`. `proline-acceptance` pasa a 1440 y 390 px (~72 s de
máquina cada uno). Recorre: registro, taller, empresa, PRO6004 desde la
biblioteca, ficha de compra, precios, ventana de prueba, tres ventanas, reglas
de taller, emisión, aprobación del cliente y liberación a producción.

## Lo que quedó demostrado

1. **La revisión que el cliente aprueba ya es fabricable.** Con «Las medidas de
   la cotización son de fabricación» (Empresa › Taller) y las reglas de taller
   confirmadas, REV-A se sella con `production_allowed` y se libera sin volver a
   emitir ni pedir otra aprobación. La revisión registra la regla con que se
   emitió (`site_measurement`).
2. **La compra para taller sale completa desde la serie real:** perfiles con su
   barra, aceros (un mismo Pro-R1 para marco y travesaño es una sola compra),
   termopanel con peso y área máxima declarados, kits Vorne con los códigos de la
   OT 385 y el tornillo del acero por la nueva hoja «Fijaciones».
3. **La orden de corte** de la obra liberada se muestra a escala
   ([1440](f1-orden-de-corte-1440.png), [390](f1-orden-de-corte-390.png)); las
   reglas de taller confirmadas en la serie
   ([1440](f1-reglas-de-taller-1440.png), [390](f1-reglas-de-taller-390.png)).

## Lo que la prueba encontró y se corrigió

- Un dato de taller faltante (altura de manilla, enlace de stock, compra de un
  kit o una fijación) hacía fallar la emisión de la cotización. Ahora la
  cotización se sella «solo cotización» y el servidor registra el motivo.
- La importación de compras no escribía el enlace físico de stock de las barras.
- Ninguna vía de taller podía declarar la compra de una fijación ni de los
  componentes de un kit.
- La altura de manilla declarada por la serie (con su fuente) se pedía confirmar
  como si fuera un punto medio genérico.
- Los accesorios quedaban sin declarar; la preparación propone «Sin accesorios
  requeridos», editable.
- Los correos mostraban «P-000044 · REV-A»; ahora «Obra N° 44 · revisión A».

## Pendiente conocido

- El área máxima del termopanel (2,6 m²) es el valor de referencia DVH 4 + 4
  rotulado como dato de ensayo; un taller real lo toma de su proveedor.
- Los documentos de taller (OT por ventana, vidrios, montaje, checklist) siguen
  en P12d-documentos.
