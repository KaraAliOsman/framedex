# Documentos, materiales y operación diaria

[Volver al plan](README.md)

## Diseñar para quien recibe el resultado

Un cliente quiere entender qué compra; quien corta necesita barra, pieza, longitud
y ángulo; quien arma necesita encuentros y destino; quien compra necesita faltante,
variante, unidad y proveedor. Una plantilla universal expone demasiado a unos y
omite lo importante para otros.

La identidad del producto, la revisión y los datos del motor son comunes. La
composición del documento y la acción de cada pantalla dependen del destinatario.

## PDF revisados y límites

Se inspeccionaron cotizaciones existentes `casa-DOC-01-REV-B.pdf` y
`taller-DOC-01-REV-B.pdf`. La cotización de casa contiene 12 posiciones en ocho
páginas. Se revisaron visualmente portada, resumen, detalle y cierre. Es legible
y tiene alineación consistente; los problemas son jerarquía, tamaño del producto,
repetición y aprovechamiento del papel, no que todo el contenido sea inútil.

Además se renderizaron, sin emitir ni persistir una orden nueva, documentos desde
el plan existente `OT-P-000010-REV-B-01`: corte (7 páginas), producción (24) y
etiquetas (8). Corresponde a cuatro unidades fijas de 1 020 × 1 020 mm en fixture.
La lectura se hizo con contexto autenticado/RLS del manager y transacción de solo
lectura. No se cambió la orden, no se liberó fabricación ni se envió nada.

El número de páginas caracteriza este caso, no toda la producción. La revisión
visual fue por páginas representativas, no una inspección de cada página de
todos los documentos. Los archivos completos quedan temporales en `.run/`;
se conservan imágenes propias seleccionadas sin enlaces de acceso al portal.

## Cotización comercial

### Problemas observados

- Portada con mucho vacío y poco protagonismo del producto.
- Dibujos pequeños respecto de la hoja; tabla de resumen sin miniaturas.
- Detalles de medidas de paños repetidos y texto técnico con el mismo peso.
- Condiciones/total/aceptación separados por una secuencia que exige recorrer
  varias páginas para comprender el conjunto.
- Enlace largo al portal; el ejemplo local no representa una URL productiva.
- «Abrir» descarga sin una vista previa integrada en el flujo observado/código.

### Composición propuesta

| Zona | Contenido | Intención |
|---|---|---|
| Cabecera breve | Empresa, cliente, obra, fecha, revisión y vigencia | Identificar sin gastar una página. |
| Resumen comercial | Total, alcance, unidades, instalación/entrega si aplica | Entender la propuesta rápidamente. |
| Posiciones | Miniatura grande, código, recinto, cantidad, medidas, apertura, material, vidrio y caras | Comparar lo que se está comprando. |
| Importes | Unitario, cantidad, neto/IVA/total según política | Evitar ambigüedad comercial. |
| Condiciones | Plazo, pago, exclusiones, medición y aceptación | Saber qué ocurre después. |
| Detalle opcional | Especificación técnica o térmica respaldada | Atender al profesional sin saturar al cliente habitual. |

Dos composiciones razonables: resumen compacto para pocas ventanas y ficha
detallada para una obra compleja. No ofrecer veinte plantillas mediocres. La
identidad del fabricante/empresa se respeta; la personalización inicial se limita
a datos y marca, no a un editor de diseño que convierta cada propuesta en otro
trabajo.

No fijar un objetivo universal de páginas. La ventana más compleja necesita más
espacio; una tabla de una fila no necesita su propia hoja salvo razón operativa.

## Visor y portal

Preparar propuesta abre un espacio con vista previa, datos pendientes y acción
Emitir. Una vez emitida, se ve revisión/fecha/alcance, descargar, imprimir y
preparar envío. Cambiar el diseño crea una revisión nueva; el documento anterior
no se reinterpreta con catálogo mutable.

El portal muestra el mismo producto, acabados y características, con precio y
condiciones legibles en teléfono. El cliente puede comparar alternativas sin
tener que entender módulos, BOM o trabajos IA. Aceptación, pago y firma/consentimiento
si aplica deben corresponder a la revisión exacta y a capacidades realmente
conectadas. No confundir una simulación fiscal o de pago con un resultado externo.

## Materiales: dibujo y cantidades juntos

