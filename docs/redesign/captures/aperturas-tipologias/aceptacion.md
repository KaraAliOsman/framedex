# D03 · aperturas físicas, composiciones y autoridad de manillas

La apertura expresa movimiento, bisagras, dirección y rol de la hoja. El
estimador elige una combinación respaldada por el sistema, ve su dibujo antes
del clic y conserva la misma geometría al guardar, cotizar y emitir el documento.
Los catálogos nuevos son DEMO y no acreditan un producto comercial.

## Alcance y compatibilidad

- `Opening`, uso ventana/puerta y composición de hojas/carriles son contratos
  separados. Los doce valores históricos tienen un mapeo total de ida y vuelta;
  la API acepta ambos transportes durante esta versión. Una puerta antigua sin
  orientación conserva ese desconocido. Sus cortes, BOM y formación de precio
  son idénticos, incluido el transporte de sus documentos sellados.
- Veintiuna variantes verificadas: abatibles interior/exterior izquierda/derecha,
  oscilobatientes, banderola, proyectante, fijo en marco/hoja, francesa activa
  izquierda/derecha, puertas simples y dobles interior/exterior y puerta con
  lateral fijo. Una francesa tiene inversor y falleba pasiva; no se sustituye por
  dos paños con montante. La puerta con lateral conserva el montante.
- Seis autoridades DEMO v3 separadas de v1/v2. Capacidades, kits, encuentro y
  reglas de manilla tienen fuente explícita. El motor deriva el lado de cierre,
  coordenadas y rango editable. La pasiva no recibe manilla de accionamiento.
  No se ofrece una apertura sin capacidad; el rechazo nombra sistemas admitidos.
- Catálogo manual, XLSX, importación revisada, diff, publicación, CSV y deshacer
  conservan las mismas capacidades. RLS/roles y guardas diferidas rechazan kits
  ajenos, inexistentes, retirados o incompatibles. Retirar una serie sin uso puede
  retirar sus kits juntos; reactivarla exige autoridad completa.
- Decimales anidados viajan como texto exacto en ambas validaciones HTTP/servicio.
  Los SKU DEMO compartidos mantienen una sola tarifa exacta y su fuente previa;
  una unidad o tarifa contradictoria provoca error al reproducir la semilla.
  No se reescriben precios anteriores ni se omite la detección de ambigüedad.
- Los vidrios históricos añadidos después de D02 resuelven la misma notación
  en descubrimiento y guardado. Las dos regresiones HTTP guardan/reabren la
  receta y siguen rechazando una propiedad técnica alterada con 409.
- El uso de puerta estructurada conserva las reglas de seguridad del vidrio en
  la vista previa, guardado y recálculo comercial. Se comprueban puertas hacia
  adentro/afuera y el transporte histórico de la vista previa. El catálogo del
  asistente omite una pareja si la bisagra pasiva opuesta no está declarada,
  conservando las aperturas independientes que sí admite la serie.
- Lienzo y documento declaran vista interior. Las líneas parten de las bisagras
  y llegan al lado de la manilla: continuo hacia el observador, discontinuo hacia
  afuera. La constitución §3.6 prevalece sobre el tablero histórico de iconos.

## Recorridos comprobados

| Recorrido | Resultado | Evidencia |
|---|---|---|
| Sistema compatible → pasar/foco sobre banderola → retirar foco | PASA: vista previa con el motor, sin aplicar ni guardar | `recorrido/preview-banderola-sin-aplicar.png` |
| Teclado → elegir → deshacer/rehacer → guardar → reabrir | PASA: apertura exacta persistida y edición atómica | `recorrido/guardado-reapertura-banderola.png`, `navegador.json` |
| 21 variantes → técnica → bisagras y manillas | PASA: hechos del motor y una manilla en la francesa | `recorrido/tipologia-*.png` |
| MiMo real → propuesta exterior derecha → revisar → aplicar → deshacer | PASA: misma operación tipada que la paleta | `recorrido/ia-mimo-propuesta.json`, `ia-mimo-aplicar-deshacer.png` |
| Importar → diff → publicar → CSV → deshacer | PASA: revisión y retiro reales, capacidades exactas | `recorrido/catalogo-diff-capacidades.png`, `catalogo-flujo.json` |
| Editar fuente → guardar → volver a consultar | PASA: doble validación y Decimal exacto | `recorrido/catalogo-navegador.json` |
| Vacío / carga / error y reintento / sin permiso / bloqueado | PASA: cinco estados con texto y causa | `recorrido/catalogo-capacidades-*.png`, `catalogo-estados.json` |
| Estimador → PATCH de catálogo | PASA: 403 del backend, autoridad intacta | `recorrido/catalogo-estados.json` |
| 21 posiciones → reapertura → precio → aplicar → sellar → PDF | PASA: BOM exacto y documento emitido de diez páginas | `recorrido/flujo-21-aperturas.json`, `cotizacion-21-aperturas.pdf` |
| Puerta estructurada → vidrio sin clase exigida → guardar/preciar | PASA: selección bloqueada con causa y 422 del servidor en ambos caminos | `recorrido/seguridad-puerta.json`, seis capturas claro/oscuro |

