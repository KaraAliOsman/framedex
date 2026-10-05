# IA1 · línea base por resultado

La IA real está conectada. Estos resultados miden si un pedido consigue el estado esperado; una respuesta convincente o un job `SUCCEEDED` no acreditan una edición. IA1 conserva los fallos y no cambia los prompts, el vocabulario ni el proveedor.

La referencia ejecutada del arnés está sellada en cada JSON. Fecha: 05-10-2026. El catálogo y las dos organizaciones son **DEMO**; esta evidencia no habilita fabricación.

## Ejecutar

Prepara las dependencias con `pip install -r requirements-dev.txt` y `npm ci --prefix frontend`. Inicia el stack local según `.agents/skills/testing-framedex/SKILL.md`, prepara `scripts/dev_fixture.py` y carga las variables locales en memoria antes del proceso. No imprimas el entorno. `DJANGO_DEBUG=true` y una conexión PostgreSQL de localhost son obligatorios. Mantén el fixture sin otras escrituras durante la corrida.

Desde la raíz, con el entorno ya cargado:

```text
python scripts/ai_evals.py --provider MOCK --out docs/ai/evals/mock-latest.json
python scripts/ai_evals.py --provider configurado --out docs/ai/evals/real-latest.json
make ai-evals
```

La interfaz de módulo pedida también funciona desde `backend/` (motor instalado por `requirements-dev.txt`):

```text
python -m ai_gateway.evals.run --provider MOCK --out ../docs/ai/evals/mock-latest.json
python -m ai_gateway.evals.run --provider configurado --out ../docs/ai/evals/real-latest.json
```

`--case E03` sirve para diagnosticar el arnés; la aceptación usa el comando sin filtro. El proceso devuelve 0 cuando los 26 casos quedaron registrados y el aislamiento pasó, aunque la línea base de producto falle. Devuelve 1 si falla el arnés o cambia el estado persistente. La falta de credencial del proveedor queda clasificada, nunca se sustituye por MOCK; un stack, ruta o login local no preparado detiene el comando antes de evaluar.

## Aislamiento y vara

Cada caso carga el proyecto real de 12 posiciones, envía **POST `/api/v1/ai/agent/`**, ejecuta el handler registrado **`ai_gateway.handlers.ai_agent_run`** y lee **GET `/api/v1/ai/jobs/{id}/`** con un JWT real y el rol Estimador. El submit, los serializadores, RLS, el contexto, el agente, la llamada al proveedor y la auditoría son los mismos de la UI. El único cambio de transporte es ejecutar el handler en la conexión de la transacción: el worker externo no puede ver una cola sin commit.

La transacción exterior siempre hace rollback, también de posición, route, wallet, job y audit. La ruta cambia temporalmente solo dentro de esa transacción para elegir MOCK o la IA ya configurada. Un snapshot por tabla detecta escrituras de dominio durante el turno y otro comprueba el estado persistente al cerrar toda la suite. No ejecutes la suite al mismo tiempo que escrituras de UI: la guarda detecta también esas escrituras ajenas.

Las propuestas se aplican a una copia en Node con **`applyDesignOps` y `ASSEMBLY_COMMANDS`**, exactamente el registro del canvas. La copia se calcula con `/engine/assembly/calculate/`; no se guarda ni se confirma ningún artefacto. E02 empieza con dos bahías fijas; E09 con el resultado estructural esperado de E02; E12 con una TILT_TURN_LEFT. El resto del editor parte de un marco fijo de 1500 × 1200 mm. Esos son inputs explícitos del caso, no resultados calculados por un LLM.

Los oráculos de edición comparan dimensiones Decimal exactas, bahías dentro de un solo marco, ejes globales de montantes/travesaños, orientación y SKU reales. E13 acepta cualquiera de las dos formas del árbol binario si sus ejes son 500 y 1000 mm y sus aperturas son las correctas. J03 admite cuatro copias nuevas o una propuesta tipada de cantidad +4. Los pedidos de lectura/refusal comprueban además la evidencia o la pregunta necesarias; no se evalúan por similitud textual ni con otro LLM.

El informe conserva la petición original y la resuelta, producto antes/después, resultado del motor, ops propuestas/rechazadas, motivo, rondas y JSON bruto del proveedor, correcciones de grounding, latencia del caso y del proveedor, tokenización y categoría. Los datos y nombres son sintéticos. No se almacena JWT, cabecera de autorización ni variable de entorno.

## Tasas por vista

| Vista | MOCK | MiMo real |
|---|---|---|
| Editor | 0/13 · 0,0 % | 3/13 · 23,1 % |
| Proyecto | 0/8 · 0,0 % | 0/8 · 0,0 % |
| Producción / Compras | 0/3 · 0,0 % | 1/3 · 33,3 % |
| General | 0/2 · 0,0 % | 1/2 · 50,0 % |
| Total | 0/26 · 0,0 % | 5/26 · 19,2 % |

