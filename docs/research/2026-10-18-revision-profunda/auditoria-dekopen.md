# Auditoría de DEKOPEN actual

Verificado el 18-10-2026 en `claude/v1-implementacion`, árbol local con cambios de Claude. Web REVIEW `http://127.0.0.1:5179`, sesión estimator de Ventanas del Sur. Es una revisión funcional acotada; no una aceptación integral de la rama.

## Evidencia y hallazgos

| ID / prioridad | Hecho verificado | Implicación y límite |
|---|---|---|
| A01 · alta | El asistente se abre desde cabecera en varias páginas y permanece abierto al navegar. | La presencia global ya existe; debe mejorarse su continuidad, no reconstruirse como página aislada. |
| A02 · alta | No hay selector visible Chat/Trabajo ni los tres niveles pedidos; aparece un checkbox “Hacer los cambios que pida” junto al texto de confirmar cambios. | Semántica contradictoria. Separar intención de autonomía y declarar qué ocurrirá antes de ejecutar. |
| A03 · alta | `/assistant` muestra trabajos de hace horas y días con transcripciones. El panel restaura el job más reciente de cada contexto. | **Existe persistencia.** Falta conversación independiente de la ruta y acceso evidente al historial desde el panel. |
| A04 · crítica de producto | Job `351f5c85-dfc3-4cc1-a464-983f824ac3ac` figura Completado, pero la transcripción deja agregar tres ventanas y calcular precio como pendientes. La obra P-000019 aparece con 0 ventanas en la lista. | Completado describe fin de respuesta/proceso, no satisfacción del objetivo. No se afirma que haya una cotización emitida ni un cálculo numérico incorrecto. |
| A05 · alta | Ese encargo declara que “efa” quedó como dato de obra, sin ficha de cliente vinculada; el usuario había pedido crear cliente. | Las postcondiciones deben distinguir texto en cabecera de entidad creada. El cierre requiere comprobar ambos objetivos. |
| A06 · media | La respuesta pide medidas/vidrio/acabado y también muestra descartes de afirmaciones, límite de consultas y avisos técnicos extensos. | Pedir dimensiones ausentes es legítimo. Debe consultar preferencias, agrupar faltantes y traducir límites operativos a una acción útil; no ocultar validación. |
| A07 · alta | Catálogos presenta una lista plana dominada por versiones DEMO; fabricante es prefijo textual. | No hay biblioteca de fabricante → serie reconocible. No significa ausencia de datos ni de todas las imágenes en código. |
| A08 · alta | La ficha inspeccionada mezcla Activo, Listo, DEMO y autoridad de proceso sin vincular. | Separar estado administrativo y preparación por uso. Una fórmula sintética no se convierte en regla de fabricante. |
| A09 · acotado | En proyecto borrador P-000015, posición `46af75f2-5659-474b-ae75-e357c17577a0`, abrir la paleta y elegir abatible con bisagras a derecha cambió dibujo, nombre e inspector; el motor volvió a Válido. | Una apertura compatible sí funciona. No descarta otro bug de selección, catálogo o familia. No se probó toda la matriz de aperturas. |
| A10 · acotado | Deshacer restauró izquierda, Guardado y resultado válido. No se pulsó Guardar. | La prueba fue reversible y no dejó cambios persistidos en esa posición. No demuestra undo tras recarga. |
| A11 · alta UX | Casa del patio figura Borrador, pero avisa que precio aplicado bloquea vanos. Código también impide edición en revisión sellada/no DRAFT y en pantallas menores de 1024 px. | Son causas distintas; no presentar todas como “no funciona”. Diseñar recuperación por revisión y explicar lectura en pantallas pequeñas. |
| A12 · media | En el editor de dos módulos la vista frontal aparecía al 19 %, con planta e inspector consumiendo gran parte de la pantalla. | La adaptación debe reservar dibujo útil y enfocar la selección. Esta captura no mide todas las resoluciones. |
| A13 · alta UX | En OT `5a00fae3-a88e-4ebc-bfbe-6a5cba6bf49c`, Corte dice “Optimiza para calcular barras y planchas”, sin botón de optimización visible en ese rol. Resumen indica que debe hacerlo el jefe. | La página debe explicar responsable y siguiente acción permitida. No se interpreta como ausencia de optimizador en el sistema. |
| A14 · media | Esa OT muestra “Listo” en el paso Corte, 0/6 pasos y falta de plan vigente. | Puede significar preparado/seleccionado, no terminado. La redacción necesita estados inequívocos por requisito. No se cambió ninguna estación. |
| A15 · media | El tablero de la fixture muestra 175 OT sin plan de corte y columnas vacías; son datos sintéticos. | Hace falta una revisión con escenario real pequeño, además del caso masivo. Esa cifra no prueba un fallo de fábrica ni se usa como KPI del producto. |
| A16 · alta | Ya existen pestañas Materiales y corte, órdenes/stock/terreno, motivos de bloqueo y controles de privacidad en arquitectura. | Aprovechar capacidades presentes; reorganizar y completar recorridos sin reemplazar lógica válida con un mockup. |

## Revisión de interfaz: cambio y propósito

