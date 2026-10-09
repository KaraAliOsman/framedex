# P12 · producción por estación

Base `62ebcbe9`, rama `codex/P12-produccion-estaciones`. Verificación local
09-10-2026; evidencia en [capturas](captures/produccion-estaciones/).

El jefe abre un tablero por estación con la primera tarea de cada OT,
compromiso declarado y motivos de bloqueo. El detalle sustituye el muro de
pasos por un stepper y nueve pestañas. El operario abre su cola privada,
escanea una pieza y trabaja con su medida, destino y siguiente paso.

## Flujos y persistencia

| Recorrido | Resultado |
| --- | --- |
| Operario 1024 oscuro: QR real → Corte → Iniciar → evidencia de operaciones → Completar | PASA: código y medidas del plan; Corte terminado por API; estación explícita conservada. |
| Elegir Soldadura → Bloquear con motivo | PASA: solo siguiente paso; motivo del equipo registrado y OT en espera. |
| Jefe: tablero → Hoy → desbloquear | PASA: misma OT y motivo en ambas superficies; Actualizar estación recarga el estado de la misma OT. |
| Soldadura → Limpieza → Vidriado → Calidad | PASA: ruta real y gates de material/orden, sin alterar pasos por SQL. |
| Operario: medición falla sin bloquear → falla con bloqueo elegido | PASA: primer registro conserva estado; segundo bloquea y avisa. |
| Jefe: elegir pieza → motivo → confirmar rechazo y remake → repetir operación | PASA: nueva OT conserva `P01-U01-I01`; mismo operation key devuelve la misma OT. |
| Vacío / carga / error + reintento / sin permiso / bloqueado | PASA: [cinco estados](captures/produccion-estaciones/estados/informe.json). Carga/error/403 usan transporte controlado; vacío y bloqueo son reales. |
| Operario: lectura privada y operaciones comerciales prohibidas | PASA: sin dirección ni cliente; preparar producción y rechazo con remake devuelven 403 reales. |
| Lista con 2.000 piezas | PASA: menos de 100 filas DOM, búsqueda y agrupación en la tabla virtualizada. |
| Un plan dentro de revisión grande | PASA: limita índices a posiciones usadas; mismas direcciones, bytes del plan y fingerprint; fallback histórico intacto. |

El [recorrido](captures/produccion-estaciones/recorrido/informe.json) conserva
las capturas del bloqueo y Hoy. La OT original tiene 100 posiciones confirmadas
antes de precio/freeze/liberación, lo que genera 100 OT por el contrato vigente.
La lámina y el suministro de vidrio fueron declarados como P12 DEMO antes de
iniciar Corte. No hay catálogo certificado ni cifras productivas inventadas.

El primer ensayo de rechazo encontró que el selector de medición no era el
selector de rechazo; creó RM-01 sin pieza. Esa evidencia no se borra ni se
reescribe. El control se corrigió, se añadió regresión y la nueva decisión
confirmada RM-02 conserva la pieza; su retry no crea una tercera OT.

## Tamaños e interactividad

La matriz tiene 96 registros: tablero/detalle/pestañas a 1440×900, 1280×800,
1024×768 en ambos temas, más operario a 390×844. Cero hallazgos y desbordes.
Las pestañas quedan antes de dos pantallas de scroll. Medición desde navegación
hasta elemento interactivo visible, sondeado por frame; el límite sigue 2.000 ms.

| Persona | Mínimo | Máximo |
| --- | --- | --- |
| Jefe de taller | 822 ms | 1.035 ms |
| Operario | 891 ms | 936 ms |

Los effects cancelan lecturas descartadas por remount/selección; el servidor
limita la reconstrucción del mecanizado al plan, sin cambiar códigos sellados.
Datos y medidas completos: [informe de matriz](captures/produccion-estaciones/despues/informe.json).
La comparación oficial contra la misma base usa sus detectores originales,
con las sesiones y credenciales solo en memoria.

El capturador oficial pasa 16 vistas, sin hallazgos nuevos al comparar por
rol, tema, tamaño, tipo y muestra. Operario pasa las ocho con cero hallazgos,
frente a 109 por vista en la base. Jefe conserva 32–50 hallazgos heredados,
frente a 883–1.068: son controles de oficina que el config histórico comprueba
como taller. Se conservan ese config y sus detectores; no se eliminan muestras
del informe. Los nuevos controles de tablero, lector, OT terminadas y liberación
tienen al menos 44 px. No hay errores HTTP, consola ni desbordes.
Evidencia: [comparación oficial](captures/produccion-estaciones/comparacion-oficial.json),
[base](captures/produccion-estaciones/oficial-antes/report.json) y
[resultado](captures/produccion-estaciones/oficial/report.json).

## Pase editorial

Primera ronda: se quitaron los nueve bloques de acciones y las tablas de piezas
de la tablet; se reemplazaron cien botones de cola por un selector táctil;
se dieron acciones a los faltantes y al plan pendiente. El operario ve una
pieza y su siguiente trabajo, sin datos comerciales.

