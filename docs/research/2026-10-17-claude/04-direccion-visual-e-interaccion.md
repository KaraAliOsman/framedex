# Dirección visual e interacción

## Punto de vista propuesto

La ventana y el documento deben parecer trabajo profesional bien resuelto; la interfaz debe hacer fácil manipularlos. Se propone un entorno **claro, luminoso y preciso**, con turquesa contenido, dibujos ricos en material y controles inequívocos. La personalidad proviene de proporciones, respuesta y claridad, no de llenar la pantalla de metáforas técnicas.

Esta es una dirección recomendada para construir y comprobar; no se atribuye al dueño la aprobación de cada token. Preservar el logo. No recuperar la variante azul ni las composiciones descartadas en los commits revertidos.

## Qué cambia en la constitución vigente

La [Constitución](../../design/CONSTITUCION.md) sigue siendo la referencia del repositorio. Las instrucciones recientes del dueño prevalecen en los conflictos explícitos. Antes de implementar superficies, Claude debe actualizar la constitución de manera trazable con estas decisiones, sin reescribir invariantes de cálculo o seguridad.

| Regla vigente | Problema con el encargo actual | Cambio propuesto |
|---|---|---|
| §1: parecer una lámina/manual técnico; precisión sin simpatía | El dueño pide una experiencia viva, comprensible y agradable | Mantener precisión; añadir calidez contenida y claridad de acciones |
| §3.1/3.7: dos temas; taller oscuro por defecto | El dueño pide un tema definitivo y rechaza ambos actuales | Un tema claro coherente, adaptado a contraste/entorno sin selector ornamental |
| §3.2: cuerpo 13, etiquetas técnicas 11 en mayúsculas | Exceso de densidad y aspecto de consola | Cuerpo más legible y etiquetas en frase; densidad técnica solo donde sirve |
| §3.4: radios máximos 4, controles 28/32 | Controles poco distinguibles en uso habitual | Escala de controles y radios por función; no redondear todo por decoración |
| §3.5: cargador de cota obligatorio | El dueño rechaza su diseño | Carga contextual, estable y vinculada a progreso real |
| §3.6: iconos propios de puntas cuadradas | Algunas metáforas no se entienden | Sistema genérico reconocible y símbolos propios del oficio consistentes |
| §7/8: momentos de firma obligatorios | Pueden imponer detalles que no ayudan al trabajo | Exigir propósito y calidad; no una decoración por pantalla |

Mantener: dibujo como interfaz, fuente única de cifras, revelado progresivo, trazabilidad accesible, estados claros, eliminación de caminos sustituidos y accesibilidad. No añadir guardas automáticas que vuelvan a fijar decisiones estéticas antes de comprobar su utilidad.

## Composición de escritorio

Base de diseño: 1440×900; comprobar posteriormente 1280×800 y 1024×768. Navegación de aproximadamente 200–216 px, cabecera de unos 56 px y un único riel contextual de aproximadamente 304–384 px. Son puntos de partida de composición, no límites de ingeniería.

En el editor el lienzo ocupa alrededor de dos tercios o más del área de trabajo. Con IA abierta, el inspector comparte espacio o se pliega. En documento, la página es protagonista y las herramientas aparecen al seleccionar. No construir por defecto tres columnas con contenido vacío.

Orden visual: contexto → objeto de trabajo → acción siguiente → detalle. Reducir franjas superiores, filtros siempre desplegados, marcos dentro de marcos y tarjetas de altura excesiva. Una lista densa necesita filas claras, alineación y separación; una galería de ventanas necesita imágenes útiles. Usar cada formato donde corresponde.

## Sistema visual inicial

| Rol | Propuesta inicial | Intención |
|---|---|---|
| Fondo general | Gris frío muy claro, alrededor de `#F4F6F7` | Separar mesa de trabajo y papel sin teñir materiales |
| Superficie principal | Blanco | Claridad de dibujo y documento |
| Tinta | Grafito profundo, cercano a `#161C1F` | Contraste y continuidad con marca |
| Texto secundario | Gris suficientemente contrastado | Información secundaria legible, sin volver toda la UI tenue |
| Acento de acción | Turquesa oscuro existente `#075F5A` | Identificar acciones principales y selección |
| Selección suave | Tinte turquesa muy ligero y borde claro | Mostrar alcance sin cubrir textura o vidrio |
| Bordes | Neutros; más fuertes en controles que en separadores | Distinguir interacción y estructura |
| Avisos | Semántica estable con texto/icono | No depender únicamente del color |
| Acento cálido | Marca y casos concretos de atención | Sin convertir cada control en una alerta |

