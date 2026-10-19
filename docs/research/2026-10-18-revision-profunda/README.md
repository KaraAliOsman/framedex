# DEKOPEN: revisión profunda y tres direcciones para elegir

> **Decisión posterior del dueño:** conservar **Mesa de obra + Estudio** como dos vistas del producto manual; IA opcional en **popup global**. La elección pendiente y el asistente acoplado de este dossier quedan superados. Usar el [paquete final](../2026-10-18-direccion-final/README.md) y su [prompt maestro](../2026-10-18-direccion-final/prompt-maestro.md). Esta investigación y sus evidencias siguen siendo consultables; los mocks no son diseño aprobado.

18 de octubre de 2026 · dossier de la fase previa a la elección. La selección estructural posterior está en el aviso anterior; las apariencias de los mocks siguen sin aceptación.

El problema principal es la continuidad del trabajo: reconocer qué ventana se modifica, qué catálogo la respalda, qué hizo la IA y qué falta para terminar. Cambiar colores sin resolver eso produciría otra versión visualmente distinta con los mismos problemas.

La investigación reúne **15 familias de producto independientes, 18 ejes comunes y 270 casillas**, más Moxisys como canal de WindoorCraft. El índice competitivo contiene **176 URLs únicas**. Hay capturas de páginas, interfaces publicadas, fotogramas de tutorial, páginas de PDF y evidencia REA. Se separan material comercial, documentación, píxeles observados y ejecución real. No se afirma haber operado quince suites privadas ni haber visto todos sus vídeos.

## Qué revisar primero

[Comparar las tres propuestas](http://127.0.0.1:5188/propuestas-preview.html) · [Galería de 28 referencias](http://127.0.0.1:5188/galeria.html) · [App actual en ejecución](http://127.0.0.1:5179). Los enlaces requieren los servidores locales de esta entrega. La comparación es un concepto interactivo, no el rediseño aplicado al producto.

1. [Tres direcciones de producto](tres-direcciones.md): **Estudio**, **Mesa de obra** y **Centro de encargos**. La recomendación es **Mesa de obra**, con editor amplio y asistente persistente; la elección sigue siendo del dueño.
2. [Auditoría de la app actual](auditoria-dekopen.md): hallazgos reproducidos, límites y cambios propuestos con su porqué.
3. [Contrato del asistente](contrato-asistente.md): Chat/Trabajo, historial y **Solo proponer / Con aprobación / Omitir todo**.
4. [Catálogos reales](catalogos-reales.md): Proline, Winhouse y aluminio; marca → serie → configuración → artículos, con fuentes y preparación técnica separadas.
5. [Prompt para Claude](prompt-claude.md): instrucciones listas para usar **después de elegir una dirección**, entregables completos y aceptación verificable.

## Investigación para consultar por tema

| Documento | Contenido |
|---|---|
| [Método y rúbrica](metodologia-rubrica.md) | Pregunta, evidencia necesaria, ponderación propuesta y prueba por cada eje. |
| [Síntesis competitiva](sintesis-competitiva.md) | Qué aprender de cada familia; decisiones de producto e ideas nuevas. |
| [Matriz completa](matriz-completa.md) | Las 15 empresas comparadas con el mismo orden y casillas detalladas. |
| [PVC](competidores-pvc.md) | Klaes, PrefSuite y RA Workshop: 54 filas y fuentes por afirmación. |
| [Ingeniería](competidores-ingenieria.md) | Logikal, SchüCal, V6 Advantage y A+W Cantor: 72 filas. |
| [Operación](competidores-operacion.md) | FeneVision, Matrix, Windowmaker, WindowCC, 3E LOOK y el canal Moxisys. |
| [Referencias locales](competidores-locales.md) | NuveraPRO, Winart y WinMaker 10: 54 filas. |
| [Evidencia visual](evidencia-visual.md) | Capturas seleccionadas, origen, fecha, observación y límite. |
| [REA](rea-evidencia.md) | Qué se capturó/analizó, huellas, hallazgos y lo que no se pudo demostrar. |
| [Fuentes](fuentes.md) | Índice de enlaces; [JSON](fuentes.json). |
| [Matriz estructurada](matriz-competitiva.json) | 18 ejes y 24 dimensiones; los punteros de grupo no se presentan como pruebas independientes. |

## Conclusiones que cambian el encargo

- **El historial existe**, pero cuesta descubrirlo y el panel se vuelve a asociar por página/contexto. Hace falta una conversación persistente que pueda trabajar sobre varios objetos.
- **Completado no puede significar solamente que acabó la respuesta del modelo.** Se observó un encargo marcado así con ventanas y precio pendientes.
- **Una apertura sí cambió de izquierda a derecha** en el borrador de revisión y se restauró con Deshacer. El caso concreto denunciado por el dueño sigue pendiente de reproducción. Hay bloqueos distintos por precio aplicado, ancho de pantalla, cálculo y compatibilidad.
- **Catálogos no está vacío en datos**: está dominado por sistemas DEMO y una lista plana. Lo que falta es una biblioteca reconocible de marcas, series y configuraciones reales, junto a su evidencia y estado.
- La competencia ya documenta IA contextual. La ventaja debe ser **terminar tareas con evidencia y pocas interrupciones**, no añadir más sugerencias al chat.
- QR, optimización y taller necesitan identidad de pieza, revisión, rol y siguiente acción. No son una colección de botones intercambiables.

## Alcance de esta revisión

Referencia: rama `claude/v1-implementacion`, árbol con cambios locales extensos de Claude, revisión del producto en `http://127.0.0.1:5179`. El informe es una fotografía fechada; la wiki y la aceptación del 12 de octubre no prueban el estado de esta implementación.

En esta fase se escribieron investigación, evidencia temporal y propuestas. No se implementaron las tres alternativas, no se borraron demos, no se publicaron catálogos, no se emitieron documentos ni se modificó una orden de fabricación. La prueba local de apertura fue reversible, sin Guardar y restaurada. El arranque/reparación local previo queda documentado aparte en la auditoría.

Los ejemplos de las propuestas sirven para evaluar organización y diseño. No son resultados calculados ni sistemas homologados. Este dossier tampoco es una declaración de producto listo para fabricación o despliegue.
