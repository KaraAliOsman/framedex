# Dirección final: el trabajo pertenece al usuario

## Decisiones resueltas

La corrección reciente del dueño prevalece sobre propuestas anteriores. No falta elegir una tercera dirección ni aprobar otra maqueta para comenzar el encargo de Claude.

| Decisión | Especificación final | Motivo |
|---|---|---|
| Centro del producto | Producto configurado, obra y cotización manual. | El sistema debe valer su precio sin usar IA. |
| Inicio recomendado | Mesa de obra. | Permite leer el conjunto y trabajar por excepción. |
| Segunda vista | Estudio, seleccionable por el usuario del SaaS. | Da prioridad al diseño de una posición sin crear otro producto. |
| Alcance del selector | Preferencia de presentación; ambas incluidas en el plan base. | El usuario elige cómo trabajar, sin migrar ni duplicar proyectos. |
| Datos compartidos | Misma obra, posición, revisión, permisos, borrador y operaciones. | Cambiar vista no puede perder trabajo, generar otra ventana o recalcular con otra fórmula. |
| Copiloto | Popup global opcional, cerrado al iniciar una sesión nueva. | La IA aparece cuando la persona la necesita. |
| Ubicación de IA | Capa flotante accesible desde cualquier ruta, sin columna reservada. | Abrir el copiloto no sustituye el inspector ni encoge el lienzo. |
| Espacio propio de IA | Conversaciones/historial y ampliación voluntaria desde el popup. | Trabajos largos necesitan espacio sin convertir el producto en un chat. |
| Modos | Chat y Trabajo. | Conversar y delegar son intenciones distintas. |
| Autonomía | Solo proponer / Con aprobación / Omitir todo. | El nivel de ejecución es independiente del modo y del plan. |
| Omitir todo | Ejecuta el trabajo reversible autorizado y entrega recibo final. | Evita aprobaciones fragmentadas y preguntas que el sistema puede resolver. |
| Autoridad | Motor, catálogo revisado, permisos y clic humano para efectos externos. | Una elección de autonomía no convierte la IA en autoridad técnica ni financiera. |
| Plan base | Recorrido manual completo; ninguna dependencia del proveedor IA. | La ausencia de IA no debe convertirlo en una demo limitada. |
| Planes superiores | Mismo núcleo IA y tres autonomías, con más créditos/límites de uso y extras profesionales concretos. | El precio no compra una IA deliberadamente inferior o menos controlada. |
| Modelo | MiMo 2.6 Pro para todos los planes IA hasta cambio explícito del dueño; transporte real por verificar. | No introducir otro modelo o fallback silencioso. DeepSeek Flash 4.1 es solo un candidato futuro mencionado, sin validar/configurar. |
| Consumo | Cuotas versionadas con proporcionalidad comprensible; PRD-03 contrastado con billing real. | El ejemplo anual 30/49/99/149 no fija tarifas ni modifica contratos existentes. |
| Personaje | Alta fidelidad al personaje animado de Grok Bot, con estilo de conversación adaptado a DEKOPEN. | La aclaración se centra en figura y movimiento; no exige copiar su aplicación completa. |
| Desarrollo | Construir 01–06 y cerrar con campaña 07. | El dueño prioriza desarrollo y corrección final, sin ceremonias de aprobación por etapa. |
| Apariencia | Sistema profesional coherente derivado de tareas y datos reales. | Los mockups anteriores no alcanzaron el nivel esperado. |

«El cliente elige» se interpreta como la persona usuaria del SaaS que elige su vista de trabajo. No añade ese selector al portal público del comprador de ventanas.

## Qué debe poder hacer la base manual

Una empresa configura sus datos y valores habituales, incorpora o selecciona una serie real revisada, crea una obra y vincula su cliente. Puede empezar un borrador antes de tener todos los datos comerciales; los pendientes se hacen visibles cuando realmente bloquean un paso.

Desde Mesa revisa posiciones, miniaturas fieles, cantidades, medidas, sistema, vidrio y precio vigente. Filtra por causa y aplica cambios en lote con la misma semántica que usa el editor. Entra a una posición para diseñar; Estudio conserva esa selección y ofrece el lienzo amplio. El inspector describe exactamente el módulo, hoja o elemento seleccionado. El cambio de vista conserva el borrador, el historial y el estado de guardado.

La persona configura medidas, divisiones, aperturas, vidrio, perfiles, herrajes y acabados mediante las capacidades reales del motor. Las opciones incompatibles explican la causa y muestran un camino válido. Las cotas, el dibujo 2D, el 3D, la BOM y el precio hablan del mismo objeto y cara. Faltantes técnicos siguen desconocidos: no se representan como cero ni se completan con una aproximación de IA.

Después revisa el precio y el documento comercial, edita textos/composición permitidos y emite una revisión con un clic consciente. Los cálculos no se editan dentro del documento. Materiales, compras, corte y taller se abren desde el objeto y revisión correspondientes. Cada rol ve su acción permitida y el responsable del paso que no puede ejecutar.

