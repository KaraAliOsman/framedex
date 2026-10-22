# P02c · Ficha editable: evidencia de integración

Verificado el 21-10-2026 con la pila sintética propia de P02 (Django 8007,
Supabase 25421 y Vite 5173). Componentes de `gpt/dk2-p02c-ficha-hoja`,
base API `1b09ceb8`; la navegación de la copia de trabajo integra además
el inicio y el diálogo que se entregan en P02e. Esta sub-PR prepara los
componentes y no activa todavía la ruta de producto.

## Comparación con Serie.dc.html

Se conservan monograma de 56 px, título de 28 px, nivel humano, botón de
prueba, franja ámbar con acción, seis pestañas y leyenda de origen. Los
valores editables usan IBM Plex Mono y coma decimal. La ficha adapta su
cabecera a 390 px y limita el desplazamiento horizontal a cada tabla.
La navegación lateral actual se actualizará en P05. Los datos son ensayos
sintéticos explícitos: no representan cifras certificadas de Proline.

| Pestaña | 1440 × 900 | 390 × 844 |
|---|---|---|
| Perfiles | [captura](serie-perfiles-1440.png) | [captura](serie-perfiles-390.png) |
| Reglas | [captura](serie-reglas-1440.png) | [captura](serie-reglas-390.png) |
| Herrajes | [captura](serie-herrajes-1440.png) | [captura](serie-herrajes-390.png) |
| Vidrios y colores | [captura](serie-vidrios-colores-1440.png) | [captura](serie-vidrios-colores-390.png) |
| Tipologías | [captura](serie-tipologias-1440.png) | [captura](serie-tipologias-390.png) |
| Precios | [captura](serie-precios-1440.png) | [captura](serie-precios-390.png) |

Las capturas son del viewport; algunas conservan el desplazamiento vertical
necesario para operar la tabla. Se inspeccionaron visualmente las doce.
La identidad completa aparece en las capturas iniciales de escritorio y en
las pestañas móviles de herrajes, vidrios, tipologías y precios.

## Comprobaciones

- 31 unitarias de tabla, ficha, modelo y errores aprobadas en el worktree.
- ESLint y TypeScript aprobados.
- Dos E2E reales del flujo completo (1440 y 390) aprobadas en 1,4 minutos:
  pegar cinco reglas, guardar, confirmar dos sugeridos, actualizar nivel y
  franja sin recarga, seis pestañas, precio exacto 1234,5678, historial y
  deshacer como escritura nueva. Axe A/AA/2.1 AA sin infracciones y sin
  desbordamiento horizontal de página en cada captura.
- Las mismas ejecuciones prueban 300 perfiles, nombres de 80 caracteres,
  paginación de 50 filas y peso exacto 1,2345. Los casos de teclado completo
  y pegado rectangular están en las 13 unitarias y cuatro E2E de P02a.
- Carga local observada: inicio 1,34–1,53 s, ficha 0,85–0,90 s y 300 perfiles
  2,34–2,35 s. Son tiempos de navegador sobre esta pila, no Core Web Vitals.

El E2E, su fixture y las capturas de inicio/prueba/extremos se entregan en
P02e para mantener la revisión por debajo de unas 2.000 líneas por sub-PR.
La prueba de ventana aquí solo calcula con el motor: el registro humano de
verificación y el caso dorado pertenecen a P03 y siguen pendientes.
