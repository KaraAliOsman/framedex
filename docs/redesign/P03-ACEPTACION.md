# P03 · navegación por flujo y trabajo de Hoy

Rama `codex/P03-shell-hoy`, base `096621c9`. Verificación local 09-10-2026.
Evidencia en [capturas](captures/shell-hoy/).

Hoy muestra compromisos con verbo, entidad, causa y destino. El motor ordena
vencidos, bloqueos, trabajo del día y seguimiento, sin comparar monedas.
El dueño revisa y decide precios dentro de Hoy; el solicitante reconoce la
decisión explícitamente. Abrir la campana consulta la misma cola y no escribe
recibos ni resuelve acciones.

## Flujos verificados

| Entrada, acción y siguiente paso | Resultado |
| --- | --- |
| Dueño: solicitud → revisar en Hoy → motivo + confirmación → rechazar/aprobar | PASA: decisión real persistida; cambia la cola y avisa al solicitante. |
| Estimador: Leer decisión → Marcar como leída | PASA: recibo idempotente; desaparece de Hoy y campana; historial intacto. |
| Campana abierta/cerrada | PASA: ninguna escritura ni cambio del estado de lectura. |
| Revisión con enlaces de documento y compartido | PASA: conserva vistas de todos sus enlaces; una fila sin vistas no oculta otro enlace leído. |
| Cotizaciones → seguimiento, fase y moneda → proyecto | PASA: filtros del backend sobre autoridad sellada; paginación de 50, sin sumar monedas. |
| Dueño: saldo → Abrir cobranza | PASA: total sellado menos pagos vigentes del motor; sección de pagos. Sin fecha no se llama vencido. |
| Taller: plan pendiente y OT terminada → entidad exacta | PASA: reservas de cada OT; no reabre faltantes históricos tras completar estaciones. |
| Instalador: entrega agendada hoy → OT exacta | PASA: agenda real; sin módulo vacío de despacho. |
| Operario entra por `/` y abre Hoy explícitamente | PASA: entrada automática a producción; `/dashboard` conserva su cola y CTA al taller. |
| Ctrl K: P-000012, OC-000003, RT-000045, OT-P-000005-REV-A-03 y Cliente Prat | PASA: búsqueda y clic hasta ruta/entidad correctas; retazo enfocado. |
| Ctrl K: cotización P-000005 | PASA: revisión vigente en lista transversal filtrada por proyecto. |
| Ayuda `?`, Tab/Shift Tab, Escape y drawer | PASA: foco contenido y devuelto; comandos del registro existente. |
| Cambio de organización durante búsqueda | Regresión de cancelación/resultado tardío en componente y recorrido real en `recorrido/informe.json`. |
| Levantamiento pendiente y conjunto no fabricable | PASA: bloqueo del dominio/motor; destino a la posición; no modifica diseño ni BOM. |
| Inventario → stock, filtros, retazo y etiqueta | PASA: ruta propia; reutiliza movimientos/retazos, sin identidades técnicas visibles. |
| Vacío, carga, error/reintento y sin permiso | PASA: transporte controlado rotulado; sin permiso mediante rol real. Bloqueo del fixture real. |

La matriz real conserva 40 capturas de Hoy (cinco roles × cuatro tamaños ×
dos temas) y 16 de inventario/cotizaciones. Tamaños: 1440×900, 1280×800,
1024×768 y 390×844. Cero hallazgos, desbordes o axe serious/critical:
[informe](captures/shell-hoy/despues/informe.json). El recorrido comprueba
además ocho anchos entre 390 y 1920. El runner oficial se conserva en
`captures/shell-hoy/oficial/`; no se cambian detectores.

Los estados de carga/error/vacío interceptan solo la lectura HTTP para hacer
determinista su inspección. Decisiones, vistas de enlace, órdenes, compras,
recepciones y retazos usan APIs y el motor reales.

## Reproducción y límites del fixture

`frontend/scripts/verify-p03.mjs` conserva el recorrido y `--matrix` las 56
comparaciones. Selecciona `DEKOPEN_FIXTURE_ORG_ID` del fixture local cuyo nombre
contiene «P03 DEMO». `DEKOPEN_P03_DECISION_PROJECT` señala un borrador DEMO con
autoridad de precio para probar rechazo/aprobación; `DEKOPEN_P03_OUTPUT` el
destino de evidencia. No admite un Supabase remoto. Sesiones y MFA permanecen
en memoria; elimina su factor al cerrar.

«Hoy · aceptación P03 DEMO» contiene tres posiciones medidas y confirmadas
antes de emitir P-000005; OT03 completó plan, estaciones, calidad y embalaje,
con entrega agendada hoy. OT01/02 conservan trabajo pendiente. Seis compras
se confirmaron, enviaron y recibieron por API; 45 retazos se registraron con
autoridad y medidas de ensayo. P-000012 tiene levantamiento pendiente. Prat
conserva solicitudes, aprobación, rechazo y una revisión compartida por vencer
con lectura real. Son datos sintéticos DEMO, sin certificación de fabricante.

Durante la preparación inicial en la organización anterior se emitió una
revisión sin confirmar el levantamiento. Liberar al taller rechazó correctamente
`production_measurements_unconfirmed`. Esa emisión se conserva intacta;
la aceptación se hizo en una organización aislada, sin forzar producción
ni borrar evidencia.

