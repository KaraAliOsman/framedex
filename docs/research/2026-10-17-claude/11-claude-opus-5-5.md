# Preparar Claude Opus 5.5 para este trabajo

## Recomendación

Dar a Claude un encargo concreto, contexto por dominio y una definición observable de terminado. La calidad no se consigue repitiendo «sé el mejor diseñador» ni cargando todos los documentos históricos. Este paquete aporta decisiones, evidencia y ejemplos para que pueda ejercer criterio sobre un objetivo bien definido.

La [guía oficial de Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5), consultada el 17-10-2026, recomienda calibrar esfuerzo, dar condiciones explícitas de finalización y especificar patrones visuales concretos. Explica que una petición genérica de evitar el aspecto de IA puede cambiar un estilo prefabricado por otro. Su orientación sobre contexto se complementa con [CLAUDE.md y mejores prompts](https://support.claude.com/en/articles/14553240-give-claude-context-claude-md-and-better-prompts).

## Configuración práctica

Usar Opus 5.5 si está disponible en el cliente del dueño. En decisiones difíciles de interacción, agentes, catálogos o editor documental, elegir un nivel de esfuerzo alto compatible con ese cliente si aporta mejor resultado; para trabajo rutinario, mantener una configuración eficiente. La guía documenta `medium` como predeterminado y reserva niveles mayores para ganancias comprobadas. Un máximo de tokens o de esfuerzo no garantiza una interfaz mejor. Los nombres y controles de API no se deben copiar a un cliente que no los ofrezca.

No pedir razonamiento interno privado. Pedir decisiones, alternativas relevantes, fundamentos breves, archivos afectados y evidencia de resultado. La inteligencia debe aparecer en la calidad de las soluciones y en el trabajo completado.

## Contexto que debe recibir

| Momento | Contexto mínimo útil |
|---|---|
| Inicio | Prompt maestro, README, encargo, evidencia y plan de ejecución |
| Dirección visual | 04, contratos de pantalla, constitución actual y componentes existentes |
| Editor | 05, pantalla del editor, modelo/comandos/dibujante y hechos de dibujo |
| IA | 07, servicios/herramientas actuales y contexto del trabajo activo |
| Catálogos | 08, esquema, servicio, gateway y archivos fuente cuando existan |
| Documentos | 06, renderizadores, snapshots, preferencias y muestras |
| Operación | 09, cálculo/materiales, producción, corte/CNC y estados |
| Cierre | 10, incidencias pendientes, contratos y evidencia de implementación |

Las referencias al código están fechadas: reubicar símbolos y confirmar lo vigente en lugar de asumir que una línea sigue igual. El wiki ayuda a encontrar contexto, no sustituye la lectura del archivo pertinente.

## Skills y criterio profesional

Se aplicaron `apple-design` y `emil-design-eng` como criterios de esta auditoría. El propósito fue mejorar respuesta, continuidad, jerarquía y cuidado del detalle, sin copiar Apple ni convertir recomendaciones aisladas en una receta estética.

En el entorno del dueño están en `C:/Users/alios/.agents/skills/apple-design/SKILL.md` y `C:/Users/alios/.agents/skills/emil-design-eng/SKILL.md`. Leer solo las pertinentes al trabajo. Si Claude está en otro ordenador o interfaz, los enlaces locales pueden no existir; usar la síntesis de este paquete y cargar recursos autorizados, sin fingir que leyó una skill que no tiene. No hace falta instalar un catálogo de skills para diseñar bien.

La skill local `testing-framedex` ayuda a preparar/reutilizar el stack para la verificación final; no autoriza reconstruir o resetear el entorno del dueño por una tarea de documentación. Las skills de PDF y navegador ayudan a observar el resultado; una conexión fallida no se resuelve proclamando aceptación visual.

No crear ni modificar ahora un `CLAUDE.md` raíz que cambie las instrucciones de todo el repositorio. El prompt maestro y los documentos son el contrato de este encargo futuro; una configuración persistente posterior debe ser breve y respetar AGENTS, las decisiones recientes y la jerarquía de autoridad.

## Antipatrones concretos que debe evitar en DEKOPEN

- Panel inicial con cuatro KPI decorativos y saludo grande antes del trabajo.
- Tres columnas vacías alrededor de un robot gigante.
- Pantallas de formulario largo con un dibujo pequeño como adorno.
- Códigos técnicos como nombre dominante de obra/cotización.
- MAYÚSCULAS pequeñas, monoespaciada para todo y controles que parecen texto.
- Un bloque de aviso para cada campo desconocido, aunque no afecte a la tarea.
- Bicolor visible por defecto y el mismo dato pedido en varias superficies.
- «Ocho plantillas» que solo cambian el acento de una composición.
- Un editor de PDF que únicamente pone anotaciones encima.
- Una IA que termina una petición de ejecución con enlaces e instrucciones manuales.
- Prometer importación completa tras OCR de filas sin relaciones ni reglas.
- Llamar integración CNC a un archivo neutro sin homologación.
- Mantener versiones visuales viejas ocultas indefinidamente.

No convertir esta lista en prohibiciones arbitrarias de todas las tarjetas, todos los radios o todas las animaciones. El criterio es que cada patrón sirva al trabajo y que el conjunto tenga una dirección reconocible.

## Uso de los prompts

1. Abrir el checkout restaurado y entregar [00 · Inicio](prompts/00-inicio.md).
2. Ejecutar las etapas en orden. El maestro autoriza continuar entre ellas cuando se use para iniciar la implementación futura.
3. Si el cliente necesita conversaciones nuevas por tamaño de contexto, dar el prompt de la siguiente etapa con un estado breve y las decisiones ya aplicadas.
4. Mantener un registro de trabajo: terminado, en curso, pendientes externos, incidencias diferidas y siguiente operación concreta. Un resumen de progreso no significa que el encargo esté completo.
5. Si el cliente corta una tarea, reanudar desde ese estado; no volver a generar el proyecto ni repetir fases completas. Evitar bucles de continuación sin nuevo progreso.

Los prompts no se han ejecutado en esta investigación. Copiarlos a Claude para iniciar es una acción futura del dueño. Su texto está redactado para implementar cuando llegue esa instrucción; leer este paquete no equivale a recibirla.

## Cómo mantener autonomía sin perder control

Claude puede elegir soluciones rutinarias, avanzar en dependencias independientes y completar la etapa. Debe pedir un dato solo si bloquea una decisión material que no puede deducir, y preparar lo demás mientras tanto. No detenerse a preguntar si puede ajustar espaciado o renombrar un botón ya comprendido en el encargo.

La autonomía no permite enviar documentos a clientes, modificar pagos, quitar permisos, homologar una máquina sin acceso o afirmar una prueba no hecha. Una limitación real debe aparecer en el registro y en la entrega. La revisión humana final debe examinar un producto y documentos concretos.

## Qué debe devolver Claude al cerrar

Descripción del comportamiento entregado, decisiones visuales relevantes, enlaces a evidencia seleccionada, validación real y limitaciones pendientes. No un manifiesto sobre lo «premium» que quedó. Mantener wiki y documentación de cambios, y preparar una PR cuando corresponda al trabajo de implementación sin mezclar el cambio ajeno de goldens.
