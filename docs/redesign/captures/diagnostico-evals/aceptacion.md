# IA1 · aceptación del diagnóstico

IA1 entrega una medición de resultado y su línea base, sin cambiar el comportamiento de la IA. La referencia ejecutada, la configuración de proveedor pública y cada resultado están en [los JSON y el informe](../../../ai/evals/README.md). El SHA del squash se registra al integrar.

La corrida final completa sobre `4e924c68440a6f87ab5464ce1f2f503f607a3208` cumple 6/26 pedidos con MiMo (23,1 %) y 0/26 con MOCK. F01 registra el HTTP 429 real. Ambas suites verifican persistencia intacta y fuentes intactas; MOCK repite exactamente todos los oráculos, estructuras, rechazos y hechos de autoridad.

## Recorridos y aislamiento

- 26 pedidos del dueño por POST agente → handler real → GET trabajo, con JWT del fixture y PostgreSQL/RLS. MOCK y MiMo usan los proveedores existentes.
- Las operaciones aceptadas se aplican con el registro real del canvas a una copia y se calculan con el motor; las medidas se comparan exactamente como Decimal. El producto/proyecto se conserva sin commit.
- El oráculo de edición exige una respuesta válida del motor, separando geometría inválida de autoridad de fabricación incompleta. Las negativas de compatibilidad se contrastan con el sistema seleccionado; J03 exige destino en dormitorios y J05 usa la fracción comercial 0.05. Los precios aplicados y planes de corte existentes se leen de su autoridad, sin constantes que los mantengan ausentes en corridas futuras.
- La referencia de fuente se captura antes de medir; el código debe estar commiteado y se verifica que no cambió durante la corrida. La reconstrucción del stack comprobó que el proyecto se descubre por CASA_LOMAS aun cuando su UUID cambia. Las respuestas y el informe redactan campos de credencial, JWT y valores privados del entorno sin alterar lo que recibe el agente.
- Rollback del caso, de route, audit, wallet y jobs. Snapshot de tablas de tenant durante la propuesta y de persistencia al cerrar la suite. Una corrida exploratoria concurrente con jobs manuales fue rechazada por esa guarda y no es la línea base entregada.
- Navegador Chromium: Proyectos → proyecto casa → editor → Orb → Agente → solicitud real E03 → trabajo del asistente. Los recorridos finales se inspeccionaron en 1440×900, 1280×800 y 1024×768, claro y oscuro. Se comprobaron cero escrituras de dominio; el POST al motor calcula y no guarda. El job puede decir COMPLETADO aun con rechazo de ops: es un hallazgo, no un resultado acreditado.
- `ux:capture`: ocho combinaciones del asistente, incluyendo 390×844, antes y después. Cero desbordes en ambas corridas. No se modifica ninguna ruta, componente, CSS o API pública.

## Capturas

| Recorrido | Claro | Oscuro |
|---|---|---|
| Editor y panel contextual | [1440](flujo/editor-light-1440-antes.png) | [1440](flujo/editor-dark-1440-antes.png) |
| Trabajo con resultado real | [1440](flujo/trabajo-light-1440-despues.png) | [1440](flujo/trabajo-dark-1440-despues.png) |
| Trabajo, ancho intermedio | [1280](flujo/trabajo-light-1280-despues.png) | [1280](flujo/trabajo-dark-1280-despues.png) |
| Trabajo, ancho mínimo escritorio | [1024](flujo/trabajo-light-1024-despues.png) | [1024](flujo/trabajo-dark-1024-despues.png) |

[Resultados del recorrido](flujo/resultados.json), [ux:capture antes](antes/report.json) y [después](despues/report.json).

Los detectores conservan tres tipos de deuda heredada del asistente: tamaño de fuente, radio y contraste. Antes: 88/32/10 instancias; después: 112/80/10. El incremento de instancias corresponde a los jobs manuales agregados al fixture, cuyos badges repiten los mismos estilos heredados; no se introducen tipos ni estilos nuevos. IA1 no acredita el rediseño de esta UI; IA3 y P17 deben corregirlo. Las capturas del trabajo muestran además el enum `formato_invalido` y texto que dice haber ajustado medidas sin aplicarlas. Se conserva como evidencia de diagnóstico.

## Pase editorial: alcance del arnés