No adoptar proporciones rígidas de color como objetivo. La tela de la página y el documento deben descansar. Verificar contrastes reales al final: texto habitual 4,5:1, texto grande y elementos aplicables según WCAG; no dar por aprobado un color por su nombre de token.

Mantener IBM Plex inicialmente permite concentrar el esfuerzo en composición. Propuesta de escala: cuerpo 14–15/20–22; título 24/30; subtítulo 18/24; etiqueta 12–13/16–18; tabla 13/18. Usar cifras tabulares; reservar monoespaciada para medidas técnicas y códigos donde ayuda. No presentar toda cantidad comercial como texto de terminal.

Espaciado con base de 4 px y ajustes ópticos justificados. Controles habituales 38–40 px; compactos 32–36 solo donde la tarea lo requiere; tablet/taller aproximadamente 44–48. Radios propuestos de 6–8 en controles, 8–12 en contenedores puntuales, 0 en papel/tabla/dibujo. No usar píldoras como botón universal ni grandes tarjetas redondeadas para cada línea.

## Gramática de controles

| Tipo | Aspecto y comportamiento |
|---|---|
| Acción principal | Relleno turquesa, texto claro, verbo concreto; una por región |
| Acción secundaria | Fondo neutro/blanco y borde visible; cambia algo en el contexto actual |
| Navegación | Enlace o elemento de navegación consistente; no imitar un botón si solo abre otra vista |
| Acción de icono | Área suficiente, nombre accesible y ayuda al foco/hover; texto para tareas decisivas |
| Peligro | Ubicado fuera de acciones frecuentes; consecuencia clara y recuperación cuando exista |
| Campo | Borde, etiqueta persistente, valor y unidad; el placeholder no es la etiqueta |
| Selección | Estado local claro, teclado, y cantidad seleccionada en operaciones de lote |
| Deshabilitado | Solo cuando existe una causa temporal; explicar qué habilita la acción |
| Guardado | Estado discreto «Guardado», «Guardando» o «Pendiente»; nunca un falso éxito anticipado |

No depender del hover para descubrir acciones esenciales. Foco visible ya existe en la base actual: conservarlo al sustituir controles. Menús y paneles devuelven el foco al origen; Escape cierra la capa, no pierde un trabajo. Respetar zoom de texto y navegación por teclado.

## Iconografía

Una familia para acciones generales, con peso óptico consistente y tamaños de 16/20/24 según uso. Primero auditar las dependencias existentes y escoger una sola base mantenida; no instalar varias para resolver cada icono. El oficio mantiene símbolos propios para fijo, corredera, abatible, oscilobatiente, división y cotas, derivados de la misma convención que usa el dibujo.

Un icono de catálogo debe reconocerse como biblioteca; uno de material no debe confundirse con cuadrícula o proyecto. Una acción compleja como «Orden de corte» requiere texto. El estado activo se distingue de hover y foco sin depender de un cambio mínimo de trazo.

Evaluar las siluetas juntas, al tamaño real, sobre sus fondos reales. No juzgar solo el SVG ampliado. Ajustar separación óptica y contraste, no inventar una metáfora distinta para una acción común.

## IA: identidad y presencia

Diseñar un compañero 2D circular original, pequeño y reconocible. El referente funcional son Grok Bot y Dots; no se han extraído sus animaciones para copiarlas. La figura de DEKOPEN debe poder verse bien a 24–32 px y ser expresiva a mayor tamaño sin añadir detalles mecánicos.

**Brief para su exploración:** una silueta simple, rostro o foco expresivo mínimo, color integrado con el producto y personalidad tranquila. Explorar pocas alternativas distintas y evaluarlas junto al botón y el panel. Elegir una; no entregar al usuario un configurador de mascotas como sustituto del diseño.

