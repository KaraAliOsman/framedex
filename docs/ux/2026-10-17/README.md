# DEKOPEN · Plan de experiencia de producto

**17 de octubre de 2026 · Investigación, reconstrucción y verificación de la experiencia.**

**Estado: implementación autorizada con «ahora empieza» y construida en
`codex/v1-experiencia`. La segunda dirección reemplaza la apariencia rechazada
por el dueño.** El [registro vigente](11-reconstruccion.md) contiene P13–P20,
construcción, campaña de cierre, evidencia y límites. El
[registro anterior](10-implementacion.md) y los capítulos 01–09 conservan la
primera implementación, investigación y plan; no describen automáticamente el
build nuevo ni acreditan su aceptación.

Los diagnósticos y observaciones de auditoría que siguen describen el punto de
partida. Para el comportamiento construido y sus límites actuales manda el
registro 11; no se presentan los defectos iniciales como fallos aún vigentes.

## La conclusión

DEKOPEN ya tiene una base funcional extensa, pero obliga al usuario a recorrer su
estructura interna para hacer un trabajo sencillo. La ventana, el precio y la
siguiente acción quedan detrás de navegación, estados, formularios y explicaciones.
El dibujo tampoco comunica la calidad física que el sistema pretende tener.

La solución propuesta es **reconstruir la experiencia alrededor de la ventana y
del trabajo de cada persona**: empezar a diseñar inmediatamente, heredar decisiones
repetidas, editar sobre el dibujo, entender el precio, preparar una propuesta y
continuar a taller sin volver a introducir los datos. La profundidad técnica se
conserva y aparece cuando sirve para tomar una decisión.

Cambiar colores, redondear tarjetas o instalar más skills no resolverá esa estructura.
El diseño de interacción, la calidad del catálogo y la representación física tienen
que avanzar juntos.

## Cómo leer el plan

| Documento | Para qué sirve |
|---|---|
| [01 · Auditoría y evidencia](01-auditoria.md) | Qué se observó, qué confirma el código, qué sobra, qué falta y qué sigue sin verificarse. |
| [02 · Competencia y fuentes](02-competencia.md) | NuveraPRO, Winart, Moxisys y Logikal, vídeos con tramos observados, matriz de capacidades y referentes adicionales. |
| [03 · Experiencia objetivo](03-experiencia.md) | Navegación, flujos, editor, formularios, tema único, lenguaje y comportamiento por dispositivo. |
| [04 · Ventanas y materiales visuales](04-representacion.md) | Uniones, secciones, acabados, vidrio, iluminación, vistas y coherencia entre pantalla y documentos. |
| [05 · IA y catálogo desde PDF](05-ia-catalogos.md) | Asistente que trabaja, pocas preguntas, deshacer, ingesta multimodal, revisión por excepciones y publicación. |
| [06 · Documentos y operación](06-documentos-operacion.md) | Cotización, materiales, corte, montaje, etiquetas, compras, inventario, planta y terreno. |
| [07 · Hoja de ruta y método](07-ejecucion.md) | Orden de implementación, dependencias, skills, objetivos y una campaña de pruebas al final. |
| [08 · Prompts listos](08-prompts.md) | Prompt maestro y doce encargos originales; consultar el estado antes de continuar. |
| [09 · Láminas de dirección visual](09-direccion-visual.html) | Propuesta documental de editor, importación y cotización. Es una maqueta, no una funcionalidad implementada. |
| [Evidencia seleccionada](evidencia/README.md) | Capturas propias, procedencia y límites. |
| [10 · Implementación y cierre](10-implementacion.md) | Cambios construidos, pruebas, evidencia y pendientes reales. |
| [11 · Segunda reconstrucción](11-reconstruccion.md) | Rechazo de la primera dirección, referencias Grok Bot/Dots, prompts P13–P20 y nueva implementación. |

## Decisiones de dirección propuestas

1. **Una sola apariencia clara, neutra y cuidada.** Fondo de trabajo ligeramente
   cálido, hoja blanca, texto oscuro y un acento contenido. Se elimina el selector
   de temas de la experiencia objetivo. La calidad se concentra en una dirección.
2. **El producto ocupa el centro.** Crear o abrir una ventana debe llevar al dibujo;
   editar una cota o una apertura debe actuar ahí mismo.
3. **El borrador empieza sin trámites.** Cliente, dirección y condiciones completas
   se solicitan cuando se necesitan para una propuesta, un envío o una orden.
4. **El sistema recuerda.** Serie, vidrio, acabado y condiciones se heredan del
   proyecto, con excepciones visibles y edición por lote.
5. **La IA hace el trabajo reversible.** Una petición explícita y acotada se aplica
   con una explicación breve y Deshacer. Un cambio amplio muestra una vista previa
   útil. Enviar, emitir, comprar o liberar conservan el clic humano correspondiente.
6. **Subir un PDF es el camino principal del catálogo.** La aplicación reconoce,
   extrae, relaciona y prepara; la persona resuelve únicamente dudas reales. La
   plantilla queda como herramienta secundaria para especialistas.
7. **Una ventana debe parecer construible.** Uniones correctas, perfiles legibles,
   textura con dirección y escala, caras interior/exterior y apertura coherentes.
8. **Cada documento se diseña para su destinatario.** Cliente, corte, armado,
   acristalamiento, compras e instalación necesitan composiciones diferentes.