La rúbrica revisa lo que IA1 añade: CLI, datos de evaluación, informe y trazabilidad. PASA no acredita el asistente heredado, que no se modifica por el contrato de diagnóstico. Los controles existentes solo se recorren para observar sus resultados. No se agrega una pantalla para maquillar el fallo de la IA.

| Ítem | Resultado | Evidencia dentro del alcance |
|---|---|---|
| R1 | PASA | Valores técnicos exactos como strings Decimal; formatos máquina explícitos en JSON, tasas es-CL en el informe. |
| R2 | PASA | No se agrega cromo ni radio. |
| R3 | PASA | Informe tabular con jerarquía de evidencia; sin tarjetas. |
| R4 | PASA | No se agrega color ni CTA. |
| R5 | PASA | No se modifica la paleta. |
| R6 | PASA | Peticiones originales y diagnóstico en español; identificadores técnicos en datos del arnés. |
| R7 | PASA | Informe permite comparar por vista/caso sin una nueva pantalla. |
| R8 | PASA | Todos los fallos quedan clasificados y con causa; no se omite un caso por error. |
| R9 | PASA | El lienzo se conserva; no se agrega una superficie de producto. |
| R10 | PASA | No cambia la selección del canvas. |
| R11 | PASA | Oráculos comprueban bisagras/manilla, bahías y carriles sin dibujar aperturas falsas. |
| R12 | PASA | Comando único ejecutable; no se añade interacción sin teclado. |
| R13 | PASA | No se añade movimiento; recorrido en reduce-motion. |
| R14 | PASA | Una ejecución produce todos los casos; no se agrega botón. |
| R15 | PASA | Fuente motor/backend, estado desconocido separado de cero y snapshots de autoridad. |
| R16 | PASA | No se añade degradado, blur, brillo ni morado. |
| R17 | PASA | Recorridos de escritorio sin overflow; ningún layout nuevo. |
| R18 | PASA | CLI real, ambos proveedores reales, sin TODO ni ruta alterna de producto. |
| R19 | PASA | Se conserva el Orb; se demuestra la diferencia entre estado del job y aplicación. |
| R20 | PASA | Simulación de comandos del canvas calculada por el motor; la vara detecta propuestas que solo afirman un cambio. |

Primera ronda: se eliminó el criterio “job exitoso = pedido cumplido”, la suposición de precios a partir de ceros del borrador y la aplicación independiente de operaciones que habría duplicado el canvas. Se sustituyeron por grafo exacto, autoridad explícita y registro compartido.

Segunda ronda: se fortaleció la detección de escrituras por tabla y rollback final; se hizo exacta la orientación y la comparación de ejes globales en árboles binarios equivalentes; se separaron fallos de formato, grounding y contexto para no atribuirlos todos al proveedor. Cada mejora tiene tests o evidencia de la corrida local.

Momento de firma preservado: F8, Orb conectado al job observado. Idea §8 instrumentada: propuesta → simulación real → resultado estructural, con preguntas y rechazos medidos. El asistente aún debe implementar el diff aplicable en IA2/IA3; IA1 aporta la prueba que distinguirá esa implementación de una frase.

## Verificación y límites

Los gates locales `make lint`, `make typecheck`, `make test` y `make build` pasaron: motor 472 PASA + 2 xfail, backend 1097 PASA, frontend 697 PASA. La compilación no cambia OpenAPI/orval y se conserva el chequeo de reproducibilidad. Los oráculos tienen 39 tests y el test PostgreSQL del observador pasó sobre el stack real, incluida la base recién reconstruida. El Database Gate completo pasó: 921 aserciones pgTAP, integración con RLS, los 11 recorridos Playwright y compatibilidad/migraciones pobladas en PostgreSQL 16. El teardown dejó libres los puertos y detuvo Supabase. Tras las correcciones de revisión se repitieron backend, oráculos, observador y ambas suites de evaluación; los cinco tests de logs también pasaron. Los cuatro checks de GitHub se registran al cerrar el PR.

No hecho, por alcance: no se arreglan prompts, registro de ops, proveedor, fixture con autoridad de fabricación ni UI del asistente. No se inventan REV/OT para hacer pasar casos cuyo contexto falta. No hay nuevas decisiones comerciales ni integraciones externas. El arnés es exclusivo de DEBUG y PostgreSQL local; no se habilita como endpoint de producción.
