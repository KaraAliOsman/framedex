# P04f · Cómo calculo mis precios

Revisión del 22-10-2026 en `gpt/dk2-p04f-empresa-precios`, sobre
`332a75ff` (P04e). Datos sintéticos aislados, sin precios reales ni autoridad
de Proline. API 8010, web 5175 y Supabase 25421; REVIEW del dueño conservado.

## Resultado y recorrido

Empresa permite configurar trabajo e instalación por m² o ventana, margen
sobre venta y redondeo. Merma, IVA y moneda se despliegan al necesitarlos.
El ejemplo usa una ventana real del borrador y sus costos resueltos por el
motor; al cambiar una tarifa o margen se reemplaza con una consulta nueva.
Sin ventanas pide crear una. Leer sugeridos no los guarda.

El E2E inicia sesión con Magic Link/TOTP, guarda cuatro decimales, crea tres
ventanas PRO6004 sintéticas por la API ordinaria y comprueba el ejemplo vivo,
margen inválido y extremo, unidades y activación avanzada todavía sin guardar.
Cinco unitarias cubren además conflicto 409 sin perder cambios, privacidad del
estimador y descarte de respuestas tardías. Veinticinco integraciones de
política/precio de trabajo verifican aislamiento, historial, concurrencia,
exactitud y modos avanzados. Veintiuna unitarias de contrato pasan.

## Capturas seleccionadas

| Estado | Escritorio 1440 × 900 | Móvil 390 × 844 |
| --- | --- | --- |
| Sugeridos, sin ventana | [Escritorio](desktop-empty.png) | [Móvil](mobile-empty.png) |
| Ejemplo del motor | [Escritorio](desktop-example.png) | [Móvil](mobile-example.png) |
| Importes extremos | [Escritorio](desktop-extreme.png) | [Móvil](mobile-extreme.png) |

[1024 px](width-1024.png), [1280 px](width-1280.png),
[320 px](width-320.png) y [320 px con texto al 200 %](text-200-percent.png).
Se inspeccionaron las imágenes completas. La estructura sigue la pantalla
única solicitada en §8 de catálogo/cálculo: controles a la izquierda, ejemplo
a la derecha, apilados en móvil. El paquete no incluye un mockup específico
de esta pantalla; se conserva la gramática vigente de Empresa.

## Extremos y pase editorial

Antes no existía esta pantalla simple: Comercial mostraba las reglas avanzadas.
Se retiró esa aparición incondicional; ahora exige guardar el interruptor.
No se añade una segunda forma de editar las mismas reglas.

Primera pasada: controles con nombres accesibles explícitos; menor repetición
de bordes en el ejemplo; margen mostrado con sus decimales exactos (99,99 % no
se convierte visualmente en 100,0 %). Segunda pasada:

- Merma `0E-80`: la API declaraba un serializer pero devolvía datos crudos.
  El ejemplo y el desglose público ahora transportan decimales planos exactos;
  el cero del motor se ve como $0. No se sustituye una ausencia por cero.
- Importe máximo de servicios y margen 99,99 %: el total largo conserva todos
  sus dígitos y pasa a su propia línea cuando necesita espacio.
- Texto al 200 % en 320 px: columnas con mínimo cero, etiquetas que se ajustan
  y botón que puede ocupar dos líneas; ningún contenido desborda la página.

La pantalla no enumera las ventanas de la empresa: el endpoint elige una
unidad mediante una consulta acotada. Los casos de 0 y 3 ventanas se ejercitan
aquí; la colección de 500 corresponde a la aceptación de la obra, pendiente.

| Rúbrica de Constitución | Resultado y evidencia |
| --- | --- |
| R1 | PASA: cifras tabulares, moneda y porcentajes explícitos, sin aritmética binaria; Sans según la dirección DEKOPEN 2 §4 |
| R2–R5 | PASA: tokens vigentes, borde/espacio, turquesa de acción y aviso de sugeridos; sin sombras nuevas |
| R6–R8 | PASA: lenguaje del taller; carga, vacío, datos, error y permiso denegado tienen causa y acción |
| R9–R11 | PASA en el alcance: no se agrega lienzo, selección ni iconografía; se preserva el shell vigente |
| R12 | PASA: controles nativos, etiquetas, foco y errores asociados; axe A/AA/2.1 AA en todos los estados capturados |
| R13 | PASA: no se agrega movimiento; el ejemplo reemplaza contenido sin animar cifras |
| R14–R16 | PASA: un Guardar principal, fuente del motor y ausencia explícita; sin degradados/blur/brillo |
| R17 | PASA: 1440, 1280, 1024, 390, 320 y texto al 200 % sin scroll horizontal |
| R18–R20 | PASA: controles con efecto real; el desglose y ejemplo vivo hacen visible la consecuencia de configurar el taller |

El momento propio es ver el precio de una ventana del trabajo responder al
margen. La idea aplicada de §8 es comparar consecuencias calculadas por el
motor, conservando la revisión de guardado y el origen de cada importe.

## Rendimiento y límites

Medición Playwright local, Chromium, dos viewports, sin throttling:
carga hasta formulario 1,29–1,37 s; LCP 1,29–1,37 s; CLS 0,0013–0,0023;
cambio de margen hasta nuevo total 0,84–0,86 s, incluidos 180 ms de espera.
Son observaciones del stack sintético, no percentiles de producción.
La compilación de producción aprueba; el aviso existente de chunks grandes
permanece y se revisará en el cierre de rendimiento.

ESLint, TypeScript, build, guardas y reproducción de OpenAPI/orval aprobados.
P04f no cambia fórmulas, SQL ni documentos emitidos. El total en la obra,
popover y emisión desde precio de trabajo siguen en P04g; P04 no se declara
terminada con esta subentrega.
