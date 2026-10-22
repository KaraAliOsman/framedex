# P03g · Diferencias entre las dos lecturas del manual

Verificación local del 22-10-2026 en `gpt/dk2-p03g-asistente-serie`, sobre
P03f. Esta entrega prepara la revisión documental; P03 sigue en curso.

## Flujo ejercitado

La revisión abre en las diferencias, con los acuerdos resumidos como propuestas.
Cada diferencia conserva las dos lecturas, página, cita y valor literal. Elegir
una lectura cambia el borrador; incluir la fila y publicar son decisiones
distintas. Los datos ausentes no se rellenan. Una lectura dudosa o una corrección
libre se presenta como dato del taller, conforme al contrato de P03c.

El E2E usa dos respuestas de modelo simuladas, parseadas y comparadas por el
backend, y almacenamiento, autenticación Magic Link/TOTP, revisión, publicación
y PostgreSQL reales. Comprueba un campo discrepante, los acuerdos sin editores
individuales, ausencia de escritura antes del clic, token de revisión y cambio
de soldadura de 3 a 4 mm con origen MANUAL al elegir la lectura citada. No es
una medición de calidad del proveedor de IA ni una afirmación sobre PRO6004 real.

Los enlaces de una fuente abren directamente su revisión. Ya no esperan la
descarga de todos los sistemas, perfiles, vidrios y kits del catálogo avanzado;
el E2E comprueba que no se soliciten esas cuatro colecciones. El catálogo
avanzado conserva su importador completo y los enlaces con `advanced=1`.

## Comparación visual

El mockup `Prueba.dc.html` gobierna la ventana de prueba, cubierta en P03e.
Para este paso documental se conserva su jerarquía de tarea única: diferencias,
valor revisado y confirmación. A 1440 px las citas aparecen en dos columnas; en
móvil se apilan en orden de lectura. Los acuerdos y los demás campos quedan a
un clic, sin obligar a revisar todos los campos del manual.

Capturas seleccionadas e inspeccionadas:

| Archivo | Qué verifica |
|---|---|
| `manual-real-1440.png` | Revisión con sesión real y ambas lecturas simuladas |
| `manual-real-390.png` | La misma capacidad dentro del shell móvil |
| `ejemplo-1440.png` | Citas simultáneas, elección e inclusión separadas |
| `extremo-390.png` | Identificador y archivo largos, cita extensa y lectura dudosa |
| `texto-200-320.png` | Texto al 200 % sin desbordar la página |
| `500-filas-1440.png` | Diez filas por página, con 500 propuestas disponibles |

## Extremos y correcciones

Se ejercitaron 0, 1 y 500 filas, códigos con ceros iniciales, Unicode,
archivo de nombre largo, cita extensa, profundidad de ensayo `200.00` mm,
identidad ambigua y valores booleanos/compuestos. Ningún identificador se
convierte a número. Una fila incluida puede excluirse después de borrar su
valor discrepante; comparar queda bloqueado si conserva diferencias sin resolver.

Los tres ensayos de navegador cubren 1440×900, 390×844 y 320×844, texto al
100/200 %, ancho de página y axe A/AA/2.1 AA. El ensayo de producto detectó un
contraste insuficiente en la fecha heredada del importador; se cambió al token
de texto secundario. No se añadieron transiciones ni movimiento a las cifras.

El montaje local DEV quedó entre 704 y 750 ms; cambiar los conjuntos tardó
entre 28 y 220 ms, incluyendo elegir e incluir una lectura cuando correspondía.
El enlace con sesión iniciada abrió en 1.112 ms a 1440 px y 1.085 ms a 390 px.
Son mediciones locales de Playwright; no se atribuyen a CWV de producción.

Validación final: 1.209 pruebas frontend, 19 dirigidas de la revisión y su ruta,
dos E2E de publicación real y tres ensayos de extremos aprobados. ESLint,
TypeScript, Prettier, Ruff de las fixtures, guardas de fuente y build aprobados.
Las medidas se presentan con coma decimal sin alterar la cadena elegida; las
citas y los códigos conservan su texto literal.

## Límites

Quedan pendientes el asistente reanudable de cinco pasos, la preselección de la
serie en la primera obra y el E2E integral de alta desde plantilla. La lectura
real con el proveedor de IA se mantiene como una capacidad separada; estas
pruebas de revisión usan resultados simulados explícitamente sintéticos.
