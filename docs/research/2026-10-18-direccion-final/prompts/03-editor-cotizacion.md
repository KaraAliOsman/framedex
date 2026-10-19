# Prompt 03 — Editor profesional, aperturas y catálogos para cotizar

Ejecuta este prompt **después de `02-dos-vistas.md`**, sobre su implementación compartida. Termina el editor manual y la biblioteca de fabricante/series que lo alimenta. No construyas otra calculadora ni otra aplicación de diseño. El dueño ya eligió: cotizador profesional central, Mesa y Estudio del mismo sistema, IA opcional solamente en un popup global invocado.

## Resultado concreto

El usuario puede reconocer una marca y su serie, escoger una configuración permitida, diseñar sobre un lienzo amplio, cambiar medidas/apertura/vidrio/acabado/herraje, entender una restricción y guardar. La misma posición aparece en Mesa y Estudio con dibujo, revisión y materiales coherentes. El trabajo manual no llama al proveedor de IA ni necesita créditos. La biblioteca normal presenta fabricantes reales con alcance honesto, imágenes o secciones útiles y fuentes localizadas; los DEMO quedan explícitamente separados sin borrar historia.

No basta cambiar colores del inspector ni ordenar tarjetas. Completa las interacciones, estados y conexiones reales descritas abajo. La composición final conserva los tokens/voz de 01; no vuelvas a proponer tres estilos visuales.

## Lectura y preparación

1. Revisa rama, ref y `git status --short`; respeta los cambios locales. Lee `AGENTS.md`, `docs/ENGINEERING.md`, `docs/design/CONSTITUCION.md`, el contrato `../01-producto-y-dos-vistas.md` y el resultado de 02.
2. Desde `docs/wiki/index.md`, lee `product/editor-canvas.md`, `physical-openings.md`, `advanced-openings.md`, `catalog-authority.md`, `physical-3d.md`, `glass-composition.md` y `hardware-classes.md` solo en sus partes pertinentes. Los refs históricos orientan; el código actual manda sobre afirmaciones de implementación.
3. Inspecciona el editor: `frontend/src/features/projects/ProjectPositionEditor.tsx`; `frontend/src/features/canvas/AssemblyEditor.tsx`, `CanvasViewport.tsx`, `OpeningPalette.tsx`, `physicalOpenings.ts`, `advancedOpenings.ts`, `canvasStore.ts`, `productEditing.ts`, `intentEditing.ts`, `designOps.ts`, `StarterGallery.tsx`, `starterAuthority.ts`, `SectionView.tsx`, `Model3DView.tsx`, `Model3DStage.tsx`, `EditorLayout.css` y módulos que esos símbolos usan.
4. Inspecciona catálogo: `frontend/src/features/catalogs/CatalogPage.tsx`, `catalogModel.ts`, `SystemWorkspace.tsx`, `WorkspaceMaterials.tsx`, `CatalogImportsPanel.tsx`, `CatalogProvenance.tsx`, `OpeningCapabilitiesEditor.tsx`, `AdvancedRecipesEditor.tsx`, `FinishAuthorityEditor.tsx`, `CatalogLimitsEditor.tsx`, `SectionImportPanel.tsx`; `backend/catalogs/serializers.py`, `service.py`, `views.py`, `authority.py`; `backend/ingest/catalog_service.py`, `catalog_views.py`, `catalog_pages.py`; `engine/src/dekopen_engine/catalog_authority.py`, `catalog_rules.py`, `openings.py`, `advanced_openings.py` como autoridad de contratos, sin reescribir sus fórmulas.
5. Lee la evidencia ya reunida: `docs/research/2026-10-18-revision-profunda/catalogos-reales.md`, `competidores-ingenieria.md`, `auditoria-dekopen.md`, y `docs/research/2026-10-17-claude/prueba-catalogos-proline-2026-10-18.md`. No repitas investigación general ni atribuyas a una captura lo que no fue observado.

