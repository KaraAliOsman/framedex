# P05h · Ventanas, medidas de obra y coordenadas

Verificado el 22-10-2026 en `gpt/dk2-p05h-ventanas`, sobre P05g `32e3b3c5`.
Build productivo 5175, API 8010 y PostgreSQL aislado, con datos sintéticos.
El stack y checkout del dueño se conservan.

## Cambio

Corrección del Database Gate (22-10): el E2E SHOT-07 conserva la verificación
real del motor, la previsualización, el rollback de red y la aprobación solo
con semáforo verde. Su selector pasa a «Coordenadas de desagües inferiores»,
la etiqueta contextual de esta fase. **1 E2E aprobado, 18,5 s**, sin reintentos.
Integra además la espera de `/projects/works/` corregida en P05g.

Los textos distinguen ventana, paño interior, abertura de obra y coordenada de
mecanizado. Las medidas de obra se presentan separadas de las de fabricación.
Los servicios se aplican por ventana; los cobros tienen comprobantes y las
tareas del asistente, resumen. Se revisaron concordancias y significado físico;
no se sustituyen coordenadas por ventanas ni se modifica una cifra.

El guardián AST rechaza también posición/vano, encargo y recibo. Sigue
comprobando textos accesibles, templates y concatenaciones. Los identificadores,
enlaces DOM y sinónimos de búsqueda mantienen compatibilidad. No existe una
lista base de infracciones permitidas; las pruebas documentan esa frontera.

Se corrigen etiquetas térmicas y acciones de Hoy en el servidor. La revisión
ampliada encontró la etiqueta histórica del proceso genérico global: el selector
proyecta una etiqueta humana conservando registro, código y versión originales.
Una prueba comprueba que los nombres propios del taller quedan intactos.
El estado vacío de cobros tiene un título explícito y gramaticalmente correcto.

## Verificación

- Suite frontend completa: 1.254 PASS. Después del último ajuste de título se
  ejercitan además los componentes de tabla, obra y decisión del portal.
- 55 pruebas Python dirigidas y ocho integraciones PostgreSQL de térmica/Hoy
  aprobadas. La comprobación general de bytes dorados pasa en modo lectura.
- 21 E2E aprobados: ocho interacciones del editor; diez recorridos de los cinco
  roles a 1440/390, con teclado y axe; el flujo real de obra con guardar,
  recargar, cantidad, duplicación y dibujos; lenguaje en catorce superficies a
  1440 × 900 y 390 × 844. Se mantiene el ensayo extremo de 500 obras en P05f.
- La prueba espera el contenido cargado, rechaza errores, busca las voces del
  glosario, comprueba separación de pestañas y evita desborde de página.
  El flujo antiguo de obra esperaba el endpoint de listado sustituido en P05;
  ahora comprueba el índice real `/projects/works/`, manteniendo sus aserciones.
- ESLint, TypeScript, Ruff, Prettier, guardas y build aprobados. No se añade
  movimiento ni cambia la lógica de cálculo.

## Rendimiento y límites

Las once superficies ya cubiertas cargan aproximadamente en 0,4–1,1 segundos
locales, sin throttling. La revisión añadida de montaje tarda 8,5–10,0 segundos;
Comercial tarda 2,1–3,3 segundos. Queda registrada esa carga para P11; esta ronda
no acredita el objetivo final de rendimiento. Los datos y precios de ensayo
son sintéticos. Chromium emula móvil; no hay un teléfono físico disponible.

Estas capturas acreditan texto y distribución de interfaz. El visor PDF embebido
no se usa como prueba visual del documento: los PDF se revisan como artefactos
independientes en la fase documental. No se activan producción ni pagos reales.

P05 sigue en curso: faltan mensajes y documentos generados por backend y motor,
además de fusionar las sub-PR en orden con los cuatro controles verdes en su
head actual. El recuento cero de TypeScript no acredita todos esos resultados.
No se reescriben registros emitidos ni texto aportado por clientes. P06–P11
permanecen pendientes.

## Capturas seleccionadas

La página completa conserva las secciones largas. Las trazas y contactos de
revisión quedan en `.run/`.

| Pantalla   | Escritorio                  | Móvil                     |
| ---------- | --------------------------- | ------------------------- |
| Térmica    | [1440](thermal-1440.png)    | [390](thermal-390.png)    |
| Precio     | [1440](pricing-1440.png)    | [390](pricing-390.png)    |
| Cobros     | [1440](payments-1440.png)   | [390](payments-390.png)   |
| Cotización | [1440](quote-1440.png)      | [390](quote-390.png)      |
| Documentos | [1440](documents-1440.png)  | [390](documents-390.png)  |
| Asistente  | [1440](assistant-1440.png)  | [390](assistant-390.png)  |
| Taller     | [1440](production-1440.png) | [390](production-390.png) |
| Terreno    | [1440](field-1440.png)      | [390](field-390.png)      |
| Compras    | [1440](purchasing-1440.png) | [390](purchasing-390.png) |
| Informes   | [1440](analytics-1440.png)  | [390](analytics-390.png)  |
| Costos     | [1440](costs-1440.png)      | [390](costs-390.png)      |
| Montaje    | [1440](mounting-1440.png)   | [390](mounting-390.png)   |
| Servicios  | [1440](services-1440.png)   | [390](services-390.png)   |
| Primer uso | [1440](onboarding-1440.png) | [390](onboarding-390.png) |
