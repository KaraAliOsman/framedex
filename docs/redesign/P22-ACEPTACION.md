# P22 · empresa, clientes y ajustes

El dueño configura su empresa por secciones y el estimador encuentra la ficha
con sus contactos, obras, cotizaciones, cobros y notas. Elegir una dirección
de obra copia su texto al proyecto; facturación y entrega permanecen separadas.
La configuración puede probarse sobre un PDF real antes de guardarse.

## Recorridos y autoridad

El recorrido crea por UI una empresa con RUT válido, dos contactos y dos
direcciones. Un duplicado canónico se rechaza. Desde la ficha se crea una obra
eligiendo la dirección Sur, se calcula con el motor, se aplica el precio y se
emite con clic humano. El DOC-01 descargado conserva esa dirección y su
cabecera coincide con el importe aplicado. La ficha enlaza la obra y su revisión.

La fusión presenta ambas fichas, exige motivo, confirmación y revisiones
vigentes. El destino recibe contactos y direcciones con procedencia; el origen
queda como alias histórico. No cambia los proyectos ni sus snapshots. El
recorrido verifica el PDF anterior byte a byte y el historial de fusión.
Las pruebas PostgreSQL comprueban edición concurrente de hijos, orden de
bloqueos y revisión CAS: una edición posterior impide aplicar una revisión vieja.

Los saldos usan la elección acordada de P10 y el ledger vigente. El motor
agrega con Decimal por moneda. Una obra sin importe acreditado permanece
«Sin dato» y no aporta un cero ficticio. Personas, empresas y tipo histórico
desconocido son distintos; no se inventa autor ni identidad de una ficha antigua.

Empresa, marca, usuarios, comercial, documentos, numeración, producción,
integraciones e IA tienen navegación y permisos por rol. Los controles
reutilizan los consumidores de vigencia, papel, condiciones, precios, extras,
montaje, retazos, estaciones, presupuesto y adaptadores ya integrados.
La numeración consulta secuencias reales, solo como referencia sin reserva.

`quotation_currency` propone la moneda nueva y `currency` conserva la moneda
base de las tarifas por m². Las listas y acuerdos mantienen su propia moneda.
El test de consumo verifica ambas direcciones con tasa, fecha y fuente
declaradas, y rechaza la falta de FX. Las tarifas 9/18 USD se consumen como
8.505/17.010 CLP con buffer contractual del 5 %; tarifas locales 9/18 CLP
se cotizan como 0,01/0,02 USD a 900 pesos por dólar, sin inventar una reserva
de importación. El replay congelado coincide con el cálculo. El golden nuevo
añade el caso CLP→USD; los golden anteriores permanecen byte a byte. No se
infiere una tasa ni una moneda UF.

La vista previa usa una revisión validada por su huella y el renderer DOC-01
común. Cambiar marca, papel, pie y condiciones conserva el precio y moneda
sellados de referencia, sin modificar su artefacto. Sin revisión muestra causa
y enlace a Documentos de la obra. Guardar Empresa propaga su revisión a Marca
antes de anunciar éxito, sin descartar el borrador. La prueba comprueba A4,
vigencia de 23 días y pie nuevo, con snapshot histórico intacto.

El dueño mantiene MFA obligatorio; exigirlo al resto es una política opcional
que API y RLS aplican, conservando el acceso mínimo para configurar su factor.
El último dueño no puede desactivarse. Invitar prepara acceso Auth sin membresía,
cifra la capability en la outbox, entrega por SMTP sandbox y exige correo vivo
verificado más aceptación humana. La primera aceptación prevalece; revocar,
vencer o desactivar conserva auditoría. El recorrido invitación→correo→acceso
→rol→desactivación pasa; no se reenvían invitaciones para repetir evidencia.

El alta inicial confirma Empresa, Comercial y Documentos con valores sugeridos
editables, y continúa por serie, cliente, primera obra y editor. El recorrido
termina en la nueva obra real; no se inventa una miniatura con precio.

## Evidencia visual y estados

- [Antes](captures/clientes-ajustes/antes/): 24 vistas de clientes, ajustes y
  alta, dueño/estimador, 1440/1024 y ambos temas.
- [Recorrido](captures/clientes-ajustes/recorrido/): cliente y dirección,
  duplicado, emisión, PDF, fusión, marca viva, invitación y alta.
- [Estados](captures/clientes-ajustes/estados/): diez capturas de vacío,
  carga, error, sin permiso y bloqueo. Carga/503 se inyectan únicamente en
  transporte Playwright; fusión, denegación y falta de revisión son estados reales.
