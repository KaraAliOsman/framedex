# Evidencia sintética de D01

Estos archivos son fixtures de verificación, sin certificación ni datos de proveedores reales.

- `ficha-sintetica.pdf`: fuente con texto enviada al proveedor MiMo configurado en el entorno local.
- `mimo-verification.json`: resultado de la extracción real del 05-10-2026: 31 candidatos, 324 campos respaldados y 27 UNKNOWN; publicación bloqueada por revisión incompleta.
- `mimo-candidates.json`: candidatos y citas originales preservados para auditar esa verificación. Las correcciones humanas se registran separadamente; esta respuesta no es autoridad del motor.
- `catalogo-nine-sheets.xlsx`: 32 filas de las nueve hojas oficiales, con reglas de junquillo declaradas y costos sintéticos. Sirve para comprobar publicación, exportación y deshacer.
- `cotizacion-demo.pdf`: salida del renderizador del producto desde una revisión sintética congelada; verifica la advertencia DEMO.

La plantilla descargable del producto está en `backend/ingest/templates/catalogo-v1.xlsx`. El generador de series DEMO usa la semilla `20261005`; sus dimensiones, masas y costos son datos de prueba reproducibles. Los usuarios cargan su autoridad real desde Catálogo y la revisan antes de publicar.
