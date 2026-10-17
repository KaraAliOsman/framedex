# Experiencia objetivo: trabajar sobre la ventana

[Volver al plan](README.md)

## Promesa de producto

«Puedo diseñar una ventana, verla bien, entender su precio y preparar lo que
necesito para venderla y construirla, sin pelear con el programa».

La aplicación asume las decisiones repetibles y muestra al profesional las
decisiones que cambian su solución. La profundidad se conserva cerca del objeto
correspondiente. No se transforma toda tarea en un asistente de veinte pasos.

## Organización por trabajo y persona

El menú depende del trabajo frecuente, además del permiso. Un permiso de lectura
no obliga a promocionar un módulo al primer nivel. La autorización sigue en
backend y RLS.

| Persona | Entrada y navegación habitual | Acceso contextual/secundario |
|---|---|---|
| Dueño de empresa pequeña | Hoy, Obras, Taller, Compras y Empresa | Analítica desde negocio; catálogos/precios en Empresa; stock dentro de operación. |
| Cotizador | Obras, Clientes y seguimiento de propuestas | Editor directo; precios autorizados; catálogo consultable dentro de selección. |
| Encargado de taller | Plan de trabajo, Materiales y Salidas | Orden, corte, recepción, stock y catálogo técnico según tarea. |
| Operario | Mi puesto y Escanear | Orden/pieza actual, instrucciones, incidencias y calidad. |
| Instalador | Mi agenda y Escanear | Obra, mediciones, evidencias, recepción y postventa. |

Se propone **Obras** como nombre humano del espacio principal y se mantiene
«Proyecto» en contratos técnicos. En empresas donde «proyecto» sea más natural,
se puede conservar ese término; la prioridad es usar uno de forma consistente.
No construir una preferencia configurable de nombres para resolver esto.

El asistente es una presencia contextual, no tres destinos principales
«Asistente/Trabajos/IA». Los trabajos largos viven en una bandeja única con
estado resumido, resultado y reanudar. El espacio amplio de IA se abre cuando
el trabajo lo necesita.

## La primera sesión

1. Entrar y crear una obra de prueba o empezar un borrador.
2. Elegir un sistema disponible y una ventana reconocible. Si aún no existe
   catálogo real, ofrecer modo de aprendizaje con alcance explícito o importar
   catálogo. No simular capacidad de fabricación.
3. Cambiar medidas y apertura sobre el dibujo.
4. Ver el precio si hay datos; si no, entender exactamente qué falta.
5. Guardar automáticamente el borrador y continuar con cliente/propuesta cuando
   la persona quiera vender.

Nombre legal, RUT, logo, impuestos, remitente, pagos, máquinas y proveedor de IA
se configuran cuando sirven. El alta de una empresa no puede ser un examen de
todos los módulos. Los campos que condicionen una acción legal o monetaria se
piden antes de esa acción.

## Recorridos principales

### Cotizar cinco ventanas de una casa

Nueva obra → seleccionar sistema y defaults de vidrio/acabado → añadir primera
ventana → introducir ancho/alto → elegir apertura → duplicar o añadir otras →
ver resumen/precio → completar cliente y condiciones → vista previa → emitir.

El usuario puede comenzar con un croquis o un archivo, pero debe poder llegar al
mismo resultado manualmente. La IA no es una dependencia para usar el editor.

La obra recuerda lo común. Duplicar conserva la configuración; cambiar un default
permite elegir «solo nuevas ventanas» o «también las existentes compatibles».
Las excepciones aparecen como «Vidrio distinto al de la obra», con restauración
clara. No sustituir automáticamente una opción incompatible por otra más cara.

### Modificar una propuesta

Abrir obra → elegir ventanas o todas → cambiar vidrio/acabado/medida → ver
diferencia de precio y compatibilidad → aplicar → preparar revisión nueva.

La revisión emitida permanece accesible. Comparación con miniaturas y diferencias
humanas: «4 ventanas cambian a Nogal exterior», no un árbol JSON. Preparar una
revisión no envía un correo por sí solo.

### Crear una composición especial

Partir de una ventana → dividir o acoplar → seleccionar paño/módulo → decidir
apertura → editar cotas → revisar planta si cambia la orientación del conjunto.

Arco, ángulo, bow/bay, corredera y plegable no son variaciones decorativas de un
rectángulo. El sistema elegido determina qué operaciones son posibles. Al no
serlo, se explica la alternativa: otro sistema compatible o mantener el diseño.

### De venta a fábrica

