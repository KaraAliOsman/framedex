# P21 · centro de trabajo del proyecto

Base `76249e5a`, rama `codex/P21-centro-proyecto`. El proyecto deja la pila de
acordeones y el riel duplicado de datos: encabezado con fuente, siete flujos
visibles y una colección de elevaciones reales que permite editar la obra.
Database Gate local completo PASA; la verificación de CI se registra al integrar.

## Recorrido y autoridad

El recorrido de biblioteca agrega tres posiciones con serie, vidrio, medidas,
acabado y ubicación declarados; agrupa por piso, duplica el lote a seis,
cambia caras, deshace el diseño completo y reaplica. El precio aplicado
posteriormente muestra **$1.925.201 con IVA** y sus seis líneas provenientes
del motor comercial. La [lectura final](captures/centro-proyecto/despues/recorrido.json)
preserva importes y fuentes exactas. Un intento de prueba interrumpido no
acredita aceptación: la continuación usa la misma obra y comprueba lo guardado.

Las [interacciones y matriz](captures/centro-proyecto/despues/interacciones-matriz.json)
pasan 31 casos: medidas en la fila con diff y deshacer, orden sin renumerar,
flechas, Enter al editor, Supr con confirmación y propuesta antes del borrado,
restauración, lista/grilla y Producción/Documentos/Actividad. Los seis tamaños
y temas de escritorio de esa matriz no presentan hallazgos ni desbordes.
La [matriz de consulta](captures/centro-proyecto/ux-final/index.html) recorre
estimador y jefe de taller, cuatro tamaños y dos temas con los detectores
oficiales sin alterar sus reglas.

Las operaciones reservan autoridad, validan cada diseño diferente y conservan
firma de concurrencia. Reintentar usa la misma clave, sin duplicar posiciones.
Los metadatos preservan BOM, número físico y mediciones; duplicar no convierte
una medición del vano original en evidencia de su copia. Las revisiones
cerradas, roles ajenos y otra organización quedan protegidos por backend/RLS.
La migración no modifica históricos para asignarles orden ni piso.

## Rendimiento

La [medición de cien posiciones](captures/centro-proyecto/despues/mediciones.json)
mide desde navegación hasta checkbox habilitado, clic y contador de selección
visible. Las capturas quedan fuera del intervalo. Cinco contextos nuevos
registran 1.975,32 / 1.781,68 / 1.800,95 / 1.904,57 / 1.803,87 ms;
el máximo es **1.975,32 ms**, con cinco posiciones montadas.
Home y End enfocan la primera y la centésima posición reales.

La lectura anterior de cien posiciones registró 2.984,16 ms y cien filas
montadas. Las mediciones anteriores de doce posiciones incluían captura;
no se usan como comparación de rendimiento ni para afirmar una mejora
porcentual. La virtualización utiliza alturas medidas, reinicia la ventana
cuando cambian vista/grupo/filtros y conserva selección por identidad.

## Dos rondas editoriales

Primera ronda:

1. Se eliminan el riel de hechos, los acordeones de flujos principales y su
   CSS. La ficha secundaria se abre en drawer; precio y servicios conservan
   sus capacidades reales sin repetir formularios.
2. La colección reemplaza filas de texto por dibujos, medidas editables,
   filtros y lote. Orden visual y dirección física quedan separados.
3. Se elimina el N+1 de mediciones. Las propuestas iguales reutilizan cálculo
   dentro de la operación; las cien elevaciones montan solo su ventana visible.

Segunda ronda:

1. Las miniaturas dejan de mostrar controles de agregar sin efecto y cotas
   externas a su caja. El renderer común mantiene la gramática de aperturas;
   los controles y cotas del editor interactivo siguen disponibles.
2. Los cambios muestran las medidas anteriores y posteriores junto a
   cantidad, ubicación y orden. La carga de proyecto usa el cargador de cota.
3. El anticipo consulta su hito sellado: un abono parcial no completa esa fase.
   Falta de consulta, precio sin aplicar, vigencia ausente y Uw desconocido
   se exponen con causa; no se inventa un total, una fecha ni un certificado.

Firma F4: la medida se cambia donde se lee y abre una propuesta del motor.
La capacidad del §8 es filtro → lote → diff de posiciones/precio → aplicar →
deshacer. Δ de Uw permanece «Sin dato» con causa y destino al catálogo.

## Rúbrica editorial

La inspección visual de lista, grilla, precio y diff se contrasta con las
matrices oficiales y los recorridos de teclado. Los veinte puntos pasan
en la superficie de proyecto; la aceptación de CI se registra por separado.

