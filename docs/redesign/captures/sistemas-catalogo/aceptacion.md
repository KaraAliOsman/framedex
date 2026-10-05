# D01 · sistemas, autoridad e ingesta de catálogo

La familia de un sistema limita las aperturas que el motor admite. Las reglas de
corte, refuerzo y límites tienen datos exactos y fuente. La importación manual y
la extracción por IA llegan a un diff común: ningún candidato cambia el catálogo
antes de la revisión y el clic de publicación. Los cinco sistemas de arranque,
sus precios y los documentos de prueba están marcados DEMO.

## Alcance y evidencia

- Motor: cinco familias, 18 roles, reglas Decimal, redondeo y refuerzo por acabado.
  Los goldens nuevos cubren marco, hoja, montantes y junquillos en PVC 60/70 y
  corredera; blanco/foliado de 900 mm y tornillos de refuerzo. Los goldens
  históricos no cambian.
- Migración: autoridad histórica inmutable para los productos ya guardados;
  borradores DEMO por familia sin cambiar sus cortes. Comerciales, mixtos y
  emitidos conservan su autoridad. El verificador de upgrade comprueba siete
  posiciones, hash y BOM, también en PostgreSQL 16.
- Plantilla XLSX de nueve hojas y CSV por hoja. Lectura numérica exacta, sin
  fórmulas ejecutables; validación de fila/columna; los valores faltantes quedan
  desconocidos. Vidrios puede declarar su matriz de junquillo con fuente.
- Revisión: cita o celda junto al valor, correcciones separadas del original,
  token del diff, publicación transaccional con procedencia y revisor. La UI
  conserva la revisión durante el refresco. Exportación y deshacer son reales.
- Deshacer: rechaza datos ya usados o modificados. Las referencias de vidrio se
  retiran mediante historial inmutable; no se eliminan documentos ni auditoría.
- Permisos: dueño/encargado publican, estimador consulta. RLS separa organizaciones
  y los costos se mantienen en el contexto autorizado de precios.

## Flujos de navegador

`frontend/scripts/verify-d01.mjs` recorrió el proveedor real ya procesado y la vía
manual. `flujos/resultado.json` conserva las aserciones, sin credenciales:

| Flujo | Resultado | Evidencia |
|---|---|---|
| PDF con texto → MiMo → candidatos revisables | PASA: 31 filas, 324 HIGH respaldados, 27 UNKNOWN; no se publica | `../../fixtures/sistemas-catalogo/mimo-verification.json`, `flujos/01-ia-fuente.png` |
| Errores de fuente → diff bloqueado | PASA: error con fila/campo y acción para corregir; publicación ausente | `flujos/02-ia-errores-diff.png` |
| Nueve hojas → diff → revisión → publicación | PASA: 32 filas y 34 cambios; botón deshabilitado antes de la revisión | `flujos/05-manual-diff.png` |
| Publicación → exportar Vidrios → deshacer | PASA: CSV descargado y publicación deshecha | `flujos/vidrios-exportados.csv`, `flujos/resultado.json` |
| Vacío y carga | PASA: demora y lista vacía controladas en la lectura; sin escritura de prueba | `flujos/06-vacio.png` |
| Error de lectura | PASA: HTTP 503 inyectado, causa en español y revisión conservada | `flujos/07-error.png` |
| Estimador sin permiso de publicación | PASA: consulta real; no aparecen carga ni publicación | `flujos/08-sin-permiso-publicar.png` |
| Catálogo y precios de arranque | PASA: datos de BD, insignia DEMO y explicación de semilla | `flujos/03-catalogo-demo.png`, `flujos/04-precios-demo.png` |
| Documentos DEMO | PASA: PDF rasterizado e inspeccionado y XLSX con metadatos | `../../fixtures/sistemas-catalogo/cotizacion-demo.pdf` |

La revisión se probó en 1440×900, 1280×800 y 1024×768, claro/oscuro,
sin desbordes ni errores de consola. `ux:capture` produjo ocho pares en Catálogo,
incluido 390×844: **cero hallazgos y cero desbordes** en `despues/report.json`.
`antes/report.json` conserva la medición previa y sus defectos. Las capturas
adicionales de costos y editor están en `precios/` y `editor/`; los hallazgos
heredados de esas superficies corresponden a P07/P04/P16 y no se acreditan como
rediseñados por D01. El editor no necesita 390 px para la aceptación de este encargo.

## Verificación automática

