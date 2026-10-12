# IA3 · corrida final completa de MiMo

Referencia ejecutada: `dd98ba5634f1f7ab0ccb653206e4bf06ea39742d`.
Modelo: `primalabs-ai/MiMo-V2.6-Pro`. Fecha: 2026-10-07T18:14:27.499028+00:00.
Resultado final: **22/26**; editor/proyecto **19/21**.
Estado persistente y fuente ejecutada sin cambios. Cada columna es una corrida completa.
La corrida previa IA3 se conserva; no se selecciona el mejor resultado por caso.

| Caso | IA2 histórica | IA3 previa | IA3 final | Rondas finales | Causa final |
| --- | --- | --- | --- | --- | --- |
| E01 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| E02 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| E03 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| E04 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| E05 | PASA | PASA | PASA | 1 | Todos los oráculos pasan |
| E06 | PASA | PASA | PASA | 1 | Todos los oráculos pasan |
| E07 | PASA | PASA | PASA | 4 | Todos los oráculos pasan |
| E08 | PASA | PASA | PASA | 1 | Todos los oráculos pasan |
| E09 | PASA | PASA | PASA | 1 | Todos los oráculos pasan |
| E10 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| E11 | PASA | PASA | PASA | 3 | Todos los oráculos pasan |
| E12 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| E13 | PASA | PASA | PASA | 3 | Todos los oráculos pasan |
| J01 | PASA | PASA | PASA | 3 | Todos los oráculos pasan |
| J02 | PASA | FALLA | PASA | 4 | Todos los oráculos pasan |
| J03 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| J04 | FALLA | FALLA | FALLA | 3 | contexto_insuficiente |
| J05 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| J06 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| J07 | PASA | PASA | PASA | 2 | Todos los oráculos pasan |
| J08 | FALLA | FALLA | FALLA | 3 | contexto_insuficiente |
| F01 | FALLA | FALLA | PASA | 1 | Todos los oráculos pasan |
| F02 | FALLA | FALLA | FALLA | 2 | resultado_incorrecto |
| F03 | FALLA | FALLA | FALLA | 1 | contexto_insuficiente |
| G01 | PASA | FALLA | PASA | 4 | Todos los oráculos pasan |
| G02 | PASA | PASA | PASA | 1 | Todos los oráculos pasan |

## Fallos preservados

- J04: contexto_insuficiente; sin error de transporte; oráculos: context_available, exact_priced_position.
- J08: contexto_insuficiente; sin error de transporte; oráculos: context_available, real_comparison.
- F02: resultado_incorrecto; sin error de transporte; oráculos: exact_cut_plan_bars.
- F03: contexto_insuficiente; sin error de transporte; oráculos: purchase_plan, context_available, real_shortages.

Delta físico final: `{"events": 109, "exchanges": 56}`.
El fixture es DEMO; ningún resultado acredita fabricación ni ejecuta acciones consecuentes.
[JSON completo](2026-10-07-ia3-mimo-final.json) · [Aceptación](../IA3-ACEPTACION.md)