## Capacidades presentes que debes preservar

- `AssemblyEditor` es un editor real de módulos/paños/uniones con simulación, selección, herramientas, planta, inspector y puente de operaciones.
- `OpeningPalette` usa `openingChoices`; las capacidades incluyen movimiento, dirección, bisagra, rol, uso y recetas. Existe un camino histórico separado. No reemplaces esto por un enum plano de nombres bonitos.
- El store tiene historia, `commitInputs`, `acceptIntent` y reconciliación de selección. El guardado ya impide cantidad/acabado/relleno/evaluación incompatibles y usa concurrencia.
- El catálogo ya tiene manufacturer/family, secciones dibujadas, procedencia, preparación por niveles, edición manual, importación estructurada, revisión de diff y publicación controlada. No lo describas ni reconstruyas como si estuviera vacío.
- El editor actualmente incluye `AssistantPanel` y `AlternativesPanel` dentro de «Asistente y alternativas». **Ambos son flujos generativos**, no el método manual de comparación. La nueva dirección exige retirarlos de esa superficie permanente y conservar la funcionalidad opcional en el contrato global, sin arrastrar un hueco vacío.

## 1. Lienzo amplio y controles que se entienden

Usa el controlador común de 02. `AssemblyEditor` sigue siendo la misma presentación técnica dentro de Estudio y del editor amplio; los wrappers no introducen ramas de cálculo diferentes.

Distribución final de escritorio:

- Cabecera compacta: obra, ventana/ubicación, revisión, estado guardado y retorno. Guardar es la acción principal de edición.
- Banda plegable de posiciones de 160 px en la composición de 1440 px del contrato visual, con miniaturas y siguiente/anterior; a 1280 px empieza plegada. Solo puede crecer hasta 200–240 px en viewports mayores que conserven el presupuesto del lienzo (al menos 60 % del ancho de trabajo). No dejes dos listas redundantes, lateral e inferior, abiertas a la vez.
- Lienzo como región predominante. Inspector contextual de aproximadamente 288–320 px, ajustado mediante tokens, con título del objeto seleccionado. Si estas columnas reducen demasiado el lienzo, pliega la banda o presenta el inspector como drawer; no conviertas el dibujo en una miniatura.
- Herramientas agrupadas por tarea: seleccionar, dividir, añadir/acoplar, medir/cotas y vistas. Las acciones decisivas llevan texto. Oculta opciones no pertinentes a la selección, pero conserva una forma clara de descubrir herramientas generales.
- Barra de vistas: Elevación, Planta, Sección y 3D. Interior/exterior es un control explícito de observación, con leyenda en la representación. No modifica mano ni fabricación.

Elevación abre primero. La planta no permanece grande por defecto para una unidad simple; aparece cuando carriles/uniones aportan información y se puede plegar. Un conjunto acoplado dispone de planta/cotas adecuadas sin obligar a repartir siempre el viewport en dos mitades iguales. El árbol técnico es progresivo; no ocupa una tercera columna permanente.

El ajuste inicial centra el contenido físico y sus cotas con margen legible. Centrar es un comando claro. No reinicies pan/zoom en cada respuesta del motor, pulsación o cambio de selección. Al reemplazar una receta o contenido completo, reajusta una vez con la identidad nueva. Mantén las transformaciones de píxeles fuera del modelo técnico.

A 1024 px, usa banda/inspector desplegables con exclusión de capas. Conserva lectura del editor por debajo de 1024 y explica la restricción vigente; no habilites escritura táctil incompleta para aparentar soporte. En 390 px el usuario puede consultar ventana/especificación y volver a la obra sin desbordes.

No añadas islas decorativas, tarjetas de estadísticas, logo nuevo, mascotón, difuminados o sombras voluminosas. Color cumple función: selección, acción, atención y material se distinguen además por forma/texto. El vidrio no se representa con el mismo gris del cromo. Las preferencias de acabado no se inventan como colores de marca.

