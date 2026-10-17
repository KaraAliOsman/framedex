# IA útil y catálogo a partir de un PDF

[Volver al plan](README.md)

## La IA tiene que reducir trabajo

La persona expresa un objetivo en el contexto en el que está. La aplicación ya
sabe qué obra, selección, sistema, revisión, defaults y permisos se están usando.
La IA debe aprovecharlo y entregar un resultado editable, no otra entrevista.

### Caso observado

Petición: «Cambia el ancho a 1200 mm y deja todo lo demás igual».
La propuesta real cambió 1 000 → 1 200 mm, mantuvo alto 1 400 mm y comunicó
precio de motor $498.769 → $540.910, diferencia $42.141 en ese caso de fixture.
No hizo preguntas. La fricción vino del modo, el recorrido de job/propuesta,
la aprobación y una advertencia térmica extensa. Se descartó la propuesta;
no se aplicó el cambio ni se alteró la ventana original.

Esto no demuestra el rendimiento general de la IA. Demuestra que incluso un
resultado correcto puede sentirse más pesado que una edición manual.

## Política de interacción por consecuencia

| Pedido | Respuesta objetivo | Confirmación |
|---|---|---|
| Cambiar ancho de la ventana seleccionada | Ejecutar operación válida; mostrar cambio y precio/estado útil; Deshacer | La petición explícita autoriza el cambio reversible del borrador. |
| Duplicar y cambiar cantidad/recinto | Resultado inmediato con selección del nuevo producto | Deshacer. |
| Cambiar todas a Nogal | Resolver alcance; vista previa breve de cantidad, compatibilidad y delta | Aplicar lote desde resumen cuando el impacto lo merece. |
| «Hazlo más barato» | Comparar alternativas elegibles del catálogo con precio del motor | Elegir propuesta; no reemplazar calidad/seguridad en silencio. |
| Generar propuesta comercial | Preparar borrador y vista previa | Emitir/envíar mediante acciones humanas separadas. |
| Comprar, pagar, enviar correo, emitir fiscal o liberar producción | Preparar todo y dejar el resultado revisable | Clic humano final según consecuencia. |
| Extraer PDF de catálogo | Ejecutar análisis y preparar candidatos automáticamente | Revisión y activación de alcance; no autocertificar fabricación. |

La implementación de aplicar directamente necesita política y permisos en backend;
no basta esconder el botón de aprobación. Deshacer debe crear una operación
auditada coherente con el estado actual. No prometer deshacer una compra ya enviada
o reescribir una revisión emitida.

## Contexto, preguntas y respuesta

- Adjuntar selección, producto, revisión actual, unidades, sistema, defaults y
  permisos a las herramientas; no enviar indiscriminadamente toda la base.
- Referirse a «esta ventana», «las seleccionadas» o «toda la obra» con alcance
  visible. Si no hay selección y hay varias candidatas, mostrar un selector breve.
- Preguntar solo si la respuesta cambia materialmente el resultado y no existe
  una elección respaldada por el contexto. Agrupar dudas relacionadas.
- Ante «hazla de 1200» en una selección con ancho/alto ambiguos, usar el contexto
  de edición si es inequívoco; en otro caso preguntar qué dimensión. No adivinar
  un dato físico crítico por ahorrar una pregunta.
- No preguntar marca, serie o color si ya están definidos y el pedido los preserva.
- Sustituir modos técnicos por una entrada: «Pedir un cambio…». El router decide
  consultar, editar, comparar o preparar trabajo largo.
- Resumir en una frase y un resultado; detalle/herramientas/costo del job bajo demanda.
- Si una capacidad no existe, ofrecer el camino disponible sin fingir ejecución.

### Ejemplos de respuestas objetivo

| Solicitud | Respuesta de producto |
|---|---|
| «Ancho 1200, el resto igual» | «Ancho actualizado a 1 200 mm. Se mantienen apertura, alto y materiales. [Deshacer]». Precio actualizado por el motor. |
| «Usa el mismo vidrio en estas cuatro» | «4 ventanas usan ahora el vidrio de P01. [Deshacer]», si todas son compatibles. |
| «Todas en nogal por fuera» | «12 ventanas · exterior Nogal · interior sin cambios. 2 necesitan otra variante compatible. [Ver cambios]». Cantidades reales del trabajo. |
| «No entiendo este total» | Resumen de materiales, trabajo, margen/impuesto autorizados, con fuente y sin inventar una explicación numérica. |

Los ejemplos con cantidades ilustran la forma de respuesta; no son resultados
medidos ni plantillas que deban fijar números en el producto.

## Trabajos largos

La bandeja muestra un resultado con fases comprensibles: Leyendo documento,
Organizando sistemas, Relacionando componentes, Preparando biblioteca y Dudas
para revisar. El usuario puede salir y volver sin reiniciar. Progreso real por
páginas/etapas, sin porcentajes inventados. Reintentos reusan lo terminado y no
duplican cargos ni publicaciones. Una falla conserva el archivo y el trabajo.

## Catálogo actual: qué existe y qué falta