Este recorrido debe funcionar con la IA deshabilitada, sin credenciales de modelo y con los derechos de IA vencidos. Conservar los permisos empresariales y las reglas comerciales existentes; no regalar por accidente capacidades administrativas de otro rol al habilitar la base manual.

## Dos composiciones, una aplicación

Mesa y Estudio cambian la distribución del espacio, no la verdad del proyecto. Mesa prioriza colección, excepciones y preparación comercial; Estudio prioriza posición, dibujo y configuración. No mantener dos implementations divergentes de aperturas, cotización, documento ni operaciones.

La selección de lista/grilla o galería/tabla sigue siendo un control local de colección. No es el nuevo selector Mesa/Estudio. Cambiar la vista debe conservar el enlace a la posición y el retorno a la colección. Los detalles de URL, preferencias y migración están en el [contrato de producto](01-producto-y-dos-vistas.md).

Un borrador se identifica por usuario, organización, obra y posición cuando corresponda. Un job captura su destino al enviarse: navegar a otra obra no redirige una operación que ya está en marcha. El hilo puede seguir abierto sin que su destino cambie silenciosamente.

## Copiloto que sabe ponerse en lugar del usuario

El botón Asistente y el atajo global abren el mismo popup. La ruta actual aporta contexto, pero no crea una conversación diferente. El popup puede minimizarse, cerrarse o ampliarse; el trabajo continúa con estado visible y recuperable. En móvil puede ocupar una hoja o pantalla voluntariamente abierta, manteniendo retorno al trabajo.

En Chat, la IA responde y prepara propuestas; no aplica cambios por interpretar una frase como delegación. Trabajo usa herramientas de dominio del sistema. En Omitir todo la petición de la persona autoriza el alcance reversible del encargo; el agente resuelve lo derivable, ejecuta y al final indica objetos afectados, cambios y pendientes. Una falta imprescindible se pregunta agrupada, con el estado real de espera; no se marca Terminado.

La IA puede abrir destinos de la aplicación y ejecutar sus funciones autorizadas. No necesita un controlador genérico del ordenador, acceso al código ni credenciales de pago para parecer capaz. Las operaciones compartidas de backend son más fiables y auditables. Si alguna tarea todavía no está implementada, decirlo y entregar trabajo parcial comprobable; no responder con enlaces fingiendo que se ejecutó.

El alcance mínimo de implementación del copiloto queda cerrado en tres recorridos: documento/listado o plano con cotas explícitas a posiciones y borrador canónico; cambios por encargo sobre ventanas; comparación de revisiones compatibles y propagación de sus diferencias a un borrador editable. Se construyen en 05 y se comprueban en 07. Marcar un extra como no disponible es correcto; usar esa etiqueta para omitir estos tres no completa el encargo. Las tarifas y asignación comercial no se activan por desarrollar los recorridos.

## Profesionalidad medible

Cada pantalla debe permitir reconocer qué se está editando, qué está guardado, cuál es la acción principal, qué falta y cuál es el siguiente paso. La limpieza no consiste en eliminar información necesaria ni volver todos los controles del mismo color.

| Before | After | Why |
|---|---|---|
| Panel IA que desplaza inspector y lienzo. | Popup opcional con foco y retorno definidos. | Mantiene el trabajo manual como primera experiencia. |
| Tarjetas y botones con el mismo peso. | Acción primaria de la tarea, secundarias delimitadas y comandos contextuales. | Hace visible la consecuencia de cada control. |
| Lista de versiones DEMO como biblioteca normal. | Marca → serie → configuración/artículo, con imagen técnica y fuente. | Permite reconocer productos y saber qué se puede usar. |
| «Lista» o «Completado» sin alcance. | Estado referido a guardado, cálculo, cotización, fabricación o tarea. | Evita confundir éxito visual con resultado técnico. |
| Precio ausente parecido a cero. | Pendiente o Sin dato con causa y acceso a resolver. | Evita decisiones económicas falsas. |
| Cotización encerrada entre paneles. | Documento legible como objeto principal al revisarlo. | Permite juzgar la propuesta que recibirá el comprador. |
| Vacío en Corte sin salida útil. | Requisito, revisión, responsable y acción autorizada. | El usuario entiende cómo continuar según su rol. |
| Opciones sugeridas como decoración del chat. | Compositor sobrio, contexto explícito y recibo verificable. | El asistente reduce trabajo en lugar de añadir ruido. |

El [contrato de diseño](02-diseno-y-referencias.md) define anatomías, roles de color, tipografía, controles y estados. Los valores son una especificación de construcción que Claude debe comprobar en el producto real; no una aprobación estética anticipada del dueño.

La ampliación de [referencias profesionales](05-referencias-profesionales.md) conecta veinte fuentes con decisiones sobre tipografía, selección, inspector y documentos. El [contrato del personaje](06-grok-bot-personaje-y-movimiento.md) sustituye la figura actual de placa facial por una reconstrucción fiel a la gramática de Grok Bot, con estados reales, movimiento interrumpible y reduced motion. La restricción de transiciones cortas del resto de la UI no aplana sus ciclos expresivos.

