# Dirección final: detalle visual, interacción y referencias

Consulta: 18-10-2026. Rama inspeccionada: claude/v1-implementacion, con cambios locales del propietario/Claude. Este documento especifica una dirección de producto; no modifica código ni acredita una nueva aceptación funcional. Ninguna apariencia se declara aprobada por este documento.

## 1. Decisiones que gobiernan esta entrega

La instrucción más reciente del dueño es la autoridad: **cotizador manual protagonista**, plan principal completo **sin IA**, dos vistas elegibles **Estudio** y **Mesa de obra** sobre el mismo modelo/datos. La IA es un **popup global opcional**; trabaja cuando se le delega una tarea. No ocupa una columna incrustada ni transforma la página principal en chat.

Estudio y Mesa de obra son composiciones de la misma aplicación. Conservan obra, posiciones, selección, borrador, cambios pendientes, validaciones, precio aplicado, revisión y permisos. Cambiar de vista no duplica proyectos, no recalcula silenciosamente ni pierde el deshacer vigente. Mesa de obra es el valor inicial recomendado. La preferencia se guarda por usuario y organización; no se impone según plan, rol o “nivel de experiencia”.

La calidad profesional proviene de tres cosas combinadas: dibujo físicamente reconocible, jerarquía que orienta una decisión y cierre operativo honesto. Una paleta bonita no corrige un plano diminuto, una acción sin responsable o un documento que oculta qué revisión representa.

## 2. Qué se revisó y qué no

Se reutiliza el dossier de quince competidores, su matriz, fuentes y 28 imágenes/fotogramas seleccionados. Esta fase volvió a inspeccionar directamente las imágenes de Logikal, V6, Klaes, RA Workshop, PrefSuite, el fotograma documental de Winart y las capturas locales de editor/corte/taller de DEKOPEN. Se releyeron páginas primarias de Logikal 3D, V6 Modules y 3E Mobile Solutions.

Las capturas de competidores son material público, algunas de años anteriores. El fotograma de Winart es un momento seleccionado, no el vídeo entero. Las capturas de DEKOPEN son una revisión local anterior con fixture declarada. Se revisó código del árbol actual para contrastar documentos, controles, estados y permisos. **No se inició un stack, no se probaron cuentas privadas y no se ejecutó fabricación, firma, QR físico o CNC en esta fase.**

Referencias del dossier: [evidencia visual](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-revision-profunda/evidencia-visual.md), [auditoría acotada](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-revision-profunda/auditoria-dekopen.md), [matriz completa](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-revision-profunda/matriz-completa.md), [fuentes](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-revision-profunda/fuentes.md).

La guía [emil-design-eng](C:/Users/alios/.agents/skills/emil-design-eng/SKILL.md) aporta frecuencia de uso, respuesta inmediata, origen de popovers e interrupción de transiciones. Se aplica subordinada al dueño y a las reglas vigentes de DEKOPEN: no se adoptan sus sugerencias de blur, rebote o stagger decorativo.

La ampliación [05 · Referencias profesionales](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/05-referencias-profesionales.md) añade 17 fuentes oficiales de Apple, Pentagram, Adobe, Shapr3D e IBM/Carbon y las relaciona con tres fuentes sectoriales ya estudiadas. Se leyeron documentos y fragmentos de transcripciones; se observaron tres imágenes oficiales adicionales. No se operaron esas aplicaciones ni se reprodujeron sus vídeos. La guía [apple-design](C:/Users/alios/.agents/skills/apple-design/SKILL.md) orientó la revisión; sus ejemplos se contrastaron con fuentes primarias. El §14 concreta las mejoras transferibles sin convertir DEKOPEN en una copia visual de esas marcas.

## 3. Contraste entre código actual y dirección elegida

Esta tabla cumple el formato de revisión de la guía de diseño. “Actual” significa código o captura citados; “Propuesto” es una decisión de esta entrega.

| Before | After | Why |
|---|---|---|
| El editor capturado deja frontal al 19 %, planta extensa e inspector permanente compitiendo. | Frontal dominante con ajuste al área útil; planta contextual plegable y un inspector por selección. | El usuario debe poder leer el objeto que modifica sin reparar el zoom primero. |
| Cabecera combina muchos selectores, precio, estado, acciones y nombres de fixture largos. | Dos bandas: identidad/acción de obra y herramientas de la posición; el precio tiene zona estable propia. | Diferencia dónde está, qué está editando y qué acción compromete trabajo. |
| El asistente está diseñado en la constitución para compartir riel con inspector. | Botón global discreto que abre popup superpuesto opcional, independiente del inspector. | Cumple la nueva preferencia y devuelve ancho al cotizador manual. |
| La página de corte dice optimizar sin ofrecer a ESTIMATOR una salida equivalente. | Con permiso: “Optimizar corte”; sin permiso: requisito, rol responsable, abrir resumen y actualizar. | La autorización correcta debe permitir entender cómo se desbloquea el trabajo. |
| Un paso muestra “Listo” mientras no existe plan vigente. | Separar selección de estado; mostrar requisito “Sin plan vigente” y estado real de estación. | Preparado, seleccionado y terminado son conceptos distintos. |
| Hay gramática real de controles: primario sólido, secundarios con borde y foco de 2 px. | Conservarla y auditar su aplicación; los controles clave no se convierten en enlaces tenues. | La base ya resuelve parte del reclamo de monocromía; el problema exige jerarquía consistente. |
| ErrorState añade recomendación genérica de conexión a errores de dominio. | Error específico con objeto, causa y recuperación; conexión solo si es la causa real. | Evita pedir reintentar una acción que necesita datos o un permiso diferente. |
| El editor documental ya renderiza un PDF borrador y permite deshacer composición. | Darle navegación documental, selecciones claras y preview honesto sin reemplazar su renderer. | Mejorar la experiencia no debe crear una maqueta que diverge del PDF emitido. |
| Existen tres plantillas comerciales y variantes de taller en código. | Composiciones completas con tareas y tipografías propias, todas ligadas al mismo snapshot. | Cambiar color o cabecera no produce tres diseños distintos. |
| Existen etiquetas, direcciones físicas y retazos previstos en el plan. | Reutilizar sus identidades entre plano, corte, estación, etiqueta y terreno. | Cambiar nombres en cada salida rompe la continuidad que el software debe garantizar. |

