# Valores por defecto del programa DEKOPEN v1

Fuente inicial: `docs/design/CONSTITUCION.md`, seccion 11. Los encargos siguientes deben mantener esta tabla cuando implementen o cambien un valor configurable.

## P08 · preparación, emisión y vigencias (2026-10-09)

- Cotizaciones nuevas: 15 días corridos desde la fecha de America/Santiago,
  configurables de 1 a 365 en Ajustes > General > Documentos. Cada cotización
  puede cambiar la fecha antes de emitir. Preparaciones históricas conservan
  su fecha o su ausencia; un PDF emitido nunca consulta el default actual.
- Revisión privada del PDF: 30 minutos, configurable de 5 a 60 en la misma
  pantalla. Da tiempo para revisar doce posiciones y limita autorizaciones
  antiguas. La caducidad y cualquier cambio de snapshot exigen otra vista.
- Anticipo inicial: 50 % al aprobar y 50 % contra entrega; calendario editable
  por organización y cotización. El motor valida las participaciones y calcula
  los montos. Plazo, instalación, exclusiones y garantía son declaraciones
  obligatorias. No se inventa plazo de producción ni plazo de garantía.
- Vencimiento del enlace separado de la vigencia comercial del documento.
  El estimador o dueño puede declarar una fecha futura hasta 365 días desde
  ahora, con comparación y confirmación. Se agrega historial; la identidad
  DOCUMENT de P09 permanece intacta. La hora del control es la del navegador,
  declarada en la ayuda; el historial presenta America/Santiago.
- Regenerar revoca el enlace seleccionado y crea un acceso nuevo a la misma
  revisión. No reenvía correo ni reemplaza el QR impreso automáticamente.
  Su reintento conserva el mismo recibo. Una respuesta comercial anterior no
  se borra; otro acuerdo exige una sucesora y nueva emisión/confirmación.
- La confirmación exige PDF verificado y cargado, destinatario y consecuencia
  concretos. La emisión usa el outbox existente. No se agrega un proveedor
  alternativo ni se presume entrega SMTP única; sandbox Mailpit sigue activo.


## P03 · trabajo por rol (2026-10-09)

- Cola: vencidos, bloqueos, trabajo del día y seguimiento, orden determinista
  del motor. Son hechos del dominio; el filtro visual no cambia consecuencias.
- Solo el operario entra automáticamente en producción. Los demás entran a
  Hoy; todos conservan ambas rutas según permisos. El riel puede contraerse
  desde el shell, con preferencia local; bajo 1024 se vuelve drawer.
- Venta por fase separada por moneda, sobre totales emitidos vigentes. No se
  presenta como ingreso contable. Cobranza sin fecha sigue como saldo, no vencida.
- Leer una notificación es un clic explícito; abrir la campana no la reconoce.
  Política comercial y banda continúan configurables en Ajustes › Precios.
- Despacho/instalación se abren en la ruta existente de producción mientras
  conservan su agenda y evidencia; no se agregan secciones vacías.

## P07 · precios y aprobación (2026-10-09)

- Banda inicial: mínimo 25 %, objetivo 35 %, máximo 60 %; descuento superior
  a 10 % también requiere aprobación. Ajustes › Precios abre las reglas para
  el dueño. La migración conserva objetivos anteriores ampliando la banda
  inicial cuando corresponde; no sustituye una autoridad histórica.
- El margen solicitado inicia en el objetivo declarado de la organización.
  Se recalcula con el motor al moverlo; el margen logrado y la utilidad
  pertenecen al dueño/jefe de taller. El estimador recibe solo venta mediante
  allowlist y nunca un costo oculto en una traza o autoridad anidada.
- CLP es la moneda inicial del formulario. USD y UF requieren un snapshot FX
  declarado y fechado. Listas, tarifas, IVA y FX se administran por el dueño;
  no se presume una cotización de cambio ni un costo ausente.
- El repricing aplica cantidad, medidas, vidrio, herrajes, diseño, lista de
  costos, FX, lista comercial, margen, descuento, segmento, servicios e
  impuesto. Una interacción corresponde al impulsor posterior. Son reglas de
  explicación determinista, no preferencias que cambien el precio.
- Se conservan los redondeos de venta: unitario indicativo a cuatro decimales
  HALF_UP, neto redondeado por línea e IVA por proyecto. La compra mantiene el
  Decimal consumido y la cascada no incluye un ajuste residual. Las trazas
  muestran el unitario exacto: multiplicar el mostrado puede diferir del neto.
- Las operaciones históricas sin autoridades congeladas suficientes muestran
  Sin dato con su causa en la explicación. Permanecen legibles y selladas;
  no se reconstruyen con el catálogo vigente ni se reparte el Δ estimándolo.
- Decisiones sin leer: recibo inmutable por organización/operación/solicitante.
  Marcar leída es idempotente. Hoy/campana conservan la decisión hasta ese clic.
  La consulta de historial admite las últimas 100 operaciones por organización.

## P25 · marca, entrada y correo (2026-10-08)

