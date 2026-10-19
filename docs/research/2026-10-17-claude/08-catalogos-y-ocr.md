# Catálogos desde PDF: extracción, integración y revisión

## Promesa útil

El usuario sube un PDF y DEKOPEN se encarga del procesamiento, organiza la línea y devuelve lo que ya se puede utilizar junto con las excepciones que requieren una decisión. El usuario no debe dividir el documento, rellenar una hoja de cálculo de cien campos ni entender un esquema interno antes de empezar.

Un catálogo comercial puede describir productos sin incluir todas las reglas necesarias para fabricar. La promesa correcta es automatizar la extracción y la integración disponible, con preparación por capacidad; no afirmar que cualquier PDF contiene todo lo que una máquina necesita.

## Base actual que se aprovecha

- Importación estructurada e IA con revisión/publicación ya existentes.
- Límite de archivo de 15 MB en el servicio revisado y candidatos estructurados acotados.
- Comprobación de valores literales de alta confianza contra texto de fuente.
- Soporte de PDF/imagen en el gateway.
- Helper multimodal con máximo de 20 páginas, 100.000 caracteres y límites de imagen; página con texto se envía como texto sin imagen.
- Compilador de catálogo con límite de texto que pide dividir el documento manualmente.

El diseño debe sustituir la limitación de experiencia y ampliar la estrategia de procesamiento; subir indiscriminadamente todos los límites no resuelve memoria, costo, recuperación ni calidad de asociación entre números y piezas.

## Recorrido visible

1. **Subir catálogo.** Una entrada admite arrastrar PDF o seleccionarlo. Detectar fabricante/serie/tipo como propuesta; preguntar solo si hay una ambigüedad que cambia el destino.
2. **Analizando.** Mostrar archivo, páginas/etapas realmente procesadas y posibilidad de dejar trabajar. No bloquear el resto de la aplicación.
3. **Resultado.** Enseñar sistemas/familias encontradas, ilustraciones o recortes, cobertura y usos preparados.
4. **Revisar excepciones.** Dudas, conflictos y datos críticos faltantes junto a su región de fuente. Lo consistente no exige una aprobación por celda.
5. **Usar/publicar.** Muestra de cambios y autorización del rol adecuado; estado de capacidad claro. Mantener la versión y el archivo original.

«Importar hoja de cálculo» y edición manual siguen disponibles como herramientas secundarias, no como puerta principal. Un estimador sin permiso de publicación puede preparar o solicitar revisión según su rol; una denegación no debe parecer un fallo del OCR.

## Pipeline interno recomendado

| Etapa | Trabajo | Persistencia y recuperación |
|---|---|---|
| Recepción | Validar archivo, formato, límites y permiso; hash del original | Fuente privada por empresa, estado y páginas |
| Preanálisis | Distinguir texto digital, escaneo, tablas, dibujos y mezcla | Inventario por página y región |
| Extracción | Texto con coordenadas, OCR donde falta o es pobre, tablas y figuras | Resultado por página, método y versión |
| Partición | Agrupar por sistema/familia/sección, conservando contexto y referencias cruzadas | Unidades de trabajo idempotentes |
| Interpretación | Identificar entidades, valores, unidades y relaciones | Propuestas tipadas con procedencia |
| Resolución global | Unir tablas continuadas, leyendas, códigos y variantes | Grafo de relaciones y conflictos |
| Validación | Reglas deterministas de formato, consistencia y compatibilidad declarada | Incidencias por entidad/capacidad |
| Ilustración | Recortar imagen o asignar familia reconocible | Activo vinculado a fuente y naturaleza de representación |
| Revisión | Agrupar excepciones según efecto | Decisiones y evidencia de cada cambio |
| Publicación | Versionar línea y su preparación por uso | Snapshot, auditoría y posibilidad de restaurar versión |

Usar lotes internos y reintentos de la página/región fallida, no volver a cobrar/procesar todo por un error al final. Conservar referencias de página a través de la partición. No truncar filas silenciosamente al alcanzar un límite de candidatos.

Una página puede tener texto digital y un dibujo escaneado importante. La presencia de texto no debe impedir analizar la figura. Decidir si se usa visión por estructura y calidad de la región, no por `literal != vacío`. La extracción visual puede proponer dimensiones; la validación debe comprobar la relación entre cota, pieza y unidad.

## Modelo de entidades y relaciones

| Entidad | Información clave | Relaciones que deben conservarse |
|---|---|---|
| Fabricante / sistema / serie | Nombre, edición, material, alcance | Pertenencia y vigencia |
| Perfil | Código original, familia, nombre, sección/medidas declaradas | Marco/hoja/montante/refuerzo y variantes |
| Vidrio / relleno | Espesores, composiciones y límites declarados | Compatibilidad con hojas/junquillos |
| Junquillo / junta | Familia, rango y código | Conjunto compatible, no solo una fila aislada |
| Herraje / kit | Identidad, variante y restricciones | Apertura, peso/tamaño admitidos cuando están documentados |
| Acabado | Código, aspecto, caras aplicables | Variantes y precios si existen |
| Regla | Descuento, holgura, unión, límite o mecanizado | Fuente, condiciones y versión |
| Compra | Unidad, presentación, longitud/pieza comercial | Perfil/material, proveedor y fecha de costo |
| Sección / foto | Activo, región original, tipo de representación | Pieza, fuente y autoridad técnica |

No todos los catálogos contienen todas estas entidades. No generar campos vacíos irrelevantes para cada fila. Distinguir código de fabricante, SKU de compra y nombre comercial; no fundirlos por similitud textual.

## Procedencia por dato

Registrar archivo, página, región, texto literal o recorte, método, valor normalizado, unidad, relación con entidad, estado de revisión y versión. Para un número reconocido, verificar que pertenece a la pieza y al concepto correctos; citar una página que contiene el mismo número no basta.