Código observado: [Controls.css](C:/Users/alios/Downloads/framedex/frontend/src/ui/Controls.css:1), [States.tsx](C:/Users/alios/Downloads/framedex/frontend/src/ui/States.tsx:1), [QuotationDocument.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/projects/QuotationDocument.tsx:130), [ProductionPage.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/production/ProductionPage.tsx:1301), [OperatorStation.tsx](C:/Users/alios/Downloads/framedex/frontend/src/features/production/OperatorStation.tsx:387), [workshop_layouts.py](C:/Users/alios/Downloads/framedex/backend/documents/workshop_layouts.py:1).

## 4. Composición de Estudio y Mesa de obra

### 4.1 Estructura común

La barra global mide 56 px. Incluye marca, contexto de organización, búsqueda y botón Asistente de 38 px; no incorpora un formulario conversacional. La navegación global usa un riel compacto de 64 px con texto accesible y etiquetas al enfocar/pasar el mouse; sus nombres completos permanecen en la navegación expandida. La vista del proyecto conserva Ventanas, Cotización, Materiales y Actividad, sin duplicar acciones de fabricación en cada pestaña.

La cabecera de obra ocupa 56 px como base y crece si el nombre requiere dos líneas. Nombre 20/26, cliente y revisión 13/18. A la derecha: selector Estudio/Mesa de obra y una acción principal coherente con el momento. La emisión pertenece a Cotización, optimizar al trabajo de Corte y confirmar fabricación al flujo de taller; no son tres primarios simultáneos en la cabecera.

El selector de vista es un grupo de dos botones con nombre, indicador seleccionado y área de 38 px. No es un selector de tema. Conserva foco y scroll lógico; cambiar Mesa/Estudio sobre la misma edición no pide confirmación, no guarda ni descarta. Elegir otra posición o salir de la obra con cambios sí conserva Guardar/Descartar/Cancelar en ambas vistas.

### 4.2 Estudio: precisión sobre el objeto

Distribución de referencia en escritorio, después del riel global:

| Ancho de viewport | Área restante | Navegador de posiciones | Separadores | Canvas útil | Inspector |
|---|---:|---:|---:|---:|---:|
| 1.440 px | 1.376 px | 160 px | 32 px | 864 px | 320 px |
| 1.280 px | 1.216 px | cerrado; abre bajo demanda | 16 px | 880 px | 320 px |
| 1.024 px | 960 px | cerrado | sin riel permanente | 960 px antes de márgenes de hoja | drawer contextual de 320 px |

Son presupuestos de composición, no tamaños de fabricación. El canvas conserva al menos 60 % del ancho de trabajo en estos tres casos; a 1.024 px el inspector se abre bajo demanda. No añadir márgenes o un segundo riel que reduzcan esos valores sin resolver la composición.

El navegador de posiciones muestra código humano, miniatura, ambiente y estado breve. Si está cerrado, “Ventanas · 12” abre una lista temporal y regresar a la posición mantiene su selección. La cifra procede del proyecto real; no se fija como contenido.

La barra de herramientas mide 44 px y agrupa Seleccionar, Dividir, Apertura, Cotas y Deshacer/Rehacer. 2D/3D y Vista interior/exterior viven en el grupo de visualización, separados de herramientas que modifican datos. La herramienta seleccionada tiene tinte y borde; cada acción decisiva lleva texto. “Avanzado” no compite con apertura, ancho, alto, vidrio y acabado.

Inspector: 320 px, margen interior 16 px, grupos separados por 24 px y campos por 12 px. Encabezado “Ventana P-03”, “Hoja 2” o “Montante 1”, con el objeto elegido como verdad principal. Un botón Cerrar selección devuelve al conjunto. Muestra primero medidas, apertura, vidrio y acabado compatibles; autoridad, perfiles, herrajes y procesos se despliegan después. No duplicar inspector completo dentro de un popup secundario.

El pie de cálculo mide 36 px y conserva ubicación estable: “Sin calcular”, “Calculando”, “Válido”, “Requiere revisión” o “No se pudo calcular”; precio con moneda y base, guardar y causa accionable cuando corresponde. Un precio anterior debe indicar “Precio anterior · cambió el diseño” hasta tener resultado nuevo. Guardar no se vuelve emitir.

### 4.3 Mesa de obra: recorrido de posiciones y precio

La superficie central es una colección de posiciones agrupable por ambiente/piso, con encabezados de grupo y una tabla legible, no una cuadrícula de tarjetas de igual importancia.

Columnas base: selección; posición y miniatura; ambiente/nombre; sistema/serie; medidas; cantidad; vidrio/acabado; unitario; total; estado/menú. La miniatura debe medir aproximadamente 80 × 64 px en lectura cómoda y mantener proporción real. Las columnas de valor se alinean a la derecha; los encabezados incluyen unidad o la celda la declara. Al reducir ancho se combinan sistema y acabado en una celda de dos líneas y se desplaza información secundaria al detalle de fila, sin scroll horizontal global.

