---
type: concept
status: active
updated: 2026-10-21
volatility: medium
verified_ref: gpt/dk2-p01e-niveles-y-bloqueos
sources:
  - engine/src/dekopen_engine/catalog_rules.py
  - engine/tests/test_gold_cases_catalog_families.py
  - supabase/migrations/20261229000100_catalog_family_authorities.sql
  - supabase/migrations/20261229000300_catalog_review_interchange.sql
  - scripts/check_catalog_family_upgrade.py
  - docs/redesign/captures/sistemas-catalogo/aceptacion.md
  - docs/wiki/product/glass-composition.md
  - docs/redesign/P16-ACEPTACION.md
  - engine/src/dekopen_engine/catalog_authority.py
  - backend/catalogs/authority.py
  - supabase/migrations/20270121000000_catalog_review_sources.sql
  - backend/catalogs/use_levels.py
  - backend/catalogs/frozen_use.py
  - backend/tests/integration/test_catalog_use_levels.py
  - supabase/migrations/20270204000000_quote_without_workshop_policies.sql
---

# Autoridad de catálogo por familia

## DEKOPEN 2 · Traza de sugeridos · 21-10-2026

Verificado en `gpt/dk2-p01b-traza-sugeridos`: el motor acepta
`SystemParams.value_origins` y adjunta `EngineResult.assumptions` para los
valores SUGGESTED que consulta durante el cálculo. No resuelve ni inventa
parámetros. La traza es local al contexto de cálculo, conserva las de los
módulos al agregarlos y evita duplicados. Un junquillo se identifica por el
espesor de paquete consumido, no por el espesor neto del vidrio.

`engine/tests/test_catalog_assumptions.py` cubre reglas irrelevantes, vidrio
doble, valores confirmados, corte estructurado, conjuntos, errores y concurrencia.
Los serializadores omiten los campos aditivos ausentes en contratos históricos;
`python -m engine.scripts.regenerate_golden --check` verifica los mismos bytes.
El historial de autoridades descrito abajo sigue siendo aplicable a los
contratos existentes.

### Origen por celda y datos de plantilla

En `gpt/dk2-p01c-valores-y-plantillas`, `catalog_value_history` añade versiones
inmutables por campo de sistema, perfil, junquillo y herraje. El valor actual
sigue en las tablas tipadas existentes. Los cambios registran el anterior,
incluida la eliminación del valor; confirmar su origen añade otra versión.
MANUAL requiere una evidencia revisada que coincida exactamente con el dato.
La migración solo clasifica datos históricos ya revisados y conserva la
distinción sintética. No promociona registros desconocidos por omisión.

`backend/catalogs/templates/families-v1.json` contiene cuatro familias con
valores de oficio explícitamente SUGGESTED, sin precios ni identidades del
proveedor. `catalog_series_setup` prepara la verificación del taller y la
invalida al editar reglas. Las pruebas en una base local sintética independiente
comprueban tenant/RLS, historia inmutable, evidencia y verificación; no prueban
todavía el flujo completo de alta ni habilitan fabricación. La conexión a
endpoints y al motor se incorpora en P01d; los niveles de uso siguen en curso.

### Ficha y lotes de P01d

`gpt/dk2-p01d-ficha-y-lotes` expone `/catalogs/series/` para crear desde plantilla,
leer seis pestañas y editar/confirmar lotes por revisión. El origen de un valor
aportado por el taller no se atribuye a la plantilla. Los lotes rechazan filas
de otra serie y revierten todo si una celda falla; el historial sigue accesible
tras quitar un perfil. Los costos del tab Precios solo se proyectan al dueño.

El repositorio incorpora versiones actuales al contrato puro del motor. La
integración `test_real_series_calculation_reports_only_consumed_suggestions`
calcula 1200 × 1100 abatible y comprueba idéntico despiece tras confirmar los
sugeridos. Las revisiones técnicas y de evidencia existentes también añaden
orígenes; insertar/borrar perfiles invalida la ventana de prueba. Esto aún no
implementa por sí sola los niveles; P01e añade los siguientes bloqueos.

### Permisos por dependencia de P01e

Verificado en `gpt/dk2-p01e-niveles-y-bloqueos` el 21-10-2026: el contrato
`usage` identifica DRAWABLE, QUOTABLE, MANUFACTURABLE y MACHINE_READY, con
pendientes que señalan campo, regla, origen, acción y operación afectada.
El antiguo `readiness` queda obsoleto; su `quote_ready` se redefine como alias
de QUOTABLE. Sus razones históricas conservan el diagnóstico antiguo y no
deben usarse para decidir si se puede cotizar.

Dibujar requiere perfiles con rol y ancho visible. Cotizar acepta SUGGESTED
y comprueba reglas y precios vigentes, unidades y ambigüedades. Para un precio
concreto el motor y el repositorio resuelven exactamente los materiales usados;
un color o artículo ajeno no bloquea ese precio. El catálogo completo muestra
la cobertura de toda la serie. La ausencia de costos no impide cortar una
serie técnicamente confirmada: cada permiso tiene sus propias dependencias.

