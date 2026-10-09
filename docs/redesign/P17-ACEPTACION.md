# P17 · asistente, trabajos y Orb

Base `4d3f220451c7b06562e944b0465d8718314db3a8`, rama
`codex/P17-asistente-trabajos-orb`. Verificado el 09-10-2026.
Implementación `c25409c2befe60d1be047ac1e4f8d37a334b20f4`.
La [evidencia](captures/asistente-trabajos-orb/) conserva antes, después,
recorridos y estados. P17 permanece en curso hasta CI y squash.

La presencia se consulta por organización, persona y contexto exacto. Un trabajo
antiguo sigue visible aunque haya más de treinta trabajos posteriores en otras
pantallas. El lanzador, dock y artefactos comparten el estado real del trabajo;
la propuesta espera un clic humano y el texto distingue propuesta, aplicación
y deshacer. El dock mide 400 px y muestra la dirección humana del proyecto
o posición. Trabajos incorpora objeto, actor, duración, resultado y permiso de
reintento autorizado por backend. La conversación de IA conserva su reintento
privado; el endpoint genérico de trabajos no puede reabrirla.

## Recorridos y autoridad

| Recorrido | Resultado y evidencia |
| --- | --- |
| Editor, proveedor de prueba explícito: dividir en dos oscilobatientes → revisar → aplicar → deshacer → auditoría | PASA. Renderer real, $75.466 → $76.190 y Δ $724 del motor; auditoría `applied`, `undone`. [Registro](captures/asistente-trabajos-orb/recorrido/verificacion.json). |
| Editor 1024 oscuro, MiMo real: misma solicitud | PASA. Propuesta verificada de tres operaciones, dos elevaciones reales; no se cambia el proveedor del tenant principal. |
| Proyecto, MiMo real: segundo piso a termopanel Low-E → revisar dos posiciones → aplicar → deshacer | PASA. Living, cantidad dos: $249.585 → $320.064, Δ $70.479. Dormitorio: $124.793 → $160.032, Δ $35.239. Cocina del primer piso conserva su vidrio. Diseños y cantidades originales se restauran y la auditoría registra ambas decisiones. [Registro](captures/asistente-trabajos-orb/recorrido/verificacion-lote.json). |
| Aplicar en editor → editar ancho a 1 510 mm → intentar deshacer IA | PASA. Rechazo con causa, ancho preservado y ningún `undone` ficticio. [Guarda](captures/asistente-trabajos-orb/estados/verificacion-guarda.json). |
| Vacío, carga, error con reintento y sin permiso en Asistente y Trabajos | PASA: ocho casos con respuestas de transporte controladas, declaradas como ensayo. No se atribuyen a una caída real del proveedor. [Estados](captures/asistente-trabajos-orb/estados/verificacion.json). |
| Tres Orbs simultáneos y reduced motion en Chromium | PASA. IDs únicos, cero animaciones, filtros o degradados. Mapeo unitario incluye pensando, trabajando, esperando, éxito, cancelado y estado desconocido seguro. |
| Continuidad o auditoría tardía después de enviar un trabajo nuevo o pulsar Nuevo | PASA: regresiones de frontend. La respuesta antigua no vuelve a asociar la conversación abandonada; la decisión se envía a su auditoría original. |
| Contexto antiguo, otro usuario, otro tenant y referencias distintas | PASA en PostgreSQL. La presencia exacta supera la paginación y conserva privacidad; INSTALLER recibe 403 real. |

Las recetas y precios son DEMO, declarados como sintéticos. Las cantidades,
dibujos y precios proceden del motor y su catálogo. El modelo propone intentos
tipados; no genera un precio ni autoriza fabricación. El Uw y su diferencia
dicen **Sin dato**, con la causa y la acción a Catálogo: falta autoridad térmica
completa de marco, vidrio y borde. P18 continúa ese contrato.

La simulación explícita y la contextual normalizan las mismas referencias antes
de usar la cache. Esto evita gastar dos consultas en el mismo resultado al
construir el artefacto; el límite de consultas sigue intacto y los resultados
se copian para evitar mutaciones. El ensayo encontró esta duplicación después
de un timeout real. Los intentos fallidos permanecen en el historial.
La verificación del lote sigue el índice exacto de turno/paso; no adjudica a
una propuesta nueva los efectos de una anterior.

## Capturas y tamaños

La matriz oficial posterior contiene 48 vistas: OWNER, ESTIMATOR y
WORKSHOP_MANAGER, dos temas y 1440×900, 1280×800, 1024×768 y 390×844.
Cero hallazgos, desbordes, errores HTTP o de consola. La matriz anterior tiene
32 vistas de estimador y jefe: 224 hallazgos en Asistente, cero en Trabajos.
La [comparación](captures/asistente-trabajos-orb/comparacion.json) mantiene
los detectores y distingue los roles adicionales. Todos los PNG se comprimen
sin pérdida y se comprueba que sus píxeles no cambian.