Existe subida de PDF/imagen/planilla/texto, candidatos tipados, evidencia,
revisión, publicación y restricciones de autoridad. La UI tiene una entrada de
archivo de 15 MB y un camino de plantilla amplio.

En el ref auditado, `backend/ingest/catalog_service.py:238` llama a
`extract_tagged`, `parse_structured` y `compile_catalog`. `catalog_ai.py:75`
construye `source_lines` de texto/ref y limita el texto a 100 000 caracteres.
La extracción PDF recoge texto por página sin conservar layout/coordenadas de
región en ese contrato.

**Sí existe transporte multimodal compartido.** `ai_gateway/service.py` resuelve
la fuente del catálogo por organización y la pasa a `providers.py:336`. Este
transporta imágenes y usa `multimodal.pdf_page_parts` para los PDF: envía texto
si una página tiene texto y rasteriza la página si no lo tiene. El helper limita
el documento a 20 páginas y 100 000 caracteres, además de límites de imagen.
Una página mixta con una pequeña capa de texto puede llegar como texto y perder
el diagrama que se necesitaba interpretar. No hay que construir este transporte
de cero ni afirmar que el producto carece de visión.

Además, `catalog_ai.parse_response` verifica las citas HIGH contra `tagged`, las
líneas extraídas localmente. Un dato leído visualmente de un escaneo puede llegar
como propuesta, pero sin ese literal local no queda verificado de la misma forma.
Esto protege frente a inventos; también traslada revisión a la persona. La mejora
debe aportar OCR/evidencia regional y relaciones, no simplemente confiar en HIGH.

**Importación de posiciones y catálogos son caminos distintos.**
`backend/ingest/service.py` contiene `vision_ocr`, mientras el catálogo invoca
`catalog_import`; ambos pueden aprovechar la pasarela multimodal. Las aceptaciones
históricas de la wiki son compatibles con ese transporte. No demuestran por sí
solas preparación de catálogos reales extensos, layout completo o relaciones
correctas. La cadena completa, no solo el payload inicial, gobierna el diagnóstico.

## Experiencia «solo subo el PDF»

### 1. Entrada

Una zona de arrastre principal: «Sube el catálogo de tu proveedor». PDF como
camino principal, fotos/varios archivos complementarios si sirven. Detectar
fabricante, fecha y sistemas; pedir un nombre solo si no se puede reconocer.
XLSX/CSV quedan en «Otras formas de importar». Un catálogo largo se divide
internamente; no se obliga a cortar el PDF o rellenar diez hojas.

El sistema debe comunicar un costo de análisis cuando sea relevante y ya exista
esa política, sin añadir un formulario de configuración del modelo/proveedor a
la tarea. Archivos relacionados pertenecen a una misma importación, no a una
colección de trabajos inconexos.

### 2. Preparación automática

```text
PDF original privado + hash
        ↓
índice de páginas / sistema / idioma / texto / tablas / imágenes / planos
        ↓
texto nativo + layout + tablas + OCR de páginas necesarias + gráficos vectoriales
        ↓
extracción de entidades y candidatos con página/región/cita
        ↓
normalización de unidades/referencias + relaciones + conflictos
        ↓
mapa del sistema + biblioteca visual + cobertura de capacidades
        ↓
revisión por excepciones → activación de alcance respaldado
```

La IA reconoce y relaciona; el código normaliza, valida esquemas y deriva con
reglas deterministas donde corresponde. Ninguna medida de fabricación surge de
que la imagen «parezca» tener cierto tamaño.

### 3. Resultado que entiende un profesional

Un catálogo preparado muestra sistemas, perfiles con miniaturas/secciones,
aperturas, vidrio, acabados, herrajes y relaciones. Ejemplo de redacción:
«Encontré los sistemas del documento. Estos están preparados para cotizar;
estos necesitan revisar una regla de corte». Los conteos son reales del análisis.

Las dudas se muestran en orden de consecuencia. Se abre la página exacta con la
región resaltada y el campo propuesto: «¿Este descuento corresponde al marco o
a la hoja?». Corregir una unidad o referencia común puede resolver un grupo;
no obliga a revisar cientos de campos que coinciden literalmente con una fuente.

### 4. Activación

La persona ve el alcance y las fuentes que respaldan el catálogo. Cotizar,
fabricar y mecanizar tienen requisitos diferentes. Un catálogo puede servir para
diseño/cotización sin estar preparado para CNC; esa diferencia se explica en
lenguaje útil, sin exponer un formulario de todos los estados internos.

La revisión humana se concentra en excepciones y en aceptar el resumen/alcance;
no desaparece por etiquetar todo HIGH. Una buena lectura de OCR no certifica una
regla industrial. Si el documento no incluye un dato crítico, la IA lo deja
pendiente y propone la fuente o tarea mínima para completarlo.

## Contenido a reconstruir

