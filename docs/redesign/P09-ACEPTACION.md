# P09 · propuesta DOC-01 v2

Rama `codex/P09-doc01-v2`, base `e80e91b8`. Verificación local 08-10-2026.

DOC-01 presenta emisor y cliente, resumen de posiciones, elevaciones acotadas,
campos y vidrio, sublíneas, totales, calendario y aceptación. Usa los precios y
autoridades sellados; el renderer no consulta el catálogo vigente. Carta, A4,
Oficio, acento, pie y condiciones se configuran para emisiones nuevas.

## Flujos verificados

| Flujo | Resultado y evidencia |
| --- | --- |
| Ajustes → calendario inválido → corregir → guardar → recargar | PASA. 40/50 se rechaza; 50/50, A4, Grafito y pie persisten. |
| Proyecto → precios del motor → preparación → clic de emisión A | PASA. PDF real Carta, revisión A y total sellado. |
| Crear sucesora → precios B → elegir A como alternativa → emitir B | PASA. Guardado mediante servicio y UI; A fuera del total, PDF B A4. |
| PDF → decodificar QR desde píxeles → portal de B | PASA. Enlace y revisión coinciden; comprobación de enlace PDF, sin token publicado. |
| Compartir enlace → volver al QR impreso | PASA. El enlace compartido no revoca el QR. |
| Revocar QR por UI → confirmar → portal revocado | PASA. El portal pierde acceso; los bytes de A y B permanecen idénticos. |
| Cambiar emisor, papel y acento después de emitir | PASA. Descargas A/B conservan SHA; preferencias restauradas. |
| Vacío, carga, error/reintento, sin permiso y bloqueado | PASA. Calendario sin hitos, transporte controlado, encargado sin escritura, falta de confirmación. |
| Teclado → condiciones legales → confirmación | PASA. Foco visible; emisión bloqueada antes del clic. |
| Renderer o upload fallido | PASA. Rollback sin aprobación, capacidad ni artefacto huérfanos. |

La matriz final tiene 44 vistas sin hallazgos ni desbordes: Ajustes y preparación
en 1440×900, 1280×800 y 1024×768, ambos temas, más portal en 390×844. El suplemento
registra condiciones, confirmación y teclado. Los runners oficiales recorren
Ajustes, proyecto y portal en cuatro tamaños y ambos temas.

[Capturas](captures/doc01-v2/) conserva PDF anterior, fixtures finales,
matrices, recorridos y reportes oficiales. Los PDFs públicos son sintéticos y
rotulados DEMO; usan enlaces `example.test`. Los documentos y las capacidades
del recorrido real permanecen en el directorio local ignorado.

## PDF y números

| Fixture | Páginas |
| --- | --- |
| 1 posición | 3 |
| 12 posiciones | 7 |
| 24 posiciones | 12 |
| 100 posiciones | 40 |
| 100 posiciones con cliente y ubicación de 120 caracteres | 45 |
| 12 posiciones A4 / Oficio | 7 / 7 |

PyMuPDF comprueba las cajas de las tablas, contenido de todas las páginas,
folio/revisión/paginación, moneda USD, total del motor, ausencia de costo/margen
y hex fuera del pie, tamaño de papel y Plex embebida. El QR se decodifica desde
el raster, con enlace idéntico al impreso. Se inspeccionaron las siete páginas de
doce posiciones y muestras de las densidades y papeles restantes. La revisión
final incluye A4/Oficio, acabado bicolor y conjunto de tres módulos. Los nombres
de módulo también aparecen en la ficha con al menos 8,25 pt: no dependen del
tamaño reducido de una elevación con muchas cotas. Se conserva el texto de
acabado por caras de D05 y su advertencia de tono aproximado.

El motor calcula unitario mostrado, ajuste de redondeo, descuento con autoridad
y reparto de hitos cuya suma es exactamente el total. Una sublínea fraccionaria
conserva su ajuste exacto, incluso en CLP. Un texto histórico no se interpreta
como porcentaje ni inventa calendario. Composición/Ug se imprimen solo cuando
existe su autoridad; el PDF omite los datos técnicos desconocidos.

