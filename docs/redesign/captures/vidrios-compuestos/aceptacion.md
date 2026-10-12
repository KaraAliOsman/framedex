# D02 · composición, seguridad, precio y pedido de vidrio

El vidrio se elige como un producto del catálogo con una receta verificable. El
motor deriva corte, espesor, masa y precio. Las reglas de la organización citan
su fuente y el pedido conserva la misma autoridad al pasar de cotización a OT.
Los datos de arranque son DEMO: no acreditan seguridad ni rendimiento térmico.

## Alcance comprobado

- Modelo exterior → interior: láminas de distintos tipos/colores, laminados con
  múltiples PVB, caras de capa, cámaras, gas, separador y sellante. Parser y
  formateador con 30 notaciones, mayúsculas/minúsculas, espacios y coma decimal;
  recetas estructuradas conservan los datos del proveedor.
- Decimal: peso con PVB, espesor neto/total, junquillo por espesor total, corte,
  área mínima, templado, pulido, perforación y palillaje por metro/cruce. Los
  goldens nuevos verifican los cargos; los goldens históricos no cambian.
- Datos con fuente: Ug, g, transmisión, clase, masa declarada y límites.
  Desconocido dice **Sin dato**; no se fabrica una densidad del PVB. El antepecho
  desconocido exige revisión. La masa de la hoja se compara con el herraje actual.
- Regla de seguridad con referencia y alternativa compatible. Recomendación por
  defecto; el backend rechaza guardar una regla obligatoria incumplida con 422.
  Los ejemplos sintéticos no satisfacen una regla oficial.
- Receta ligada a un mapping inmutable: el backend rechaza propiedades,
  composiciones o identidades falsificadas. Publicar un SKU nuevo en una serie
  global congelada no modifica la autoridad anterior. Dueño/encargado publican;
  estimador consulta y selecciona; RLS separa organizaciones.
  Omitir la receta de un SKU estructurado tampoco permite evitar sus límites o
  cargos. Las escrituras con notación histórica siguen sujetas a reglas de
  seguridad obligatorias; el nombre antiguo no acredita una clase.
- Décima hoja **Reglas de vidrio**, por la ingesta D01 con fuentes, diff,
  publicación, historial inmutable y deshacer. Los mappings anteriores reciben
  composición conservadora o UNKNOWN sin cambiar BOM, precio, revisión o hash.
- Pedido de OT o lote de hasta 100 órdenes: PDF/CSV/etiquetas desde el BOM sellado,
  ordenados por proyecto/revisión/posición, con composición, procesos, cantidad,
  huella y QR de la pieza real. CSV neutraliza fórmulas. La descarga usa
  `export_format` para no colisionar con la negociación de formato HTTP.

## Recorridos y cinco estados

| Recorrido | Resultado | Evidencia |
|---|---|---|
| Ajustes → ejemplos → diff → aplicar reglas | PASA: fuente e historial reales | `recorrido/reglas-aplicadas.png` |
| Low-E en paño lateral → aviso en la bahía → alternativa → deshacer/rehacer | PASA: selección atómica con el motor | `recorrido/aviso-en-bahia.png` |
| Guardar → reabrir → compositor → diff → publicar variante → deshacer/rehacer → guardar | PASA: receta persistida e identidad inmutable | `recorrido/guardado-y-reabierto.png`, `diff-antes-de-publicar.png`, `qa-report.json` |
| Estimador → avanzado → compositor sin permiso | PASA: consulta y corte a escala; publicación restringida | `recorrido/compositor-sin-permiso-dark-1024.png` |
| Vacío | PASA: reglas vacías reales y acción para configurarlas | `recorrido/estado-vacio-real.png` |
| Carga | PASA: consulta real retenida y cargador de cota | `recorrido/estado-carga-transporte.png` |
| Error → reintentar | PASA: fallo 503 de transporte y recuperación real | `recorrido/estado-error-transporte.png`, `states-report.json` |
| Bloqueado → guardar | PASA: regla obligatoria real, causa y 422 del backend | `recorrido/estado-bloqueado-real.png`, `regla-obligatoria-rechaza-guardar.png` |
| 12 posiciones → precio con procesos → aplicar → sellar → DOC-01 → 12 OT | PASA: 24 etiquetas, cantidades y medidas exactas | `recorrido/flujo-12-posiciones.json`, `cotizacion-12-posiciones.pdf` |
| OT/lote → revisar pedido → descargar PDF/CSV en navegador | PASA: cantidades y corte iguales al motor | `recorrido/pedido-12-posiciones.pdf`, `pedido-12-posiciones.csv`, `ui-pedido-vidrio.pdf`, `ui-pedido-vidrio.csv` |

