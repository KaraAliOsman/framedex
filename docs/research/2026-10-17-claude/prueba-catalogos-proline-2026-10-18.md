# Prueba del importador con PDF reales Proline / Aluminios 2000 · 18-10-2026

Los archivos los aportó el dueño en la conversación. **No se copian al repositorio** (documentos de terceros); se registran por nombre y huella.

| Archivo | SHA-256 | Tamaño | Páginas |
|---|---|---|---|
| `ilide.info-plantilla-de-corte-ventanas-de-pvc-proline-pr_…pdf` (plantilla de corte Aluminios 2000 / Proline) | `bf16d500eae5b7f2af9bef2f983b987acc4e0fda63c6c8fa499ed47ae4ac816f` | 0,87 MB | 25 |
| `CATALOGO-PERFILES-DE-PVC.pdf` (catálogo de perfiles Proline, aluminios2000.com) | `b2732493f1981cbc0f7a595104a1603bbc4bafe76a6e625ab5a3119bfe755cfe` | 18,4 MB | 24 |

## Qué se probó y con qué alcance

Se ejecutó en local, sin pila ni proveedor de IA: inventario de páginas, partición en lotes, render de páginas para el proveedor, analizador determinista de plantillas de corte y la orquestación por lotes con un proveedor **simulado** (incluido un lote que falla y su reintento). **No se ejecutó la extracción con el modelo real**: requiere la configuración del proveedor y la pila del dueño. Por eso no se afirma qué lecturas hará la IA ni su exactitud.

## Hallazgos que cambiaron el código

1. **Ambos superan 20 páginas.** El importador anterior los rechazaba (`ai_source_page_limit` del helper multimodal). Ahora se procesan en lotes internos: plantilla 4 lotes, catálogo 4 lotes de 6 páginas.
2. **Capa de texto corrupta** (catálogo p. 2: fuente con codificación rota, «símbolos»). Se marcaba como «texto» y la imagen no se leía. Se añadió `text_quality`: texto ilegible ⇒ la página también se lee como imagen.
3. **Dibujos técnicos vectoriales** (catálogo p. 3–19: secciones con cotas, hasta 126 000 trazos y ~25 caracteres de texto). No son imágenes, por lo que se clasificaban «texto» y la IA habría recibido solo «PRO6004 60 MM». Ahora poco texto o muchos trazos ⇒ lectura visual. Las 24 páginas del catálogo se leen como imagen (1,3–1,6 MB por lote, ~1,5 s de render).
4. Las cotas de esas páginas no tienen capa de texto: cualquier lectura de la IA quedará **«lectura dudosa»** hasta contrastarla con la página, que se muestra al lado en la revisión. Es el comportamiento correcto: una lectura visual no es autoridad.

## Plantilla de corte: ejemplos, no reglas

`ingest/cut_examples.py` lee las hojas de corte de forma determinista: 18 hojas, uniendo tablas que continúan en la página siguiente (13–14, 15–16, 17–18, 20–21). Líneas: PROLINE PRO6004 y PRO SLD-70. Perfiles: PRO01, PRO04, PRO05, PRO10, PRO12, PRO201, PRO204, PRO211, PRO213, PRO521, PRO703, R1, R2, R3, R5.

Desplazamientos constantes entre ejemplos de distinto tamaño (observaciones para revisión técnica, **no publicadas como reglas**):

| Línea | Perfil | Lado | Cortes | Largo respecto a la medida | Ejemplos |
|---|---|---|---|---|---|
| PRO6004 | PRO01 marco | Alto | 45°/45° | +5 mm | 11 |
| PRO6004 | R1 refuerzo | Ancho | 90°/90° | −108 mm | 16 |
| PRO6004 | PRO01 marco | Alto | 45°/90° | +3 mm | 5 |
| PRO6004 · proyectante | PRO01 / PRO521 / R1 / R2 | varios | — | +5 / −67 / −108 / −212 mm | 2 c/u |

Inconsistencias de la propia fuente, señaladas y no corregidas:

- Págs. 15–16: seis medidas con `#NAME?` (error de planilla) en vez de número.
- Págs. 19 y 20–21: el título dice «Puerta doble exterior con solera» pero los perfiles son de corredera SLD-70.
- Págs. 20–21: posiciones de las filas en otra página.

Uso previsto: cuando las reglas de corte de PRO6004 estén declaradas, comparar el corte que calcula DEKOPEN con estos ejemplos («conciliación con la plantilla del fabricante»). Pendiente de la etapa 07.

## Qué falta para afirmar importación correcta

- Ejecutar la extracción con el proveedor real sobre ambos archivos y revisar campo por campo contra las páginas.
- Declarar y revisar reglas de corte de PRO6004 con autoridad técnica; luego conciliar con las 18 hojas.
- El catálogo comercial no trae precios ni reglas de fabricación: aunque se importe bien, servirá para biblioteca y diseño, no para corte certificado.