- Dirección B y Plex Sans 600 convertida a contornos; corrección óptica solo en
  marca inferior a 24 px y favicon. La cota D se reserva a Acerca de y correo.
  Son contratos de identidad del producto, sin variantes arbitrarias en Ajustes.
- Onboarding de cuatro pasos: serie vigente, cliente, obra y primera posición.
  Pide solo nombres; el contacto queda en divulgación progresiva. Usa las series
  que ofrece el motor; una respuesta perdida solo adopta una coincidencia fresca
  única con el mismo cliente y todos los campos enviados. Guarda por organización.
- Color de organización: teal-800, hexadecimal de seis caracteres, contraste
  mínimo 4,5:1 contra paper. Ajustes › Identidad permite cambiarlo y explica el
  fallback. Las emisiones nuevas sellan color y pies; las antiguas no se alteran.
- Atribución documental oculta y portal discreto visible por defecto. Ambos pies
  se configuran en Ajustes › Identidad para emisiones nuevas. Los correos al
  cliente conservan siempre su emisor, sin marca de plataforma.
- Avisos internos desactivados. El dueño declara el correo del encargado y los
  activa en Ajustes › Identidad. Aprobar o bloquear una OT registra el aviso;
  enviar al cliente exige vista previa y clic explícito.
- Proveedor de correo `sandbox` con Mailpit; SMTP TLS se configura en el servidor
  siguiendo ACTIVACION.md. El contenido se cifra y permanece sellado. SMTP no
  garantiza entrega única: una respuesta perdida o worker interrumpido muestra
  «Entrega sin confirmar». No se reenvía hasta comprobar ausencia y confirmarla.
- El correo comercial presenta el PDF sellado antes de confirmar y liga el
  clic al SHA revisado. La intención se conserva en la sesión del navegador
  después de una respuesta perdida o recarga; otra confirmación crea un envío
  nuevo. Son garantías de autorización e idempotencia, sin preferencia que las
  desactive. Un enlace revocado conserva su historia y conduce a una nueva
  revisión/confirmación en la cotización vigente.

| Decision                   | Valor por defecto                                                                                               | Donde se cambia                   | Estado      | Encargo que la implementa |
| -------------------------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------- | ----------- | ------------------------- |
| Papel de los documentos    | Carta                                                                                                           | Ajustes > Documentos              | por defecto | P09                       |
| Anticipo                   | 50 % al aprobar, saldo contra entrega; calendario editable y montos derivados por el motor | Ajustes > General > Documentos | implementado | P08 |
| Validez de la cotizacion   | 15 días corridos; configurable de 1 a 365, editable antes de emitir | Ajustes > General > Documentos | implementado | P08 |
| Garantia                   | Plantilla editable sin plazo inventado; obligatoria antes de preparar el PDF | Ajustes > General > Documentos / Cotización | implementado | P08 |
| Plazo de entrega           | Declaración obligatoria por cotización cuando no existe autoridad de producción | Cotización | implementado | P08 |
| Revisión privada del PDF   | 30 minutos; configurable de 5 a 60, sin alterar revisiones previas | Ajustes > General > Documentos | implementado | P08 |
| Banda de margen            | Mínimo 25 %, objetivo 35 %, máximo 60 %; fuera de la banda requiere aprobación del dueño                           | Ajustes > Precios                 | implementado | P07                       |
| IVA                        | 19 %, precios netos en la app y total con IVA en el documento                                                   | Ajustes > Impuestos               | por defecto | P07                       |
| Pie "Generado con DEKOPEN" | Oculto en documentos del cliente (white-label); visible solo en el portal, discreto                             | Ajustes > Documentos              | por defecto | P09                       |
| Nombre del asistente       | "Asistente DEKOPEN" con el Orb. No se usa "STARWIN"                                                             | Ajustes > Marca                   | por defecto | P17                       |
| Marca de la app            | Direccion B del estudio de identidad (`DEKOPEN` con la O como seccion de perfil)                                | P25                               | por defecto | P25                       |
| Moneda                     | CLP; USD y UF con snapshot FX declarado                                                                         | Precio del proyecto > Moneda y autoridades | implementado | P07                |
| Catalogo                   | Demo con precios aleatorios de semilla fija, marcado DEMO en todas partes                                       | Catalogo > Importar               | por defecto | D01/P16                   |

## P01 · contratos de presentación (2026-10-05)

Estos contratos técnicos aplican la constitución; no son preferencias comerciales configurables:

- Redondeo visible `ROUND_HALF_UP`, con strings Decimal y `BigInt`. Los payloads conservan la precisión recibida del backend mediante `decimalInputValue`.
- Texto atenuado pequeño: `text-small-muted` con AA. Se conserva g-500 para guías/anotaciones grandes; las unidades pequeñas usan la tinta accesible.
- Aperturas: prevalece la constitución §3.6 sobre el vértice inverso del estudio histórico. Vista interior por defecto; exterior reflejada y discontinua.
- Densidad: controles de 32 px en oficina, 44 px en taller, 40 px en documento y 44 px en documento móvil. El muestrario permite revisar las tres; los encargos de superficie conectarán la densidad y su tema al contexto de uso.