Separar **extraído**, **normalizado**, **interpretado**, **confirmado** y **aprobado para un uso**. La confianza del modelo es una señal de priorización, no la autoridad final. Un valor literal bien leído tampoco prueba que la regla sea aplicable a toda la serie.

Conservar coma/punto decimal y unidades de origen. La normalización se realiza con Decimal y reglas deterministas. No convertir una imagen a escala en una dimensión certificada si no hay referencia suficiente. Si dos tablas discrepan, conservar ambas fuentes y abrir un conflicto.

## Preparación por capacidad

| Nivel visible | Qué puede hacer | Qué no debe insinuar |
|---|---|---|
| Biblioteca preparada | Buscar, reconocer y seleccionar referencias | Que ya calcula correctamente |
| Diseño preparado | Configurar tipologías dentro de reglas disponibles | Que tiene precios o datos completos de taller |
| Cálculo/materiales preparado | Derivar componentes/cantidades con reglas autorizadas | Que existe costo vigente si falta |
| Cotización preparada | Calcular una oferta con costos/reglas comerciales disponibles | Que todos los procesos de fabricación están homologados |
| Fabricación preparada | Corte y operaciones autorizadas para el alcance | Que sirve para cualquier máquina |
| CNC preparado para… | Adaptador, herramienta y configuración de una máquina validados | Compatibilidad universal |

En UI habitual, mostrar un resumen como «Lista para diseñar y cotizar; falta validar corte» con acceso al detalle. No exponer seis insignias por cada perfil. El backend conserva la precisión de estados aunque la presentación sea sencilla.

## Revisión por excepciones

Agrupar por causa: códigos duplicados, pieza sin familia inequívoca, dimensión dudosa, regla incompleta, relación incompatible y contradicción entre ediciones. Cada excepción muestra efecto práctico: «Impide el corte de esta hoja», no «field unknown».

Permitir resolver una causa común para varias filas cuando la evidencia lo permite. Mostrar el recorte de PDF y los datos relacionados al lado. Acciones: aceptar interpretación, corregir, conservar como referencia, descartar duplicado, vincular entidad y solicitar información adicional. No exigir que el dueño apruebe campos sin efecto en el uso solicitado.

La publicación de autoridad técnica mantiene revisión del rol autorizado. Reducir trabajo manual exige mejores verificaciones automáticas y mejores fuentes; no eliminar la revisión de una regla crítica sin evidencia.

## Añadir un segundo catálogo

Destino explícito: crear línea o ampliar una existente. Detectar edición, fabricante y solapamientos como propuesta. Comparar por identidad fiable y relaciones; un nombre parecido no autoriza fusionar dos perfiles.

Presentar añadidos, complementos, conflictos, datos reemplazados y cambios que afectan proyectos. Política inicial: completar ausentes, conservar aprobados y revisar contradicciones. No sustituir automáticamente por «el último PDF» ni cambiar silenciosamente revisiones emitidas.

Los proyectos existentes mantienen sus versiones; el negocio decide actualizar un borrador y ve el efecto en cálculo/precio. Una reversión de catálogo restaura una versión publicada conservando eventos, no borra el historial de la fuente.

## Reglas de fabricación

La IA puede traducir una regla documental a una propuesta declarativa admitida por el motor. Nunca ejecutar código arbitrario obtenido del PDF. Cada fórmula nueva necesita semántica, alcance y fuente comprensibles, y los casos dorados exigidos por el repositorio se incorporan en la campaña final antes de entregar.

Si el documento no contiene descuentos, uniones o límites necesarios, preparar el resto y mostrar exactamente qué hace falta para fabricar. No completar con un supuesto «estándar del sector» sin autoridad. No confundir una norma comercial o una imagen de perfil con un catálogo técnico de mecanizado.

## Evaluación de herramientas

Comparar extracción local actual, motor de layout/OCR especializado y visión de modelo con los mismos documentos. Azure y Google documentan tablas, regiones y estructura; son candidatos a una capa de extracción, no motores de ingeniería. Mantener adaptadores para no acoplar el catálogo a un proveedor.

Medir reconocimiento por campo, asociación a la entidad, relaciones, cobertura de páginas, corrección manual, tiempo y costo por importación completa. Reservar el modelo más capaz para regiones ambiguas y resolución global; tareas de partición/normalización no requieren razonamiento libre. La calidad y privacidad mandan sobre una optimización de costo no medida.

## Proline y Aluminios 2000

El dueño anunció estos PDF, pero no están adjuntos a este encargo. Se localizó la [página de catálogos de Aluminios 2000](https://aluminios2000.com/catalogos/), que lista perfiles PVC y otras familias. Esto no identifica la edición exacta del dueño ni autoriza afirmar que se importó una línea Proline completa.

Cuando estén disponibles: registrar nombre/hash/edición, páginas y origen; escoger muestras con tablas, secciones, variantes y reglas; elaborar una referencia técnica revisable; importar sin dividir manualmente; comprobar entidades/relaciones y un caso de cálculo/cotización/corte cuando el PDF tenga datos suficientes. Si falta autoridad de fabricación, conservar ese resultado como límite del catálogo.

No almacenar PDF de terceros en Git sin permiso de redistribución. Guardar evidencia mínima, referencias y resultados revisables conforme al almacenamiento privado del negocio.

## Aceptación final del importador

Incluir PDF digital, escaneado, mixto, largo, tabla continuada, mala rotación, duplicado, edición contradictoria y ampliación parcial. Debe poder detener/reanudar sin duplicar, conservar página fuente y permitir usar capacidades listas antes de completar las demás. El informe distingue cobertura real de éxito visual de la barra de progreso.
