# Experiencia propuesta y arquitectura de información

## La unidad de trabajo

La unidad visible es un **proyecto con sus ventanas y cotizaciones**. Una cotización rápida puede iniciar ese proyecto sin obligar a describir una obra entera. La ventana sigue siendo el objeto que conecta diseño, precio, materiales y fabricación. «Posición» puede usarse en listas profesionales cuando ayuda; en la primera experiencia, hablar de ventanas, puertas o conjuntos según corresponda.

No crear un segundo modelo de cálculo para el modo rápido ni otro chat que almacene una versión diferente del diseño. El modo manual y la IA deben modificar los mismos objetos mediante los mismos servicios y comandos autorizados.

## Navegación principal

| Lugar | Contenido habitual | Qué sale de la navegación principal |
|---|---|---|
| Proyectos | Recientes, búsqueda, trabajos activos y vista de cotizaciones | La separación permanente entre proyecto, precios y emisión |
| Clientes | Ficha, proyectos, contactos y direcciones | Formularios repetidos de identidad en otros módulos |
| Catálogos | Sistemas utilizables, importación, fuentes y versiones | Una primera vista dominada por campos técnicos |
| Taller | Órdenes, corte, compras, existencias y salidas | Módulos dispersos que requieren conocer el recorrido de datos |
| Empresa, acceso inferior | Preferencias, documentos, equipo y controles del negocio | Opciones de infraestructura en el uso diario |

El logo permite volver a la lista de trabajos. La IA permanece como acceso estable y panel contextual; «Trabajos de IA» pasa a ser su actividad, no otra aplicación que el usuario tenga que administrar. Analítica se abre desde el resumen del negocio o Empresa. La búsqueda global encuentra obra, cliente, cotización, material y acciones por sus nombres habituales.

No es necesario cambiar todas las URL al mismo tiempo. Conservar enlaces profundos y redirigir destinos sustituidos. Un enlace a la vista antigua de precios debe abrir el contexto correspondiente, no devolver una pantalla vacía.

**Por rol:** el dueño y estimador comienzan en proyectos; el responsable de taller en órdenes y pendientes de producción; el operario en su estación; el instalador en su agenda. Compras e inventario deben ser accesos inmediatos dentro del espacio habitual de quien los usa. La simplificación de navegación no modifica los permisos de las API.

## Primera sesión

1. Mostrar una entrada reconocible: «Nueva cotización», trabajos recientes y «Importar catálogo» si no existe ningún sistema utilizable.
2. Abrir tipologías con dibujos y nombres. No ofrecer primero una lista de estructuras internas del catálogo.
3. Permitir diseñar con datos autorizados existentes. Si solo hay un catálogo de demostración, indicarlo una vez en el contexto del trabajo; no repetir una advertencia por cada campo.
4. Si la empresa no está preparada para calcular precio o emitir, permitir avanzar en el dibujo y resolver los datos que faltan en el momento correspondiente.
5. Guardar preferencias al completar el primer trabajo real. No convertirlo en una visita guiada de todas las funciones del programa.

**Dependencia de datos:** el backend actual exige relaciones para crear proyectos. Antes de implementar, comprobar sus restricciones. La dirección preferida es permitir un borrador incompleto en el agregado existente, con cliente opcional hasta emitir y validación por etapa. Si eso exige una alteración mayor, conservar un borrador provisional explícito hasta vincularlo a un cliente real. No crear clientes falsos ni proyectos duplicados para simular que el recorrido es simple.

## Recorrido manual: una ventana sencilla

| Momento | Lo que ve la persona | Lo que hace el sistema |
|---|---|---|
| Empezar | «Nueva cotización» y tipologías ilustradas | Aplica preferencias válidas de empresa |
| Definir | Dibujo, ancho, alto, cantidad, apertura | Resuelve compatibilidades y componentes mediante el modelo vigente |
| Elegir aspecto | Muestras de acabado y vidrio | Aplica una elección coherente al producto completo |
| Revisar | Ventana, precio calculado y acción «Ver cotización» | Prepara presentación con condiciones heredadas |
| Presentar | PDF real y cliente editable en contexto | Indica solo faltantes que impiden esa entrega |
| Continuar | «Materiales» y «Orden de corte» | Prepara resultados asociados a la misma revisión |

No convertir la secuencia en seis páginas obligatorias. El editor reúne diseño y opciones; el documento es otra vista del mismo trabajo. Una persona experta puede entrar directamente a su tarea.

La meta de aproximadamente un minuto se aplica a una ventana estándar con sistema, costos y preferencias preparados. Medir aparte el primer catálogo, la configuración de empresa, una forma especial y la espera de proveedor de IA. No acelerar ocultando un dato de fabricación que realmente falta.

## Recorrido con IA

Solicitud ilustrativa: «Prepara cuatro correderas de 1.200 por 1.000 para la casa de Ana, con lo habitual, y enséñame la cotización».

El asistente identifica el proyecto/cliente si hay coincidencia inequívoca, usa preferencias válidas, crea el borrador autorizado, solicita cálculo al motor y abre una muestra con los cuatro dibujos, especificaciones principales y documento. Solo pregunta si falta una decisión esencial o hay ambigüedad material. Si hay dos clientes Ana, no elige arbitrariamente.

La revisión debe permitir «Cambiar el acabado», «Editar una ventana», «Aplicar a todas» y «Deshacer». No devolver una explicación de diez pasos para que el usuario repita la solicitud en formularios. El [contrato del trabajador](07-ia-como-trabajador.md) define ejecución, límites y estados.

## Preferencias y preguntas