- [Ajustes](captures/clientes-ajustes/ux/ajustes/index.html): nueve secciones,
  tres roles, cuatro tamaños y ambos temas. Empresa y Comercial tienen
  repeticiones finales con la corrección de tarifas y Marca.
- [Clientes](captures/clientes-ajustes/ux/clientes/index.html) y
  [alta](captures/clientes-ajustes/ux/alta/index.html): mismos tamaños/temas,
  dueño/estimador. El operario tiene su denegación real en Estados.
- [Precios](captures/clientes-ajustes/ux/precios-final/index.html): controles
  de moneda y fuente explícita. El recorrido USD produce US$ 582,20 con la
  observación DEMO a 900 pesos por dólar, sin aplicar ni emitir ni modificar
  el acuerdo CLP. `moneda-fx.json` conserva el resultado de API y navegador.

Las matrices finales suman **280 vistas únicas**: 216 de ajustes, 32 de
clientes, 16 de alta y 16 de Precios. Todas pasan sin hallazgos, desbordes,
errores HTTP ni consola. La inspección visual adicional confirma la comparación
y las posiciones móviles, además de la fuente y tasa completas del selector.

La captura de Precios usa `DEKOPEN_UX_SERIAL=1`: en este entorno las cuatro
navegaciones concurrentes saturaron el cálculo y agotaron el timeout de 45 s.
El modo secuencial conserva tamaños, roles, temas, espera y detectores; la
ejecución concurrente sigue siendo el valor predeterminado de la herramienta.

Chromium completo muestra el PDF incrustado real, inspeccionado en el recorrido.
El headless-shell de captura oficial deja en blanco el visor nativo del iframe;
esa limitación de captura no se atribuye a un PDF vacío. La primera página del
PDF descargado confirma contenido; el artefacto privado no se publica.

## Dos rondas editoriales

Primera ronda:

1. Se elimina el muro de ajustes y su CSS muerto; una sección explica el
   efecto y deja una acción principal por tarea.
2. La ficha básica se reemplaza por contactos y direcciones reutilizables,
   cuenta por moneda e historial con enlaces reales, sin duplicar proyectos.
3. La vista de documento usa renderer/snapshot real; sin
   referencia hay una causa y destino concreto.

Segunda ronda:

1. Guardar Empresa y Marca coordina CAS antes del éxito; elegir la misma
   obra conserva la revisión. Las etiquetas de vigencia, retazos y pie legal
   tienen nombres accesibles sin ambigüedad.
2. Se corrige la retícula de checkboxes en Documentos/alta y se tokenizan los
   campos de Marca. No quedan controles nativos sin foco o texto cortado.
3. Las tarifas declaran moneda base y formato Money/Mono; los enlaces de
   historial usan teal y foco, y las acciones deshabilitadas conservan texto legible.
   La inspección adicional de Precios corrige las filas superpuestas a 390 px:
   cada valor conserva su etiqueta y fuente. La observación de cambio conserva
   su precisión real sin ceros de relleno, y declara la fuente junto al selector.

Firma: PDF real sobre papel, con cajetín/huella y marca en preparación. La idea
del §8 funciona: estados comprobados de adaptadores e instrucciones que se
leen de ACTIVACION, más valores sugeridos editables y confirmados en el alta.

## Observaciones de revisión del PR

La dirección editada se conserva en API parcial, con el mismo selector y en
escritura directa bajo RLS: el cambio explícito desvincula la dirección maestra.
Seleccionar otra dirección vuelve a copiar su texto. Editar una revisión nueva
conserva el snapshot y la huella de la anterior. Las tres variantes fallaban
antes de la corrección y pasan con PostgreSQL real.

El endpoint de estaciones ya era un upsert por `(org_id, code)`. La observación
de que siempre creaba una fila no se reproduce: devuelve 201 al crear y 200
al actualizar, con el mismo ID. El formulario ahora conserva el código al
editar y ofrece cancelar; la regresión comprueba identidad y número de filas.

El directorio filtra, cuenta y pagina en SQL; los contactos/direcciones se
cargan por lote únicamente para la página. El filtro de saldo lee acuerdos
y pagos por lote y sigue usando el motor con Decimal y monedas separadas.
La prueba de mil coincidencias exige consultas acotadas, página final y offset
vacío; la de fusión contrasta aliases, obras activas y saldo con el dossier.
Las 16 integraciones focales y la regresión del formulario de estación pasan.
Los [recorridos de revisión](captures/clientes-ajustes/revision/recorridos.json)
registran tres flujos reales y 36 vistas en ambos temas y 1440/1280/1024,
sin hallazgos ni desbordes. La matriz `ux:capture` revalida además las rutas
de Producción y Clientes por rol, tema y los cuatro tamaños del contrato.

