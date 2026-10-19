# Prompt 02 — Cotizador manual y dos vistas del mismo proyecto

Implementa esta fase después de `01-fundamentos.md`. No es un nuevo estudio de alternativas: el dueño ya decidió que **Mesa de obra y Estudio conviven como dos vistas elegibles** y que el producto principal funciona completamente sin IA. Continúa sobre los cambios existentes; no rehagas el repositorio ni sustituyas sus capacidades por una maqueta.

## Resultado que debes construir

DEKOPEN permite crear y gestionar una cotización manual desde Mesa de obra y diseñar sus ventanas desde Estudio. Ambas muestran la misma obra, posiciones, revisión, selección y autoridades técnicas/comerciales. Cambiar vista, ampliar el editor o volver de él conserva el trabajo y no guarda ni recalcula por una ruta distinta. Mesa es la entrada predeterminada; la elección se recuerda por usuario y organización.

La IA no es la portada, no crea la obra por defecto, no forma una columna del cotizador y no reserva espacio al estar cerrada. El futuro popup global opcional se implementa en su fase; aquí no añadas otra interfaz de chat ni controles de créditos a los pasos manuales. No reincorpores el «Centro de encargos» de los documentos anteriores.

## Antes de editar: lectura acotada y autoridad

1. Inspecciona `git status --short`, rama y ref. Conserva los cambios locales del dueño/Claude. No uses reset/checkout destructivo ni limpies `.run/` para empezar.
2. Lee `AGENTS.md`, `docs/ENGINEERING.md`, `docs/design/CONSTITUCION.md` ya alineada por 01 y `docs/wiki/index.md`. Sigue solo las rutas de proyecto/editor/precio pertinentes.
3. Lee completos `docs/research/2026-10-18-direccion-final/01-producto-y-dos-vistas.md` y este prompt. La corrección del dueño sustituye las referencias históricas a asistente incrustado. No reabras la elección de concepto, paleta o nombres.
4. Inspecciona `frontend/src/features/projects/ProjectPages.tsx`, `PositionCollection.tsx`, `ProjectPositionEditor.tsx`, `useProject.ts`, `ProjectOpsReview.tsx`, `QuotationGlobalChanges.tsx`, `DesignDefaults.tsx`, `ProjectPositionLibrary.tsx`, `positionDraft.ts`; `frontend/src/App.tsx`, `frontend/src/app/navigation.ts`, `UnsavedChangesGuard.tsx`; `frontend/src/features/canvas/canvasStore.ts` y `canvasSession.ts`.
5. Para contratos, revisa `backend/projects/service.py`, `project_ops.py`, `ops_registry.py`, `urls.py`, y las funciones generadas que usan esos componentes. No edites `frontend/src/api/generated/` a mano. Si cambia API, comienza en serializers/views y regenera OpenAPI/orval por el flujo del repositorio.

La inspección base del 18-10-2026 encontró HEAD `6f78e3299d93816991fb7c2fe2a2044458fc5e7a` más un árbol amplio de cambios. Revisa la versión que recibes, porque puede ser posterior; no reviertas una mejora nueva para coincidir con una captura anterior.

## Lo que ya existe y debes aprovechar

- `useProjectView` y `projectKey(orgId,id)` comparten la lectura del proyecto entre shell, cabecera y contenido.
- `ProjectPages` organiza Ventanas, Cotización, Materiales y corte, Actividad; mantiene formularios visitados y usa `section` en query. No hace falta volver a construir todos sus paneles.
- `PositionCollection` ya ofrece galería/tabla, filtros, agrupación, multi selección, teclado, virtualización, duplicación, cambios y borrado. Estos formatos no son las dos vistas de producto.
- `PositionWorkspace` dentro de `ProjectPositionEditor` ya contiene carga, guardado, baseline, evaluación, borrador, guardas y editor real. Reutilízalo y refactoriza su ciclo de vida; no copies su lógica a otro archivo para crear un editor distinto.
- `useProjectOperations` ya maneja preview, `before_sig`, `operation_key`, apply y undo. `ProjectOpsStateView` permite reconciliar una clave. No conviertas una tabla nueva en escritura directa que salte esas garantías.
- `ProjectPrices`, `QuotationDocument`, `ProjectQuotationPanel`, `ProjectMaterials`, `ProjectBom`, `ProjectServicesPanel` y las preferencias manuales ya existen. Aquí se conectan coherentemente, no se reemplazan con tarjetas ficticias.