## 2. Selección, cotas y cambios manuales

La selección física distingue posición, módulo, paño/hoja, división y unión. Al seleccionar se ve su nombre y ámbito. Reconcíliala tras reemplazar receta, deshacer, quitar unidad o cambiar catálogo. Ningún inspector puede apuntar a un ID que dejó de existir.

Haz que medidas y cotas tengan una ruta manual directa:

- La cota editable y el campo de inspector actúan sobre el mismo comando.
- Durante entrada se conserva el lexema; Enter/confirmación aplica un valor válido y Escape restaura el aceptado. No redondees a entero un dato fuente fraccionario ni sobrescribas una celda inválida sin explicación.
- Un cambio inválido mantiene la base aceptada y señala el campo/objeto y la regla que lo bloquea. No mostrar «Válido» mientras la evaluación del nuevo estado sigue pendiente.
- Los números calculados llegan del motor. Los formateadores existentes presentan mm, m², kg, porcentajes y moneda; no agregues aritmética de fabricación/margen en el componente.
- Cambios de ubicación/cantidad que no son geometría no deben destruir la selección o resetear zoom/historia.

Mantén comandos manuales de dividir, igualar, quitar división, añadir/quitar módulo, acoplar y cambiar propiedades pertinentes. Los atajos de deshacer/rehacer, borrar con ámbito claro y copiar/aplicar especificación respetan foco de campos y edición de texto. Una tecla Delete no debe eliminar una ventana cuando el usuario borra un carácter de un input.

Conservar el resultado anterior durante debounce es aceptable solo si está marcado como anterior/calculando y no habilita guardar ni una cifra actual. Las respuestas llevan identidad de org, posición, diseño, serie y cantidad; una respuesta tardía de otra selección no reemplaza el resultado actual.

## 3. Aperturas físicas: corregir el flujo, conservar autoridad

La denuncia del dueño se investiga con el objeto y catálogo reales. La auditoría anterior logró cambiar una apertura izquierda→derecha y deshacer sin guardar; por tanto, no supongas que todo el subsistema falta. Distingue:

1. No hay selección o se seleccionó otro paño.
2. Opciones de serie no cargadas o fallidas.
3. La familia no admite ese movimiento.
4. Falta capacidad, receta, kit o autoridad.
5. Se está consultando una revisión/precio aplicado cerrado.
6. Se está en lectura por ancho de pantalla.
7. Hay un fallo real de comando, simulación, representación o persistencia.

Cada caso necesita causa y acción localizada. No quitar una regla del motor ni habilitar todas las aperturas como solución visual.

Paleta manual final:

- Miniatura técnica y nombre inequívoco; mano, dirección y rol se leen desde la vista declarada.
- Opciones procedentes de `opening_capabilities`, `paired_leaf_rule` y recetas de la serie; no hardcodear una galería universal.
- Puerta y ventana son usos distintos. Una francesa conserva activa/pasiva, inversor y manilla; no se sustituye por dos fijos con montante.
- Correderas muestran hojas, carriles, movilidad y sentido; la planta hace comprensible dónde corre cada hoja. Elevadora, paralela, plegable, pivotante o guillotina requieren receta y herraje que el catálogo realmente declare.
- Fijo en marco y fijo en hoja no son el mismo producto.
- Cambiar apertura reinicia o conserva el herraje y la manilla según el contrato existente, con consecuencia visible. No conservar un kit incompatible para evitar campos vacíos.
- Vista previa de opción sin mutación; aplicar deja una transacción deshacible y vuelve a evaluar. Selección, rótulo, glifo, 2D, 3D y BOM deben referirse al mismo resultado.

Conserva la gramática DIN/interior-exterior del repositorio y los códigos de transporte históricos. La inversión de cámara o un icono de competidor no justifica cambiar bisagras o reglas del cálculo. El fallback legado se limita a autoridad histórica válida; una serie nueva con capabilities ausentes no recibe una supuesta capacidad universal por caer en ese fallback.