## Por caso

| Caso | MOCK | MiMo real | Rondas MiMo | Evidencia del resultado MiMo |
|---|---|---|---|---|
| E01 | resultado_incorrecto | resultado_incorrecto | 1 | one_frame, mullion_axes |
| E02 | resultado_incorrecto | grounding_rechazo | 2 | ai_agent_ungrounded |
| E03 | grounding_rechazo | PASA | 1 | Todos los oráculos pasan |
| E04 | resultado_incorrecto | resultado_incorrecto | 1 | one_frame, horizontal_transom, top_bay_height, upper_fixed |
| E05 | resultado_incorrecto | PASA | 4 | Todos los oráculos pasan |
| E06 | resultado_incorrecto | PASA | 4 | Todos los oráculos pasan |
| E07 | resultado_incorrecto | formato_invalido | 1 | incompatibility_explained |
| E08 | no_pidio_aclaracion | resultado_incorrecto | 3 | installation_height_question |
| E09 | resultado_incorrecto | resultado_incorrecto | 4 | exact_engine_weight |
| E10 | resultado_incorrecto | resultado_incorrecto | 3 | exact_backend_blockers |
| E11 | grounding_rechazo | grounding_rechazo | 2 | ai_agent_ungrounded |
| E12 | resultado_incorrecto | formato_invalido | 1 | hinges_and_handle |
| E13 | resultado_incorrecto | resultado_incorrecto | 1 | one_frame, mullion_axes |
| J01 | resultado_incorrecto | resultado_incorrecto | 3 | exact_second_floor_targets, real_glass_ops |
| J02 | op_rechazada_validador | resultado_incorrecto | 2 | new_position_or_incompatibility |
| J03 | resultado_incorrecto | resultado_incorrecto | 1 | four_exact_copies_or_quantity_plus_four |
| J04 | contexto_insuficiente | contexto_insuficiente | 3 | context_available, exact_priced_position |
| J05 | resultado_incorrecto | resultado_incorrecto | 2 | discount_draft, human_approval |
| J06 | resultado_incorrecto | resultado_incorrecto | 3 | preparation_deeplink |
| J07 | contexto_insuficiente | contexto_insuficiente | 3 | context_available |
| J08 | contexto_insuficiente | contexto_insuficiente | 2 | context_available, real_comparison |
| F01 | resultado_incorrecto | PASA | 3 | Todos los oráculos pasan |
| F02 | contexto_insuficiente | contexto_insuficiente | 1 | context_available, exact_cut_plan_bars |
| F03 | contexto_insuficiente | contexto_insuficiente | 3 | purchase_plan, context_available, real_shortages |
| G01 | resultado_incorrecto | resultado_incorrecto | 3 | draft_before_calculation |
| G02 | resultado_incorrecto | PASA | 3 | Todos los oráculos pasan |

## Taxonomía de causa principal

Cada caso fallido tiene una causa principal. Los rechazos internos y correcciones se conservan aparte, de modo que una respuesta corregida que pasa no desaparece del diagnóstico de grounding.

| Causa | MOCK | MiMo real |
|---|---|---|
| proveedor_no_configurado | 0 | 0 |
| proveedor_error | 0 | 0 |
| formato_invalido | 0 | 2 |
| op_no_soportada | 0 | 0 |
| op_rechazada_validador | 1 | 0 |
| grounding_rechazo | 2 | 2 |
| contexto_insuficiente | 5 | 5 |
| resultado_incorrecto | 17 | 12 |
| no_pidio_aclaracion | 1 | 0 |
| accion_consecuente_ejecutada | 0 | 0 |

MiMo: 6 rondas correctivas de grounding; 2 fallos terminales de grounding.

## Cinco causas raíz, por impacto potencial observado

El orden sigue cuántas capacidades impide la causa. Los casos pueden tener causas contribuyentes compartidas; estos grupos no se suman como si fueran categorías exclusivas.

1. **Vocabulario limitado al módulo, sin edición de bahías ni posiciones.** `backend/ai_gateway/agent.py:175` y `backend/projects/design_assist.py:927` enumeran/cierran el contrato. E01/E02/E04/E12/E13 necesitan splits o una apertura dirigida a una bahía; J02/J03 necesitan crear/duplicar posiciones. Un conjunto de módulos acoplados no equivale a dos hojas en un mismo marco. E07 tampoco dispone de una validación de compatibilidad por sistema en ese contrato (`OPENINGS`, `design_assist.py:23`). IA2 debe compartir un registro tipado de dominio con el canvas.

2. **Contexto sin la autoridad necesaria para responder.** `backend/ai_gateway/context.py:437` omite precios individuales; `:529` omite validación/peso completo y catálogo de vidrio; `:965` omite el plan de barras. En J01 el agente debe obtener un SKU por consultas y dirigirse por ubicación; E05/E06 deben conocer recetas; E09/E10/J04/J07/J08/F02/F03 necesitan autoridad que la proyección o el fixture no entregan. `agent.py:876` solo anuncia disponibilidad de ops y `:879` una descripción parcial de campos. IA2/IA3 deben aportar proyecciones verificables, sin deducir datos ausentes.

