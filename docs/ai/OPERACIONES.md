# Operaciones compartidas de diseño y proyecto

IA2 usa `design-ops-v1`, definido en `engine/src/dekopen_engine/design_operations.py`.
Sus 50 operaciones declaran nombre, parámetros, precondiciones, manejador,
descripción y ejemplos. La API publica el mismo registro y OpenAPI genera los
tipos del cliente. Los comandos, atajos e inspector expresan intención; el motor
devuelve el modelo resultante. La IA no mantiene un vocabulario de edición propio.

## Simular, aplicar y deshacer

- `GET /api/v1/projects/operations/registry/`: registro autorizado para la UI.
- `POST /api/v1/projects/operations/simulate/`: copia del diseño, operaciones,
  evaluación, hojas/manillas del motor, diff y venta neta indicativa.
- `POST /api/v1/projects/{id}/operations/preview/`: posiciones afectadas,
  simulaciones y firma del estado actual, sin escribir el proyecto.
- `POST .../apply/`: requiere esa firma y una clave de idempotencia; ejecuta
  todas las operaciones en una transacción y conserva evidencia inmutable.
- `GET .../state/?operation_key=...`: consulta si la propuesta se aplicó o
  deshizo. Reabrir un trabajo lee esa autoridad sin repetir la escritura.
- `POST .../{operation_id}/undo/`: restaura las identidades y las mediciones
  originales; una edición posterior bloquea un deshacer obsoleto con causa.

Las escrituras requieren dueño o estimador y pertenencia al proyecto/tenant.
Una propuesta obsoleta debe volver a simularse. Emisión, liberación, compras y
enlaces de pago solo preparan la ruta; su ejecución exige el clic humano allí.

## Herramientas y cifras

`calculate_position`, `validate_position`, `price_position`, `price_project`,
`explain_price_delta`, `list_catalog_options`, `get_blockers`, `simulate_ops`
y `preview_project_operations` leen autoridad real. La referencia debe estar
observada y pertenecer a la organización. Los costos confidenciales se excluyen
de las respuestas comerciales. Una venta desconocida conserva `net: null`,
causa y acción; el cero histórico de un borrador no acredita precio aplicado.
El motor cuantiza ambos netos a la moneda antes de restarlos, para que el Δ
coincida con los montos visibles. En lotes conserva la tarifa unitaria exacta
y cuantiza después de multiplicar por la cantidad, sin redondear cada unidad.

El verificador acepta medidas explícitas y cifras del contexto/herramientas
del turno. Una operación de incremento declara el delta pedido; el motor deriva
el resultado. Los números inventados se rechazan. La vista previa utiliza las
hojas y manillas de la evaluación, también para el diseño anterior; el dibujo
no deriva una hoja física por su cuenta.

La aclaración usa `clarify {question, options[]}`. Los chips copian alternativas
reales del catálogo y continúan el mismo trabajo. Si falta la altura del
antepecho, se pregunta sin ofrecer alturas inventadas. Un SKU que ya coincide
puede resolver la petición sin crear una modificación artificial.

## Configuración operativa

El prompt versionado está en `backend/ai_gateway/prompts/agent-v2.md`.
Los procesos leen `AI_AGENT_MAX_STEPS` (20, máximo 50),
`AI_AGENT_MAX_QUERIES` (6, máximo 12), `AI_AGENT_MAX_ROUNDS` (6, máximo 12)
y `AI_AGENT_TOTAL_TIMEOUT_S` (180, máximo 600). Un valor fuera de rango se
rechaza al iniciar; no se adopta silenciosamente. Los resultados guardan
rondas, consultas, herramientas, operaciones, límites y latencia por trabajo.
IA3 continúa la configuración del proveedor y sus estados de conexión.

La IA real se configura exclusivamente en el entorno del backend/worker;
las credenciales no cruzan al frontend ni al informe de evaluación.
