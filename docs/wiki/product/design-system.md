---
type: concept
status: active
updated: 2026-10-17
volatility: medium
verified_ref: codex/v1-experiencia
sources:
  - docs/wiki/sources/owner-ux-direction-2026-10-17.md
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

## Construcción autorizada · 17-10-2026

En `codex/v1-experiencia` se adoptó el tema claro único de mesa neutra/papel
blanco/acento verde; `ThemeProvider` descarta preferencias antiguas oscuras y
no ofrece selector. Constitución y tokens se reconciliaron. Navegación por rol,
obra con ventanas primero, fichas amplias y detalle progresivo reducen carga.
La cabecera del editor trunca nombres largos sin eliminar su nombre accesible.
[Cambios, pruebas y límites](../../ux/2026-10-17/10-implementacion.md).

Las aceptaciones siguientes conservan fecha/ref. No se atribuye al dueño la
elección de cada token ni se da por demostrada una nueva aceptación profesional.

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
