# IA3 · aceptación del proveedor real

Referencia de código: `75bd60c70b7ad6c1943b5fd855d4672ae3a29f31`. Evaluación completa y gate DB: `041cb622836c745897c04e52a354d10bbf16a8b4`.
Transporte PDF final: `d660f72054c0777b542a6bb1ef5b65c2477b6310`. Después de la evaluación solo se consolidó el contenido PDF y se retiró la instrucción de repetir la prueba al guardar; el agente no cambió.
Fecha de verificación: 07-10-2026. CI/merge se registran después en ESTADO.md.

## Resultado funcional

El dueño con MFA configura cuatro capacidades, proveedor/modelo, tiempo, reintentos,
herramientas, tarifa y presupuesto. Ve credencial disponible, resultado y causa legible,
prueba E03 sobre una copia con el motor y abre costo/traza por trabajo. Cambiar el transporte de una ruta
invalida solo su prueba anterior; presupuesto, tarifas y rutas idénticas la conservan; una respuesta tardía no declara conectada otra configuración.
Los demás miembros solo consultan sus propias llamadas. La clave permanece en servidor.

MiMo usa herramientas nativas del registro IA2 y resultados emparejados. Solo un rechazo
explícito de herramientas habilita JSON estricto con esquema. Hasta dos reintentos
transitorios comparten clave y plazo. DEBUG no activa el modo de prueba. El presupuesto
serializa reservas concurrentes, incluye débitos históricos sin duplicar los nuevos y
avisa al dueño. Tokens y costo sin medición/tarifa quedan «Sin dato».

Los intercambios físicos y los eventos sobreviven al rollback de una propuesta; auditoría
y débito conservan su transacción atómica. El lock financiero usa `FOR NO KEY UPDATE`
también en el trigger para permitir la FK del registro independiente sin deadlock.
El polling de trabajos publica fases reales con commit independiente y guarda de lease.

## Capacidades y evaluación real

[Metadatos de los sondeos](IA3-CAPACIDADES.json): herramientas nativas sí, imagen sí,
PDF directo HTTP 400. El transporte implementado pasa seis oráculos: herramientas,
resultado emparejado/final, imagen, PDF escaneado, PDF literal y PDF mixto.
El primer sondeo literal con varios bloques de texto falló y se conserva como
historia; la representación corregida reúne texto y referencias en un solo bloque. Todos usan MiMo real,
sin fallback y con fuente ejecutada sin cambios. D01 mantiene extracción literal,
límites de páginas/píxeles/tamaño y revisión humana; visión no acredita autoridad HIGH.

[Corrida final completa](evals/2026-10-07-ia3-mimo-review.json) y
[comparativa por caso](evals/2026-10-07-ia3-comparativa-review.md): **22/26**;
editor **13/13**, proyecto **6/8**,
planta **1/3**, general **2/2**.
Editor/proyecto: **19/21**. Dominio, auditoría y billetera sin cambios;
delta físico explícito: 53 intercambios y 104 eventos.
No se mezclaron casos de corridas ni se modificaron oráculos/límites.

IA2 histórica permanece 21/26; las corridas completas IA3 anteriores 19/26 y
22/26 se conservan. La nueva corrida se ejecutó tras corregir referencias y
progreso configurable, sin alterar oráculos ni límites. J04/J08/F03 carecen de
contexto suficiente; F02 no entrega el resultado de negocio exacto. La
representación PDF posterior tiene seis oráculos propios y no modifica las
llamadas del agente. Un transporte correcto no equivale a una tarea de negocio
resuelta. El fixture es DEMO y no autoriza fabricación.

## Verificación automática

`make lint`, `make typecheck`, `make test` y `make build`: **PASA** sobre el código final.
Motor 744 (+2 xfail), backend 1.241, frontend 817. Ochenta y dos pruebas
focalizadas incluyen PDF literal/mixto, reintentos, progreso hasta doce rondas
y procedencia. `make test-db`: **PASA**, 78 archivos byte a byte,
1.137 pgTAP, 395 integraciones, 11 E2E y ocho upgrades poblados PostgreSQL 16.
Este gate ejecutó `041cb622`; después solo cambió PDF y un mensaje,
sin cambios SQL/permisos. CI verifica el head del PR.
[Metadatos y hashes de logs](IA3-VERIFICACION.json).