Fabricar exige valores confirmados y verificación con fecha, actor y huella
del catálogo actual. P03 aportará la ventana de prueba y su decisión humana.
Los ejemplos globales permanecen explícitamente sintéticos: su uso de prueba
no los convierte en series reales verificadas. Las estaciones, el inspector,
las mediciones y el proceso conservan sus comprobaciones específicas.

Una cotización puede emitirse sin políticas de taller: registra ausencias,
precio y despiece exactos, sin sintetizar hechos de fabricación. Las políticas
declaradas siguen ligadas a la serie y empresa correctas. El PDF comercial
funciona; hoja de corte y OT informan los pendientes congelados. Ni liberar
ni reutilizar un artefacto consulta el catálogo mutable para reinterpretar
la revisión. Confirmar después exige otra revisión antes de fabricar.

`test_catalog_use_levels.py` ejercita PRO6004 sintética de 1200 × 1100 con
precios del taller, PDF y optimización; comprueba políticas de otra serie,
huella obsoleta y rechazo físico después de emitir y luego confirmar.
Estas pruebas no validan medidas ni precios reales de Proline.

La emisión v2 usa las confirmaciones por celda y la verificación vigente para
la revisión técnica. Un `review_pending` del modelo anterior sigue visible
como diagnóstico, pero no puede contradecir una revisión actual completa.
Los controles físicos de fabricación y proceso siguen siendo obligatorios.
`test_current_cell_confirmation_supersedes_stale_row_review_but_keeps_physical_checks`
comprueba la transición con Postgres real y dos rechazos físicos. Una revisión
de informes térmicos no verifica las reglas de fabricación: el PDF comercial
puede congelar esos informes y conservar el permiso físico bloqueado.

## Biblioteca real y fuentes reunidas · 18-10-2026

El [paquete final](../../research/2026-10-18-direccion-final/README.md) conserva
esta exigencia en el producto manual: incorporar/usar una serie real no puede
depender de IA ni de créditos. La IA de planes superiores acelera preparación
y excepciones con la misma revisión técnica. La fase actual sigue documental:
no hay nueva publicación ni aceptación de fabricación por escribir el prompt.

El dueño pide fabricante → serie/sistema → configuraciones/artículos, imágenes
útiles y separación de demos. PRO6004 y PROSLIDE70 se agrupan bajo Proline;
un número comercial 60/70 no demuestra equivalencia. «Vinhaus» sigue ambiguo.
La [revisión de fuentes](../../research/2026-10-18-revision-profunda/catalogos-reales.md)
incluye Proline, Winhouse, Deceuninck e Indalum y separa procedencia, identidad
de proveedor y preparación para cotizar/fabricar/CNC.

A diferencia de la disponibilidad descrita en la investigación del 17-10,
esta revisión sí inspeccionó los PDF de Proline aportados/referenciados en el
material del dueño: catálogo de 24 páginas y casos de corte de 25 páginas, con
huellas y límites documentados. Los casos no se convierten en fórmula general;
errores de documento o celdas `#NAME?` no son autoridad productiva. No se publicó
un catálogo ni se certificó fabricación mediante esta investigación.

La app local del 18-10 en `claude/v1-implementacion` (`6f78e329` más cambios
locales) muestra lista plana dominada por DEMO; no está vacía de registros.
La propuesta mejora su organización sin borrar la DB ni revisiones existentes.
Ver [auditoría](../../research/2026-10-18-revision-profunda/auditoria-dekopen.md).

## Investigación posterior · 17-10-2026

El dueño pide PDF como entrada única habitual, integración asistida y revisión
de excepciones. El [plan](../../research/2026-10-17-claude/08-catalogos-y-ocr.md)
propone extracción por regiones, trabajos reanudables, relaciones y preparación
por capacidad. No está implementado. En `6f78e329`, el helper multimodal de
`backend/ai_gateway/multimodal.py` admite como máximo 20 páginas y omite imagen
cuando hay texto; el compilador acota texto y pide división manual. Estos límites
no significan ausencia total de OCR/IA. Los PDF concretos de Proline y Aluminios
2000 no fueron aportados ni probados. Ninguna interpretación IA certifica una
regla de fabricación ausente. Los hechos históricos siguientes mantienen sus
fuentes y no son evidencia de la nueva experiencia propuesta.

## Hechos verificados en D01

Los productos nuevos eligen una familia declarada: practicable, corredera, elevable,
puerta o fijo de fachada. El motor comprueba las aperturas de cada módulo contra esa
familia y sus límites con fuente. No basta que dos perfiles dibujen rectángulos
parecidos para intercambiarlos. La API devuelve sistemas visibles compatibles al
rechazar una apertura; el editor filtra las opciones con el mismo contrato.

Cada perfil admite una regla de corte y una de refuerzo con procedencia. El motor
aplica los descuentos, pérdidas por extremo y redondeo usando Decimal; el refuerzo
depende del largo y acabado y produce sus tornillos en el BOM. Los goldens nuevos
incluyen perfiles, junquillos, correderas y el contraste blanco/foliado de 900 mm.
Los goldens históricos permanecen byte por byte.