Revisión aceptada → verificar mediciones necesarias y materiales → preparar
orden/lote → revisión breve de pendientes reales → liberar con clic humano →
cola de estación → registro de producción → calidad → embalaje/salida.

No pedir otra vez dimensiones, color, composición de vidrio o lista de piezas.
Cambios después de emitir o liberar crean el sucesor correspondiente.

### Importar catálogo

Arrastrar PDF → reconocer fabricante/sistemas → preparar biblioteca y relaciones
en segundo plano → revisar resumen y dudas concretas → activar capacidades
respaldadas. El [documento de IA/catálogos](05-ia-catalogos.md) desarrolla el flujo.

## La obra como espacio de trabajo

```text
Obras / Casa Los Aromos                 Borrador · Guardado
Cliente pendiente                      [Preparar propuesta]

Ventanas      Propuesta      Seguimiento             Más…

[Añadir ventana] [Importar medidas]     Buscar · Recinto · Vista
Defaults: Sistema … · Vidrio … · Acabado …             Cambiar

P01  [miniatura] Cocina        medida · apertura       precio
P02  [miniatura] Dormitorio    medida · apertura       precio
P03  [miniatura] Estar         medida · apertura       precio

Selección: 3 ventanas  [Cambiar vidrio] [Acabado] [Duplicar] […]
Resumen de obra: ventanas · unidades · precio del motor
```

La vista de miniaturas ayuda a reconocer. La tabla compacta sirve a obras grandes;
conserva miniatura, código corto y recinto. Se puede alternar una sola vista
principal sin duplicar el resto de la pantalla. El filtro y la selección no se
pierden al volver del editor.

Fases y revisiones son información útil, pero no un segundo menú horizontal
permanente. Cobros, adjuntos, documentos emitidos e historial viven en Seguimiento
y enlaces contextuales. La ubicación exacta se ajusta con el uso; no añadir una
pestaña por endpoint.

## Editor principal

```text
‹ Casa Los Aromos / P01 · Cocina          Guardado    Precio    [Propuesta]

[Añadir/dividir] [Apertura] [Vidrio] [Acabado]     2D | 3D | Sección
┌───────────┬─────────────────────────────────┬────────────────────┐
│ Ventanas  │                                 │ Ventana / selección│
│ P01 [img] │       cota editable              │                    │
│ P02 [img] │       ┌───────────────┐         │ Sistema heredado   │
│ P03 [img] │       │               │         │ Medidas            │
│           │       │    producto   │         │ Apertura visual    │
│           │       │               │         │ Vidrio             │
│           │       └───────────────┘         │ Interior / exterior│
│           │                                 │                    │
│           │   Vista interior · zoom/ajustar  │ Detalles técnicos ›│
└───────────┴─────────────────────────────────┴────────────────────┘
             [Pedir un cambio…]       [Deshacer]   Materiales / precio
```

### Reglas de interacción

- Seleccionar un paño cambia las propiedades del paño; seleccionar marco o
  módulo cambia su contexto. La jerarquía aparece con nombres humanos.
- Clic en una cota abre un input local. Enter confirma; Escape restaura el
  borrador. No ocultar una entrada inválida ni alterar la geometría silenciosamente.
- Arrastrar un montante permite una vista previa; el resultado aplicado procede
  de la operación del dominio. Teclado y campo numérico ofrecen precisión.
- La herramienta de apertura usa una paleta visual compatible con ese sistema;
  se puede ver el movimiento, bisagra y manilla antes de elegir.
- Interior/exterior siempre se entiende. Cambiar de vista no cambia la apertura
  física ni confunde izquierda/derecha comercial con orientación del modelo.
- Dividir y acoplar son verbos con resultado reconocible. Mostrar la vista previa
  en el paño, no pedir entender nodos o ejes internos.
- Vidrio, acabado y cantidad permiten actuar sobre selección múltiple sin salir
  del editor. Deshacer conserva la selección y el encuadre cuando sea posible.
- La lista lateral de ventanas puede plegarse. En el área central se mantiene
  espacio suficiente para entender el producto; no imponer una cifra porcentual
  que deje sin lugar una tarea legítima.
- Un solo inspector con esenciales y detalles. No abrir simultáneamente cinco
  paneles que compitan por el lienzo.
- Guardado automático del borrador con estado corto y recuperación. Emisión,
  publicación de catálogo o liberación son acciones diferentes.
- Una edición pendiente/rechazada se identifica junto al objeto afectado. Mantener
  el último resultado válido sin presentarlo como si correspondiera al borrador.

## Qué se pregunta y cuándo

