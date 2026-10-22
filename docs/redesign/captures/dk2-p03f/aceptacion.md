# P03f · Precios del proveedor

Verificado el 22-10-2026 en `gpt/dk2-p03f-precios-ui`. Depende de P03e; P03
sigue pendiente del asistente de cinco pasos y de la aceptación integral.

## Recorrido real

El dueño abre Precios en la ficha de una serie y elige un XLSX o CSV UTF-8.
El servidor sugiere Código, Descripción, Unidad de compra y Precio de compra.
El usuario declara el separador decimal del texto y elige la lista de destino,
con proveedor, moneda y vigencia visibles. Puede crear una lista vacía mediante
un clic explícito antes de revisar el archivo.

Revisar valida todas las filas sin guardarlas. La muestra contiene hasta diez;
el clic Confirmar y guardar precios aplica el archivo completo y su token de
revisión. Cambiar cualquier columna, archivo, separador o lista descarta ese
token en pantalla. Un conflicto del servidor también exige volver a revisar.
La confirmación conserva auditoría y origen del taller, y actualiza la ficha.
No se calculan ni redondean precios con números binarios en la interfaz.

`catalog-prices.spec.ts` usa Magic Link y TOTP reales en una empresa sintética.
Importa `fixtures/p03-precios-sinteticos.xlsx` (12 filas), creado por
`scripts/generate_p03_price_fixture.py`. Consulta la misma API autenticada de
costos para comprobar que la lista está vacía después de revisar, descarta el
token cambiando una columna y comprueba después del clic las 12 filas, el
código `001`, `0.2500` y `45000.1234`. El proveedor y los importes son sintéticos;
no certifican Proline ni una lista de fabricante.

## Revisión visual

Se mantiene el ancho de 1120 px y la jerarquía de revisión de `Prueba.dc.html`:
entrada, comparación tabular y acción explícita al final. Ese mockup define la
ventana de prueba, sin un diseño específico del mapeo de precios. El mapeo usa
controles, color, radios y tipografía compartidos con la ficha del producto.
No se añaden animaciones; se conserva el tratamiento común de movimiento reducido.

| Estado | Escritorio 1440 × 900 | Móvil 390 × 844 |
|---|---|---|
| Archivo y mapeo | [Captura](mapeo-1440.png) | [Captura](mapeo-390.png) |
| Revisión explícita | [Captura](revision-1440.png) | [Captura](revision-390.png) |
| Recibo de guardado | [Captura](guardados-1440.png) | [Captura](guardados-390.png) |

## Extremos y correcciones

La ruta DEV `/dev/precios-proveedor` reutiliza la misma tabla con selector de
datos de ejemplo, peor caso, vacío, uno y 500 precios. Está fuera del build de
producción. `catalog-prices-stress.spec.ts` recorre los cinco estados a
1440/390/320 px y texto al 100/200 %, comprueba desplazamiento horizontal por
teclado, límites visibles de las celdas de monto y axe A/AA/2.1 AA.

| Antes | Después | Motivo |
|---|---|---|
| Descripciones de 1.000 caracteres alargaban toda la página | Muestra con altura acotada, encabezado fijo y scroll local | La confirmación sigue siendo alcanzable |
| El monto máximo no cabía a 320 px y texto al 200 % | Permite saltos entre grupos de miles; conserva todos los dígitos y decimales | El precio completo se puede leer sin recorte |
| El selector del ensayo tapaba la muestra al ampliar texto | Selector DEV compacto, independiente del tamaño del producto | Permite inspeccionar la tabla ampliada |
| Un fallo de inspección obligaba a volver a elegir el archivo | Conserva el archivo y ofrece Volver a leer | La recuperación conserva el trabajo |

Se comprueban códigos de 100 caracteres, ceros iniciales, Unicode y emoji,
descripciones de hasta 1.000 caracteres, vacíos y montos de `9999999999.9999`.
La muestra sigue limitada a diez filas con un total de 500. El tema del
producto es claro; no se afirma soporte oscuro o RTL.

[Monto completo a 320 px y texto al 200 %](extremo-320-200.png) ·
[Muestra de un archivo de 500 precios](500-precios-1440.png).

## Validación y rendimiento

- Suite completa: **1.197 pruebas en 112 archivos aprobadas**. Tras añadir la
  recuperación de inspección, las 19 dirigidas pasan, incluidas las diez del
  importador, la exclusión por permisos y las regresiones de ficha.
- Dos E2E reales de importación y tres de extremos aprobados. Las capturas
  de producto se revisan con axe sin exclusiones. ESLint, TypeScript, guardas,
  Prettier, `git diff --check` y build de producción aprobados.
- Chromium local y Vite DEV, sin limitar CPU/red: mostrar la tabla de ensayo
  tardó 668–750 ms en la corrida de extremos; cambiar estados tardó 24–59 ms.
  Revisar las 12 filas del XLSX real tardó 270 ms a 1440 px y 287 ms a 390 px.
  Son tiempos de interacción locales; no son INP, LCP ni un benchmark productivo.

No cambia fórmulas, esquema, permisos del backend ni API generada. La lista
vacía puede quedar creada si se abandona el flujo; se muestra antes de crearla.
Los duplicados existentes se rechazan: no hay sobrescritura implícita.
