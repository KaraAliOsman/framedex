# P04 · editor centrado en el lienzo

Rama `codex/P04-editor-canvas-first`, base `c2ecdbc1`, revisión local
08-10-2026. Integración y CI pendientes de registrar después de sus gates.

El estimador abre una posición, elige una tipología compatible, edita las
cotas sobre el dibujo y guarda. La franja compacta reúne ubicación, cantidad,
serie, caras, historial, estado y venta neta indicativa. «Qué falta» lleva al
campo que necesita atención. El inspector usa la selección; herrajes, montaje,
extras y procedencia se despliegan cuando hacen falta.

El precio y el Δ de la propuesta salen del registro y del motor comercial.
Una evaluación sin operaciones consulta el diseño sin mutarlo; una edición
conserva las validaciones del registro. La cantidad es entera y el motor
multiplica/redondea la venta. Carga, error o ausencia de autoridad se muestran
con causa, sin reutilizar silenciosamente cifras viejas.

## Flujos comprobados

| Recorrido | Resultado y evidencia |
| --- | --- |
| Obra → nuevo vano → dos hojas oscilobatientes | PASA. 1500 × 1200 mm y vidrio 4-16-4 mediante tipología, vidrio y dos cotas en el dibujo; el E2E cuenta ≤6 interacciones de diseño. Guardar/recargar conservan hojas, medidas y ubicación. |
| Medida inválida → corrección → guardar | PASA. El registro rechaza ancho 10 mm, conserva la fila persistida y devuelve el campo al ancho aceptado. Ancho 1100,25 y alto 1050,5 se guardan exactamente. |
| Error de transporte al guardar → reintentar | PASA. El borrador conserva medidas/apertura; reintentar usa el servidor real. El recorrido existente sigue comprobando duplicación, precio, BOM y el límite entre organizaciones. |
| Recálculo/precio pendiente → fallo → reintentar | PASA. La franja oculta el importe anterior durante el recálculo y después de un fallo de transporte. Reintentar consulta el motor real y recupera la venta del diseño actual. |
| Seleccionar/apertura/vidrio/dividir | PASA. Riel etiquetado, nombres españoles y aperturas compatibles; una serie practicable no ofrece corredera. Elegir apertura cierra el selector antes de Guardar. |
| Pan extremo → Centrar | PASA. El dibujo mantiene intersección visible después de 10.000 px, comprobada antes de Centrar. El botón ajusta el producto completo. |
| Cambios pendientes → enlaces de proyecto, posiciones y precio | PASA. El guard exige resolver cambios; Cancelar conserva ruta/diseño. Los paneles inferiores se excluyen. |
| Paleta → «partir en tres, centro fijo, laterales abatibles hacia el centro» | PASA. Fantasma naranja, Δ del motor y fuente antes de aplicar. Aplicar produce tres paños; Deshacer devuelve dos. Cambiar cantidad descarta una respuesta tardía. |
| Venta indicativa sin edición | PASA. Integración real comprueba `ops=[]`, diff vacío, siete unidades, Δ cero y fila persistida idéntica. Cantidades 1/7/máximo entero se reconcilian; cantidades inválidas se rechazan. |
| Tablet 1024 → inspector | PASA. Drawer contextual, once campos/lecturas visibles en 768 px de alto; selector no cierra el inspector al elegir. |
| Lectura 390 → cotas/precio/centrar | PASA. Aviso explícito, sin desborde; Ctrl+S y Supr no producen escrituras. |

Las intercepciones E2E solo introducen retrasos y fallos de transporte
declarados. Creación, cálculo, propuesta, persistencia, rechazo y autorización
usan Supabase/Django reales. Las organizaciones E2E se aíslan y eliminan.

## Matrices y capturas

En [capturas](captures/editor-canvas-first/), `antes/` conserva seis vistas
1440/1280/1024 en ambos temas. `despues/` contiene ocho vistas a
1440×900, 1280×800, 1024×768 y 390×844, dos drawers y cinco estados:
vacío, carga, error, sin permiso y bloqueado por revisión cerrada.
`verificacion.json` registra medidas, texto, campos y ausencia de errores.

A 1440 el lienzo mide 928×725 px: 64,4 % del ancho y 80,6 % del alto.
A 1280 mide 768×625 px: 60 % del ancho y 78,1 % del alto. El E2E
comprueba ausencia de scroll horizontal hasta 1920 px. El contenedor flex
reserva el alto real de cabecera: Centrar/pie quedan accesibles en móvil.

El recorrido conserva `dos-hojas-disenadas.png`, `propuesta-fantasma.png`,
`propuesta-fuente.png`, `propuesta-aplicada.png` y `propuesta-deshacer.png`.
La venta DEMO capturada es $746.563 para dos hojas 1500×1200; el ensayo
de propuesta sobre 2000×1200 muestra Δ $−92.216. Son salidas verificadas
del fixture, no tarifas comerciales.