La fila de lectura tiene 80 px cuando contiene elevación y especificación. La edición activa puede crecer; no encoger campos para obligarlos a caber en una sola línea. Las tablas operativas de materiales usan 40 px; no imponer la altura de galería técnica a todo el sistema.

Seleccionar una fila abre su detalle y su preview, manteniendo las demás posiciones. Doble clic en dibujo es un atajo al mismo editor amplio en esa posición, conservando la vista elegida y su retorno; también existe botón textual y Enter. Cambiar cantidad/ancho/alto manualmente usa los mismos comandos/validaciones que Estudio. Al salir del campo se valida; Enter confirma el grupo y Escape revierte la edición local. La pérdida de foco no emite, borra ni acepta una cotización.

La selección múltiple ofrece una barra contextual única: “3 ventanas seleccionadas”, Cambiar vidrio, Cambiar acabado, Duplicar y Más. Un cambio en lote presenta afectados, incompatibles y efecto de precio cuando exista cálculo; nunca inventa un delta. El total de obra queda en un cierre comercial estable con neto/impuesto/total según configuración. Los faltantes no se sustituyen por ceros.

### 4.4 Catálogo que acompaña a ambas vistas

La ficha de sistema presenta fabricante, serie, material, miniatura de ventana y sección de perfil cuando exista fuente. Para Proline, sus series pertenecen a Proline; las revisiones se archivan dentro de la serie. No crear una tarjeta de marca por cada versión.

Separar “Disponible en biblioteca” de “Apto para cotizar”, “Apto para fabricar” y “CNC validado”. Cada aptitud abre evidencia y faltantes. Una imagen pública sirve de referencia visual con atribución; no autoriza precio, fórmula o mecanizado. Sin imagen autorizada, usar dibujo propio derivado de geometría conocida y rótulo “Imagen de referencia pendiente”; no inventar una fotografía ni dejar el catálogo vacío sin ruta útil.

## 5. Gramática visual concreta

### 5.1 Color, superficies y contraste

Conservar la base de Plex y el vocabulario de tokens actual, corrigiendo aplicación y contraste donde falle. La diferencia entre app y papel debe ser visible: mesa #F4F6F7, panel blanco, relleno inset #EEF2F1, hoja/documento blanco con borde definido. Un control usa borde #B4BFC1; una regla estructural usa #E0E6E5. Son papeles distintos.

| Función | Apariencia | Lectura buscada |
|---|---|---|
| Acción principal | Teal #075F5A, texto blanco, peso 600, borde del mismo relleno | “Esta acción avanza el trabajo”. |
| Acción secundaria | Blanco, borde de control, tinta #161C1F, peso 500 | “Se puede pulsar aun sin hover”. |
| Navegación/enlace | Teal #0B7770, subrayado cuando está en un párrafo | “Abre otro lugar o detalle”. |
| Selección | Fondo #E6F4F2 + contorno #0F8F85 + indicador/etiqueta | “Este es el objeto actual”. |
| Edición activa | Campo blanco, borde/foco, unidad visible y estado de validación | “Este valor se puede modificar”. |
| Correcto | Fondo verde suave #E3F2EA y texto #13502F con nombre de estado | “Requisito cumplido”. |
| Advertencia | Fondo #FDF1E3 y texto #7A3D05 con causa | “Hay una condición que revisar”. |
| Bloqueo/error | Fondo #FBE9E7 y texto #7E1F19; icono y acción | “Esta operación no puede continuar”. |
| Requiere persona | Naranja #E56A32 como marcador; texto oscuro #A84418 sobre #FBEBE2 | “Hay una decisión humana pendiente”. |

El vidrio y los acabados aportan riqueza material; no pintar módulos con colores arbitrarios. El naranja no sirve para todos los botones. Un relleno verde no convierte “seleccionado” en “terminado”. Texto normal debe cumplir 4,5:1; texto grande y límites esenciales de controles, 3:1 según su categoría. Estos objetivos se calculan sobre pares reales al final; no se declara “AA” por haber copiado un hex. Evitar g-500 como cuerpo pequeño sobre un fondo gris.

### 5.2 Tipografía y espacio

| Uso | Tamaño/interlínea/peso | Detalle |
|---|---|---|
| Título de página | Plex Sans 24/30, 600 | Uno por superficie. |
| Nombre de obra/contexto | Sans 20/26, 600 | Permite dos líneas. |
| Título de sección/popup | Sans 18/24, 600 | No todo en mayúsculas. |
| Grupo/inspector | Sans 15/20, 600 | Empieza una decisión real. |
| Cuerpo y campos | Sans 14/20, 400/500 | Siempre legible en escritorio. |
| Tabla compacta | Sans 13/18 | Valores comerciales con cifras tabulares. |
| Ayuda/metadato | Sans 12/16 | No contiene la única explicación decisiva. |
| Medida/código | Plex Mono 13/18 | Cotas de canvas, mínimo 11–12 px en pantalla. |
| Taller | Cuerpo 16/24; código ≥32/40; medida 28/36 | Se reconoce a distancia. |

Espaciado: 4, 8, 12, 16, 24, 32, 48; 2 y 6 solo en ajustes ya tokenizados. Distancia etiqueta/campo 6 px; campos de un grupo 12 px; grupos 24 px; secciones mayores 32 px. Una lista densa reduce altura, no elimina la distinción entre etiquetas y valores.

Radios: 6 px controles, 8 contenedores, 12 popup/diálogo, 0 papel. Bordes para estructura; sombras E2 solo en menú/popover y E3 en popup/diálogo. No encadenar tarjetas dentro de tarjetas para crear jerarquía. Prohibidos blur, glow, degradados decorativos y morado para IA.