Las decisiones y los mecanismos se detallan en [Sistema v2](../design/SISTEMA-V2.md).

## D01 · autoridad e ingesta (2026-10-05)

- Catálogo de arranque: cinco series sintéticas y precios con semilla `20261005`.
  La semilla es una propiedad reproducible del fixture; el dueño carga y revisa sus
  fuentes en Catálogo › Importar. La selección de sistema y acabado es configurable
  por producto. Una importación no certifica automáticamente el catálogo.
- Sin autoridad de corte o límites, el producto nuevo se bloquea con causa y fuente
  faltante. No se adoptan descuentos ni capacidades silenciosos. El dueño los
  declara en Catálogo › Sistema › Parámetros o mediante la plantilla.
- Revisión: dueño o encargado de taller, con diff, confirmación explícita y
  procedencia. El estimador consulta. Los costos conservan el permiso de precios
  del dueño. Deshacer es atómico y se bloquea al usarse una autoridad.
- Productos guardados: preservar las fórmulas anteriores mediante autoridad
  histórica. No recalcular documentos emitidos; no mover catálogos comerciales ni
  composiciones mixtas. Las series históricas no se ofrecen a productos nuevos.
- MiMo de texto: admitir PDF con texto, planilla, correo y texto pegado. Una foto o
  escaneo sin texto muestra la limitación; no se simula OCR. IA3 verificará la ruta
  multimodal antes de habilitarla. El proveedor se configura en el backend y su
  credencial permanece exclusivamente en el entorno.

## D02 · vidrio y seguridad (2026-10-05)

- Las reglas de NCh 135/2 empiezan vacías. **Revisar ejemplos DEMO** propone zonas
  sintéticas de puerta, paño lateral, antepecho bajo y paño grande, con fuente y
  aviso. No transcribe ni certifica una norma. El dueño o encargado revisa el diff
  y configura fuente, zona, clases y obligatoriedad en Ajustes › Reglas de vidrio,
  o importa la norma aportada mediante Catálogo › Importar › Reglas de vidrio.
- Una regla es recomendación salvo obligatoriedad explícita. La ausencia de
  altura sobre el piso provoca revisión, sin presumir una altura segura.
- Masa del PVB: sin espesor, densidad y fuente no se muestra un peso estimado. El
  proveedor aporta esos campos en el compositor; Ug, g, transmisión y clase
  permanecen **Sin dato** hasta recibir su ficha. Las variantes exigen publicación
  revisada antes de asignarse al producto.
- El mínimo facturable y los recargos se configuran por producto mediante sus
  autoridades de precio. Un proceso declarado sin tarifa no se cotiza como gratis.
- El pedido mantiene los decimales del motor cuando existan y pide confirmar esa
  precisión con el vidriero. Las medidas enteras se imprimen sin decimales. No hay
  preferencia de redondeo que cambie la autoridad de fabricación.
- Las etiquetas enlazan a la aplicación mediante `DEKOPEN_PUBLIC_APP_URL`,
  configurada en el entorno de backend. El QR identifica el infill sellado y
  conserva el acceso autenticado del taller.

## D03 · aperturas y manillas (2026-10-06)

- Vista interior por defecto y gramática DIN de la constitución §3.6. El tablero
  histórico de iconos no cambia el lado de bisagras ni de manilla. La dirección
  se elige en la apertura compatible; la vista exterior continúa en P05.
- No se infieren capacidades ni alturas en un catálogo antiguo. El dueño o
  encargado configura movimiento, dirección, rol, kits, fuente, encuentro con
  inversor y regla de manilla en Catálogo › Ficha de serie o en su importación.
  Las nuevas autoridades DEMO v3 son versiones separadas y no certificadas.
- La altura de manilla toma centro, borde inferior o superior **de la regla
  declarada**. El estimador la edita dentro del rango del motor en Avanzado; las
  manillas de banderola/proyectante quedan en su borde de cierre y una pasiva no
  lleva manilla de accionamiento. No se usa una altura universal en Ajustes:
  corresponde al sistema/herraje, cuya fuente es configurable en Catálogo.
- La precisión del encuentro puede producir medios centésimos exactos. El
  motor conserva esos valores; los formatos de presentación no redondean el
  BOM ni el documento sellado a una autoridad distinta.

## D04 · herrajes y fabricación (2026-10-06)

- Clase automática: la prioridad pertenece a la familia de catálogo y solo se
  usa si la masa y las restricciones son decidibles. El técnico puede fijar una
  clase compatible en Avanzado, con diff, precio de herrajes y deshacer. Las
  prioridades y fuentes se revisan/importan en Catálogo; no hay capacidad global
  ficticia en Ajustes.
- Manilla, color y altura proceden de la clase. El rango es editable según su
  ficha; alturas fijas o referidas al borde superior se mantienen fijas. No se
  asigna una manilla activa a la hoja pasiva. D05 ampliará acabados de perfiles.