| Ítem | Resultado | Evidencia |
|---|---|---|
| R1 | PASA | Medidas y dinero en Mono tabular; diff anterior/posterior con unidades. |
| R2 | PASA | Bordes y controles usan radios del sistema, sin píldoras. |
| R3 | PASA | Encabezado, colección y propuesta se distinguen por borde y espacio. |
| R4 | PASA | Naranja limitado a bloqueo que requiere decisión humana. |
| R5 | PASA | Teal común para selección, foco y acciones del cromo. |
| R6 | PASA | Tipologías, fases y cinco operaciones nuevas tienen nombres humanos. |
| R7 | PASA | Lista de oficina densa y grilla legible a 1024; ficha secundaria en drawer. |
| R8 | PASA | Vacío, carga, error recuperable, sin permiso y precio bloqueado probados. |
| R9 | PASA | Elevación en papel diferenciado de la mesa en ambos temas. |
| R10 | PASA | Contorno/tinte de posición activa y checkbox de selección del lote. |
| R11 | PASA | Renderer DIN común; miniaturas declaran Vista interior. |
| R12 | PASA | Flechas, Enter, Supr, Home/End y foco visible en colección virtualizada. |
| R13 | PASA | Movimiento y reduce-motion usan reglas comunes sin animación añadida. |
| R14 | PASA | Próxima acción por fase; una confirmación principal en cada propuesta. |
| R15 | PASA | Precio aplicado con fuente; vigencia, vano y Uw ausentes con causa. |
| R16 | PASA | Guardas y capturas sin degradados, blur, brillo ni croma IA. |
| R17 | PASA | 32 vistas oficiales y matriz lista/grilla sin desbordes. |
| R18 | PASA | Riel/acordeones viejos retirados; miniaturas sin controles muertos. |
| R19 | PASA | F4 cambia medidas en la fila, con revisión y restauración verificadas. |
| R20 | PASA | Filtro/lote, diff del motor, aplicar/deshacer y total comercial reales. |

Los [cinco estados](captures/centro-proyecto/estados/estados.json) incluyen
retención de la consulta para carga y respuesta 503 para error, inyectadas
solo por Playwright; vacío, instalador sin permiso y precio bloqueado son
estados reales del fixture. Ninguna de esas pruebas modifica una posición.
La [captura de medidas](captures/centro-proyecto/despues/diff-medidas.png)
muestra 1 500 × 1 200 → 1 300 × 1 200 mm y Δ neto de la simulación;
se descarta sin persistir. La compresión verifica píxeles, modo y tamaño
exactos de los PNG, no solo su legibilidad.

## Verificación local

PostgreSQL focal pasa **33 pruebas** de proyecto/operaciones, incluyendo
tenant, rol, catálogo, medición, orden, sellado y compatibilidad de firmas.
La repetición final de `make lint typecheck test build` termina con código 0
sobre la implementación `38bac104c8774dc0225fccec74e6089872701cb1`:
886 pruebas del motor (+2 xfail preexistentes), goldens byte a byte,
1.476 backend y **988 frontend**; tipos, fuente/API reproducibles y build
pasan. Las traducciones de las nuevas operaciones pasan su contrato común.
Ningún check ni detector se debilita. El build conserva la advertencia de
tamaño del bloque 3D compartido; el centro de proyecto carga sus paneles
secundarios bajo demanda.

Database Gate sobre `e309768b` pasa **1.325 pgTAP en 91 archivos**, **502
integraciones**, **19 E2E** y diez verificaciones de upgrades poblados PG16.
Los checks finales de fuente y tipos pasan sobre las correcciones E2E. La
primera repetición completa encontró el selector de la acción Precio, una
proyección de posición que incorpora metadatos del sistema y el intento de
borrar un fixture con auditoría retenida. Las pruebas ahora verifican la
proyección exacta, el before/after persistido del lote y el rechazo 409/23503
del borrado; la auditoría no se borra ni se modifica para limpiar la prueba.
La recarga de Precio espera la proyección del motor, comprueba el monto actual
antes de leer la tabla y mantiene el estado de cálculo pendiente sin anunciar
una ausencia de precio. Su regresión de frontend retiene la respuesta hasta
comprobar cargador, bloqueo de Aplicar y ausencia del mensaje contradictorio.
La repetición completa de los cuatro gates pasa 886 motor (+2 xfail),
1.476 backend, 989 frontend, goldens byte a byte y build sobre ese código.
El upgrade D01/D02 compara la fila histórica completa más los dos campos
aditivos esperados: `display_order=null` y `placement={}`. Todos los campos
anteriores y cualquier columna nueva inesperada siguen en la comparación.
Ningún caso ni aserción de autoridad se elimina. CI se registra antes del
merge. Los 79 PNG anteriores y
posteriores conservan los recorridos sin tokens de autenticación ni valores
de entorno. Los procesos propios de aplicación quedan detenidos y el fixture
se conserva; la puerta SQL usa un proyecto aislado diferente.

## Límites

El catálogo es DEMO, Uw no tiene autoridad completa y las superficies
restantes conservan su propio encargo. No se conecta un servicio productivo
ni se emite una nueva cotización en esta aceptación. La integración de precio,
documentos, importación y producción conserva sus contratos sellados y el
clic humano. Activación: [ACTIVACION.md](../operations/ACTIVACION.md).


## Integración verificada

PR [#146](https://github.com/KaraAliOsman/framedex/pull/146), squash `412029ac1ea688a0f5bf1d560ba9b2e99871fae6` en `integracion/v1`.
Los cuatro checks de [CI](https://github.com/KaraAliOsman/framedex/actions/runs/38110211964) pasan sobre `50a00fe9e509338cdee706459c17395119e036a8`.
Las revisiones automáticas externas fueron omitidas por sus proveedores; no se cuentan como revisión completa.