Controles de oficina: altura base 38 px; compacto explícito 32 px solo en herramientas/tabla; táctil ≥48 px. Botón principal lleva verbo y objeto cuando evita ambigüedad: Guardar ventana, Emitir cotización, Optimizar corte. El icono sin texto se reserva para acciones frecuentes inequívocas y siempre tiene nombre accesible.

### 5.3 Números, unidades y procedencia

Medidas: 2 400 × 1 800 mm; moneda CLP: $1.435.471; cantidades comerciales con cifras tabulares de Sans; medidas/códigos en Mono. Usar los formateadores existentes y el Decimal de la autoridad. El formateo puede redondear una presentación según política, nunca alterar el valor que alimenta corte, precio o impresión.

En superficies comerciales, el dato importante es el precio aplicable. En taller, longitud, dirección, pieza y siguiente paso. La traza “¿De dónde sale?” abre entradas, regla, revisión de catálogo y versión de motor; no se vuelca todo eso en cada celda.

“Sin dato” lleva causa y recuperación cuando el dato es necesario. Cero solo se muestra si la autoridad devuelve cero real. Un total parcial debe decir qué excluye.

## 6. Selección, render y aperturas

### 6.1 Cuatro estados independientes del dibujo

| Estado | Tratamiento | Prohibición |
|---|---|---|
| Reposo | Material, perfiles, vidrio y simbología legibles | Toda la ventana teal por ser interactiva. |
| Hover con puntero fino | Contorno breve del objeto y nombre localizado | Elevación de toda la tarjeta o reencuadre automático. |
| Selección | Contorno 1,5–2 px y tinte localizado del miembro/hoja, manijas con borde blanco | Teñir vidrio, marco y otros módulos indiscriminadamente. |
| Previsualización/ inválido | Trazo discontinuo y rótulo; inválido añade patrón/causa | Mostrar como aplicado un cambio todavía propuesto. |

Foco de teclado y selección son distintos: foco rodea el control actual; selección identifica el objeto. La selección se conserva entre 2D y 3D cuando el objeto existe. Si deja de existir después de una operación válida, volver al ancestro más próximo y anunciarlo; no conservar un inspector de un objeto borrado.

### 6.2 Ventana creíble

La geometría deriva del modelo. Espesores visuales, nudos, montantes, travesaños, refuerzos y manillas se representan según datos disponibles. No exagerar todos los perfiles con una misma doble línea para “dar profundidad”. Vidrio tiene tinte muy tenue; panel opaco es materialmente diferente. Los acabados interior/exterior no se intercambian al cambiar punto de vista.

Las cotas mantienen tamaño de lectura en pantalla y se colocan fuera de la geometría cuando es posible. Medida total y parcial relevante para selección no se solapan; las flechas y líneas de extensión usan un sistema único. La vista dice Interior/Exterior y conserva una referencia lateral en frontal/planta. No copiar coeficientes o descuentos de un tutorial competidor.

El ajuste de vista usa bounding box de geometría y cotas, con margen útil; nunca un zoom fijo de 19 %. Si se abre el inspector o cambia el tamaño del viewport, conservar encuadre del objeto seleccionado y ofrecer Ajustar. No reiniciar el zoom por cada cálculo de precio.

La planta es obligatoria cuando explica carriles o un acople y se puede plegar. En la edición frontal no debe ocupar por defecto media altura. Sus rótulos deben distinguir ancho desarrollado, frente/cuerda y proyección según geometría real. No ocultar esa información para “limpiar”; priorizarla según tarea.

### 6.3 Apertura como acción verificable

Al seleccionar una hoja, Apertura muestra tipo, mano/bisagras y dirección admitidos por su serie. El preview usa el mismo renderer que el resultado; una flecha no reemplaza la cinemática física. La manilla permanece del lado de cierre según la receta. Activa/pasiva, correderas y encuentros requieren información específica, no un flip genérico de SVG.

Acciones de vista no modifican apertura. Cambiar mano no invierte todas las hojas del conjunto. Un cambio incompatible muestra cuál requisito falla y una alternativa válida si el motor la ofrece. El sistema no ofrece una apertura sin autoridad para simular completitud.

2D sirve para cotas/simbología y 3D para comprensión material/pose. Si un navegador no puede renderizar 3D, se conserva 2D y se explica la limitación; no fingir que una imagen plana es un modelo 3D.

Referencia visual observada: [Logikal](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/logikal-editor.png). Muestra conjunto dominante, cara declarada y vista separada de edición. Su manual documenta animación de elevables-correderas; no acredita todas las aperturas ni exactitud de DEKOPEN.

## 7. Estados y microinteracciones

### 7.1 Estados de superficie

| Estado | Contenido mínimo | Acción concreta |
|---|---|---|
| Vacío inicial | Qué falta y por qué la colección está vacía | Crear primera ventana o elegir serie real. |
| Vacío filtrado | Filtro actual y ausencia de coincidencias | Limpiar filtro; no sugerir importar de nuevo. |
| Cargando | Reserva de la forma final y objeto que se carga | Cancelar cuando sea una operación larga cancelable. |
| Error de red | Qué no llegó, conservación de cambios | Reintentar sin duplicar operación. |
| Dato inválido | Campo/objeto y restricción concreta | Ir al dato o volver al último válido. |
| Sin permiso | Operación, rol responsable y camino permitido | Abrir resumen/volver; no mostrar un botón muerto. |
| Bloqueado por requisito | Requisito, causa y responsable | Ir al lugar exacto o actualizar tras resolución. |
| Obsoleto | Qué cambió y qué resultado ya no aplica | Recalcular/reoptimizar mediante acción válida. |
| Solo lectura emitida | Número/revisión/fecha y razón de cierre | Crear nueva revisión con permiso. |
| Cambios pendientes | Alcance sin guardar y si el precio corresponde | Guardar o descartar explícitamente. |

