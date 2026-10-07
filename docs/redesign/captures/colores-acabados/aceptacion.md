# D05 · colores y acabados por caras

El estimador elige interior y exterior desde una carta con fuente y ve el
refuerzo, plazo adicional y delta neto calculado. La identidad comercial llega
al precio, revisión, compras, stock y plan de corte. Cliente y documento declaran
las caras de esa revisión; el render utiliza los canales del catálogo.

## Evidencia del alcance

| Recorrido | Evidencia |
| --- | --- |
| Siete acabados PVC/aluminio → reglas, BOM y recargo exacto | `engine/tests/golden_finishes.json`, `test_gold_cases_finishes.py` |
| Combinación inválida, límites, refuerzo, moneda y dato ausente | Tests del motor, integración `test_finish_api.py` |
| Stock por perfil/color y acero independiente → reservas/optimización | `test_finishes.py`, `179_finish_authority.test.sql` |
| Seleccionar caras → igual caras → deshacer → guardar y reabrir | `recorrido/navegador.json`, `selector-bicolor-*.png` |
| 3D → canales lineales por cara y ausencia de grano inventado | `finishMaterials3d.test.ts`, `recorrido/bicolor-3d.png` |
| Catálogo → carta y fuente consultables | `recorrido/catalogo-*.png` |
| Vacío, carga, error y reintento, sin permiso, acabado retirado | `recorrido/estados-publicacion.json`, `estado-*.png`, `carta-vacia.png` |
| Carta importada → editar muestra → diff → publicar → deshacer | `recorrido/carta-*.png`, `estados-publicacion.json` |
| Siete posiciones → precio → emitir → siete OT optimizadas | `recorrido/flujo-7-acabados.json` |
| Otra cotización emitida → portal interior/exterior y PDF | `recorrido/portal-fixture.json`, `portal-*.png`, `cotizacion-acabados.pdf` |
| Upgrade poblado → catálogos y datos históricos exactos | `scripts/check_finish_upgrade.py` |
| Cálculo, inspección, layout y corte → una autoridad y hash exactos | Siete goldens diagnósticos, dos regresiones HTTP y tres recorridos canvas reales |
| Portal → muestras selladas sin códigos internos de compra | `test_customer_finish_preserves_sealed_faces_without_internal_profile_bindings`, lectura pública en `verify-d05.mjs` |
| Carta sin blanco → todas sus combinaciones requieren compra completa | `test_chart_without_white_checks_every_declared_combination` |
| Delta → moneda y modo configurado coinciden con la cotización | Cuatro casos reales en `test_finish_pricing_modes.py`, más conversión ausente y margen de proyecto |

Editor y catálogo se recorren a 1440×900, 1280×800 y 1024×768, ambos temas.
El portal añade 390×844. Su prueba espera que la imagen realmente cambie antes
de capturar la cara exterior. Los cuatro folios del PDF se rasterizaron y
revisaron: nombres comerciales por cara, muestra interior, IVA/precios sellados
y condición DEMO. Los fallos de transporte se inyectan para ensayar estados;
publicación, permisos, persistencia, precio y documentos usan el stack real.

El barrido formal `ux:capture` tiene 24 comparaciones en
[`comparacion.json`](comparacion.json): editor, catálogo y portal en ambos temas
y cuatro anchos. No hay hallazgos nuevos, errores de consola/HTTP ni desbordes
nuevos. El editor conserva su desborde móvil anterior; no ocurre en escritorio
ni portal. La comparación por firma conserva los hallazgos heredados y elimina
el degradado del fondo de las miniaturas del portal. Los 80 PNG se optimizan sin
pérdida y se comprueba la identidad de sus píxeles.

El portal de referencia usa el frontend anterior (`ef0a4137`) y el mismo payload
sellado, servido por el backend D05, para comparar la presentación. Los enlaces
públicos permanecen en memoria; los reportes publicables sustituyen el token por
`fixture-vigente` antes de guardarse en `docs/`.

## Pase editorial: dos rondas

