# Recomendación gerencial: seis iniciativas con resultado observable

No son una aprobación de alcance nueva. Cada iniciativa se divide entre lo ya exigido por el [encargo final](../2026-10-18-direccion-final/README.md) y la ampliación que el dueño podría adoptar después de comprobar su valor. Mantener la misma identidad de obra/posición/revisión y las operaciones de dominio; la IA permanece opcional.

## 1. Revisión antes de comprometer una etapa — I01

**Trabajo del usuario.** Saber si puede enviar una cotización o pasar a fabricar y resolver lo que falta sin visitar todos los módulos.

**Recorrido.** Desde Mesa o el documento, «Revisar para emitir» abre un resumen de esa etapa. Agrupa un mismo problema de catálogo que afecte varias posiciones, separa precio vigente de dato técnico desconocido y muestra responsable y destino. Una apertura incompatible destaca su hoja/módulo. Resuelto el problema, se reevalúa el conjunto; no basta cerrar el aviso. «Revisar para taller» usa sus requisitos distintos.

**Datos y construcción.** Reutilizar `catalog_readiness`, motor, medición confirmada, precio, permisos y gates de emisión/producción. La proyección puede resumirlos, pero no reemplazar la validación transaccional al ejecutar. Cada hallazgo tiene código estable, objeto, revisión, causa, acción y permiso. Si cambió el objeto tras revisar, volver a validar.

**Diseño.** El dibujo/documento sigue siendo protagonista; el resumen abre temporalmente y permite localizar. Un estado global acompaña cada etapa, con texto y causa. No comprimir diseño/cotización/fabricación/CNC en un porcentaje ni bloquear una cotización por un requisito que solo corresponde a CNC.

**Valor y aceptación.** Una persona encuentra el bloqueo y llega a su causa sin intervención técnica, puede seguir trabajando en lo independiente y no logra emitir/liberar un objeto inválido mediante otro endpoint. Medir hallazgos verdaderos, falsos bloqueos y tiempo hasta resolver.

**Qué es cierre actual.** Mensajes con causa/salida, aperturas válidas, requisitos de emisión y autoridad honesta ya están comprometidos. La mejora opcional es su revisión transversal y agrupada, si no cabe en la composición prevista. Manual y disponible sin IA; IA puede resolver solo operaciones autorizadas.

## 2. Catálogos mantenibles con impacto — I02

**Trabajo del usuario.** Incorporar una lista nueva del fabricante sin descubrir semanas después que sus presupuestos usan reglas o costos anteriores.

**Recorrido.** Cargar una fuente nueva → vincular fabricante/serie y correspondencias por código → revisar cambios y ambigüedades → publicar versión autorizada → ver borradores dependientes → simular actualización → aplicar a la selección autorizada. Una revisión emitida conserva fuente, precio y contenido; un cambio comercial exige sucesora.

**Datos y construcción.** Identificadores estables, fuente/página/región, versión técnica, política de precios y vigencia. Distinguir regla técnica, dato comercial privado y disponibilidad; no tratarlos como un archivo único que sobreescribe todo. Un alias no prueba que un artículo nuevo sea equivalente. Guardar decisiones de correspondencia y conflictos, con scope de organización.

**Diseño.** La vista de cambios presenta anterior/nuevo y objetos afectados. «Sin dato nuevo» no borra automáticamente el anterior. El estado de revisión de la evidencia es visible. Si cambia una regla esencial, los borradores afectados reciben causa y siguiente acción; no actualización automática silenciosa.

**Valor y aceptación.** Ante un cambio autorizado se identifican exactamente los borradores dependientes, se rechazan los ajenos y una cotización emitida mantiene sus bytes/autoridad. Se mide cobertura de correspondencias, excepciones que requieren experto y tiempo de mantenimiento por serie. Ese costo operativo define si la biblioteca es sostenible.

**Qué es cierre actual.** Fabricante/serie, fuentes útiles, catálogo real revisado y flujo manual ya están comprometidos. El análisis de propagación de actualizaciones es ampliación. Puede convertirse en ventaja difícil de replicar si proveedores participan con permisos y responsabilidad; aún no existe un acuerdo que lo garantice.