- Las opciones se ofrecen solamente si la fuente las declara. Un dato RC
  requiere su fuente; la seguridad sintética DEMO no acredita una clase RC.
- El delta corresponde a herrajes netos por hoja, incluida merma/margen vigente.
  La división añade otra hoja y montante: su precio total se confirma cotizando.
  No se presenta el delta parcial como precio final de la posición.
- Sin coordenadas, cara, herramienta, profundidad, cobertura o pieza inequívoca,
  el mecanizado queda declarado no emitido y bloquea completar esa estación. El
  proveedor configura la autoridad mediante la plantilla de Catálogo. P14 la
  conecta a las máquinas; no se adopta un mecanizado por defecto.

## D05 · carta por caras (2026-10-06)

- Vista interior por defecto. La exterior usa su muestra física y conserva el
  sentido de apertura respecto del observador. La cotización declara ambas
  caras; el PDF comercial dibuja interior. El cliente puede cambiar de cara en
  el portal sin modificar su revisión.
- La combinación guardada identifica stock/compra. Interior y exterior nunca
  se suman como dos artículos; la base de PVC y el acero tienen sus identidades
  declaradas. El dueño o encargado configura esta autoridad en Catálogo ›
  Ficha de serie o en la plantilla/importación, con fuente y diff.
- La primera combinación de la carta es la referencia del delta de precio.
  El catálogo permite cambiar su orden y regla por metro, porcentaje o fijo.
  El delta sigue el modo de precio predeterminado de la organización y su moneda,
  con el mismo cálculo que Precios: costo más margen, tarifa por m², matriz o
  lista comercial. Es indicativo sin descuento y con contexto predeterminado.
  El margen objetivo requiere calcular el proyecto completo y muestra Sin dato
  por posición; una tarifa o conversión ausente también explica Sin dato.
  La resta exacta pertenece al motor. No hay un recargo universal oculto.

- Sin textura del fabricante se usa la muestra lineal declarada, marcada como
  aproximada; no se inventa grano ni brillo emisivo. Los límites, refuerzo y
  días adicionales son datos revisables de catálogo. Un plazo no declarado
  permanece Sin dato. DEMO v5 nunca acredita una ficha productiva.

## D06 · accesorios y servicios (2026-10-06)

- DOC-01 muestra sublíneas con precio por defecto. El dueño puede elegir precio
  agrupado en Ajustes › Extras y servicios; la revisión conserva la política que
  se selló al emitir. Un cambio posterior no altera un documento anterior.
- No se agregan servicios ni accesorios silenciosamente cuando la organización
  no los declaró. Ajustes permite definir plantillas para nuevas posiciones,
  con regla, tarifa y fuente. La página del proyecto mantiene visible la revisión
  de instalación/flete/retiro y explica la ausencia de tarifas. Una plantilla
  incompatible bloquea su creación con causa, sin desaparecer en otra serie.
- Las sugerencias del motor requieren aceptación del estimador; descartar queda
  guardado y deshacer lo revierte. Los vuelos, lados y reglas por vano/hoja son
  datos configurables de catálogo; no se adopta una medida universal de obra.
- Las tarifas representan el accesorio o servicio completo. Su BOM se conserva
  para fabricar/comprar, pero no genera un segundo costo. La instalación explícita
  reemplaza el cargo histórico equivalente; dos reglas de instalación se rechazan.
- El neto aplicado gobierna la presentación. El reparto exacto incluye el ajuste
  de cuantización a moneda; cantidad × tarifa + ajuste = sublínea. La base y sus
  sublíneas suman el total de posición sellado, también con descuento o margen
  objetivo de proyecto. Las tarifas DEMO se muestran como sintéticas.
- «Por vano» (`WINDOW`) cuenta el marco completo, con sus divisiones internas.
  «Por hoja» (`LEAF`) cuenta cada hoja compatible a sus dimensiones; un
  ensamblaje contiene un marco por módulo. La definición del catálogo elige la
  regla: no se transforma un mosquitero completo en piezas por bahía sin fuente.
- El módulo de origen identifica las sugerencias de ensamblajes. El consumidor
  aplica o descarta la selección solo en ese árbol; la compatibilidad se entrega
  por módulo. El inspector actual consulta directamente su módulo seleccionado.
- Costos confidenciales según PRD-05: los endpoints de venta aplican una
  proyección por rol, conservando la autoridad interna completa. El estimador
  ve venta y restricciones autorizadas; no ve costos de servicios ni agregados
  que los revelen por resta. Los costos de cambios en lote quedan Sin dato con
  la causa de permiso y nunca se presentan como delta cero. IA2/IA3 continúan el
  diff de venta de esas propuestas sobre las operaciones tipadas.

## D07 · vano y montaje (2026-10-07)

- El tipo de muro empieza sin selección y es obligatorio para calcular. Se
  declara el muro observado; no se presume albañilería ni otro material.
- No existe una holgura ni tolerancia universal silenciosa. El dueño o encargado
  declara cada tipo, deducción por lado, accesorio y fuente en Ajustes › Vano y
  montaje para la serie. Los ceros del formulario son una declaración explícita
  de que ese lado no aplica la deducción; las reglas no se guardan sin fuente.
