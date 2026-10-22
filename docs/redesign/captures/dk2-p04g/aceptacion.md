# P04g · Precio automático en la obra

Revisión del 22-10-2026 en `gpt/dk2-p04g-precio-obra`, sobre P04f
`bcc35e90`. Stack sintético propio: web 5175, API 8010 y Supabase 25421.
No se modificó REVIEW ni se enviaron mensajes a clientes reales. PRO6004 y
sus precios son datos sintéticos de ensayo, sin certificación de Proline.

## Recorrido y autoridad de las cifras

La cabecera, la colección y la sección Precio leen importes del backend.
Un borrador usa su precio vigente de trabajo; no recupera un total anterior
cuando el cálculo está bloqueado. READY permite preparar la cotización;
PENDING muestra el importe por aprobar y conserva la aprobación del dueño.
La moneda acompaña al precio, incluyendo USD. Ninguna fórmula nueva vive en
la interfaz.

Desde el importe de cada ventana se abre «¿De dónde sale?». El dueño ve
materiales, merma, servicios, costo, utilidad, redondeo y política exacta.
El vendedor recibe solamente venta: la respuesta pública no agrega costos
ni política privada. Escape cierra y devuelve el foco al importe.
Sugeridos y series sintéticas se declaran explícitamente.

El flujo normal no pide Aplicar. Cotizar admite pendientes de fabricación
que el backend ya permite; conserva ubicación, condiciones comerciales,
confirmación de sugeridos de manilla, revisión del PDF y clic de emisión.
La fabricación sigue bloqueada si faltan sus antecedentes. El modo avanzado
permanece optativo y conserva su historial y decisiones.

`working-pricing.spec.ts` usa Magic Link y TOTP reales, crea tres abatibles
PRO6004 mediante la API ordinaria y compara el total con el motor. Cambia el
margen en Empresa, comprueba el nuevo borrador, prepara el PDF sin operación
aplicada, comprueba su SHA-256 y lo emite con la confirmación humana del
entorno sintético. Otro cambio de margen conserva versión, total y los mismos
bytes del archivo emitido. También se comprueban los precios de sus ventanas.

## Capturas y revisión visual

| Estado                             | Escritorio 1440 × 900                     | Móvil 390 × 844                     |
| ---------------------------------- | ----------------------------------------- | ----------------------------------- |
| Obra vacía                         | [Escritorio](desktop-empty.png)           | [Móvil](mobile-empty.png)           |
| Tres ventanas, precio automático   | [Escritorio](desktop-three-windows.png)   | [Móvil](mobile-three-windows.png)   |
| Desglose del motor                 | [Escritorio](desktop-breakdown.png)       | [Móvil](mobile-breakdown.png)       |
| Precio de la obra                  | [Escritorio](desktop-price-panel.png)     | [Móvil](mobile-price-panel.png)     |
| PDF y confirmación humana          | [Escritorio](desktop-reviewed-pdf.png)    | [Móvil](mobile-reviewed-pdf.png)    |
| Emitida, después de cambiar margen | [Escritorio](desktop-issued.png)          | [Móvil](mobile-issued.png)          |
| Quinientas ventanas                | [Escritorio](desktop-500-windows.png)     | [Móvil](mobile-500-windows.png)     |
| Desglose con importe extremo       | [Escritorio](desktop-large-breakdown.png) | [Móvil](mobile-large-breakdown.png) |

[1280 px](width-1280.png), [1024 px](width-1024.png),
[320 px](width-320.png) y [texto al 200 % en 320 px](text-200-percent.png).

La especificación P04 pide el precio simple y su desglose; no aporta un mockup
propio. Se conserva la jerarquía vigente: obra/cliente, total, acción de
cotización y ventanas. La mesa de tres regiones del mockup Main pertenece a
P06. No se adelanta ese cambio ni su decisión de vista única.

## Extremos, accesibilidad y correcciones

La segunda parte de cada E2E intercepta únicamente la lectura de detalle con
un DTO marcado «Ensayo visual»: 500 ventanas, nombres polacos/japoneses,
emoji, palabras sin espacios e importes grandes. Ningún importe de ese
ensayo se envía al backend. Se montan menos de 40 filas, la búsqueda encuentra
la ventana 500 y su importe abre el desglose. Se revisan además 0 y 3 ventanas
con datos reales del entorno de pruebas.

- Corregido contraste de código, seguimiento comercial, contador e índices.
  Axe A/AA/2.1 AA comprueba cabecera, colección, panel de precio y popover.
- Nombres y totales largos se ajustan al ancho. El listado deja de imponer
  mínimos de columna que ocultaban acciones; en móvil coloca las acciones
  bajo los datos. Texto al 200 % conserva lectura y controles sin desborde.
- El PDF emitido conserva precios de ventana: la lectura acepta las líneas
  de la política simple y las avanzadas, usando los importes congelados del
  motor y una allowlist de venta. No los deriva del catálogo actual.
- El Database Gate detectó una comparación histórica del reloj de cálculo en
  la clonación. `9223078d` exige que ese reloj avance y compara exactamente
  todos los demás campos del original. Se propagó a P04d, P04e y P04f.

| Constitución               | Resultado en el alcance P04                                                                             |
| -------------------------- | ------------------------------------------------------------------------------------------------------- |
| Tipografía, cifras y color | Importes tabulares, moneda explícita y decimales recibidos del motor; tokens existentes y contraste AA  |
| Jerarquía y controles      | Un destino principal por región; desglose desde el importe y ajustes avanzados bajo revelado progresivo |
| Estados y verdad           | Vacío con acción; cálculo bloqueado con causa; aprobación pendiente visible; emitidos conservados       |
| Accesibilidad              | Botones y regiones con nombre, foco visible y Escape; axe en los estados capturados                     |
| Movimiento                 | No se agrega animación ni se animan cifras; popover reutiliza el componente existente                   |
| Adaptación                 | 1440, 1280, 1024, 390 y 320 px, además de texto ampliado; sin desborde de página                        |
| Oficio y trazabilidad      | Materiales/servicios/margen a un clic, sugeridos visibles y fabricación con sus controles propios       |

## Validación y rendimiento

Dos E2E del flujo simple aprueban, uno por viewport; 43 unitarias UI y 39
integraciones de trabajo, emisión, PDF y clonación aprueban. Las cinco
integraciones de emisión se repitieron al corregir las líneas emitidas.
ESLint, tipos, Ruff, guardas, build y reproducción OpenAPI/orval aprobados.
La regresión E2E avanzada aprueba completa en 2 minutos: edición, aplicación,
dos revisiones emitidas, correo sandbox y conservación de los bytes del PDF.
Se ejecutó sobre el build de producción. El servidor Vite de desarrollo
observaba los HTML de las trazas en `.run` y recargaba la app durante el ensayo;
no se aumentó el límite ni se retiraron comprobaciones.

Observaciones locales del build de producción en Chromium sin throttling:
carga del precio 1,45 s en escritorio y 1,47 s en móvil; LCP 1,33–1,42 s;
CLS 0,0009–0,0233. El DTO visual de 500 ventanas carga en 1,62–1,80 s y
la búsqueda tarda 34–52 ms. Esta prueba de presentación no mide rendimiento del backend con
500 cálculos ni representa percentiles de producción. El aviso previo de
chunks grandes sigue reservado al cierre de rendimiento P11.

P04 espera sus cuatro controles y fusiones ordenadas después de P03. El
glosario global, la navegación y la mesa nueva corresponden a P05/P06.
