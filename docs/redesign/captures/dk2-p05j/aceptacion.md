# P05j · Documentos y taller en lenguaje de producto

Verificado el 22-10-2026 en `gpt/dk2-p05j-documentos-taller`, sobre P05i
`bca5adff`. API 8010, vista previa 5175 y PostgreSQL aislado. Se conserva
REVIEW y el checkout del dueño. El frontend usa el build ya verificado de P05h.

## Cambio

Veintiún módulos de documentos, corte, CNC y terreno distinguen ventana de
obra, paño del dibujo, ubicación en barra y revisión emitida. El comprobante
conserva su sentido financiero; «Juntas estancas» describe la comprobación de
instalación. Los pendientes piden completar o explican la ausencia histórica.

La lectura del marcador antiguo «Sin dato» sigue omitiendo campos vacíos en la
cotización; una prueba protege esa compatibilidad y la prosa del cliente. No
se transforman snapshots ni bytes emitidos. El CSV de vidrio conserva su
encabezado canónico «Posición» para los consumidores existentes; PDF y pantalla
usan ventana. SQL, claves y literales numéricos permanecen idénticos por AST.

## Verificación

- 288 pruebas dirigidas de documentos, cotización, corte, CNC, producción y
  cobranza aprobadas; 19 de cotización vuelven a pasar tras la prueba histórica.
- 74 integraciones PostgreSQL aprobadas: emisión, vista previa guiada, corte,
  CNC, terreno, repetición de solicitudes e inmutabilidad y privacidad de PDF.
- Nueve PDF de la ruta real de render, rasterizados con Poppler. Revisión de
  sus 49 páginas: cotización 1 ventana (2), 100 ventanas y nombres de 120
  caracteres (27), corte agrupado (4), etiquetas A4 (1) y rollo 100 × 50 (8),
  comprobante (1), factura interna (1), acta (1) y pedido de vidrio (4).
- Se comprueban importes exactos, fuentes embebidas, límites y colisiones de
  tablas, códigos, secuencia, cierres de barra y lectura de QR en las pruebas.
  El texto extraído de las nueve muestras no contiene las voces antiguas.

- Cuatro E2E aprueban catorce superficies a 1440 × 900 y 390 × 844 y el
  flujo de precio/cotización: tres ventanas, nueva política, PDF revisado,
  emisión y mismos bytes después de cambiar margen. Incluye 500 ventanas,
  nombres/montos extremos, 320 px, texto al 200 %, teclado y axe.
- Ruff, Django check, guardas y comparación de goldens por bytes aprobados.
  Documentos cargan en 1.007–1.059 ms, taller en 593–627 ms y terreno en
  984–994 ms. Precio de obra: LCP 924–956 ms, CLS 0,00086–0,0233. Son medidas
  locales con trabajo concurrente y sin throttling. Montaje 9,0–12,9 s y
  servicios 2,2–4,4 s siguen como deuda de rendimiento P11.

## Pantallas

| Superficie | 1440 × 900 | 390 × 844 |
| --- | --- | --- |
| Documentos | [Escritorio](documents-1440.png) | [Móvil](documents-390.png) |
| Taller | [Escritorio](production-1440.png) | [Móvil](production-390.png) |
| Terreno | [Escritorio](field-1440.png) | [Móvil](field-390.png) |
| Comprobantes | [Escritorio](payments-1440.png) | [Móvil](payments-390.png) |

La captura automática del visor de escritorio puede preceder a su pintura.
La validación visual de las páginas usa los PDF descargados y Poppler; el
E2E comprueba los bytes emitidos y su SHA-256. No se afirma que una captura
oscura del iframe acredite la página renderizada.

## Evidencia impresa

| Documento | PDF | Páginas seleccionadas |
| --- | --- | --- |
| Cotización | [1 ventana](cotizacion.pdf) | [Dibujo](cotizacion-1.png), [resumen](cotizacion-2.png) |
| Escala | [100 ventanas](cotizacion-100.pdf) | [Inicio](cotizacion-100-01.png), [total](cotizacion-100-27.png) |
| Corte | [Pack](corte.pdf) | [Barras](corte-1.png), [lámina](corte-4.png) |
| Etiquetas | [A4](etiquetas-a4.pdf), [rollo](etiquetas-rollo.pdf) | [A4](etiquetas-a4-1.png), [100 × 50](etiquetas-rollo-1.png) |
| Cobranza | [Comprobante](comprobante.pdf), [factura interna](factura-interna.pdf) | [Comprobante](comprobante-1.png), [factura](factura-interna-1.png) |
| Terreno | [Acta](acta-terreno.pdf) | [Recepción](acta-terreno-1.png) |
| Vidrio | [Pedido](pedido-vidrio.pdf) | [Cortes](pedido-vidrio-1.png), [etiquetas](pedido-vidrio-4.png) |

## Límites

Catálogo, precios, firmas y obras son fixtures sintéticos. El pack conserva un
aviso de retazo histórico sin dirección; imprimir no crea stock. La firma del
acta es el PNG mínimo de la fixture, no una firma de cliente real. La factura
interna conserva su declaración de documento no tributario. Esta revisión no
certifica Proline, maquinaria ni rendimiento térmico. Chromium emula el móvil;
no se dispone de un teléfono físico. No se incorpora movimiento.

P05 continúa con diagnósticos del motor y los mensajes restantes del servidor.
P06–P11 siguen pendientes. Las fusiones requieren los cuatro controles verdes
del head vigente.