- Una o tres medidas por eje, con mínimo y dispersión exactos. Escuadra,
  desplome y fijación se pliegan en Avanzado; la fijación exige motivo. La
  confirmación reconoce los avisos según la tolerancia configurada.
- Cada cambio de regla crea autoridad nueva. Las medidas guardadas conservan
  la anterior; usar la vigente es una decisión explícita. Deshacer crea otra
  autoridad y no reescribe el historial. Los lados de los extras son los
  compatibles con el catálogo D06 de esa serie.
- El Δ de rectificación es venta neta del proyecto completo, con la misma
  política comercial que Precios. Una revisión aprobada abre una sucesora;
  emitir con medidas pendientes permite la propuesta comercial, pero no OT.
- Todas las nuevas emisiones requieren confirmación de medidas antes de
  producción. La ausencia de esa marca en un snapshot histórico conserva su
  contrato anterior. El instalador móvil se conecta en P23 al contrato de
  rectificación, sin permiso genérico de edición del proyecto.

## IA2 · operaciones y aclaraciones (2026-10-07)

- Una propuesta usa el registro único del motor y siempre se simula antes de
  aplicar. La aplicación de proyecto exige dueño o estimador; reabrir el
  trabajo consulta su estado durable sin repetir la operación. Una propuesta
  obsoleta vuelve a simularse y conserva su clave de idempotencia.
- Los topes iniciales son 20 pasos, 6 consultas, 6 rondas y 180 segundos,
  configurables mediante `AI_AGENT_*` del backend/worker, con límites explícitos
  documentados en `docs/ai/OPERACIONES.md`. IA3 continúa los ajustes del proveedor.
- Los chips ofrecen únicamente alternativas respaldadas por el catálogo.
  La altura de antepecho se pregunta como dato de obra; no se generan opciones
  numéricas sin una fuente. Elegir el SKU que ya existe no fabrica un cambio.
- La venta de la simulación es indicativa con las reglas comerciales vigentes.
  El precio aplicado sigue siendo autoridad para emisión. Sin esa autoridad,
  el borrador de descuento conserva la intención y `base_price: null`; no
  produce una cifra comercial ni ejecuta aprobación.

## IA3 · proveedor, presupuesto y fuentes (2026-10-07)

- Las diez capacidades parten en MiMo Pro. El dueño con MFA puede cambiar las
  cuatro rutas de diseño, agente, contexto y catálogo en Ajustes, incluyendo
  modelo, tiempo (60 s), hasta dos reintentos y modo automático de herramientas.
  Un override guardado prevalece sobre el modelo inicial del entorno.
- Sin tarifa declarada, costo «Sin dato». Las dos tarifas en USD por millón de
  tokens vienen del contrato del proveedor y quedan selladas por intercambio.
  La cifra usa Decimal en el motor; no se adoptan precios públicos aproximados.
- Presupuesto inicialmente sin límite mensual adicional, sujeto a la billetera.
  El dueño puede declarar un tope entero de créditos de solicitudes; cero
  bloquea llamadas. Mes de America/Santiago. Las reservas concurrentes cuentan
  antes de pagar al proveedor y el dueño recibe un aviso al exceder el tope.
- El registro físico y el débito se muestran separados: una respuesta pagada
  puede existir aunque su propuesta revierta. Reutilizar esa misma clave no
  dispara otro pago. Los intentos fallidos y herramientas ejecutadas conservan
  historial inmutable; cada miembro solo consulta sus llamadas.
- El PDF escaneado usa render a imagen cuando no tiene texto literal; conserva
  el límite de veinte páginas y la revisión de D01. El modo de prueba necesita
  flag y ruta explícitos y siempre se rotula. DEBUG no lo activa.
- En un PDF mixto, las páginas literales llegan como texto y las escaneadas
  como imagen, en orden y con referencia de página. El texto tiene un límite
  total de 100 000 caracteres; excederlo exige reducir el archivo, sin truncarlo.
- Presupuesto y tarifas no invalidan una conexión probada. Solo cambiar
  proveedor, modelo, tiempo, reintentos o modo de herramientas exige otra prueba
  de esa capacidad; las demás conservan su evidencia. Una nueva tarifa solo
  afecta intercambios futuros y no reescribe costos sellados.

## P02 · códigos como direcciones (2026-10-07)

- OC, RT y REC usan seis dígitos como mínimo y contador por organización y tipo.
  Son contratos de identidad, no preferencias de marca editables. Los proyectos
  conservan su secuencia global. Un rollback no consume código; una entidad
  eliminada conserva el alias para impedir reutilización.
- El alias histórico se guarda aparte. No se vuelve a firmar una compra ni se
  altera su código fuente para mejorar la lectura. Una OC nueva reserva código
  antes de sellarse. Los documentos anteriores conservan sus bytes y los slots
  de artefacto ya emitidos; la proyección nueva verifica primero la huella.
