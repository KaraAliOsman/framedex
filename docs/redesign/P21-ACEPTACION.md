# P21 · centro de trabajo del proyecto

Base `76249e5a`, rama `codex/P21-centro-proyecto`. El proyecto deja la pila de
acordeones y el riel duplicado de datos: encabezado con fuente, siete flujos
visibles y una colección de elevaciones reales que permite editar la obra.
La verificación de CI y Database Gate se registra al cerrar este encargo.

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

## Verificación pendiente de cierre

PostgreSQL focal pasa **33 pruebas** de proyecto/operaciones, incluyendo
tenant, rol, catálogo, medición, orden, sellado y compatibilidad de firmas.
El primer gate completo pasa lint, tipos, 886 motor (+2 xfail), goldens byte
a byte y 1.476 backend; frontend detecta seis traducciones faltantes de las
nuevas operaciones. Esa corrida no acredita un gate completo. Se corrigen
las traducciones y se repiten los gates finales sin alterar los checks.

La rúbrica, los cinco estados, Database Gate y CI se completan y registran
antes del merge. Los PNG anteriores y posteriores conservan la evidencia
de los recorridos, sin tokens de autenticación ni valores de entorno.

## Límites

El catálogo es DEMO, Uw no tiene autoridad completa y las superficies
restantes conservan su propio encargo. No se conecta un servicio productivo
ni se emite una nueva cotización en esta aceptación. La integración de precio,
documentos, importación y producción conserva sus contratos sellados y el
clic humano. Activación: [ACTIVACION.md](../operations/ACTIVACION.md).