## 4. Vidrio, acabado, herraje y serie

El inspector presenta los datos por selección, con progresión de básico a técnico:

- Vidrio/relleno: nombre, composición disponible, espesor y compatibilidad de junquillo; seguridad/ensayo/valores térmicos solo con fuente válida. `Sin dato` cuando falte evidencia.
- Acabado: interior y exterior, combinación comercial/código de catálogo, muestra o textura legítima. La muestra es presentación, no autoridad de precio o geometría.
- Herraje: kit/clase compatible, rol de hoja y límites disponibles, manilla y rangos del motor. Los códigos detallados se pueden consultar; no sustituyen el nombre legible.
- Sección: perfil/rol/orientación y fuente; dibujo aproximado identificado cuando no existe geometría fuente. No dibujar cámaras o refuerzos supuestos para aparentar detalle técnico.
- Fuente de número: enlaza a traza o información existente; no crea una explicación LLM para un cálculo determinista.

Cambiar de serie es una operación técnica. Muestra fabricante/serie destino y comprueba aperturas, rellenos, herrajes, acabado y uniones. El diff explica qué se conserva y qué requiere elegir nuevamente. No asignar un SKU «parecido» de otra marca ni trasladar un acabado por coincidencia de nombre. Si algo no tiene equivalencia, se conserva como falta explícita o se bloquea antes de aplicar según el contrato vigente.

Los valores habituales de empresa/obra ayudan a iniciar; no completan silenciosamente una preferencia incompatible. Una corrección local no se publica como regla global. Un producto existente conserva su versión técnica/documental.

## 5. 2D, planta, sección y 3D coherentes

No crees geometría comercial independiente para el render. Usa el producto y hechos calculados que ya alimentan el dibujo/BOM. El 3D puede cargarse de forma diferida al abrir su vista; no montes todos los contextos WebGL ocultos por cada posición.

Permite inspeccionar interior/exterior, abrir/cerrar las hojas soportadas y restablecer cámara. El movimiento no estira hojas rígidas ni atraviesa piezas para parecer una apertura. Si una tipología no tiene movimiento validado, declara visualización estática; no inventes cinemática. Si WebGL falla, conserva 2D y especificación, con recuperación localizada.

En correderas/uniones muestra franja en planta y medidas del mismo modelo. En sección declara corte/orientación. Acabados bicolor mantienen caras. La miniatura de Mesa y la vista del documento no se convierten en otra interpretación libre de los símbolos.

La referencia comercial actual es X3D de V6 anunciado el 25-08-2026; sirve para coherencia de opciones, no para copiar materiales ni fórmulas. El objetivo de esta fase no es un motor de render separado ni prometer fotografía de la obra real.

## 6. Eliminar dependencia de IA de la edición

Retira `AssistantPanel` y el generador `AlternativesPanel` de la estructura persistente de `AssemblyEditor`; retira estilos/capas vacíos y affordances duplicados que solo abrían ese panel. Conserva el registro de comandos y `useRegisterDesignOpsBridge` o su contrato sucesor cuando la fase global lo necesita: es la vía tipada que el popup opcional puede delegar, no un motivo para mantener el chat local.

No se debe hacer una llamada generativa por cargar opciones, seleccionar una hoja, abrir un inspector, crear una ventana o pulsar Guardar. Si una acción secundaria «Pedir al asistente» se conserva, abre exclusivamente el popup global mediante su contrato y solo después del clic explícito, con obra/posición/selección y baseline. No crea un chat privado del canvas. Si el popup todavía no está implementado en la secuencia, no presentes un botón muerto; deja preparada su integración interna y continúa con la fase correspondiente.

