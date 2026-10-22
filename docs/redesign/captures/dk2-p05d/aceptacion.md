# P05d · Obras por etapa real

Verificado el 22-10-2026 en `gpt/dk2-p05d-obras`, con las dependencias de
catálogo P03h integradas en P04/P05. API 8010 y build de producción 5175 sobre
Supabase sintético aislado. Se conserva el stack REVIEW del dueño.

## Comparación con Obras.dc.html

Título de 32 px, acción principal, segmentos con recuentos, búsqueda en
píldora y una lista blanca con cinco columnas: obra/cliente, etapa, ventanas,
total con IVA y actividad. Se conserva un código humano adicional para
identificar nombres iguales. La cola de decisiones se consulta en Hoy.
Se retiró su tarjeta duplicada de esta pantalla.

En móvil, cada fila conserva todos los campos en dos columnas. A 320 px pasa
a una columna. El enlace ocupa la fila y admite Enter, menú contextual y
abrir en otra pestaña; no simula un enlace con un onClick sobre una tarjeta.
Se corrigieron el color heredado de enlaces y el desborde del botón al 200 %.
No se añadió movimiento; solo se reutiliza la respuesta de controles existente.

| Campo      | Origen y límite                                                                               |
| ---------- | --------------------------------------------------------------------------------------------- |
| Etapa      | `ProjectResponse.progress.stage` calculado en backend, sin deducirla del estado antiguo       |
| Recuento   | Obras de la consulta que coinciden con búsqueda/estado; antes del segmento y la página        |
| Ventanas   | `position_count` de la API; cantidad de diseños guardados, no suma de unidades de fabricación |
| Total      | Oferta vigente elegida; en su ausencia, precio aplicado de la revisión actual con su moneda   |
| Sin precio | «Abre para calcular» o «Añade ventanas»; no cero ni importe de una revisión anterior          |
| Actividad  | `updated_at` del proyecto, con fecha completa en el atributo title                            |

La API existente devuelve hasta las 500 obras más recientes. La pantalla
declara ese límite al alcanzarlo; no presenta ese recuento como todas las
obras posibles del tenant. Filtros y orden operan sobre ese conjunto antes de
paginar. El estado histórico en `?status=` se conserva y se puede quitar; el
segmento nuevo guarda `?stage=` y descarta el estado anterior al cambiarlo.

## Pruebas

Seis E2E reales, OWNER/ESTIMATOR/WORKSHOP_MANAGER en 1440 × 900 y 390 × 844,
usan sesión normal con Magic Link y TOTP del dueño. El seeder reutiliza
cotización emitida y borrador con ventanas, restringido a tenant sintético
local cuyo dueño coincide; no se relajan permisos ni se envía nada.
Los roles operario/instalador mantienen su exclusión de Obras, comprobada
en los recorridos de [navegación](../dk2-p05a/aceptacion.md).

`break-ui`: selector Demo data / Worst case / Empty inyectado solo por la
prueba, 500 obras, ocho etapas, diseños con 0/500 ventanas, nombres/clientes
de 255 caracteres y montos de 20 dígitos. Se comprueban la primera, segunda
y última página, filtros que vuelven a página uno, búsqueda y regreso desde
el detalle. No hay desborde horizontal ni infracciones axe A/AA/2.1 AA en la
pantalla a 1440/390, 320 px o texto al 200 %.

Las unitarias comprueban preferencia del importe emitido, precisión textual,
borradores sin precio, enlaces de estado antiguo, búsqueda, orden estable y
offsets inválidos. 48 comprobaciones dirigidas pasan. Lint/tipos, guardas y
build productivo pasan. Tras integrar P03h pasan las 1.245 pruebas del
frontend y veinte integraciones PostgreSQL de alta de serie, precios del
proveedor, etapas y Hoy. El contrato OpenAPI coincide con su regeneración.

El primer reensayo integrado detectó un timeout al preparar 300 perfiles
innecesarios para Obras. Se usa el catálogo mínimo en este recorrido, sin
reducir sus 500 obras de estrés. Los seeders se esperan de forma asíncrona
para no bloquear las conexiones del runner. Si preparación y limpieza fallan,
el fixture conserva ambos errores; nunca convierte la limpieza fallida en éxito.

Carga visible local con caché caliente: 295–328 ms en los seis recorridos
de roles. Sin throttling; no acredita rendimiento de producción.

## Capturas seleccionadas

| Rol / estado                 | Escritorio                    | Móvil                       |
| ---------------------------- | ----------------------------- | --------------------------- |
| Dueño, obras reales          | [1440](owner-desktop.png)     | [390](owner-mobile.png)     |
| Vendedor, obras reales       | [1440](estimator-desktop.png) | [390](estimator-mobile.png) |
| Jefe de taller, obras reales | [1440](manager-desktop.png)   | [390](manager-mobile.png)   |
| 500 obras                    | [1440](worst-desktop.png)     | [390](worst-mobile.png)     |
| En taller                    | [1440](stage-desktop.png)     | [390](stage-mobile.png)     |

También [320 px con texto 200 %](worst-320-200.png) y [vacío](empty.png).