9. **Ocultar complejidad no significa perder control.** Datos técnicos, historial,
   permisos y procedencia permanecen accesibles en el contexto adecuado.
10. **Construcción orientada a calidad; pruebas al final.** Se evita la sucesión de
    gates, suites y reportes por cada ajuste. La inspección del diseño mientras se
    construye sirve para diseñar. La campaña de aceptación y corrección de bugs
    se concentra al terminar la integración.

La apariencia clara fue la recomendación del estudio adoptada durante la
implementación autorizada. La decisión explícita del dueño es tener **un tema
definitivo**; no se le atribuye haber elegido cada token o composición.

## Prioridades que más cambiarían la experiencia

| Orden | Resultado visible | Qué resuelve |
|---|---|---|
| 1 | Obra y editor directos, con decisiones heredadas | «Soy profesional y no entiendo cómo hacer una ventana». |
| 2 | Ventanas convincentes en 2D/3D y acabados reconocibles | Sensación de demo genérica y falta de confianza visual. |
| 3 | IA contextual con acciones breves y reversibles | Pedir a la IA resulta más trabajoso que hacerlo manualmente. |
| 4 | Catálogo desde PDF con revisión visual por excepciones | Configuración excesivamente técnica y manual. |
| 5 | Cotización y documentos de taller rediseñados | Resultado comercial pobre e instrucciones difíciles de usar. |
| 6 | Operación por tarea, rol y excepción | Compras, stock y planta muestran datos sin orientar el trabajo. |

Las fases de implementación no son independientes: el catálogo alimenta los
renderizados, la IA, los precios y la fabricación. La [hoja de ruta](07-ejecucion.md)
explica cómo trabajar con un conjunto pequeño de productos representativos antes
de extender la calidad al sistema completo.

## Evidencia que cambia las decisiones

- El proyecto observado dedica el primer viewport a cabecera, fases, pestañas y
  controles; las ventanas empiezan más abajo. [Captura](evidencia/proyecto.jpg).
- En 3D, el acabado Nogal observado aparece como marrón plano. El renderer admite
  texturas, pero la existencia del selector no garantiza una textura disponible
  ni un mapeo correcto. [Captura](evidencia/editor-3d.jpg).
- El código del renderer 3D trata expresamente los extremos como rectos y deja
  el inglete fuera de la representación. El SVG 2D sí tiene lógica de uniones:
  hay que mejorar la representación, no afirmar que no existe ninguna unión.
- Una petición real de IA para cambiar solo el ancho propuso correctamente
  1 000 → 1 200 mm y mantuvo el alto; añadió una ceremonia de trabajo/aprobación
  y una advertencia térmica poco relevante para esa tarea.
  [Captura](evidencia/ia-cambio-simple.jpg).
- El importador muestra plantilla y revisión técnica antes de comunicar una
  experiencia «sube el PDF». La pasarela ya envía imágenes/páginas sin texto a
  visión, pero limita PDF a 20 páginas y prioriza texto sobre imagen por página.
  Falta una lectura integral de layout, planos, tablas y relaciones.
- En una OT existente de cuatro unidades fijas, el paquete completo renderizado
  tiene 24 páginas; su plano de ensamblaje corta y superpone identificadores.
  El documento específico de corte es más aprovechable y merece conservarse.
  [Plano observado](evidencia/pdf-ensamblaje.png).

## Alcance y honestidad de la investigación

Se combinaron navegación real con roles de estimación y taller, capturas, una
petición real a la IA, lectura de código de las rutas afectadas, documentos
existentes y renderizados de taller sobre un plan existente. También se revisaron
fuentes públicas de proveedores y tramos de vídeos de los cuatro competidores
principales. No se crearon cuentas comerciales ni se enviaron formularios de demo.

**Código de referencia:** `edcfd2844d2c2fc7cbb0d3b543b50e9089ab9b3f`, rama
`codex/limpieza-repositorio`. El stack REVIEW reutilizado tiene un build cuyo SHA
no se verificó. Una observación del stack se etiqueta como tal y no se atribuye
automáticamente a ese commit.

No se hizo una prueba exhaustiva de todas las pantallas, permisos y dispositivos.
Los vídeos se observaron por tramos, no íntegramente. Las funciones públicas de un
proveedor no demuestran su calidad real, su edición contratada ni una capacidad
que no se haya mostrado. La [matriz](02-competencia.md) distingue observado,
documentado, comercial e incógnita. No se presenta una ausencia de evidencia como
ausencia del producto.

El inventario funcional del 12-10-2026 ayuda a cubrir todos los dominios del plan;
sus aceptaciones y métricas de IA siguen siendo históricas. Este estudio no las
convierte en una evaluación nueva.

## Qué significa «el mejor» en este plan

Que un profesional consiga su trabajo con menos decisiones innecesarias y entienda
lo que está construyendo; que un cliente vea una propuesta convincente; y que el
taller reciba instrucciones precisas, legibles y consistentes. Los resultados se
medirán en tareas reales, no por número de pantallas, módulos, prompts o capturas.

**Todavía no hay una promesa de superioridad demostrada frente a todos los
competidores.** Hay una dirección y un programa concreto para conseguir una
experiencia mucho más sencilla y de mayor calidad.
