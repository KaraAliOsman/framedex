# Formato genérico de corte DEKOPEN

CSV y DXF describen el plan vigente de una OT. Son formatos genéricos de
DEKOPEN; no afirman compatibilidad con formatos propietarios de sierras,
mesas de vidrio ni CNC. La integración con una máquina requiere su perfil,
postprocesador y validación propios. Un plan invalidado rechaza la descarga.

Todos los milímetros se exportan como decimales exactos con punto decimal,
sin separador de miles. CSV usa UTF-8, encabezado y coma como delimitador;
una coma, comilla o salto de línea dentro de un campo se protege con comillas
dobles. `piece_label` es el código físico pegado a la pieza. Los IDs sirven
para trazabilidad técnica, no sustituyen su etiqueta.

La descarga comienza con un comentario `# dekopen order=… plan=… emitted=…`
que identifica la OT, el prefijo de huella del plan y la hora técnica de
exportación en UTC. Un consumidor debe omitir las líneas que empiezan con
`#` antes de leer el encabezado CSV. Los números y el orden de las filas
permanecen iguales aunque cambie la hora de exportación.

## Barras · DEKOPEN-CNC-BARS-V1

Una fila por corte, ordenada por `bar_index` y `sequence_in_bar`.

| Columna | Contenido |
|---|---|
| `bar_index` | Barra del plan; empieza en 1. |
| `stock_sku` | Código de compra del suministro declarado. |
| `stock_length_mm` | Largo de la barra o retazo tomado. |
| `sequence_in_bar` | Secuencia sellada por el motor dentro de la barra. |
| `piece_label` | Dirección física P/U/M, incluido el sufijo de refuerzo. |
| `piece_id` | Identidad técnica de la demanda del motor. |
| `cut_length_mm` | Largo de corte exacto. |
| `angle_left_deg`, `angle_right_deg` | Ángulos de los extremos, en grados; Sin dato impide exportar un refuerzo. |
| `unit_index` | Unidad física dentro de la posición. |
| `bay_id`, `leaf_id`, `source_position_id` | Origen técnico sellado; vacío significa que no aplica. |

La alimentación se lee desde el extremo inicial izquierdo. Cada longitud y
ángulo viene del motor y la autoridad congelada. El cierre del PDF muestra
por separado piezas, disco, despuntes y remanente; no redondea para cerrar.

## Láminas · DEKOPEN-CNC-SHEETS-V1

Una fila por pieza ubicada, ordenada por `sheet_index`, Y y X.

| Columna | Contenido |
|---|---|
| `sheet_index`, `purchasing_sku` | Lámina y suministro de compra. |
| `sheet_width_mm`, `sheet_height_mm` | Dimensiones físicas declaradas de la lámina o retazo. |
| `x_mm`, `y_mm` | Esquina de colocación del plan. |
| `width_mm`, `height_mm` | Dimensiones de la colocación en su orientación de corte. |
| `rotated` | `True` o `False`: el motor giró la pieza para ubicarla. |
| `piece_id`, `unit_index`, `bay_id`, `leaf_id` | Demanda técnica y origen físico. |
| `piece_label` | Misma etiqueta que el PDF, el DXF y el QR. |

Una pieza no ubicada conserva sus medidas y la causa. No se convierte en
una colocación inventada ni recibe un formato por defecto. Las piezas con
forma requieren la plantilla del contorno congelado.

## DXF, papel y QR

DXF usa AC1021 (AutoCAD 2007), UTF-8 y unidades en mm (`$INSUNITS=4`).
`bars.dxf` mantiene barras/cortes en secuencia; `sheet_n.dxf` mantiene Y/X.
Capas: `OUTLINE` para el suministro, `CUT` para contornos, `MARK` para
líneas de corte y `LABEL` para etiquetas. Las coordenadas conservan su
precisión de origen; el lector destino determina su precisión numérica.
Se conservan «Junquillo», «Ñ» y los códigos de proveedor en español.

El pack apaisado y las etiquetas normales siguen esa secuencia. La vista
agrupada es una ayuda opcional para sierra manual: presenta las direcciones
B/Sec. y no altera el CSV ni el DXF. Su hoja de etiquetas agrupa con el
mismo orden de primera aparición del grupo y mantiene todas las piezas.
La huella del plan aparece en cada hoja y etiqueta. El QR de pieza incluye
OT, etiqueta e identidad estable; abre su trazabilidad bajo autenticación.
El QR de retazo abre Inventario con su identidad RT y código. Antes de
completar Corte indica el destino previsto; después resuelve el stock físico.