| Dato | Tratamiento objetivo | Momento | Precaución |
|---|---|---|---|
| Nombre de obra | Nombre inicial editable | Al empezar, sin bloquear dibujo | No crear clientes falsos para satisfacer el contrato actual. |
| Cliente | Elegir existente o nombre breve | Al preparar propuesta; antes de enviar, destinatario válido | Backend puede necesitar estado de borrador sin cliente. |
| RUT/datos fiscales | Opcionales hasta documento que los requiera | Acción fiscal/comercial correspondiente | Validar según país/tipo, sin exigirlo para diseñar. |
| Dirección | Heredar de cliente/obra cuando existe | Medición, entrega o instalación | Distinguir comercial de dirección de obra. |
| Serie/sistema | Heredar del proyecto/último compatible | Primera ventana o cambio deliberado | No derivar compatibilidad de apariencia. |
| Ancho/alto | Entrada principal visible sobre cota | Diseño | Declarar si es medida de fabricación o vano. |
| Apertura/mano | Elección visual | Diseño | Solo opciones físicamente admitidas. |
| Cantidad/recinto | Cantidad inicial 1; recinto opcional | Diseño/lista | Alcance visible por posición/unidad. |
| Vidrio | Receta compatible heredada | Diseño, cambiar si hace falta | No elegir por grosor suelto si se requiere composición. |
| Acabado | Heredar; caras visibles al editar | Diseño | Acabado y variante de compra no son solo un hex. |
| Junquillo/refuerzo/kit | Derivar de reglas y elegibilidad | Detalle técnico o excepción | La derivación requiere fuente válida. |
| Altura de manilla | Regla/preset compatible, editable autorizado | Apertura o detalle | Mostrar efecto; no preguntar en cada fijo. |
| Holguras/descuentos de corte | Motor/catálogo | Especialista y medición | Nunca calculados por la IA o un input decorativo. |
| Uw/clasificación | Resultado respaldado o pendiente | Exigencia del encargo/consulta técnica | No bloquear todo cambio por falta de ensayo. |
| Merma/barra/estrategia | Política industrial y stock existente | Plan de corte | No invadir cotización simple. |
| Precio/margen/descuento | Política heredada y decisiones autorizadas | Comercial | Mostrar precio final sin exponer costos privados. |
| Trazas/huellas/versiones | Acceso bajo demanda | Investigación, auditoría o emisión | Código corto en la UI; identidad completa disponible. |

Defaults significa preferencias o reglas autorizadas. Un dato industrial ausente
no se convierte en default porque simplifique la pantalla.

## Tema definitivo propuesto

**Dirección: herramienta clara de estudio/taller, con el producto como protagonista.**
La claridad ayuda a comparar vidrio, madera, aluminio, planos y PDF en una misma
mesa de trabajo. Es una elección de dirección, no la afirmación de que el claro
sea siempre superior para toda persona o entorno.

| Elemento | Punto de partida propuesto | Intención |
|---|---|---|
| Fondo de aplicación | `#F4F3EF` | Mesa neutra, suave y ligeramente cálida. |
| Superficie / hoja | `#FFFFFF` | Dibujo y documentos reconocibles. |
| Texto principal | `#202625` | Lectura firme sin negro absoluto. |
| Texto secundario | `#58625D` | Contexto legible. |
| Separación | `#D9DDD6` | Bordes selectivos, no una caja por frase. |
| Acento principal | `#24634F` | Acción y selección contenidas. |
| Avisos | Tonos semánticos con texto/ícono | Comunicar efecto y resolución. |
| Tipografía | Plex Sans disponible; tamaños principales 14–16 px | Jerarquía y lectura antes de cambiar de familia. |
| Números | Tabulares; Mono solo donde ayude | No convertir toda la interfaz en código. |
| Controles | ~36–40 px escritorio; ~44 px táctil | Densidad útil sin dificultad de pulsación. |
| Filas | Compactas legibles; mayor altura en tareas táctiles | La densidad sigue a la tarea. |
| Radios | Moderados, aprox. 6–10 px según componente | Agrupar sin aspecto de dashboard de tarjetas. |
| Profundidad | Líneas y sombra discreta en capas flotantes | Entender qué está sobre qué. |

Estos son valores iniciales de diseño para afinar en las láminas, no un nuevo
conjunto de prohibiciones arbitrarias. Contraste, foco, estados y legibilidad se
comprueban en la campaña final. El estándar AA incluye contraste mínimo 4,5:1
para texto normal y 3:1 para texto grande; los objetivos táctiles de producto
de ~44 px no se confunden con el mínimo AA de 24 px y sus excepciones de WCAG 2.2.

