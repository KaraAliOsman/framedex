# Prompts preparados para la implementación

[Volver al plan](README.md) · [Orden y dependencias](07-ejecucion.md)

**Autorizado con «ahora empieza», 17-10-2026.** Estos son los encargos originales,
no instrucciones para reconstruir lo ya hecho. Consultar primero
[implementación y pendientes](10-implementacion.md). El prompt maestro permite
ejecutar el programa completo; los paquetes permiten continuar una parte sin
depender de la memoria del chat. Se usan el ref y el estado local del momento de
inicio, no se restaura el commit auditado.

## Prompt maestro

```text
Inicia el rediseño integral de experiencia de DEKOPEN descrito en
docs/ux/2026-10-17/. El dueño ya autoriza implementar; trabaja hasta completar
el recorrido y preparar el resultado revisable, sin pedir aprobaciones de cada
pantalla o elección reversible.

Primero lee AGENTS.md, inspecciona rama/git status y preserva trabajo ajeno.
Lee docs/ux/2026-10-17/README.md y 07-ejecucion.md; consulta los demás capítulos
según el paquete. Usa docs/wiki/index.md para llegar al código actual. No vuelvas
a ejecutar la cola histórica ni asumas que su aceptación demuestra buena UX.

Objetivo: una herramienta de ventanas práctica, sencilla, agradable, inteligente
y profesional. La ventana es el centro; el sistema deriva y recuerda lo común.
Cliente/datos administrativos se piden cuando se necesitan. Los detalles de
backend, jobs, autoridades y trazas no dominan el trabajo habitual.

Implementa P01–P12 de 08-prompts.md, atendiendo dependencias y completando cada
recorrido. Se puede adelantar el trabajo de datos de catálogo que necesite el
renderer. No entregues una nueva capa visual que deje el flujo viejo por debajo.
Un solo tema definitivo: usa la dirección clara/neutra propuesta como punto de
partida y afínala con criterio. No construyas un segundo tema.

Usa apple-design y emil-design-eng para criterio de interacción, jerarquía y
detalle, sin copiar marcas. Lee las skills pertinentes cuando correspondan;
no acumules herramientas ni instales dependencias sin una necesidad concreta.
No crees subagentes sin autorización posterior aplicable.

Respeta la preferencia del dueño: durante construcción, céntrate en diseño y
calidad. Mira el resultado en el navegador para poder diseñarlo. No ejecutes
suites/gates por cada cambio, no inventes tests que reflejen el JSX ni generes
cientos de reportes de aceptación intermedios. Mantén un único registro breve
de pendientes. La campaña de pruebas, regresión y bug fixing va en P12 al final.
Corrige antes solo lo imprescindible para seguir construyendo.

Conserva la autoridad del motor/Decimal, org_id/RLS, costos por permiso,
identidades estables y revisiones/documentos emitidos inmutables. La IA usa las
mismas operaciones del dominio. Datos industriales sin fuente quedan pendientes.
Preparar es reversible; enviar, emitir, comprar, pagar o liberar requieren la
acción humana correspondiente en el producto. No fabriques una conexión real
con un stub ni conviertas el catálogo DEMO en autoridad comercial/industrial.

Si hay cambios API, hazlos en backend y regenera OpenAPI/orval. Si una regla
visual antigua contradice la intención reciente, actualiza la autoridad de
diseño y sus controles de estilo explícitamente; no elimines guardas de cálculo,
seguridad o inmutabilidad. No cambies fórmulas para acomodar una imagen.

Reutiliza el stack y datos del dueño cuando su estado importe; lee la skill
testing-framedex antes de arrancar/reconstruir. No limpies .run, bases, perfiles
o contenedores por conveniencia. Trabaja en el checkout adecuado, sin perder
cambios ajenos. Los cambios se entregan por PR según el repositorio; el cierre
de CI se concentra después de integrar el trabajo, sin debilitar checks.

Al terminar: una experiencia conectada de obra → diseño → IA/catálogo → propuesta
→ materiales/taller, resto de superficies consistente, documentos renderizados,
campaña final completada, errores corregidos y límites reales declarados.
Resume qué cambió y por qué, evidencia seleccionada, pruebas finales y pendientes
concretos. No declares «mejor del mercado» sin una comparación operativa real.
```

## P01 · Dirección visual, componentes y estructura