3. **Formato de operación ambiguo para el modelo.** `agent.py:173`/`:175` enumera campos pero no ofrece un ejemplo completo de op con su discriminador; el validador exige `op` (`design_assist.py:523`). En corridas reales MiMo devolvió objetos con `kind` o `name`: son rechazados como `formato_invalido`, aunque la frase diga que ajustó medidas. El artefacto de cada ronda permite verificar los campos exactos; IA2 debe hacer único y explícito ese contrato.

4. **Grounding literal trata cifras derivadas como citas no autorizadas.** `agent.py:1005` puede rechazar todo el turno; `:1039` usa únicamente los valores declarados en la meta para las ops. El +200 mm de E11 deriva el ancho 1700 del diseño, pero ese número no está literal en la meta ni en el contexto anterior. `design_assist.py:74` declara la misma restricción. IA2 debe representar la derivación como operación tipada que ejecuta el motor, sin relajar la protección de cifras inventadas.

5. **La finalización del job no acredita un resultado aplicado.** `agent.py:1279` decide `SUCCEEDED` si no quedaron preguntas ni pasos aprobables, aun cuando todos los pasos fueron rechazados. `frontend/src/features/assistant/AgentBody.tsx:842` y `AssistantWorkspacePage.tsx:856` muestran el job como trabajo completado. Las capturas reproducen la explicación de medidas con `formato_invalido` y ninguna escritura de producto. IA3 debe mostrar el rechazo y el estado de aplicación reales; el arnés ya exige el estado estructural, no ese badge.

## Límites verificados del fixture

- El proyecto casa tiene 12 posiciones y sigue en borrador sin precio aplicado. Los `0.00` de precio persistidos no son cotizaciones del motor: J04 no permite elegir una posición “más cara” a partir de esos ceros.
- El catálogo actual declara VIDRIO-BASE como `4 Float Incoloro`; las posiciones históricas llevan una receta de termopanel 4-16-4. No se certifica ni se corrige esa contradicción en IA1. E05 admite solo el SKU de 4-12-4 real o alternativas reales; E06 nunca inventa laminado. D01/D02 corrigen la autoridad de catálogo.
- DEMO_60 admite aperturas mixtas en el editor actual. La base practicable exclusiva exigida por E07 aún carece de catálogo separado; ese defecto de compatibilidad se conserva en el resultado y se entrega a D01/D03.
- No hay REV-A/REV-B emitidas ni OT con plan de corte en este fixture. J08/F02 quedan en contexto insuficiente: no se inventan ni se sellan datos de fabricación DEMO para hacerlos pasar. F01 sí puede comprobar la lista vacía real, pero eso no acredita diagnóstico de una OT bloqueada.
- El Estimador no puede verificar la cobertura de compras; la proyección lo declara. F03 no debe acreditar un plan inventado. Los oráculos conservan esa falta de permiso/contexto; las siguientes pruebas de planta deben usar el rol de taller y autoridad documental real.
- `/documents/.../inputs/` entrega preparación, pero todavía no un contrato exhaustivo `missing`. J07 exige una lista exacta y el arnés registra esa carencia de backend.

MOCK es reproducible: se repitieron los 26 casos y se compararon sus verdictos, checks, rejections y estructura. Las identidades sintéticas de módulos, las fechas y la latencia no son el oráculo. MiMo con temperatura 0 sigue siendo un servicio externo: las corridas exploratorias de E03 variaron entre propuesta válida y formato inválido. Se conserva una corrida completa fechada, sin seleccionar el mejor intento ni prometer determinismo de red/modelo.

## Evidencia y aceptación

- [MOCK completo](2026-10-05-mock.json) y [MiMo completo](2026-10-05-mimo.json).
- [Aceptación, rúbrica y capturas](../../redesign/captures/diagnostico-evals/aceptacion.md).
- 20 tests de oráculos/observación verifican exactitud, orientación, divisores, rechazo de SKU inventado, aclaración, preparación sin escritura y taxonomía.
- Se corrigió una omisión de redacción de logs del gate local: las filas S3 «Secret Key» y «Access Key» del CLI también quedan ocultas. El test usa valores sintéticos; ninguna credencial se guarda en el informe.
- El arnés no introduce pantalla ni modifica API pública; no hay cambios de OpenAPI/orval. No se cambiaron prompts, operaciones, proveedores ni fórmulas. No hay integración nueva en sandbox de producto ni decisión comercial configurable.
- La corrida inicial concurrente con escrituras manuales de UI fue rechazada por la guarda de persistencia y no se acredita. Los JSON entregados son las corridas aisladas finales con `persistent_state_unchanged=true`.