No usar un único banner amarillo para todos. Carga indeterminada no muestra porcentaje inventado. Un resultado “Terminado” requiere sus postcondiciones, no solo una respuesta HTTP o fin de texto de IA.

### 7.2 Movimiento que ayuda al oficio

Selección, cotas, navegación por teclado y cambio de valor: respuesta inmediata. Hover de color/borde 90 ms; cambio visual de estado hasta 160 ms; popup/panel ocasional 180–220 ms; salida hasta 120 ms. Tope 280 ms para transiciones de controles y paneles; los ciclos expresivos del personaje siguen su contrato específico. Animar propiedades concretas, sin transition: all. Una transición se interrumpe desde el punto actual; nada espera a que termine una animación para aceptar Escape.

Popovers nacen de su disparador. Popup centrado en móvil tiene origen propio, sin volar desde otra esquina. Al abrir por atajo, no añadir desplazamiento animado. Sin stagger de posiciones ni cifras que suben contando. La animación propia del personaje del asistente sigue [06 · Grok Bot: personaje y movimiento](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/06-grok-bot-personaje-y-movimiento.md), manteniéndose discreta y funcional; no traslada sus gestos a cotas, campos o tablas. Reduced motion elimina desplazamientos y adapta el personaje según su contrato; hover solo para puntero fino. Las acciones repetidas de tablas/editor no tienen rebote.

Un press en oficina puede usar desplazamiento 1 px ya presente; no escalar campos, cotas o filas completas. Taller confirma con cambio de texto/estado y destino siguiente, no solo un toast fugaz.

## 8. Popup del asistente como accesorio opcional

Visualmente: figura de 28–32 px dentro de un botón Asistente con blanco interactivo mínimo 44 × 44 px, sin llamarlo a la fuerza. Popup de escritorio inicialmente 420 × 600 px, mínimo útil 340 × 420 px y siempre limitado por el viewport. Permite mover/redimensionar desde la cabecera/bordes y mediante controles accesibles, según el contrato del copiloto. No cambia el ancho del inspector/canvas ni instala una columna permanente. Mantiene historial/estado al cerrarse y al navegar.

Su cabecera muestra nombre, contexto de trabajo y cerrar. El contenido prioriza conversación o tarea delegada y resultado. El personaje y su animación siguen fielmente [06 · Grok Bot: personaje y movimiento](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/06-grok-bot-personaje-y-movimiento.md), con presencia discreta y funcional; no se sustituyen por una mascota arbitraria o robot genérico. Los estilos compatibles se adaptan a DEKOPEN; la fidelidad del personaje no impone copiar todo el chat o desktop de la referencia. No añadir parrilla de sugerencias vistosas ni bienvenida genérica. El progreso aparece solo cuando existe un trabajo. La configuración de autonomía y el contenido detallado se especifican en el contrato del asistente; aquí se fija que no toma el control sin delegación.

En escritorio modeless, no atrapar el foco ni bloquear el canvas. Cuando un diálogo realmente modal requiere una decisión humana, el fondo sí queda inerte y hay una sola superficie decisoria activa. En móvil se adapta al área útil con cabecera recuperable, minimizar/restaurar y cerrar siempre visibles, sin fingir un arrastre de escritorio. Una confirmación realmente modal mantiene sus reglas de foco. Un resultado técnico vuelve a la ventana/documento real, no a una página chat como destino principal.

La aplicación manual debe seguir siendo completa con IA desactivada, sin proveedor o sin saldo. Nunca transformar Crear ventana, Calcular precio o Emitir en acciones disponibles solo mediante un prompt.

## 9. Documentos, taller y terreno: intención visual

### 9.1 Tres lecturas comerciales

Esencial: encabezado compacto y fichas de posiciones; el cliente identifica cada ventana y el total rápidamente. Proyecto: apertura editorial con alcance/obra y elevaciones mayores; después posiciones y condiciones. Alternativas: comparación de revisiones/opciones válidas, con diferencias y totales separados; ninguna alternativa entra de nuevo al total vigente.

Las tres usan los mismos datos sellados. No son el mismo HTML recoloreado. Carta es el valor inicial configurable; margen de 14 mm como composición base, texto de cuerpo comercial 10–10,5 pt, mínimo 9,5 pt para datos secundarios. Totales con Plex Sans tabular, dimensiones en Mono. Regla fina, sin cebra ni cards de app. La página es papel de esquinas rectas.

Número comercial, cliente, obra, solución, precio y vigencia se leen antes de huellas internas. Aceptación/firma opcional; no se inventan garantía/plazo o datos del emisor. Sin contenido de relleno. El documento comercial conserva la marca del fabricante que emite; DEKOPEN no compite por atención.

### 9.2 Plano y corte son herramientas de trabajo

Plano: elevación principal, orientación declarada, cotas, sección/planta cuando resuelven ensamblaje, tabla de componentes y cajetín. No encoger un conjunto hasta volver ilegibles las cotas: dividir páginas o seleccionar un papel soportado/configurado. Conservar fuente técnica y revisión.

Corte: orden de barra/lámina y piezas, medida, ángulos, código, material/acabado, fuente de suministro y destino de sobrante. La secuencia y la lista agrupada resuelven tareas distintas. Las tres composiciones son Secuencia, Cortes idénticos y Por ventana; nunca perder identidades al agrupar.

Necesidad por obra y pedido a proveedor también son documentos distintos. La primera explica abastecimiento; el segundo compromete cantidades con un destinatario y necesita emisión/envío humanos. No llamar orden de compra a una lista interna.