- La etiqueta física conserva posición, unidad y miembro del snapshot; el sufijo
  visible de refuerzo es `-R`, dictable por radio y común a todos los formatos.
  El escáner sigue aceptando `·R` y QR históricos. Una dirección nueva incluye
  OT e identidad estable; el código solo no sustituye la autorización.
- La interfaz y el papel usan la tabla de `ENGINEERING.md`. Los archivos CNC
  mantienen punto decimal y datos exactos, pues los consume una máquina.
  Se agrega la etiqueta al final del CSV de láminas para conservar las columnas.
  Sin autoridad de ángulo o código, se declara Sin dato; no se inventa 90° ni
  se sustituye una pieza desconocida por un hash recortado.
- Escanear un código sin OT se admite hasta 100 candidatos de taller. Por encima
  se exige la dirección QR con OT, sin resultados parciales ni cargar snapshots.
  Es un límite de búsqueda, no una pérdida del historial. Las etiquetas de bulto
  conservan su historia; las de corte exigen un plan vigente y muestran su causa
  y la acción de optimizar cuando no lo hay.

## P04 · lienzo y venta indicativa (2026-10-08)

- El precio de franja es neto indicativo sin descuento, con fuente y enlace
  a las reglas comerciales configurables existentes. Cantidad/multiplicación
  y redondeo pertenecen al motor. No se crea autoridad comercial aplicada.
  Una consulta sin operaciones solo evalúa y conserva diseño/fila persistida.
- El precio se sustituye por estado explícito durante cálculo; sin autoridad
  muestra «Sin dato» con causa. Las cifras viejas no autorizan guardar.
- Biblioteca ofrece únicamente recetas compatibles con serie, apertura,
  perfiles y acopladores del catálogo. Geometría/glifos siguen en P05.
- Desde 1024 se edita; debajo se lee, con navegación, cotas/precio y Centrar.
  Es el contrato de interacción de P04, no una preferencia comercial.
  La densidad contextual conserva los controles de taller existentes.
- Tres paños se propone con registro tipado: fantasma/Δ antes del clic,
  deshacer después. Cambiar diseño o cantidad invalida una respuesta tardía.

## P05 · gramática y vista declarada (2026-10-08)

- Vista interior al abrir; el selector interior/exterior cambia la lectura
  sin mutar el diseño. Es un control de cada dibujo, disponible también en
  el portal; no crea una preferencia de fabricación ni altera lo emitido.
- Carril 0 representa el exterior, índices crecientes hacia interior. Es una
  convención de dibujo explícita hasta contar con sección/orden del fabricante;
  no se convierte en autoridad de corte. La planta numera desde 1.
- Una dirección histórica ausente conserva sus bytes y la convención anterior
  como «Dirección inferida». El inspector y las recetas nuevas declaran el
  viaje, validado por el motor; una móvil no puede viajar hacia su jamba.
- Cotas técnicas en mm enteros, HALF_UP solo en presentación. La altura total
  del arco viene de sus extremos exactos; «Alto hasta arranque» sigue editable.
  Las cadenas cortas y módulos apilados reservan niveles propios fuera del
  conjunto. No se modifica una medida manufacturada para hacer legible su cota.
- Sin acoplador autorizado, los ejemplos DEV de conjuntos son solo gramática
  DEMO del motor. No se agrega un SKU ni se habilita fabricación para capturarlos.

## P09 · documento y condiciones (2026-10-08)

- Carta y Verde técnico siguen como valores iniciales. Ajustes › General ›
  Documentos permite A4, Oficio, Verde técnico oscuro y Grafito, pie legal y
  condiciones. El formato se sella por revisión; no reescribe documentos.
- Para una preparación nueva, los hitos iniciales son 50 % al aprobar y 50 %
  contra entrega. Se pueden editar o quitar; solo se guardan si suman 100 %.
  Un texto histórico no adquiere ese calendario por migración ni por parsing.
  El motor asigna el resto monetario al último hito para conservar el total.
- Plazo, instalación, exclusiones, garantía y jurisdicción vacíos se omiten
  del PDF. No se imprime una plantilla incompleta ni se inventa un plazo.
- La densidad usa fichas completas hasta tres posiciones, compactas hasta 24
  y densas por encima. Son reglas de presentación: conservan cada campo,
  precio y cota del motor, sin eliminar posiciones. Los nombres admiten 120
  caracteres. Las tablas de resumen repiten encabezados cuando continúan.
- Alternativas: hasta tres revisiones previas del mismo proyecto, selladas y
  sin recursión. Se presentan fuera del total y se eligen al preparar emisión.
- El QR impreso tiene su enlace de revisión separado del compartido y la
  vigencia de acceso de 30 días del portal existente. La vigencia comercial
  sigue declarada en la cotización. Revocar no cambia los bytes del PDF.

## P12 · puesto y control de calidad (2026-10-09)

- El operario elige explícitamente su estación. La preferencia se guarda por
  usuario y organización; cambiar de tenant no adopta el puesto anterior.
  Los puestos disponibles provienen de los centros activos configurados en
  Ajustes. Escanear una pieza conserva el puesto, sin asignar permisos.