| Estado real | Expresión/acción visual propuesta | Texto o control necesario |
|---|---|---|
| Disponible | Pose quieta; respuesta breve al foco o entrada | «Asistente» |
| Recibe instrucción | Orientación hacia compositor | Contexto sobre el que trabajará |
| Trabaja | Cambio suave de postura/actividad discreta | Qué está preparando y detener |
| Necesita dato | Mirada/énfasis local; sin alarma repetitiva | Una pregunta concreta con opciones |
| Revisión lista | Estado estable de atención | Muestra, diferencias y acción de revisar/aplicar |
| Terminado | Microgesto único, luego reposo | Resultado guardado y deshacer si aplica |
| Error/cancelado | Estado sobrio, sin tristeza teatral | Qué quedó hecho y cómo continuar |

No caminar por el lienzo, seguir el puntero constantemente, ocupar una portada vacía o emitir celebraciones repetidas. La personalidad no puede competir con medir, dibujar o leer una cotización. El botón incluye un nombre; la mascota por sí sola no explica qué hace.

## Movimiento

Aplicar los principios de Apple y Emil: respuesta inmediata, continuidad espacial, interrupción y buenos valores predeterminados. Las skills son criterios de trabajo, no garantía de buen gusto ni autorización para imponer todos sus ejemplos.

| Interacción | Dirección propuesta | Razón |
|---|---|---|
| Pulsar un control | Respuesta de color/posición mínima, inmediata | Confirmar que recibió la acción |
| Abrir panel | 180–240 ms, origen coherente, interrumpible | Explicar de dónde aparece sin ralentizar |
| Seleccionar o editar cota | Actualización directa; sin animar el número mientras se escribe | Mantener precisión |
| Zoom/pan/arrastre | Movimiento unido al gesto; sin retardo decorativo | Conservar control espacial |
| Alternar 2D/3D | Mantener identidad y encuadre; transición breve | Reconocer que es el mismo producto |
| Actualizar precio | Sustituir resultado y señalar cambio brevemente | No hacer que una cifra bailando parezca otro cálculo |
| Aplicar lote | Resaltar objetos afectados una vez | Hacer visible el alcance |
| Entrada de mensajes | Desplazamiento solo si el usuario está al final | No arrebatar el punto de lectura |
| Mascota | Eventos de trabajo; reposo predominante | Vida sin distracción continua |

Estos tiempos son una propuesta de interacción, no una prueba de rendimiento. Priorizar transformaciones/opacidad y evitar animar layout durante tareas pesadas. No introducir blur y efectos costosos por inercia. Movimiento reducido conserva estados y elimina desplazamiento no esencial. Operaciones frecuentes de teclado no necesitan una animación por cada pulsación.

## Carga, vacíos y errores

Reemplazar el cargador de cota como marca omnipresente. Para una espera breve, mantener la composición estable y deshabilitar la acción en curso con un estado local. Para carga de una lista, usar reserva estática de filas; para un PDF, conservar el lugar de la página y distinguir vista anterior de vista actualizada.

En tareas largas de IA/importación, mostrar pasos reales y páginas procesadas cuando se conocen. Si no hay avance medible, mostrar actividad indeterminada sin porcentaje inventado. El `DimLoader` actual usa semántica de estado cuando no recibe progreso; el cambio propuesto es de claridad y diseño, no una acusación de que ya publique porcentajes falsos a lectores de pantalla.

Los vacíos ofrecen una acción del trabajo: crear ventana, subir catálogo o cambiar filtro. Una ilustración pequeña puede ayudar; una gran lámina decorativa no debe ocupar la herramienta. Los errores explican objeto, causa y remedio, conservan entradas y no muestran una excepción de backend como título.

## Pase de calidad visual que debe realizar Claude

Comparar con el mismo contenido: página inicial, proyecto de varias ventanas, editor, materiales, PDF comercial, importación y panel IA. Revisar ritmo de espacios, alineación, proporción del dibujo, diferenciación de controles, texto innecesario, contraste, consistencia y estado de guardado. Este pase es parte del diseño; la depuración y la campaña de pruebas se concentran en la etapa final.

Una pantalla puede pasar todas las pruebas funcionales y seguir siendo rechazada por composición. Documentar decisiones y mostrar evidencia del resultado real; no declarar «premium» por haber aplicado tokens.