## Trabajo en orden

### 1. Contenedor compartido de obra

Introduce un contenedor de estado de UI de obra en `frontend/src/features/projects/ProjectWorkspaceState.tsx`. Sitúalo en un límite común de las rutas de la misma obra, de modo que navegar internamente y cambiar vista no cree dos instancias independientes. Usa las rutas existentes y un único shell autenticado; no desmontes y montes otro `AppShell` al ampliar el editor.

Su identidad es `userId:orgId:projectId`, con reinicio explícito cuando cambia usuario/organización/rol o se abandona ese contexto. El dato persistido del proyecto sigue en la consulta compartida del servidor. El contenedor conserva **estado de interfaz**, no una segunda obra serializada como fuente de verdad.

Mantén separados:

- `workspaceView`: Mesa o Estudio.
- Sección comercial/técnica actual y ruta de retorno.
- Posición activa, conjunto de posiciones marcadas y foco de teclado.
- Búsqueda, filtros, agrupación, galería/tabla y punto de scroll de la colección.
- Identidad/sesión de edición actual, sus cambios y estado de salida.
- Propuesta de operación de lote, clave de reintento, estado de aplicación y último undo permitido.

No mantengas una instancia de `useProjectOperations` por layout ni registres dos veces sus callbacks globales. Los formularios especializados conservan su estado cuando se cambia la vista; no renderices dos copias ocultas del mismo formulario con efectos de lectura/escritura duplicados.

Extrae del actual `PositionWorkspace` el controlador de sesión necesario para que una sola edición pueda presentarse en Estudio y en el editor amplio. Su estado y `useCanvasStore` no se recargan por un cambio cosmético. Se admite extraer componentes internos para mantener el archivo legible; el nombre y autoridad de los comandos, las validaciones y el guardado se conservan. La presentación detallada del editor se termina en 03.

### 2. Ruta y preferencia deterministas

Usa `view=mesa|estudio` y `position=<id>` en la obra; conserva `section` y los vínculos antiguos. Las rutas de edición existentes permanecen válidas:

```text
/projects/:id?view=mesa&position=:positionId
/projects/:id?view=estudio&position=:positionId
/projects/:id?view=estudio&section=quote&position=:positionId
/projects/:id/positions/:positionId/edit?view=mesa
/projects/:id/positions/new?view=estudio
```

Precedencia: query válida, preferencia por usuario/organización, Mesa. La preferencia no es un campo técnico ni altera huellas/cotizaciones. Permite almacenamiento local de esa preferencia con clave versionada y ámbito de usuario/org; no guardes importes privados ni payloads del servidor en ella. Si el almacenamiento está bloqueado, el selector funciona en memoria.

Valida toda posición contra la obra cargada y el rol. Una query ajena, inexistente o eliminada se normaliza a la última selección válida de esa obra o a su primera posición real. Un ID inválido no dispara lectura de datos de otro tenant. Una obra vacía no inventa `g1` como posición persistida.

El selector de vista usa reemplazo de query para no saturar Atrás. Las navegaciones deliberadas de sección/posición conservan historial navegable. No borres parámetros que otro panel utiliza. El retorno desde el editor se reconstruye con parámetros internos permitidos de la misma obra; no admitas redirección arbitraria desde un `returnTo` sin validar.

### 3. Mesa de obra completa y legible

Conserva el mapa de cuatro destinos. Recompón cabecera y colección con las primitivas/tokens de 01:

- Nombre de obra, cliente real vinculado, código humano, revisión y estado comercial, con una acción principal por región.
- «Añadir ventana» abre la creación manual existente. El usuario no tiene que buscar un botón de importación o escribir a IA para empezar.
- Miniatura de elevación real con vista declarada, nombre/código, cantidad, dimensiones, serie, acabado, vidrio y precio de venta cuando existe. `Sin precio` no es `$0`; no derives una cifra nueva de la miniatura.
- Clic selecciona; miniatura/botón textual y Enter abren editor amplio. Doble clic queda como atajo adicional. Detalle y edición son funciones visibles diferentes.
- Galería y tabla conservan filtros, orden, foco y selección. Usa la virtualización existente para colecciones grandes; no destruyas Home/End ni el objetivo de foco tras acciones.
- El selector Mesa/Estudio se ve y se entiende sin entrar en Ajustes. Sus dos nombres son textuales; no uses dos íconos ambiguos como único identificador.