Las pruebas cubren 1440×900, 1280×800 y 1024×768 en ambos temas; pedido también
390×844. `qa-report.json` contiene **36 capturas, cero desbordes, cero errores,
cero hallazgos de texto y cero hallazgos de presentación en los controles de
vidrio**. Los fallos de carga/error inyectan solamente el transporte; las reglas,
recetas, permisos y escrituras usan el servidor real.

`ux:capture` verifica además las rutas completas en `despues/ajustes/`,
`despues/produccion/` y `despues/posicion-edicion/`. Los defectos heredados del
editor y Producción permanecen identificados en esos reportes; la cantidad de
filas DEMO crece al repetir los recorridos. La aceptación de D02 corresponde al
selector, compositor, reglas y pedido nuevos. P04/P12/P13 deben cerrar los radios,
densidad y objetivos táctiles anteriores del resto de esas pantallas. No se
atribuyen a D02 sus rediseños pendientes. El editor no requiere 390 px en D02.

Los dos PDF se rasterizaron e inspeccionaron: papel Carta, seis páginas cada uno,
Plex Sans/Mono, pedido legible y 24 etiquetas con QR. La marca DEMO se repite en
todas las páginas del DOC-01, incluso aceptación, y reconoce una receta sintética
en una serie comercial. La corrección de URI de fuente Windows admite solo los
TTF empaquetados y rechaza archivos externos. Los documentos anteriores no se
reescriben.

Para repetir la aceptación con el stack y el fixture de la skill cargados, desde
la raíz del repositorio:

```text
python scripts/verify_glass_flow.py
node --experimental-strip-types frontend/scripts/verify-d02.mjs
```

El primer comando crea un proyecto DEMO nuevo, lo cotiza, sella y libera doce OT;
el segundo recorre los controles y descarga los archivos de esas OT. Los secretos
se reciben por entorno. El navegador falla ante errores, desbordes o hallazgos
de texto/presentación en la superficie de vidrio; no declara PASA por capturar una
pantalla. Las reglas quedan en los ejemplos DEMO revisados de este fixture.

## Pase editorial, dos rondas

Primera ronda, las tres mejoras más débiles:

1. Se reemplazó el compositor apilado por sección a escala fija y campos en dos
   columnas dentro del diálogo; el estimador ve la receta sin perder su corte.
2. Se eliminó `GlassSummary` y su edición paralela. El pedido por OT y lote lee la
   revisión sellada; no permite introducir otra medida en una tabla auxiliar.
3. Se compactó el PDF en cinco columnas, se tradujeron procesos y se separaron las
   etiquetas. La advertencia DEMO común dejó de repetirse dentro de cada fila.

Segunda ronda, las tres mejoras más débiles:

1. Masa a un decimal y área a dos; precisión original en **¿De dónde sale?**.
   Notación con coma decimal, medidas Mono y textos largos con título accesible.
2. Los controles de vidrio dejan de heredar radios de 6 px y tipografía pequeña
   del inspector. El enlace de ingesta pasa AA en oscuro; el pedido usa 44 px.
3. Se corrigieron las fuentes locales del PDF y la marca DEMO multipágina. Se
   verificó descargar desde el navegador, no solo la respuesta JSON del pedido.

Momento de firma: corte exterior → interior a escala, con cámara, gas, separador
y PVB. Huella en cajetín y etiqueta. Idea que sube el techo: aviso de seguridad en
la bahía afectada y alternativa compatible aplicada con un clic, deshacer y
rehacer reales.