Segunda ronda: se plegaron operaciones repetidas y materiales de oficina;
se hicieron explícitos barra, coordenada, referencia y ángulo del plan;
se corrigieron la recarga tras desbloqueo y el selector persistente del rechazo.
Se retiraron contadores decorativos, tablas de barras/láminas duplicadas,
texto redundante de organización y aliases CSS muertos. No se ajustan guardas.

| Rúbrica | Resultado | Evidencia del alcance |
| --- | --- | --- |
| R1 · Formatos y Mono tabular | PASA | Medidas exactas, unidades en encabezados técnicos, cantidades y códigos del plan. |
| R2 · Radios e inglete | PASA | Tokens ≤4 px; detectores sin radios nuevos. |
| R3 · Jerarquía | PASA | Bordes por estación, un panel de paso, sin sombra decorativa. |
| R4 · Naranja | PASA | Motivos de bloqueo y espera de persona; sin CTA naranja. |
| R5 · Teal | PASA | Selección y acción principal con roles del sistema. |
| R6 · Vocabulario | PASA | Sin enums; etiquetas de taller, historial humano y logs en Detalles técnicos. |
| R7 · Densidad | PASA | Pestañas antes de 2 pantallas; piezas virtualizadas; tablet con controles ≥44 px. |
| R8 · Cinco estados | PASA | Runner de estados, causas, reintento y permisos reales de API. |
| R9 · Papel y mesa | PASA | Planos técnicos mantienen superficies del sistema y geometría del motor. |
| R10 · Selección | PASA | Stepper y pieza con contorno/tinte, sin elevación al hover. |
| R11 · Íconos | PASA | Primitivas existentes; sin nuevo símbolo de apertura ni iconografía mezclada. |
| R12 · Foco y teclado | PASA | Formularios etiquetados, selectores nativos y focus-visible del sistema. |
| R13 · Movimiento | PASA | Sin animación añadida; tokens y reducción de movimiento conservados. |
| R14 · Acción principal | PASA | Iniciar/Completar ocupa su región; registro QC y confirmación explícitos. |
| R15 · Autoridad | PASA | Plan/revisión sellados; falta de plan y agenda se declaran, sin capacidad inventada. |
| R16 · Sin efectos arbitrarios | PASA | Detectores originales y guardas; sin degradados, blur, brillos ni morado. |
| R17 · Anchos | PASA | Matriz 1440/1280/1024/390 sin desbordes. |
| R18 · Acciones reales | PASA | Clics y persistencia del recorrido; estructura vieja retirada. |
| R19 · Firma | PASA | F9: pieza ≥32 px, medida, destino y siguiente; F7: bloqueo requiere persona. |
| R20 · Capacidad | PASA | QR del plan localiza la pieza; rechazo confirmado crea remake y aparece en Hoy. |

## Reproducción, decisiones y límites

`make lint`, `make typecheck`, `make test` y `make build`: PASA sobre la fuente
final. Motor: 829 pruebas + 2 xfail; backend: 1.370; frontend: 903 en 81 archivos.
OpenAPI/orval son reproducibles; golden cases y guardas permanecen intactos.

El gate completo pasó 1.217 pgTAP, 441 integraciones y 17 E2E, y detectó un
faltante del entorno independiente PG16: no creaba `auth.users`, que Supabase
proporciona y la nueva clave foránea necesita. El bootstrap se amplía con su
clave primaria; se mantienen todos los checks y se agregan rechazo de usuario
inexistente y limpieza de su puesto. El cierre exige repetir el gate completo
con esa referencia externa disponible, conservando la clave foránea real.

La repetición correctiva termina PASA: 84 archivos / 1.218 pgTAP,
441 integraciones RLS, 17 E2E y las diez suites de actualización poblada
en PostgreSQL 16. El focalizado PG16 también pasa. El gate completo cierra
con código 0 y deja 8000/5173 libres; no se omite ni debilita ningún check.

Con el stack de `.agents/skills/testing-framedex`, seleccione el tenant DEMO
mediante `DEKOPEN_FIXTURE_ORG_ID`; el estado de su proyecto/OT está en
`.run/p12-fixture.json`. Los runners `verify-p12.mjs`, `verify-p12-flow.mjs` y
`verify-p12-states.mjs` se ejecutan desde la raíz con Node y el entorno del stack.
No admiten un Supabase remoto. El capturador oficial se ejecuta con
`npm --prefix frontend run ux:capture -- --routes produccion --roles WORKSHOP_MANAGER,OPERATOR`.

[Decisiones](../decisions/valores-por-defecto.md): puesto por usuario/tenant,
oscuro inicial configurable, medición opt-in y remake del conjunto con pieza
como motivo. Cámara solo si el navegador/dispositivo la ofrece; el recorrido
verifica el lector/input con el QR real. No requiere activar un tercero.
[Activación](../operations/ACTIVACION.md) mantiene los adaptadores externos.

P13/P14/P15 siguen corte avanzado, CNC y retazos. La autoridad DEMO no certifica
un fabricante. El remake requiere optimización propia. No se afirma aceptación
de módulos pendientes ni se altera una revisión emitida para facilitar el fixture.