## Rúbrica editorial

| Ítem | Resultado | Evidencia |
|---|---|---|
| R1 | PASA | Dinero y tarifas en Mono tabular, moneda/unidad y fechas chilenas. |
| R2 | PASA | Radios de tokens ≤ 4 px; inglete en hoja/documento. |
| R3 | PASA | Secciones y reglas por borde; una confirmación flotante. |
| R4 | PASA | Naranja conserva marca y atención humana. |
| R5 | PASA | Teal en enlaces, foco y controles de ambas superficies. |
| R6 | PASA | Persona/empresa, obra, rol y revisión en español; sin IDs visibles. |
| R7 | PASA | Ajustes por tarea y ficha con historia; cuenta del operario táctil. |
| R8 | PASA | Cinco estados y causas/destinos comprobados. |
| R9 | PASA | PDF real en hoja sobre mesa, mismo renderer DOC-01. |
| R10 | PASA | Ficha/sección elegida con contorno, tinte y texto. |
| R11 | PASA | Iconografía común y elevación del renderer sellado. |
| R12 | PASA | Labels explícitos, foco tokenizado, controles por teclado. |
| R13 | PASA | Sin movimiento ornamental; reduce-motion común. |
| R14 | PASA | Una acción por formulario/región; consecuencias confirmadas. |
| R15 | PASA | Snapshot/motor/ledger y FX; faltantes con causa. |
| R16 | PASA | Sin degradado, blur, brillo ni morado IA. |
| R17 | PASA | 1440/1280/1024/390, claro/oscuro; matriz final sin desbordes. |
| R18 | PASA | Cliente, obra, nota, fusión, configuración e invitación tienen efecto real. |
| R19 | PASA | Marca/condiciones en PDF vivo con documento histórico intacto. |
| R20 | PASA | Integraciones verificadas y guía de activación consumida desde la fuente. |

## Validación y límites

Los cuatro gates completos sobre `a3bffc10c4ea43f9bec221a47ecaaefbe2b15bfa` pasan: lint, tipos, build, 903 tests de motor (+2 xfail preexistentes), 1494 de backend y 1014 de frontend. Golden byte check PASA; los golden anteriores conservan sus bytes. Database Gate completo sobre la misma revisión PASA: 1389 pgTAP en 93 archivos, 535 integraciones, 19 Auth E2E y once programas de upgrades poblados PostgreSQL 16. Las 280 vistas de aceptación se conservan; la revisión revalida otras 40 rutas y 36 vistas de los formularios afectados. El [registro de validación](captures/clientes-ajustes/validacion.json) conserva refs, recuentos y hashes de logs locales. La CI se verifica antes del squash.

La identidad fija y restaura tanto el JWT JSON como el subject individual
que prioriza PostgreSQL. Incluye contextos anidados, workers y transacciones
especiales de cálculo, congelación y preparación/emisión guiada. Las 33
regresiones focales usan Auth real y comprueban un subject residual y su
restauración al salir. Los actores de integración son explícitos, sin depender
de identidad residual ni reducir assertions de replay, aislamiento o
inmutabilidad. El probe consulta las variables de sesión sin ampliar los
permisos del rol comercial sobre Auth.

El material en camino usa una proyección privada de identidad y cantidad
física por empresa/rol; el estimador no recibe órdenes, precios ni líneas
privadas de proveedor. Las regresiones RLS y la comprobación de navegador
de dueño, estimador y operario conservan denegaciones de escritura. El
[recorrido de identidad](captures/clientes-ajustes/recorrido/identidad-verificada.json)
registra esa comprobación sin capabilities ni respuestas privadas.
La unicidad canónica conserva aliases y colisiones históricas de RUT;
las siete regresiones de conducta comprueban duplicados, edición, tenant
y fusión. Las comprobaciones de acceso/expiración conservan su volatilidad
real, sin bajar filtros ni niveles del lint SQL.

Hosting, SMTP/dominio, Flow y DTE productivos requieren activación externa
según [ACTIVACION](../operations/ACTIVACION.md). Sus adaptadores/sandbox
funcionan; la invitación verificada usa Mailpit. El catálogo y las tarifas
del fixture conservan DEMO. La preferencia de moneda no revaloriza acuerdos,
no cambia la base de tarifas y no altera secuencias. El visor nativo blanco
del headless-shell conserva la limitación documentada en Evidencia visual;
Chromium completo y el PDF descargado sí muestran el documento real.
Los procesos propios están detenidos y el fixture persistente se conserva.
