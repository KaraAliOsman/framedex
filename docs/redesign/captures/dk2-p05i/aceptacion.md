# P05i · Mensajes de obras y precios del servidor

Verificado el 22-10-2026 en `gpt/dk2-p05i-mensajes-servidor`, sobre P05h
`b9b98cee`. API 8010 y PostgreSQL aislado; el build productivo de P05h se
reutiliza porque esta ronda no modifica el frontend. REVIEW del dueño intacto.

## Cambio

Obras, operaciones por lote, montaje, herrajes, acabados, servicios, búsqueda,
precios e informes usan ventana, origen, datos guardados y revisiones emitidas.
Los errores mantienen sus códigos y explican qué completar. La ausencia de tipo
de cambio conserva selección, moneda y falta de precio; el mensaje se presenta
una sola vez. Un certificado requiere una entidad certificadora. La ventana
aceptada conserva su revisión y la serie ausente pide completar su nombre.

Se revisaron diecinueve módulos del servidor. La comparación AST verifica claves
de diccionarios, literales numéricos y consultas SQL idénticos. No cambia ninguna
fórmula, permiso, contrato de API ni escritura sobre historia emitida. Los textos
nuevos se producen al consultar o preparar resultados nuevos; no se transforman
recursivamente valores del cliente ni snapshots guardados.

## Validación

- Backend completo: 1.737 PASS en 270 s. Tras el último pase editorial pasan
  otras 18 pruebas de analítica y búsqueda.
- Integraciones PostgreSQL de operaciones, medidas de obra, herrajes, acabados,
  extras, permisos de precios e informes. La única expectativa antigua de «Sin
  dato» se actualiza conservando la comprobación de moneda y selección sin precio.
  Las 31 regresiones finales de servicios, acabados y espacio de precios pasan,
  incluyendo reproducción exacta sin I/O y límites de lectura comercial por rol.
- Cuatro E2E pasan: catorce superficies a 1440 × 900 y 390 × 844, y precio simple
  con tres ventanas, cuatro decimales, margen, recuperación, importes enormes,
  320 px y texto al 200 %. Axe no encuentra infracciones en el precio simple.
- Ruff, Django check y guardas aprobados. Las cifras doradas y el cliente
  generado no cambian. El build ya verificado en P05h sirve estas pruebas.
- Precio simple carga en 331–357 ms; LCP 296–316 ms; CLS 0,00086–0,00156;
  cambio de ejemplo en 858–877 ms. Son medidas locales sin throttling.
  La carga lenta de montaje registrada en P05h sigue pendiente para P11.

## Límites

El catálogo PRO6004, sus precios y las obras son sintéticos; esta prueba no
acredita el manual real ni la aceptación de P10. Chromium emula móvil. No se
valida aquí el PDF embebido ni se cambia movimiento. Se conservan las jerarquías
visuales existentes y se selecciona evidencia representativa de las respuestas.

P05 continúa: mensajes del motor, documentos y otras áreas del servidor aún
requieren su revisión contextual. No se reescribe evidencia ya emitida para
eliminar palabras antiguas. Las fusiones esperan su orden y los cuatro controles
verdes del head actual; P06–P11 siguen pendientes.

## Capturas seleccionadas

| Pantalla          | Escritorio                            | Móvil                                  |
| ----------------- | ------------------------------------- | -------------------------------------- |
| Precio de obra    | [1440](pricing-1440.png)              | [390](pricing-390.png)                 |
| Informes          | [1440](analytics-1440.png)            | [390](analytics-390.png)               |
| Servicios         | [1440](services-1440.png)             | [390](services-390.png)                |
| Ejemplo de precio | [1440](02-pro6004-breakdown-1440.png) | [390](02-pro6004-breakdown-390.png)    |
| Montos enormes    | [1440](05-large-amounts-1440.png)     | [390](05-large-amounts-390.png)        |
| Extremos          | [320 px](07-width-320.png)            | [Texto 200 %](08-text-200-percent.png) |