| Before | After | Why |
|---|---|---|
| Mascota grande, panel con mucho vacío y sugerencias extensas. | Cabecera pequeña, conversación y resultado como contenido principal; sugerencias discretas y prescindibles. | La atención debe estar en la tarea y lo que produjo. El dueño rechazó expresamente el asistente actual. |
| Checkbox de autonomía y texto de confirmación ambiguos. | Chat/Trabajo separados de Solo proponer/Con aprobación/Omitir todo. | El usuario debe anticipar si va a conversar, preparar o ejecutar. |
| Historial disponible en una ruta poco evidente. | Acceso visible “Conversaciones”, reanudación desde el mismo panel y espacio propio. | La persistencia que no se puede encontrar se percibe como pérdida. |
| Cambiar ruta remonta `AgentBody` por contexto. | Conversación con ID estable y destino de trabajo explícito. | Navegar no debe equivaler a empezar otra conversación. |
| Completado con objetivos pendientes. | Esperando datos / Parcial / Terminado, derivados de postcondiciones. | Evita delegar una tarea y descubrir que no se hizo. |
| Lista de sistemas con versiones duplicadas y fabricante como texto. | Entrada por fabricante, series dentro y archivo de versiones separado. | Permite encontrar Proline y entender qué pertenece a cada marca. |
| Activo, Listo y DEMO juntos. | Disponible / Apto para cotizar / Apto para fabricar / CNC, con causa. | Separa disponibilidad, evidencia y consecuencia. |
| Botones secundarios, selección y bordes con énfasis parecido. | Acción principal sólida, edición con borde reconocible, selección teñida y contorneada, aviso con texto y causa. | El color debe explicar función; añadir saturación por todas partes volvería a confundir. |
| Dibujo pequeño al dividir espacio entre frontal, planta e inspector. | Canvas predominante; planta plegable/contextual, inspector por selección y zoom ajustado. | La ventana vuelve a ser el objeto de trabajo. |
| Estado vacío “Optimiza” sin acción para el rol actual. | Acción autorizada o responsable y camino concreto; conservar el requisito técnico. | El permiso correcto no debe convertirse en un callejón sin salida. |
| Siglas, SKUs y detalles del modelo mezclados con la respuesta. | Resultado en lenguaje de taller; detalle técnico expandible a un clic. | Se preserva trazabilidad sin convertir la conversación en log técnico. |

## Receta reproducible de apertura

1. Abrir `/projects/5a10069e-efdf-4837-bcae-1acef71df3b2` y la primera posición de la fixture.
2. Confirmar Borrador, sin precio aplicado y ancho de escritorio. La posición tiene dos módulos; elegir el primero.
3. Inspector → Apertura → “Abatible hacia adentro — bisagras a la derecha”.
4. Esperar al motor: el primer paño cambia a derecha, el segundo conserva izquierda, y aparece Válido.
5. Deshacer: ambos vuelven al estado anterior y la cabecera indica Guardado. Salir sin Guardar.

Capturas: [cambio de mano](../../../.run/revision-profunda/capturas/dekopen-apertura-derecha.png), [historial](../../../.run/revision-profunda/capturas/dekopen-historial.png), [completado con pendientes](../../../.run/revision-profunda/capturas/dekopen-completado-con-pendientes.png), [catálogos](../../../.run/revision-profunda/capturas/dekopen-catalogos.png), [taller](../../../.run/revision-profunda/capturas/dekopen-taller.png), [corte](../../../.run/revision-profunda/capturas/dekopen-corte-sin-accion.png). Las capturas son evidencia local temporal; el índice visual conserva huellas y URLs.

## Código que explica los comportamientos

- `frontend/src/features/assistant/AskDekopen.tsx`: presencia global y clave del cuerpo por contexto.
- `frontend/src/features/assistant/AgentBody.tsx:246`: autonomía `draft|propose`; `:367`: limpia thread y consulta `aiPresenceGet` por `surface/refs`; los fallos de restauración quedan sin mensaje de recuperación.
- `frontend/src/features/assistant/AssistantWorkspacePage.tsx`: lista y transcripciones duraderas; `frontend/src/App.tsx:478`: ruta `/assistant`.
- `frontend/src/features/catalogs/CatalogPage.tsx:278`: filtro/lista de sistemas; `:365`: fabricante como prefijo. No es un árbol de marcas.
- `frontend/src/features/projects/ProjectPositionEditor.tsx:97`: bloqueo por revisión/precio; `:345` y `:1091`: lectura bajo 1024 px con aviso.
- `frontend/src/features/canvas/AssemblyEditor.tsx:1131`: paleta física cuando hay capabilities; fallback legado si no. `physicalOpenings.ts:204` filtra opciones desde datos de capacidad.
- `backend/ai_gateway/agent.py`: herramientas y validación tipadas; la ampliación de autonomía exige contrato y runtime, no solo cambiar el texto de un selector.

## Qué no fue probado aquí

No se probó cada apertura, QR con cámara, lector físico, CNC en máquina, importación/publicación real de Proline ni flujo completo de cobro/emisión/compra. No se lanzó una batería nueva de tests porque esta fase produce investigación y propuestas. Los tests adecuados se exigen a la implementación posterior.

El stack ya se había reconstruido para mostrar cambios de Claude. Antes de esta investigación se resolvió una colisión local de historial migratorio y se añadió `supabase/migrations/20270130000400_v1_project_read_grants.sql` para lectura de dos columnas nuevas en proyectos, manteniendo RLS. Proyectos/materiales devolvieron HTTP 200 en ese smoke. Ese arranque limitado no acredita aceptación funcional completa ni forma parte del rediseño propuesto.
