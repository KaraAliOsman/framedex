# Experiencia y diseño · DEKOPEN 2

Dirección de diseño con la vara de Pentagram (claridad tipográfica, sistema
riguroso), Apple (respuesta inmediata, materiales, movimiento con propósito),
Figma (lienzo + inspector, paneles estables) y Linear («no competir por atención
no ganada», «la estructura se siente, no se ve»). La base visual de las PR
160–162 (tokens, IBM Plex, `#F5F5F7`, acento teal, controles segmentados) se
conserva; lo que cambia es la **arquitectura de información** y los **flujos**.

## 1. Arquitectura de información

Cinco destinos en la barra lateral, siempre los mismos para todos los roles
(los que no aplican a un rol se ocultan, no se deshabilitan):

| Destino | Qué contiene | Rol principal |
|---|---|---|
| **Hoy** | Lo que hay que hacer ahora: cotizaciones por enviar o vencer, aceptaciones, atrasos de taller, aprobaciones de la IA | Todos |
| **Obras** | Cotizaciones y obras en una sola lista con etapas (Cotizando → Enviada → Aceptada → En taller → Instalada → Cobrada); clientes dentro de cada obra | Vendedor, dueño |
| **Taller** | Órdenes, corte, estaciones, compras, inventario, despachos | Jefe de taller, operario |
| **Catálogo** | Fabricantes → series (ficha de serie), vidrios, herrajes, colores, plantillas | Dueño, técnico |
| **Empresa** | Datos, usuarios, precios («cómo calculo mis precios»), documentos, plan, IA y funciones avanzadas | Dueño |

- **Clientes** deja de ser destino principal: se accede desde la obra y desde la
  búsqueda (Ctrl K). Analítica pasa a **Hoy** (tarjetas) y a Empresa › Informes.
- Arriba a la derecha, siempre: **búsqueda/comandos (Ctrl K)** y **Pedir a DEKOPEN** (agente).

## 2. Flujos principales (camino feliz)

### F1 · Primer uso (≤ 15 minutos hasta la primera cotización real)
1. Registro con correo (enlace mágico) → nombre del taller → país (CLP/IVA preconfigurados).
2. «¿Qué series fabricas?» — buscador de la biblioteca LatAm con logos de
   fabricantes. Marcar Proline PRO6004.
3. «Pon tus precios» — pegar desde Excel o subir la lista del proveedor; la IA mapea columnas.
4. «Revisa una ventana de prueba» — despiece 1200 × 1100 lado a lado con columna de confirmación.
5. «Crea tu primera cotización» — abre el flujo F2 con un cliente de ejemplo editable.

### F2 · Nueva cotización (tres puertas, una sola pantalla de destino)
- **Dibujar:** elegir tipología de la biblioteca → medidas → listo.
- **Describir:** pegar el WhatsApp/correo o dictar → la IA crea las ventanas.
- **Desde plano o foto:** subir → la IA extrae el cuadro de vanos → revisar diferencias.

Todas terminan en la **mesa de la obra**: lista de ventanas a la izquierda,
ventana seleccionada al centro (dibujo), inspector a la derecha, total arriba
siempre visible y un botón principal **Enviar cotización**.

### F3 · Enviar y cerrar
**Enviar cotización** → vista previa del PDF real a pantalla completa con edición
en línea de condiciones → elegir canal (correo, WhatsApp con enlace, descarga) →
el cliente abre el portal, elige alternativa, firma y paga el anticipo →
DEKOPEN avisa en **Hoy** y propone **Pasar a taller**.

### F4 · Taller
**Pasar a taller** crea la OT con la hoja de corte optimizada, los pedidos de
vidrio y perfiles propuestos y las etiquetas QR. El operario en tablet ve su
estación: pieza actual grande, siguiente pieza, botón **Hecho**.

### F5 · Instalación y cobro
El instalador ve su agenda del día en el celular, marca cada ventana instalada
con foto y firma del cliente. El saldo se cobra con enlace de pago.

## 3. Pantallas clave (especificación de layout)

### 3.1 Hoy
- Saludo breve + fecha. Tres tarjetas de métricas como máximo (por enviar,
  aceptadas esta semana, atrasos).
- Cola única «Para hacer» con filas accionables: verbo + objeto + botón
  («Enviar cotización a Pérez · Enviar»). Nada de tablas largas.
- Bandeja de la IA: «DEKOPEN preparó 2 cotizaciones · Revisar».

### 3.2 Obras (lista)
- Barra superior: título, búsqueda, filtro por etapa (control segmentado), botón **Nueva cotización**.
- Lista densa estilo Linear: nombre de obra, cliente, etapa (pastilla), ventanas,
  total, última actividad. Fila completa clicable. Sin tarjetas grandes.

### 3.3 Mesa de la obra (corazón del producto)
```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Obras   Casa Pérez · Ana Pérez        Total $3.480.000 IVA incl.  [Enviar cotización] │
├────────────┬──────────────────────────────────────────┬──────────────────┤
│ Ventanas   │                                          │ Inspector        │
│ ▢ V1 1800×1400  │         [ dibujo 2D con cotas ]          │ Serie  PRO6004 ▾ │
│ ▢ V2 1200×1100  │                                          │ Apertura  ◫ ▾    │
│ ▢ V3  600×600   │                                          │ Ancho  1800  mm  │
│ + Añadir       │      [2D | 3D]   [interior | exterior]      │ Alto   1400  mm  │
│            │                                          │ Vidrio 4-12-4 ▾  │
│            │                                          │ Color  Blanco ▾  │
│            │                                          │ Cantidad 2       │
│            │                                          │ ─────────────    │
│            │                                          │ $1.240.000       │
│            │                                          │ Ver despiece ›   │
└────────────┴──────────────────────────────────────────┴──────────────────┘
```
- Las cotas se editan **sobre el dibujo** (clic en la cota, escribir, Enter).
- Dividir: arrastrar desde el borde para crear montante/travesaño; o tecla.
- La biblioteca de tipologías aparece al crear una ventana y desde «Cambiar tipología».
- El 3D es una pestaña del lienzo, no un panel flotante.
- Los avisos del motor aparecen como **chips sobre la ventana afectada** con
  corrección propuesta («Hoja de 1450 mm supera el máximo de 1400 · Dividir»).