## Pase editorial

Primera ronda: se quitaron tarjetas sin decisión y navegación por módulos;
se unificó Hoy/campana para evitar criterios contradictorios; se añadieron
destinos de entidad y resolución de precios inline con confirmación humana.

Segunda ronda: se corrigió el UUID de especificación de stock y el contraste
del buscador oscuro; se corrigió foco de paleta/drawer; se reparó pérdida de
vistas entre enlaces y atribución de faltantes generales a OTs terminadas.
El test de tokens detectó tres bordes con variable inexistente: usan el token
canónico. No se debilitaron guardas ni permisos.

| Rúbrica | Resultado | Evidencia del alcance |
| --- | --- | --- |
| R1 · Formato, unidad y Mono | PASA | Money/DateOnly/Qty; medidas declaradas exactas; stock. |
| R2 · Radios/inglete | PASA | Tokens de primitivas; detectores en 56 vistas. |
| R3 · Jerarquía/superficie flotante | PASA | Cola con filetes; exclusión de menús, paleta y ayuda. |
| R4 · Naranja | PASA | Solo intervención/bloqueo; ningún CTA naranja. |
| R5 · Teal | PASA | Navegación, filtros y foco con tokens comunes. |
| R6 · Voz/vocabulario | PASA | Verbos de negocio; estados traducidos; sin IDs visibles. |
| R7 · Densidad | PASA | Filas y controles office/workshop; no hay inspector nuevo. |
| R8 · Cinco estados | PASA | Recorrido HTTP rotulado y permiso/bloqueo reales. |
| R9 · Papel/mesa | PASA | Índices en superficie existente; editor/documentos conservados. |
| R10 · Selección | PASA | Contorno/tinte de navegación y filtros; sin nueva selección geométrica. |
| R11 · Íconos/aperturas | PASA | Monolínea 1,5 px; no redibuja elevaciones. |
| R12 · Foco/teclado | PASA | Tab/Shift Tab, `?`, Ctrl K y Escape; regresiones de cancelación. |
| R13 · Movimiento | PASA | Drawer en un eje, tokens existentes y reduce-motion. |
| R14 · Acción por región | PASA | Un verbo por fila; decisión humana localizada. |
| R15 · Fuente/desconocidos | PASA | Saldo/pipeline del motor, revisión y ledger; Sin dato explícito. |
| R16 · Sin degradado/blur/brillo | PASA | Guardas y presentación calculada. |
| R17 · Anchos | PASA | 390–1920; matriz de cuatro tamaños sin overflow. |
| R18 · Sin código paralelo | PASA | Elimina `attention.ts` y panel anterior; rutas preservadas. |
| R19 · Firma | PASA | F3 cargador de cota; F8 Orb de trabajos reales conservado. |
| R20 · Motor | PASA | Consecuencia determinista, saldo exacto y precio resuelto en Hoy. |

## Validación

`make lint`, `make typecheck`, `make test`, `make build`: PASA. Motor: 829
pruebas + 2 xfail y golden byte check. Backend unitario: 1.364. Frontend: 900.
`make test-db`: PASA en el proyecto local aislado `framedex-cola-native`:
83 archivos / 1.205 pgTAP, 439 integraciones, 17 E2E y upgrades poblados PG16.
El E2E conserva autenticación, navegación, recarga y autoridad emitida;
los selectores usan Inicio y las migas finales. [CI 37919211491](https://github.com/KaraAliOsman/framedex/actions/runs/37919211491): cuatro checks PASA sobre `4eb66fbd72c5b2a4ef13c13b6397982a29eb823e`.
[PR #134](https://github.com/KaraAliOsman/framedex/pull/134) integrado con squash `5b06ceb12457b297a8748580453695714469c6a0` en `integracion/v1`.

La corrida CI `37915677274` detectó una espera insuficiente en el E2E de
simulación del editor. La reproducción local midió vidrio/ancho/propuesta
en 7,4–7,9 s: la respuesta HTTP 200 y `valid=true` llegaba después de los
5 s de la aserción del botón. El recorrido focalizado pasa en 43,5 s al
esperar la transacción concreta. Ahora comprueba también las respuestas
del motor y la cota final; conserva Guardar, aplicar, deshacer y rechazo de
la respuesta tardía. No cambia timeouts globales, retries ni comportamiento
del producto. La corrida correctiva `37919211491` pasa los cuatro checks sobre `4eb66fbd72c5b2a4ef13c13b6397982a29eb823e`.
La suite completa del editor pasa 6/6 en 2,8 min; la espera del precio
indicativo verifica también el producto y la cantidad de su respuesta real.

## Decisiones, integraciones y riesgos

Decisiones de navegación, orden y privacidad en
[valores por defecto](../decisions/valores-por-defecto.md). No agrega credenciales
ni integración externa. Conexiones de producción en
[ACTIVACION](../operations/ACTIVACION.md).

Instalación usa agenda de entregas y estado de OT existentes, no inventa
otra agenda. Estación de operario y detalle de producción continúan en P12;
compras, inventario y retazos conservan sus controles para P15. No se afirma
aceptación editorial de esas pantallas internas. Pipeline describe venta
emitida, nunca ingreso contable. No se comparan CLP/USD/UF ni se deducen
vencimientos de texto libre.