Primera ronda:

1. Se sustituyó el color libre por caras compatibles de la carta. La igualdad
   usa una combinación permitida, sin inventar otra al activar el control.
2. Se retiró el grano sintético del camino de carta y se asignaron materiales
   interior/exterior/canto. La muestra 2D y el 3D derivan del mismo RGB lineal.
3. Refuerzo, plazo y delta quedan junto a la elección. Restricciones y fuente
   se pliegan para conservar la lectura básica y explicar cualquier límite.

Segunda ronda:

1. Deshacer republica la evaluación correcta aun al volver al cache; Guardar
   espera el resultado pendiente. La regresión tiene prueba específica.
2. La ficha global ofrece Consultar sistema. Se retiró la opacidad acumulada
   del formulario readonly para leer fuentes y muestras en ambos temas.
3. La portada PDF usa nombres comerciales; el error de precio tiene causa en
   español, reintento y detalles plegados. Permisos nombran a quien puede actuar.

La revisión final encontró y corrigió dos desvíos: el inspector/layout omitían
la preparación del acabado al entrar por el cálculo diagnóstico, y el portal
transportaba bindings internos de perfiles. Todos los cálculos comparten ahora
la misma carta y hash; la proyección pública conserva las muestras y excluye
esos bindings sin modificar el snapshot. Las aserciones E2E siguen verificando
medidas y SKU exactos del catálogo v5, incluida su holgura declarada; no se
retiraron las comprobaciones de hash, rollback, permisos o tiempos de pintura.

La revisión del PR encontró tres fallos adicionales: readiness suponía blanco,
el delta suponía CLP y su fórmula suponía costo más margen. Readiness verifica
todas las combinaciones y cada identidad independiente de acero. El selector
comparte el cálculo de venta con Precios, en moneda y modo predeterminados de la
organización. Matriz/lista conservan delta cero si la venta no cambia; tarifa o
conversión ausente explica Sin dato. El margen objetivo exige el proyecto entero.
La diferencia firmada pertenece al motor y conserva precisión extensa. Siete
regresiones de integración y tres goldens monetarios cubren estos casos. Los
recorridos de navegador, cinco estados y publicación/deshacer volvieron a pasar.

El primer intento de CI posterior a la revisión aprobó pgTAP e integración,
pero la prueba recogió una consulta anterior al recargar el proyecto recién
duplicado y Chromium liberó su cuerpo. El helper de E2E escucha las peticiones
nuevas y lee su respuesta en cuanto llega, antes de terminar la acción. Conserva
las aserciones de duplicación, BOM, hashes y persistencia; no intercepta tráfico,
no agrega retries ni respuestas sintéticas. Se descartó el reenvío intermedio
porque podía retirar una ruta todavía activa. El gate se vuelve a ejecutar con
la captura final.

Momento de firma: lienzo y 3D bicolor real, revisión y documento por caras.
Idea que sube el techo: foliado oscuro explica refuerzo y plazo extra en el
selector, con delta calculado por motor y tarifa vigente.

| Rúbrica | Resultado | Evidencia del alcance D05 |
| --- | --- | --- |
| R1 | PASA | Precio Mono, mm y canales exactos; unidades y formatos comunes |
| R2 | PASA | Radios de token, muestras rectangulares y bordes técnicos |
| R3 | PASA | Una región de elección; reglas en divulgación progresiva |
| R4 | PASA | Naranja reservado para atención humana |
| R5 | PASA | Teal en el cromo; colores físicos pertenecen a las muestras |
| R6 | PASA | Nombres comerciales, vocabulario del taller y error en español |
| R7 | PASA | Dos caras compactas; catálogo organizado por muestras/reglas |
| R8 | PASA | Cinco estados con causa, reintento y responsable |
| R9 | PASA | Dibujo comercial sobre papel y vista declarada |
| R10 | PASA | Selección conserva contorno/tinte/manijas |
| R11 | PASA | Exterior conserva espejo y dirección relativa al observador |
| R12 | PASA | Controles etiquetados, foco común y deshacer comprobado |
| R13 | PASA | Sin movimiento ornamental ni espera artificial en producto |
| R14 | PASA | Guardar o publicar después de revisar, sin primarios en competencia |
| R15 | PASA | Reglas/fuentes y Sin dato ante tarifa/plazo desconocido |
| R16 | PASA | Sin degradado, blur, brillo ni morado en la superficie nueva |
| R17 | PASA | Matriz de anchos/temas; portal con 390 px sin desborde |
| R18 | PASA | Caras/igual/undo/guardar/reabrir, diff/publicar/deshacer reales |
| R19 | PASA | Bicolor visible y declarado en documento sellado |
| R20 | PASA | Restricción, plazo y delta ligados a la autoridad del motor |

