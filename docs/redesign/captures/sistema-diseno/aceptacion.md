# P01 · aceptación del material de interfaz

Verificado el 05-10-2026 sobre `codex/P01-sistema-diseno`, desde la base `7e98f71d02f31949def1383766eb2b6ee53e156c`. La aceptación cubre las primitivas, los formatos, la validación y la migración de estilos. Las pantallas pendientes de la cola conservan sus defectos heredados; esta tabla no las acredita como rediseñadas.

## Flujos y capturas

- Manual: sesión Estimador real → `/dev/ui` → obra/BOM de la organización → entrada Decimal → validación en español → diálogo → Escape y retorno del foco → Ctrl+K → ficha → Bien/Mal. Matriz de 22 combinaciones: 1440×900, 1280×800 y 1024×768 en ambos temas y las tres densidades, más 390×844 en taller/documento. Axe se ejecuta en la superficie, con errores y con diálogo; no admite `serious` ni `critical`.
- Catálogo: sesión Jefe de taller → crear serie → enviar campos incompletos → errores en español y foco en el primer campo. Cobranza: sesión Estimador → vivienda del fixture → Registrar pago → monto incompleto/decimal en CLP → error junto al campo y foco. Ambos temas; se verifica `noValidate` y **cero escrituras** de API para datos inválidos.
- Regresión: **352 capturas por lado**, mismas rutas, roles, temas y cuatro viewports. [Comparación](comparacion.json): ningún detector aumenta su número de ocurrencias en una combinación y no aparece un desborde nuevo. Las capturas tienen compresión PNG sin pérdida, comprobada por igualdad de píxeles.
- Inspección visual: manual claro/oscuro a 1024, taller a 390, proyecto a 1440 y los errores reales de Catálogo/Cobranza. Las capturas se enlazan debajo y los informes conservan sus límites.
- Revisión de entradas: un identificador fiscal extranjero se conserva sin imponerle RUT; las entradas monetarias libres rechazan puntos decimales ambiguos; una edición numérica inválida borra el valor del consumidor y mantiene el borrador/error visibles. El manual también verifica precisión inválida, refoco y axe. Los tres E2E del lienzo pasaron con medidas agrupadas y foco delineado; sus aserciones exactas se actualizaron al contrato vigente, preservando cálculos, rollback, snapping y límite de pintura de 300 ms.

| Evidencia | Enlace |
|---|---|
| Manual claro, oficina, 1440 | [PNG](manual/light-office-1440.png) |
| Manual oscuro, oficina, 1024 | [PNG](manual/dark-office-1024.png) |
| Manual oscuro, taller, 390 | [PNG](manual/dark-workshop-390.png) |
| Bien / Mal | [PNG](manual/light-office-1440-bien-mal.png) |
| Cobranza, error visible | [PNG](validacion/cobranza-light-1440.png) |
| Catálogo, error en español | [PNG](validacion/catalogo-dark-1440.png) |
| Proyecto antes | [PNG](antes/proyecto-detalle__ESTIMATOR__light__1440x900.png) |
| Proyecto después | [PNG](despues/proyecto-detalle__ESTIMATOR__light__1440x900.png) |
| Matriz del manual / validación | [Resultados](manual/results.json) · [Resultados](validacion/results.json) |
| Matriz completa | [Antes](antes/report.json) · [Después](despues/report.json) |
| Limpieza CSS | [Reglas y causas](css-cleanup.json) · [Métrica reproducible](css-metrics.json) |

## Reducción de estilos

Los tres archivos solicitados contenían **5.357 líneas**. Sus módulos migrados, **incluyendo los entrypoints de imports**, contienen **3.750**: reducción aproximada del **30,00 %**. Se retiraron reglas sin coincidencia en navegador ni referencia alcanzable, animaciones decorativas, controles reemplazados y los exports de Layout sin consumidores. Se agruparon declaraciones idénticas y se eliminaron defaults de botón ya provistos por la base.

El costo completo también se informa: los estilos de las primitivas nuevas agregan **792 líneas**. El grafo completo de ese alcance queda en **4.542 líneas**, reducción neta del **15,21 %** al incluirlas. No se atribuye a borrar CSS lo que solo cambió de archivo ni se presenta el 30 % como reducción neta de todo el material nuevo. Reproducción: `node --experimental-strip-types frontend/scripts/css-metrics.ts`.

| Detector | Antes | Después |
|---|---:|---:|
| Radio > 4 px | 11.860 | 3.656 |
| Fuente < 11 px | 2.820 | 1.728 |
| Contraste insuficiente | 812 | 338 |
| Sombra fuera de escala | 200 | 112 |
| Degradado | 16 | 0 |
| Objetivo táctil < 44 px | 480 | 476 |
| Enum crudo | 192 | 192 |
| Interactivo sin efecto detectado | 40 | 40 |
| Varios primarios por región | 8 | 8 |

