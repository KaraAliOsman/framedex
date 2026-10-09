# P06 · conjuntos, planta y autoridad de acoples

Base `19cb78c0`, rama `codex/P06-conjuntos-planta`. Verificación del
09-10-2026 sobre Supabase, Django, worker y Chromium locales.

El conjunto se edita en el mismo lienzo que una ventana. La planta reserva
una franja ajustable bajo la elevación; ambas seleccionan el mismo módulo.
El ángulo se escribe donde se lee o se arrastra con ajuste a
0°, 10°, 15°, 22,5°, 30°, 45° y 90°. La vista previa consulta geometría
y venta al motor; soltar aplica la operación tipada y Deshacer la revierte.
Una unión incompatible conserva el diseño anterior y ofrece el campo exacto
o la autoridad del catálogo para resolverla.

## Autoridad y números

`CouplerRule` declara límites de deflexión absoluta, aporte desarrollado y
fuente. El aporte es la separación entre frentes sobre la bisectriz; en
una unión apilada aumenta la altura. No se infiere del nombre, ancho de
cara ni ángulo de sierra. El motor entrega ancho desarrollado, cuerda,
proyección perpendicular y altura, junto con la ubicación desarrollada
y proyectada de cada módulo. Las juntas se dibujan al centro del aporte.

El catálogo DEMO v7 agrega autoridades explícitas sin reescribir v1–v6.
Sus pivotes comparten el frente y declaran aporte neto cero; siguen
teniendo corte, refuerzo, peso y precio. Son sintéticos, sin certificación.
La autoridad se carga por campos de Catálogo o por la plantilla oficial
CSV/XLSX; un catálogo usado permanece bloqueado. Sin autoridad nueva,
serialización y evaluación omiten los campos añadidos y conservan los
bytes históricos. OpenAPI y orval incluyen los nuevos contratos.

Cada módulo se cotiza de forma independiente con sus medidas, apertura
y relleno. «Acoples y ajustes» es el residual exacto entre el precio unitario
del conjunto y la suma de esas cotizaciones; puede incluir costos comunes
o diferencias de tarifa. No se reparte el total proporcionalmente.
En el bow del recorrido: módulos $300.623, $191.423 y $300.623;
acoples y ajustes $24.319; neto $816.988 y total con IVA $972.216.

## Dos rondas editoriales

Primera ronda:

1. Se elimina la planta separada del formulario y su CSS muerto. Planta,
   selección y elevación comparten el editor y el inspector contextual.
2. Se reemplazan acopladores por nombre con filtros de autoridad angular
   y de sistema. La biblioteca conserva solo recetas compatibles.
3. Se distinguen las cuatro cotas y su fuente. El desglose de venta usa
   cotizaciones por módulo; los errores dejan el botón de reparación preciso.

Segunda ronda:

1. El arrastre mantiene una geometría y un precio de vista previa reales,
   con texto de estado; los rótulos y objetivos conservan tamaño en pantalla.
2. La inspección humana detecta rótulos superpuestos en la sobreluz: una
   huella coincidente recibe un rótulo común y una fila de selección por
   módulo, sin desplazar la geometría. La puerta declara bisagras izquierdas
   antes de resolver su apertura interior desde el catálogo.
3. Se corrigen la ubicación de juntas con aportes no nulos y la lectura
   tipada de medidas decimales selladas en DOC-01. Se prueba el aporte de
   24 mm, incluido el apilamiento, y se elimina la dependencia de IDs fijos
   en la regresión de eliminación y deshacer.

La inspección final compacta el selector de elevación: comparte una sola
fila con la cara visible y deja libre el dibujo. La regla queda acotada al
editor y supera el ancho heredado de los formularios de proyecto. Se reserva
la franja inferior de controles para que el zoom no tape cotas; Centrar
mide el área efectiva de la hoja y conserva sus números y proporciones.

Las [recetas de la primera ronda](captures/conjuntos-planta/ronda1/recetas.json)
y [las posteriores](captures/conjuntos-planta/ronda2/recetas.json) conservan
su evidencia. El [antes](captures/conjuntos-planta/antes/diagnostico.json)
confirma que el catálogo anterior no ofrecía acoples; no se simula un bow
fabricable sin autoridad para producir una captura anterior.

## Recorridos y evidencia