- [Asistente antes](captures/asistente-trabajos-orb/antes/asistente/asistente__ESTIMATOR__light__1440x900.png), [después](captures/asistente-trabajos-orb/despues/asistente/asistente__ESTIMATOR__light__1440x900.png).
- [Trabajos antes](captures/asistente-trabajos-orb/antes/trabajos/trabajos__ESTIMATOR__dark__1440x900.png), [después](captures/asistente-trabajos-orb/despues/trabajos/trabajos__ESTIMATOR__dark__1440x900.png).
- [Propuesta dibujada](captures/asistente-trabajos-orb/recorrido/01-propuesta-antes-despues.png), [aplicada](captures/asistente-trabajos-orb/recorrido/02-aplicado.png), [auditoría](captures/asistente-trabajos-orb/recorrido/04-auditoria.png).
- [Low-E, dibujo y precio](captures/asistente-trabajos-orb/recorrido/06-lote-lowe.png), [artefacto completo](captures/asistente-trabajos-orb/recorrido/06-lote-artefacto-completo.png), [deshacer](captures/asistente-trabajos-orb/recorrido/08-lote-deshacer.png).

## Pase editorial

Primera ronda: presencia por contexto exacto en vez de una página de treinta
trabajos; reintentos sujetos al lifecycle y dueño de la conversación;
deshacer con protección de identidad e historial del editor. Segunda ronda:
medidas separadas de la etiqueta del marco; enlaces de objetos legibles en
oscuro; estados de consulta reales en el workspace, con error y permiso
explícitos. La revisión final pliega consultas y restricciones extensas y
traduce los nombres conocidos de herramientas en la presentación.

Se quitan sugerencias iniciales cuando ya existe una conversación, el CSS de
identificadores que dejó de usarse, respuestas redundantes sobre artefactos
y el color naranja permanente en estados terminados. Los fallos repetidos
se agrupan, con detalles técnicos plegados. El proveedor de prueba es una
insignia discreta únicamente en DEV. El historial auditable se conserva.

| Revisión | Resultado | Evidencia del alcance P17 |
| --- | --- | --- |
| R1 · Formatos y Mono tabular | PASA | Medidas, CLP, actor/duración y Δ; matriz y recorridos. |
| R2 · Radios e inglete | PASA | Tokens; hoja de preview y Orb plano. |
| R3 · Jerarquía y una superficie flotante | PASA | Dock de 400 px; trazas plegadas, sin tarjetas decorativas. |
| R4 · Naranja | PASA | Solo espera de persona/restricción; estado terminado usa semántica. |
| R5 · Teal | PASA | Controles, enlaces y foco por tokens en ambos temas. |
| R6 · Vocabulario y voz | PASA | Tipos/errores/herramientas traducidos; IDs en detalles. |
| R7 · Densidad | PASA | Workspace/lista densos; el dock no aumenta el inspector. |
| R8 · Cinco estados | PASA | Ocho ensayos de transporte y guarda real bloqueada. |
| R9 · Papel sobre mesa | PASA | Elevaciones del renderer dentro de la hoja de simulación. |
| R10 · Selección delineada | PASA | El bridge aplica las operaciones del editor existente. |
| R11 · Aperturas e íconos | PASA | Renderer DIN compartido; vista interior declarada. |
| R12 · Foco y teclado | PASA | Textarea, acciones, enlaces y details; foco tokenizado. |
| R13 · Movimiento | PASA | Reduced motion con tres Orbs; bienvenida opcional. |
| R14 · Acción principal | PASA | Aplicar antes; Deshacer después; detalles secundarios. |
| R15 · Fuentes y desconocidos | PASA | Motor comercial y traza; Uw Sin dato con causa. |
| R16 · Sin degradado/blur/brillo | PASA | SVG plano, sin filtros; guardas y Chromium. |
| R17 · Anchos | PASA | 48 vistas oficiales, sin desbordes ni hallazgos. |
| R18 · Acciones reales | PASA | Aplicar, descartar, deshacer, auditoría y reintento; sin UI paralela. |
| R19 · Firma F8 | PASA | Estado real compartido entre shell, dock y artefactos. |
| R20 · Capacidad del §8 | PASA | Low-E de segundo piso, filtro exacto, dibujos, Δ y undo real. |

## Gates y límites

`make lint typecheck test build` PASA sobre la corrección final: 829 pruebas de
motor y dos xfail conocidos, goldens byte a byte, 1.382 backend y 917 frontend
en 82 archivos. OpenAPI/orval reproducibles. Database Gate PASA: 84 archivos,
1.218 pgTAP, 444 integraciones PostgreSQL, 17 E2E y actualizaciones pobladas PG16.
El gate termina con código 0 y detiene sus servicios aislados. Los cuatro
checks de GitHub y el squash se registran al integrar.

Decisiones en [valores por defecto](../decisions/valores-por-defecto.md).
MiMo real continúa conectado por el entorno local; no se cambia su ruta ni se
introduce fallback a MOCK. El proveedor de prueba requiere habilitación
explícita y un tenant aislado. Las activaciones externas del programa continúan
en [ACTIVACION](../operations/ACTIVACION.md).

No hecho/riesgos: sin catálogo certificado ni Uw inventado; los resultados de
IA varían y pueden fallar con timeout o presupuesto, con historial conservado.
La propuesta del editor vive en la sesión hasta Guardar; una recarga recupera
el trabajo auditado, no una edición no guardada. Un deshacer posterior a otro
cambio exige el historial del editor. Una caída del registro de outcome muestra
la causa y pide verificar la auditoría; no se fabrica un evento. P17 no declara
aceptadas las superficies restantes de la cola.
