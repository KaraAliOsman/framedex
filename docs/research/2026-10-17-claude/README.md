# DEKOPEN v1 — investigación, auditoría y encargo para Claude

**Fecha:** 17 de octubre de 2026. **Estado:** propuesta de producto y diseño; pendiente de implementación y aceptación del dueño.

La recomendación central es reorganizar DEKOPEN alrededor del trabajo que una persona quiere terminar: **dibujar una ventana, preparar una cotización convincente y obtener sus materiales y su corte**. La profundidad técnica debe sostener ese recorrido sin ocupar toda la interfaz. La IA debe realizar trabajo dentro de él y devolver resultados que se puedan comprobar y modificar.

Este paquete contiene investigación y documentación. **No modifica código de la aplicación, no aplica los prompts y no reintroduce el rediseño rechazado.** Las eliminaciones indicadas son decisiones propuestas para la siguiente implementación.

## Lectura recomendada

| Necesidad | Documento |
|---|---|
| Entender exactamente el encargo y sus prioridades | [00 · Encargo y criterios](00-encargo-y-criterios.md) |
| Comprobar qué se encontró y con qué evidencia | [01 · Evidencia y auditoría](01-evidencia-y-auditoria.md) |
| Estudiar competidores, videos y fuentes | [02 · Competencia y fuentes](02-competencia-y-fuentes.md) |
| Resolver navegación, recorridos y preferencias | [03 · Experiencia y arquitectura](03-experiencia-y-arquitectura.md) |
| Definir estilo, controles, iconos, carga y movimiento | [04 · Dirección visual e interacción](04-direccion-visual-e-interaccion.md) |
| Mejorar dibujos, perfiles, materiales y 3D | [05 · Ventanas, perfiles y texturas](05-ventanas-perfiles-y-texturas.md) |
| Diseñar plantillas y edición de documentos | [06 · Documentos y editor](06-documentos-y-editor.md) |
| Convertir la IA en un trabajador con límites reales | [07 · IA como trabajador](07-ia-como-trabajador.md) |
| Importar y ampliar catálogos desde PDF | [08 · Catálogos y OCR](08-catalogos-y-ocr.md) |
| Simplificar materiales, corte, compras, taller y CNC | [09 · Materiales, corte y operación](09-materiales-corte-y-operacion.md) |
| Ejecutar por etapas y cerrar calidad al final | [10 · Ejecución y aceptación](10-ejecucion-y-aceptacion.md) |
| Preparar el contexto de Claude Opus 5.5 | [11 · Guía de Claude](11-claude-opus-5-5.md) |
| Conocer límites, dudas y defectos diferidos | [12 · Incidencias y pendientes](12-incidencias-y-pendientes.md) |
| Resolver el contenido y estados de cada pantalla | [13 · Contratos de pantalla](13-contratos-de-pantalla.md) |
| Comenzar posteriormente la implementación | [Prompt maestro](prompts/00-inicio.md) |

Para Claude: empezar por el prompt maestro, el encargo, la auditoría y el plan de ejecución. Cargar los documentos de cada dominio cuando se trabaje en él. No es necesario introducir todo el paquete en una sola conversación inicial.

## Qué está comprobado

- Checkout: `codex/v1-experiencia`, HEAD `6f78e3299d93816991fb7c2fe2a2044458fc5e7a`. Las fuentes del producto están restauradas al estado de `edcfd2844d2c2fc7cbb0d3b543b50e9089ab9b3f`.
- Se inspeccionaron fuentes de navegación, editor, acabados, 3D, IA, importación, documentos, precios, producción, CNC y superficies secundarias.
- Se revisaron capturas y PDF locales anteriores, identificados en el registro de evidencia. Su aspecto es evidencia histórica; no acredita el estado exacto del navegador actual.
- Se consultaron fuentes públicas primarias de nueve familias de competidores, referencias de agentes, documentación de procesamiento documental y recomendaciones oficiales de Anthropic.

## Límites que importan

El navegador de la sesión no logró conectar después de que el dueño activara su uso. **No hay una nueva visita visual en vivo acreditada en esta investigación.** La URL ambiente era `/pricing/commercial`; no se usa esa URL como prueba de su contenido. Las capturas previas y el código permiten un diagnóstico amplio, pero Claude debe completar la revisión en vivo antes de afirmar aceptación visual del producto futuro.

No se recibieron los PDF concretos de Proline y Aluminios 2000. Se localizó la página pública de catálogos de Aluminios 2000; **no se probó la importación de esos fabricantes**. Tampoco hubo acceso privado a las aplicaciones comerciales ni pruebas en máquinas CNC. «Sistemas Z» sigue sin identificación inequívoca.

Las metas de un minuto para una cotización sencilla y de unos quince minutos para aprender el recorrido son **objetivos del dueño**, no resultados medidos. No se afirma superioridad universal frente a competidores.

## Qué cambia respecto a los intentos rechazados

1. El plan parte del producto restaurado y del encargo actual; los documentos del rediseño anterior son antecedentes, no instrucciones activas.
2. Cada intervención enlaza problema, evidencia, comportamiento deseado y forma de reconocer su calidad.
3. La dirección visual se define junto con la jerarquía de acciones y los recorridos. Cambiar colores o redondear tarjetas no constituye el trabajo.
4. Se distingue lo que ya existe y necesita otra presentación de lo que necesita nuevas capacidades de backend.
5. La campaña de corrección de bugs y pruebas se agrupa al final, conforme a la instrucción del dueño. Durante la construcción se lleva una lista de incidencias, sin abrir una campaña de depuración por cada pantalla.

## Preservación del espacio de trabajo

El cambio local previo en `engine/tests/golden_analytics.json` es ajeno a esta investigación y debe conservarse. Su SHA-256 de referencia es `F6A97BEBCED724C4C80FBBA0170B43019BD6C409E62901E472E420138EEAC8B3`. No se reinició el stack, no se ejecutaron fixtures, no se borraron sesiones y no se modificaron datos del negocio.

La PR 159 está cerrada sin merge tras el rechazo del diseño. No reabrirla ni recuperar sus commits de interfaz como si fueran una dirección aprobada. La PR 158 pertenece a otro trabajo.
