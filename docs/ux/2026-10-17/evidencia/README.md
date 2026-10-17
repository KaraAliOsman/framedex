# Evidencia seleccionada · auditoría UX 17-10-2026

[Volver al plan](../README.md)

Capturas propias del producto y páginas renderizadas de documentos del fixture.
Se conservan doce imágenes de la auditoría inicial y seis de la implementación,
sin convertir toda la exploración temporal en documentación versionada.

## Procedencia y autoridad de la auditoría inicial

- Navegador: stack REVIEW reutilizado en `127.0.0.1:5179`, roles de estimación y
  encargado de taller. Viewports de escritorio de aproximadamente 1 280 × 720.
- **El SHA del build que sirven los contenedores no se verificó.** Las capturas
  muestran el producto de esa sesión; el código se inspeccionó por separado en
  `edcfd2844d2c2fc7cbb0d3b543b50e9089ab9b3f`.
- Datos DEMO/sintéticos; no acreditan fabricación ni operación de una empresa real.
- PDF comercial: artefacto existente `casa-DOC-01-REV-B.pdf`, página 2 de 8.
- PDF de taller: renderizados on-demand de un plan existente, en lectura
  autenticada/RLS sin escrituras. No se emitió una revisión ni orden nueva.
- Se preservaron sesiones, stack, bases y los diseños originales. La propuesta IA
  de ancho se descartó; su job/historial de consulta puede permanecer registrado.
- Se evaluaron ambos temas y se restauró el tema oscuro inicial. Estas imágenes
  documentan el estado previo, no la apariencia propuesta.
- `manifest.json` registra archivo, origen temporal, bytes y SHA-256. Las imágenes
  se copiaron sin editar; la extensión se ajustó a JPEG/PNG según los bytes
  devueltos por la captura, sin recomprimir. Los originales permanecen en
  `.run/ux-audit-2026-10-17/` en esta estación.

## Índice

| Imagen | Qué permite revisar |
|---|---|
| [proyecto.jpg](proyecto.jpg) | Cabecera, fases y pestañas que preceden a las ventanas. |
| [editor-2d.jpg](editor-2d.jpg) | Lienzo, herramientas, cotas e inspector. |
| [editor-3d.jpg](editor-3d.jpg) | Nogal plano observado, encuadre y capas de controles. |
| [ia-cambio-simple.jpg](ia-cambio-simple.jpg) | Propuesta correcta de ancho y carga de ceremonia/advertencias. |
| [catalogo-importador.jpg](catalogo-importador.jpg) | Plantilla primero y controles de archivo redundantes. |
| [produccion.jpg](produccion.jpg) | Concentración de OT y tarjetas sin referencia visual fuerte. |
| [compras.jpg](compras.jpg) | Jerarquía de necesidades, lenguaje y materiales con compra cero. |
| [inventario.jpg](inventario.jpg) | Filas de apariencia idéntica; no demuestra duplicación de registros. |
| [hoy.jpg](hoy.jpg) | Tareas repetidas por causa/obra en el punto de entrada. |
| [pdf-comercial.png](pdf-comercial.png) | Resumen legible sin miniaturas y aprovechamiento de página. |
| [pdf-corte.png](pdf-corte.png) | Información de corte útil que debe conservarse. |
| [pdf-ensamblaje.png](pdf-ensamblaje.png) | Códigos cortados y solapados en plano de ensamblaje. |

Las fuentes de competencia se citan mediante enlaces y tramos de vídeo en
[la investigación](../02-competencia.md). No se redistribuyen vídeos ni catálogos
de terceros. No se incluyen PDF completos con acceso al portal, tokens, credenciales
o archivos de sesión. No se hicieron pruebas responsive nuevas en esta auditoría.

## Ejemplos que sostienen el diagnóstico

### El objeto queda detrás de controles

![Proyecto observado con fases, pestañas y controles antes de las ventanas](proyecto.jpg)

### La textura seleccionada no se reconoce como madera

![Vista 3D exterior observada con acabado Nogal marrón plano](editor-3d.jpg)

### El plano pierde legibilidad en los códigos de pieza

![Página 13 del pack de producción con anotaciones cortadas y superpuestas](pdf-ensamblaje.png)

## Implementación autorizada · 17-10-2026

Las capturas siguientes pertenecen a la construcción de `codex/v1-experiencia`,
desde `edcfd2844d2c2fc7cbb0d3b543b50e9089ab9b3f`. REVIEW se reconstruyó desde
este checkout sin ejecutar fixture/reset. Se seleccionaron imágenes de builds
sucesivos de la integración final; las anteriores no se atribuyen al build nuevo.
El [registro](../10-implementacion.md) separa código, ejercicios reales y límites.

Los datos son sintéticos. La IA se ejercitó como estimador; el importador se
inspeccionó como jefe de taller. Se restauró la sesión de estimación. El PDF
privado de `P-000016` se preparó y revisó sin emitir ni enviar. La captura del
importador muestra la entrada y sus permisos; no acredita la conversión completa
de un catálogo de fabricante. Las texturas 3D son ilustrativas.

| Captura | Qué permite revisar |
|---|---|
| [Editor 2D](implementacion/editor-2d.jpg) | Lienzo, uniones, cotas, precio indicativo e inspector progresivo. |
| [Exterior 3D](implementacion/editor-3d.jpg) | Vista exterior Nogal con ingletes; representación ilustrativa. |
| [Muestra IA](implementacion/ia-propuesta.jpg) | Precio del motor y continuidad hacia la preparación del PDF. |
| [PDF integrado](implementacion/pdf-revision.jpg) | Página 2 del PDF real, dibujo mayor, destinatario e importe; sin emisión. |
| [Materiales](implementacion/materiales.jpg) | Relación entre dibujo y materiales en una ficha amplia. |
| [Catálogo desde PDF](implementacion/catalogo-pdf.jpg) | PDF primero y plantilla secundaria con rol autorizado. |

[Manifiesto de implementación](implementacion/manifest.json): formato, dimensiones
de imagen, bytes y SHA-256. Los archivos son JPEG devueltos por CUA; solo se corrigió
la extensión, sin editar ni recomprimir. Las dimensiones del archivo no acreditan
por sí mismas una matriz de dispositivos. No se incluyen QR de acceso, PDFs
completos con capacidades, credenciales, mensajes de acceso ni sesiones.
