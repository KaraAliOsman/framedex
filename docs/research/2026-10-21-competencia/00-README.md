# DEKOPEN 2 · Paquete de dirección (21-10-2026)

Preparado por Claude como director de producto, diseño y tecnología. **No
contiene código de aplicación**: contiene la investigación, las decisiones, los
diseños y los prompts para que GPT (Codex) construya DEKOPEN 2 de punta a punta.

## Qué hay y en qué orden leerlo

| # | Documento | Para qué sirve |
|---|---|---|
| 1 | [Auditoría de DEKOPEN](01-auditoria-dekopen.md) | Qué está mal, medido; si los cálculos están bien; qué conservar y qué retirar |
| 2 | [Informe de competencia](reports/Competencia%20en%20software%20de%20ventanas.md) | 30+ productos analizados: cómo funcionan, cuánto cuestan, dónde fallan, matriz por capacidad |
| 3 | [Estrategia de producto](02-estrategia-producto.md) | Qué es DEKOPEN 2, para quién, por qué gana, precio propuesto, alcance y métricas |
| 4 | [Catálogo y cálculo](03-catalogo-y-calculo.md) | El núcleo: serie real cotizable con valores sugeridos y ventana de prueba |
| 5 | [Experiencia y diseño](04-experiencia-y-diseno.md) | Arquitectura, flujos, pantallas, sistema de diseño, glosario y decisiones pendientes |
| 6 | [Agente de IA](05-agente-ia.md) | Las 12 automatizaciones, autonomía, contrato técnico y métricas |
| 7 | [Mockups](mockups/) · [lienzo en línea](https://claude.ai/artifact/VsEy8i4sHe8zgZhEQK5G9u) | 9 pantallas: obra, Hoy, Obras, ficha de serie, ventana de prueba, envío, agente, taller, portal |
| 8 | [Prompts para GPT](prompts/README.md) | Contexto maestro + 11 fases + bucle continuo |
| — | [Notas de investigación](research_notes/Competencia%20en%20software%20de%20ventanas/) · [Evidencia REA](evidencia/README.md) | Fuentes con URL y capturas con ID de evidencia |

## La tesis en tres líneas

1. Se gana con **el catálogo real y los precios del taller**, no con la interfaz:
   DEKOPEN debe cotizar Proline PRO6004 con precios propios en minutos.
2. **Valores sugeridos visibles en lugar de bloqueos**, con una ventana de prueba
   que convierte cada serie verificada en un caso dorado propio.
3. Un **agente que hace el trabajo** (de WhatsApp o plano a cotización enviada y
   orden de taller) con cifras del motor y clic humano para lo externo.

## Decisiones que necesitan al dueño

Ver [Experiencia y diseño §6](04-experiencia-y-diseno.md#6-decisiones-que-necesitan-al-dueño):
vista única de obra (frente a Mesa + Estudio), panel lateral del agente (frente
al popup) y precios comerciales. Los prompts implementan las propuestas detrás
de banderas para no bloquear a GPT.

## Lo que la evidencia no cubre

Reseñas independientes de usuarios, precios de la mayoría de suites europeas,
cuota de mercado en Chile y la lista real de series de NuveraPRO (requiere su
prueba de 15 días, que debe abrir el dueño). Detalle en el informe, sección
«Lo que la evidencia no permite afirmar todavía».
