# Ventanas, perfiles y texturas

## Conservar y mejorar la base

El motor y los hechos de dibujo continúan siendo la fuente de medidas y componentes. `ProductFrontSvg` ya se reutiliza fuera del editor y `finishMaterials3d.ts` ya carga mapas de textura. No construir un segundo dibujante independiente para la cotización ni anunciar soporte de texturas como si partiera de cero.

El objetivo es que una ventana se reconozca por su composición, apertura, espesor visible y acabado, y que la misma identidad continúe en miniatura, editor, 3D, comparación y PDF.

## Tres representaciones con funciones distintas

| Representación | Para qué sirve | Fuente de verdad |
|---|---|---|
| Dibujo técnico | Dimensiones, apertura, orientación y fabricación | Geometría/hechos declarados por motor y catálogo |
| Presentación comercial | Explicar el producto y mostrar material con claridad | Mismo producto; estilo de representación distinto |
| Ilustración de perfil | Reconocer familias y elegir en catálogo | Familia conocida; aproximada si no hay sección verificada |

Una ilustración atractiva no se convierte en sección de fabricación. Una foto puede ayudar a identificar material; no prueba descuento de corte, pared interna o compatibilidad. «Serie 60» tampoco demuestra por sí sola una sección de 60 mm: nombres comerciales y medidas técnicas deben conservarse separados.

## Dibujo 2D

1. Mantener proporciones y vista interior/exterior declarada; no reflejar un dibujo solo para que parezca otra vista.
2. Jerarquizar líneas: contorno principal, miembros, encuentros, juntas y símbolos. Evitar que cada línea tenga el mismo peso.
3. Mostrar cotas generales por defecto. Cotas de módulos y detalle al seleccionar o activar una vista técnica. Una miniatura no debe contener el mismo conjunto de cotas que una lámina.
4. Representar apertura, mano de cierre, carriles y solapes a partir de hechos del producto. Mantener la convención entre icono y plano.
5. Usar vidrio sobrio y marco con acabado reconocible; la selección no debe teñir toda la ventana hasta borrar su material.
6. Incluir manilla/herraje visibles cuando existen datos que lo justifican, a una escala que permita reconocerlos.
7. Conservar selección por pieza y relación con materiales, sin llenar el plano de etiquetas al mismo tiempo.

La presentación comercial usa menos cotas, anotaciones breves y una vista coherente. No eliminar información necesaria para comprender apertura o medidas. El estilo técnico permite fondo blanco, línea fuerte y contraste de impresión incluso en blanco y negro.

## Encuentros y uniones

El código revisado en `Product3DScene.ts:422` extruye perfiles con encuentros de extremos rectos. El plan debe ampliar su representación según el tipo de unión autorizado, en lugar de superponer una diagonal a todas las esquinas.

| Caso | Tratamiento propuesto |
|---|---|
| PVC soldado | Encuentro y línea de soldadura/acabado coherentes con la unión declarada; sin exagerar un hueco negro |
| Aluminio con inglete | Dirección y encuentro derivados del corte/unión; diagonal legible cuando corresponde |
| Unión a testa | Jerarquía y continuidad del travesaño/montante correctas |
| Corredera | Carriles, solapes, hojas y cruce del encuentro coherentes con su configuración |
| Acople entre conjuntos | Diferenciar unión de conjuntos de una división dentro del mismo marco |
| Geometría no declarada | Reserva ilustrativa reconocible, sin afirmar una unión de fabricación inventada |

Resolver continuidad de caras y texturas en 3D. Una línea 2D puede representar un encuentro; no debería ocultar una intersección geométrica incorrecta en una vista de detalle. No modificar fórmulas de corte para conseguir una apariencia bonita.

## Biblioteca de acabados

Definir un conjunto inicial de calidad que cubra acabados realmente soportados: PVC blanco y foliados habituales, aluminio pintado, anodizado y otros acabados autorizados por los catálogos. No asignarles nombres de fabricantes sin correspondencia real.

