# Evidencia de DEKOPEN

## DEKOPEN 2

- [P05f · Cotizaciones dentro de Obras](dk2-p05f/aceptacion.md): índice del
  servidor, filtros históricos, permisos y dieciséis capturas finales.

- [P05d · Obras por etapa](dk2-p05d/aceptacion.md): lista densa, enlaces de
  fila, filtros persistentes y 500 obras en tres roles autorizados.

- [P05c · Hoy y revisión de preparadas](dk2-p05c/aceptacion.md): saludo,
  tareas reales por rol, revisión humana y extremos de 1.000 acciones.

- [P04g · precio automático en obra](dk2-p04g/aceptacion.md): total, desglose,
  emisión sin aplicar, PDF conservado y extremos de 500 ventanas.

- [P04f · precios de empresa](dk2-p04f/aceptacion.md): pantalla simple,
  ejemplo del motor, importes extremos y texto ampliado en diez capturas.

- [P03h · alta reanudable](dk2-p03h/aceptacion.md): cinco pasos, conservación
  de borradores, corrección exacta y primera obra con la serie seleccionada.

- [P03g · doble lectura visible](dk2-p03g/aceptacion.md): diferencias, ambas
  citas, elección humana, publicación real y extremos de 0/1/500 filas.

- [P03f · precios del proveedor](dk2-p03f/aceptacion.md): mapeo, revisión del
  archivo completo, confirmación explícita y extremos de precios exactos.

- [P03e · ventana de prueba](dk2-p03e/aceptacion.md): comparación exacta,
  ajustes, verificación humana, edición protegida y extremos de 0/1/500 piezas.

- [P02a · tabla editable](dk2-p02a/aceptacion.md): diez capturas seleccionadas
  de escritorio/móvil, extremos, accesibilidad y alcance del componente.

- [P02c · ficha de seis pestañas](dk2-p02/aceptacion-ficha.md): doce capturas
  de integración, comparación visual y límites de la entrega.

- [P02 · catálogo integrado](dk2-p02/aceptacion.md): inicio, seis pestañas,
  prueba preliminar, flujo real y extremos en 19 capturas seleccionadas.

## DEKOPEN v1

La aceptación vigente está en [el informe final](../acceptance-2026-10-12.md).
`aceptacion-final/` conserva íntegros sus 2,185 archivos:
capturas, recibos, resultados, QA y gates con los refs de cada medición.
Esta limpieza no vuelve a ejecutar ni reatribuye esos ensayos.

## Evidencia histórica recuperable

Se retiraron del checkout 6,979 archivos generados de
rondas anteriores (1,488.18 MiB). Se conservan los
informes Markdown, resultados JSON completos y código de las herramientas.
Se retiraron imágenes, videos, exportaciones de presentación, cobertura con
copias de código y registros parciales duplicados. Los PNG/PDF de
`identificadores-humanos/recorrido/` permanecen como entradas de
`scripts/verify_human_codes_qr_pixels.py`; los informes de antes/después que
consume `scripts/compare_human_codes_captures.py` también permanecen.

Todos los archivos retirados siguen en el
[árbol anterior a la limpieza](https://github.com/KaraAliOsman/framedex/tree/2db4e13171884b93a989e68508a55f5590f9b34d/docs/redesign/captures),
commit `2db4e13171884b93a989e68508a55f5590f9b34d`. Los enlaces directos de los informes apuntan a ese SHA cuando
su destino fue retirado. Sus nombres de archivo internos siguen describiendo
la corrida original; no convierten una captura antigua en estado vigente.

Para recuperar una ronda sin modificar el código actual, exporte solo ese
subárbol a una carpeta temporal. Ejemplo desde la raíz, con `.run/` existente:

```powershell
git archive --format=zip --output=.run/evidencia-P02.zip 2db4e13171884b93a989e68508a55f5590f9b34d docs/redesign/captures/identificadores-humanos
```

La copia original de los mapas extensos también es consultable:
[estado anterior](https://github.com/KaraAliOsman/framedex/blob/2db4e13171884b93a989e68508a55f5590f9b34d/docs/wiki/state/current-reality.md),
[progreso de fase 00](https://github.com/KaraAliOsman/framedex/blob/2db4e13171884b93a989e68508a55f5590f9b34d/docs/redesign/progress.md) e
[índice de evidencia de fase 00](https://github.com/KaraAliOsman/framedex/blob/2db4e13171884b93a989e68508a55f5590f9b34d/docs/redesign/evidence-index.md).

Guarde exploraciones nuevas en `.run/`; seleccione evidencia durable antes de
versionarla. Consulte [mantenimiento del workspace](../../operations/WORKSPACE.md)
para proteger fixtures, secretos, sesiones, WSL y bases. `.rgignore` excluye
estos payloads de las búsquedas generales; las rutas explícitas y
`rg --no-ignore docs/redesign/captures/` permiten investigarlos.

- [P05a · Navegación por rol](dk2-p05a/aceptacion.md): dieciséis capturas de
  cinco roles en escritorio/móvil; contenido nuevo de Hoy/Obras aún pendiente.
