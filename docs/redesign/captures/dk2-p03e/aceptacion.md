# P03e · Comparación y protección de la ventana de prueba

Verificado el 22-10-2026 en `gpt/dk2-p03e-prueba-ui`. Esta entrega depende de
P03d y conserva pendiente el asistente completo de alta de P03.

## Flujo real

`catalog-trial.spec.ts` inicia sesión con Magic Link y TOTP en una empresa
sintética aislada. Completa reglas de la serie de ensayo, calcula con el motor,
declara un marco de 1208 mm y compara su diferencia exacta de 2 mm. El usuario
elige la adición de soldadura de 3 a 4 mm; se recalcula el despiece completo.
La confirmación explícita guarda la referencia y comprueba en la respuesta del
servidor que la capacidad MANUFACTURABLE está aprobada.

Después edita el solape de hoja de 8 a 9 mm. La revisión muestra antes/después;
cancelar conserva el borrador y la verificación. Aceptar aplica la misma
mutación revisada e invalida la verificación. La referencia original persiste.
Las medidas son de la fixture sintética; no acreditan un catálogo Proline real.

Los cinco E2E de flujo/extremos aprobaron en Chromium. Los dos flujos reales
usan 1440 × 900 y 390 × 844. Axe WCAG A/AA/2.1 AA comprueba cada captura sin
exclusiones. El ensayo móvil detectó contenido del fondo accesible durante el
modal: se corrigió el diálogo compartido con aislamiento/restauración del fondo
y manejo de teclado solo en el diálogo superior.

## Comparación con el mockup

Se conserva de `Prueba.dc.html` la jerarquía del título, el símbolo de apertura,
la tabla de seis columnas, comparación editable, aviso ámbar y confirmación al
pie. El panel de escritorio tiene el ancho de referencia de 1120 px; en móvil
el despiece tiene desplazamiento local accesible. Los controles usan los tokens
de la aplicación. No se añaden animaciones; permanecen las transiciones comunes
de controles y su tratamiento de movimiento reducido.

Los cinco pasos del encabezado del mockup se integran en la siguiente entrega;
esta sub-PR implementa el panel reutilizable y la revisión de futuros cambios.

| Estado | Escritorio | Móvil |
|---|---|---|
| Diferencia exacta | [Captura](diferencia-1440.png) | [Captura](diferencia-390.png) |
| Elección de regla y piezas afectadas | [Captura](ajuste-1440.png) | [Captura](ajuste-390.png) |
| Confirmación guardada | [Captura](verificada-1440.png) | [Captura](verificada-390.png) |
| Edición protegida | [Captura](edicion-protegida-1440.png) | [Captura](edicion-protegida-390.png) |

## Extremos y correcciones

La ruta DEV `/dev/prueba-serie?data=0` conserva un selector de datos de ejemplo,
peor caso, vacío, uno y 500 piezas. Usa la misma tabla del producto y permanece
fuera del build de producción. `catalog-trial-stress.spec.ts` comprueba esos
cinco estados a 1440, 390 y 320 px con texto al 100/200 %, sin desborde de página.

| Hallazgo | Corrección verificada |
|---|---|
| Los encabezados podían romper palabras al estrecharse | Anchos mínimos por columna y scroll local; el panel amplio aprovecha el escritorio |
| Los botones de revisión se salían del pie del diálogo móvil | Distribución flexible y texto multilínea; el E2E verifica los límites visibles de cada botón |
| 500 medidas crearían 500 entradas simultáneas | Páginas de 50; editar conserva las medidas de las otras páginas |
| El selector DEV tapaba demasiado contenido con texto al 200 % | Controles de revisión compactos; la tabla conserva el tamaño de texto ampliado |
| Los códigos numéricos del diff podían perder ceros | Formato numérico solo para campos de medida/cantidad; prueba con `001` y `002` |
| Un cálculo vacío o fallido podía dejar una confirmación anterior | Vacío bloqueado; recalcular invalida la confirmación antes de la petición |

Se ensayan códigos sin espacios de 84 caracteres, nombres largos, caracteres
no latinos, emoji, cantidades grandes y medidas de ocho enteros y dos
decimales. Los valores permanecen completos y las acciones son alcanzables.
El producto usa un tema claro; no se afirma soporte RTL o tema oscuro.

[Extremo a 320 px y texto al 200 %](extremo-320-200.png) ·
[500 piezas paginadas](paginada-1440.png).

## Pruebas y rendimiento

- Frontend completo: **1.188 pruebas en 111 archivos aprobadas**. Incluye
  cancelación/cola de revisiones, reintento único, cambio de empresa, ángulos,
  componentes, ceros iniciales y restauración del fondo de los diálogos.
- ESLint, TypeScript, Prettier, source guards, `git diff --check` y build de
  producción aprobados. La guarda del build incluye la nueva ruta DEV.
- Ensayo Chromium local por Playwright/CDP, Vite DEV, navegador frío,
  1440 × 900 y sin limitación de red/CPU: tabla lista en **397 ms**; activar
  500 piezas y pasar a la página siguiente en **120 ms**. CDP registró
  80 ms de ejecución de scripts, 224 ms de tareas y 15,4 MB de heap utilizado.
- Las muestras de interacción del E2E bajo la suite concurrente fueron
  46–322 ms. No son INP ni una prueba de carga de producción. Esta captura
  CDP no entregó FCP/LCP; no se atribuye una puntuación de Core Web Vitals.

P03 sigue pendiente de alta desde plantilla, revisión documental integrada,
mapeo de precios en pantalla y creación de la primera cotización. No se
modifican fórmulas, migraciones, datos reales, producción ni precios comerciales.
