# DEKOPEN — dirección final y encargo para Claude

18-10-2026 · decisión de producto del dueño + especificación de implementación. **El rediseño todavía no está implementado ni aceptado visualmente.**

DEKOPEN será un cotizador y sistema de trabajo completo que se puede usar de principio a fin sin IA. Tendrá dos vistas del mismo trabajo: **Mesa de obra**, recomendada al empezar, y **Estudio**, elegible por cada usuario. El copiloto será un **popup global opcional**, cerrado inicialmente, que ejecuta tareas cuando la persona se las delega. No ocupa permanentemente la cotización ni reemplaza el inspector.

Esta entrega integra tres revisiones especializadas: producto/editor; copiloto/planes; diseño/documentos/operación. Parte de la [investigación de quince familias](../2026-10-18-revision-profunda/README.md), su rúbrica de 270 casillas, 176 URLs y 28 imágenes. No repite ese trabajo como si fueran nuevas sesiones de los competidores. La evidencia pública y el análisis REA conservan sus límites originales.

La aclaración posterior añade tres contratos: planes/créditos, referencias profesionales y personaje Grok Bot. **Todos los planes con IA usarán MiMo hasta que el dueño lo cambie; se diferencian por consumo disponible y extras profesionales concretos.** Los importes «anual 30/49/99/149» son una referencia sin tarifa aprobada. DeepSeek Flash 4.1 queda como candidato futuro mencionado por el dueño, sin configurar ni validar. La fidelidad a Grok Bot se centra en su personaje animado; la conversación conserva el diseño propio de DEKOPEN.

**Alcance final aclarado:** Claude debe entregar la versión completa y ejecutable, candidata definitiva para la revisión del dueño. Solo quedarán pendientes las conexiones/configuración finales de producción de **Railway, Supabase y pagos**. El código, las migraciones, la persistencia, los permisos, el copiloto y los créditos pertenecen al desarrollo completo, junto con los archivos y pasos de conexión. Tras la aprobación del dueño se conectan los servicios finales y se realizan las pruebas de lanzamiento antes de publicar. La campaña técnica 07 sigue al final del desarrollo y precede a esa revisión; no hay aprobaciones entre 01–06.

## Abrir primero

1. [Dirección final](direccion-final.md): decisiones resueltas, experiencia manual, alcance y prioridades.
2. [Prompt maestro para Claude](prompt-maestro.md): encargo listo para copiar; ejecuta los siete prompts en orden, sin pedir otra elección de diseño.
3. [Criterios de entrega](criterios-de-entrega.md): qué significa terminado, rúbrica y pruebas al final.

## Contratos por área

| Contrato | Responsabilidad |
|---|---|
| [Producto y dos vistas](01-producto-y-dos-vistas.md) | Mesa/Estudio, misma identidad, navegación y edición manual. |
| [Diseño, documentos y operación](02-diseno-y-referencias.md) | Anatomía de superficies, lenguaje visual, documentos, materiales y taller. |
| [Copiloto y planes](03-copiloto-y-planes.md) | Popup, Chat/Trabajo, autonomía, historial, ejecución y valor de los planes. |
| [Planes, créditos y límites](04-planes-creditos-y-limites.md) | PRD-03 contrastado con código, cuotas proporcionales, consumo, reservas y compatibilidad comercial. |
| [Referencias profesionales](05-referencias-profesionales.md) | Veinte referencias trazables: Apple, Pentagram, Adobe, Shapr3D, IBM y sector; decisión, razón y límite. |
| [Personaje y movimiento](06-grok-bot-personaje-y-movimiento.md) | Referencia fiel a Grok Bot, SVG/estados, interacción y análisis REA estático parcial, con cuatro capturas seleccionadas. |