| Capacidad | Resultado |
| --- | --- |
| Bow: central fijo 1 200, laterales abatibles 600, dos uniones de 22,5° | Regresión E2E: siete interacciones, menos de un minuto, guardar/reabrir y modelo idéntico; selección en ambas vistas, cambio de elevación y altura de planta. |
| Arrastre hasta 30°, simulación y deshacer | Regresión E2E: geometría y precio reales, ajuste de ángulo, commit al soltar y restauración con Ctrl+Z. |
| Bow, Bay 45°, puerta + lateral, ventana + sobreluz, esquina 90° | Recorrido con vidrio del catálogo y selección por teclado. La puerta usa la serie de puerta; las otras recetas usan la practicable. [Recetas](captures/conjuntos-planta/ronda2/recetas.json). |
| Vacío, carga, error/reintento, bloqueo angular, sin permiso | Cinco estados en Chromium; el reintento recupera el catálogo real y el bloqueo enfoca Acoplador. [Estados](captures/conjuntos-planta/estados/informe.json). |
| Proyecto → precio → preparación/manillas → emisión → DOC-01 | Revisión A real y worker. Tres páginas Carta, planta y elevación desarrollada en página 2; cuatro cotas presentes, cifras cerradas y sin costos internos. [Verificación](captures/conjuntos-planta/recorrido/doc01-verificacion.json), [página](captures/conjuntos-planta/recorrido/doc01-planta-pagina-2.png). |

El PDF completo y las sesiones privadas permanecen fuera de Git. Su SHA256
es `01afcaaba751ab06cfb09e7d8c979ef786593c288c4ea7b923d0530ed178c3dd`.
La regresión documental también verifica las juntas de un snapshot sellado
con aporte de 24 mm, sin consultar el catálogo actual.

El gate detecta una carrera en la regresión heredada de importación: esperaba
el sistema y confirmaba antes de resolver el vidrio. Se espera también la
selección de vidrio prevista antes del clic, conservando la confirmación,
su carga útil y todas las aserciones existentes.
La integración PostgreSQL actualiza el nombre esperado de la serie vigente
a acoples v7; conserva la igualdad completa del contrato, la serie histórica
v1, todos los campos y el aislamiento por tenant.
La regresión comercial en navegador usa esa misma etiqueta vigente y conserva
las verificaciones de precio, emisión, comparación e inmutabilidad.

La matriz oficial de `ux:capture` conserva 24 vistas posteriores: ocho de
editor y dieciséis de Catálogo como dueño/jefe, en 1440, 1280, 1024 y 390,
ambos temas. No hay hallazgos, errores HTTP, consola ni desbordes nuevos.
La ficha de acople añade ocho vistas, con límites, aporte y fuente reales
del catálogo global bloqueado. Véanse los informes de
[editor](captures/conjuntos-planta/despues/editor/report.json),
[catálogo](captures/conjuntos-planta/despues/catalogo/report.json) y
[ficha](captures/conjuntos-planta/catalogo-acople/informe.json).

## Rúbrica

| # | Estado | Evidencia |
| --- | --- | --- |
| R1 | PASA | Plex Mono, coma/espacio fino, unidades; precisión conservada en el contrato. |
| R2 | PASA | Tokens de radio y hojas existentes con inglete. |
| R3 | PASA | Franja integrada; un inspector y un popover por vez. |
| R4 | PASA | Naranja en manija de ángulo y decisiones humanas. |
| R5 | PASA | Teal para selección y foco, sin colores por módulo. |
| R6 | PASA | Vocabulario de unión, acople, cuerda y módulo; fuente explícita. |
| R7 | PASA | Inspector contextual; campos secundarios plegados; planta ajustable. |
| R8 | PASA | Cinco estados, causa y reintento/campo exacto. |
| R9 | PASA | Planta y elevación sobre papel; mesa y cromo diferenciados. |
| R10 | PASA | Contorno, tinte y manija; selección compartida. |
| R11 | PASA | Gramática DIN existente y aperturas físicas declaradas en recetas nuevas. |
| R12 | PASA | Selección y ángulo por teclado; separador con flechas; reparación enfoca campo. |
| R13 | PASA | Arrastre directo, tokens de movimiento y reduce-motion existentes. |
| R14 | PASA | Guardar como acción de la posición; controles de planta secundarios. |
| R15 | PASA | Cotas y precios con fuente; ausencia de autoridad muestra Sin dato. |
| R16 | PASA | Sin degradado, blur, brillo ni color de IA añadido. |
| R17 | PASA | Matriz de editor y catálogo, ambos temas y anchos del contrato; lectura móvil. |
| R18 | PASA | Se elimina UI/CSS anterior; cada control tiene efecto real. |
| R19 | PASA | F4: el ángulo se edita en la unión donde se lee. |
| R20 | PASA | Arrastrar consulta geometría y precio del motor y permite deshacer. |

## Límites honestos

3D del conjunto corresponde a P19. Las recetas no certifican un fabricante:
la aceptación usa catálogo DEMO declarado. No se inventa autoridad térmica,
de curvado, de acople ni una tarifa ausente. Las revisiones anteriores,
sus snapshots y documentos siguen inmutables. P06 no añade integraciones
externas ni habilita compras, envío o producción sin clic humano.

Gates finales y CI se registran al integrar; esta evidencia no sustituye
los cuatro checks obligatorios.