```text
P01 · Cocina · Revisión B             Alcance: 4 unidades
┌───────────────────────────┬────────────────────────────────────┐
│ Ventana con miembro       │ Perfiles   Vidrio   Herrajes       │
│ o vidrio resaltado        │ Material / variante / cantidad     │
│                           │ pieza → corte → barra de origen   │
│ clic = localizar fila     │ fila = localizar en el producto    │
└───────────────────────────┴────────────────────────────────────┘
Ver: por ventana | compra total | corte y sobrantes
```

| Necesidad | Presentación |
|---|---|
| Entender el BOM | Nombres, miniaturas/sección y función antes del SKU largo. |
| Saber cuánto | Distinguir por unidad, por posición y total de obra/lote. |
| Comprar | Unidad comercial y conversión respaldada; barra/planchas/caja/unidad distintas. |
| Verificar | Cantidad exacta y fuente del resultado, sin recalcular en frontend. |
| Localizar pieza | Selección cruzada con miembro, vidrio o herraje. |
| Comparar cambio | Qué material cambia, delta de costo/precio autorizado y consecuencias. |
| Exportar | Documento/planilla con revisión y agrupación elegidas. |

La agrupación usa identidad técnica completa: artículo, acabado/caras, especificación,
largo/formato, unidad y versión cuando corresponda. Dos filas parecidas no se
suman solo porque comparten un nombre comercial.

## Corte, ensamblaje, vidrio y etiquetas

| Salida | Mantener | Rediseñar |
|---|---|---|
| Corte por barra | Secuencia, ángulos, largo, sobrante, balance y origen | Encabezado por material/variante; identificar pieza y destino con claridad. |
| Pack de producción | Identidad, revisión, datos de pieza y trazabilidad | Quitar portada casi vacía; ordenar por tarea; evitar anexos repetidos sin necesidad. |
| Ensamblaje | Mapa de unidad y tabla de piezas | Callouts cortos, gutters para anotación, leyenda y encuentros ampliados. |
| Acristalamiento | Medidas, composición, cantidad y destino | Alcance por unidad/lote explícito; agrupar filas y no desperdiciar la hoja. |
| Pedido a proveedor | Referencias, unidades, cantidades, plazos | Agrupar por proveedor, variante y unidad de compra; no mezclar costo privado en copia comercial. |
| Etiqueta | QR y código humano | Miniatura de destino, orientación útil, jerarquía para lectura rápida y formato físico real. |
| Instalación/entrega | Identidad de unidad y evidencia | Checklist breve, croquis/ubicación, recepción y observaciones. |

### Fallo de ensamblaje que debe resolverse

En la página 13 del pack observado, los identificadores laterales quedan cortados
y otros se superponen con el marco. [Evidencia](evidencia/pdf-ensamblaje.png).
El origen a revisar es `_unit_map_svg` en `backend/production/pack.py`.

La solución es estructural: calcular el espacio de anotaciones, usar llamadas
breves (por ejemplo 1, 2, 3) y resolver su correspondencia con códigos completos
en leyenda. No reducir toda la fuente hasta que quepa. Añadir detalle de junta
cuando el dibujo general no la explica.

### Paginación y papel

Agrupar información que se usa junta; mantener encabezados con sus filas; repetir
cabecera útil al continuar una tabla; evitar renglones huérfanos; no partir una
ventana ilegiblemente. Impresión de taller con contraste suficiente en blanco
y negro. Los formatos de etiqueta y sus márgenes se ajustan al equipo real; un
QR legible en pantalla no acredita lectura sobre impresora térmica.

Los documentos exactos de corte ya son más útiles que el pack general observado.
Conservarlos como base y mejorar vínculos/jerarquía, en lugar de reemplazarlos
por una presentación bonita que pierda datos necesarios.

## Compras

Entrada: «Qué falta para las órdenes seleccionadas». Tabla accionable por
proveedor/material, con necesidad, cubierto, pendiente, unidad, fecha y precio
disponible. Stock suficiente se resume aparte; comprar cero no domina la lista.

Asignar proveedor/precio puede ser por grupo. Los datos faltantes se resuelven
donde bloquean una compra, no como una colección de formularios para todo el BOM.
Antes de enviar: cantidades, unidades, destinatario y condiciones revisables.
La IA prepara; la persona envía o confirma la consecuencia correspondiente.