### 9.3 Taller por responsabilidad

Jefe: cola priorizada con próxima estación, fecha/compromiso, bloqueo y material/plan pendiente. Las columnas vacías no dominan; se pueden mostrar como estructura de ruta reducida. Un resumen de bloqueos abre su lista filtrada; no se usa como KPI decorativo.

Operario: una tarea y una pieza dominante. Código ≥32 px, medida ≥28 px, dibujo/ángulo/destino legibles, acciones ≥48 px y preferiblemente 56 px. No muestra precios/márgenes/direcciones comerciales que el backend excluye. Escanear conserva estación elegida; no amplía permisos ni cambia de puesto silenciosamente.

Instalador: próxima visita/obra asignada, unidad, ubicación, evidencia a registrar, incidencia y cierre explícito. La cámara es opcional; código manual/lector mantienen el recorrido. Sin conexión, solo se permite lo que esté realmente implementado con confirmación pendiente visible; no anunciar guardado remoto antes de sincronizar.

## 10. Teclado, móvil y bordes reales

Orden de foco: contexto → vista → colección/herramientas → objeto → inspector → resultado. En grupos se usa navegación de flechas y un solo Tab de entrada; Tab no recorre cientos de piezas gráficas sin posibilidad de saltar a inspector. Cada icono tiene nombre; aria-live anuncia una operación terminada sin leer toda la BOM.

Atajos básicos coherentes con implementación/documentación: Ctrl/Cmd+Z, rehacer, Escape, Enter y búsqueda global. V/H y otros atajos de herramienta solo se registran si no hay un campo, select o composición IME activo. No interceptar zoom del navegador. La ayuda muestra el atajo efectivo para la plataforma.

A 390 px, Mesa de obra usa filas apiladas con dibujo, nombre, medidas, cantidad, estado y total; detalle por posición en página/panel de ancho completo. Cabecera y acción actual no tapan contenido con teclado virtual. Los formularios comerciales/manuales compatibles permanecen utilizables. Debajo de 1.024 px se conserva la lectura técnica del editor actual con motivo visible y retorno a las tareas disponibles; este encargo no promete un CAD táctil completo. La política del editor no convierte consulta de obra, documentos o terreno en solo lectura.

Tocar, mover canvas y editar una cota son gestos distintos. Las áreas de toque no alteran la geometría visual. Arrastre usa pointer capture y tolerancia de movimiento; un tap en hoja no debe crear un montante. Deshacer permanece disponible.

Texto largo: nombre de obra/cliente hasta dos líneas y acceso al completo; códigos no se cortan si son la única forma de identificar pieza. Idiomas y formatos usan glifos reales. En móvil se evita la tabla horizontal gigante; en papel se hace un salto o una nueva página antes de superponer columnas.

## 11. Trazabilidad: fuente → detalle → decisión → razón

