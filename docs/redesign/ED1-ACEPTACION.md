# ED1 · coherencia editorial de la ola 1

Base `81ee66d7`, rama `codex/ED1-pase-editorial-ola1`. Verificación del
09-10-2026. La revisión reúne shell/Hoy/paleta, editor/DIN/selectores,
precios, DOC-01, taller, asistente/Orb y marca/ingreso. La
[comparación por persona](captures/ed1/index.html) conserva las capturas
anteriores y posteriores lado a lado.

## Qué cambió y por qué

La primera ronda mejora los cinco puntos más débiles encontrados:

1. Producción usa densidad de taller también en el shell del jefe. Controles
   y enlaces llegan a 44 px; la densidad refleja la tarea y conserva el rol.
2. La sección del perfil conserva el polígono y los ejes del catálogo, y lleva
   nombres y medidas a una leyenda HTML legible. «Vidrio» y «Alma» reemplazan
   los enums reducidos por la escala del SVG.
3. Los inspectores de módulo y paño usan una paleta heredada común con el
   renderer DIN. Se conserva compatibilidad y bloqueo de puerta por contexto;
   las etiquetas usan la retícula de la paleta física y dejan de cortarse.
4. Importaciones y enlaces de pago reutilizan los formateadores canónicos de
   fecha. La selección de apertura comparte nombres y mantiene Fijo como
   inicio del contrato heredado.
5. Veintiocho insignias en catorce fuentes usan `StatusBadge`, con un único
   tono por estado. Se eliminan noventa declaraciones CSS duplicadas. Naranja
   representa una decisión humana; un trabajo terminado usa su estado real.

La segunda ronda mejora otros tres puntos:

1. El corte horizontal separa rótulos de la escala del dibujo y conserva la
   precisión de la profundidad declarada. Sin sección, las proporciones
   aproximadas permanecen como dibujo y la profundidad dice Sin dato.
2. El plan de corte usa Plex Mono y tamaños de token; los rótulos cancelan
   la escala del SVG y usan grafito sobre el material claro en ambos temas.
   La altura de barra es esquemática y las longitudes siguen proporcionales.
   Las piezas con objetivo menor de 44 px se seleccionan desde la leyenda
   HTML completa. Material/acabado usan el glosario y un ángulo ausente
   conserva «Sin dato», sin completar 90°. Preparación/QC bajan a peso 600.
   La superficie de firma usa papel; radios de formularios y comparaciones
   quedan en 4 px.
3. El progreso usa 160 ms y un eje. Dock y menús usan capas/elevación por
   tokens. Se elimina un selector del dock sin consumidores y once alias de
   tokens muertos. El inicio conserva prioridad de su imagen sin advertencia
   de React 18.

No se añaden funcionalidades de dominio. Unificar la primitiva alcanza
también insignias de Clientes, Ajustes y Cobranza; esta adopción no constituye
la aceptación de sus flujos posteriores.

## Recorridos con autoridad real

| Persona/capacidad | Resultado y evidencia |
| --- | --- |
| Estimador: Hoy → buscar proyecto → editor/vistas DIN/sección → precio → preparación → emitir → DOC-01 | PASA. Tres posiciones, cascada del motor cerrada, neto $68.211 y total $81.171. Clic y worker generan cuatro páginas Carta con Plex embebida, sin costos internos. [Recorrido](captures/ed1/recorridos/estimador.json), [PDF verificado](captures/ed1/recorridos/doc01.json), [primera página](captures/ed1/recorridos/doc01-carta.png). |
| Dueño: Hoy → Precios → solicitud bajo la banda → aprobar → Asistente | PASA. Backend rechaza aplicar como estimador; el dueño revisa y aprueba por UI. [Personas](captures/ed1/recorridos/personas.json). |
| Jefe: Hoy → tablero → QC bloqueado con motivo → remake → plan de corte | PASA. Conserva la pieza rechazada y obtiene doce cortes del motor en el plan del remake. [Personas](captures/ed1/recorridos/personas.json). |
| Operario, 390 oscuro: estación Corte → QR → pieza → iniciar → bloquear → supervisor desbloquea | PASA. Código físico real, puesto privado y causa persistente. [Personas](captures/ed1/recorridos/personas.json). |
| Editor/Orb: propuesta de dos oscilobatientes → dibujos y Δ → aplicar → deshacer → auditoría | PASA. Proveedor de prueba explícito en tenant aislado; MiMo real conserva su propuesta en la organización principal. [IA](captures/ed1/recorridos/ia/verificacion.json). |
| Proyecto/MiMo real: segundo piso a Low-E → dos posiciones/dibujos/Δ → aplicar → recargar → deshacer | PASA. Nueva consulta real, filtro exacto, cocina intacta y diseños/cantidades restaurados. El Uw sigue Sin dato con causa. [Lote](captures/ed1/recorridos/ia/verificacion-lote.json). |
| Vacío, carga, error, sin acceso y movimiento reducido | PASA. Ocho respuestas de transporte controladas, tres Orbs sin animaciones ni IDs repetidos. El bloqueo de revisión y el de taller se recorren con estado real. [Estados](captures/ed1/estados/verificacion.json). |
| Secciones técnicas, 1440/1280/1024 y ambos temas | PASA. Doce vistas y detectores sin hallazgos. La profundidad fraccional y ausencia de autoridad tienen regresiones. [Técnica](captures/ed1/tecnica/verificacion.json). |
| Plan de corte, 1440/1280/1024/390 y ambos temas | PASA. Ocho vistas sin hallazgos ni desbordes; la selección abre el origen y resalta la pieza exacta. El texto conserva su tamaño físico y toda pieza ofrece un objetivo HTML de taller. [Plan](captures/ed1/plan/verificacion.json). |