La rúbrica evalúa la superficie de D05. Las capturas formales conservan los
hallazgos heredados del cromo para los encargos posteriores. El editor móvil
está incluido en el barrido aunque el contrato D05 exige 390 px solo en portal;
su rediseño pertenece a P04. El PDF conserva la paginación previa, que P09 debe
mejorar: la última ficha puede continuar entre páginas. D05 verifica su acabado
y no atribuye a esa ficha una mejora de paginación inexistente.

## Reproducción, decisiones y límites

Con el stack de testing-framedex y el entorno cargado solo en memoria:

```text
python scripts/verify_finish_flow.py
python scripts/verify_finish_flow.py --portal-only
node --experimental-strip-types frontend/scripts/verify-d05.mjs
node --experimental-strip-types frontend/scripts/verify-d05.mjs --states-only
```

Los tokens no entran a evidencia. `--states-only` reutiliza el estado del primer
recorrido y publica una serie aislada, que deshace sin tocar autoridades usadas.
El catálogo v5 no reescribe v1–v4. La verificación de upgrade conserva BOM/hash,
precio aplicado y revisión emitida de diez tipologías anteriores.

Reglas y prioridades se configuran con fuente en Catálogo; las decisiones se
registran en `docs/decisions/valores-por-defecto.md`. El fabricante debe aportar
carta física, restricciones y tarifas productivas según `ACTIVACION.md`.
DEMO no certifica color, fabricante ni plazo. No se activa un servicio externo.
P04/P09/P19 continúan editor/documento/3D y no se declaran terminados aquí.

Validación local final tras las correcciones de revisión: lint, typecheck, test
y build PASA; 626 pruebas del motor y dos
xfail históricos, 1 179 backend, 719 frontend y goldens exactos. Nueve pruebas
del harness protegen el gate; 27 regresiones focalizadas cubren acabados/HTTP y
tres recorridos canvas pasan con pintura inferior a 300 ms. PostgreSQL 16 y sus
ocho verificadores de upgrade poblado pasan, incluido D05. El Database Gate
inicial PASA sobre el proyecto aislado: 1 031 pgTAP en 73 archivos, 304 pruebas
de integración, 11 recorridos E2E y los ocho upgrades poblados en PostgreSQL 16.
La limpieza verifica ausencia de contenedores y volúmenes propios. Los cuatro
checks de CI se registran al cerrarse el PR. La ejecución final posterior a la
revisión está en curso y se registra por separado; la inicial no sustituye ese gate.

Una publicación sintética inicial anterior al arreglo del transporte conserva
su historial: la guarda impidió deshacer un etag obsoleto. Su serie sin artículos
ni capacidad de cotizar se retiró por la API vigente del encargado, sin forzar
deshacer ni modificar auditoría. La publicación final sí completó deshacer con
el transporte actual y mantiene la comprobación del catálogo retirado.

Hubo un [incidente de aislamiento del gate local](../../../operations/INCIDENTE-GATE-2026-10-06.md):
un reset alcanzó el stack local `dekopen` al iniciarse antes de terminar la
sincronización. El informe conserva el impacto y la contención; esa ejecución
no cuenta como aceptación. No se puede afirmar que sus datos previos sobrevivieron.
