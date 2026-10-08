# P02 · identificadores humanos y presentación exacta

Estado: recorridos y documentos finales verificados en
`codex/P02-identificadores-humanos`, base `18c814bc`; gates locales PASA el
08-10-2026.
No se considera integrado hasta los cuatro checks del PR y squash.

Las compras, recepciones y retazos se nombran OC/REC/RT mediante alias inmutables
por organización. Los códigos, payloads, hashes y artefactos históricos no se
reescriben. La etiqueta física usa la identidad congelada del motor en web,
PDF de corte y producción, CSV, DXF, etiqueta y QR. Se conserva el contrato
numérico CNC; la interfaz y el papel usan el formato de `ENGINEERING.md`.

## Evidencia de dominio

`scripts/verify_human_codes_flow.py` recorre el stack real propio: compra,
recepción/replay, doce OT de una revisión, exportaciones, etiquetas/QR, retazo y
búsqueda. `recorrido/http-flow.json` y los archivos por OT permiten repetir la
comparación. Los conjuntos planificados son iguales en web/PDF de corte/CSV/DXF/
etiquetas; son 646 códigos físicos en doce OT, no una OT ficticia con doce
posiciones. El pack completo de producción se compara contra todas las piezas
congeladas de cada posición: incluye además 30 referencias sin solución de
corte, con su causa, que no se exportan a una máquina. La matriz unitaria
comprueba además 96 códigos de doce posiciones con formatos combinados.

Ocho regresiones PostgreSQL cubren concurrencia, rollback, independencia por
organización, replay, permisos, inmutabilidad y búsqueda/aislamiento. Diecinueve
pgTAP comprueban el contrato de alias. `check_human_codes_upgrade.py` se incorpora
al gate PostgreSQL 16 para el backfill poblado conservando filas completas.

## Gates finales

`make lint typecheck test build` pasa con 744 pruebas del motor (+2 xfail),
1.249 del backend y 817 del frontend tras las correcciones de revisión.
OpenAPI/orval y guardas reproducibles;
fórmulas y goldens intactos. `make test-db` pasa completo: 1.156 pgTAP en 79
fuentes, 403 integraciones PostgreSQL y 11 E2E de Chromium. Nueve verificadores
de PostgreSQL 16 cubren diez recorridos de upgrades poblados, incluido P02.
El backfill conserva las ocho tablas
históricas comparadas y continúa OC-000004.

