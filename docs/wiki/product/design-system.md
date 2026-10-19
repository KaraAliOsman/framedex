---
type: concept
status: active
updated: 2026-10-18
volatility: medium
verified_ref: fa3731843dbfbd75d00024e95f4986a3616a8747
sources:
  - ED2 PR https://github.com/KaraAliOsman/framedex/pull/145, CI 4/4 sobre dd3fe1ffce2c14ba1125442d8a137021d1ba32f2, corrida https://github.com/KaraAliOsman/framedex/actions/runs/38091279743, squash fa3731843dbfbd75d00024e95f4986a3616a8747, 2026-10-10.
  - ED2 implementación 0ab8b7204ac250c0bd8d118fdab041c22b5892b3, navegador, 2026-10-10
  - docs/redesign/ED2-ACEPTACION.md
  - ED1 PR https://github.com/KaraAliOsman/framedex/pull/137, CI 4/4 sobre ae9292864ad7d8efb9beba9243451fba49d8c04e, squash 7c214c28f2af841f7fe21c6ecf08a0b0045b9c9d, 2026-10-09
  - ED1 autoridad angular 9019282e1ded4b287f4518b09da069bcdee20abc, gate completo y ocho vistas finales, 2026-10-09
  - ED1 corrección de apariencia 3dd2a8bef4c4b05d01fe4598f5b99ea08d283c75, gate completo y ocho vistas, 2026-10-09
  - ED1 implementación ecf24d2b02184135c60ea64c2691db2a63672ee2, gates locales y navegador, 2026-10-09
  - docs/design/CONSTITUCION.md
  - docs/design/SISTEMA-V2.md
  - frontend/src/ui/
  - frontend/src/styles/tokens.test.ts
  - frontend/src/i18n/domainLabels.test.ts
  - docs/redesign/captures/sistema-diseno/aceptacion.md
  - docs/redesign/ED1-ACEPTACION.md
---

# Sistema de diseño convertido en código

## Referencias profesionales y personaje · 18-10-2026 · dirección pendiente

La [aclaración del dueño](../sources/owner-credits-and-grokbot-2026-10-18.md)
pide referencias profesionales adicionales y fidelidad al personaje animado
de Grok Bot. La [matriz de veinte referencias](../../research/2026-10-18-direccion-final/05-referencias-profesionales.md)
conecta Apple, Pentagram, Adobe, Shapr3D, IBM y sector con jerarquía, selección,
inspector, documentos y respuesta. Son fuentes DOC/VIS con límites explícitos;
no nuevas sesiones operadas de esas aplicaciones.

El [contrato del personaje](../../research/2026-10-18-direccion-final/06-grok-bot-personaje-y-movimiento.md)
separa figura/movimiento fieles de la composición de chat adaptada. Sus ciclos
expresivos pueden durar segundos: la regla breve de transiciones UI no los
limita a 280 ms. Conservar movimiento reducido y suspensión cuando no se ve.
Claude concilia esa excepción y la figura en Constitución durante 01; no se
modificó la autoridad visual ni se implementó producto en esta investigación.

## Dirección resuelta; diseño profesional por implementar · 18-10-2026

Tras revisar la implementación de Claude, el dueño vuelve a rechazar su calidad:
asistente, controles, estados y superficies no expresan suficiente jerarquía.
La revisión local del 18-10 sí pudo inspeccionar la app en vivo (`6f78e329` más
cambios locales de `claude/v1-implementacion`); esto actualiza el límite de acceso
de la investigación anterior. La [auditoría](../../research/2026-10-18-revision-profunda/auditoria-dekopen.md)
vincula cada cambio propuesto con problema, causa y evidencia.

La [corrección posterior](../sources/owner-final-direction-2026-10-18.md) conserva
Mesa de obra y Estudio como vistas del mismo producto manual, con Mesa como
inicio recomendado y copiloto opcional en popup global. Sustituye el panel
acoplado y Centro de encargos como entrada. No acepta los píxeles de los mocks.
El [contrato final de diseño](../../research/2026-10-18-direccion-final/02-diseno-y-referencias.md)
define anatomías, controles y referencias para construir y revisar en producto.
No se cambia la Constitución durante esta investigación; el prompt 01 exige
conciliar sus reglas afectadas durante la implementación.

## Intención reciente y propuesta pendiente · 17-10-2026

Tras rechazar y revertir dos rediseños, el dueño encarga investigación sin código.
Pide un tema definitivo, claridad de controles, menos texto/jerga y una IA 2D
viva; considera útiles el logo, turquesa y bases del dibujo/3D. El [plan visual](../../research/2026-10-17-claude/04-direccion-visual-e-interaccion.md)
identifica cambios propuestos a la constitución y aplica principios Apple/Emil
sin copiar productos. No se modifica la constitución durante la investigación.
La dirección clara/tokens del plan son propuestas, no aceptación del dueño.
Las declaraciones de intención siguientes sobre dos temas, densidad y cargador
son antecedentes cuando contradigan este encargo; sus hechos de código mantienen
el ref histórico. No hubo nueva inspección visual en vivo por fallo de conexión.

