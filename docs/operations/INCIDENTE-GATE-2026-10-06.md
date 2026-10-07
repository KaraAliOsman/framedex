# Incidente de aislamiento del gate local · 06-10-2026

Durante la verificación D05 se lanzó `make test-db` antes de que finalizara la
sincronización del clon Linux aislado. La sincronización copiaba temporalmente
el `supabase/config.toml` original y sustituía su identidad al terminar. En esa
ventana, el CLI leyó `project_id=dekopen`, encontró su stack ya activo y ejecutó
`supabase db reset --local` en esa base local. El log confirma recreación del
esquema, migraciones y semilla; no permite afirmar que se preservaron sus datos
previos. Es un error del agente que ejecutó el gate, ajeno a los cambios de
acabados del producto.

El repositorio Git `KaraAliOsman/dekopen` y `main` no se editaron ni recibieron
push. Esto no limita el impacto de base: **los datos locales de aquel stack
pueden haberse perdido**. No se realizó otra mutación ni un intento de
restauración sobre ese stack. No se envió un mensaje a su otro agente. El
stack de aplicación propio `framedex-cola` conserva sus fixtures y documentos.

Contención aplicada al entorno local ignorado de esta tarea:

1. La sincronización transforma la identidad y puertos antes de escribir el
   archivo y lo reemplaza atómicamente; nunca publica el proyecto original.
2. El wrapper de **cada** llamada al CLI exige el directorio absoluto
   `/tmp/framedex-cola-native`, proyecto `framedex-cola-native`, API 25341 y DB
   25342. Rechaza cualquier otra identidad antes de ejecutar Supabase.
3. Los gates se inician solamente después de recibir la terminación exitosa de
   la sincronización. La limpieza valida etiquetas y nombres de volúmenes
   propios; no opera sobre recursos ajenos.

Protección permanente en el repositorio: `scripts/local_gates.py` rechaza
contenedores (incluidos detenidos o sin etiqueta moderna) y volúmenes previos
del proyecto configurado antes de `supabase start`. Las regresiones de
`test_gate_harness.py` comprueban que el rechazo no ejecuta start, reset ni stop.
El gate mantiene la instalación limpia, pgTAP, RLS, navegador y upgrade PG16;
se usa un proyecto aislado vacío para verificarlo.

La ejecución afectada no cuenta como aceptación. La aceptación de D05 usa una
ejecución posterior sobre el proyecto aislado con esas guardas. Si existía
información útil en la base local anterior, el dueño deberá revisar sus propios
respaldos; no hay un respaldo de esos datos en la evidencia de este encargo.
