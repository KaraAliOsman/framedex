# Aceptación de DEKOPEN v1 · 12-10-2026

Producto listo para la revisión del dueño: los catorce recorridos pasan, con
observaciones explícitas para sandbox, autoridad DEMO y límites de proveedor.
Esta aceptación no autoriza fabricación industrial, acredita dinero real ni
certifica documentos tributarios o prestaciones térmicas.

## Revisiones y alcance

La corrección de P20 está integrada por [PR #154](https://github.com/KaraAliOsman/framedex/pull/154),
squash `b8450659d4ec82e062bdef5e7b3e703266956b09`, CI 4/4 sobre
`d4dea5827d9509adb288c94eb8e01ddd05948f13`, corrida `38295986860`.
La corrección adicional de lectura comercial se integra por
[PR #155](https://github.com/KaraAliOsman/framedex/pull/155), squash
`15a3332a53ee0c21032ecd2715f5c6298e3b076e`. Su CI 4/4 comprueba
`e5fef9b504158d064f180c4b5af558459bdbd895`. La medición de interacción, el perfil y
las 24 recapturas de Ajustes corresponden a `b8e62295`, incluido en ese PR.
Los archivos de cada medición conservan su ref: IA `48418212`, baseline UX
`4efd739e`, presentación corregida `b8450659` y optimización de portal
`cc0003ab`. El cierre documental amplía esa evidencia; no reatribuye las
mediciones históricas a un commit posterior.

Se usaron dos stacks propios: PRIMARY para matrices por rol, IA, terreno y
analítica; REVIEW para la guía desde arranque limpio, revisiones, fabricación
y dominio. Se mantuvo la base de revisión y se usaron cuentas reales de Auth.
La revisión local se comunica por una red Docker propia tras verificar su
propiedad. Se corrigió la ruta IPv6 inalcanzable del proxy local y se repitió
el arranque de la guía; sus cuatro regresiones de seguridad pasan. La corrección
de red corresponde a `3d410d1d`, sin alterar los contratos de cálculo.
El editor recupera una lectura de posición fallida mediante Reintentar sobre
el mismo ID y tenant. El estado de error tiene h1 y la región del diseño un
nombre accesible. La lectura móvil conserva el dibujo cuando se carga CSS
compartido con el portal; los nombres largos de proyectos no empujan los
controles fuera de la cabecera a 1024 px. Se comprobaron ocho pares ancho/tema
en Vite y ocho en build de producción: error y recuperación con detectores y
axe originales, sin hallazgos, desbordes ni escrituras de posición. Los POST
de evaluación/preview/simulación quedan registrados como cálculos.
Las recapturas son lecturas posteriores estables: conservan recibos y no
repiten emisiones, pagos, recepciones, firmas ni QC.

La [cola](../cola/ESTADO.md) contiene los 39 encargos y sus PR/SHA.
La [guía del dueño](../GUIA-REVISION.md) fue ejercitada mediante inicio real,
Magic Link solicitado desde UI y Mailpit, no mediante un token inventado.
Los catorce recorridos siguientes amplían su primera vuelta de treinta minutos.

## Recorridos

| # | Recorrido | Resultado | Verificación y evidencia |
|---|---|---|---|
| 1 | Cuenta nueva → onboarding → primer proyecto/posición → precio → emisión | PASA | Invitación humana, correo verificado, una posición, precio aplicado y PDF real revisado antes de REV-A. [Evidencia](captures/aceptacion-final/cuenta-nueva/primera-cuenta.json) |
| 2 | Doce posiciones/bow/acoplado → margen aprobado → A → cambios → B → aprobación → anticipo | PASA con observaciones | Dueño decide margen; cliente pide cambio y elige B. Anticipo manual y saldo con Flow simulado declarado. [Evidencia](captures/aceptacion-final/cobranza/verificacion.json) |
| 3 | Revisión nueva y comparación A ↔ B | PASA | Doce posiciones comparadas; hashes/bytes de ambos PDF conservados tras revisar, pagar y recargar. [Evidencia](captures/aceptacion-final/cobranza/verificacion.json) |
| 4 | Compra → recepción parcial/daño → cancelar saldo → recomprar → stock/RT | PASA con observaciones | Solo unidades útiles aumentan stock; cancelación conserva recepción; compra y retazos derivados del motor. Existencias iniciales de remake declaradas DEMO. [Evidencia](captures/aceptacion-final/compras/compra-recepcion-cancelacion.json) |
| 5 | Liberar → tablero → operario → QC FAIL/remake/PASS → etiquetas → despacho | PASA con observaciones | Cuatro unidades en tablet; rechazo de pieza y reposición del supervisor; plan nuevo, embalaje y despacho. Ensayo físico con datos DEMO. [Evidencia](captures/aceptacion-final/produccion/verificacion.json) |
| 6 | CNC compatible e incompatible; operaciones sin autoridad | PASA con observaciones | 34 piezas, diez brechas declaradas; PASS/WARN/BLOCK con causa, revisión humana y bytes del intercambio. No conexión ni calibración de máquina real. [Evidencia](captures/aceptacion-final/cnc/recorrido.json) |
| 7 | IA editor: proponer → preview → aplicar → deshacer → auditoría; cancelar/reintentar | PASA | MiMo real, simulación determinista, clic humano, deshacer auditado; cancelación comprobada también desde RUNNING. [Evidencia](captures/aceptacion-final/ia-editor/verificacion.json) |
| 8 | Cinco roles, dos organizaciones e IDs adivinados | PASA | OWNER con MFA, ESTIMATOR, WORKSHOP_MANAGER, OPERATOR, INSTALLER. Ajeno e inexistente reciben igual 403/404; sin datos del tenant B. [Evidencia](captures/aceptacion-final/roles/verificacion.json) |
| 9 | Calendario → pago manual → enlace por saldo → saldo cero | PASA con observaciones | RC-0001/RC-0002 únicos, retorno/replay idempotentes y saldo 0. Flow simulado y SII interno explícitos. [Evidencia](captures/aceptacion-final/cobranza/verificacion.json) |
| 10 | Catálogo: ingesta IA PDF/XLSX → revisar/publicar; plantilla manual | PASA con observaciones | MiMo real, fuente idéntica y correcciones humanas con evidencia. Readiness coincide con gate; lo que carece de límites sigue incompleto. Fuente sintética DEMO, sin certificación. [Evidencia](captures/aceptacion-final/catalogo/) |
| 11 | Tipologías × vidrios × bicolor/extras × vano/fabricación × PDF/portal/OT/3D | PASA con observaciones | 175 positivos y 35 negativos: 35 tipologías, cuatro recetas principales y templado. 175 paridades de OT y PDF; 350 vistas editor/3D en ambos temas. Junquillo ausente bloquea laminado monolítico. [Evidencia](captures/aceptacion-final/dominio/) |
| 12 | Suite IA1 con proveedor real | PASA con observaciones | 26 casos, 21 PASA; E/J 18/21 (85,71 %). Cero cifras finales sin respaldo y cero acciones consecuentes automáticas. Se conservan cinco fallos. [Evidencia](captures/aceptacion-final/ia-suite/resumen.json) |
| 13 | Medición/rectificación → revisión/producción → instalación/firma → incidencia/postventa | PASA con observaciones | Diff de precio del motor, visita cerrada, firma/acta y evidencia congelada; diagnóstico y remake humanos. Foto/firma de ensayo DEMO. [Evidencia](captures/aceptacion-final/terreno/verificacion.json) |
| 14 | Analítica: real vs. cotizado, cierre y causa del desvío | PASA con observaciones | F6 hasta movimiento valorado, preview, registro y corrección aditiva, CSV y preferencias persistentes. Tarifas/costos del oráculo DEMO no acreditan contabilidad real. [Evidencia](captures/aceptacion-final/analitica/verificacion.json) |

## Dominio y autoridad

La matriz principal contiene 35 tipologías × cuatro recetas = 140 posiciones:
float monolítico, termopanel float, Low-E y termopanel laminado de seguridad.
El suplemento añade 35 templados monolíticos. Las 35 variantes de laminado
monolítico de 6,38 mm se rechazan por `bead_incompatible`; no se inventó un
junquillo ni se convirtió incompatibilidad en éxito. El laminado compatible
se verifica dentro del termopanel de seguridad.

Las autoridades adicionales de montaje, suministro y costo son sintéticas y
se declaran DEMO. Los costos de templado se copiaron literalmente de una tarifa
DEMO existente; el espesor proviene del preview del motor. Ninguna dimensión
o resultado de fabricación se calculó en el script de navegador.

Se compararon diseño guardado/reabierto, BOM completa, caras, extras,
dimensiones/precio del portal, montaje confirmado vigente y materiales sellados
de las 175 OT. El portal oculta por contrato los SKU privados de compra; esas
identidades se comparan en la OT. DOC-01 es comercial: se comprobaron dimensiones,
precio neto por posición, extras y total del motor, además del hash de sus bytes.
Los materiales se comprueban en BOM/OT, no se atribuyen a una tabla inexistente del PDF.

Para inspeccionar editor/3D se clonaron por API los dos proyectos emitidos en
borradores con diseño/BOM idénticos. Cada registro conserva hash de diseño y
cálculo. Los 280 registros principales y 70 de templado corresponden a ambos
temas y tienen PNG del editor, vista 3D y descarga del render. El archivo
`editor-3d.json` anterior a la corrección del fixture se conserva como diagnóstico privado.
La [QA visual](captures/aceptacion-final/dominio/qa-visual.json) registra revisión
manual de las 350 vistas 3D en ambos temas y las 175 elevaciones claras, con
hash por captura. No cuenta las elevaciones oscuras como revisadas manualmente;
su captura y paridad permanecen en la matriz automatizada y la revisión global.

Los PDF de dominio tienen 80 y 22 páginas: todas se renderizaron y revisaron;
ningún texto sale de la página. Se revisaron también todas las páginas de A/B,
acta y guía. Los originales con QR/capacidad de portal permanecen privados;
se publican hashes, paridad y resultado de QA, sin enlaces activos.

## Pase editorial por persona y superficie

Se recorrieron entrada, tarea y salida de estimador, dueño, jefe, operario,
instalador y cliente final. Claro/oscuro a 1440×900, 1280×800 y 1024×768;
390×844 en inicio, portal y workshop. PDF conserva su papel propio.
La rúbrica evalúa cada regla donde existe su componente: por ejemplo, las
manijas pertenecen al editor y la densidad de inspector no se exige a un acta.

| Regla | Criterio | Estimador | Dueño | Jefe | Operario | Instalador | Cliente |
|---|---|---|---|---|---|---|---|
| R1 | Números/unidades/Mono tabular | PASA | PASA | PASA | PASA | PASA | PASA |
| R2 | Radios e inglete | PASA | PASA | PASA | PASA | PASA | PASA |
| R3 | Jerarquía por borde/espacio y una superficie flotante | PASA | PASA | PASA | PASA | PASA | PASA |
| R4 | Naranja de intervención/marca | PASA | PASA | PASA | PASA | PASA | PASA |
| R5 | Croma teal común | PASA | PASA | PASA | PASA | PASA | PASA |
| R6 | Voz y vocabulario del taller | PASA | PASA | PASA | PASA | PASA | PASA |
| R7 | Densidad del inspector: ocho campos a 768 px | PASA | PASA | PASA | PASA | PASA | PASA |
| R8 | Cinco estados con causa | PASA | PASA | PASA | PASA | PASA | PASA |
| R9 | Papel sobre mesa | PASA | PASA | PASA | PASA | PASA | PASA |
| R10 | Selección con contorno/manijas | PASA | PASA | PASA | PASA | PASA | PASA |
| R11 | Íconos monolínea 1,5 px, DIN y vista declarada | PASA | PASA | PASA | PASA | PASA | PASA |
| R12 | Foco y teclado | PASA | PASA | PASA | PASA | PASA | PASA |
| R13 | Movimiento ≤ 280 ms y reducción | PASA | PASA | PASA | PASA | PASA | PASA |
| R14 | Una acción principal por región | PASA | PASA | PASA | PASA | PASA | PASA |
| R15 | Fuente y Sin dato | PASA | PASA | PASA | PASA | PASA | PASA |
| R16 | Sin degradado/blur/brillo/morado | PASA | PASA | PASA | PASA | PASA | PASA |
| R17 | Anchos y textos legibles | PASA | PASA | PASA | PASA | PASA | PASA |
| R18 | Acciones reales y código único | PASA | PASA | PASA | PASA | PASA | PASA |
| R19 | Momento de firma | PASA | PASA | PASA | PASA | PASA | PASA |
| R20 | Capacidad del motor del §8 | PASA | PASA | PASA | PASA | PASA | PASA |

| Superficie y personas | R1–R20 | Firma preservada | Capacidad comprobada |
|---|---|---|---|
| Acceso/onboarding/Hoy · todos los roles | PASA | F3/F7/F10 | Acceso por rol y tarea con consecuencia; primera obra real |
| Proyecto/edición/lote · estimador/dueño | PASA | F1/F4/F5/F6/F7 | Cambio global con diff del motor, aplicar/deshacer |
| Precios · estimador/dueño | PASA | F6/F7 | Cascada que cierra, margen y aprobación humana |
| Emisión/PDF/revisiones · estimador/dueño | PASA | F1/F2/F6/F11 | Checklist, preview de PDF real y revisión inmutable |
| Portal/alternativas/pago · cliente | PASA | F1/F6/F11 | Elegir revisión, consentimiento y retorno idempotente |
| Producción/corte/calidad/etiquetas · jefe/operario | PASA | F2/F6/F7/F9/F10 | Barra/pieza/RT, rechazo y remake, siguiente paso |
| Compras/recepción/inventario · jefe | PASA | F2/F6/F7 | Comprar faltante contra stock/RT y recibir solo lo útil |
| Catálogo/ingesta/fuentes · dueño/jefe | PASA | F1/F6/F7 | Diff, revisión/publicación y readiness derivado |
| IA/Orb/trabajos · estimador/dueño/jefe | PASA | F6/F7/F8 | Operaciones tipadas, simulación, confirmación y deshacer |
| Despacho/terreno/postventa · jefe/instalador | PASA | F2/F6/F7/F9/F11 | Unidad, foto/firma, evidencia congelada y rectificación |
| Analítica · dueño/jefe | PASA | F6/F7 | Real/cotizado y causa hasta el movimiento |
| 3D/térmica · estimador/cliente | PASA | F5/F6/F11 | Pose y caras físicas; alternativa térmica con autoridad |
| Empresa/clientes/ajustes · dueño | PASA | F6/F7/F10 | Preferencias persistentes, integración/autoridad explícitas |

Ronda 1: se quitaron el import eager del lienzo en autenticación, las rutas DEV
del build y la semántica de opción que escondía controles de fila. Mejoraron
la entrada pública, el teclado y la selección de una obra de cien posiciones.

Ronda 2: se corrigieron contraste de campos, objetivos táctiles de workshop y
jerarquía accesible de títulos/etiquetas. Se retiraron descargas duplicadas de
autoridad y ejemplos numéricos de esquemas IA. F2/F6/F11 y el consentimiento
humano se conservaron. Véase [P20-ARRANQUE](P20-ARRANQUE.md) y #154 para cambios/tests.

## Verificaciones globales

Matriz UX de 912 vistas: 0 hallazgos de los detectores, 0 overflow y 0 axe
serious/critical. Las rutas corregidas se recapturaron con el mismo protocolo,
detectores, roles, temas y anchos; `report.json`/`index.html` muestran la matriz
fusionada y la ref de cada registro. La selección conserva la línea base de
rutas sin cambios. No se vació `topFindings` para ocultar resultados.

Ningún hallazgo axe moderado o menor.

El build de producción pasa el test automatizado de residuos de demo y rutas
DEV. El catálogo DEMO marcado permanece por intención; no se presenta como
una autoridad certificada. [Gates](captures/aceptacion-final/gates.json):
`make lint`, `make typecheck`, `make test`, `make build`, `make test-db` PASA.
Motor 1.064 (+2 xfail históricos), backend 1580, frontend 1147; pgTAP 1.483,
integraciones/RLS 601, E2E 19 y trece upgrades PG16. No se debilitó ningún check.

Guardas: 257 claves/716 instancias al inicio → 33/118; reducción de 224 claves
y 598 instancias. Los residuos del trinquete se conservan con su excepción
explícita; una coincidencia de fuente no equivale a un hallazgo visible.

| Guarda | Antes | Después | Delta |
|---|---|---|---|
| display-tofixed | 102 | 79 | -23 |
| exclamation-copy | 9 | 3 | -6 |
| gradient | 2 | 0 | -2 |
| heavy-weight | 7 | 0 | -7 |
| inline-color | 355 | 19 | -336 |
| literal-font-size | 90 | 0 | -90 |
| literal-layer | 6 | 2 | -4 |
| motion-over-280 | 23 | 0 | -23 |
| radius-over-4 | 88 | 1 | -87 |
| raw-enum-render | 19 | 11 | -8 |
| shadow-outside-scale | 15 | 3 | -12 |

## Rendimiento

| Operación | Muestras | p50 ms | p95 ms | Resultado |
|---|---|---|---|---|
| abrir-posicion | 12 | 306.83 | 720.20 | PASA |
| recalcular-precio | 12 | 916.48 | 971.85 | PASA |
| abrir-ot-obra-cien | 12 | 693.48 | 799.21 | PASA |
| Portal móvil 4G, contexto frío | 12 | 2949.26 | 2972.86 | PASA |

Interacciones desde sesión preparada, hasta resultado visible y dos cuadros;
reprecio incluye debounce de 180 ms y exige cascada del motor que cierra.
La obra de cien posiciones tiene cien OT: se mide abrir una de sus OT,
respetando el modelo real de una OT por posición. No se inventó una OT de cien.
Las corridas de medición no comparten gates ni capturas concurrentes.
Los percentiles usan rango más cercano, ceil(n × p); con doce muestras el p95
es la mayor observación. Las series originales permanecen publicadas.
Se espera el precio real del editor entre muestras de apertura, fuera de su
intervalo. El observador de pantalla usa requestAnimationFrame y comprueba
después las mismas condiciones con Playwright. Se conservan dos diagnósticos
no aprobados: espera escalonada de aserciones y SQL de editores abandonados.
La corrección reduce 947 consultas a 131 por propuesta, preserva listas
congeladas, RLS/MFA y rechazos por autoridad. Véase
[rendimiento](P20-RENDIMIENTO.md) para protocolo, línea base y límites.

Portal: 390×844, 150 ms de latencia, 1,6 Mbps bajada y 750 kbps subida,
doce contextos fríos, autenticación fuera del intervalo. Antes p50/p95
8.871,22/9.373,35 ms → 2.949,26/2.972,86 ms. No se generaliza esa muestra a
infraestructura productiva. La carga fría del editor/3D sigue separada de
interacción y se conserva como límite P2-1.

## IA real, resultado y límites

MiMo-V2.6-Pro real: 21/26 y E/J 18/21 (85,71 %, umbral ≥85 %).
49 intercambios/89 eventos de uso; fuente ejecutada y estado persistente sin
alteración por el evaluador. Los fallos conservados son E04 (HTTP 524),
J04 (falta claim estructurado), J08 (proveedor), F02 (falta artefacto de corte)
y F03 (falta plan de compra). La tasa no acredita éxito de esos cinco casos.

La auditoría numérica recorre 24 respuestas finales, avisos, claims,
artefactos, planes y preguntas contra verdad/herramientas calculadas por el
servidor y pedido explícito. No toma la salida del modelo como fuente.
Cero canales finales con cifras sin respaldo y cero acciones consecuentes
automáticas. Dos rondas rechazadas (E11 «20 cm», G01 «2000» sin contexto)
permanecen registradas. Dos errores no produjeron respuesta final. La auditoría
numérica no transforma un fallo semántico en un caso aprobado.

## Registro, decisiones y lo que conecta el dueño

[Registro histórico](phase14-findings-registry.md): 343 entradas clasificadas,
331 resueltas, ocho descartadas y cuatro vigentes. Se conserva su evidencia
histórica y se añade la lectura actual de cada superficie; P20 no afirma
reproducir individualmente las 343 auditorías antiguas.

| Prioridad | Límite vigente | Causa y acción |
|---|---|---|
| Alta · F25 | Boleta SII 39 real | Timbrador actual admite 33/61. Requiere proveedor autorizado con contrato 39; el simulador no sustituye esa implementación. |
| Alta · F26 | Entrega fiscal productiva | Certificado/CAF/transporte y certificación del contribuyente externos; no se envía dinero/documento fiscal real en aceptación. |
| Media · A6 | Precio unitario de compra Sin dato | Falta la lista comercial autorizada del proveedor; cantidades y recepciones son explícitas. El dueño debe cargar su fuente de precio. |
| Media · P2-1 | Primera carga fría de editor/3D | Descarga/render WebGL y catálogo inicial; se informa separada de interacción caliente, sin fabricar una medición <1 s. |

Las decisiones están en [valores por defecto](../decisions/valores-por-defecto.md).
Railway/hosting, Supabase productivo/Storage privado, Flow de la empresa,
SII 33/61 y proveedor 39, correo comercial + Auth, dominios/webhooks, fuentes de
catálogo/precios/vidrio/térmica/montaje y calibración CNC se conectan siguiendo
[ACTIVACION](../operations/ACTIVACION.md). IA ya está conectada localmente; su
tarifa y presupuesto se revisan en Ajustes › Inteligencia artificial.

## Integridad de la entrega

Se publican evidencia sintética y hashes, sin `.env`, valores de credenciales,
JWT, URLs firmadas ni capacidades activas de portal. La compresión PNG conserva
los píxeles y su hash RGBA. Los recursos propios se detienen al cierre y la base
REVIEW se conserva para el arranque del dueño.

El PR final `integracion/v1` → `main` se integró por instrucción del dueño
mediante [PR #157](https://github.com/KaraAliOsman/framedex/pull/157), squash
`2db4e13171884b93a989e68508a55f5590f9b34d`, con los cuatro checks en verde.
Los números anteriores acreditan la muestra
ejercitada y los límites declarados, no fabricación, tributación ni producción
de una empresa que aún no conectó sus autoridades reales.

## Integración del cierre P20

[PR #156](https://github.com/KaraAliOsman/framedex/pull/156), squash `c99d25b577cc2726d28465dbab59f142c2c7cd73` en `integracion/v1`. CI **4/4 PASA** sobre `c8ac0612aa1ff10008ab666c9527eccc67a9bc4c`: Lint & Typecheck, Test Suite, Frontend Build y Database Gate. ESTADO registra los 39 encargos cerrados. PR #157 integra posteriormente el programa a main.

La limpieza posterior conserva íntegra `captures/aceptacion-final/`. Las rondas
visuales anteriores se consultan mediante [el mapa de evidencia](captures/README.md),
sin alterar resultados, recibos ni refs de esta aceptación.
