# P09 · Taller simple, compras propuestas e instalación móvil

**Rama:** `gpt/dk2-p09-taller` · **Depende de:** P07 · **Siguiente:** P10

## Objetivo

Al aceptar el cliente, un clic **Pasar a taller** genera todo lo necesario para
fabricar: OT, hoja de corte optimizada, etiquetas QR y pedidos de material
propuestos. El operario trabaja en tablet con una pieza a la vez; el instalador
cierra en el celular con foto y firma.

Especificación: `04-experiencia-y-diseno.md` §2 (F4, F5), §3.6. Mockup:
`mockups/Taller.dc.html`. Revisa `backend/production/`, `backend/purchasing/`,
`backend/inventory/`, `engine/src/dekopen_engine/{cutting,nesting,purchasing,inventory}.py`,
`frontend/src/features/{production,purchasing,field}/`.

## Qué construir

1. **Pasar a taller** (desde Hoy y desde la obra aceptada): exige serie
   MANUFACTURABLE (si no, muestra exactamente qué confirmar con enlace a la
   ficha). Crea la OT, ejecuta la optimización de barras con retazos del
   inventario, genera la hoja de corte (documento existente DOC-05 con diseño
   limpio), etiquetas QR y **pedidos propuestos** de perfiles y vidrios por
   proveedor (compra con clic humano).
2. **Estación (tablet, densidad taller):** pieza actual en grande (perfil, largo
   en mono 96 px, ángulos dibujados, cantidad, barra), siguiente pieza, barra
   optimizada dibujada con retazo, botones **Hecho** y **Problema** de 72 px,
   escaneo QR. Estaciones configurables (corte, soldadura, herrajes, vidriado,
   control, embalaje) con las existentes.
3. **Simplificación:** el tablero de producción para el jefe muestra OT por
   estación con progreso; las funciones avanzadas (CNC, cierres de costos) quedan
   en Empresa › Funciones avanzadas.
4. **Instalación móvil:** agenda del día, cada ventana con foto y firma del
   cliente, cierre de obra → saldo por cobrar con enlace de pago.

## Criterios de aceptación

- [ ] e2e: obra aceptada (fixture) → Pasar a taller → OT con hoja de corte y
      pedidos propuestos → operario marca 3 piezas en 1180 × 820 → instalador
      cierra con foto y firma en 390 × 844 → saldo en Hoy.
- [ ] La optimización usa retazos existentes y registra el retazo nuevo.
- [ ] Pasar a taller con una serie solo QUOTABLE muestra los pendientes exactos.
- [ ] `mobile-native` y `break-ui` aplicados; capturas comparadas con el mockup.
- [ ] Todo verde; wiki (`production-stations.md`, `purchasing-inventory.md`,
      `field-work.md`) y ESTADO.md.