| Rúbrica | Resultado | Evidencia en la superficie D02 |
|---|---|---|
| R1 | PASA | Mono tabular, unidades, coma decimal, precisión visible y exacta separadas |
| R2 | PASA | Tokens r-1 y contornos; comprobación de estilos efectivos |
| R3 | PASA | Jerarquía por borde; un compositor en diálogo |
| R4 | PASA | Naranja solo en aviso que requiere revisar una persona |
| R5 | PASA | Teal funcional y tonos de la constitución |
| R6 | PASA | Vocabulario de vidrio/taller; procesos traducidos; documento trata de usted |
| R7 | PASA | Campos compactos, grilla de capas y detalle progresivo en 768 px |
| R8 | PASA | Vacío, carga, error, sin permiso y bloqueo recorridos |
| R9 | PASA | Sección y documento como papel sobre mesa |
| R10 | PASA | Selección con contorno y tinte; bahía conserva manijas |
| R11 | PASA | Línea técnica del lienzo, sin iconografía decorativa añadida |
| R12 | PASA | Botones/inputs nativos, foco del sistema y acceso al aviso por teclado |
| R13 | PASA | Validación diferida sin animación ornamental; movimiento existente respeta reducción |
| R14 | PASA | Revisar y luego publicar/aplicar; exportaciones secundarias |
| R15 | PASA | Propiedades con fuente; derivados del motor; Sin dato con causa |
| R16 | PASA | Sin degradados, blur, brillo ni morado IA en D02 |
| R17 | PASA | Sin desbordes en tamaños exigidos; títulos en textos largos |
| R18 | PASA | Selección, publicación, reglas, deshacer, lote y archivos funcionan; resumen viejo retirado |
| R19 | PASA | Corte a escala, huella y carga de cota conservados |
| R20 | PASA | Aviso localizado y alternativa compatible calculada por el motor |

## Validación técnica (06-10-2026)

`make lint`, `make typecheck`, `make test` y `make build` pasan sobre la versión
final: 526 pruebas de motor y dos xfail históricos, 1.147 de backend y 707 de
frontend. Los goldens históricos permanecen idénticos y el drill detecta las
28 mutaciones de ±0,01 mm.

`make test-db` pasa aislado: SQL lint, 959 aserciones pgTAP, 280 pruebas de
integración, 11 recorridos Chromium, migraciones sobre PostgreSQL 16 y actualización
de datos poblados. La actualización conserva BOM/hashes, revisiones y todo el
historial de precios y documentos. Los seis casos de integración de vidrio
incluyen falsificación de autoridad, RLS y rechazo del intento de omitir la receta
o eludir una regla obligatoria mediante notación histórica.

La ejecución directa detectó y corrigió una colisión de unidad en el fixture:
comprar una pieza de vidrio no implica cotizar su código técnico por unidad.
`dev_fixture.py` ahora resuelve ese código en m² y siembra las tarifas DEMO
declaradas, incluidos los procesos, leyendo `NUMERIC` como `Decimal`. La reparación
idempotente queda limitada a la lista y filas sintéticas `FIXTURE`; los precios
sellados anteriormente no se reescriben.

Los dos verificadores publicados se ejecutaron directamente desde la raíz y
pasaron. Los PDF finales tienen seis páginas cada uno, Plex y marca DEMO en todas
las páginas; la nueva prueba cubre también la continuación del pedido. Las 36
capturas verificadas tienen cero hallazgos y desbordes en los controles de vidrio.

## Decisiones y límites

Las decisiones están en `docs/decisions/valores-por-defecto.md`; norma oficial,
fichas, tarifas y origen del QR se activan con `docs/operations/ACTIVACION.md`.
Se mantienen los decimales del corte: convertirlos a enteros cambiaría fabricación
y rompería 0,00 mm. El proveedor debe aceptar esa precisión, no un redondeo oculto.

No se acredita NCh 135 ni se inventa Ug/g/TL. D04 ampliará herrajes y P13 la
estación completa de etiquetas; sus capacidades futuras no se presentan como
terminadas. El pedido se descarga; no se envía a un tercero. Se conserva el
catálogo histórico y las revisiones emitidas. Un vidrio con contorno exige su
plano sellado. La auditoría general de documentos corresponde a P09.