```text
Implementa P01 del plan docs/ux/2026-10-17/. Es parte del rediseño ya autorizado
por el dueño después de «inicia». Revisa rama/status y conserva trabajo ajeno.
Lee README.md, 03-experiencia.md y 07-ejecucion.md de esa carpeta, además de
docs/design/CONSTITUCION.md y las primitivas reales de frontend/src/ui/.

Construye una sola dirección clara/neutra con jerarquía cuidada, producto
protagonista, texto legible y acento contenido. Usa apple-design y emil-design-eng
como criterio. Las láminas 09-direccion-visual.html son referencia documental,
no código listo para copiar ni una especificación industrial.

Reconcilia la constitución con la intención del 17-10: sustituye dos temas,
oscuro por taller y restricciones cosméticas que impidan la nueva dirección;
conserva principios de dominio, accesibilidad, autoridad e inmutabilidad. Marca
lo anterior como histórico donde corresponda. Adapta tokens/primitivas compartidas,
no añadas un tercer sistema de estilos. Retira el selector de temas y resuelve
preferencias antiguas sin mezclar superficies. Mantén formatos Decimal canónicos.

Rediseña shell, cabeceras, navegación por trabajo/rol, estados y capas flotantes.
Agrupa IA/trabajos en presencia contextual y bandeja. Hoy debe agrupar causas
comunes de una obra/lote, en lugar de repetir decenas de tareas equivalentes.
No confundas simplificar menú con conceder permisos de backend.

Afina la base en una obra, un editor y una tabla reales para evitar diseñar un
manual desconectado. Construye vacíos, carga, error, foco y acceso por teclado.
No ejecutes suites ni gates intermedios: mira el producto para diseñar; la
campaña formal se concentra en P12. Guarda solo decisiones y pendientes útiles.
```

## P02 · Obra, defaults y biblioteca de ventanas

```text
Implementa P02 del plan docs/ux/2026-10-17/ después de la base P01. Lee
01-auditoria.md (A02–A06), 03-experiencia.md y 07-ejecucion.md. Inspecciona
frontend/src/features/projects/, backend/projects/ y sus contratos actuales.

Haz que una obra comience con un borrador y una ventana, sin cliente completo
ni preparación administrativa. El nombre puede tener un valor inicial editable;
no inventes clientes o RUT para satisfacer un schema. Si hace falta, agrega el
estado/contrato de borrador sin cliente con migración y API correctas.

Al entrar a una obra, ventanas primero: cabecera breve, siguiente acción,
miniaturas o tabla útil, búsqueda/recinto y selección múltiple. Abre el editor
con una acción evidente. Conserva filtro, selección y posición al volver.
Fases, historial, cobros y adjuntos no deben desplazar el objeto de trabajo.

Define defaults de sistema, vidrio, acabado y condiciones por obra. Hereda en
nuevas ventanas y al duplicar; conserva opciones compatibles al cambiar sistema.
Permite cambiar solo el default o aplicarlo a existentes compatibles con alcance
y diferencias. Identifica excepciones sin obligar a reconfigurar cada posición.
Defaults técnicos proceden de fuente/regla; no rellenes datos industriales ausentes.

Biblioteca visual con familias/aperturas reconocibles, favoritos/recientes útiles
y compatibilidad del sistema. Añadir debe llevar al dibujo, no a un formulario
que replique el inspector. Incluye obra pequeña y grande sin sacrificar lectura.
Regenera contratos si cambian. La verificación formal y bugs generales van al
final P12; usa inspección de diseño durante construcción sin gates repetidos.
```

## P03 · Editor directo y propiedades progresivas

```text
Implementa P03 del plan docs/ux/2026-10-17/. Lee 03-experiencia.md y los hallazgos
A07–A08, A19. Parte de AssemblyEditor, ProductFrontSvg, inspectores y operaciones
reales del dominio; no reconstruyas un editor paralelo sin identidad/historial.

El recorrido habitual es diseño → medidas → apertura → vidrio → acabado → precio.
Cota editable local, selección clara de ventana/módulo/paño/miembro, herramientas
contextuales, preview de dividir/acoplar y selección por teclado. Enter confirma,
Escape cancela; una entrada inválida no modifica silenciosamente el producto.

Aperturas como opciones visuales compatibles, con bisagra/manilla/vista. El
inspector principal contiene decisiones; derivados, kit, autoridad y overrides
van a detalle técnico accesible. No pedir refuerzo/junquillo/descuentos si los
puede resolver el motor con catálogo. Mantén lo desconocido con causa y acción.

Un panel secundario a la vez; lienzo legible en portátil; lista de ventanas
plegable; selección múltiple para vidrio/acabado/cantidad. Deshacer/rehacer,
guardado automático y recuperación coherentes. No muevas el encuadre en cada
respuesta ni presentes un resultado viejo como si fuese del borrador actual.

Usa operaciones compartidas y el resultado del motor para geometría/precio.
No alteres fórmulas para hacer caber el dibujo. El editor debe poder usarse
sin IA. Inspecciona el resultado para diseñar y conserva casos representativos;
deja suites/regresión/campaña de bugs para P12.
```