Quince integraciones IA3 verifican presupuesto, tarifas, invalidez de cambios
reales, carrera de prueba, caché por ejecución, permisos/MFA/RLS, idempotencia,
rollback y progreso visible desde otra conexión. La caché original ya era
local a cada ejecución y las consultas siguen verificando tenant; además
se impide promover referencias desde respuestas cacheadas o fallidas.
El golden de costo Decimal y todos los golden anteriores conservan sus bytes.
OpenAPI/orval reproducibles. El escaneo contra secretos pasa sin mostrar valores.

Dos intentos de Database Gate pasaron SQL/integraciones pero fallaron por el puerto
8000 publicado por el contenedor propio, aunque Django estaba detenido. Esos intentos
no se cuentan como aceptación. Se detuvo ese contenedor y se comprobó el bind libre
antes del gate completo. El stack ajeno nunca se modificó.

El primer CI del commit de evidencia `e5350f76` pasó 1.137 pgTAP y 395
integraciones, pero falló al esperar el título del catálogo: el test iniciaba
esa espera al llegar herrajes y sistemas seguía cargando. La carrera se
reprodujo localmente. `catalog-kit.spec.ts` ahora espera las cuatro respuestas
que necesita la pantalla, verifica HTTP 200 y conserva las aserciones,
timeouts y ausencia de reintentos originales. El recorrido real focalizado
pasa; no se modificaron el producto ni los checks. CI verifica otra vez el
head corregido antes de integrar.

## Navegador y estados

[Recorrido y aserciones](../redesign/captures/proveedor-real/recorrido/navegador.json)
y [carga, permiso y recuperación](../redesign/captures/proveedor-real/recorrido/navegador-estados.json).

| Flujo | Resultado y evidencia |
| --- | --- |
| Sin credencial | PASA · Qwen sin variable, guardado por dueño; instrucciones sin error crudo; ruta real restaurada. |
| Error real | PASA · modelo MiMo inválido, rechazo real sanitizado; restauración posterior. |
| Bloqueado | PASA · presupuesto cero impide la llamada, explica quién lo cambia; restaurado. |
| Conexión | PASA · E03 real, propuesta/motor exactos; estado verde y sin mutar proyectos. |
| Presupuesto editado | PASA · conserva Conectado y la misma fecha de prueba, sin otra llamada pagada. |
| Costo/traza | PASA · historial consultable, herramientas del motor, costo Sin dato sin tarifa. |
| Vacío | PASA · filtro sin llamadas, causa y acción de recuperación. |
| Carga | PASA · respuesta demorada solo para observar esqueleto/cota, en claro 1440 y oscuro 1024. |
| Sin permiso | PASA · token real ESTIMATOR devuelve 403 en Ajustes; UI lo explica y no ofrece edición. |
| Error de red | PASA · abort controlado, causa/reintento; recuperación sin recargar en ambos temas. |
| Agente real | PASA · trabajo terminado, fases observadas CONSULTING_PROJECT, costo/traza accesibles. |

Las fases CALCULATING_ENGINE y PREPARING_PROPOSAL usan el mecanismo de progreso con
prueba de commit visible desde otra conexión. El último recorrido corto de navegador
solo capturó CONSULTING_PROJECT; no se le atribuyen las otras dos fases.

[Comparación formal](../redesign/captures/proveedor-real/comparacion.json): 32 registros
de `ux:capture` (Ajustes OWNER, Trabajos OWNER/ESTIMATOR, Asistente ESTIMATOR),
1440×900, 1280×800, 1024×768 y 390×844, claro/oscuro. **Cero hallazgos nuevos**,
sin errores HTTP/consola ni desbordes nuevos. Ajustes/Trabajos no tienen hallazgos.
El asistente conserva 14 hallazgos heredados por captura (112 acumulados en las ocho),
iguales antes/después; se documentan para P17 y no se atribuyen a la superficie nueva.

Capturas clave:
[conexión](../redesign/captures/proveedor-real/recorrido/conexion-verificada-light-1440.png),
[sin credencial](../redesign/captures/proveedor-real/recorrido/sin-credencial-light-1440.png),
[presupuesto](../redesign/captures/proveedor-real/recorrido/presupuesto-bloqueado-light-1440.png),
[edición conserva conexión](../redesign/captures/proveedor-real/recorrido/presupuesto-conserva-conexion-light-1440.png),
[traza](../redesign/captures/proveedor-real/recorrido/agente-costo-traza-light-1440.png),
[sin permiso](../redesign/captures/proveedor-real/recorrido/ajustes-sin-permiso-dark-1024.png).
PNG optimizados sin pérdidas e inspeccionados visualmente.

## Dos rondas editoriales