Por acabado, conservar identidad, color, procedencia, mapa base y metadatos de presentación: escala de repetición, dirección del grano, rugosidad/brillo y, si mejora de verdad la lectura, mapas adicionales. Estos metadatos visuales no introducen medidas de fabricación.

En 3D, comprobar UV por miembro y escala física de textura; girar el grano con el perfil, no con la página. Evitar que la madera se estire con el ancho total de una ventana o que todas las barras tengan la misma mancha repetida. La iluminación debe revelar el material sin cambiar arbitrariamente su color. Mantener la separación existente entre colores del tema y color del producto.

En 2D, usar patrones recortados por miembro, orientación y contraste preparados para su tamaño. En miniatura, reducir ruido sin convertir madera en un relleno plano. Las muestras del selector deben ser suficientemente grandes para reconocer veta y acabado.

**Un color normal:** elegir un acabado aplica la solución habitual. «Acabado especial → distinto por cara» habilita interior/exterior y muestra una representación explícita. Los datos bicolor existentes se siguen abriendo correctamente, aunque el control deje de dominar la primera vista.

## Material aportado por el negocio

Recorrido: subir imagen → recortar/alinear → preparar repetición o usar imagen de referencia → revisar muestra sobre una ventana → guardar en biblioteca privada.

La IA puede limpiar iluminación, proponer un patrón continuo y clasificar el aspecto. Conservar original y versión preparada, permitir ajustar escala/orientación y deshacer. No asignar un RAL exacto ni certificación de fabricante a partir de una foto. La interfaz puede distinguir «Referencia del negocio» de «Acabado del fabricante» con un detalle discreto.

Los permisos y almacenamiento son por empresa; validar formato/tamaño, quitar metadatos innecesarios y usar acceso privado. Guardar licencia/origen de activos distribuidos con DEKOPEN. Generar imágenes nuevas solo en la futura implementación si son necesarias para materiales; no usar una imagen generativa como plano técnico.

## Ilustraciones de perfiles

Preparar familias de marco, hoja, montante, travesaño, junquillo, acople, refuerzo y perfiles auxiliares. Una familia puede tener variantes de profundidad, ala y forma para reconocimiento. Aplicar únicamente dimensiones confirmadas y marcar la representación ilustrativa como tal cuando no haya sección real.

Orden preferido de representación: sección vectorial verificada → imagen/foto del fabricante vinculada → ilustración de familia → reserva explícita. No mostrar simultáneamente las cuatro. Conservar siempre acceso a la página fuente.

La IA puede proponer familia, recorte o ajuste ilustrativo. Un polígono de sección exacta exige extracción verificable o aprobación técnica específica. El rectángulo aproximado actual es honesto; mejorar su valor de reconocimiento no significa quitar esa honestidad.

## 3D y salida documental

El 3D sirve para acabado, apertura y explicación espacial. Mantener cámara predecible, zoom y giro recuperables, vistas interior/exterior claras, luz neutral y opción de volver a un encuadre útil. Cargarlo cuando se necesita; una primera cotización no debe esperar a una escena pesada si el dibujo 2D ya comunica la solución.

La cotización debe usar una instantánea estable del producto y sus activos. No depender de una URL que pueda caducar al volver a imprimir una revisión emitida. Preparar variantes técnica/comercial del mismo dibujo, conservar vector donde sea posible y rasterizar solo materiales o vistas que lo requieran.

La caché de vistas debe considerar geometría, acabado, activos y versión del renderizador. No reutilizar una imagen antigua después de cambiar el color. Si falla una textura, ofrecer una reserva coherente y distinguir el problema; no bloquear el cálculo por un fallo ornamental ni emitir una muestra engañosa como si estuviera completa.

## Criterios finales

Evaluar juntos: fijo blanco, corredera foliada, abatible con manilla, conjunto con travesaño, aluminio con unión declarada, forma especial y bicolor excepcional. En cada uno comprobar identidad entre editor/PDF, legibilidad a tamaño real, textura por miembro, vista de apertura y diferencia entre ilustración y autoridad técnica. Estos son casos de cierre, no una orden de ejecutar pruebas en cada cambio.