## P04 · 2D/3D, uniones, acabados y escena común

```text
Implementa P04 del plan docs/ux/2026-10-17/. Lee 04-representacion.md y revisa
Product3DScene.ts, scene3dGeometry.ts, finishMaterials3d.ts, ProductFrontSvg.tsx,
capturas y catálogo actual. Hay lógica y activos parciales aprovechables.

Corrige encuentros físicos: inglete cuando corresponda, testa, T, inversor,
carril, umbral y acople según datos reales. Elimina la omisión visual deliberada
de ingletes del renderer 3D. No dibujes diagonales de 45 grados en todos los
sistemas ni conviertas una aproximación en autoridad de fabricación.

Mejora secciones, profundidad, bordes, juntas, vidrio y poses de apertura.
Interior/exterior, bisagras, manilla, carriles y hojas deben coincidir con el
modelo. Usa una escena/elevación común en editor, miniaturas, PDF y portal.
Los números siguen viniendo del motor Decimal; no derives cotas de la malla.

Prepara materiales con activos de fuente/derechos conocidos, escala de textura
en modelo y veta por eje de perfil. Dos caras y cantos correctos, espacio de
color, rugosidad y luz neutra. Resolver carga/fallo de textura y captura final;
no guardar marrón plano como supuesto Nogal terminado. Si falta una fuente,
deja el alcance explícito y completa los casos con datos disponibles.

Encuadra para entender el producto. Muestrario visual con nombre/referencia,
dos caras y preview. Mantén un modo técnico legible y uno comercial cuidado,
sin duplicar verdad. Mira varias familias durante diseño; suites y aceptación
visual formal, rendimiento y bugs generales se concentran al final P12.
```

## P05 · Asistente que trabaja con poco trámite

```text
Implementa P05 del plan docs/ux/2026-10-17/. Lee 05-ia-catalogos.md, inspecciona
frontend/src/features/assistant/, jobs, backend/ai_gateway/ y el registro de
operaciones. El caso observado de ancho fue correcto pero demasiado ceremonioso.

Sustituye modos Preguntar/Agente por una entrada contextual. Adjunta selección,
obra, revisión, sistema, defaults y permisos; no pidas de nuevo lo conocido.
Preguntas solo ante ambigüedad que cambie el resultado; agrupa dudas y muestra
el alcance de la acción. No simules que se aplicó algo no soportado.

Una petición explícita, acotada y reversible sobre borrador se puede aplicar
con resultado breve y Deshacer. Implementa esta política y su autorización en
backend, no solo quitando una aprobación en frontend. Los lotes/cambios de gran
alcance muestran preview de diferencias, incompatibilidades y precio del motor.
Preparar envío/emisión/compra/liberación deja la consecuencia al clic humano.

La IA usa operaciones tipadas y números del motor; no fabrica cálculos, precios,
compatibilidades o fuentes. Una advertencia aparece por su impacto sobre el
pedido, no como un volcado de todos los pendientes técnicos de la obra.
Deshacer respeta concurrencia, revisión e historial; no promete revertir algo
ya emitido/enviado.

Trabajos grandes en bandeja recuperable con resultado, cancelar/reanudar y
errores comprensibles; herramientas/auditoría bajo demanda. Conserva idempotencia
y no duplica cargos en reintentos. No hagas campañas de evaluación ni suites
durante cada ajuste: prepara escenarios y ejecútalos en P12 con proveedor real
configurado, resultados y límites medidos.
```

## P06 · Ingesta real de PDF de catálogo