Lint, typecheck, test y build pasan. Resultado: **482 pruebas del motor y dos
xfail históricos**, **1 136 de backend**, **704 de frontend**. OpenAPI/orval se
regeneran sin drift; los source guards permanecen activos. El byte-check de
goldens es de solo lectura y pasa.

Database Gate: pendiente de cierre de la corrida limpia. Se exige lint SQL,
pgTAP, integración RLS, navegador de autenticación y PostgreSQL 16, con el
verificador poblado de migración. No se acepta D01 hasta que pase completo.

## Pase editorial

Primera ronda: (1) separar opciones de apertura por familia y explicar la
incompatibilidad; (2) llevar la fuente al lado de cada candidato en una sola
revisión; (3) preservar el panel durante el refresco después de publicar.

Segunda ronda: (1) eliminar enums/UUID visibles y traducir las clasificaciones y
unidades de herraje; (2) corregir la confirmación cortada y la jerarquía del botón
de publicación; (3) reemplazar radios ajenos a tokens, texto demasiado pequeño y
dimensiones diminutas dentro de las secciones por rótulos legibles.

Se quitó la publicación directa del importador antiguo para las nueve hojas; no
hay dos caminos de autoridad. Se quitaron identificadores internos del diff y
nombres duplicados en la ficha. Se quitó la sombra de selección, reemplazada por
contorno y tinte. Las fuentes originales siguen consultables.

| Revisión | Resultado | Evidencia del alcance modificado |
|---|---|---|
| R1 · Formatos y unidades | PASA | Diff en Mono tabular; mm/kg en rótulos; CLP y fechas Chile; exportación exacta |
| R2 · Radios e inglete | PASA | Radios de token ≤4 px; detector sin hallazgos en catálogo |
| R3 · Jerarquía | PASA | Tablas y delineados; una revisión integrada y diálogo puntual para deshacer |
| R4 · Naranja | PASA | Marca y necesidad de revisión; publicación usa teal |
| R5 · Cromo | PASA | Tokens teal en selección, foco y acción |
| R6 · Vocabulario | PASA | Familias/roles/errores/clasificaciones en español; referencias internas ocultas |
| R7 · Densidad | PASA | Campos técnicos en grilla; comparación de valor/fuente con lectura tabular |
| R8 · Cinco estados | PASA | Recorrido y capturas de vacío/carga/error/permiso/bloqueado |
| R9 · Papel | PASA | PDF claro con aviso DEMO y página legible; contraste de fuente/cromo en ambos temas |
| R10 · Selección | PASA | Contorno y tinte; sin sombra de elevación |
| R11 · Símbolos | PASA | Familias coherentes con apertura; no se representa corredera como practicable |
| R12 · Teclado | PASA | Controles semánticos, foco visible, confirmación con etiqueta y check real |
| R13 · Movimiento | PASA | Sin animación de carga decorativa; reducción de movimiento heredada del sistema |
| R14 · Acción principal | PASA | Comparar → revisar → publicar; publicar solo aparece en un diff válido |
| R15 · Autoridad | PASA | Fuente por campo, UNKNOWN explícito; goldens y rechazo del motor |
| R16 · Sin efectos prohibidos | PASA | Cero degradados, blur y brillo en revisión y fichas |
| R17 · Anchos | PASA | Tres anchos de escritorio en dos temas; catálogo también 390; confirmación sin recorte |
| R18 · Acciones reales | PASA | Subir, analizar, revisar, publicar, exportar y deshacer completados |
| R19 · Firma | PASA | Cita PDF/celda junto a cada valor extraído |
| R20 · Capacidad | PASA | PDF real a candidatos tipados en minutos; la revisión conecta con las autoridades del motor |

## Decisiones y límites

Las decisiones están en `docs/decisions/valores-por-defecto.md` y la síntesis durable
en `docs/wiki/product/catalog-authority.md`. El proveedor MiMo está conectado en el
backend; D01 no necesita adaptadores nuevos de pagos, SII ni correo.

No hecho/riesgos: ninguna serie DEMO es certificada. El proveedor de texto no hace
OCR de fotos/escaneos sin texto; la UI declara esa limitación y requiere fuente
legible. No se atribuye a D01 la autoridad especializada completa de D02–D07 ni la
aceptación final del catálogo de P16. Deshacer una publicación usada se bloquea
para conservar historia. El fixture real de IA es sintético y no constituye una
evaluación universal de extracción de catálogos de fabricante.