### 3.4 Ficha de serie (Catálogo)
- Cabecera: logo del fabricante, nombre, etiqueta de nivel («Lista para cotizar ·
  3 por confirmar»), botón **Ventana de prueba**.
- Pestañas: Perfiles · Reglas · Herrajes · Vidrios y colores · Tipologías · Precios.
- Cada pestaña es una **tabla editable** con origen por celda (punto de color) y
  pegado desde Excel. Encima de la tabla, una franja con lo pendiente y su acción.

### 3.5 Vista previa y envío de cotización
- PDF real a pantalla completa con zoom; columna derecha con condiciones
  editables (plazo, validez, anticipo, notas) que se reflejan al instante.
- Botón principal **Enviar**; secundarios Descargar y Copiar enlace.

### 3.6 Estación de taller (tablet, densidad taller)
- Pieza actual en grande: perfil, largo, ángulos, cantidad, OT y obra.
- Botones de 56 px: **Hecho**, **Problema**. Escaneo QR siempre disponible.
- Color solo para lo anómalo.

### 3.7 Portal del cliente
- Marca del taller, total grande, alternativas como tarjetas, dibujo de cada
  ventana con 3D, condiciones claras, botón **Aceptar y firmar**, pago del anticipo.

### 3.8 Agente (panel lateral)
- Conversación por obra, adjuntos arrastrables, tarjetas de progreso de cada
  tarea, recibo final con lo hecho, supuestos y «Deshacer todo».

## 4. Sistema de diseño (ajustes sobre lo existente)

**Tipografía:** IBM Plex Sans (UI), IBM Plex Mono solo para cotas en el lienzo y
códigos. Escala: 12 / 13 / 15 (cuerpo) / 17 / 20 / 24 / 32. Interletrado
negativo en títulos ≥ 24 px.

**Color:** fondo `#F5F5F7`, superficies blancas, texto `#1D1D1F` y `#565C62`,
acento teal (`--interactive`) solo para acciones y selección. Estados: ámbar
(sugerido/aviso), rojo (falta/error), verde (del manual/listo), azul (del taller).

**Densidad:** filas de 40 px en oficina, 56 px en taller; radios 8/12/16; sombras
solo de la escala (`--e2`, `--e3`, `--sheet`).

**Movimiento:** 160–220 ms, curva `cubic-bezier(0.23, 1, 0.32, 1)`; presionar
botón `scale(0.97)`; sin animación en acciones de teclado; respeta reduced-motion.

**Componentes clave:** tabla editable (tipo hoja), inspector de propiedades,
control segmentado, píldora de búsqueda, chip de aviso con acción, tarjeta de
tarea de la IA, etiqueta de origen (punto de color + texto), barra de comandos.

**Lenguaje (glosario obligatorio):**

| No decir | Decir |
|---|---|
| Autoridad, fuente, procedencia | Del manual · Del taller · Sugerido |
| Sellado, revisión sellada | Emitida (no se puede cambiar) |
| Sin dato | Falta — Completar / Sugerido — Confirmar |
| Encargo, recibo | Tarea, Resumen |
| Mesa de obra / Estudio | Obra (una sola vista; el modo amplio es «Pantalla completa») — **decisión pendiente del dueño**, ver §6 |
| Posición, vano | Ventana (o puerta) |
| Preparación documental | Condiciones de la cotización |

## 5. Calidad exigida (definición de terminado de diseño)

1. Cada pantalla responde en 3 segundos a «qué tengo que hacer ahora».
2. Un solo botón principal por región.
3. Ningún texto explicativo de más de una línea en el flujo normal; la ayuda va en «?».
4. Captura a 1440 × 900 y 390 × 844 sin desbordes ni texto cortado.
5. Contraste AA; foco visible; navegación completa por teclado en oficina.
6. `scripts/check_guards.py` y la [constitución](../../design/CONSTITUCION.md)
   en verde; donde la constitución contradiga este documento, se actualiza la
   constitución en la misma PR y se deja registro en el wiki.

## 6. Decisiones que necesitan al dueño

| Decisión | Propuesta | Por qué | Si el dueño dice que no |
|---|---|---|---|
| Mesa de obra + Estudio (decidido el 18-10) | Una sola vista «Obra» con modo pantalla completa | Dos vistas de la misma sesión duplican conceptos y botones; los mejores editores (Figma, Linear) tienen una sola superficie | Se conservan ambas, con el layout de §3.3 como Mesa y el editor amplio como Estudio |
| Popup global del copiloto (decidido el 18-10) | Barra Ctrl K + panel lateral por obra | El agente necesita espacio para progreso, recibos y adjuntos; el popup tapa el trabajo | Se conserva el popup y se le agregan progreso y recibos |
| Precios de DEKOPEN 2 | Tabla de la [estrategia](02-estrategia-producto.md) §4 | Ancla de mercado NuveraPRO/Luminio | Se usan los precios que defina el dueño |