En Mesa seleccionada puede mostrarse una ficha compacta o drawer con resumen/materiales; no pongas un editor diminuto dentro de una tarjeta. «Abrir editor» debe aumentar el espacio disponible de verdad.

### 4. Estudio con el mismo editor

Presenta la sesión compartida con franja de posiciones, dibujo predominante e inspector manual. Usa el mismo `AssemblyEditor` y la misma evaluación/guardado que el editor amplio. El wrapper de Estudio no serializa otro diseño ni mantiene un segundo historial.

Si no hay posiciones, abre la biblioteca manual con una acción clara de añadir, sin documento ficticio. Si no hay posición activa, elige una válida en el orden de obra. Si un filtro oculta la posición que se está editando, conserva su sesión e indica que está fuera del filtro; ofrece mostrarla o limpiar el filtro. No cambies silenciosamente a otra mientras tiene cambios.

Cotización, Materiales y Actividad usan exactamente los paneles de Mesa. Al volver a Ventanas se recupera la misma sesión. No dupliques el PDF, precio o materiales para que la nueva vista parezca completa. No añadas un panel del asistente a Estudio; 03 retira el panel heredado del editor y la fase global del popup resuelve la delegación opcional.

### 5. Selección, operaciones y resultado

La posición activa define qué dibujo se ve. Las casillas definen qué posiciones recibe una operación de lote. La selección física del canvas define qué módulo/paño/división/unión se edita. No son un único array intercambiable.

En un lote muestra cantidad marcada y cuántas están fuera del filtro. «Seleccionar visibles» significa exactamente las filas visibles por filtro, no todas las posiciones del proyecto. Las marcadas ocultas no se aplican sin que el alcance total sea visible en el diff.

Reutiliza duplicar, cantidades, ubicación/piso/recinto/eje, reordenar y eliminar. Cambios globales de serie, vidrio, acabado y herrajes se conectan a `QuotationGlobalChanges`/registro tipado con selección compartida. No se habilita un cambio incompatible solo porque el formulario permita escribirlo.

Después de aplicar/deshacer:

- Reconciliar consulta compartida, lista y cabecera; tomar cantidades/números del servidor.
- Conservar la posición activa si sigue existiendo; si se elimina, elegir la siguiente válida según el orden real y luego la anterior si no hay siguiente.
- Reconciliar lote y selección física con IDs que todavía existen.
- Si una operación afecta a la posición con borrador local, resolver Guardar/Descartar/Cancelar antes de aplicarla. No pisar su edición ni simular sobre dos baselines diferentes.
- Mantener el mismo `operation_key` en un reintento incierto y consultar su estado cuando corresponde; no generar otra clave porque el layout cambió.
- Reordenar mantiene códigos físicos. Duplicar no copia levantamiento físico ni precio aplicado a una ventana nueva.

Las operaciones manuales pueden reutilizar componentes de diff ubicados bajo `features/assistant` si son renderizadores deterministas. Una ruta de importación de código no implica consumo de IA. No borres un componente compartido sin revisar sus consumidores.

### 6. Guardado, cambios pendientes y recuperación

Mantén Guardar explícito. No introduzcas autosave de negocio para esconder el problema de navegación.

