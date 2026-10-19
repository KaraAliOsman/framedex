# ED2 · coherencia editorial de la ola 2

Base `fb7a661d`, rama `codex/ED2-pase-editorial`, revisión del 10-10-2026.
El pase reúne bow/acoplados, emisión/enlace, cobranza, corte/etiquetas, CNC,
compras/inventario y catálogo/ingesta, conservando las decisiones de ED1.
La [comparación por persona](https://github.com/KaraAliOsman/framedex/blob/2db4e13171884b93a989e68508a55f5590f9b34d/docs/redesign/captures/ed2/index.html) contiene las vistas
anteriores y posteriores; los recorridos registran decisiones reales.

## Dos rondas de mejoras

Primera ronda, cinco puntos débiles:

1. CNC comparte `formatMillimeters`: misma coma, agrupación, precisión y
   «Sin dato» en pieza y autoridad. Se eliminan ambos formateadores locales.
2. La importación de sección muestra el contorno que realmente se aplica,
   con sus centésimas, Plex Mono y coma. La caja del renderer permanece visual;
   la medida se obtiene de los mismos vértices decimales confirmados. Se prueba
   un origen negativo y una dimensión de 60,01 × 70,02 mm sin truncarla.
3. Compra confirmada, proveedor vencido y autoridad de catálogo usan
   `StatusBadge`, incluyendo texto e icono. Se borran las insignias CSS propias.
4. Fabricante, familia y material se leen como metadatos, sin chips que
   aparenten estados. Las capacidades forman una lista técnica con el mismo
   vocabulario/estado común; se quitan las tarjetas y puntos decorativos.
5. Catálogo y Compras usan tokens de color, control y espaciado. Se eliminan
   alternativas hex/rgba y variaciones de verde/ámbar heredadas. El formulario
   real de centro de trabajo mantiene la retícula y los controles compartidos.
   Los metadatos pequeños de las series usan la celda densa de 12 px, evitando
   que la herencia del cuerpo de oficina los reduzca bajo el mínimo de 11 px.

Segunda ronda, tres puntos débiles:

1. Descuentos de comparación y detalle usan el formateador decimal común,
   con coma, espacio y porcentaje. No convierten la fracción mediante float.
2. Las tablas móviles conservan encabezado al lado del valor. Cobranza,
   documentos, enlaces, cobertura, recepción, stock y retazos caben en 390 px.
   El filtro y orden de la tabla compartida siguen disponibles. La retícula
   de Inventario permite encoger el contenido sin ocultar columnas ni textos.
3. Inventario del operario usa densidad de taller. Se conservan permisos:
   consultar material no permite editarlo. La alerta orienta al dueño y el
   retorno de formatos a Producción usa un enlace táctil. El recorrido de
   emisión identifica módulos por su ordinal físico, conservando los UUID
   internos de sus destinos y toda la autoridad de la manilla.
   La superficie consume el tema elegido para que las tintas y el fondo
   correspondan; el checkbox de stock conserva un objetivo de 44 px.

No se agregan capacidades de dominio ni se cambian fórmulas, tarifas,
catálogos, políticas, documentos históricos o permisos. No cambió el contrato
OpenAPI. Las nuevas rutas oficiales de captura cubren emisión y corte.

## Recorridos y evidencia

| Persona           | Flujo y evidencia                                                                                                                                                                                                                         |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Estimador         | Hoy/búsqueda → doce posiciones, primera con tres módulos bow → cascada real → aplicar precio → checklist/políticas → PDF real → confirmar → emitir/enviar → portal 390 → seguimiento. [Registro](captures/ed2/recorridos/estimador.json). |
| Dueño             | Cobranza con pagos y documentos → nuevo PDF de proveedor → MiMo real → tres candidatos → fuente original y revisión; las filas dudosas quedan excluidas y no se publican. [Registro](captures/ed2/recorridos/dueno.json).                 |
| Jefe de compras   | Faltante de una nueva OT DEMO → precios declarados para el ensayo → propuesta revisada → OC/envío → recibir una barra → stock/REC y saldo pendiente → retazo físico/etiqueta RT. [Registro](captures/ed2/recorridos/compras.json).        |
| Taller y cortador | Cortes agrupados por teclado → pack PDF/etiquetas PDF → pieza CNC → comparación y confirmación obligatoria → estación privada 390. [Registro](captures/ed2/recorridos/taller.json).                                                       |

La cotización bow queda «Solo cotización»: la falta de medidas/autoridad para
fabricar permanece visible y no se sustituye por datos sintéticos silenciosos.
La firma explícita permite emitir el documento comercial sin liberar una OT.
Los recorridos de fabricación usan las OT DEMO ya selladas para ese fin.

El PDF se verifica en Chromium completo, que carga su visor. El Chromium
headless shell no habilita la confirmación porque no carga ese visor; ese
primer intento no acredita aceptación ni se fuerza el control desde el test.

## Revisión por superficie

La lectura conjunta protege F1/F4/F5/F6 en bow, F2/F11 en emisión, F6 en
cobranza/compras/catálogo y F2/F9 en corte/CNC. La elevación interior y la planta
se conservan. Ninguna decoración sustituye una operación del motor.

| Revisión                   | Bow  | Emisión | Cobranza | Corte | CNC  | Compras/stock | Catálogo |
| -------------------------- | ---- | ------- | -------- | ----- | ---- | ------------- | -------- |
| R1 · formato, unidad, Mono | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R2 · radios                | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R3 · bordes/jerarquía      | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R4 · naranja por persona   | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R5 · cromo teal            | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R6 · lenguaje de taller    | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R7 · densidad por tarea    | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R8 · estados/causas        | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R9 · papel/mesa            | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R10 · selección explícita  | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R11 · DIN/iconos           | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R12 · teclado/foco         | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R13 · movimiento acotado   | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R14 · acción por región    | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R15 · fuente/desconocidos  | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R16 · sin slop visual      | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R17 · anchos/legibilidad   | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R18 · efectos/componentes  | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R19 · firmas conservadas   | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |
| R20 · capacidad real       | PASA | PASA    | PASA     | PASA  | PASA | PASA          | PASA     |

R20 usa planta angular y venta del motor; PDF/confirmación real; calendario,
saldo/recibos y origen sellado; secuencia de barras/destino RT; intercambio
neutro/autoridad física; compra contra existencias; e ingesta con fuente y
revisión. Se conserva el límite industrial y la decisión humana.

## Verificación y límites

La matriz anterior tiene 224 vistas, 16 desbordes y 24 hallazgos de objetivos
táctiles (16 en Inventario, ocho en formatos). La matriz final tiene 224 vistas
en 14 rutas, cuatro tamaños y ambos temas: **cero hallazgos, cero desbordes,
cero errores HTTP y cero errores de consola**. El baseline baja de 69 claves/187
ocurrencias a 45/139; las infracciones reales previas eran 60/171.
El registro anterior conserva además un error del navegador
`ERR_NO_BUFFER_SPACE` en Hoy; la matriz final no lo reproduce. Los 490 PNG
se comprimen sin cambiar modo, dimensiones ni un solo píxel, según
[comparación](captures/ed2/comparacion.json).

La matriz intermedia encontró tintas oscuras sobre fondo claro en Inventario
del operario, su checkbox menor de 44 px y metadatos de Catálogo menores de
11 px. Se corrigieron el consumo del tema elegido, el objetivo táctil y el
token de texto denso; se recapturaron ambas rutas completas. Las otras doce
rutas conservan los resultados finales. No cambió ningún detector ni umbral.

Las pruebas completas pasan: **881 motor (+2 xfail), 1.476 backend y 968
frontend**, junto a lint, tipos, OpenAPI/orval reproducibles, goldens byte a
byte y build. Las correcciones posteriores solo de presentación pasan
lint, tipos, las 968 pruebas frontend y build. CI 4/4 pasa en el PR #145. SQL, RLS, permisos y OpenAPI no cambiaron; Database Gate corre
íntegro en CI. Las primeras corridas fallidas no acreditan aceptación.

Los [estados de bow](captures/ed2/estados/bow/informe.json),
[catálogo](captures/ed2/estados/catalogo/estados.json) y
[tablas](captures/ed2/estados/tablas/estados.json) conservan vacío, carga,
error/reintento, sin permiso y bloqueo. El
[ensayo de tema/tacto](captures/ed2/estados/tablas/tema-inventario.json)
protege ambos temas y el control de stock de 44 px.

Los fallos de servicio/carga de los ensayos de estados se inyectan solo en
la respuesta de red del navegador: no alteran el backend ni atribuyen fallos
al producto. Los permisos y bloqueos se recorren con roles/autoridad reales.
El registro de estados distingue esa evidencia de los recorridos de negocio.

No se conectan servicios externos en este pase. Flow/SII siguen en sandbox,
SMTP local usa Mailpit y la IA usa MiMo configurado. Activación se mantiene en
[ACTIVACION.md](../operations/ACTIVACION.md). La fuente del nuevo PDF es
sintética y conserva DEMO; la revisión no certifica datos de un fabricante.
Uw ausente, calibración de máquinas, validación industrial y superficies de
ola 3 permanecen fuera de esta aceptación.

ED2 PR https://github.com/KaraAliOsman/framedex/pull/145, CI 4/4 sobre dd3fe1ffce2c14ba1125442d8a137021d1ba32f2, corrida https://github.com/KaraAliOsman/framedex/actions/runs/38091279743, squash fa3731843dbfbd75d00024e95f4986a3616a8747, 2026-10-10.
Los cuatro checks requeridos pasan sobre el mismo head; el PR se integra con squash y el fixture persistente se conserva.