No mantener un segundo tema oculto o un «modo taller oscuro» como rediseño paralelo.
Al migrar, una preferencia antigua debe resolverse de forma coherente y sin dejar
rutas con mezclas de colores.

## Reconciliación con la constitución anterior

`docs/design/CONSTITUCION.md` contiene principios útiles y también decisiones
visuales/ceremoniales que ya no representan el pedido actual. Al comenzar la
implementación se debe actualizar esa autoridad antes de propagar componentes.

| Se conserva | Se sustituye o corrige |
|---|---|
| Dibujo como interfaz, autoridad numérica, español de oficio, progresivo y una acción principal | Dos temas, oscuro por densidad taller y proporciones de color obligatorias. |
| Apertura física, fuentes, identidad e inmutabilidad | Radios máximos rígidos y tipografía técnica pequeña aplicada por defecto. |
| Recuperación, claridad de estados y componentes compartidos | «No es simpático» como rechazo al placer de uso; el objetivo ahora incluye disfrute y fluidez. |
| Profundidad técnica a un clic cuando sirve | Repetir «¿De dónde sale?»/traza/huella en toda superficie como carga visual permanente. |

No se reescribe todavía la constitución: este es un plan pendiente de inicio.
La instrucción reciente del dueño gobierna la dirección; no necesita una segunda
aprobación de las decisiones antiguas para poder trabajar.

## Lenguaje que ayuda a actuar

| Texto observado o patrón técnico | Redacción de producto propuesta |
|---|---|
| Requisitos congelados | Materiales de la revisión B |
| Elegibilidad explícita | Qué se puede fabricar y qué falta |
| REVIEW_READY / trabajo en espera de aprobación | Catálogo preparado · 3 dudas para revisar |
| Ejecutar agente | Escribe lo que quieres cambiar |
| Publicar operaciones | Aplicar cambios |
| Falta autoridad | Falta la regla de corte del perfil… · Ver fuente |
| Sin dato repetido en todas las filas | Resumen de datos pendientes con filas afectadas |
| Elemento/objeto | Ventana, puerta, paño, marco, hoja o pieza, según el caso |

No reemplazar todos los términos técnicos por vaguedades: «junquillo», «refuerzo»
y «merma» son útiles para quien los necesita. Lo robótico es la falta de contexto,
no la existencia de vocabulario profesional.

## Respuesta, placer y movimiento

La parte divertida es ver el resultado, manipularlo con seguridad y sentir que
el programa acompaña. No requiere puntos, mascotas ni festejos por cada guardado.

- Selección y foco responden inmediatamente; no animar un retraso artificial.
- Paneles/menús pueden entrar en ~140–180 ms con opacidad/desplazamiento leve.
- Cambio interior/exterior puede mantener continuidad en 3D sin perder orientación.
- Apertura física se usa para explicar movimiento, con pausa y control del usuario.
- Operaciones frecuentes de tamaño no deben esperar una animación para continuar.
- Transiciones interrumpibles y preferencia de movimiento reducido.

`apple-design` informa continuidad y manipulación directa; `emil-design-eng`
informa precisión, jerarquía y eliminación de fricción. No se copia una superficie
de Apple ni se llenan las pantallas de translucidez y resortes.

## Dispositivos y condiciones reales

| Entorno | Experiencia |
|---|---|
| Escritorio normal | Editor completo, teclado, selección múltiple y propiedades en contexto. |
| Portátil de 13 pulgadas | Un panel secundario a la vez; lista plegable y cotas legibles sin zoom de navegador. |
| Tablet de taller | Mi estación, escáner, instrucciones visuales y grandes acciones. |
| Teléfono en obra | Agenda, medir, foto, nota y confirmar; no toda la cinta del editor de escritorio. |
| Portal del cliente | Dibujo, características, precio, condiciones y aceptación sin lenguaje industrial. |

El plan no acredita pruebas responsive hechas en esta auditoría. El flujo móvil
se valida en dispositivo real al final, incluidos teclado, luz exterior y red.

## Estados que forman parte del diseño

Vacío con acción apropiada al rol; primer uso con ejemplo útil; carga que no
borra el contexto; error con recuperación; datos pendientes con impacto claro;
desconexión con cambios locales identificados; conflicto de edición con diferencia
legible; falta de permiso sin callejón; éxito breve con siguiente paso; revisión
emitida con acceso al borrador sucesor. Ninguno se resuelve con un toast genérico
que desaparece y deja la persona sin saber qué ocurrió.