- Taller abre oscuro cuando no hay tema elegido. El tema claro/oscuro sigue
  configurable con el control de apariencia existente y su preferencia local.
- Registrar una medición fuera de especificación conserva la OT abierta,
  salvo que la persona marque «Bloquear la OT y avisar al jefe». El control
  final y el rechazo con remake corresponden al jefe o dueño, con motivo y
  confirmación. Cada decisión tiene una clave idempotente por operación.
- El remake conserva el conjunto sellado y la pieza rechazada como motivo;
  requiere su propio plan. No se recorta automáticamente el BOM de una OT
  por una medición de una pieza: sería una nueva decisión de dominio.
- Sin agenda o capacidad declarada se muestra «Sin dato» o se omite capacidad.
  Los filtros de obra, compromiso y bloqueo son controles de lectura, sin
  convertir fechas ni cantidades estimadas en autoridad de fabricación.

## P17 · presencia y decisiones del asistente (2026-10-09)

- El asistente sigue el trabajo de la persona en el contexto exacto, incluyendo
  posición/proyecto/OT; la selección del lienzo es transitoria y no inicia otro
  hilo. «Nuevo» es una decisión explícita. El nombre de marca sigue configurable
  en Ajustes y no cambia el contrato del Orb ni sus estados.
- Bienvenida opcional solo en el estado vacío. Reduced motion elimina la
  animación. El Orb es plano: prevalece la constitución sobre degradados y
  duraciones decorativas de los adjuntos históricos.
- Propuesta y aplicación son estados distintos. Aplicar y Deshacer requieren
  clic y conservan las operaciones/auditoría. Si hubo una edición posterior,
  la IA no la elimina: se revisa el historial del editor.
- El precio del artefacto es indicativo y procede del motor y las reglas de
  Ajustes; no reemplaza calcular/aplicar precios antes de emitir. Sin autoridad
  térmica completa, Uw y su diferencia siguen Sin dato con causa y acción.
- MOCK exige habilitación explícita en desarrollo y se muestra como «Proveedor
  de prueba» solo en DEV. La aceptación conserva MiMo en la organización
  principal y separa el tenant sintético. No se activa fallback silencioso.

## ED1 · reglas editoriales comunes (2026-10-09)

- La densidad sigue la tarea: Producción y su shell usan `workshop` para
  jefe/dueño/operario. No cambia permisos. La apariencia claro/oscuro sigue
  configurable con el control existente, conservando la preferencia elegida.
- La sección distingue forma aproximada y profundidad declarada. El dibujo
  puede conservar proporciones esquemáticas; la medida sin catálogo dice
  «Sin dato · declara la sección en Catálogo». No se crea autoridad por un
  fallback de presentación ni se redondea una profundidad fraccional.
- El plan mantiene proporciones longitudinales y altura de barra esquemática.
  Textos tienen tamaño físico constante y tinta legible sobre el material.
  Si una pieza queda bajo 44 px, su leyenda HTML conserva la selección completa.
  No se ensancha una pieza para alterar su lectura como longitud fabricada.
- Materiales y fechas comparten glosario/formateadores. Un ángulo ausente
  sigue Sin dato; los rótulos nunca completan 90° por presentación.
- `StatusBadge` centraliza el tono; naranja significa decisión humana.
  No aparecen nuevos defaults comerciales configurables en este pase.

## P06 · conjuntos y fuentes (2026-10-09)

- La elevación inicia desarrollada; el selector permite proyectada sin mutar
  el producto. La planta se puede ocultar o ajustar entre 144 y 320 px.
  Estos controles de dibujo son preferencias de la vista, no fabricación.
- Las recetas nuevas declaran apertura interior. Bow lleva bisagras hacia
  los extremos; puerta con lateral inicia con bisagras izquierdas, visibles
  y editables desde Apertura. La compatibilidad proviene del catálogo.
- El aporte desarrollado se declara como separación de frentes sobre su
  bisectriz; apilado aumenta la altura. Un pivote compartido puede declarar
  cero. Catálogo permite editar límites, aporte y fuente antes de bloquear
  el sistema usado. No se completa autoridad a partir del nombre del SKU.
- «Acoples y ajustes» es la diferencia exacta del precio unitario del conjunto
  contra cotizaciones independientes de sus módulos. No implica reparto de
  costos internos ni un precio independiente del acoplador.
- El arrastre ajusta a 0°, 10°, 15°, 22,5°, 30°, 45° y 90°, o admite el ángulo
  numérico declarado entre −90° y 90°. El catálogo decide su viabilidad.

## P13 · corte y etiquetas (2026-10-10)

- Las etiquetas usan Carta con grilla de 100 × 50 mm; Ajustes › General ›
  Documentos permite A4 o rollo térmico de 100 × 50 mm. La elección define
  el papel; conserva medidas, identidad, huella y secuencia del motor.