| Dato | Comportamiento propuesto |
|---|---|
| Sistema/serie | Preferencia válida para el tipo elegido; si no existe, elección ilustrada |
| Ancho y alto | Entrada esencial para calcular; aceptar lenguaje natural y confirmar interpretación ambigua |
| Cantidad | Una unidad visible por defecto, editable; no confundir unidades con hojas |
| Apertura | Tipología elegida o instrucción clara; vista y lado de apertura visibles |
| Vidrio | Heredar una configuración compatible; excepción por ventana |
| Acabado | Un acabado por defecto; bicolor dentro de «Acabado especial» |
| Refuerzo/herraje/junquillo | Derivar cuando hay regla declarada; preguntar por una excepción real |
| Margen/impuestos | Preferencias autorizadas del negocio, con alcance por rol |
| Cliente/contacto | Se completan cuando hace falta guardar/vincular/entregar; no al cambiar una cota |
| Dirección de obra | Solo necesaria para tareas que dependan de ubicación/entrega; no por costumbre |
| Firma/pago | Política del negocio y acción explícita; no un requisito de diseño |
| Parámetros de corte | Preferencias de taller válidas; se muestran al ajustar o si falta autoridad |

**Herencia:** empresa → proyecto → ventana. Mostrar «De la empresa» de manera discreta cuando se necesite entender el origen. Una excepción permite «Volver a lo habitual». Cambiar el valor global no altera silenciosamente revisiones emitidas ni todos los proyectos existentes.

## Proyecto y colección de ventanas

Cabecera compacta: nombre, cliente, estado comercial y acción principal. Debajo, colección de ventanas con dibujo reconocible, ambiente/nombre, medidas, cantidad, acabado y precio. El usuario alterna entre una vista visual y una tabla útil para muchas posiciones; no necesita que una vista intente ser ambas simultáneamente.

Acciones de fila: abrir, duplicar y menú de opciones. Acciones de selección: aplicar acabado/vidrio, duplicar, mover y eliminar con posibilidad de recuperación. No mostrar iconos de todas las acciones en cada fila. El total y la siguiente acción permanecen localizables sin competir con las ventanas.

Cuatro vistas del proyecto: **Ventanas, Cotización, Materiales y Actividad**. Corte y documentos se abren desde sus acciones. La información de fabricación aparece en la ventana o en Taller. No mantener ocho pestañas visibles para trabajos que aún no las necesitan.

## Editor

- El dibujo ocupa la mayor parte del área útil. Cotas editables y selección directa de marco, hoja, vidrio o división.
- Herramientas de uso frecuente agrupadas: seleccionar, dividir, apertura, medidas, deshacer/rehacer y vista 2D/3D.
- Inspector contextual con lo aplicable a la selección; no una lista de propiedades del proyecto entero.
- Precio resumido y estado del cálculo claros. Los cambios no deben desplazar el dibujo ni borrar el punto de trabajo.
- Al abrir IA, compartir el riel lateral con el inspector o plegarlo; evitar dibujo estrecho entre dos columnas vacías.
- Teclado para repetición y precisión; alternativas visibles para quien no conoce atajos. Los atajos complementan el recorrido, no lo explican.
- Formas, uniones y fabricación especial en herramientas de contexto. No eliminarlas; evitar que parezcan necesarias para una corredera sencilla.

## Lenguaje

| Texto actual o patrón | Texto habitual propuesto | Contexto |
|---|---|---|
| Autoridades de precio | Costos y reglas de venta | Configuración del negocio |
| Completar costos y autoridades | Completar el costo de este material | Faltante concreto |
| Posiciones | Ventanas / puertas / conjuntos | Según objeto; «posición» queda donde sea útil al oficio |
| Artefacto | Documento, comparación, dibujo o lista | Nombrar el resultado real |
| Jobs / trabajos técnicos | Actividad del asistente | Panel de IA |
| Emitir revisión canónica | Emitir cotización | Revisión en información secundaria |
| Sin dato, repetido en todo | Falta elegir vidrio / Falta costo del marco | Solo donde cambia la acción |
| P-000015 como título | Casa de Ana | Código en detalle |
| Δ precio neto por posición | Cambio en el precio de esta ventana | Vista de efecto del acabado |
| Requisitos congelados de la revisión | Materiales de esta orden | Detalle auditable a un clic |
| Cargando precios y autoridades | Calculando precio | Si eso es lo que realmente ocurre |

Usar español profesional, frases cortas y verbos concretos. No sustituir terminología conocida por palabras vagas para parecer sencillo. Marco, hoja, junquillo y travesaño ayudan al profesional; fingerprints, payloads y capacidades internas no ayudan al cliente.

## Retirar, plegar y conservar

**Retirar de la experiencia habitual:** selector de tema, ilustraciones vacías gigantes, tarjetas sin una acción útil, introducciones repetidas de cada módulo, estados técnicos como títulos, selector manual de superficie IA, inspector de artefacto vacío y configuración de caducidad técnica de preview.

**Plegar o ubicar en contexto:** PVC bicolor, trazas, huellas, refuerzos especiales, mecanizado, tolerancias declaradas, reglas avanzadas de corte, auditoría de precio, configuración del proveedor de IA y soporte técnico.

**Conservar y hacer accesible:** permisos, operaciones históricas, diagnóstico de un faltante, revisión emitida, cambios de costo/margen, búsqueda, materiales, corte, CNC y estados reales de tareas.

No hacer una limpieza de rutas o tablas por intuición. Cada retirada de UI debe tener una alternativa concreta y una migración de enlaces si corresponde.