## 3. Alternativas para decidir y vender — I03/I04/I10

**Trabajo del usuario.** Explicar por qué una solución cuesta más y permitir que el cliente elija con conocimiento del alcance.

**Recorrido.** Partir de la obra y restricciones → preparar dos o tres soluciones válidas → comparar diferencias → previsualizar la experiencia del comprador → compartir con clic humano → registrar una elección de la revisión ofrecida. Las alternativas conservan cantidades y alcance, o explican cada diferencia. No se comparan una propuesta con instalación y otra sin ella sin advertirlo.

**Datos y construcción.** Reutilizar versiones ofrecidas y elección sellada. Diferencia de precio desde motor y reglas; prestaciones desde cálculo/ensayo aplicable; imágenes desde el mismo modelo de producto. Mostrar dimensiones nominales, apertura, vidrio, acabado e incluidos. Falta de ensayo = no comparable en ese eje. No deducir propiedades de una etiqueta «premium» o de mayor precio.

**Diseño.** Máximo inicial de diferencias que realmente explican la elección, con detalle técnico desplegable. El comprador ve su precio y alcance; costos/margen internos quedan protegidos. El PDF y el portal expresan la misma solución. Una mejora opcional no se preselecciona de forma que parezca obligatoria.

**Valor y aceptación.** El comprador puede describir qué eligió y qué no incluye; la versión elegida coincide con la que alimenta cobro, compra y fabricación. Medir dudas de aclaración, cambios posteriores por incomprensión y finalización de la decisión. Una tasa de aprobación mayor sin controlar precio/segmento no acredita causalidad.

**Qué es cierre actual.** Alternativas/documento/portal y claridad del alcance tienen base existente y compromiso de refinamiento. Un buscador general por necesidades o una optimización multicriterio es ampliación. La selección manual no depende de créditos.

## 4. Impacto del cambio hasta su última consecuencia — I05

**Trabajo del usuario.** Cambiar algo sin olvidar qué se debe recotizar, volver a aprobar, comprar o gestionar en taller.

**Recorrido.** Elegir posición y proponer cambio → capturar versión base → evaluar diseño/BOM/precio → consultar compromisos → presentar un paquete de impacto → aplicar solo lo permitido. Antes de producción puede preparar sucesora; con material comprado u OT en curso debe pasar por conciliación o decisión del responsable. La autorización de una propuesta no reescribe un documento emitido.

**Datos y construcción.** Grafo de dependencias por identidad real: posición, revisión, solución aceptada, OT, reservas, OC, documento y visita. El grafo es una lectura de fuentes existentes, no un nuevo estado autoritativo que debe mantenerse por duplicado. Toda cifra usa el motor. «Costo de cambio» puede tener componentes desconocidos: reparación, cancelación de proveedor o nueva visita no se suponen gratis.

**Diseño.** Separar lo recalculado, lo que necesita decisión y lo que ya está comprometido. La persona ve la diferencia aplicable antes de confirmar. Ofrecer undo solo cuando siga siendo válido; para lo sellado o externo preparar una acción compensatoria explícita. La IA de Trabajo presenta exactamente este contrato según autonomía.

**Valor y aceptación.** Un cambio concurrente invalida el paquete anterior; compras/OT ajenas no aparecen; el cambio no deja un documento o trabajo operativo fingiendo otra configuración. Medir conciliaciones omitidas, versiones obsoletas detectadas y tiempo de resolver el cambio.

**Qué es cierre actual.** Diff, concurrencia, sucesoras e inmutabilidad ya son obligatorios. La orquestación transversal de todos los compromisos es ampliación importante. Construir por escenarios delimitados, sin prometer al inicio reconciliación universal de cualquier estado industrial.

## 5. Primer valor con los datos propios — I08/I09

**Trabajo del usuario.** Llegar a una propuesta útil sin transcribir toda su empresa ni navegar una base DEMO que no reconoce.

