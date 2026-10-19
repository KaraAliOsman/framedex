# Encargo del dueño y criterios de producto

## Resultado que se busca

DEKOPEN v1 debe ser una herramienta profesional para diseñar, calcular, cotizar y fabricar ventanas de PVC y aluminio. Debe permitir trabajar manualmente con facilidad y delegar en una IA capaz de preparar casi todo el trabajo autorizado. La experiencia debe resultar comprensible, agradable y productiva para alguien del oficio desde su primera sesión.

El dueño considera que el producto actual está aproximadamente al 30 % de lo que necesita. Esa cifra expresa su valoración, no una medición funcional. Dos propuestas visuales anteriores fueron rechazadas y revertidas. Ninguna puede considerarse aceptada por haber pasado pruebas técnicas.

## Requisitos trazables

Los identificadores siguientes sirven para comprobar cobertura del plan, no deben aparecer en la interfaz.

| ID | Intención del dueño | Decisión del plan | Desarrollo |
|---|---|---|---|
| O01 | Cada detalle debe aportar valor | Revisar acción, texto, jerarquía, estado y ubicación; eliminar redundancia | 01, 03, 04 |
| O02 | Entender sin guía extensa | Recorrido principal visible, ejemplos accionables y revelado progresivo | 03 |
| O03 | Cotizar y obtener material muy rápido | Preferencias heredadas; resumen de materiales y acceso directo a corte | 03, 09 |
| O04 | La IA pregunta demasiado | Ejecutar borradores con datos conocidos; agrupar solo dudas imprescindibles | 07 |
| O05 | Usar preferencias guardadas | Decisión explícita ya tomada: empresa → proyecto → ventana | 03, 07 |
| O06 | IA disponible en cualquier lugar | Panel contextual persistente junto al archivo o trabajo activo | 07 |
| O07 | IA para hacer, no solo responder | Herramientas tipadas para crear, modificar, comparar y preparar documentos | 07 |
| O08 | IA con límites suficientes | Permisos del servidor, aislamiento por empresa y ausencia de herramientas prohibidas | 07 |
| O09 | No permitir pagos, código ni seguridad a la IA | Denegación estructural; no depende de una frase en el prompt | 07 |
| O10 | Inspiración Grok Bot y Dots | Continuidad de trabajo, resultados visibles y compañero 2D original | 02, 04, 07 |
| O11 | No gusta el robot actual | Reconstruir su identidad, botón y presencia; conservar semántica de estados | 04 |
| O12 | Turquesa puede conservarse | Acento controlado, un tema definitivo propuesto y contraste legible | 04 |
| O13 | Logo actual funciona | Preservar marca principal; no gastar el esfuerzo en rehacerla | 04 |
| O14 | Dibujos y 3D tienen base útil | Mejorar acabados, uniones, escala y salida documental | 05 |
| O15 | Texturas visibles y de calidad | Biblioteca calibrada; foto propia opcional con preparación asistida | 05 |
| O16 | PVC normalmente de un color | Un acabado normal; bicolor dentro de opciones especiales | 03, 05 |
| O17 | Perfiles reconocibles aunque no haya foto | Ilustraciones de familia separadas de secciones técnicas verificadas | 05, 08 |
| O18 | Importar con solo subir el PDF | Una entrada; análisis interno por páginas y revisión de excepciones | 08 |
| O19 | Ampliar una línea con otro catálogo | Fusión con procedencia, conflictos y versión; no sobrescribir en silencio | 08 |
| O20 | Probar Proline y Aluminios 2000 | Corpus pendiente de recibir; protocolo preparado y sin afirmar éxito | 08, 12 |
| O21 | Cotizaciones profesionales | Tres diseños comerciales distintos y coherentes | 06 |
| O22 | Diseños por familia documental | Dos pedidos y tres órdenes de corte, además de las tres cotizaciones | 06 |
| O23 | Firma y aprobación opcionales | Política del negocio y acción explícita; sin bloque fijo obligatorio | 06 |
| O24 | Numeración humana configurable | Cotización 1/N.º 1 por defecto; prefijo e inicio por empresa | 06 |
| O25 | Editar plantilla y documento final | Editor visual del original estructurado, con vista de impresión | 06 |
| O26 | IA también edita documentos y página | Operaciones sobre contenido/estilo de documentos y portal del negocio | 06, 07 |
| O27 | Botón claro de orden de corte | Orquestación de preparación con explicación solo de faltantes reales | 09 |
| O28 | CNC útil sin dominar el producto | Capacidades por máquina, adaptadores y homologación real | 09 |
| O29 | Superar a la competencia | Matriz de trabajos comparables y criterios medibles; sin ranking inventado | 02, 10 |
| O30 | Pensar con principios de gran diseño | Apple y Emil aplicados a claridad, respuesta, consistencia y criterio | 04, 11 |
| O31 | No repetir pruebas y bugs durante toda la obra | Registro de incidencias y campaña conjunta de cierre | 10, 12 |
| O32 | Ahora solo investigación y preparación para Claude | Documentación y prompts; ninguna implementación en esta sesión | README, 11 |
| O33 | Ignorar por ahora planes comerciales | Sin trabajo nuevo de suscripciones ni monetización | 10 |
| O34 | Identidad de IA de DEKOPEN | Marca del asistente veraz; no inventar entrenamiento propio | 07 |
| O35 | Experiencia agradable y viva | Movimiento funcional, manipulación directa, continuidad y respuesta inmediata | 04 |