El documento se rasterizó y revisó: Carta, Plex, marca DEMO en las diez páginas,
vista interior y símbolos de todas las variantes. La puerta con lateral de
2 200 mm conserva R05 cuando falta inercia del montante. Se puede emitir una
cotización incompleta con su advertencia; la liberación a producción permanece
bloqueada. La carga ficticia del ensayo no certifica viento ni una obra.
Las otras veinte variantes tienen fabricación completa en la integración.

Los controles nuevos se recorren en 1440×900, 1280×800 y 1024×768, en ambos
temas. La matriz de técnica comprueba físicamente las bisagras y la manilla de
cada hoja. Los fallos de carga/error retienen o sustituyen solo el transporte;
permisos, catálogo, escritura y cálculos pasan por el servidor real.

`antes/` conserva la línea base de posiciones. `despues/posiciones/`,
`despues/catalogo/` y `despues/proyecto/` conservan los reportes de rutas completas.
Los defectos heredados del editor y del flujo comercial se distinguen de la
paleta, manillas y catálogo D03. El editor no exige 390 px en este encargo; su
desborde anterior queda registrado para P04. P04/P05 continúan radios, densidad,
símbolos y el rediseño general. La consulta de integración de pagos por estimador
ya producía 403 en P01; P08 debe corregir ese acceso sin ampliar permisos.

## Pase editorial: dos rondas

Primera ronda:

1. Se sustituyó la lista de abreviaturas por aperturas con nombre completo y
   gramática común de paleta/lienzo/documento. Se retiró la elección paralela
   que ofrecía combinaciones sin fuente y las rechazaba después.
2. La vista previa usa el cálculo real y mantiene la selección antes del clic;
   pasar, enfocar, Enter, deshacer y guardar se prueban en navegador.
3. Se derivaron lado/rango de manilla y roles de la francesa. Se retiró la
   entrada lateral contradictoria para aperturas estructuradas y la manilla pasiva.

Segunda ronda:

1. Importación y diff dejan de mostrar el parser, UUID y metadatos como prosa.
   Fuentes técnicas quedan plegadas; publicar y deshacer vuelven a ser revisables.
2. Los checkboxes tienen tamaño propio, separación y objetivos accesibles.
   Campos numéricos usan Mono; textos de fuente largos tienen título. La carga
   tiene cargador de cota y el bloqueo sin fuente aparece antes de guardar.
3. Códigos de perfiles/refuerzos/compras quedan en Detalles técnicos; roles se
   traducen también en la ficha. El peso se presenta con dos decimales y su
   precisión exacta en el título. Se retira la interferencia del estilo general
   sobre herramientas/árbol y se corrigen los radios de miniaturas y cantidades.

Momento de firma: la misma gramática de apertura, con el vértice hacia la manilla,
en la paleta, el lienzo y el documento. Idea que sube el techo: vista previa de
la apertura compatible, calculada por el motor, antes de elegirla.