| Conjunto | Entidades y relaciones que importan |
|---|---|
| Identidad | Fabricante, sistema, versión, material, país/idioma, fuente y vigencia. |
| Perfiles | Código, nombre, función, sección, dimensión declarada, unidad de venta y largo comercial. |
| Construcción | Marco↔hoja, montante/travesaño, inversor, umbral, acoples y juntas. |
| Corte/refuerzo | Fórmula o descuento explícito, condiciones, refuerzo compatible y fijación. |
| Vidrio | Composición/rangos, junquillo, junta, calzo y compatibilidad. |
| Apertura/herraje | Familias, mano, kit, límites, manilla, activos/pasivos y mecanizados declarados. |
| Acabado | Caras admitidas, referencia, variante, recargo y muestra. |
| Comercial | Tarifas, moneda, unidad, vigencia y proveedor; costos con permiso. |
| Evidencia | Documento, página, región, literal, método, transformación y revisión. |

No todos los PDF contienen todo esto. La preparación reporta cobertura y huecos;
no transforma una ficha comercial en un manual de fabricación completo.

## Arquitectura técnica propuesta

| Componente | Responsabilidad |
|---|---|
| Documento original | Storage privado por org, hash, versión, tamaño y acceso autorizado. |
| Modelo intermedio de documento | Páginas, bloques, tablas, imágenes, coordenadas, idioma y procedencia. |
| Extractores | Texto nativo primero; OCR/layout/visión donde se necesite; paths vectoriales cuando existan. |
| Compilador de catálogo | Entidades tipadas, referencias cruzadas y relaciones con evidencia. |
| Normalizador | Decimal/unidades, códigos equivalentes, separadores regionales, duplicados y conflictos. |
| Resolutor | Compatibilidad/relaciones; no inventa reglas ausentes. |
| Preparación/cobertura | Qué permite diseñar, cotizar, fabricar o mecanizar con esa fuente. |
| Revisor visual | Página y candidato lado a lado, excepciones agrupadas, cambio masivo seguro. |
| Publicación | Versión, diff y alcance revisados, concurrencia, inmutabilidad y auditoría. |
| Mantenimiento | Nueva edición de proveedor, cambios, obsolescencia y actualización de borradores elegibles. |

Un candidato necesita valor bruto y normalizado, unidad, fuente/región/cita,
método de extracción, confianza de lectura y estado de revisión. La confianza
numérica del modelo no se usa como probabilidad calibrada sin evaluación.
Separar «lo leí fielmente» de «es válido para fabricar».

Los diagramas vectoriales pueden conservarse como vista del proveedor. Para
convertirlos en sección exacta hacen falta escala/orientación/cotas y verificación.
Un recorte de imagen no se convierte automáticamente en un polígono de autoridad.

## Documentos grandes y recuperación

- Un trabajo por importación con subtrabajos por página/sistema; deduplicar por
  hash de documento/página y versión de extractor.
- Clasificación inicial para no enviar cada página completa a un modelo caro.
- Tablas que continúan entre páginas se recomponen con referencias.
- Evidencia permanece vinculada aunque se corrija un campo o se reintente OCR.
- Guardar cada etapa y sus errores; reanudar solo lo fallido; concurrencia/cancelar
  coherentes con el estado del trabajo y con los cargos.
- Si falla un proveedor, conservar el avance y ofrecer reintento. La plantilla
  no debe aparecer como castigo automático por un fallo temporal.
- Costos y latencia observables internamente; resumen comprensible para el dueño.
- Evitar truncar candidatos silenciosamente por un límite de filas: indicar lo
  procesado y continuar el resto de forma controlada.

## Herramientas candidatas, sin elección prematura

- [DoclingDocument](https://docling-project.github.io/docling/concepts/docling_document/):
  modelo de documento/layout/tablas y procedencia que merece evaluar.
- [PyMuPDF · gráficos](https://pymupdf.readthedocs.io/en/latest/recipes-drawing-and-graphics.html):
  acceso a paths/vector y regiones; revisar licencia y ajuste al despliegue.
- Extracción de texto existente y renderizado de páginas: reutilizarlos donde
  aporten; no reemplazar todo por una sola llamada multimodal.
- Visión del proveedor configurado: examinar páginas/recortes con contexto y
  schema, conservando la evidencia; medir calidad en documentos reales.

La selección final se decide por calidad de extracción, relaciones, evidencia,
tiempo, costo, despliegue y licencia. No se hizo un benchmark de estas librerías
en este encargo ni se instalaron dependencias nuevas.

## Revisión final de IA y catálogo

La campaña final debe incluir PDF con texto, escaneado, mixto, tablas largas,
códigos parecidos, unidades diferentes, sección vectorial, contradicciones entre
ediciones, páginas sin regla de corte y precios privados. Usar documentos reales
con autorización de uso; lo sintético sirve para casos controlados, no como única
demostración de capacidad.

Medir tiempo humano de revisión, preguntas necesarias, campos fieles a fuente,
relaciones correctas, cobertura de capacidades y falsos datos aceptados. Un cero
inventado con HIGH es peor que un pendiente bien explicado. Los resultados deben
separar extracción, corrección humana y aptitud técnica.

También evaluar pedidos breves, lotes, ambigüedad, deshacer, reanudación y estados
obsoletos. El PDF y el chat son datos de entrada: sus instrucciones internas no
otorgan permisos, envíos, acceso entre organizaciones ni autoridad industrial.
