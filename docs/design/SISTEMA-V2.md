# Material de interfaz DEKOPEN v2

P01 convierte la constitución en material compartido. El código de referencia está en `frontend/src/ui/`, los roles en `frontend/src/styles/tokens.css` y el manual, disponible solo en desarrollo, en `/dev/ui`. Las pantallas de producto se rediseñan en los encargos siguientes.

## Contratos para construir superficies

- Use `Button` con una acción principal por `ButtonGroup region`. Un `IconButton` exige nombre, atajo y efecto. Los botones pequeños miden 28 px, los normales 32 px y los táctiles 44 px.
- Use `ValidatedForm`: desactiva la validación nativa, anuncia errores en español y lleva el foco al primer campo. `Field` relaciona etiqueta, ayuda y error. `NumberField` entrega strings canónicos; `MoneyField` declara la moneda y su precisión.
- Use `Panel`, `Inspector` y `KeyValue` para estructura técnica. `Stat` requiere una decisión asociada. `DataTable` conserva el valor Decimal para ordenar, ofrece selección y acciones en lote, y virtualiza sobre 200 filas.
- Use `domainLabel`/`StatusChip` para estados; el mapa cubre todos los enums generados. `UnknownValue` muestra causa y acción. Los estados de carga, error, bloqueo y falta de permiso son componentes, no textos sueltos.
- Use los formateadores de `format.ts` y los componentes `DomainValues`. Los milímetros usan espacio fino U+2009; el dinero usa la moneda declarada. Para rellenar un input o enviar un payload desde el backend, use `decimalInputValue`, nunca el texto formateado.
- `TraceButton` presenta una traza recibida; no produce fórmulas ni resultados. Su contrato incluye fórmula, entradas, autoridad y versión. Si la API no adjunta esos campos, muestra «Sin dato» y la causa. Una huella de BOM vive en Detalles técnicos y no sustituye una fórmula.
- `OpeningGlyph` declara vista y apertura. La vista exterior refleja bisagras/manilla y usa líneas discontinuas. Una corredera usa flechas paralelas al carril.
- La paleta tiene un registro extensible; P03 conectará el shell. Abrir una nueva capa operativa cierra la anterior. Los menús y popovers se ajustan al viewport, y los diálogos devuelven el foco al cerrar.

## Decisiones cerradas y contradicciones

El redondeo de presentación es `ROUND_HALF_UP`, implementado con enteros `BigInt`: preserva empates negativos y montos superiores a 2⁵³. La autoridad sigue siendo el Decimal original del motor; el formato nunca altera el payload. El motor usa ese modo en sus cuantizaciones declaradas, no una precisión única para todas las magnitudes.

La rampa g-500 se conserva exactamente como pide la constitución. Su contraste no sirve para texto pequeño en todos los fondos claros. El rol `text-small-muted` usa g-700 en claro y un rol AA en oscuro; unidades y metadatos pequeños usan ese rol. g-500 queda para guías y anotaciones grandes. Esta resolución aplica la exigencia AA del mismo documento.

El estudio histórico de identidad dibujó un vértice hacia la bisagra. La constitución vigente §3.6 exige vértice hacia la manilla y abatimiento desde las esquinas inferiores al centro superior. P01 sigue la constitución; la referencia histórica no se presenta como autoridad vigente.

La única reproducción de degradados/radios históricos es el contrajemplo pasivo «Mal» de `/dev/ui`. La ruta, su import y su lámina desaparecen del build de producción. No contiene botones sin efecto ni resultados de ingeniería.

## Guardas y evidencia

`scripts/check_guards.py` mantiene las guardas de Decimal, SQL/RLS y colores, y agrega un trinquete por archivo/regla/fragmento. `scripts/design_guard_baseline.json` admite únicamente violaciones heredadas: una nueva ocurrencia falla. Al retirar una violación, reduzca su entrada; nunca incremente la línea base para aceptar un defecto nuevo. El render de enum crudo y las palabras inglesas se detectan por heurística documentada en el propio script; no reemplazan la revisión editorial.

El test de tokens lee todo el CSS y las referencias en código, falla ante una variable fantasma y limita las variables sin uso con `unused-token-baseline.json`. Los pares de texto/fondo y tinta/fondo semántico se prueban en ambos temas. El test AST de `domainLabels` compara los enums de Orval con el mapa; agregar un miembro sin etiqueta provoca un fallo.

La evidencia de P01 está en `docs/redesign/captures/sistema-diseno/`: manual y axe, validación real de Cobranza/Catálogo, matriz de rutas antes/después, cobertura CSS y registro de reglas retiradas. Consulte `aceptacion.md` para los resultados y sus límites.