- Mesa↔Estudio y abrir/cerrar el **mismo** editor amplio mantienen sesión y no piden confirmar ni guardan por sorpresa.
- Otra posición o salida de obra con cambios ofrece Guardar / Descartar / Cancelar. Guardar espera confirmación real antes de navegar; Descartar restaura base; Cancelar conserva inputs/foco.
- `Ctrl/⌘+S` sigue invocando guardar cuando es permitido. No dispara el guardado de página del navegador ni guarda en lectura móvil.
- Mantén `expected_updated_at`, locks, revisión/precio aplicado y estado `uncertainCreate`. En conflicto se conserva el borrador; no reenvíes con timestamp actualizado silenciosamente.
- Actualiza la identidad del buffer local a usuario+org+obra+posición o creación nueva con ID estable. Dos obras nuevas y dos copias del mismo origen no comparten `new`/`copyId` como destino.
- Guarda versión del formato, revisión/baseline y fecha. Una recuperación de otro baseline muestra comparación/decisión antes de aplicar; nunca se toma por resultado calculado vigente.
- No borres todos los borradores existentes. Lee el legado solo si puedes demostrar correspondencia de identidad y obra; el antiguo `new` ambiguo no se carga en cualquier obra. El guard de autenticación conserva su limpieza de estado cargado.

No uses número de posición, nombre de cliente o etiqueta de recinto como clave de identidad. Los códigos humanos sirven para lectura; los IDs y la revisión sirven para concurrencia.

### 7. Herramientas manuales y revisiones

Haz que el recorrido crear obra/cliente → valores habituales → añadir/editar ventanas → revisar lote → calcular/aplicar precio → preparar propuesta se pueda completar sin IA configurada. Reutiliza los métodos actuales de `ProjectPrices`; no implementes un motor de margen/descuento paralelo en React.

Distingue con palabras:

- Diseño guardado frente a cambios locales.
- Geometría válida frente a definición de fabricación incompleta.
- Precio indicativo frente a precio aplicado de revisión.
- Borrador frente a revisión emitida.
- Necesidad preliminar de materiales frente a una OT liberada.

`editable` del servidor sigue rechazando revisión cerrada, estado no DRAFT o precio aplicado. Explica la causa y el camino válido existente para revisar precio/crear sucesora. No escondas un bloqueo real detrás de un Guardar gris sin explicación, ni lo elimines para que la vista nueva parezca funcionar.

El detalle de compras/CNC/taller no se incrusta como una colección de botones en Cotización. Conserva vínculos al módulo y al objeto correctos. La fase de operaciones del paquete completa esos recorridos.

### 8. Estados y adaptación

Implementa vacío, carga, error, sin permiso y bloqueo con una acción concreta y la identidad del recurso. Conserva datos editados al fallar una petición. El error de lectura reintenta la misma obra/organización, no crea una nueva.

En 1440/1280 se leen cabecera y dibujo; en 1024 el inspector puede abrirse como drawer. Debajo de 1024 el editor técnico conserva lectura y explica el límite; navegación y consulta de la obra siguen disponibles. No soluciones desbordes encogiendo todo a tipografía ilegible. Usa las reglas de accesibilidad y color de 01/constitución; no cambies logo ni generes una marca nueva.

## Límites de esta fase

- No implementar el runtime de IA ni planes/pasarela/despliegue.
- No cambiar fórmulas, tolerancias, goldens, RLS, inmutabilidad o clic humano para consecuencias externas.
- No eliminar fixtures/DEMO ni sus referencias; 03 reorganiza su descubrimiento sin limpieza destructiva.
- No degradar herramientas que ya existen por centrarse en los layouts. Si mueves un componente, conserva su contrato antes de reemplazar la envoltura.
- No lanzar una campaña de pruebas, suites, build o capturas de aceptación al terminar cada subpaso. El paquete tiene una campaña final después del desarrollo completo. No llames «probado» a lo que todavía no pasó esa campaña.

## Entrega de desarrollo y continuidad

Completa la implementación de ambos hosts y sus conexiones reales. No dejes botones vacíos, TODOs de flujo, variantes a elegir ni una pantalla de Estudio que sea solo un enlace a otra aplicación. Deja explícita la propiedad de estado y elimina duplicación introducida por el refactor.

Al finalizar informa archivos/símbolos principales, decisiones de compatibilidad y riesgos concretos para la campaña final. Enumera como **pendientes de verificación final**, no como pruebas aprobadas, la continuidad de borrador/undo, Atrás/Adelante, selección en lote, conflicto de guardado, cambio de identidad, flujo sin IA y restricciones de revisión. Continúa con `03-editor-cotizacion.md`; no vuelvas a pedir al dueño elegir entre Mesa y Estudio.
