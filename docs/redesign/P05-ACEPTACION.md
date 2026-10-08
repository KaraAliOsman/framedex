# P05 · simbología, cotas y vista declarada

Rama `codex/P05-simbologia-cotas`, base `a67bcefa`. Revisión local 08-10-2026.

Editor, PDF y portal consumen la misma gramática DIN del motor. El recorrido de
cada hoja corredera se declara, se valida y se puede deshacer; cambiar de vista
espeja el conjunto y cambia continuo/discontinuo sin editar el producto. Los
datos sellados de hoja/manilla se proyectan en el portal sin costos ni fuentes
privadas. Puertas usan triángulo en elevación, nunca arco de giro.

## Flujos y evidencia

| Recorrido | Resultado |
| --- | --- |
| Proyecto → tres hojas → dirección central → deshacer → guardar/recargar | PASA. Viaje explícito persistido, ambos lados legibles; intento hacia jamba rechazado por motor. |
| Producto histórico sin viaje | PASA. Bytes/serialización y BOM conservados; «Dirección inferida» visible, declaración mediante inspector. |
| 56 casos de gramática, dos vistas | PASA. Fixtures Python/TS/PDF comparan puntos, flechas, discontinuidad y manilla en mm; incluye 13 casos base, composiciones D03 y diagramas reservados. |
| Arco rebajado/medio punto, trapecio y triángulo | PASA. Marco/vidrio desde contorno e inset; extremo exacto del motor. Capturas reales de arco/trapecio y SVG/PDF de cuatro fixtures. |
| Bahías desiguales, cotas cortas y módulos apilados | PASA. 24 vistas DEV de fixtures del motor, 13 px mínimos, sin colisiones/desborde. Cuatro láminas PDF, dos caras. Sin acoplador autorizado: no se declara fabricación ni persistencia comercial del fixture. |
| Revisión sellada → DOC-01/DOC-03 | PASA. Render solo lectura; una y dos páginas respectivamente, vista/leyenda y cotas legibles. Snapshot sin mutación. |
| Enlace público → doce posiciones/nueve hojas físicas → dos vistas | PASA. 16 vistas en 1440/1280/1024/390, sin exposición de autoridad privada; selectores accesibles debajo de la elevación. |
| Vacío/carga/error/sin permiso/bloqueado | PASA. Cinco estados capturados; transporte demorado/fallido declarado, permisos y revisión cerrada reales. |

[Capturas](captures/simbologia-cotas/): `antes/`, `despues/`, `formas/`,
`conjuntos/`, `portal/`, `estados/`, `pdf/`, `ux/` y `ux-portal/` conservan
matrices y verificaciones. Correderas: 12 vistas y seis muestrarios completos;
formas reales: 24 vistas, tres tamaños y ambos temas/caras. Los runners
oficiales registran 16 vistas de editor y ocho del portal. PNG comprimidos sin
pérdida. El enlace opaco público se elimina de los reportes.

## Pase editorial

Primera ronda: retirar selección de glifos duplicada en Python/TS en favor de
una tabla exportada por el motor; eliminar arcos de puerta y flechas por índice
de las recetas nuevas; llevar las cotas de bahía/manilla fuera de las hojas.

Segunda ronda: alternar niveles de etiquetas cortas y separar módulos apilados;
usar el extremo exacto del arco y distinguir su arranque editable; corregir
selectores del portal en dibujos bajos. Revisión final: elevar la leyenda para
liberar el pie y sustituir contador en píldora/sombra por radio token/delineado.
Se eliminan código de marcas de herrajes y definiciones de flecha sin uso,
parámetros de marcadores muertos y el bloque anterior de cotas apiladas.
La revisión de láminas agrega total del conjunto/testigos y margen para las
etiquetas cortas; contrarrefleja rótulos de módulo/ángulo y retira el ángulo
cero redundante. El ancho gráfico impreso se adapta a conjuntos anchos.

| Revisión | Resultado | Evidencia del alcance P05 |
| --- | --- | --- |
| R1 · Formatos y Mono | PASA | mm enteros HALF_UP, Plex Mono tabular; entrada exacta conservada. |
| R2 · Radios | PASA | Tokens ≤4 px; contador público corregido. |
| R3 · Jerarquía | PASA | Leyenda plegable/delineado; sombra pública retirada. |
| R4 · Naranja | PASA | Solo selección pendiente y autoridad que requiere persona. |
| R5 · Teal | PASA | Selección, vista y foco de tokens. |
| R6 · Voz | PASA | Vista, carril, hoja, jamba, dirección inferida; portal trata de usted. |
| R7 · Densidad | PASA | Inspector de P04 conservado, dirección por hoja contextual. |
| R8 · Estados | PASA | Cinco estados con causas, permisos/revisión reales. |
| R9 · Papel | PASA | Contornos sin relleno oscuro, mismo marco/vidrio en ambos temas. |
| R10 · Selección | PASA | Contorno/tinte/manijas conservados; gramática sin brillo. |
| R11 · Aperturas | PASA | Paridad de 56 casos y vistas; manilla del modelo, puerta sin arco. |
| R12 · Teclado | PASA | Selector/leyenda/inspector con controles nativos y foco. |
| R13 · Movimiento | PASA | Sin animación nueva; tokens/reduce-motion conservados. |
| R14 · Principal | PASA | Guardar y aprobar mantienen región/confirmación existente. |
| R15 · Fuente | PASA | Cotas/extremos del motor; desconocidos explícitos; carril como convención. |
| R16 · Efectos | PASA | Runner oficial sin hallazgos después de corregir contador/sombra. |
| R17 · Anchos | PASA | Matrices 1440/1280/1024; portal 390, sin colisiones/desborde. |
| R18 · Código y acciones | PASA | Selector, viaje, undo, guardado/recarga reales; duplicación/código muerto retirados. |
| R19 · Firma | PASA | F5 planta por bahía/carril y vista declarada; F4 cota conserva edición. |
| R20 · Techo | PASA | Un clic cambia cara/símbolos; viaje imposible se rechaza por el motor. |

## Gates y límites

OpenAPI/orval regenerados. `make goldgen` deja solo 21 líneas aditivas de hechos
de dibujo/envolvente en el golden de operaciones; BOM/cortes/precios existentes
conservados. Prueba de coronación exacta y paridad de cotas/manillas incluidas.
`make lint`, `make typecheck`, `make test` y `make build` PASA sobre la versión
definitiva. Motor: 810 pruebas y dos xfail esperados; backend: 1.335;
frontend: 887 en 77 archivos. Los 150 casos focalizados de paridad, documento
y gramática también pasan. Los 126 PNG finales conservan píxeles tras compresión;
24 registros oficiales no tienen hallazgos, errores ni desborde.

Decisiones en [valores por defecto](../decisions/valores-por-defecto.md).
No se cambia SQL, RLS ni permiso; Database Gate de CI verifica la integración.
No hay integración externa nueva ni sandbox comercial añadido por P05.

Riesgos: el catálogo DEMO no certifica fabricante; sin orden de carriles físico
se declara convención. Curvado pendiente mantiene fabricación incompleta.
D08 conserva los movimientos avanzados, P06 el bow, P07 el rediseño comercial
del portal y P09/P13 la anatomía final de sus documentos. Los diagramas DEV
reservados no habilitan esos dominios. El PDF comercial conserva su precio
sellado y los artefactos ya emitidos no se regeneran automáticamente.
