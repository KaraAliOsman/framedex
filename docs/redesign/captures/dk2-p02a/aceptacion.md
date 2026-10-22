# P02a · Tabla editable reutilizable

Verificación local de P02a, entregada en `gpt/dk2-p02a-tabla-editable`.
La ruta `/dev/tabla` usa datos sintéticos y queda fuera del build productivo.
La ficha de serie y su conexión con el catálogo se entregan en las siguientes
sub-PR de P02; estas capturas acreditan el componente compartido.

Se comparó la tabla con `mockups/Serie.dc.html`: cabecera tenue, filas de
sugeridos en ámbar, valores alineados a la derecha, borde y radios de tokens.
En móvil la tabla conserva columnas mediante desplazamiento horizontal local;
la página no se desborda. Los controles de ensayo son exclusivos de desarrollo.

| Datos | 1440 × 900 | 390 × 844 |
|---|---|---|
| Cinco perfiles | [Escritorio](tabla-ejemplo-1440.png) | [Móvil](tabla-ejemplo-390.png) |
| Nombres de 80 caracteres, cero y vacío | [Escritorio](tabla-extremo-1440.png) | [Móvil](tabla-extremo-390.png) |
| Vacío | [Escritorio](tabla-vacio-1440.png) | [Móvil](tabla-vacio-390.png) |
| Una fila | [Escritorio](tabla-uno-1440.png) | [Móvil](tabla-uno-390.png) |
| 300 perfiles, página de 50 filas | [Escritorio](tabla-300-1440.png) | [Móvil](tabla-300-390.png) |

Las diez capturas fueron abiertas e inspeccionadas. Playwright aprueba cuatro
pruebas en ambos tamaños, incluyendo axe WCAG A/AA/2.1 AA y ancho de página.
Carga local de desarrollo desde navegación hasta tabla visible: 418–831 ms;
no es una medición de red móvil ni una promesa de producción.

Trece pruebas unitarias verifican precisión textual de cuatro decimales y enteros
mayores que el rango seguro de JavaScript, pegado atómico de cinco filas,
errores en línea y límites distintos por fila, bloque fuera de rango, columnas de consulta, cero frente a
vacío, deshacer local y mediante escritura nueva, conflicto sin pérdida del
borrador, consulta sin edición, foco solicitado y teclado entre páginas.
El build comprueba que la ruta de desarrollo no llega al producto.

## Pase editorial

- Jerarquía y siguiente acción claras; una sola acción de guardar por tabla.
- Campos editables distinguibles, foco global visible y teclado completo.
- Números como texto exacto: ninguna cifra se calcula en el componente.
- Texto, estructura y tono además del color; contraste AA aprobado con axe.
- Sin movimiento añadido. La tabla usa los controles y diálogos existentes.
- Pendiente del conjunto P02: ficha real, precios auditados, confirmación y
  recorrido PRO6004 con portapapeles nativo.