```text
Implementa P06 del plan docs/ux/2026-10-17/. Lee 05-ia-catalogos.md y revisa
backend/ingest/catalog_service.py, catalog_ai.py, extract.py, catalog_review.py,
backend/catalogs/ y jobs. Sigue la cadena completa: source_lines más referencia
de fuente → ai_gateway/service → providers → multimodal.pdf_page_parts. Ya hay
transporte de imágenes y páginas sin texto. No lo reconstruyas ni lo confundas
con el nombre de capacidad vision_ocr de importación de posiciones.

Objetivo: el usuario sube su PDF y el sistema prepara entidades, relaciones,
fuentes y pendientes. No le pidas convertirlo a una plantilla o dividirlo por
un límite del prompt. Soporta texto, escaneo y documento mixto por etapas.

Crea un modelo intermedio de documento con páginas, layout, tablas, imágenes,
regiones y procedencia. Usa texto nativo primero, OCR/visión donde haga falta
y gráficos vectoriales cuando aporten. Corrige el límite de 20 páginas mediante
partición interna y no pierdas el gráfico de una página que también tiene texto.
Mejora evidencia regional/literal para datos leídos por visión sin autocertificarlos.
Evalúa herramientas como Docling o
PyMuPDF por ajuste, despliegue y licencia; no adoptes todo sin necesidad.

Reconoce sistema/perfil/sección/vidrio/acabado/herraje/corte/refuerzo y relaciones
con evidencia. Conserva bruto/normalizado, Decimal/unidad, página/región/cita y
transformaciones. No deduzcas cotas exactas de un croquis sin escala ni inventes
reglas ausentes. Confianza de extracción no equivale a aptitud industrial.

Partición interna y trabajo recuperable por página/sistema, deduplicación,
reanudación de etapas fallidas, presupuesto y cargos idempotentes. Tablas
multipágina y referencias cruzadas no se pierden en el chunking. No truncar
silenciosamente por 2 000 candidatos. Conservar archivo privado por org/RLS.

Entrega un mapa estructurado y cobertura de capacidades para P07. Reutiliza
schema/publicación existentes donde sirven y regenera API si cambia. Conserva
un corpus autorizado para la campaña final; no ejecutes benchmarks y gates
por cada iteración. La evaluación integral de extracción/relaciones va en P12.
```

## P07 · Importador visual, revisión y mantenimiento de catálogo

```text
Implementa P07 del plan docs/ux/2026-10-17/ sobre la ingesta P06. Lee
05-ia-catalogos.md, 03-experiencia.md y CatalogImportsPanel/catalogs actuales.

Una zona principal: subir PDF del proveedor. Detectar fabricante/sistemas;
archivos complementarios en la misma importación. Plantilla/CSV como opciones
secundarias para especialista. Elimina input nativo y botón redundantes.
Trabajo en segundo plano con progreso real, resumen y continuación.

El resultado es una biblioteca visual de sistemas/componentes y relaciones,
no una planilla de cientos de campos. Muestra capacidades preparadas y dudas
por consecuencia. Revisión lado a lado con página/región resaltada, valor
propuesto, evidencia y acción corta. Agrupa conflictos comunes y permite
resolverlos coherentemente sin revisar cada campo que coincide con fuente.

Activación por alcance respaldado: diseñar/cotizar/fabricar/CNC diferentes.
Conservar revisión y clic de publicación; la IA no se autocertifica. Si falta
una regla en el PDF, explicar qué fuente falta sin trasladar toda la extracción
al usuario. Un catálogo DEMO sigue siendo DEMO.

Versión vigente clara; historial secundario; importar nueva edición compara
cambios y fuentes. Borradores pueden proponer actualización; documentos/órdenes
emitidos conservan su versión. Miniaturas/secciones/acabados comparten los activos
y alcance del renderer, sin inventar geometría de autoridad desde imágenes.
Costos siguen privados según permiso. Inspección visual para construir; suites
y campaña formal con catálogos reales al final P12.
```

## P08 · Precio, propuesta, PDF y portal