Los datos son DEMO y se presentan como sintéticos. Los precios y dibujos
proceden del motor y sus snapshots; un ensayo de proveedor no acredita un
fabricante ni autorización de producción. Los PDF completos y capacidades
privadas del recorrido permanecen fuera de Git.

## Matriz y guardas

La matriz oficial recorre diez rutas, 192 vistas por fase: 1440×900,
1280×800, 1024×768 y 390×844, claro y oscuro, con roles autorizados.
El estado anterior contiene ocho hallazgos de fuente y 954 de objetivo
táctil, más ocho advertencias de consola en inicio. Después: cero hallazgos,
cero desbordes, cero errores HTTP y cero errores de consola. No se modifica
ningún detector ni su umbral. Algunos inputs plegados contribuyen al conteo
anterior; se corrigen sus tamaños mediante la densidad compartida.

La baseline baja de **257 claves / 716 ocurrencias** a **69 / 187**.
Las infracciones presentes al iniciar eran **155 / 466**: se eliminan
279 ocurrencias reales y 529 permisos antiguos. No se incorpora ninguna
tolerancia. Las restantes incluyen geometría de presentación, detalles
técnicos y superficies de encargos posteriores.

[Comparación y compresión sin pérdida](captures/ed1/comparacion.json).
Cada PNG optimizado conserva sus píxeles; los originales no se sustituyen
por maquetas.

## Rúbrica por superficie

S = shell/Hoy/paleta; E = editor/DIN; D = selectores de dominio;
P = precios; Q = DOC-01/preparación; T = producción/estación;
A = asistente/Orb/trabajos; M = marca/ingreso/estados.
PASA indica el alcance editorial de la ola 1, con la evidencia anterior;
no certifica las funcionalidades de olas posteriores.

| Revisión | S | E | D | P | Q | T | A | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 · Formatos y Mono tabular | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R2 · Radios e inglete | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R3 · Jerarquía por delineado | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R4 · Naranja requiere persona | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R5 · Teal en el cromo | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R6 · Voz y vocabulario | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R7 · Densidad por tarea | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R8 · Estados y causas | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R9 · Papel sobre mesa | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R10 · Selección delineada | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R11 · DIN e iconografía | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R12 · Foco y teclado | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R13 · Movimiento acotado | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R14 · Acción principal | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R15 · Fuente y Sin dato | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R16 · Sin slop visual | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R17 · Anchos y legibilidad | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R18 · Acciones y código vivo | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R19 · Firmas conservadas | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |
| R20 · Motor y capacidad real | PASA | PASA | PASA | PASA | PASA | PASA | PASA | PASA |

Las firmas se conservan: marca de sección, hoja con inglete, DIN/vista,
procedencia del número, sello de revisión, una pieza por estación y Orb ligado
a trabajo real. Las capacidades del §8 se prueban mediante la simulación del
editor y lote Low-E, cascada/margen, checklist/emisión y plan de corte/QR.
Shell y marca conducen a esos flujos; no presentan una capacidad ornamental.

## Gates y límites

`make lint typecheck test build`: PASA en la copia nativa aislada del checkout
final. Motor: 829 pruebas y dos xfail previstos; backend: 1.382; frontend:
919 en 83 archivos. Golden byte check y assets de marca pasan. No se reduce
ningún timeout, assertion, detector ni check. Los cuatro checks de CI se
comprueban sobre el HEAD publicado antes del squash y se registran al integrar.
No se modifica motor, backend, API, permisos, migraciones ni contrato de
dominio. Database Gate conserva su ejecución requerida en CI. La prueba de
navegación precarga el módulo real de proyectos durante el setup para separar
transformación de fuentes de la interacción; conserva timeout y assertions.

No se conecta hosting, Flow, SII ni correo productivo en este pase editorial.
MiMo permanece conectado; MOCK está limitado al tenant de ensayo. La
activación productiva continúa en [ACTIVACION](../operations/ACTIVACION.md).
Catálogos DEMO no son certificados y la autoridad térmica incompleta sigue
visible. Clientes, compras, inventario, instalación y CNC esperan su encargo
y ED2; aquí solo comparten la primitiva cuando corresponde.
