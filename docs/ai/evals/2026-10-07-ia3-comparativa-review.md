# IA3 · evaluación completa tras la revisión del PR

Referencia ejecutada: `041cb622836c745897c04e52a354d10bbf16a8b4`. Fecha: 2026-10-07T19:02:40.439042+00:00.
Resultado: **22/26**; editor/proyecto **19/21**. Fuente y estado persistente sin cambios.
Cada columna corresponde a una corrida completa. La modificación posterior solo adapta PDF y el mensaje de guardado; no cambia el bucle del agente.

| Caso | IA2 histórica | IA3 anterior | IA3 tras revisión | Rondas | Causa |
| --- | --- | --- | --- | --- | --- |
| E01 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| E02 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| E03 | PASA | PASA | PASA | 3 | Todos los oráculos pasan |
| E04 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| E05 | PASA | PASA | PASA | 1 | Todos los oráculos pasan |
| E06 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| E07 | PASA | PASA | PASA | 1 | Todos los oráculos pasan |
| E08 | PASA | PASA | PASA | 1 | Todos los oráculos pasan |
| E09 | PASA | PASA | PASA | 1 | Todos los oráculos pasan |
| E10 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| E11 | PASA | PASA | PASA | 3 | Todos los oráculos pasan |
| E12 | PASA | PASA | PASA | 4 | Todos los oráculos pasan |
| E13 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| J01 | PASA | PASA | PASA | 3 | Todos los oráculos pasan |
| J02 | PASA | PASA | PASA | 3 | Todos los oráculos pasan |
| J03 | PASA | PASA | PASA | 3 | Todos los oráculos pasan |
| J04 | FALLA | FALLA | FALLA | 3 | contexto_insuficiente |
| J05 | PASA | PASA | PASA | 1 | Todos los oráculos pasan |
| J06 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| J07 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| J08 | FALLA | FALLA | FALLA | 1 | contexto_insuficiente |
| F01 | FALLA | PASA | PASA | 2 | Todos los oráculos pasan |
| F02 | FALLA | FALLA | FALLA | 2 | resultado_incorrecto |
| F03 | FALLA | FALLA | FALLA | 1 | contexto_insuficiente |
| G01 | PASA | PASA | PASA | 3 | Todos los oráculos pasan |
| G02 | PASA | PASA | PASA | 1 | Todos los oráculos pasan |

## Fallos conservados

- J04: contexto_insuficiente; oráculos: context_available, exact_priced_position.
- J08: contexto_insuficiente; oráculos: context_available, real_comparison.
- F02: resultado_incorrecto; oráculos: exact_cut_plan_bars.
- F03: contexto_insuficiente; oráculos: purchase_plan, context_available, real_shortages.

Delta físico: `{"events": 104, "exchanges": 53}`.
Cero fallos de proveedor y cero acciones consecuentes ejecutadas. El catálogo DEMO no acredita fabricación.
[JSON completo](2026-10-07-ia3-mimo-review.json) · [Aceptación](../IA3-ACEPTACION.md)