## Dos rondas editoriales

Primera: reemplazar el layout anterior y sus CSS muertos; retirar tarjetas,
cebra, cifras decorativas y página de leyenda aislada. Colocar la leyenda con
las fichas y separar las columnas monetarias. Aumentar cotas y hacer legible la
planta por carril y hoja, sin duplicar una planta diminuta en el detalle.

Segunda: ampliar la elevación representativa de portada; eliminar su planta
duplicada y conservarla en detalle. Dar dos columnas a Documentos en Ajustes,
una a sus condiciones durante la preparación y foco con tokens. Corregir
desborde del resumen al abrir Cotización apilando las referencias a la derecha;
normalizar nombres de criterio y radios de checklist/veredicto. Compartir
distingue el QR del enlace que sí reemplaza.

| Rúbrica | Estado | Evidencia del alcance P09 |
| --- | --- | --- |
| R1 · Números | PASA | Plex Mono, mm, CLP/USD y reparto exacto del motor. |
| R2 · Radios | PASA | Tokens ≤4 px; checklist/veredicto corregidos. |
| R3 · Jerarquía | PASA | Filetes, blanco, peso y cajetín; fichas sin tarjetas anidadas. |
| R4 · Naranja | PASA | Solo avisos que requieren persona; PDF sin ornamento naranja. |
| R5 · Teal | PASA | Acentos de paleta y foco de tokens; Grafito configurable. |
| R6 · Voz | PASA | Cliente tratado de usted; nombres de criterio legibles. |
| R7 · Densidad | PASA | Ficha completa/compacta/densa; 100 posiciones en 40–45 páginas. |
| R8 · Estados | PASA | Cinco estados con causa y recuperación, permisos reales. |
| R9 · Papel | PASA | Hoja blanca y tinta técnica, formatos declarados. |
| R10 · Selección | PASA | Alternativas por checkbox/foco, sin efectos decorativos. |
| R11 · Símbolos | PASA | Renderer común P05, vista interior, planta de corredera separada. |
| R12 · Teclado | PASA | Selectores etiquetados, foco y suplemento de teclado. |
| R13 · Movimiento | PASA | Sin animaciones nuevas; reduce-motion conservado. |
| R14 · Principal | PASA | Guardar documentos y emitir en regiones propias. |
| R15 · Fuente | PASA | Motor/snapshot; Ug con fuente, desconocidos omitidos del PDF de cliente. |
| R16 · Efectos | PASA | Detectores oficiales y matriz sin efectos prohibidos. |
| R17 · Anchos | PASA | Tres tamaños de oficina, portal 390, tablas sin colisiones. |
| R18 · Acciones | PASA | Guardar, emitir, alternativa, compartir, revocar y descargar reales; layout viejo retirado. |
| R19 · Firma | PASA | F1/F2/F11: filete, inglete y folio/huella como plano. |
| R20 · Techo | PASA | Densidad automática, vidrio autoritativo y calendario calculado. |

## Gates y límites

OpenAPI/orval regenerados. Golden nuevo de proyección comercial sin modificar
los resultados históricos. Lint, typecheck, test y build completos pasan;
55 casos focalizados, siete integraciones PostgreSQL P09 y las 19 regresiones
finales de PDF/acabado/conjuntos también pasan. La corrida final y Database Gate
se registran antes de integrar el PR.

Decisiones en [valores por defecto](../decisions/valores-por-defecto.md) y pasos
de conexión en [ACTIVACION](../operations/ACTIVACION.md). No hay proveedor
externo nuevo: QR usa el portal existente y almacenamiento inmutable.

Riesgos: el catálogo DEMO no certifica un fabricante. Los artefactos históricos
conservan sus bytes y pueden conservar el layout anterior. Una revisión con
muchas alternativas o textos legales extensos puede superar 45 páginas; el
límite probado corresponde a las 100 posiciones del contrato. Sin Ug/plazo/
garantía declarados se omite la línea, sin inventar autoridad. P07 conserva el
workspace de precios, P08 el flujo comercial y P06 el de conjuntos/bow.