Las cinco series DEMO pasan el gate real de cotización. La disponibilidad de
refuerzos usa la regla declarada por perfil, incluidos hoja de corredera y riel;
no exige acero donde el catálogo nuevo no lo declara. La integración RLS y el
descubrimiento de sistemas del navegador verifican esta coincidencia.

La migración conserva la autoridad histórica para posiciones existentes, incluso
si la familia antigua mezclaba aperturas. Solo los borradores exclusivamente DEMO
se trasladan a copias por familia que preservan sus reglas anteriores. Proyectos
comerciales, composiciones mixtas y documentos emitidos conservan su autoridad.
Un registro inmutable guarda el BOM anterior y el verificador de upgrade comprueba
los cortes y hashes exactos. Esto no certifica el antiguo catálogo ni convierte sus
datos en recomendaciones de fabricación para productos nuevos.

## Ingesta y revisión

La plantilla oficial actual tiene diez hojas y conserva los lexemas numéricos del XLSX.
D02 agregó **Reglas de vidrio**; la versión integrada en D01 tenía nueve hojas.
Las fórmulas se rechazan como autoridad; los errores identifican fila y columna.
PDF con texto, planillas, correo y texto pegado usan extracción y candidatos
tipados. La IA necesita evidencia literal para cada valor; LOW y valores sin
soporte quedan desconocidos. La procedencia original se conserva después de una
corrección humana.

Ambos caminos convergen en revisión, simulación del diff y publicación por clic.
Un token liga el diff revisado al catálogo actual; los locks y la transacción
impiden aplicar una vista previa obsoleta o publicar una parte del archivo.
Exportar devuelve las filas revisadas. Deshacer revierte la publicación completa
solo mientras ninguna autoridad publicada esté usada o modificada. El vidrio se
retira con un registro inmutable, sin borrar su identidad ni su historial; una
nueva publicación necesita otra versión.

El revisor autorizado es el dueño o encargado de taller. El estimador consulta;
backend y RLS hacen cumplir el permiso. Costos se mantienen en el contexto de
precios del dueño y no aparecen en auditoría de IA para otros roles.

## Intención del dueño y límites

El catálogo de arranque usa cinco series DEMO y precios reproducibles con semilla 20261005. Insignias en catálogo, editor, costos y documentos declaran que son
sintéticos. La importación de una fuente real requiere revisión; ni la IA ni la
semilla certifican valores.

La verificación histórica D01 con MiMo produjo 31 candidatos de un PDF sintético:
324 campos HIGH con soporte y 27 UNKNOWN. Ese PDF no se publicó en D01. IA3
verificó después transporte multimodal real y PDF literal/mixto/escaneado.
P16 verifica desde Catálogo un PDF de tres páginas con tres candidatos, dos
dudosos, corrección humana de colores/sección, regla excluida, publicación y
deshacer. Su auditoría conserva archivo, extracción, revisión, publicación y undo.
Una imagen rasterizada de la ficha también produce candidatos con MiMo real;
ningún valor visual sin literal comprobable recibe HIGH ni se publica solo.
D02 agrega [composición y reglas de vidrio](glass-composition.md).
D03 y D04 añaden [aperturas físicas](physical-openings.md) y
[clases de herrajes](hardware-classes.md), con sus propias pruebas y autoridad.
D05–D07 ya integraron [colores](color-finishes.md),
[accesorios](accessories-services.md) y [vano](opening-measurements.md),
cada uno con sus propias pruebas de autoridad. La plantilla no certifica una
declaración del fabricante por contener columnas para esas capacidades.

La evidencia y las limitaciones están en [la aceptación](../../redesign/captures/sistemas-catalogo/aceptacion.md).

## Autoridad visible en P16

Catálogo y emisión usan `catalog_authority_gate` con revisión, fabricación y
proceso. Catálogo comprueba cobertura; una emisión declara los artículos usados.
La paridad DEMO_60/incompleto compara el mismo conjunto. Liberación conserva
decisión/proceso sellados y no consulta autoridad mutable del catálogo.
El contrato `WHITE_FIXED_CATALOG` permanece: cotizable no implica fabricación,
centros ni CNC completos.

DEMO tiene prioridad incluso después de una revisión. VERIFIED exige revisión
vigente, evidencia acorde con cada valor técnico presente y una sección válida.
REVIEWED no es certificación. Las correcciones HUMAN_CORRECTION conservan original
y literal, pero no se atribuyen al fabricante. La revisión de la sección exige
origen/orientación explícitos y profundidad exacta; la lectura histórica permanece.

Los eventos de importación y los valores/fuentes de la evidencia son inmutables.
Los cambios de estado de revisión requieren actor técnico correcto; el miembro
no puede autocertificarse. Originales potencialmente comerciales solo se descargan
por dueño/jefe de taller; los historiales respetan la visibilidad del import.
Véase [aceptación P16](../../redesign/P16-ACEPTACION.md).
