# IA2 · aceptación de operaciones compartidas

Código verificado: `5224dbfba0f3f6c7d218639704bb013eceeb88dd`. Fecha: 07-10-2026.
Proveedor real: `primalabs-ai/MiMo-V2.6-Pro`. La corrida completa obtiene
21/26; editor y proyecto 19/21 (90,48 %).
Véase la [comparativa por caso y categoría](../../../ai/evals/2026-10-07-ia2-comparativa.md)
y el [JSON completo](../../../ai/evals/2026-10-07-ia2-mimo.json).

## Resultado y alcance

UI, API e IA expresan las 50 operaciones del registro `design-ops-v1`.
El motor ejecuta la intención y devuelve efectos tipados, geometría, validez,
hojas/manillas y venta indicativa; el frontend consume esa autoridad. Un lote
se simula y aplica en una transacción con firma, idempotencia, historial y
deshacer que conserva las identidades originales. Reabrir un trabajo consulta
el estado persistido. Las preparaciones de emisión, OT, compra y cobro exigen
el clic humano en su propia superficie.

El prompt versionado tiene glosario, ejemplos del registro, aclaraciones y
límites. Los números del contexto o herramientas del turno sirven como
evidencia; un número inventado falla antes de producir una propuesta.
Los límites configurables y decisiones constan en
[valores por defecto](../../../decisions/valores-por-defecto.md) y
[operaciones](../../../ai/OPERACIONES.md).

## Recorrido de navegador

Chromium real sobre Supabase, Django, worker y Vite propios. No se utilizó
el stack ni los datos del otro repositorio. La clave real se cargó en memoria.

| Flujo | Resultado | Evidencia |
| --- | --- | --- |
| E02, fijo + oscilobatiente | PASA: hoja física, bisagra izquierda/manilla derecha, aplicar y guardar | [Propuesta](recorrido/E02-propuesta-light-1440.png) |
| E04, travesaño desde arriba | PASA: 400 mm exactos, aplicar y persistir | [Propuesta](recorrido/E04-propuesta-light-1440.png) |
| E08, manilla desde piso | PASA: pregunta antepecho, continúa el mismo trabajo, referencia piso 1 000 mm con antepecho 600 mm; altura local igual al motor | [Pregunta](recorrido/E08-aclaracion-light-1440.png), [continuación](recorrido/E08-continuacion-light-1440.png) |
| J02, serie histórica incompatible | PASA: causa del catálogo, cero escrituras | [Incompatibilidad](recorrido/J02-incompatibilidad-light-1440.png) |
| J03, cuatro dormitorios | PASA: 4 → 8 vanos, recargar, deshacer, recargar; restaura los 4 IDs originales | [Diff](recorrido/J03-diff-light-1440.png), [aplicado](recorrido/J03-aplicado-restaurado-light-1440.png), [deshecho](recorrido/J03-deshacer-restaurado-light-1440.png) |
| E06, composición sin alternativa compatible | PASA: chip real del catálogo, foco visible, Enter y continuación del mismo trabajo | [Opciones reales](recorrido/E06-alternativas-reales-light-1440.png) |

La matriz comprende editor, proyecto y espacio del asistente en 1440×900,
1280×800 y 1024×768, claro/oscuro: 18 capturas; las propuestas y su continuación
aportan 9 capturas más. [Resultado: 27 capturas sin hallazgos de texto,
presentación, desborde ni errores de página](recorrido/resultados.json).

Los cinco estados tienen 10 capturas, claro/oscuro a 1024×768:
[carga](estados/cargando-light-1024.png), [error](estados/error-light-1024.png),
[sin permiso](estados/sin-permiso-light-1024.png),
[bloqueado](estados/bloqueado-light-1024.png), [vacío](estados/vacio-light-1024.png).
El error 503, permiso 403 y bloqueo 422 se interceptaron en Playwright para
verificar su presentación y reintento sin escritura; no fueron caídas reales
del servidor. Las integraciones verifican además permisos reales por rol/tenant.
[Resultados de estados](estados/resultados.json).

`ux:capture` compara 24 capturas antes/después (también 390×844) sin hallazgos
nuevos, desbordes nuevos ni errores HTTP/consola. Se conserva el desborde
heredado del editor a 390, fuera de los tamaños office exigidos; P04 sigue ese
rediseño. Cromo y proyecto mantienen observaciones históricas para P17/P21.
No se declara saneada toda la aplicación. [Comparación](comparacion.json).

## Dos rondas editoriales

Primera ronda:

1. Se sustituye la aceptación de alias históricos como autoridad nueva por
   compatibilidad física del catálogo. Una propuesta incompatible explica la
   causa en vez de simular éxito; se elimina el rechazo ambiguo al guardar una
   apertura que sí tiene kit declarado.
2. Se corrige el estado del lote al recargar, con clave estable por trabajo,
   turno y paso, consulta durable y re-simulación de propuestas obsoletas.
   La aplicación ya no depende solo de la memoria del componente.
3. La aclaración ofrece opciones reales, elimina cifras sugeridas sin fuente
   y agrega foco/Enter. Su respuesta continúa el mismo trabajo.

Segunda ronda:

1. Se quita prosa que repetía las operaciones antes del dibujo, estados crudos,
   identificadores en borradores y el bloque naranja vacío de preguntas
   duplicadas. La pregunta y el diff ocupan el espacio útil.
2. La vista previa usa hojas/manillas del motor para antes y después. El fijo
   pierde una raya decorativa que confundía apertura. Moneda desconocida sigue
   ausente; el Δ coincide con la resta visible y los lotes conservan la tarifa
   unitaria exacta hasta multiplicar la cantidad.
3. La lista de trabajos usa radio/espaciado del sistema y texto ≥11 px incluso
   con historial largo. La cabecera acomoda el trabajo pendiente a 390 px sin
   desbordar. Se corrigen datos vigentes de borradores y traducciones conocidas.

Momento de firma: la pregunta con chips del catálogo real y continuación del
mismo trabajo. Idea que sube el techo: un pedido compuesto genera un plan único
simulado por el motor con geometría física y diff antes de aplicar. Los golden
de operaciones congelan el marco, divisiones, aperturas y cotas exactas.

| Rúbrica | Resultado | Evidencia en el alcance IA2 |
| --- | --- | --- |
| R1 | PASA | Dims/Money/Qty y Mono tabular con unidades; moneda ausente explícita |
| R2 | PASA | Radios r-1 y límites del sistema, también en listas restauradas |
| R3 | PASA | Diff por bordes y un dock; sin capas adicionales |
| R4 | PASA | Naranja reservado a pregunta/requiere persona; bloque vacío retirado |
| R5 | PASA | Teal de los tokens como croma funcional |
| R6 | PASA | Glosario del taller y traducciones; sin UUID/estado crudo en borradores |
| R7 | PASA | Registro en detalles y diff compacto; no añade campos al inspector existente |
| R8 | PASA | Cinco estados con causa, acción y reintento; estado durable tras recargar |
| R9 | PASA | Antes/después sobre papel con vista interior declarada |
| R10 | PASA | Selección por contorno/tinte del editor; sin brillo añadido |
| R11 | PASA | Hoja y manilla de autoridad física, simbología compatible |
| R12 | PASA | Chips con foco y Enter; aplicar, guardar y deshacer reales |
| R13 | PASA | Sin movimiento decorativo; reduce-motion en el recorrido |
| R14 | PASA | Propuesta → aplicar; reintento y deshacer según estado |
| R15 | PASA | Herramientas/engine como fuente, desconocido con causa, Δ reconciliado |
| R16 | PASA | Sin degradado, blur, brillo ni morado en controles nuevos |
| R17 | PASA | Matriz office sin desbordes; cabecera 390 corregida; legado 390 documentado |
| R18 | PASA | Paridad de registro, persistencia, consulta y deshacer; sin edición paralela |
| R19 | PASA | Aclaración con alternativas reales y continuación estable |
| R20 | PASA | Plan compuesto con motor, golden, simulación y aplicación exactas |

## Gates y límites

Sobre el código indicado: `make lint`, `make typecheck`, `make test` y `make build`
PASA. API/OpenAPI/orval reproducibles y guardas vigentes.
740 pruebas motor (+2 xfail), 1 205 backend y 806 frontend.
`make test-db`: 77 archivos/1 101 pgTAP, 380 integraciones, 11 E2E y ocho
upgrades poblados PG16, con limpieza del stack propio verificada.
Las regresiones de grounding, paridad, operaciones, obsolescencia, rol/tenant,
transacción/undo y progreso del worker forman parte de esas suites.

La revisión del PR identificó tres pérdidas de información y se corrigieron
antes del merge. El snapshot conserva y bloquea la preparación documental;
deshacer una eliminación restaura su fila completa, IDs, políticas, JSON,
hash y metadatos bajo RLS y guardas de sellado. Una preparación posterior
invalida el deshacer. El adaptador conserva `product-v2` en contornos y módulos
sin marco; las integraciones prueban aplicar, reabrir y deshacer ambas formas.
Al seleccionar un vidrio histórico se deriva el espesor de su receta en el
motor o queda desconocido, sin heredar el anterior. Las 16 integraciones
focalizadas y 74 pruebas de operaciones/golden pasan. `make goldgen` agrega
tres casos de vidrio y mantiene todos los casos anteriores idénticos.
La evaluación y el recorrido se repiten completos sobre el código corregido.

Los hallazgos heredados de cromo/editor y el rediseño del dock/Orb pertenecen a
P04/P17/P21. IA3 continúa ruteo, proveedor, reintentos y configuración en Ajustes.
El catálogo y los precios usados son DEMO sintéticos, sin certificación.
J04/J08 carecen de autoridad aplicada/emitida y F03 exige otro rol. F01/F02
conservan resultados incorrectos sin cifras técnicas inventadas. La corrida final
no registra fallos del proveedor; el error J01 de la corrida anterior permanece
como hecho histórico en el log. Los cinco fallos finales se mantienen en la
comparativa, sin aprobarlos por terminar el trabajo ni por una respuesta verbal.
No se agregan integraciones externas ni acciones consecuentes automáticas.
Los cuatro checks de CI deben estar verdes antes del squash a integracion/v1.
