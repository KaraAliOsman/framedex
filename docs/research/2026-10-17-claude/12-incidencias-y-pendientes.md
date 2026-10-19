# Incidencias, límites y preguntas pendientes

Este registro distingue defectos confirmados en ejecución, limitaciones comprobadas en fuente, observaciones históricas y decisiones todavía propuestas. No se corrigió código ni se ejecutó una campaña de pruebas durante esta investigación.

## Limitaciones y fricciones comprobadas o documentadas

| ID | Naturaleza | Hecho/evidencia | Tratamiento futuro |
|---|---|---|---|
| L01 | Herramienta externa | Navegador de la sesión no conecta después de activación declarada | Completar inspección nueva cuando la conexión funcione; no eludir configuración |
| L02 | Límite de fuente | Helper multimodal rechaza más de 20 páginas | Partición interna y trabajos reanudables |
| L03 | Limitación de estrategia | Página con texto omite imagen en helper actual | Inspección por regiones y páginas mixtas |
| L04 | Límite de fuente | Compilador pide división manual por exceso de texto | Partición conservando relaciones y referencias |
| L05 | Comportamiento de fuente | Aceptación/firma añadida incondicionalmente en renderer de cotización | Política y acción opcionales, respetando revisiones |
| L06 | Capacidad no acreditada | Consulta de numeración no configura un folio comercial de cotización | Contador por empresa y migración sin alterar emitidos |
| L07 | Brecha de ejecución | Varios flujos IA preparan enlaces y no mutan el trabajo solicitado | Servicios/herramientas de borrador reales |
| L08 | Representación actual | Encuentros rectos en extrusión del miembro revisado | Representación según unión autorizada |
| L09 | Alcance actual | CNC genera intercambio neutro en ruta comprobada | Etiquetado preciso y adaptador/homologación separados |
| L10 | Observación histórica | PDF de ejemplo con gran espacio inicial, aceptación fija y URL larga | Revisar muestras nuevas tras implementación; corregir composición |
| L11 | Observación histórica | Materiales en modal estrecho y códigos dominantes | Vista amplia y relación con dibujo |
| L12 | Observación histórica | Inicio/listas con muchas OT/alertas de fixture | Diseñar agrupación; no inferir escala real del negocio |
| L13 | Desacuerdo del dueño | Estilo, iconos, carga y mascota actuales rechazados | Nueva dirección basada en recorridos y evidencia |

Los L02–L04 son límites/estrategias, no bugs de OCR demostrados sobre Proline. L08 no autoriza sustituir toda unión por inglete. L10–L12 requieren cautela sobre fecha y SHA servido.

## Datos externos pendientes

| Pendiente | Lo que ya se hizo | Qué falta y por qué importa |
|---|---|---|
| PDF Proline | Se preparó contrato y protocolo | Archivo exacto, edición y origen; medir cobertura real |
| PDF Aluminios 2000 | Se localizó página oficial de catálogos | PDF exacto anunciado por el dueño; no intercambiarlo por otra edición sin decirlo |
| Identidad «Sistemas Z» | Búsqueda sin coincidencia inequívoca | Enlace o nombre legal; evitar atribuciones falsas |
| Versiones comerciales de competidores | Documentación y fotogramas seleccionados | Acceso operativo para comparar recorridos enteros y tiempos |
| Mascota Grok/Dots | Intención del dueño y docs oficiales | Revisión visual actual si se quiere comparar gestos concretos; no necesaria para copiar |
| Editor PDF externo | Candidatos localizados y separación arquitectónica | Evaluación de edición/exportación, alcance de licencia e integración |
| Máquina CNC | Código y salida neutra revisados | Modelo/controlador, herramientas, documentación y prueba técnica |
| Usuario nuevo representativo | Objetivos definidos | Sesión observada para medir comprensión/aprendizaje |

No deben bloquear toda la construcción. Sí impiden declarar terminadas las capacidades específicas que dependen de ellos.

## Decisiones de diseño propuestas que no se deben confundir con aceptación

- Tema claro definitivo, escala de tipografía y controles del documento 04.
- Cuatro áreas habituales y espacio Taller con accesos por rol.
- Ocho composiciones documentales iniciales, con el editor de originales propios como base.
- Borrador incompleto explícito para separar diseño de datos administrativos.
- Permiso para trabajo IA reversible dentro del encargo, revisión agrupada y clic final para consecuencias externas.
- Compañero 2D original con expresividad contenida.

Todas requieren criterio y revisión del resultado al implementarse. No atribuir al dueño la elección de cada valor visual ni tratar un plan escrito como aceptación del producto.

## Registro de defectos para la futura construcción

Al descubrir un problema durante 01–09, anotar: identificador, superficie, pasos o fuente, resultado observado, impacto, captura/log mínimo y dependencia. Si no se reprodujo, marcar «sospecha»; si viene de una captura antigua, «histórico». No convertir cada observación de gusto en bug.

La etapa 10 agrupa reproducción, corrección y pruebas. Integridad, aislamiento, cálculos y pérdida de datos tienen prioridad. No realizar acciones externas reales con un defecto conocido. Un bloqueo que impida construir se resuelve de forma acotada y se registra; el resto de depuración espera a la campaña final.

## Afirmaciones prohibidas por falta de evidencia

- «Se revisó visualmente la página actual completa».
- «Se vieron de nuevo todos los videos y se probaron todos los competidores».
- «Proline y Aluminios 2000 importan correctamente».
- «CNC es compatible con cualquier marca» o «ya está calibrado en máquina».
- «Los usuarios cotizan en un minuto» o «aprenden en quince minutos» antes de medirlo.
- «El rediseño está aprobado» porque las suites pasan.
- «OCR verificado» como sinónimo de catálogo técnicamente autorizado para fabricar.

## Preservación y cierre de esta investigación

Mantener el cambio local de `engine/tests/golden_analytics.json`, el estado de `.run/`, sesiones y datos del stack. Las dos migraciones aditivas locales del rediseño revertido no se eliminan para embellecer el entorno. No reabrir PR 159 ni mezclar PR 158.

Al finalizar este paquete solo corresponde comprobar coherencia documental, enlaces locales y diferencia de Git. No se ejecuta la suite del producto, porque no hubo modificación de su código. Este registro es un punto de partida; no reemplaza el registro de bugs que genere la implementación futura.
