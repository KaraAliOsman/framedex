# IA2 · comparación completa con IA1

Proveedor real: `primalabs-ai/MiMo-V2.6-Pro`. Corrida IA2 completa del 2026-10-07T13:54:25.066833+00:00,
fuentes verificadas en `1711ebea2829a192b5e07ceb9a91bd1492e906d7`. Línea base IA1: `dd4ce1cca555d5e8fa1fa130c8b538c7c5c1aa43`.

IA1: **3/26**; IA2: **20/26**.
Editor y proyecto: **18/21 (85,71 %)**, meta ≥ 85 %.
Estado persistente y fuente ejecutada sin cambios. Una corrida completa; no se seleccionan mejores casos de otras corridas.

| Superficie | IA1 | IA2 |
| --- | --- | --- |
| editor | 1/13 | 13/13 |
| proyecto | 0/8 | 5/8 |
| planta | 1/3 | 0/3 |
| general | 1/2 | 2/2 |

| Caso | IA1 | IA2 | Causa IA2 |
| --- | --- | --- | --- |
| E01 | FALLA | PASA | — |
| E02 | FALLA | PASA | — |
| E03 | PASA | PASA | — |
| E04 | FALLA | PASA | — |
| E05 | FALLA | PASA | — |
| E06 | FALLA | PASA | — |
| E07 | FALLA | PASA | — |
| E08 | FALLA | PASA | — |
| E09 | FALLA | PASA | — |
| E10 | FALLA | PASA | — |
| E11 | FALLA | PASA | — |
| E12 | FALLA | PASA | — |
| E13 | FALLA | PASA | — |
| J01 | FALLA | FALLA | proveedor_error |
| J02 | FALLA | PASA | — |
| J03 | FALLA | PASA | — |
| J04 | FALLA | FALLA | contexto_insuficiente |
| J05 | FALLA | PASA | — |
| J06 | FALLA | PASA | — |
| J07 | FALLA | PASA | — |
| J08 | FALLA | FALLA | contexto_insuficiente |
| F01 | PASA | FALLA | resultado_incorrecto |
| F02 | FALLA | FALLA | resultado_incorrecto |
| F03 | FALLA | FALLA | contexto_insuficiente |
| G01 | FALLA | PASA | — |
| G02 | PASA | PASA | — |

| Categoría de fallo | IA1 | IA2 |
| --- | --- | --- |
| proveedor_no_configurado | 0 | 0 |
| proveedor_error | 0 | 1 |
| formato_invalido | 2 | 0 |
| op_no_soportada | 0 | 0 |
| op_rechazada_validador | 0 | 0 |
| grounding_rechazo | 3 | 0 |
| contexto_insuficiente | 5 | 3 |
| resultado_incorrecto | 12 | 2 |
| no_pidio_aclaracion | 1 | 0 |
| accion_consecuente_ejecutada | 0 | 0 |

## Límites y honestidad del resultado

J01 registra `proveedor_error` tras 63,88 s; la causa transportada está sanitizada y no se atribuye un status HTTP que no quedó observado. F01 promete consultar un listado truncado sin entregar la lista exacta; F02 pide identificar la revisión porque la OT solicitada no fue observada. Ninguno inventa cantidades técnicas.

J04 conserva la ausencia de precios aplicados; J08 no tiene revisiones emitidas A/B. El arnés no convierte precios indicativos en esa autoridad ni crea revisiones para ganar un caso.
F03 se ejecuta con estimador: la cobertura de compras exige otro rol. Los casos de planta que fallen conservan sus comprobaciones exactas de artefacto, listado y referencia observada.
Los 26 casos mantienen los oráculos estructurales de IA1. La equivalencia de apertura física conserva bisagras, sentido y papel de hoja; no equipara una puerta o una hoja pasiva con una ventana simple. Los lotes nuevos requieren aplicar la transacción real dentro del rollback antes de verificar el diseño persistido.
La UI pregunta por el antepecho cuando falta; la simulación determina la altura local. Las alternativas de vidrio se copian del catálogo y el Enter continúa el mismo trabajo. Ninguna acción consecuente se ejecuta por el agente.

Los JSON contienen la evidencia de cada comprobación y las rondas redactadas. La ausencia de fallo terminal de grounding no significa que todos los pedidos de planta estén resueltos.

[Informe IA2 completo](2026-10-07-ia2-mimo.json) · [Línea base IA1](2026-10-05-mimo.json) · [Aceptación de navegador](../../redesign/captures/operaciones-herramientas/aceptacion.md)
