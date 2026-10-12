# D07 · del vano a fabricación

El estimador ingresa el vano y el motor obtiene fabricación con la regla
de montaje de su organización y serie. Una o tres medidas por eje conservan
el mínimo, la dispersión, las holguras y la fuente. La fijación manual necesita
motivo y deja su desviación visible. El documento comercial muestra vano y
producto; el taller conserva exclusivamente fabricación y su BOM sellado.

## Recorridos verificados

| Recorrido | Resultado y evidencia |
| --- | --- |
| En vano, premarco, traslape y renovación | PASA: `engine/tests/golden_mounting.json`, regenerado mediante `make goldgen` |
| Tres puntos → mínimo y aviso de dispersión | PASA: `recorrido/minimo-tres-puntos.png`, prueba del motor y navegador |
| Tipo de muro no declarado | PASA: sin selección no hay propuesta; explica el campo faltante y continúa tras elegir el muro observado |
| Fabricación fijada con motivo → aviso de incoherencia | PASA: `recorrido/fijacion-incoherente.png`; diferencia exacta de 10 mm |
| Aplicar → deshacer/rehacer → guardar/reabrir | PASA: `recorrido/navegador-editor.json`; conserva evidencia ligada al diseño |
| Medidas del cliente → rectificación → confirmación | PASA: confirmación explícita de generación y timestamp actuales; avisos reconocidos |
| Ajustes con MFA → diff → ensanche izquierdo → guardar/deshacer | PASA: `recorrido/ajustes-diff-fuente.png`, `navegador-cadena.json`; las medidas previas conservan su regla |
| Estimador consulta; dueño/encargado declara | PASA: navegador y pruebas HTTP/SQL; instalador sin acceso a esta superficie de oficina |
| Aprobar A → rectificar → REV-B y Δ de venta | PASA: `flujo-medidas-revision-ot.json`; $314.275 → $331.020, Δ $16.745, tarifas DEMO |
| PDF anterior después de rectificar | PASA: igualdad byte a byte de REV-A; se emite un PDF nuevo para B |
| Confirmar B → emitir → liberar OT | PASA: fabricación 1 600 × 1 200 mm; DOC-03 sin medida del vano 1 620 mm |
| Emitir con medidas pendientes → intentar liberar OT | PASA: rechazo `production_measurements_unconfirmed` en backend y SQL |
| Borrar posición en borrador | PASA: desaparece la posición y conserva su historial inmutable; no se puede confirmar un destino eliminado |
| Tenant ajeno, actor falsificado, proyecto ajeno o secuencia incorrecta | PASA: pruebas PostgreSQL `test_opening_mounting.py` y pgTAP 182 |
| Portal a 390 px | PASA: `recorrido/portal-vano-producto-390.png`; proyección comercial sin actor ni motivos privados |
| Vacío, carga, error/reintento, sin permiso y revisión cerrada | PASA: `recorrido/estado-*.png` y `navegador-matriz.json` |
| Cambiar montaje con ensanche → montaje sin ensanche | PASA: retira solo la pieza exigida; conserva ensanche independiente derecho o mosquitero, BOM y guardado/reapertura |
| Editar mientras llega una propuesta | PASA: respuesta diferida descartada, sin borrar el accesorio nuevo; `recorrido/navegador-revision.json` y regresiones del inspector |
| Otra serie con igual código/revisión de regla | PASA: la rectificación resuelve la autoridad de la serie propuesta y proyecta solo venta |
| Revisión anterior de otro marco | PASA: sigue ligada a su revisión inmutable mientras se mide el segundo marco |
| Lista de 10 000 mediciones | PASA: se rechaza por cantidad de marcos antes de construir los modelos individuales |

Los PDF de A y B y el de taller se emitieron, rasterizaron e inspeccionaron.
La presentación nueva conserva espacio fino, coma decimal y precisión exacta;
no se cambia el formateador de los documentos históricos. Las revisiones
anteriores y su precio permanecen intactos.

La matriz formal compara 24 capturas de editor, proyecto y Ajustes en
1440×900, 1280×800, 1024×768 y 390×844, en ambos temas.
[`comparacion.json`](comparacion.json) conserva los hallazgos anteriores y no
añade ninguno; no registra errores HTTP o consola. El desborde móvil heredado
del editor permanece visible fuera de los anchos obligatorios de oficina.
P04/P05 y P21 rediseñan las superficies completas; D07 acredita sus controles,
cotas, estado y rectificación, sin atribuir conformidad al cromo histórico.

## Pase editorial: dos rondas

Primera ronda:

1. Se elimina la cota general superior duplicada cuando hay mediciones. Las
   cotas de vano y fabricación se separan y los ajustes asimétricos proceden del
   motor, sin distribuir una holgura ficticia por mitades.
2. Se pliegan escuadra, desplome y fijación manual. La fabricación calculada
   se aplica con propuesta y deshacer; guardar explica cualquier desacuerdo
   con las medidas vigentes.
3. La confirmación reconoce los avisos y comprueba cobertura de cada marco.
   Un cambio de serie descarta su montaje anterior; quitar un módulo filtra su
   evidencia atómicamente y deshacer la restaura.

Segunda ronda:

1. Se corrige el recorte de la cota a 1024×768. El lienzo medido conserva una
   altura útil y la matriz comprueba que ambos textos caben en la hoja.
2. Ajustes permite elegir los lados compatibles de ensanches/fijaciones y
   revisar la selección antes de guardar. Sin fuente o accesorio físico
   compatible, el backend rechaza la autoridad; no se sustituye por un valor.
