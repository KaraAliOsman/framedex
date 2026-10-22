# P05f · Cotizaciones dentro de Obras

Verificado el 22-10-2026 en `gpt/dk2-p05f-cotizaciones-obras`, sobre P05e
`9429a911`. API 8010 y build productivo 5175, PostgreSQL aislado y datos
sintéticos. Se conserva el stack REVIEW del dueño.

## Pantalla y contrato

Obras consume el índice paginado de P05e: recuentos del servidor antes del
segmento, páginas de 50 y búsqueda sin el límite anterior de 500 obras.
La carga inicial usa un módulo propio; el formulario completo sigue disponible
en `?create=1`, conservando cliente/serie y la confirmación humana.

`/quotes` redirige con replace a `/projects?view=quotes`, conservando consulta,
hash, seguimiento, fase, moneda y offset exacto. La vista de emitidas conserva
la pertenencia y orden de emisión históricos; también permite ordenar por
actividad o nombre. La fila abre su revisión de cotización y muestra respuesta,
seguimiento, visitas, última vista y vigencia cuando existen.

Título, acción, segmentos, búsqueda y lista mantienen la jerarquía de
`Obras.dc.html`. Los filtros comerciales amplían ese mockup para conservar
enlaces existentes. En móvil se distribuyen en filas y cada obra conserva sus
campos. Los selectores usan los tokens compartidos. No se añadió movimiento.

Cambiar filtros vuelve a página uno; cambiar de vista limpia los filtros
comerciales ocultos. La búsqueda conserva el foco mientras consulta y cancela
peticiones anteriores; oculta resultados anteriores durante esa espera.
La caché se separa por usuario, empresa y rol. Un conflicto 409 pide recargar.
Dueño/vendedor consultan emitidas; jefe de taller consulta Obras. Operario e
instalador conservan sus límites de navegación.

## Verificación

- Frontend completo: 1.254 pruebas aprobadas; 69 comprobaciones finales dirigidas
  de rutas, índice, búsqueda, caché, permisos, creación y listado.
- Seis E2E finales: dueño, vendedor y jefe de taller a 1440 × 900 y 390 × 844,
  con sesión real Magic Link/TOTP y cálculos del motor del fixture local.
- Se prueba el enlace antiguo con revisión, fase, moneda y seguimiento; filtrar
  por vistas cambia el resultado. No se envía correo ni se llama al proveedor IA.
- Extremos: 500 obras, nombres/clientes de 255 caracteres, 0/500 ventanas,
  importes grandes, páginas intermedias/finales, filtros y vacío. A 320 px y texto
  al 200 % no hay desborde de página. Axe A/AA/2.1 AA pasa en las capturas.
- ESLint, TypeScript, formato, guardas y build productivo aprobados.
- Carga visible local caliente: 271–304 ms en los seis recorridos, sin
  throttling. No constituye una medición de producción.

La purga global de lenguaje y su guardián siguen pendientes en P05; P06–P11
siguen pendientes. La integración no cambia cifras, emisión ni permisos SQL.

## Capturas seleccionadas

| Rol / estado | Escritorio | Móvil |
| --- | --- | --- |
| Dueño, obras | [1440](owner-desktop.png) | [390](owner-mobile.png) |
| Vendedor, obras | [1440](estimator-desktop.png) | [390](estimator-mobile.png) |
| Jefe de taller | [1440](manager-desktop.png) | [390](manager-mobile.png) |
| Dueño, cotizaciones | [1440](quotes-owner-desktop.png) | [390](quotes-owner-mobile.png) |
| Vendedor, cotizaciones | [1440](quotes-estimator-desktop.png) | [390](quotes-estimator-mobile.png) |
| 500 obras | [1440](worst-desktop.png) | [390](worst-mobile.png) |
| En taller | [1440](stage-desktop.png) | [390](stage-mobile.png) |

También [320 px con texto 200 %](worst-320-200.png) y [vacío](empty.png).