`ux/` conserva el runner oficial de `npm --prefix frontend run ux:capture`:
16 registros de nueva/edición, cuatro tamaños y ambos temas, sin hallazgos,
desbordes ni errores de consola/HTTP. Se inspeccionaron visualmente matrices,
drawers y propuesta; «Sin dato» en el primer ensayo condujo a reparar la
consulta de precio sin operaciones.

## Pase editorial

Primera ronda: reemplazar formularios sobre el lienzo por franja/chips;
herramientas con nombre y tipologías agrupadas; sustituir banner por «Qué
falta» con acciones al campo. Se retira su CSS anterior para conservar una
sola implementación de la superficie.

Segunda ronda: compactar inspector con unidades separadas/Avanzado plegado;
acotar pan/zoom sobre el dibujo físico; corregir capas/borradores rechazados.
La revisión adicional corrige altura móvil y registra el menú contextual como
capa excluyente. El riel de 64 px usa la sección de marca de P25 en lugar de
recortar su logotipo completo. Cierre del selector y consulta sin edición fueron fallos
detectados y reparados en los recorridos existentes.

| Revisión | Resultado | Evidencia del alcance P04 |
| --- | --- | --- |
| R1 · Formatos/unidades/Mono | PASA | Formateadores exactos, coma editable, sin `.00` sobrantes, unidades separadas. |
| R2 · Radios/inglete | PASA | Tokens de radio; inglete en la hoja. |
| R3 · Jerarquía/capa única | PASA | Registro común de flyouts/popovers/pie/menú; E2E de exclusión y cierre. |
| R4 · Naranja | PASA | Fantasma pendiente de aplicar y acciones que necesitan persona; Guardar sin naranja. |
| R5 · Teal | PASA | Selección/riel/foco con tokens. |
| R6 · Voz/taller | PASA | Herramientas, aperturas, causas/comandos en español; DEMO visible. |
| R7 · Densidad | PASA | Once campos/lecturas en drawer 1024×768, registrados. |
| R8 · Cinco estados | PASA | Cinco capturas con causa, permiso/revisión cerrada reales. |
| R9 · Papel sobre mesa | PASA | Lienzo separado por borde y tono en ambos temas. |
| R10 · Selección | PASA | Contorno, tinte/manijas conservados; selección común con inspector/árbol. |
| R11 · Iconos/aperturas | PASA | Riel monolínea 1,5 px; nombres/compatibilidad, renderer sin modificar glifos. |
| R12 · Foco/teclado | PASA | F, paleta, historial, cotas Enter/Esc y guard probados; sin edición móvil. |
| R13 · Movimiento | PASA | Tokens/reduce-motion; sin animación de entrada añadida. |
| R14 · Principal | PASA | Guardar en franja; aplicar en propuesta; regiones sin primarios competidores. |
| R15 · Fuente/desconocidos | PASA | Motor/BOM/precio con fuente; lado de manilla legacy «Sin dato · revisa apertura». |
| R16 · Sin efectos decorativos | PASA | Tokens y runner oficial sin hallazgos; sin degradado/blur/brillo nuevo. |
| R17 · Anchos | PASA | Matriz 1440/1280/1024/390 y E2E hasta 1920; Centrar/pie accesibles. |
| R18 · Acciones/código | PASA | Guardar, cotas, riel, biblioteca, propuestas/pie/historial reales; CSS anterior retirado. |
| R19 · Firma | PASA | F1 hoja/inglete, F4 cota editable, F5 planta existente y F7 manijas conservadas. |
| R20 · Techo | PASA | Comando → registro → fantasma/Δ → aplicar → deshacer con motor real. |

## Decisiones, alcance y riesgos

Véase [decisiones](../decisions/valores-por-defecto.md). Venta indicativa
comparte registro con cantidad explícita; no crea precio aplicado ni sustituye
aprobación comercial. Sin autoridad conserva «Sin dato» con causa/acción.
Tipologías se filtran por serie/perfiles; no se agregan aperturas por decoración.

P04 conserva geometría/glifos/documentos: P05 continúa símbolos/cotas
técnicas, P06 bow/planta y P19 3D. No declara aceptadas esas superficies
pendientes. Catálogo DEMO sin certificación. La franja explica precio indicativo
sin descuento; emisión conserva la autoridad aplicada. Sin integración externa
nueva en este encargo.

## Gates

`make lint`, `make typecheck`, `make test` y `make build`: PASA sobre la
versión final. Motor: 744 pruebas y dos xfail esperados; bytecheck golden
intacto. Backend: 1272 pruebas. Frontend: 831 pruebas en 76 archivos.

`make test-db`: PASA desde stack aislado y limpio. 1173 aserciones pgTAP,
418 integraciones y 17 E2E Chromium, incluidos los seis nuevos de P04.
Las actualizaciones pobladas de PostgreSQL 16 preservan BOM, dinero,
revisiones, artefactos e historiales anteriores. Los 12 recorridos combinados
del stack de desarrollo también pasan. Las 24 integraciones focalizadas
reconcilian cantidades y consulta sin mutación.

CI e integración se registran tras los cuatro checks requeridos. No se
debilita ningún gate.
