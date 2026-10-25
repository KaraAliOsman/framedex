# P12b · Proline PRO6004 real, medido contra la OT 385 del dueño

Verificación local del 25-10-2026 en `claude/dk3-p12b-proline`, con el stack
aislado `dekopen-ci`. Fuentes, ambas aportadas por el dueño:

- **Plantilla de corte de ventanas PVC Proline** (Aluminios 2000, 25 págs.,
  huella `bf16d500…`): reglas del fabricante (marco 1000 → 1005, hoja 933,
  refuerzos 892 y 788, vidrio 902 y 798).
- **OT N° 385** generada por NuveraPro en el taller del dueño (7 págs., huella
  `7ce2fd45…`): cortes reales de cinco ventanas, herrajes Vorne y códigos de compra.

## Lo que quedó demostrado

1. **El motor reproduce la OT al 0,00 mm.**
   [`test_gold_cases_proline.py`](../../../../engine/tests/test_gold_cases_proline.py)
   calcula los ítems 04 y 05 de la OT. Coinciden marcos, travesaños, hojas,
   junquillos, vidrios y refuerzos de marco, travesaño y hoja:
   - ítem 04 (1193 × 1350): hojas de 554,5 × 1284, vidrios de 418,5 × 1148 y refuerzos de 408,5 / 1138;
   - ítem 05 (2385 × 900): vidrios de 1118,5 × 802.
2. **La biblioteca prepara una serie real.** «Preparar PRO6004» crea la serie
   con la hoja de corte citada:
   - perfiles Pro01, Pro521, Pro03 y Pro05;
   - aceros Pro-R1 y Pro-R2 con sus descuentos;
   - junquillo para termopanel de 20 mm;
   - aperturas fija y abatible;
   - dos kits Vorne.

   La prueba de integración
   [`test_reference_prepare.py`](../../../../backend/tests/integration/test_reference_prepare.py)
   dibuja el ítem 05 con esa serie y obtiene exactamente los cortes y aceros impresos en la OT.
3. **La aceptación completa usa esa serie.** `proline-acceptance` corre a 1440 y
   390 px:
   - registro, taller y segundo factor;
   - PRO6004 desde la biblioteca;
   - ficha de compra con los códigos de la OT (barras, aceros, termopanel);
   - lista de precios;
   - ventana de prueba de 800 × 1400 mm comparada con 806 mm;
   - una obra con dos fijos y un abatible de 800 × 1400;
   - emisión por correo y aprobación del cliente.

   Total ~52 s de máquina por tamaño ([`tiempos.json`](tiempos.json)).

## Lo que la prueba encontró y se corrigió

- Una serie sin carta de colores compra sus perfiles como barras simples
  (`profile_purchase_mappings`). Ninguna importación de taller podía escribirlas,
  así que una serie blanca importada nunca cotizaba. La hoja «Colores y SKU por color»
  ahora las declara para esas series (migración `20270212000200`, pgTAP 264).
  Las políticas antiguas de miembros quedan limitadas a `authenticated`.
- En móvil, el selector de aperturas se abría detrás de la hoja del inspector.
  Los popovers suben por encima de hojas y diálogos (`--z-popover: 65`).

## Pendiente conocido

- La hoja interior Pro02 lleva un junquillo 13 mm más largo que la exterior
  Pro521 (441,5 frente a 428,5). Las reglas de junquillo van por espesor de vidrio
  y no por hoja; la prueba lo marca `xfail` estricto.
- La OT lista un segundo acero (Pro-R19) en la hoja exterior; el motor modela un
  acero por perfil.
- Los kits Vorne cubren hojas de 400–600 y 1200–1400 mm de alto, los rangos
  que prueba la OT. Otras alturas necesitan los kits correspondientes.
- Los precios de la lista son del taller de ensayo; la OT no trae costos.
- La masa del tornillo de refuerzo (2 g) es una estimación marcada para confirmar.