La comparación **manual** permanece disponible mediante duplicar/editar y comparación del sistema, sin proveedor. No rebautices un endpoint generativo como «alternativas manuales». El cierre del popup nunca modifica ni borra un borrador del editor.

## 7. Biblioteca de fabricante → serie → contenido útil

Recompón `CatalogPage` sobre los datos existentes:

1. **Fabricantes.** Entrada reconocible con nombre, material/familias y series disponibles; búsqueda por marca, serie y código. Solo usar logo/foto con procedencia adecuada; el nombre textual debe bastar cuando no hay logo.
2. **Series de un fabricante.** Nombre exacto, código/familia técnica, material, imagen/sección útil, versión, configuraciones y estado por uso. Versiones anteriores se consultan dentro de la serie; no llenan la portada como fabricantes separados.
3. **Serie seleccionada.** Resumen de aplicaciones y configuraciones; perfiles/refuerzos/juntas/junquillos, vidrio, herrajes, acabados, fuentes y revisión. Los editores de reglas se abren desde su sección por rol; no todos en la portada.
4. **Artículo.** Código legible con nombre, rol, unidad/suministro/largo conocido, sección/orientación, acabado y procedencia. Costos privados siguen en su área autorizada.

`manufacturer` y `family` ya existen en serializers/modelo de UI. Empieza agrupando con esos datos; no inventes tablas paralelas de artículos solo para mostrar cards. Normaliza únicamente diferencias tipográficas seguras para agrupar visualmente; no fusiones fabricantes por parecido. Una identidad desconocida va a «Fabricante por identificar» con causa y edición permitida, no a Proline por defecto.

La agrupación visual no elige autoridad por `max(version)` en el cliente. Cada acción conserva el `system_id`, procedencia global/tenant y versión que la API permite usar. Si hay varias versiones activas, muestra claramente cuál usa una obra; no cambia la serie de una posición antigua sin una operación explícita.

Desde un selector dentro del editor, abrir la biblioteca devuelve la serie exacta al mismo contexto. Desde Catálogos sin obra, «Ver configuraciones» es consulta; «Usar en una obra» elige una obra/borrador permitido sin crear un proyecto vacío inesperado. No necesitas un checkout comercial ni portal nuevo para resolver esta selección.

## 8. Datos reales y separación de DEMO

La portada normal no estará dominada por clones DEMO. Añade separación explícita de laboratorio/sistemas sintéticos manteniendo seed, fixtures, referencias, revisiones y documentos históricos. **No borrar, migrar a ciegas ni renombrar DEMO como real.** Una obra antigua que usa DEMO conserva su aviso y sigue pudiendo consultarse.

Prioridad de contenido real:

- **Proline PRO6004** y **Proline PROSLIDE70**, como series distintas bajo la misma marca. «60/70» puede ser una ayuda de búsqueda, pero no fusiona familia practicable y corredera.
- **Indalum Superba 33 RPT** y **Superba 44 RPT** como referencias de aluminio con sus usos separados y documentos exactos cuando estén disponibles.
- **Winhouse Diamond 60 / Opal 70** y Deceuninck Chile como referencias adicionales ya investigadas, sin atribuirles publicación técnica que no se haya completado.
- «Vinhaus» no está identificado de forma inequívoca. No lo conviertas automáticamente en Winhouse, Winhaus.cl o Winhouse by Haustek. Conserva el nombre/consulta como pendiente de identidad cuando corresponde, sin contaminar datos de otra marca.

Consulta las fuentes exactas reunidas, no una búsqueda genérica para rellenar:

- Proline productos: https://www.prolinepvc.com/en/products
- Proline catálogo: https://www.prolinepvc.com/catalogue/Proline_PVC_Catalogue.pdf
- Proline distribuidor chileno: https://www.proline-pvc.com/
- Winhouse biblioteca: https://www.winhouse.com.tr/en-us/architects-engineers/technical-brochures
- Winhouse Diamond: https://www.winhouse.com.tr/en-us/pvc-window-and-door-system/diamond-60-pvc-series/main-profiles
- Winhouse Opal: https://www.winhouse.com.tr/en-us/pvc-window-and-door-system/opal-70-series-pvc-windows/main-profiles
- Indalum catálogos: https://www.indalum.cl/fabricantes-minisite/catalogos/40
- Indalum manuales: https://www.indalum.cl/arquitectos/manuales/39
- Deceuninck Chile: https://www.deceuninck.cl/nuestros_catalogos.html

Resuelve la ubicación del material Proline aportado por el dueño desde `prueba-catalogos-proline-2026-10-18.md`, sin asumir que un archivo de igual nombre es el original. Huellas de referencia:

- Catálogo de 24 páginas: `b2732493f1981cbc0f7a595104a1603bbc4bafe76a6e625ab5a3119bfe755cfe`.
- Casos de corte de 25 páginas: `bf16d500eae5b7f2af9bef2f983b987acc4e0fda63c6c8fa499ed47ae4ac816f`.

Los casos de corte son ejemplos, no una fórmula general. Conserva las incidencias documentadas `#NAME?` y títulos inconsistentes; no las arregles silenciosamente inferiendo números. PDF público, revisión humana y catálogo fabricable son estados distintos.

Construye fichas reales útiles con fuente/imagen/sección y cobertura honesta. Publica como cotizable/fabricable únicamente el alcance que pueda justificarse mediante datos y revisión competentes. Si la evidencia reunida no permite completar una receta, implementa su ficha y recorrido de revisión, mantén el bloqueo exacto y registra esa carencia concreta para la campaña final. **No declares lista para fabricar una serie incompleta para satisfacer una pantalla verde.** Continúa el resto del desarrollo sin pedir una nueva decisión estética.

No tomes precios de internet como costos negociados del usuario. La autoridad técnica compartida no incluye las listas privadas de cada empresa. Una imagen o PDF privado con precios no se expone en la galería global. Los medios se vinculan a fuente/página/versión y permisos; una miniatura comercial no certifica un perfil o ensayo.

## 9. Estado técnico y publicación manual sin IA

Separa visualmente:

- Estado administrativo: activo/inactivo.
- Preparación: apto para cotizar, fabricar y proceso/CNC según contrato real.
- Procedencia: DEMO, referencia, revisado/verificado y su versión.

Usa `readiness` y `catalog_authority_gate`; no derives «CNC listo» por tener secciones bonitas, un centro vinculado o una etiqueta revisada. La decisión de emisión considera artículos consumidos y su revisión. Un estado desconocido no es falso ni éxito; explica qué dato falta.

El camino manual de mantenimiento está completo:

1. Crear/editar fabricante/serie y artículos con los formularios autorizados.
2. Adjuntar documento fuente y localizar página/evidencia. Adjuntar no llama por sí solo a un modelo generativo.
3. Usar plantilla XLSX/CSV y revisión estructurada para datos; conservar lexemas Decimal, unidad y moneda. Fórmulas de planilla o celdas de error no se convierten en autoridad técnica.
4. Revisar relaciones/capacidades/reglas con los editores existentes; mostrar fuente y desconocidos de forma localizada.
5. Obtener diff de publicación, resolver errores, confirmar revisión y publicar por el rol permitido con su token vigente. Mantener concurrencia, transacción, auditoría y undo cuando su contrato lo permita.
6. Separar carga de precios privados del catálogo técnico y de la vista del estimador.

Una extracción opcional de PDF/imagen por IA se solicita desde el popup global y devuelve candidatos al mismo revisor; no existe una segunda ruta que publique sin validación. El plan sin IA puede adjuntar fuentes y completar/importar todos los datos manualmente. No deshabilites el botón de plantilla porque falte API key.