Recepción: buscar OC o escanear → cantidades recibidas/dañadas → ubicación →
registrar diferencias. No exigir recapturar las líneas completas. La reserva y
disponibilidad se muestran por la revisión/orden que las utiliza.

## Inventario y retazos

En la muestra existen filas visualmente idénticas. El código utiliza identidad
de artículo/variante; la solución comienza por mostrar las diferencias que hoy
pueden estar ocultas. No se propone deduplicar registros sin investigarlos.

Vista de material con acabado, largo/formato, unidad comercial, disponible,
reservado, por recibir y ubicación. Desplegar lotes/variantes cuando haga falta.
Los retazos tienen largo útil, material, acabado, ubicación y origen; escanearlos
permite usarlos/moverlos con el flujo de stock autorizado.

Registrar un ajuste requiere motivo y consecuencia, sin una pantalla contable
innecesaria. Historia detallada bajo demanda. Las alertas de antigüedad sirven
para decidir, no para añadir un banner fijo en cada visita.

## Planta y estaciones

Una cola de trabajo debe responder qué se hará, para qué obra, qué bloquea y cuál
es la siguiente acción. El tablero observado con 175 OT en una columna se vuelve
una lista muy larga; el número de tarjetas no explica la carga.

| Vista | Comportamiento objetivo |
|---|---|
| Encargado | Agrupar por obra/lote, fecha, carga y bloqueos; entrar a unidades cuando se necesita. |
| Corte | Material/barra actual, siguiente pieza y etiqueta; registrar sobrante real con identidad. |
| Armado | Ventana/unidad grande, mapa, encuentros, piezas e instrucción relevante. |
| Vidrio | Composición, tamaño, destino y verificación. |
| Calidad | Chequeos primero, producto visible, aceptar/rechazar y causa; corte como consulta. |
| Embalaje | Unidades completas, accesorios, identificación y destino. |

Conservar permisos y transiciones; una acción más directa no habilita saltos
físicos imposibles. Remakes/reposiciones mantienen relación con pieza, causa y
orden original. No inflar la portada de una OT con todos los estados históricos.

## Medición, despacho, terreno y postventa

- **Medición:** identificar vano/recinto, tomar medidas necesarias y distinguir
  del tamaño de fabricación. Mostrar qué deriva el sistema y qué se confirma.
- **Despacho:** seleccionar salida, revisar unidades/embalaje, ruta/vehículo si
  aplica y comprobante. La identidad que escanea el taller sirve en obra.
- **Instalación:** agenda por rol, croquis/foto, checklist y recepción. Guardado
  local/sincronización explican qué está pendiente, sin mostrar una cola técnica
  como interfaz principal.
- **Postventa:** buscar por cliente/obra/etiqueta; registrar problema sobre la
  ventana concreta; conservar revisión instalada y relación con rectificación.
- **Vacíos:** al encargado ofrecer planificar; al instalador mostrar que no tiene
  visitas asignadas y el camino adecuado. No usar el mismo mensaje para todos.

## Clientes, cobros y negocio

| Área | Prioridad de experiencia |
|---|---|
| Clientes | Búsqueda rápida, creación breve, obras/propuestas/pendientes y contacto. Datos fiscales y fusión en contexto avanzado. |
| Precio y margen | Explicar la diferencia entre costo, venta, descuento e impuesto; comparar alternativas sin inventar números. |
| Cobranza | Qué vence, cuánto está verificado y siguiente acción. Preparar recordatorio/recibo con revisión humana de envío. |
| Fiscal | Estado de integración y documento real o simulación claramente distintos. No pedir certificados para dibujar. |
| Analítica | Qué obra pierde margen, qué material falta, dónde se atasca la producción y qué cobro requiere acción. |
| Empresa | Catálogos/precios/equipo/conexiones agrupados por tarea; billetera y plan de plataforma en administración. |
| Notificaciones | Agrupar misma causa; distinguir error/bloqueo de un aviso informativo; enlace al trabajo concreto. |
| Búsqueda | Obra, cliente, ventana, orden y pieza con nombres/códigos humanos; no exigir un UUID. |

La planificación cubre estas áreas aunque no se hayan operado todas en esta
auditoría. El foco inicial es la ruta diseño–venta–taller; después se extiende la
misma calidad al resto, sin borrar capacidades solo porque estén mal presentadas.