## Prioridades cuando dos deseos compiten

1. Exactitud del cálculo, aislamiento entre empresas y control de consecuencias externas.
2. Terminar el trabajo principal con pocas decisiones comprensibles.
3. Calidad del dibujo y del documento que recibe el cliente.
4. IA con capacidad real y resultados comprobables.
5. Coherencia visual, sensación de respuesta y cuidado de detalles.
6. Funciones especializadas, accesibles en su contexto.

Esto evita utilizar la «simplicidad» para borrar capacidades de fabricación o la «potencia» para mostrar todas las opciones a la vez. Las opciones raras deben existir donde ayudan; no dominar la primera pantalla.

## Datos que pueden heredarse y datos que no pueden inventarse

La empresa puede guardar sistema habitual, acabado, vidrio, condiciones comerciales, presentación de PDF y preferencias de taller cuando tenga autoridad para ello. El proyecto puede sustituirlos y una ventana puede tener una excepción. Se debe ver el origen de una excepción sin convertir cada control en una explicación técnica.

Las medidas de una ventana, un precio de compra inexistente, una regla de fabricación ausente o una compatibilidad no documentada no se vuelven verdaderos por sugerencia de la IA. El sistema puede preparar un diseño ilustrativo y señalar lo que falta para calcular, cotizar o fabricar. Cada capacidad tiene su nivel de preparación; no hace falta bloquear todo por un dato que solo afecta a otra etapa.

## Qué significa «libertad total» en documentos y en IA

El negocio controla la composición, el contenido editorial, el aspecto y las secciones opcionales. Puede modificar precios y especificaciones mediante las operaciones de negocio correspondientes y ver su efecto en el documento. No puede quedar un total escrito a mano que contradiga el cálculo oficial sin que el sistema lo sepa.

La IA puede realizar cambios reversibles dentro del permiso recibido, presentar una muestra y permitir deshacerlos. Emitir, enviar, comprometer una compra o liberar una acción de fabricación conserva el clic humano previsto por las invariantes. El clic debe aprobar un resultado concreto, no abrir una cadena de diez confirmaciones.

## Criterios para eliminar una cosa

Retirar un elemento de la vista habitual si no cambia una decisión del usuario, duplica un estado, presenta una implementación interna o solo explica por qué existe el software. Conservarlo en contexto si ayuda a corregir una excepción, verificar una cifra o trabajar con mayor precisión. Eliminar del producto únicamente la decoración redundante y los caminos sustituidos, después de mapear sus capacidades y enlaces.

Ejemplos: ocultar la huella criptográfica del cuerpo comercial no significa quitar el registro auditable; retirar la página de trabajos de la navegación principal no significa perder tareas en curso; simplificar los acabados no significa eliminar PVC bicolor.
