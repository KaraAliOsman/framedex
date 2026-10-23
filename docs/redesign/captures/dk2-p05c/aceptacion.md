# P05c · Hoy: revisión y acciones reales

Verificado el 22-10-2026 en `gpt/dk2-p05c-hoy`, sobre P05b. Stack sintético
aislado: API 8010, preview del build 5175, Supabase local 25421/25422.
No se reinició REVIEW del dueño ni se usaron datos de clientes.

## Comparación con Hoy.dc.html

Se conserva la jerarquía del mockup: fecha/saludo y acción principal, hasta
tres métricas, tarjeta de preparadas y cola «Para hacer». Los paneles blancos,
acento verde, radios, espaciado y tipografía usan tokens existentes. En móvil
la acción principal y Revisar pasan a otra línea, sin desplazar texto fuera
de la pantalla. No se añadió movimiento.

Las cifras ficticias del mockup se sustituyen por recuentos reales de tareas.
«Aceptadas por coordinar» refleja lo que mide la API; no afirma una semana ni
un margen no disponibles. Venta por etapa permanece en un desplegable.

| Dato visible | Origen verificado |
| --- | --- |
| Fecha | Día de la organización recibido de TodayResponse, sin desplazarlo por zona horaria |
| Saludo | Nombre de la sesión y hora de Santiago; sin nombre conserva el saludo |
| Métricas | Entidades únicas en tareas autorizadas por rol; no se muestran ceros |
| Preparadas | Borradores con ventanas y recibo verificado, creados por el asistente del usuario |
| Acciones, saldos y enlaces | TodayResponse del motor/backend bajo RLS; sin recomputar importes |
| Nueva cotización | POST explícito de borrador; bloqueo de clic repetido y descarte de navegación tardía |

## Ensayo y límites

Diez E2E reales de navegación cubren OWNER, ESTIMATOR, WORKSHOP_MANAGER,
OPERATOR e INSTALLER en 1440 × 900 y 390 × 844. Dos E2E de Hoy crean una
cotización emitida y un borrador preparado, revisan sin escribir/enviar,
comprueban Escape/restauración de foco y crean un borrador mediante clic.
El trabajo IA de la prueba es sintético y cumple el contrato del recibo;
no representa una ejecución de proveedor. Se usa Magic Link y TOTP reales.

La edición bajo 1024 px sigue mostrando «Vista de lectura» en el editor
actual. La prueba comprueba ese límite; no acredita edición móvil, cuyo
rediseño corresponde a P06.

`break-ui`: selector inyectado exclusivamente por Playwright (Demo data /
Worst case / Empty), 1.000 acciones, nombres de 255 caracteres, título sin
espacios y montos de 20 dígitos. La cola conserva 50 filas por página y el
límite 51–100. Se revisan 320 px y texto al 200 %. Se corrigió el solapamiento
del contador de campana: «99+» visual conserva el total accesible. No hay
desborde horizontal ni infracciones axe A/AA/2.1 AA en Hoy y el diálogo.
No se incluyen datos ni selectores de prueba en el producto.

Las mediciones de preview local con caché caliente estuvieron entre 276 y
322 ms hasta el contenido de Hoy; LCP 132–152 ms, CLS 0,0012–0,0035. Son
observaciones del entorno de prueba sin throttling, no un SLA de producción.
Build productivo, ESLint/TypeScript, 14 unitarias dirigidas y Ruff aprobados.
La suite frontend anterior detectó únicamente cuatro etiquetas de etapas
faltantes, corregidas en P05b y comprobadas con 212 pruebas del glosario.

## Capturas seleccionadas

| Estado | Escritorio | Móvil |
| --- | --- | --- |
| Hoy real | [1440](today-desktop.png) | [390](today-mobile.png) |
| Preparadas | [1440](prepared-desktop.png) | [390](prepared-mobile.png) |
| 1.000 acciones | [1440](worst-desktop.png) | [390](worst-mobile.png) |
| Vacío | [1440](empty-desktop.png) | [390](empty-mobile.png) |

Extremos adicionales: [320 px](worst-320.png), [texto 200 %](worst-200.png).
Roles sin tareas: [vendedor](estimator-desktop.png), [vendedor móvil](estimator-mobile.png),
[jefe de taller](manager-desktop.png), [jefe de taller móvil](manager-mobile.png),
[operario](operator-desktop.png), [operario móvil](operator-mobile.png),
[instalador](installer-desktop.png), [instalador móvil](installer-mobile.png).