3. La rectificación conserva la regla previa salvo elección explícita de una
   autoridad nueva, consulta reglas solo al abrirse y muestra el Δ persistido
   al reabrir. Se retiran peticiones innecesarias; los informes de editor,
   cadena y matriz tienen nombres distintos para conservar toda la evidencia.

Momento de firma: cota doble de vano y fabricación, con contorno de holgura y
«¿De dónde sale?» que muestra deducciones, fijación y fuente. Idea que sube el
techo: el mínimo de tres puntos y su dispersión se calculan y registran en la
misma evidencia que gobierna la revisión y el permiso de producción.

| Rúbrica | Resultado | Evidencia del alcance D07 |
| --- | --- | --- |
| R1 | PASA | Medidas y moneda en Mono tabular, unidades y formato exacto |
| R2 | PASA | Radios del sistema; ninguna superficie blanda nueva |
| R3 | PASA | Inspector y fuentes plegadas, sin capa flotante adicional |
| R4 | PASA | Avisos humanos y marca; ningún CTA naranja |
| R5 | PASA | Teal funcional de los tokens |
| R6 | PASA | Vano, fabricación, holgura, premarco y rectificación en español |
| R7 | PASA | Controles compactos y ocho campos de montaje visibles en el inspector a 768 px |
| R8 | PASA | Cinco estados con causa, acción y rol; revisión cerrada visible |
| R9 | PASA | Lienzo como hoja y documentos sellados en papel |
| R10 | PASA | Contorno de vano y selección existente, sin brillo |
| R11 | PASA | Gramática de apertura y vista declarada conservadas |
| R12 | PASA | Etiquetas, foco por token, teclado y deshacer reales |
| R13 | PASA | Sin animación decorativa; movimiento y reduce-motion conservados |
| R14 | PASA | Calcular/revisar → aplicar; una confirmación principal por región |
| R15 | PASA | Desglose y fuente exactos; ausencia explícita sin regla o precio |
| R16 | PASA | Cero degradados, blur, brillo o morado en las superficies nuevas |
| R17 | PASA | Cotas dentro del lienzo y sin desbordes nuevos en la matriz |
| R18 | PASA | Guardado, historial, precio, revisión, PDF y OT con efecto persistente |
| R19 | PASA | Cota doble y traza de holguras |
| R20 | PASA | Mínimo, dispersión y revisión calculados por el motor |

## Validación técnica y límites

La revisión del PR #125 identificó seis problemas potenciales, reproducidos o
aislados antes del merge. Los accesorios independientes se guardan separados
de las piezas exigidas por montaje; una regla nueva conserva la selección
independiente y combina sus lados compatibles sin acumular piezas anteriores.
Los accesorios exigidos muestran su causa y se modifican desde Vano y montaje.
La propuesta captura la identidad del diseño y descarta respuestas o aplicaciones
obsoletas; cambiar la regla durante la espera también invalida la petición.
Cada revisión de regla se resuelve por organización, serie, código y revisión;
no se sustituye silenciosamente una regla de otro sistema. La simulación usa
el contexto comercial habitual y devuelve exclusivamente venta. La cantidad
de mediciones se comprueba contra los marcos reales antes del parseo.

El recorrido adicional verifica persistencia, BOM y respuesta tardía en el
navegador, con seis capturas en 1440, 1280 y 1024, claro y oscuro. Las pruebas
del motor verifican conservación de lados independientes y rechazo de destinos
contradictorios. El golden añade solo el campo de atribución opcional nulo;
las medidas y deducciones congeladas no cambian.

El gate nativo aislado pasa lint, typecheck, test y build: 662 pruebas del motor
(+2 xfail históricos), 1 186 del backend y 734 del frontend. Los goldens pasan
la comprobación de bytes. Las 25 pruebas PostgreSQL focalizadas verifican roles,
confirmación vigente, inmutabilidad, cobertura, rectificación, aislamiento y
borrado y rechazo de copia de evidencia obsoleta a otra revisión. Database Gate
pasa completo sobre la revisión con 1 090 pgTAP, 362 integraciones, 11 E2E y los ocho recorridos
de upgrade en PostgreSQL 16. Se verifica la limpieza del stack aislado al
terminar. Los cuatro checks de CI pasan sobre `12d24009d10b59626ba54d7f1ce9cd9324f1e440`.
PR [#125](https://github.com/KaraAliOsman/framedex/pull/125) integrado por squash
`f85c555c3e9bb63bf1eb7a98d2ac627e867ca21d` en `integracion/v1`.

Los intentos fallidos de selectores, formato y runner de captura no cuentan
como aceptación. El recorte visual detectado se corrigió y se añadió una
aserción específica; el chequeo no se debilitó. El stack de app y el de gates
usan identidades y puertos propios; las credenciales se cargan en memoria.

No hecho / riesgos: las reglas del recorrido son DEMO, sin certificación. La
organización debe declarar las holguras, accesorios, tolerancia y fuente reales
en Ajustes para cada serie. D07 no inventa una tolerancia universal ni transforma
un montaje en ingeniería estructural certificada. P23 incorporará la captura de
obra del instalador móvil sobre este contrato; ese rol no recibe escritura
genérica del editor. Un proyecto en producción pide gestionar su corrección con
el encargado, conservando la revisión liberada. Los snapshots históricos sin
`measurements_required` conservan su contrato anterior; todas las emisiones
nuevas exigen evidencia confirmada antes de liberar OT.