| ID y fuente primaria/evidencia | Detalle observado o documentado | Decisión para DEKOPEN | Por qué y límite |
|---|---|---|---|
| R01 · [Logikal 3D manual](https://help.orgadata.com/en/documentation/input-of-elements/user-interface/3d-view/) | DOC: vistas inside/outside/laterales y rotación; animación L/S descrita. | Cara declarada y controles de vista separados de edición/apertura. | Evita interpretar un cambio de cámara como cambio físico. No se ejecutó Logikal. |
| R02 · [captura Logikal](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/logikal-editor.png) | VIS: conjunto grande, cotas externas, perfiles/material y etapas separadas. | Estudio dedica ≥60 % al canvas y mantiene orientación/cotas legibles. | El objeto debe guiar la tarea; no copiar ribbon ni densidad. |
| R03 · [V6 Modules](https://www.cyncly.com/en-GB/products/soft-tech-v6/modules) | DOC: Drawing genera dibujos de taller y PDF desde diseños; Automation es otro módulo. | Plano derivado de la revisión; exportación de plano no se anuncia como CNC. | Separa comunicación técnica y posprocesador validado. No se probó precisión. |
| R04 · [plano V6](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/v6-drawing.jpg) | VIS: elevación, sección horizontal/vertical, herrajes y cajetín. | Plano con vistas complementarias y cajetín técnico, no captura del canvas. | Cada vista resuelve un montaje; los valores/unidades del ejemplo no se transfieren. |
| R05 · [Klaes tour](https://www.klaes.de/en-tour) y [captura](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/klaes-editor.png) | VIS histórica 2019: dibujo por posición junto a descripción y precio. | Mesa de obra conserva miniatura y especificación de cada ventana. | Reconocimiento por objeto y ambiente reduce lectura de códigos; no copiar su cromo antiguo. |
| R06 · [PrefSuite manual](https://prefsuite.zendesk.com/hc/pt-br/articles/34430593841684-PrefSuite-N%C3%ADveis-de-folhas) y [imagen](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/prefsuite-leaf-levels.jpg) | VIS/DOC: niveles de hoja/cotas diferenciados y flechas de corredera. | Cotas total/parcial/útil rotuladas y planta de carriles cuando corresponde. | Muestra que dos medidas no son intercambiables; no adoptar descuentos del ejemplo. |
| R07 · [RA Workshop manual](https://help.raworkshop.bg/docs?lang=bg&url=https://www.raworkshop.com/Help/Ra%2520Workshop/4.1/en/topics/profile-system-overview.htm) y [captura](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/ra-profile-systems.png) | VIS: proveedor, familia, tipo y material; fila seleccionada legible. | Marca/serie/material separados y selección visible en catálogo. | Facilita encontrar un sistema; no prueba un árbol anidado o Proline. |
| R08 · [Windowmaker Web](https://windowmaker.com/windowmaker-web/) y [frame170](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/windowmaker-asistente-frame170.png) | VIS: asistente sobre cotizaciones con chips de herramientas. | Asistente opcional que conserva contexto y muestra resultados reales. | Se toma la continuidad, no su columna: el dueño pide popup. No se probó memoria/autonomía. |
| R09 · [Windowmaker R4](https://windowmaker.com/wp-content/uploads/2026/02/WINDOWMAKER-2025-R4-0-0-Release-Document.pdf) | DOC: cambios globales, revisiones y precio congelado/recálculo. | Diferenciar cambios de diseño, precio vigente y precio aplicado. | Impide repricing silencioso. Notas internas 29-12-2025; no ensayo. |
| R10 · [FeneVision permisos](https://fenevision.support.cyncly.com/hc/en-us/articles/33380224362641-Managing-User-Permissions-in-FeneVision) | DOC: permisos efectivos por usuario/grupo. | Los controles explican quién puede actuar y cuál permiso falta. | Ocultar botón no explica el bloqueo; documento no acredita seguridad de DEKOPEN. |
| R11 · [FeneVision unposting](https://fenevision.support.cyncly.com/hc/en-us/articles/45201059625873-Unposting-Documents-in-FeneVision) | DOC: compensación en lugar de despublicar documentos contabilizados. | Separar deshacer, nueva revisión y transacción compensatoria. | La UI debe conservar la verdad histórica. No copiar su modelo contable sin dominio propio. |
| R12 · [Matrix Supplier Import](https://knowledge-base.matrix-software.com/nl/help/matrix-windows/manual-and-use/supplier-import) | DOC: datos provienen del proveedor; mapeo y rechazos explícitos. | Catálogo real con procedencia y estado por capacidad. | Un PDF en internet no es un catálogo de fabricación validado. |
| R13 · [3E mobile](https://www.3e-it.com/en/window-design-software/mobile-solutions) | DOC: datos por componente, evidencia de campo y firma; NFC. | Terreno abre la unidad y su tarea, con evidencia específica. | El valor está en identidad/continuidad; NFC no se renombra QR. |
| R14 · [Winart tutorial 04:35](https://www.youtube.com/watch?v=26qVxUTQP3A&t=275s) y [fotograma](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/winart-tutorial-04-35.png) | VIS: PDF Plan de Ejecución con herrajes/accesorios separados. | Listas de taller agrupadas por tarea/material con códigos y cantidades. | El operario busca una familia concreta; no copiar valores o aceptar legibilidad sin render final. |
| R15 · [3E producción](https://www.3e-it.com/en/window-design-software/digital-production) | DOC: estaciones y seguimiento de unidades. | Cola por estación y pieza, con siguiente paso y condición de inicio. | La ruta real orienta; no se afirma haber usado la suite. |
| R16 · [SchüCal brochure 2023](https://www.schueco.com/resource/blob/4249866/bd6e3252f6b70a93524d9f7b7ab3d2d1/digital_solutions_brochure_en.pdf?domain=no) | VIS en PDF p16: ecosistema por oficina, construcción y fabricación. | Distinguir venta, taller y terreno sin duplicar modelo. | Es diagrama comercial histórico, no evidencia de sincronización real. |
| R17 · [DEKOPEN editor](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/dekopen-apertura-derecha.png) | RUN/VIS previa: selección funcional y frontal pequeño. | Conservar capacidades y recuperar área útil del dibujo. | No llamar rota a toda apertura; el fallo concreto requiere matriz final. |
| R18 · [DEKOPEN corte](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/dekopen-corte-sin-accion.png) | RUN/VIS previa: requisito sin acción y “Listo” ambiguo. | Estado por requisito, responsable y salida permitida por rol. | La carencia de permiso no debe parecer fallo del optimizador. |
| R19 · [DEKOPEN taller](C:/Users/alios/Downloads/framedex/.run/revision-profunda/capturas/dekopen-taller.png) | RUN/VIS previa: 175 OT de fixture sin plan y columnas vacías. | Cola filtrada/priorizada y estado vacío de filtro preciso. | No usar conteo sintético como prueba de negocio real. |
| R20 · [Controls.css](C:/Users/alios/Downloads/framedex/frontend/src/ui/Controls.css:1) | CODE: primario teal, borde de secundario, foco 2 px y press 1 px. | Reusar y aplicar la gramática a todos los recorridos. | Evita rediseñar primitivas ya correctas y dejar dos sistemas paralelos. |
| R21 · [QuotationDocument](C:/Users/alios/Downloads/framedex/frontend/src/features/projects/QuotationDocument.tsx:130) | CODE: preview real, borrador sin número, historial de composición y bloques obligatorios. | Editor documental sobre renderer canónico. | Un mock de PDF no es la versión final ni coincide necesariamente con lo emitido. |
| R22 · [workshop_layouts](C:/Users/alios/Downloads/framedex/backend/documents/workshop_layouts.py:1) | CODE: cortes compactos/por ventana y requerimiento por obra con aviso interno. | Mantener tres tareas documentales y su autoridad sellada. | No convertir el requerimiento interno en compra externa por cambiar su título. |
| R23 · [OperatorStation](C:/Users/alios/Downloads/framedex/frontend/src/features/production/OperatorStation.tsx:387) | CODE: pieza, medida, siguiente, gates del plan y acciones reales. | Una pieza dominante y recuperación de bloqueos por responsable. | Mantiene seguridad de la estación y vuelve evidente el siguiente paso. |
| R24 · [emil-design-eng](C:/Users/alios/.agents/skills/emil-design-eng/SKILL.md) | Guía: frecuencia, foco, origen e interrupción de movimiento. | Respuesta instantánea en editor; transiciones breves en popup ocasional. | El ritmo del oficio importa más que mostrar animaciones. |

## 12. Divergencias y riesgos que Claude debe resolver

1. La constitución actual pide asistente compartiendo riel y catálogo DEMO por defecto. La instrucción posterior del dueño cambia ambos. Al implementar se deben actualizar los apartados correspondientes y sus guardas, manteniendo invariantes; esta investigación no edita la constitución.
2. Los nombres Estudio/Mesa de obra pueden confundirse con densidades office/workshop. Son conceptos distintos: las vistas son elección del cotizador; workshop es adecuación de tamaño por tarea/rol.
3. Varias capacidades documentales ya existen en el árbol sin commit; deben integrarse y mejorar, no reinstalar otra versión paralela ni regenerar históricos emitidos.
4. El catálogo real puede tener autoridad parcial. No bloquear toda revisión por falta de CNC si solo se cotiza; tampoco habilitar fabricación con una referencia visual. Exponer el límite por capacidad.
5. El código de corte usa float/Number para dibujo en ciertos lugares; cualquier revisión visual debe mantener el valor Decimal canónico para cálculo/exportación. Cambiar escala de SVG nunca cambia corte.
6. Una agregación de obra no debe convertir varias OT históricas por posición en una OT artificial ni perder unidad/pieza al agrupar.
7. El popup global puede competir con menús, teclado o un diálogo de emisión. Resolver una sola superficie decisoria activa y restauración de foco; no bloquear interacción de fondo si es modeless.
8. Las capturas y los tests históricos no certifican esta futura versión. La batería integrada y el pase editorial se ejecutan al final del encargo completo, con evidencia nueva y límites honestos.

## 13. Cierre exigible en el encargo completo

No hay rondas de aprobación ni batería por cada etapa. Claude desarrolla el paquete como un trabajo continuo y ejecuta la batería común al terminar todos los prompts, corrigiendo los fallos antes de la entrega final.

El cierre visual incluye 1.440, 1.280, 1.024 y 390 px; ambos modos manuales; IA cerrada/desactivada; estados vacío/carga/error/sin permiso/bloqueado; selección y foco; aperturas compatibles; documento de pocas y muchas posiciones, nombres largos y alternativas; corte/retazo/QR por rol. Los PDFs se renderizan y se inspeccionan como páginas completas: no basta que el HTML compile.

El cierre conserva motor como fuente, Decimal, RLS por org_id, snapshots emitidos inmutables e idempotencia. Emitir, enviar, comprar, cobrar, liberar fabricación y exportar una salida industrial consecuente conservan el clic humano autorizado que corresponda. No se declara terminado un recorrido si solo existe una captura o un botón sin efecto.

## 14. Refinamientos derivados de referencias profesionales

El detalle de fuente, evidencia, decisión, razón y límite está en [05 · Referencias profesionales](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/05-referencias-profesionales.md). Las siguientes precisiones forman parte de esta dirección y se integran en el trabajo continuo, con comprobación final común en 07.

| Área | Refinamiento concreto | Referencias y motivo |
|---|---|---|
| Jerarquía | Roles completos de tamaño/interlínea/peso; campos, valores y ayudas legibles. Reflujo al crecer texto, sin bajar contraste para “limpiar”. | P01/P02/P17: tipografía consistente expresa importancia con pocos recursos. Se conserva Plex y no se copian métricas nativas de Apple. |
| Inspector | Encabezado de entidad; sin selección, contexto útil; con selección, propiedades pertinentes; con varias, cantidad/valores Varios y acciones comunes compatibles. | P06/P09/P13: el alcance del cambio se entiende antes de aplicarlo. Un valor mixto no se reemplaza por el de la primera ventana. |
| Selección | Distinguir hover, selección y foco. Desambiguar entidades superpuestas y sincronizar árbol/lienzo/inspector. Aumentar área de impacto sin alterar dimensiones físicas. | P14: control preciso sobre qué parte recibe la edición. No importar un CAD completo ni sus fórmulas. |
| Mesa de obra | Abrir detalle, seleccionar para lote y menú tienen blancos propios. Un doble clic abre el mismo editor amplio, conservando vista de retorno y sesión. | P05/P16: colección, trabajo sobre objeto y propiedades resuelven tareas distintas, sin duplicar modelos. |
| Identidad y soportes | Gramática común de títulos, proporciones y reglas; composición específica para oferta, plano, corte y etiqueta. Revisar marca a tamaño real antes de necesitar variante óptica. | P07/P08: coherencia permite variedad. No rediseñar la marca ni copiar logos, glifos o Metro. |
| Documentos | Estilos por función; ámbito obra/empresa explícito. Problemas localizables por página/posición y orden lógico del texto exportado. El PDF conserva texto seleccionable; accesibilidad etiquetada solo se anuncia si está implementada y comprobada. | P10/P11/P12/P15: composición y lectura son partes del mismo documento. Revisión editorial no equivale a validación industrial. |
| Respuesta | Feedback inmediato a selección/press; confirmación persistida para guardado/emisión/avance físico. Interrupción de panel y foco de retorno. | P03/P04: rapidez visual no permite anunciar un éxito aún no confirmado. El popup continúa modeless. |

Las herramientas contextuales y operaciones por lote pertenecen al cotizador manual; no se reservan al plan IA. El personaje autorizado conserva su contrato [06](C:/Users/alios/Downloads/framedex/docs/research/2026-10-18-direccion-final/06-grok-bot-personaje-y-movimiento.md). Las referencias Apple no añaden glow, glass, blur o rebotes a las superficies manuales, ni cambian los tamaños, permisos y límites ya fijados.