El primer intento del gate DB tras reiniciar Docker encontró vacío el bind
de pgTAP del daemon. Se restauraron sus 79 fuentes y se verificaron byte a
byte; el segundo intento completo pasa. No se cambió un check ni el SQL para
corregir el entorno. El gate detuvo y limpió su stack aislado; la aplicación
propia permanece detenida durante el gate. El PR
[#128](https://github.com/KaraAliOsman/framedex/pull/128) pasó los cuatro checks
sobre `4f18e061`; las correcciones requieren una nueva corrida de CI antes del squash.

## Correcciones de revisión

La búsqueda de pieza consulta únicamente OT y trae como máximo 101 candidatos.
Si supera 100, rechaza la consulta antes de cargar snapshots y pide escanear el
QR con la OT. No presenta una página parcial como todo el historial. Las
direcciones QR y los códigos de unidad con OT siguen acotados a esa orden;
se conserva el filtro de identificador técnico histórico. Una dirección mal
formada se rechaza con detalle en español, sin responder 500. Iniciar otro
escaneo retira el resultado anterior y el mensaje, y un rechazo no deja piezas
de la consulta anterior visibles.

Las etiquetas de bulto conservan el manifiesto histórico. Si el plan no existe
o fue invalidado, las etiquetas de corte quedan vacías con su causa y la acción
«Revisar plan de corte». No se proyecta el snapshot en esos casos. Regenerar una
consulta válida sustituye el bloqueo; no se imprimen piezas obsoletas.

La observación de permisos se contrastó con `purchasing/views.py`: sus lectores
son dueño, estimador y jefe de taller. `orders_index`, `order_receiving` y la
paleta usan la misma autoridad documental. La integración comprueba lectura
de OC y REC antes de buscar por código con cada rol, y conserva aislamiento y
rechazo de operario/instalador. No se cambió un grant ni el permiso de Compras.

La matriz de revisión conserva 32 capturas adicionales en
`recorrido/revision/`, cuatro tamaños × ambos temas: dirección mal formada
contra la API real (ocho), límite que requiere OT (ocho) y etiquetas con plan
invalidado/ausente (dieciséis). Las dos últimas superficies usan intercepción
HTTP declarada; el límite de 101 OT se verifica en PostgreSQL y el bloqueo se
prueba en backend sin llamar a la proyección. Cero hallazgos numéricos, errores
de página o desborde. Recuperar el QR real limpia el error; abrir de nuevo las
etiquetas válidas repone las piezas y retira la causa. El enlace al corte usa
teal del tema y lleva al plan; su margen conserva la cabecera visible.
Se repitieron las ocho capturas/impresiones de unidad válidas y la lectura QR
de píxeles de ocho capturas, 24 PDF y cuatro impresiones: PASA.

## Navegador y edición

`frontend/scripts/verify-p02.mjs` prueba la paleta por OC/REC/RT/OT, la recepción
seleccionada, etiqueta de retazo, QR directo y URL escaneada en cuatro tamaños y
ambos temas. La escritura se protege en API/RLS; estimador consulta en solo
lectura y operario no accede a Compras. Los estados de carga/error/vacío usan
intercepción HTTP explícita; los flujos de negocio usan el fixture real DEMO.

La matriz formal de cinco rutas y ocho combinaciones conserva 40 capturas antes
y 40 después, además del recorrido. Los detectores siguen activos. Los hallazgos
anteriores del cromo y las pantallas pendientes se reportan con su baseline,
sin atribuir a P02 los rediseños posteriores de la cola.

Ronda 1: se quitaron los fallback de hash y UUID truncado; se unificó la etiqueta
por unidad física; se sustituyeron la cantidad y la medida crudas por el formato
de la magnitud. Ronda 2: se eliminó la interpretación errónea de campos de
presentación como datos del motor; se corrigió la apertura de recepción al cambiar
la dirección; se descartaron cargas anteriores y se preservó la identidad QR al
navegar. Los radios del índice usan tokens y se eliminaron dos aliases CSS muertos.
La revisión visual final corrigió el contraste del QR oscuro, el `viewBox` para
evitar recorte y su margen de lectura de cuatro módulos; las cantidades usan
`Qty` y las medidas Mono. Los colores/estrategias conocidos se nombran en español
sin alterar la identidad del catálogo. La impresión del retazo elimina el
contenido oculto de la maquetación: una página en ambos temas, con tinta sobre
papel. La impresión de piezas conserva todos sus QR y códigos.

Resultado final: 54 capturas del recorrido principal, ocho de unidades y dos
de impresión; cero UUID/hex/decimales largos, errores de página o desborde del
documento. Los 24 PDF finales conservan los conjuntos esperados y el formato.
`verify_human_codes_qr_pixels.py` decodifica ocho capturas de retazo, 24 PDF de
taller y cuatro impresiones del navegador; las dos impresiones de piezas
contienen exactamente sus 16 códigos planificados y la etiqueta de la unidad.
La matriz formal pasa sus 40 comparaciones con cero hallazgos numéricos,
firmas nuevas o desborde. Se conservan 96 ocurrencias adicionales de SKU DEMO
heredados (doce por captura de Compras), por las dos OC del recorrido real.

## Rúbrica editorial del cambio

PASA se refiere a la identidad, formato, navegación y etiqueta de P02. La
anatomía heredada de las pantallas se conserva por el alcance explícito del
encargo; los informes antes/después mantienen esos hallazgos para sus rediseños
y ED1/ED2. No se presenta esta aceptación como la aceptación de toda la UI.

| Regla | Resultado | Evidencia / alcance |
|---|---|---|
| R1 | PASA | Códigos/medidas/cantidades Mono; formatos de magnitud y moneda; CNC exacto. |
| R2 | PASA | Índice, filtros y etiqueta cambiados usan radios ≤4 px. Radios heredados se conservan en el baseline. |
| R3 | PASA | Etiqueta delimitada por borde; paleta única, sin elevación añadida. |
| R4 | PASA | Sin acento naranja nuevo; se conserva la marca y la falta real de material. |
| R5 | PASA | Tokens de acento teal y papel, iguales en ambos temas. |
| R6 | PASA | OC/REC/RT y piezas dictables; Blanco/Rápida; causas en español. |
| R7 | PASA | Lectura compacta; no se introduce inspector ni formulario técnico nuevo. |
| R8 | PASA | Carga/vacío/503 y retry, permisos reales, dirección ausente y OT con faltante. |
| R9 | PASA | Papel/tinta de etiquetas impresas y packs; QR blanco en el tema oscuro. |
| R10 | PASA | Dirección seleccionada con aria-current y foco; no brillo ni elevación nuevos. |
| R11 | PASA | Se conserva la iconografía y la geometría del motor; no se inventan ángulos. |
| R12 | PASA | Ctrl+K, campo/resultado de paleta, botones de etiqueta/impresión; foco de primitivas P01. |
| R13 | PASA | No se añade animación; se conserva reduce-motion del sistema. |
| R14 | PASA | Etiqueta → imprimir; navegación por código sin acción consecuente automática. |
| R15 | PASA | Fuente congelada y comparación de códigos; falta de identidad/medida explícita. |
| R16 | PASA | Sin degradado, blur, brillo o croma IA en el cambio. |
| R17 | PASA | Cero desborde de documento a cuatro tamaños; etiqueta/QR completos. Tablas anchas heredadas conservan scroll interno. |
| R18 | PASA | Dirección, escaneo, etiquetas, impresión y retry reales; aliases CSS muertos retirados. |
| R19 | PASA | F2: código humano y huella abreviada en el cajetín del pack. |
| R20 | PASA | Código como dirección por paleta/QR, autorizado por organización y rol. |

Firma F2: código humano y huella documental permanecen juntos en el cajetín.
La capacidad del §8 funciona como dirección: la paleta y el QR llegan a la misma
entidad con autorización de organización. No hay efecto consecuente automático.

## Límites

El fixture es DEMO; no certifica un catálogo ni el mecanizado de una máquina real.
Los PDFs ya emitidos conservan sus identificadores históricos por inmutabilidad.
Los IDs de columnas CSV/DXF son contratos de máquina; no son identificadores
visibles de taller. El resto de la anatomía de Compras/Producción continúa con
P11/P12/P13. P02 no conecta servicios externos ni modifica fórmulas o goldens.
El teléfono conserva el scroll interno de las tablas existentes; P02 no afirma
que esas pantallas ya cumplan la anatomía final. Las piezas sin autoridad de
stock/corte se muestran en el bundle y quedan fuera de la exportación CNC.