**Recorrido.** Elegir una serie real revisada, configurar lo indispensable para el primer presupuesto e importar el conjunto mínimo de clientes/precios/posiciones. Mostrar preview por tipo: nuevo, actualiza, sin cambios y conflicto. Confirmar la parte válida sin perder un informe de rechazos; continuar con una cotización manual. Guardar mapeo útil para próximas listas.

**Datos y construcción.** Unidades y moneda explícitas, IDs del proveedor, origen del precio, ámbito del cliente y reglas de coincidencia. Formularios siempre permiten corrección manual. No importar una planilla opaca como autoridad de ingeniería. Los duplicados no se resuelven solo por parecido de nombre. La reejecución del mismo lote no duplica objetos.

**Diseño.** Pedir solo el dato que desbloquea la tarea presente; ajustes avanzados después. Una lista con errores muestra línea y salida. La base manual permite importación estructurada y edición; extracción de archivos no estructurados con MiMo puede ser un acelerador de planes con IA.

**Valor y aceptación.** Un taller llega a la primera propuesta con datos suyos y entiende los faltantes. Medir tiempo activo humano, asistencia requerida, correcciones y retorno a la segunda obra. No contar una cotización DEMO autogenerada como activación real.

**Qué es cierre actual.** Primer recorrido real y onboarding no engañoso ya son obligatorios. Migración amplia de sistemas antiguos y librería de conectores son ampliaciones que deben responder a archivos de talleres observados.

## 6. La obra terminada mejora la siguiente — I06/I18

**Trabajo del usuario.** Entender por qué perdió margen y cambiar una política futura con evidencia.

**Recorrido.** Cerrar consumos/reportes de una OT → mostrar qué cobertura falta → comparar costo previsto y real sobre la misma solución → localizar desvíos y reposiciones → revisar la causa → preparar una propuesta de política futura. Un dueño puede decidir que el presupuesto de instalación necesita otra base; el software no lo cambia retrospectivamente.

**Datos y construcción.** Reutilizar reportes y métricas actuales, movimientos, devoluciones, retazos, tarifas declaradas y reposiciones. Tiempo transcurrido de una estación no es hora remunerada. Un dato faltante no es costo cero. La evidencia determina si existe una causa conocida o solo una correlación.

**Diseño.** Priorizar pocos desvíos relevantes con acceso a fuente, responsable y estado de revisión. Mostrar «cierre incompleto» cuando corresponda. Preparar una recomendación concreta y su impacto simulado en borradores futuros permitidos; no una gráfica que el dueño deba interpretar solo.

**Valor y aceptación.** El resultado concilia con las fuentes de la OT, protege costos por rol y diferencia corregir reporte de modificar política. Medir esfuerzo de cierre, cobertura y decisiones de política revisadas. El ahorro posterior se mide; no se promete antes del piloto.

**Qué es cierre actual.** Costo/margen trazable y UX comprensible tienen base existente. Aprendizaje asistido y simulación de políticas son ampliaciones; el modelo puede redactar y organizar evidencia, pero no calcular dinero fuera del motor ni adjudicar responsabilidad sin revisión.

## Tres apuestas de empresa

**Producto de entrada: el taller empieza con su primera cotización real.** Invertir en velocidad manual, biblioteca útil, importar lo necesario y propuesta clara. Es una hipótesis de adquisición y activación, no de dar gratis ingeniería o minimizar el producto.

**Ventaja técnica: datos mantenidos y consecuencias trazables.** Cada serie incorpora evidencia, revisión, casos comprobables y mantenimiento. Cada cambio llega a sus dependencias. Esta disciplina puede ser una barrera competitiva más duradera que añadir un modelo de chat; su costo y acuerdos deben ser sostenibles.

**Expansión: coordinación y conocimiento del negocio.** Cuando el taller ya usa el núcleo, añadir escenarios de capacidad/suministro, postventa y análisis asistido sobre su información. Cada extra demuestra tiempo o errores evitados. Mantener MiMo común y más consumo por plan; no presentar un modelo peor como diferenciación comercial.