```text
Implementa P08 del plan docs/ux/2026-10-17/. Lee 06-documentos-operacion.md,
03-experiencia.md y módulos pricing/documents/portal/quotations actuales.

Precio visible en diseño y obra con explicación útil. Costo, precio, descuento,
margen e impuesto distintos; costos solo con permiso. Comparar alternativas y
revisiones con miniaturas y diferencias humanas; números solo del motor/política.

Preparar propuesta completa cliente y condiciones que falten, usa defaults y
abre visor. Rediseña el PDF: cabecera breve, producto legible, resumen, posiciones,
cantidades/importes y condiciones. No malgastes portada ni reduzcas los dibujos
a un adorno. Paginación por contenido, tablas continuadas y anexos pertinentes.
No persigas un número mínimo universal de páginas.

Emitir y enviar son acciones diferentes; revisión exacta, recibo claro y PDF
inmutable. Abrir debe permitir ver, además de descargar/imprimir. Imágenes del
producto derivadas de la misma escena y autoridad que editor/portal.

Portal móvil con ventana, acabado, características, precio, condiciones y
siguiente acción comprensibles. Aceptación/pago corresponden a revisión y
servicios reales; sandbox/simulación se declaran. No lleves BOM, jobs o estados
internos al cliente.

Renderiza documentos para componerlos durante diseño, sin una campaña de tests
por cada ajuste. La revisión formal de PDF, impresión, portal, inmutabilidad y
checks transversales se hace al final P12.
```

## P09 · Materiales, documentos de taller y operación

```text
Implementa P09 del plan docs/ux/2026-10-17/. Lee 06-documentos-operacion.md y
revisa production, documents, purchasing, inventory y capacidades CNC actuales.

Materiales en espacio amplio: dibujo↔pieza/vidrio/herraje con selección cruzada,
nombre/función, código, variante/unidad y alcance por unidad/posición/lote.
No sumes filas solo por nombre ni confundas medida de corte con unidad de compra.

Conserva el documento de corte útil; mejora identidad/destino/variante. Rediseña
pack por estación. Corrige _unit_map_svg: códigos cortados/solapados requieren
callouts cortos, espacio de anotación y leyenda, no fuente minúscula. Vidrio y
etiquetas con cantidad/alcance claros, miniatura de destino y formato físico.

Planta por obra/lote y tarea. Encargado ve carga y bloqueos; operario ve producto
e instrucciones de su estación. Calidad abre chequeos, no una tabla de corte.
Remake/defecto conserva vínculo a pieza y orden. CNC permanece área especialista
con capacidad real, preview y autoridad; no prometas máquina por tener pantalla.

Compras comienza por faltantes positivos; cubierto por stock se resume. Asignar
proveedor/precio por grupo; revisión de cantidades/unidad/destinatario antes de
enviar. Recepción parcial/daño y ubicación sin recapturar todas las líneas.
Inventario muestra las variantes que hoy parecen duplicadas; no deduplicar BD
por apariencia. Retazos con largo útil, acabado, ubicación e identidad escaneable.

Una sola experiencia visual/terminológica, sin nuevos formularios de backend.
No ejecutar suites o gates a cada ajuste. La campaña general de taller, papel,
lector, RLS y bugs se concentra al final P12, con recursos reales apropiados.
```

## P10 · Clientes, cobros, terreno, despacho, analítica y ajustes

```text
Implementa P10 del plan docs/ux/2026-10-17/. Lee 06-documentos-operacion.md y
03-experiencia.md. Usa docs/wiki/index.md para inspeccionar cada dominio actual;
el reporte del 12-10 es inventario histórico, no prueba de estado presente.

Extiende la calidad al resto del sistema. Clientes: búsqueda/creación breve,
obras, propuestas, pendientes y contacto; fiscal/fusión avanzados en contexto.
Cobros: qué vence, qué está verificado y qué hacer; documentos y pagos externos
claramente distinguidos de simulación. Preparar mensajes no envía automáticamente.

Despacho: unidades/embalaje y salida; recepción con identidad física. Terreno:
agenda por rol, medición sobre vano/ventana, fotos/notas y sincronización clara.
No expongas cola técnica como tarea principal ni el mensaje del instalador al
encargado. Postventa por cliente/obra/etiqueta y revisión instalada.

Analítica responde preguntas de margen, materiales, atascos y cobros, con acciones
y definición de fuente. Evita KPI decorativos. Ajustes agrupados por tarea:
empresa, equipo, catálogo/precios, conexiones y administración; no exigir la
configuración de toda la plataforma para empezar a diseñar.

Aplicar la dirección única también a vacíos, errores, permisos, correos/recibos y
buscador. Móvil es una experiencia de tarea, no todo el editor encogido. Usa la
skill mobile-native si corresponde. No añadas preferencias para cada diferencia
de criterio. Preserva autoridad, RLS y clic humano en consecuencias externas.
Construye e inspecciona; pruebas y bugs generales al final P12.
```