La ampliación explícita posterior incorpora **documentos, imágenes y demás archivos compatibles al popup**, en Chat/Trabajo. El [contrato 03](03-copiloto-y-planes.md#adjuntos-multimodales--ampliación-explícita-del-dueño), el prompt 05 y los casos A15–A17 concretan formatos, varios adjuntos, persistencia, fuentes y lectura parcial. Las tres [recomendaciones adicionales de innovación](../2026-10-18-innovacion/06-archivos-y-mejoras-con-sentido.md) se distinguen del requisito ya incorporado.

## Orden de implementación

| Paso | Prompt | Resultado que construye |
|---|---|---|
| 01 | [Fundamentos](prompts/01-fundamentos.md) | Contradicciones resueltas, sistema visual y contratos compartidos. |
| 02 | [Dos vistas](prompts/02-dos-vistas.md) | Mesa por defecto y Estudio, sin duplicar editor ni datos. |
| 03 | [Editor y cotización](prompts/03-editor-cotizacion.md) | Recorrido manual completo, aperturas y biblioteca real. |
| 04 | [Operación y documentos](prompts/04-operacion-documentos.md) | Documento comercial, materiales, corte y continuidad por rol. |
| 05 | [Copiloto](prompts/05-copiloto.md) | Asistencia opcional capaz de ejecutar sobre el sistema existente. |
| 06 | [Planes](prompts/06-planes.md) | Base sin IA y núcleo MiMo común con límites de uso, reutilizando billing. |
| 07 | [Cierre y QA](prompts/07-cierre-qa.md) | Una campaña final de pruebas, correcciones y entrega ejecutable. |

Las etapas 01–06 son de desarrollo. No se exige una batería de pruebas ni una aprobación del dueño entre etapas. La campaña de pruebas se concentra en 07, con correcciones hasta cerrar los fallos. El trabajo debe mantenerse compilable y respetar invariantes durante toda la construcción.

## Evidencia reutilizable

- [Auditoría real de DEKOPEN](../2026-10-18-revision-profunda/auditoria-dekopen.md): hechos fechados y casos que Claude debe resolver.
- [Síntesis competitiva](../2026-10-18-revision-profunda/sintesis-competitiva.md), [matriz completa](../2026-10-18-revision-profunda/matriz-completa.md) y [metodología](../2026-10-18-revision-profunda/metodologia-rubrica.md).
- [Referencias visuales](../2026-10-18-revision-profunda/evidencia-visual.md) y [alcance real de REA](../2026-10-18-revision-profunda/rea-evidencia.md).
- [Fuentes de catálogos](../2026-10-18-revision-profunda/catalogos-reales.md), incluido el material Proline del dueño y sus incidencias.

## Qué sustituye esta decisión

La elección de tres propuestas ha terminado: se conserva Mesa + Estudio. Centro de encargos deja de ser una puerta principal del producto; puede haber historial de trabajos dentro del copiloto. Los mockups anteriores, sus colores, tarjetas y paneles de IA no son diseño aprobado. Los prompts de 17-10 y el anterior `prompt-claude.md` del 18-10 se conservan como historia y no deben ejecutarse en paralelo a este paquete.

`docs/PRODUCT.md` y partes de la Constitución todavía describen la IA como interfaz central o acoplada al inspector. El prompt 01 exige reconciliarlos con la decisión reciente. Esta fase de investigación no altera silenciosamente esas reglas ni toca el código del producto.

## Estado de la entrega

Base observada: rama `claude/v1-implementacion`, HEAD `6f78e3299d93816991fb7c2fe2a2044458fc5e7a` **más cambios locales extensos**. El SHA solo no reconstruye lo observado. No se han desplegado cambios, publicado catálogos ni ejecutado estos prompts. Tampoco se declara que DEKOPEN supere comercialmente a todas las suites: esa es una aspiración que debe sostenerse con tareas reales, no una nota inventada.

Revisión documental de esta entrega: 17 documentos, siete prompts en secuencia, 391 enlaces locales comprobados sin errores y revisión cruzada de continuidad, permisos y alcance, incluidas las aclaraciones de conexiones finales y adjuntos multimodales. Se preservaron las huellas de Constitución y golden preexistentes. La selección Grok contiene cuatro imágenes con hashes. Esta comprobación acredita el paquete documental; las pruebas de producto corresponden a la etapa 07 de Claude y las del entorno de lanzamiento a las conexiones posteriores a la aprobación.
