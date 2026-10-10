---
type: concept
status: active
updated: 2026-10-10
volatility: medium
verified_ref: codex/P16-catalogo-tecnico
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
---

# Autoridad de catálogo por familia

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