- Los retazos recuperables se dirigen inicialmente a «Recepción de retazos».
  Es una ubicación declarada de recepción, editable en los mismos Ajustes;
  queda fijada al optimizar y no se reescribe al cambiar la preferencia.
  Se reserva el código RT en la transacción del plan y se da de alta la
  pieza física solo al completar Corte. Reservar una etiqueta no crea stock.
- La lectura inicia en secuencia de barras. El cortador puede imprimir el
  pack y las etiquetas por cortes idénticos para una sierra manual. La
  agrupación compara suministro, color, función, largo, ángulos y flecha
  exactos; mantiene cada dirección física y su posición original.
- No se propone tamaño de lámina ni despunte silencioso. Catálogo › Vidrios
  y paneles › Formatos permite declarar ambos desde la ficha del proveedor,
  con fuente y permisos de dueño/jefe de taller. La variante es inmutable;
  una nueva declaración se aplica al volver a optimizar. No es un ingreso
  de stock ni un cambio de las medidas ya selladas de la pieza.

## P15 · compras e inventario (2026-10-10)

- Revisar retazos disponibles a los **90 días**, configurable en Ajustes ›
  General › Documentos. La alerta invita a una revisión física; no desecha
  material ni declara su condición por antigüedad.
- La propuesta descuenta reservas, stock útil, tránsito y retazos del motor;
  una OC preparada tiene columna propia. Se compran solo las líneas visibles
  en la página revisada, con detalle antes de confirmar. Las listas tienen
  páginas de 50 y filtros por material/proveedor/proyecto/OT.
- El precio unitario es autoridad declarada del proveedor, opcional. Ausencia
  significa Sin dato. No se imputa un precio de venta ni una tarifa DEMO.
- Una compra parcial no modifica el requisito sellado. Cuando las OT separadas
  requieren más barras que su consolidación original, se muestra el faltante
  adicional y se exige revisar planificación/revisión; no se inventa capacidad.
- Mover o desechar retazos requiere motivo, confirmación y actor. El catálogo
  fija identidad/color/sustrato y límites de medida del suministro. La ubicación
  inicial conserva la preferencia P13; la recepción y el traslado declaran rack.

## P11 · cobranza y documentos internos (2026-10-10)

- Vigencia de enlaces de pago: **7 días**, configurable entre 1 y 90 en
  Ajustes › General › Cobranza e integraciones. Se fija al crear cada enlace;
  modificar la preferencia no cambia su autoridad histórica.
- Simuladores explícitos habilitados por defecto en esa sección. No contactan
  proveedores ni acreditan dinero; sus pagos/folios permanecen etiquetados.
  SII activo y certificación declarada parten desactivados.
- Anticipo al aprobar y saldo contra **entrega completa con comprobante**, o
  la fecha explícita del acuerdo sellado si se declaró. La agenda estimada y
  una entrega parcial no hacen vencer el saldo. Se configuran los eventos/fechas
  en las condiciones de emisión; una revisión ya emitida conserva su calendario.
- Fecha manual del cobro obligatoria, sin futuro, en America/Santiago. El
  calendario reparte pagos vigentes en el orden del acuerdo y excluye anulados.
- Una factura o boleta interna por revisión, conservada en reintentos. Corregir
  su tipo requiere NC y nueva revisión; el original no se sobrescribe.
- Recordatorio IA preparado para el dueño, sin cifras propuestas por el modelo.
  Enviar exige clic y confirmación, revalidación del saldo y outbox cifrada.
  Un saldo que incluye pagos simulados no se comunica como cobranza real.

## P14 · autoridad de mecanizado (2026-10-10)

- No se precargan capacidad, ejes, mordazas, profundidad ni montajes de máquina.
  Los declara el dueño o jefe de taller desde Mecanizado › Máquinas y
  herramientas. La ausencia bloquea; no es una preferencia numérica.
- La única salida implementada es intercambio neutro revisado. Elegirlo no
  acredita un controlador propietario ni envía archivos a la máquina.
- Una sección nueva se sella con la revisión. Un histórico sin sección exige
  nueva revisión; un montaje vincula esa sección, orientación y fuente.
- Restaurar prepara los datos anteriores para comparación y confirmación.
  No elimina la declaración posterior ni los archivos de programas emitidos.

## P16 · fuente y revisión de catálogo (2026-10-10)

- LOW y REVIEW_REQUIRED comienzan desmarcados. UNKNOWN no recibe un valor
  silencioso; una corrección conserva el candidato y literal originales.
- «Revisado por técnico» exige revisión humana vigente. «Verificado con
  evidencia» exige soporte vigente para cada autoridad técnica presente;
  una corrección humana no se atribuye al fabricante. DEMO prevalece siempre.
- El catálogo declara cobertura de la serie; emisión comprueba y sella los
  artículos consumidos. Liberar usa esa decisión histórica. No se usa la
  cobertura de un artículo ajeno para reescribir una cotización emitida.
- El archivo original puede contener costos: acceso de dueño/jefe de taller,
  con RLS y sin caché pública. Los otros roles consultan únicamente las
  proyecciones técnicas que su permiso permite.