## Referencias que sí cambian decisiones

| Fuente de aprendizaje | Aplicación en DEKOPEN | Límite de la referencia |
|---|---|---|
| Logikal, PrefSuite, RA Workshop | Selección, etapas de configuración, datos por proveedor y preparación de series. | Manuales y material oficial; no sesión privada ni algoritmo copiado. |
| Klaes, FeneVision, A+W Cantor | Continuidad entre obra, pedido, dato técnico y operación. | Capacidad documentada no demuestra todos los permisos ni su rendimiento. |
| V6 Advantage y Winart | Separar propuesta comercial, elevación, sección y plan del taller. | Fotogramas/capturas no prueban exactitud de fabricación. |
| Matrix, Windowmaker, WindowCC/WindoorCraft | Incorporación de datos, interacción directa y contexto del asistente. | REA público parcial no recupera lógica industrial privada. |
| 3E LOOK, NuveraPRO, WinMaker 10 | Trabajo por excepción, proveedor local y comparación de alternativas. | No hay benchmark homogéneo para declarar una clasificación global. |

Las fuentes concretas y sus etiquetas DOC/VIS/RUN/NV están en la [síntesis competitiva](../2026-10-18-revision-profunda/sintesis-competitiva.md), [matriz](../2026-10-18-revision-profunda/matriz-completa.md) y [evidencia visual](../2026-10-18-revision-profunda/evidencia-visual.md). No convertir estas referencias en una lista de módulos nuevos que duplique lo que ya existe.

## Catálogo real sin atajos falsos

Priorizar Proline con el material aportado, manteniendo PRO6004 y PROSLIDE70 como series distintas. Completar primero un alcance real que se pueda revisar, cotizar y verificar. Incorporar otra familia PVC/aluminio según evidencia disponible, sin prometer fabricación de todas las marcas por disponer de folletos.

La biblioteca puede mostrar una serie como referencia con sección y fuente aunque todavía le falte una regla. Ese estado no satisface la aceptación de una cotización real publicada. Si falta un dato de fabricante o costo privado, registrar el faltante exacto y el trabajo listo para resolverlo. Los ejemplos Proline de corte no son fórmulas generales; no generalizarlos ni silenciar errores del documento.

Separar demos del recorrido normal con filtros/capacidades y conservar referencias antiguas. No borrar el tenant, renombrar series sintéticas como marcas ni destruir las revisiones que las usan. Más detalle en [catálogos reales](../2026-10-18-revision-profunda/catalogos-reales.md).

## Desarrollo acotado a esta versión

El encargo reutiliza el producto existente y termina sus recorridos. No migra Django a Rails, no reinventa billing ni inventa condiciones comerciales. Los USD 39/69/149 del brief son antecedentes, no tarifas nuevas aprobadas para cobrar. Los derechos de los planes se desacoplan de la apariencia y de las autonomías; la contratación y configuración final de proveedores de cobro quedan documentadas para el dueño.

El [contrato de créditos](04-planes-creditos-y-limites.md) distingue cupo de servicio, packs, saldo retenido/gastable y presupuesto operativo. El código debita hoy un coste fijo de ruta; la fórmula por coste real del PRD no se presenta como implementación actual. Preparar cuotas proporcionales y reservas correctas no activa nuevos precios ni cambia retroactivamente el ledger. Los tres recorridos obligatorios y MiMo son comunes a todos los planes con IA.

Reconciliar `docs/PRODUCT.md` y las cláusulas de Constitución que exigen IA central/acoplada o DEMO como experiencia inicial. Mantener motor/Decimal/RLS/inmutabilidad/idempotencia/clic humano, accesibilidad y datos desconocidos visibles. No usar un documento histórico para revivir decisiones rechazadas.

## Cierre esperado

Claude entrega todo el alcance funcional integrado y una app en ejecución como **candidata definitiva para revisión**, con los archivos y el procedimiento de puesta en producción preparados. Solo pueden quedar pendientes las conexiones/configuración finales de **Railway, Supabase y pagos**. Persistencia, auth/RLS, lógica de pagos/créditos y copiloto real son parte de la construcción, no trabajo aplazable bajo el nombre de integración.

01–06 desarrollan; 07 verifica y corrige ambos modos manuales y los planes con IA. El dueño revisa y aprueba esa versión ejecutable; después se realizan las conexiones finales, las pruebas de lanzamiento y las correcciones necesarias antes de publicar. No se acepta una presentación de demos ni otra fase pendiente de desarrollo funcional. Si falta una fuente o función obligatoria, la entrega sigue incompleta y debe identificar el bloqueo real. El dueño no debe deducir qué quedó conectado ni qué servidor contiene los cambios. El [prompt maestro](prompt-maestro.md) define el alcance por servicio y exige `production-handoff.md` con pasos exactos, sin secretos.