Evita porcentajes inventados de avance o confianza. Si no se dispone de una métrica calibrada/documentada, muestra extracción revisable, fuente y dato ausente. El hecho de estar «revisado» no es una certificación de fabricante ni una homologación térmica.

## 10. Vacíos y errores terminados

Completa los cinco estados de la constitución, con causas concretas:

| Caso | Respuesta final de interfaz |
|---|---|
| Sin series reales preparadas | Marca/referencia/fuente visibles y acción permitida de incorporar/revisar; acceso explícito a laboratorio. No una lista vacía sin salida. |
| Serie sin foto | Sección/dibujo disponible o placeholder técnico identificado y útil; no foto genérica o imagen rota. |
| Falta origen/fórmula/capacidad | Enumerar el requisito y enlazar al registro/campo; respetar permiso de revisión. |
| No hay apertura compatible | Causa por familia/receta y acceso a seleccionar serie o revisar autoridad. No paleta universal que falla después. |
| Petición de opciones fallida | Dibujo y borrador conservados, error con Reintentar; no tomar la lista vacía como catálogo válido. |
| Revisión/precio bloquea guardar | Motivo específico y enlace de revisión/precio según permiso. |
| Simulación inválida | Objeto y regla afectados, datos corregibles y deshacer disponible; no llamada IA automática para resolver. |
| Catálogo cambió durante diff | Invalidar propuesta obsoleta, conservar revisión editable y volver a preparar diff con el servidor. |
| Sin permiso de publicación/costos | Lectura permitida y responsable; no fuga de fuentes privadas ni un botón que termina en 403 como camino normal. |
| WebGL no disponible | Elevación/especificación útil, mensaje localizado y regreso sin perder edición. |

Los detalles técnicos se pueden expandir para soporte, pero el cuerpo no muestra UUID/enums/stack traces como explicación principal. Todos los controles por icono tienen nombre accesible; selección/error no se comunican solo por color. Foco, anchos reales, textos largos y dibujos extremos siguen las reglas del sistema.

## Invariantes y alcance de implementación

No cambies fórmulas para encajar una pantalla. Dimensiones, dinero y cálculo permanecen Decimal/motor, tolerancia `0.00 mm`. Guarda el contrato de aperturas/autoridades históricas. RLS, `org_id`, costos privados, snapshots emitidos, historial y clic humano para emitir/enviar/comprometer permanecen intactos.

Si necesitas campos de medios/identidad que el modelo actual no cubre, añade el mínimo contrato siguiendo serializer/view → OpenAPI/orval y migración aditiva del repositorio, con permisos y origen claros. No edites generado a mano ni migres a otro framework/BD. No implantes una taxonomía paralela que cambie IDs técnicos. No limpies el stack del dueño para montar una demo nueva.

La fase no incluye planes de pago, proveedor IA, despliegue, software de CNC nuevo ni certificación de catálogos por inferencia. Incluye los recorridos manuales completos y estados honestos de su autoridad. Conserva lo útil ya implementado; elimina código viejo duplicado que el refactor vuelva innecesario tras revisar sus consumidores.

## Entrega y continuidad del paquete

Desarrolla todos estos cambios antes de iniciar la campaña integrada final. **No ordenes ni ejecutes una suite/build/E2E/capturas por cada sección de este prompt.** La campaña final del paquete concentra validación técnica, visual, de roles y recorridos completos, seguida de correcciones focalizadas. No reescribas ni debilites pruebas/guardas/goldens para conseguir aceptación aparente.

Entrega el editor conectado a ambas vistas, catálogo navegable real con fuentes/alcances explícitos, rutas manuales y retiro de IA incrustada. Informa qué se reutilizó, qué cambió y cualquier dato técnico concreto que todavía impida fabricar una serie. Diferencia implementación terminada de verificación final pendiente. No declares que viste un video, publicaste un catálogo validado o probaste una máquina si esa evidencia no existe. Continúa con el siguiente prompt del paquete; no pidas otra elección de diseño al dueño.
