# Archivos que se convierten en trabajo y tres mejoras justificadas

18-10-2026. Ampliación documental para Claude; no implementación ni prueba de producto. El dueño recibió favorablemente las ideas anteriores y **añadió explícitamente documentos, imágenes y cualquier otro archivo compatible como entrada de IA**. Eso respalda la dirección; no ordena que las treinta oportunidades previas sean requisitos simultáneos del lanzamiento.

## Lo que sí pasa al encargo

La persona podrá abrir el popup, adjuntar varias fuentes y consultarlas en Chat o delegar un resultado en Trabajo. Ejemplo: «Con este listado, este plano y estas fotos, prepara las posiciones de esta obra y el borrador de propuesta». La IA usa contexto autorizado, resuelve lo acreditado y completa operaciones reales. Las fotos ayudan a interpretar etiquetas, composición o notas; las medidas de fabricación requieren datos explícitos y validación del motor.

El contrato queda integrado en [03: copiloto](../2026-10-18-direccion-final/03-copiloto-y-planes.md#adjuntos-multimodales--ampliación-explícita-del-dueño) y [prompt 05](../2026-10-18-direccion-final/prompts/05-copiloto.md). Mínimo especificado: PDF con texto o escaneado, PNG/JPEG/WebP, XLSX/CSV, DOCX y TXT/Markdown. Es una decisión de implementación para documentos, imágenes, planillas y texto habituales, no una afirmación de soporte existente completo. Otros formatos se habilitan con adaptador y verificación reales, desde una matriz del servidor.

**Recorrido:** Adjuntar/arrastrar/pegar → lista compacta con preview → mensaje con fuentes y destino visibles → progreso real → resultado con referencias al origen. Cada cita abre página/región, hoja/celda o párrafo/tabla. El detalle se amplía al necesitarlo; no llena el popup de controles permanentes. Subir o previsualizar no gasta IA por sí solo. Reabrir conserva archivos persistidos sin repetir extracción pagada.

**Distinción esencial:** recibir, poder leer, poder usar para una tarea y estar validado son estados distintos. Una imagen legible puede no tener la dimensión necesaria. Una planilla puede traer un precio ajeno al acuerdo de esa empresa. Una lectura parcial enumera lo pendiente; no se presenta como trabajo completo.

## Tres mejoras que sí tienen razón de ser

### 1. Fuentes reutilizables de la obra

**Problema.** Plano en un chat, medición en otro y foto en un tercero obligan a explicar repetidamente la obra. Un historial largo no organiza la evidencia.

**Propuesta.** Vincular explícitamente una fuente a la obra y reutilizarla desde otro encargo. Una sección ligera en la obra conserva plano, medición, especificación y documentación comercial con versión y estado. El popup permite «Usar fuentes de esta obra», mostrando el alcance. No envía todos los archivos al modelo cada vez: recupera lo necesario y registra la versión utilizada.

**Ejemplo.** Al retomar «revisa el vidrio de V3», se usa la especificación vinculada sin cargarla otra vez. Una foto privada del hilo no pasa a una biblioteca compartida automáticamente. La autorización sigue al usuario.

**Valor y criterio.** Menos reenvíos y búsquedas, continuidad entre sesiones/personas autorizadas y menos errores por fuente obsoleta. Medir esos resultados con una obra real; no vender «memoria infinita».

**Alcance.** Extiende importaciones/artefactos y refina I08/I19; no crear otro gestor documental. La continuidad de adjuntos del propio hilo ya es obligatoria. La biblioteca entre conversaciones es ampliación recomendada.

### 2. Contradicciones visibles antes de cambiar una ventana

**Problema.** Un paquete puede contener plano antiguo, medición posterior y nota comercial distinta. Interpretarlo más rápido no ayuda si se elige la fuente equivocada.

**Propuesta.** Comparar campos de fuentes vinculadas con identidades conocidas. Mostrar el conflicto en la posición: valores, documentos, revisiones y estado de confirmación. Aplicar la autoridad ya establecida cuando exista; agrupar solo las excepciones materiales que necesitan decisión. No elegir por orden de subida ni por un porcentaje de confianza sin calibrar.

**Ejemplo ilustrativo.** Listado: V3 de 1200 mm; medición confirmada: 1180 mm. Localizar la discrepancia y explicar qué fuente gobierna esa etapa. No deducir si representan vano o fabricación. Las posiciones independientes continúan.

**Valor y criterio.** Evitar errores de coordinación antes de emitir/fabricar. Medir conflictos verdaderos, falsos avisos y esfuerzo de resolución; no cantidad de alertas.

**Alcance.** Refina I01/I05/I07 y el comparador exigido. Tratar conflictos del encargo actual es obligatorio; la revisión transversal persistente de todas las fuentes es ampliación. Sin correspondencia suficiente, declarar la incertidumbre.

### 3. Señalar sobre el dibujo para pedir una corrección

**Problema.** Describir «esa hoja de la derecha» o transcribir notas de un PDF añade ambigüedad cuando la persona ya ve el objeto.

**Propuesta.** Seleccionar una hoja o marcar una región y añadir una nota. «Pedir al asistente» transfiere ID de posición/hoja, revisión, cara y nota al popup. La IA prepara una operación tipada y el antes/después según autonomía. Dibujar una flecha por sí solo no autoriza cambios.

**Ejemplo.** Seleccionar una hoja y pedir el cambio compatible de apertura. Ver diferencia y efecto calculable por el motor. Una anotación importada conserva origen; sin correspondencia cierta, resolverla antes de aplicar. Empezar por el dibujo nativo, cuya identidad ya se conoce.

**Valor y criterio.** Reducir aclaraciones y cambios sobre el objeto equivocado. La edición manual sigue siendo la vía directa para acciones sencillas; no convertir cada clic en consumo IA. Comparar con describir el mismo cambio por texto.

**Alcance.** Refina I15 y cambios sobre selección. El contexto de selección ya es obligatorio; marcado y lectura de anotaciones importadas son ampliación. Primero selección + nota, después evaluar dibujo libre.

## Investigación adicional y límites

Cinco páginas oficiales abiertas y leídas el 18-10-2026; sin operar cuentas de estos productos ni probar la cuenta MiMo. Informan mecanismos, no demuestran ventaja comercial ni funcionalidad actual DEKOPEN.

| Fuente primaria | Hecho documentado | Aplicación propuesta |
|---|---|---|
| [MiMo: Image Understanding](https://mimo.mi.com/docs/en-US/quick-start/usage-guide/multimodal-understanding/image-understanding) | Incluye MiMo 2.6 Pro, imágenes URL/Base64 y múltiples imágenes. | Visión con el proveedor elegido. Office/PDF requieren preparación; no se deduce entrada nativa de sus binarios. |
| [Adobe: citas](https://helpx.adobe.com/acrobat/desktop/explore-pdf-spaces/view-citations.html) | Citas que abren fuente y sección, con título/página. | Acceder al origen desde el resultado; no confundir cita con validación técnica. |
| [Adobe: formatos y límites](https://helpx.adobe.com/acrobat/desktop/explore-pdf-spaces/supported-formats-limitations.html) | Lista formatos y contenido no soportado. | Matriz honesta; sus límites no se transfieren a DEKOPEN. |
| [Microsoft: fuentes](https://support.microsoft.com/en-us/microsoft-365-copilot/control-review-sources-copilot-chat) | Controles de fuentes, citas y listado consultado. | Entender qué información se usa; acceso a una obra no exige leerla entera. |
| [Autodesk: Markup Import/Assist](https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-WhatsNew/files/GUID-64CFD65E-ABD0-49A8-9218-D4E2D22BC070.htm) | Superpone PDF/PNG/JPG anotados e identifica marcas incorporables. | Referencia para corrección localizada. Nuestras operaciones sobre ventanas son una propuesta propia. |

Inspección estática del 18-10, rama `claude/v1-implementacion`, HEAD `6f78e3299d93816991fb7c2fe2a2044458fc5e7a` más cambios locales extensos: existen [extractores](../../../backend/ingest/extract.py), [ingestión de proyectos](../../../backend/ingest/service.py), [catálogo](../../../backend/ingest/catalog_service.py), [preparación multimodal](../../../backend/ai_gateway/multimodal.py) y [transporte](../../../backend/ai_gateway/providers.py). Tienen límites distintos y faltan lectores; no acreditan el flujo global. DOCX y Markdown declarado son trabajo adicional. Ninguna llamada al proveedor fue realizada en esta revisión.

## Decisión gerencial

Incorporar adjuntos completos al núcleo y a su aceptación final en 07. Después priorizar **fuentes de obra → conflictos localizados → selección con nota**, reutilizando objetos/pantallas. Cada extensión debe reducir transcripción, errores de fuente o aclaraciones. Si añade más revisión humana de la que elimina, simplificarla o descartarla.

La base manual puede consultar fuentes, editar y resolver por sus permisos; la interpretación y delegación ahorradas constituyen valor IA. MiMo sigue común y los planes varían por consumo según el contrato vigente. Sin nuevas tarifas ni promesas de memoria o formatos ilimitados.

No añadiría ahora otro dashboard ni un agente por menú. El problema observado pide continuidad, claridad y trabajo terminado. Estas propuestas se integran a recorridos existentes; no necesitan tres aplicaciones nuevas.