Primera ronda: (1) estado Conectado ligado al modelo efectivo, firma/revisión y resultado
del oráculo; (2) traza y costo medido separados de la aceptación del dominio; (3) fases
publicadas fuera del rollback y logs de metadatos sin contenido. Se retiró el falso
Conectado por mera respuesta HTTP y el fallback ante cualquier 400.

Segunda ronda: (1) el presupuesto incluye historia sin doble conteo y explica la falta
de medición; (2) fechas, créditos y tarifas en Mono, enlace teal y copy de billetera
que distingue intercambio auditado de aplicar; (3) presentación histórica/localización
de superficies sin alterar auditoría, URL, SKU ni cifras. Se eliminó «dashboard» de
prosa y de métricas nuevas; no se borraron conversaciones para limpiar las capturas.

La revisión añadió regresiones para PDF literal/mixto, verificación por
capacidad, progreso monótono y referencias obtenidas solo de consultas exitosas.
Se retiró la instrucción de repetir una prueba al guardar; se espera el estado
final de la ruta antes de capturar, sin relajar contraste ni detectores.

## Rúbrica R1–R20

Alcance: controles, Ajustes de IA, costo/traza, modo de prueba y fases agregadas por IA3.
El dock/Orb y cromo históricos mantienen su baseline explícito para P17; esta tabla
no certifica un rediseño global del asistente ni las pantallas futuras de la cola.

| Revisión | Veredicto | Evidencia |
| --- | --- | --- |
| R1 | PASA | Tarifas, fechas, créditos, tokens y costo con formatos centrales y Mono tabular. |
| R2 | PASA | Radios de tokens ≤4 px; los controles nuevos no agregan ingletes decorativos. |
| R3 | PASA | Filas y reglas de borde; opciones avanzadas plegadas, sin capas simultáneas. |
| R4 | PASA | Naranja reservado al aviso al dueño/marca; CTA teal. |
| R5 | PASA | Teal y grafito de los tokens en ambos temas. |
| R6 | PASA | Capacidades y herramientas en español; errores sanitizados y Modo de prueba. |
| R7 | PASA | Modelos y estado visibles; tiempo/herramientas/tarifa y consumo por persona plegados. |
| R8 | PASA | Los cinco estados se recorren con causas, permisos reales y reintento. |
| R9 | PASA | Sin cambios al lienzo/papel; prueba de diseño conserva la copia y autoridad del motor. |
| R10 | PASA | Filtros y detalles usan bordes/foco; no aparece elevación al pasar el puntero. |
| R11 | PASA | Sin iconos nuevos ajenos a la gramática ni cambios a símbolos de apertura. |
| R12 | PASA | Controles etiquetados, foco tokenizado y teclado de formularios nativos sin validación del navegador. |
| R13 | PASA | Esqueleto/cota centrales, sin shimmer; movimiento y reducción heredados de primitivas. |
| R14 | PASA | Probar conexión como principal; guardar y navegación secundarios; un reintento por estado. |
| R15 | PASA | Costo Decimal con tarifa sellada, traza visible; Sin dato para medición/tarifa ausentes. |
| R16 | PASA | Cero gradiente/blur/brillo/morado en estilos agregados; detectores y lint. |
| R17 | PASA | Matriz claro/oscuro en los tres anchos exigidos, más 390; sin desborde nuevo. |
| R18 | PASA | Guardar/probar/filtros/paginación/enlaces actúan sobre API; sin componentes paralelos. |
| R19 | PASA | Cargador de cota y fases reales alimentan el polling que consume Orb. |
| R20 | PASA | Por trabajo: costo, tiempo y herramientas; E03 y propuestas usan el motor real. |

## Decisiones, activación y límites

[Valores por defecto](../decisions/valores-por-defecto.md#ia3--proveedor-presupuesto-y-fuentes-2026-10-07):
MiMo inicial, cuatro overrides por tenant, 60 s, hasta dos reintentos, herramientas
automáticas, presupuesto sin límite adicional hasta que el dueño lo declare y tarifa
desconocida hasta configurarla. No se adopta un precio público como autoridad.
[Proveedor](../operations/AI_PROVIDERS.md) y [activación](../operations/ACTIVACION.md).
IA se verificó real; Flow/SII/correo/despliegue siguen sus adaptadores y encargos de la cola.

No hecho/riesgos: no se garantiza 26/26 ni respuesta determinista de MiMo; se conservan
todos los fallos exactos de las corridas completas. El escaneo visual no convierte una fuente en autoridad
certificada. Una llamada de desenlace ambiguo retiene reserva prudente. La tarifa
monetaria no se inventa y el historial incompleto conserva Sin dato. P17 continúa el
rediseño completo del dock/Orb y sus hallazgos históricos.