Estos son totales de ocurrencias de la matriz heredada, no defectos únicos. Los conteos que permanecen se conservan para los encargos de superficie y no se convierten en excepciones nuevas.

## Pase editorial

Ronda 1: se distinguió el payload Decimal del texto visible; se reemplazó el UUID del sistema por su código; se corrigió el inspector para mantener su riel y plegarse en móvil. Ronda 2: se ajustaron popovers/menús al viewport y el retorno de foco; se separó la validación del consentimiento y la precisión monetaria; se llevó el error de Cobranza junto al input para que no quedara fuera del panel visible.

| Revisión | Resultado | Evidencia del alcance P01 |
|---|---|---|
| R1 · Formatos y Mono | PASA | Formateadores únicos, negativos/empates/2⁵³, unidad y fracción explícita; capturas del manual. |
| R2 · Radios e inglete | PASA | Primitivas r-1/r-2; un inglete en la hoja; contrajemplo histórico aislado DEV-only. |
| R3 · Jerarquía y capas | PASA | Bordes técnicos, E2/E3 solo en superposiciones; coordinador de capas operativas. |
| R4 · Naranja | PASA | Marca/manipulación/requiere persona; ningún CTA naranja del material. |
| R5 · Teal | PASA | Roles funcionales compartidos; primario teal y semánticos declarados. |
| R6 · Voz | PASA | Mapa exhaustivo de enums y validación común en español; UUID/huella en Detalles técnicos. |
| R7 · Densidad | PASA | Inspector de ocho datos en el manual a 768 px; controles 28/32/44 según densidad. |
| R8 · Estados | PASA | Tabla y componentes con vacío, carga, error, sin permiso y bloqueo, causa/acción. |
| R9 · Papel sobre mesa | PASA | SheetSurface y roles sheet/app distintos en ambos temas. |
| R10 · Selección | PASA | Contorno y tinte en controles, tabla y registro; sin elevación al seleccionar. |
| R11 · Aperturas | PASA | SVG monolínea; vértice hacia manilla, exterior reflejado/discontinuo y corredera paralela. |
| R12 · Foco/teclado | PASA | Formulario, opciones, diálogo/Escape, menú y paleta; axe en superficie/error/diálogo. |
| R13 · Movimiento | PASA | Escala ≤ 280 ms; cota horizontal; reducción de movimiento y guardas. |
| R14 · Primario | PASA | Regiones explícitas y advertencia de desarrollo para primarios competidores. |
| R15 · Procedencia | PASA | Obra/BOM de API; ausencia de traza/peso/U con causa, sin cero inventado. |
| R16 · Sin efectos SaaS | PASA | Material sin gradientes/blur/brillo; la lámina Mal es la excepción solicitada, ausente de producción. |
| R17 · Anchos | PASA | Matriz del manual sin overflow de página; capas limitadas por viewport. |
| R18 · Efectos reales | PASA | Acciones del manual ejercitadas; Layout muerto eliminado; imports DEV omitidos del build. |
| R19 · Firma | PASA | Inglete, cota de carga, procedencia honesta y familia de aperturas operativas. |
| R20 · Capacidad respaldada | PASA | El manual conecta selección → posición/BOM → ficha con los resultados del motor; formatos, tabla y controles preservan el valor exacto. No añade una fórmula de UI. |

## Decisiones, integraciones y riesgos

Las decisiones sobre redondeo, texto atenuado accesible y contradicción DIN están en [Sistema v2](../../../design/SISTEMA-V2.md) y [Valores por defecto](../../../decisions/valores-por-defecto.md). La plantilla de PR incorpora la misma rúbrica. P01 no agrega adaptadores externos; las activaciones siguen registradas en [ACTIVACION](../../../operations/ACTIVACION.md).

No se añadió una traza ficticia: la respuesta actual de posición entrega huella, pero no fórmula/entradas/versión completas. `TraceButton` acepta ese contrato y expone la ausencia. Tampoco se fabricaron revisiones ni aprobación de catálogo para llenar capturas: los cinco enlaces de portal provisionales ejercitan errores, **no cinco cotizaciones emitidas**. Esta limitación permanece explícita para los encargos de cotización/portal. Los reportes conservan los errores HTTP/consola y desbordes heredados; la matriz es evidencia de regresión, no aceptación de toda la aplicación.

Los cuatro gates locales pasaron: lint (incluye OpenAPI/orval y guardas), typecheck, test y build; 472 tests del motor con dos fallos esperados, 1.058 del backend y 697 del frontend. Los cuatro checks GitHub se registran en el PR antes del merge. No se modificaron API, migraciones ni fórmulas del motor.

Integrado mediante [PR #117](https://github.com/KaraAliOsman/framedex/pull/117), squash `023b8ba303b680ca50b6e10119ce4ee4514c9c38` en `integracion/v1`. Lint & Typecheck, Test Suite, Frontend Build y Database Gate: PASA sobre el head final `1f6f225c99c8faebec6f42a4a37f9bcf2514d5cd`.