| Rúbrica | Resultado | Evidencia del alcance D03 |
|---|---|---|
| R1 | PASA | Medidas y rangos Mono; transporte exacto; presentación con unidades |
| R2 | PASA | Controles D03 con r-1; contornos; radio del árbol corregido |
| R3 | PASA | Aperturas dentro del inspector, una superficie de edición de catálogo |
| R4 | PASA | Naranja reservado al bloqueo/revisión humana |
| R5 | PASA | Teal en selección, controles y focos |
| R6 | PASA | Nombres del taller, roles traducidos y códigos plegados |
| R7 | PASA | Ingeniería en Avanzado; capacidades en grupos compactos |
| R8 | PASA | Cinco estados reales y 403 de permiso comprobados |
| R9 | PASA | Elevación sobre papel, vista interior y PDF Carta |
| R10 | PASA | Selección con contorno/tinte, vista previa sin mutar |
| R11 | PASA | Gramática DIN y manilla de cierre derivada por el motor |
| R12 | PASA | Foco, preview por teclado, Enter y deshacer |
| R13 | PASA | Sin animación ornamental añadida ni demora de aplicación |
| R14 | PASA | Una elección por bahía; revisión y luego publicación |
| R15 | PASA | Capacidad, manilla y encuentro con fuente; desconocido y R05 explícitos |
| R16 | PASA | Sin degradados, blur, brillos ni morado IA en D03 |
| R17 | PASA | Matriz de anchos exigidos y textos largos accesibles |
| R18 | PASA | Elegir, guardar, revisar, publicar, CSV y deshacer funcionan |
| R19 | PASA | Paleta/lienzo/documento comparten la gramática física |
| R20 | PASA | Preview real del motor con mouse/foco antes del clic |

La rúbrica corresponde al alcance nuevo; no acredita las pantallas pendientes
de P04/P05/P08/P16. Los reportes completos conservan sus hallazgos anteriores.

## Verificación y repetición

Los cuatro gates generales pasan: lint, typecheck, test y build. El motor tiene
581 pruebas aprobadas y dos xfail históricos; backend 1 161; frontend 717 en
62 archivos. El gate de base de datos pasa 986 aserciones pgTAP, 287 pruebas de
integración, 11 recorridos Chromium y los upgrades poblados en PostgreSQL 16.
El drill de mutaciones mata 28/28. OpenAPI/orval, guardas y mypy pasan.
Los goldens históricos no cambian. Los nuevos congelan corte, herrajes y peso para
las 21 variantes; las regresiones comprueban enum/Opening y precio íntegro.
El upgrade poblado incluye BOM/hash, revisiones, historial y tarifas previas.

La comparación final está en `comparacion.json`: cero hallazgos nuevos en las
32 capturas de rutas completas. El catálogo tiene cero hallazgos en sus ocho
capturas; su línea base D01 es manager, con los mismos permisos estructurales
que owner. Posiciones reducen los hallazgos heredados y proyecto queda en 20.
Los desbordes de 390 px y el 403 de integración de pagos ya existían en P01.
La matriz final de estilos tiene 12 capturas limpias y comprueba también los
radios efectivos de las herramientas y del árbol, evitando la interferencia
de cascada. El recorrido publicado tiene 37 capturas limpias; catálogo, 11.

Con el stack local de la skill, el fixture y MiMo configurados por entorno:

```text
python scripts/verify_opening_flow.py
node --experimental-strip-types frontend/scripts/verify-d03.mjs
node frontend/scripts/verify-d03-glass-safety.mjs
```

El navegador copia las posiciones verificadas a su propio proyecto editable.
Comprueba símbolos, manillas, preview, persistencia y propuesta real; falla si
encuentra errores, desbordes o hallazgos en la superficie nueva. Ningún secreto
se guarda en la evidencia. La configuración temporal de ruta IA local se restaura.
La verificación de seguridad restaura las reglas originales del fixture en su
cierre; no modifica reglas productivas ni reclasifica vidrios sintéticos.

## Decisiones, activación y límites

Véanse `docs/decisions/valores-por-defecto.md` y
`docs/operations/ACTIVACION.md`. El proveedor debe aportar capacidades, kits,
encuentro y manillas con fuente; los precios y límites DEMO no los reemplazan.
No hay redondeo oculto de fabricación, incluido el medio centésimo del encuentro.

D04 ampliará selección de herrajes; D08 implementará los movimientos avanzados
declarados. P04/P05 completarán el editor y su simbología general. No se ofrecen
elevables, plegables, pivotantes ni guillotinas como fabricables por D03.
No se envía una cotización a terceros ni se habilita una integración productiva.
