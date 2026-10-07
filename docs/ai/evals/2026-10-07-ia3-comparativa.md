# IA3 · evaluación completa con MiMo real

Modelo: `primalabs-ai/MiMo-V2.6-Pro`. Referencia ejecutada: `a15abd2c6b658dc390b8f770d10d73f22f011da5`.
Fecha: 2026-10-07T17:59:09.164240+00:00. Resultado: **19/26**.
Estado persistente de dominio, auditoría y billetera sin cambios; fuente ejecutada sin cambios.
Una corrida completa, sin seleccionar casos de otras corridas. Los intercambios físicos pagados se registran por separado.

| Caso | IA2 histórica | IA3 | Rondas IA3 | Causa IA3 |
| --- | --- | --- | --- | --- |
| E01 | PASA | PASA | 2 | Todos los oráculos pasan |
| E02 | PASA | PASA | 2 | Todos los oráculos pasan |
| E03 | PASA | PASA | 2 | Todos los oráculos pasan |
| E04 | PASA | PASA | 2 | Todos los oráculos pasan |
| E05 | PASA | PASA | 1 | Todos los oráculos pasan |
| E06 | PASA | PASA | 1 | Todos los oráculos pasan |
| E07 | PASA | PASA | 1 | Todos los oráculos pasan |
| E08 | PASA | PASA | 1 | Todos los oráculos pasan |
| E09 | PASA | PASA | 1 | Todos los oráculos pasan |
| E10 | PASA | PASA | 2 | Todos los oráculos pasan |
| E11 | PASA | PASA | 3 | Todos los oráculos pasan |
| E12 | PASA | PASA | 2 | Todos los oráculos pasan |
| E13 | PASA | PASA | 2 | Todos los oráculos pasan |
| J01 | PASA | PASA | 3 | Todos los oráculos pasan |
| J02 | PASA | FALLA | 6 | op_rechazada_validador |
| J03 | PASA | PASA | 2 | Todos los oráculos pasan |
| J04 | FALLA | FALLA | 2 | contexto_insuficiente |
| J05 | PASA | PASA | 2 | Todos los oráculos pasan |
| J06 | PASA | PASA | 2 | Todos los oráculos pasan |
| J07 | PASA | PASA | 2 | Todos los oráculos pasan |
| J08 | FALLA | FALLA | 1 | contexto_insuficiente |
| F01 | FALLA | FALLA | 1 | resultado_incorrecto |
| F02 | FALLA | FALLA | 2 | resultado_incorrecto |
| F03 | FALLA | FALLA | 1 | contexto_insuficiente |
| G01 | PASA | FALLA | 3 | grounding_rechazo |
| G02 | PASA | PASA | 1 | Todos los oráculos pasan |

## Aislamiento y límites

Delta físico observado: `{"events": 99, "exchanges": 50}`.
Las tablas físicas nuevas no contienen prompts ni respuestas. Los snapshots originales de dominio, auditoría y billetera mantienen sus comprobaciones.
Las series y el fixture son DEMO; la medida es resultado de oráculos exactos del motor y no autoriza fabricación.
IA2 histórica conserva su resultado 21/26 y editor/proyecto 19/21. IA3 mide su propio transporte nativo y conserva cada fallo.

[Informe completo](2026-10-07-ia3-mimo.json) · [Aceptación](../IA3-ACEPTACION.md)