**Hecho verificado en PR #117, merge `023b8ba303b680ca50b6e10119ce4ee4514c9c38`:** tokens por rol, fuentes IBM Plex autoalojadas, primitivas técnicas, formatos Decimal, validación común en español, guardas con trinquete y detectores computados. `/dev/ui` consume las posiciones/BOM de la organización autenticada y existe solo en desarrollo. No acredita que las pantallas pendientes ya estén rediseñadas.

**Intención del dueño:** cada encargo adopta este material y conserva el oficio visible: inglete de la hoja, cota como cargador, gramática de aperturas y procedencia del número. El flujo productivo y los cálculos continúan gobernados por motor, catálogo y revisiones emitidas.

**Contexto histórico:** el estudio de identidad y la constitución difieren en la orientación del vértice de apertura. Se sigue la constitución vigente. g-500 tampoco satisface AA para todo texto pequeño; el rol pequeño atenuado tiene una tinta accesible, manteniendo la rampa exacta.

**Verificación editorial ED1:** la densidad sigue la tarea: Producción y su shell
usan `workshop` también para el jefe, con tema oscuro inicial si no existe
preferencia elegida. El control de apariencia actualiza el contexto real y guarda
la elección desde el primer clic. Una primitiva `StatusBadge` concentra
veintiocho adopciones y el tono de decisión humana. Los inspectores de módulo
y paño comparten paleta heredada, etiquetas y renderer DIN. Fechas usan los
formatos canónicos. Las secciones conservan polígonos/ejes y llevan su texto
fuera del SVG; sin profundidad declarada no imprimen una medida aproximada.
El plan mantiene las longitudes del motor, tamaño de texto constante y tinta
física legible. Las piezas estrechas se seleccionan mediante leyenda táctil;
los valores ausentes siguen Sin dato. Estas reglas no crean defaults de negocio.

La matriz ED1 tiene 192 vistas antes y después, con cero hallazgos posteriores.
La baseline cae de 257 claves/716 ocurrencias a 69/187; de las 466 infracciones
reales iniciales se eliminan 279. Ningún detector ni umbral se flexibiliza.
Los recorridos conectan Hoy, editor, emisión real, jefe/operario y MiMo real
con aplicar/recargar/deshacer. [Aceptación ED1](../../redesign/ED1-ACEPTACION.md)
conserva la rúbrica por superficie y los refs de integración.

**Decisiones editoriales ED2 para la ola 3:** las medidas de CNC comparten
`formatMillimeters`; los descuentos usan la fracción decimal y las dimensiones
de una sección se leen de sus vértices confirmados a centésimas. El float del
renderer no gobierna el texto técnico ni la geometría aplicada. `StatusBadge`
representa también procedencia, capacidades y compra confirmada; fabricante,
familia y material son metadatos, sin chips de estado. Las capacidades del
catálogo forman filas técnicas, sin tarjetas ni puntos decorativos.

Las tablas estrechas conservan etiqueta y valor con `data-label` y el patrón
común `.ui-stacked-table`; no eliminan columnas ni orden/filtro. Inventario
permite encoger sus hijos y usa `workshop` para el operario. Consultar material
no da permiso de modificarlo: la orientación de alertas lleva al dueño. La
superficie consume el tema elegido y mantiene tintas/fondos correspondientes,
con objetivo táctil de 44 px también en el checkbox de stock. La
preparación de emisión nombra módulos por ordinal físico; conserva los UUID
internos y la autoridad de cada hoja. Los ocho alias de tokens sin consumidores
se eliminan, manteniendo la guarda de variables definidas.

[Aceptación ED2](../../redesign/ED2-ACEPTACION.md) registra la comparación y los
recorridos. Estas decisiones son de presentación; no crean valores por defecto
de catálogo, precios, fabricación, máquina o permisos.

**Límites actuales:** sin autoridad térmica, Uw sigue Sin dato. La aceptación
de la ola 1 no acredita compras, inventario, CNC, instalación ni portal completo;
esas superficies conservan encargos propios. La matriz provisional del portal
era una limitación histórica de P01: P09 ya verifica emisión y QR reales,
mientras P10 conserva la aceptación completa del cliente. Toda fórmula/traza
debe provenir del motor; una huella por sí sola no autoriza inventarla.

El manual y las guardas viven en [Sistema v2](../../design/SISTEMA-V2.md). La [realidad actual](../state/current-reality.md) registra el ref aceptado al integrar.
