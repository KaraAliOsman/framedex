# P04 · Precio simple y automático

**Rama:** `gpt/dk2-p04-precio-simple` · **Depende de:** P01 · **Siguiente:** P05

## Objetivo

Que cada ventana tenga precio **en cuanto la serie es cotizable**, calculado por
el motor con una política simple que el dueño entiende en una pantalla. Que
desaparezca «Falta calcular el precio» del flujo normal.

Especificación: `03-catalogo-y-calculo.md` §8. Revisa `backend/pricing/`,
`engine/src/dekopen_engine/pricing.py`, `price_workspace.py`, `commercial.py` y
`frontend/src/features/pricing/`.

## Qué construir

1. **Empresa › Cómo calculo mis precios** (una pantalla): costo de materiales
   (de los precios de la serie), mano de obra (por m² o por ventana), instalación
   (por m² o por ventana), margen % y redondeo. Vista previa en vivo con una
   ventana de ejemplo mostrando el desglose. Valores iniciales sugeridos y
   editables.
2. **Precio automático:** al crear o cambiar una ventana en una serie QUOTABLE,
   el backend pide al motor el precio con la política simple y lo guarda como
   **precio vigente de trabajo** (no emitido). El total de la obra se actualiza
   en vivo. La «aplicación» formal del precio se registra automáticamente al
   **emitir** la cotización (revisión inmutable), no como paso manual.
3. **Modo avanzado** (listas con vigencia, recargos por color, matrices, bandas de
   margen y aprobación de descuentos — lo que ya existe): oculto tras un
   interruptor «Usar precios avanzados» en Empresa. Si está activo, sustituye a
   la política simple con la misma regla de automatismo.
4. **Desglose del precio** («¿De dónde sale?») como popover desde el precio de
   la ventana: materiales, mano de obra, instalación, margen, supuestos.

## Criterios de aceptación

- [ ] Prueba del motor: política simple con casos dorados nuevos (ventana fija y
      abatible PRO6004 con precios de prueba) → precio exacto en `Decimal`.
- [ ] e2e: crear obra con 3 ventanas en PRO6004 → total visible sin ningún clic
      de «aplicar»; cambiar margen en Empresa → el total de una obra en
      borrador se recalcula; una cotización ya emitida no cambia.
- [ ] Cero apariciones de «Falta calcular el precio» en el flujo de una serie QUOTABLE.
- [ ] Todo verde; wiki (`product/price-workspace.md`) y ESTADO.md actualizados.
