# P05g · Lenguaje de producto y valores pendientes

Verificado el 22-10-2026 en `gpt/dk2-p05g-lenguaje`, sobre P05f `a4e2ca98`.
Build productivo 5175, API 8010 y Supabase/PostgreSQL aislado. Los datos son
sintéticos; el stack REVIEW del dueño se conserva.

## Cambio

El guardián de Catálogo analiza ahora todos los textos TypeScript/JSX de
producto y todos los valores del diccionario. Rechaza las cinco voces del
encargo («Sin dato», «sellado», «autoridad», «fuente», «procedencia») sin una
lista base de excepciones. Sus pruebas distinguen textos, aria-label,
templates y concatenaciones de claves de contrato, comentarios y relaciones
DOM. La API generada y las rutas exclusivas de desarrollo quedan fuera.

Los mensajes piden completar el dato o indican su origen. Una revisión
preparada sigue siendo de solo lectura; un documento emitido se identifica
como emitido. Los precios guardados y las piezas de la orden conservan su
significado. La aplicación de sellante y la junta de cierre mantienen su
función física. Las tareas de IA muestran un resumen. Null sigue siendo
distinto de cero; medidas, dinero y cálculos conservan su precisión.

También se corrigen los avisos térmicos y de Hoy en su origen del servidor.
No se modifica evidencia ya emitida ni prosa de clientes. El ensayo visual
detectó etiquetas superpuestas en las pestañas móviles: conservan ahora su
ancho dentro del desplazamiento local y la prueba comprueba su separación.

La regresión del editor encontró una lectura repetida de todos los costos DEMO
por material y módulo. El perfil del proceso confirmó el trabajo en
`demo_cost_rows`/`cost`. El precio indicativo usa ahora una lectura de costos
propia del cálculo, con el repositorio y prefetch existentes; no hay caché
global. PostgreSQL comprueba una lectura DEMO, igualdad exacta con la lectura
sin caché y un precio actualizado después de cambiar tarifas del tenant entre
consultas. Las dos interacciones bow vuelven a pasar en 39,7 s, manteniendo los
límites originales de las pruebas y el rechazo del ángulo inválido.

## Verificación

- 1.254 pruebas frontend aprobadas con dos trabajadores; guardián y pruebas
  del detector aprobados, con cero infracciones de las cinco voces.
- Python completo: 2.858 PASS y dos xfail previos. La prueba térmica conserva
  el golden exacto; la comprobación general de bytes dorados pasa en modo
  lectura. Se ejercitan además térmica y Hoy con PostgreSQL real.
  Después del ajuste de lectura de costos pasan 46 regresiones unitarias
  dirigidas de precios, Hoy y térmica, y 25 integraciones de operaciones.
- Once pantallas en escritorio y móvil: térmica, precio, cobros, cotización,
  documentos, asistente, taller, terreno, compras, informes y costos. La prueba
  espera contenido visible cargado, rechaza errores, comprueba el texto final,
  la separación de pestañas y el ancho de página. No confunde una carga oculta
  dentro de un details cerrado con el estado visible de la pantalla.
- Dieciséis E2E de navegación/Obras y cuatro de precios aprobados, con cinco
  roles, 500 obras/ventanas, nombres largos, montos grandes, 320 px, texto al
  200 % y axe en las regiones correspondientes. El PDF emitido conserva sus
  bytes después de cambiar el precio del borrador.
- Las ocho interacciones existentes del editor pasan después del ajuste:
  creación y arrastre bow, cotas, precio pendiente y recuperación, propuesta,
  deshacer, protección de borrador y permisos de móvil/tablet actuales.
- Lint, tipos, formato, guardas y build aprobados. No se añade movimiento.
- Carga visible local de estas once pantallas: 410–1.855 ms, sin throttling;
  el recorrido completo de ambos tamaños tarda 55,2 s. La consulta de ejemplo
  de precios tarda 881–894 ms; la búsqueda de 500 filas tarda 47–48 ms.

## Límites y continuación

P05 sigue en curso: ventana/medida de obra/coordenada necesita una revisión
contextual separada. Una coordenada de herramienta no se puede renombrar como
ventana; la abertura de obra tampoco equivale a su fabricación.
P06–P11 permanecen pendientes. La revisión móvil usa Chromium emulado; no hay
un teléfono físico disponible para confirmar teclado, gestos y Safari móvil.

Los ensayos no activan producción, envían correos, ejecutan pagos reales ni
atribuyen el catálogo sintético al fabricante. Las capturas conservan la
estructura existente de las superficies avanzadas; la mesa y los flujos
comerciales se rediseñan en sus fases posteriores.

## Capturas seleccionadas

Corrección del Database Gate (22-10): el recorrido SHOT-10 esperaba el GET
anterior de proyectos. Obras consulta `/projects/works/` desde P05e. Se ajusta
solo esa espera al contrato vigente, conservando la respuesta vacía y todo el
recorrido de guardado, BOM, clonación e inmutabilidad. Repetición local sobre
la rama de P05g: **1 E2E aprobado, 1,3 min**, sin reintentos.

Los viewports son 1440 × 900 y 390 × 844. Se conserva la página completa,
incluidas las secciones largas. Las trazas de diagnóstico quedan en `.run/`.

| Pantalla | Escritorio | Móvil |
| --- | --- | --- |
| Térmica | [1440](thermal-1440.png) | [390](thermal-390.png) |
| Precio | [1440](pricing-1440.png) | [390](pricing-390.png) |
| Cobros | [1440](payments-1440.png) | [390](payments-390.png) |
| Cotización | [1440](quote-1440.png) | [390](quote-390.png) |
| Documentos | [1440](documents-1440.png) | [390](documents-390.png) |
| Asistente | [1440](assistant-1440.png) | [390](assistant-390.png) |
| Taller | [1440](production-1440.png) | [390](production-390.png) |
| Terreno | [1440](field-1440.png) | [390](field-390.png) |
| Compras | [1440](purchasing-1440.png) | [390](purchasing-390.png) |
| Informes | [1440](analytics-1440.png) | [390](analytics-390.png) |
| Costos | [1440](costs-1440.png) | [390](costs-390.png) |
