# P05k · Diagnósticos del motor y mensajes del servidor

Verificado el 22-10-2026 en `gpt/dk2-p05k-diagnosticos`, sobre P05j
`4beeb8d1`. API propia 8010, preview 5175 y PostgreSQL aislado. REVIEW y el
checkout del dueño se conservan. El frontend usa el build verificado de P05h;
esta entrega cambia textos del servidor, del motor y de sus instrucciones IA.

## Alcance y compatibilidad

55 módulos Python distinguen ventana de obra, paño interior, abertura de obra,
ubicación de piezas, reglas declaradas, revisión emitida y comprobante de pago.
Un dato físico de la orden nunca se presenta como un documento emitido. Los
pendientes explican qué completar. El agente solicita el mismo vocabulario y
conserva los contratos, las reglas de cifras verificadas y los clics humanos.

El evaluador acepta «Falta completar» solo acompañado de una causa técnica y
continúa rechazando pesos inventados, también dentro de esa respuesta. Acepta
el vocabulario anterior para comparar ejecuciones históricas. Los textos
aportados por clientes y los documentos emitidos no se reescriben.

La auditoría restante clasifica los marcadores históricos de cotización y
plantillas, encabezados CSV/XLSX, sinónimos de entrada, expresiones de evaluación,
docstrings e instrucciones internas. No son etiquetas nuevas de interfaz.
`catalog_template.display_label` ya proyecta los títulos de plantilla al lenguaje
actual sin romper sus encabezados versionados.

Una comparación AST confirma que en los 55 módulos solo cambian valores de
cadenas: SQL, claves de diccionarios, números y estructura ejecutable idénticos.
No cambia una fórmula, una autorización ni una regla de fabricación.

## Casos dorados

Se compararon los 22 archivos del escritor canónico antes de regenerar. La única
diferencia es el texto de nueve sugerencias de vierteaguas en
`golden_advanced_openings.json`: «Hay una ventana compatible; revisa si la fachada
necesita vierteaguas». Listas, claves, tipos y todas las cifras son idénticos.

Se ejecutó el escritor de `make goldgen` (`python -m
engine.scripts.regenerate_golden`, mismo target del Makefile en Windows), se
revisó el diff y la comprobación posterior `--check` aprobó sin escribir bytes.
Los otros 21 archivos permanecen idénticos. Ningún snapshot emitido se regenera.

## Validación

- Suite completa de motor y backend: 2.860 PASS, dos xfail previos, 292,27 s.
- 94 regresiones de agente/evaluador pasan después del último ajuste de prompts.
- 81 integraciones PostgreSQL aprobadas: vidrio, compras/inventario, intercambio
  de catálogo, datos visibles, API de catálogo y operaciones del proveedor IA.
- 229 regresiones finales aprobadas: aperturas avanzadas, extras, mutación de
  bytes dorados, contexto, tareas, inventario y evaluación de cifras IA.
- P05j corrige dos expectativas textuales antiguas en su propia rama;
  sus 95 pruebas de dibujo/desglose pasan en `4beeb8d1`.
- Ruff, mypy (143 archivos), Django check, guardianes y regeneración reproducible
  de OpenAPI/orval aprobados. No se editó el cliente generado a mano.
- Dos E2E reales recorren catorce superficies a 1440 × 900 y 390 × 844:
  contenido cargado, cero voces del glosario, pestañas sin solapamiento y
  ausencia de desborde horizontal. Magic Link y TOTP reales; datos sintéticos.

## Pantallas y rendimiento

Seis capturas seleccionadas conservan Asistente, Compras y Terreno en ambos
tamaños. Se revisó su contenido y distribución; no hay cambio de layout ni
movimiento en esta entrega. La aceptación de los cinco roles, los extremos de
Obras y la comparación con Hoy/Obras se conserva en P05c/P05f/P05h.

Los 28 tiempos reales están en [tiempos.json](tiempos.json). Montaje tarda
8,0–10,2 s y Servicios 2,2–3,2 s bajo carga local concurrente: deuda explícita de
P11, sin atribuir una mejora de rendimiento a este cambio textual. El móvil se
verifica mediante emulación Chromium, sin dispositivo físico. Esta entrega no
ejecuta una evaluación con proveedor IA real ni acredita un catálogo de fabricante.

| Superficie | Escritorio | Móvil |
| --- | --- | --- |
| Asistente | [1440](assistant-1440.png) | [390](assistant-390.png) |
| Compras | [1440](purchasing-1440.png) | [390](purchasing-390.png) |
| Terreno | [1440](field-1440.png) | [390](field-390.png) |

P05 permanece en curso hasta cerrar sus fusiones con los cuatro controles de
CI sobre cada head actual. P06–P11 siguen pendientes; producción sin activar.