## P11 · Integración y detalle fino de toda la experiencia

```text
Integra y pule P11 del plan docs/ux/2026-10-17/ después de construir P01–P10.
Lee 01-auditoria.md, 03-experiencia.md y 07-ejecucion.md. Completa pendientes de
construcción antes de iniciar la campaña final de pruebas.

Recorre el diseño como diseñador: obra nueva, varias ventanas, cambio manual/IA,
catálogo, propuesta, materiales y taller. Resuelve jerarquía, proporciones,
coherencia de nombres, acciones principales y transiciones a pantallas viejas.
Quita redundancia y detalles internos que no ayuden a decidir. No crees nuevos
paneles para esconder otros paneles mal organizados.

Todos los estados merecen diseño: primer uso, vacío por rol, carga, error,
sin dato, conflicto, guardado pendiente, desconexión y recuperación. Texto en
español de oficio; códigos largos y trazas bajo demanda. Acceso por teclado,
foco, tamaño táctil, legibilidad y movimiento reducido coherentes.

Pulir apertura, selección, paneles y vistas con movimiento breve e interrumpible
solo cuando ayude. Usa animate/animation-performance si la tarea lo requiere.
No gamificación ni animaciones que ralenticen operaciones frecuentes.

Revisa consistencia del mismo producto en editor/miniatura/PDF/portal/materiales.
Retira código/CSS viejo que haya quedado sin uso, conservando datos, historia,
contratos y fixtures necesarios. Documenta decisiones duraderas en wiki, con
fuentes/ref; no declares aún pruebas finales ejecutadas.

Entrega una tabla Before | After | Why de los cambios principales y una lista
corta de escenarios para P12. No lances suites completas en bucle durante el
acabado: la campaña de aceptación y bugs comienza en P12.
```

## P12 · Pruebas finales, corrección de bugs y entrega

```text
Ejecuta P12 del plan docs/ux/2026-10-17/: la construcción e integración están
terminadas y ahora corresponde la campaña final solicitada por el dueño.
Lee 07-ejecucion.md y usa testing-framedex para revisar el stack/roles sin
reconstruir o resetear estado ajeno. No conviertas este cierre en otra fase
indefinida de rediseño.

Verifica tareas completas con datos realistas: empresa nueva; obra simple y
grande; familias/aperturas; acabados; edición/lotes/undo; IA breve/ambigua/larga;
PDF de catálogo nativo/escaneado/mixto y conflictos; propuesta/revisión/portal;
BOM, corte, montaje, etiquetas, calidad/remake; compras/stock/retazos; terreno.
Usa fuentes autorizadas y proveedor IA real configurado; separa simulación de
capacidad real. Dispositivos reales donde importen teclado, tacto, red y QR.

Revisa PDF renderizado, impresión B/N y formato de etiqueta. Sin códigos cortados,
solapados ni cantidades de alcance confuso. Contrasta números con el motor y
fuentes, no con lo que diga el modelo. Confirma permisos/costos privados, RLS,
concurrencia, inmutabilidad e idempotencia de consecuencias.

Mide tiempo/ayudas/esfuerzo de tareas e IA, tiempo humano de catálogo y defectos
visuales. No conviertas las metas del plan en resultados inventados ni uses
aceptación histórica como corrida nueva. Si es posible, observa profesionales
sin explicarles la interfaz; registra dónde se pierden y corrige el producto.

Ejecuta lint, typecheck, tests, build y gate DB del repo en el entorno apropiado,
porque el cambio es transversal. Fórmulas tocadas requieren golden-case y drill
pertinente; no regenerar goldens para ocultar diferencias. Corrige bugs y repite
solo checks/recorridos afectados por cada arreglo. No debilites CI ni guardas.

Cierra con PR y un recibo breve: ref, cambios, evidencia seleccionada, resultados
de tareas/checks y límites. No enviar correos, comprar, pagar, emitir fiscal o
liberar producción real por la sola autorización de probar el software.
Si falta un recurso externo imprescindible, completa el resto y declara ese
límite concreto sin presentar un stub como integración probada.
```

## Para continuar en otra sesión

Usar el prompt del paquete pendiente y adjuntar el estado real de la rama/PR.
No copiar todos los prompts al contexto de cada sesión. Una nota mantenida con
paquete actual, decisiones y pendientes basta; este estudio es referencia, no
una orden de redescubrir toda la competencia antes de cada cambio.
