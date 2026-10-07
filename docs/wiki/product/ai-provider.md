---
type: concept
status: active
updated: 2026-10-07
volatility: medium
verified_ref: 383a013e8dacc8651165c3b321dfd92a96bb2f6a
sources:
  - backend/ai_gateway/providers.py
  - backend/ai_gateway/configuration.py
  - backend/ai_gateway/usage.py
  - supabase/migrations/20270106000000_ai_provider_operations.sql
  - docs/ai/IA3-ACEPTACION.md
  - docs/ai/IA3-CAPACIDADES.json
---

# Proveedor de IA y su autoridad

## Hechos verificados del repositorio

Las cuatro capacidades de diseño/agente/contexto/catálogo admiten rutas por
organización con OWNER y MFA. El modelo del entorno inicializa; el modelo
guardado por el dueño prevalece. API y frontend reciben disponibilidad de
credencial, estado y causa permitida; la clave y el endpoint siguen en servidor.
Una ruta guardada invalida su prueba anterior, y una prueba tardía no cambia
el estado de otra revisión. E03 aplica las operaciones sobre una copia y
valida dimensiones con el motor antes de mostrar Conectado.

MiMo real admite herramientas nativas y visión. El registro IA2 define
esquemas; assistant/tool se emparejan por identidad. Solo un rechazo explícito
de herramientas permite JSON estricto validado. Los reintentos transitorios
son como máximo dos y conservan la clave y un único plazo, también entre
direcciones públicas fijadas. DEBUG y pytest no activan el modo de prueba:
necesita flag y ruta explícitos, y la UI lo declara.

El PDF directo fue rechazado por MiMo. El transporte extrae texto literal o
renderiza páginas escaneadas de forma acotada para visión. Los cuatro oráculos
reales del transporte final pasan. Eso acredita lectura de entradas sintéticas;
no acredita un catálogo ni da confianza HIGH a cifras sin evidencia literal.
La revisión/publicación de [D01](catalog-authority.md) conserva su autoridad.

Presupuesto en créditos de solicitudes y mes de America/Santiago. Las reservas
concurrentes y los débitos históricos inmutables cuentan sin duplicación.
El registro físico separado conserva llamadas y eventos aunque revierta la
propuesta de dominio. Tokens sin medición completa y costo sin tarifa quedan
Sin dato. El dueño declara ambas tarifas USD por millón y el motor calcula
con Decimal; cada intercambio sella su tarifa. Crédito solicitado, débito de
billetera y costo monetario son magnitudes distintas.

El lock financiero `FOR NO KEY UPDATE` también gobierna el trigger de
billetera: la FK del registro independiente no provoca un deadlock con la
transacción externa. Un intercambio pagado no se repite con la misma clave
si el dominio revirtió. Los eventos son append-only y cada miembro solo ve
sus llamadas. Logs de trabajo/intercambio contienen metadatos permitidos,
sin prompts, respuestas, credenciales ni cabeceras.

El polling existente publica fases reales mediante commits separados y
guarda de lease. IA3 prepara la entrada de Orb; P17 continúa su rediseño.
La captura final observa Consultando proyecto. Calculando con el motor y
Preparando propuesta usan el progreso cuyo commit visible desde otra conexión se prueba
en integración; el recorrido corto no se presenta como evidencia visual de ambas.

## Medición y límites

La corrida final completa MiMo sobre `dd98ba5634f1f7ab0ccb653206e4bf06ea39742d` pasa 22/26:
editor 13/13, proyecto 6/8, planta 1/3
y general 2/2. Editor/proyecto 19/21. Conserva dominio,
auditoría y billetera sin cambios; el delta físico explícito es 56 llamadas
y 109 eventos. Véanse [aceptación](../../ai/IA3-ACEPTACION.md) y
[comparativa completa](../../ai/evals/2026-10-07-ia3-comparativa-final.md).

Una tarea resuelta requiere su oráculo de negocio; un transporte correcto
solo acredita la llamada. La corrida IA3 previa 19/26 y la IA2 histórica
21/26 se conservan como ejecuciones completas distintas. Ninguna selecciona
los mejores casos de otra. El catálogo es DEMO, sin certificación productiva.
La matriz de Ajustes/Trabajos/asistente conserva cero hallazgos nuevos y
el baseline histórico del asistente para P17.

## Intención del dueño y activación

La intención vigente es IA real configurada, sin cifras fabricadas y con
acciones consecuentes bajo clic humano. La tarifa comercial desconocida
no se sustituye por una cifra de investigación externa. La credencial se
carga en memoria de Django y del worker según
[AI_PROVIDERS](../../operations/AI_PROVIDERS.md) y
[ACTIVACION](../../operations/ACTIVACION.md).

La presencia de visión no equivale a certificación ni determina normas,
costos reales de fábrica o autoridad de CNC. [Riesgos](../quality/known-risks.md)
y [evaluaciones](../quality/ai-outcome-baseline.md) mantienen esas fronteras.
