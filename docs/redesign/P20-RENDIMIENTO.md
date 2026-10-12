# P20 · Interacciones y lectura de autoridades

El precio de doce posiciones tardaba más de cinco segundos. La propuesta ahora
reutiliza lecturas dentro de su transacción y vuelve a resolver la autoridad en
la siguiente solicitud. No cambian fórmulas, listas congeladas, permisos de
escritura ni la separación entre compra privada y venta pública.

## Cambio

Las barras y refuerzos se precargan con las mismas reglas de tenant, color,
ambigüedad, unidad y longitud desconocida. Los costos completos se conservan
para el reprecio; se indexan en memoria solo durante la propuesta. Los modelos
técnicos ya validados se reutilizan y se retira una copia profunda redundante
después de deserializar JSON en un grafo independiente.

La política de lectura comercial conserva las membresías activas, los roles
OWNER/ESTIMATOR/WORKSHOP_MANAGER y la exigencia de MFA de
`private.current_user_org_ids()`. Evalúa ese conjunto una vez por sentencia,
evitando resolverlo para cada una de las 3.193 filas de costos del fixture.
Los permisos de escritura conservan sus reglas. Las regresiones comparan el
permiso anterior con el nuevo, los ocho pares rol/MFA, la revocación de acceso,
unidades, nueva autoridad entre propuestas y la precedencia/ambigüedad de stocks.

La espera del formulario pasa de 350 a 180 ms y conserva el rechazo de respuestas
anteriores. En Ajustes › Producción, el título del formulario pasa de h4 a h3
para mantener la jerarquía accesible bajo el h2 de la sección.

La revisión local usa una red Docker propia y el nombre del contenedor API.
El DNS de `host.docker.internal` ofrecía además una dirección IPv6 sin ruta;
nginx acumulaba esperas y devolvía 502. La guía conserva la base y ahora evita
ese salto por el host. Se comprueba la propiedad de la red antes de crear
contenedores; una red ajena se conserva. El arranque real de la guía y las
cuatro regresiones del stack pasan. La reutilización técnica sigue siendo
opcional para los repositorios que cumplen el contrato anterior.

Si la lectura de una posición falla, el editor muestra su causa y permite
Reintentar. El clic vuelve a consultar el mismo identificador dentro de la
misma organización; no guarda ni aplica cambios. El estado tiene un título
principal accesible y el área de diseño tiene un nombre para navegar con
lector de pantalla. Debajo de 1024 px, la regla de herramientas conserva su
prioridad frente al CSS compartido del portal: no crea filas implícitas que
dejen el dibujo sin altura. La lectura móvil mantiene ubicación/cantidad
bloqueadas y el dibujo visible.
Los controles de la cabecera conservan su ancho y la ruta de navegación
puede ocupar otra línea: el nombre largo del proyecto ya no empuja el Orb
fuera de 1024 px.

La comprobación inyecta un 502 solo en la lectura inicial y pulsa Reintentar
para obtener la respuesta real. Los POST de evaluación, preview de catálogo
y simulación se registran por separado; no se presentan como escrituras.
Se verifican ambos temas y los cuatro anchos con los detectores originales
y axe, tanto en Vite como en el build de revisión. La evidencia de
[error y recuperación](captures/aceptacion-final/ux/error-posicion/)
conserva las revisiones de cada corrida.

## Medición

Build de producción y APIs propios sobre
`b8e62295bdcbf04c2427b0420551cbb2c1a30eec`. Chromium, 1440 × 900, sesión real de
Auth, doce muestras calientes por interacción, sin gates ni capturas simultáneos.
Los percentiles usan rango más cercano: se ordenan las muestras y se toma
la posición ceil(n × p). Con doce muestras, p95 es la mayor observación.

| Interacción | p50 ms | p95 ms | Resultado |
|---|---:|---:|---|
| Abrir posición, obra de doce posiciones | 306,83 | 720,20 | PASA |
| Recalcular precio, incluidas espera y respuesta del motor | 916,48 | 971,85 | PASA |
| Abrir OT desde tablero de obra con cien posiciones/cien OT | 693,48 | 799,21 | PASA |

Se mide desde la acción hasta el editor visible con ubicación correcta, la
respuesta correspondiente al margen pedido y Aplicar habilitado, o la cabecera
exacta de la OT. Se esperan dos cuadros renderizados. El observador de pantalla
usa requestAnimationFrame para evitar la espera escalonada de las aserciones;
después se comprueban las mismas condiciones con Playwright.

Cada precio del editor termina entre muestras, fuera del tiempo de apertura.
Así no se acumula el SQL de editores abandonados por doce recargas consecutivas.
Los diagnósticos con ese trabajo acumulado y con la espera escalonada se
conservan; no se presentan como aprobados. El contrato de fabricación mantiene
una OT por posición. Se abre una OT real en una obra de cien posiciones.

La [medición](captures/aceptacion-final/rendimiento/interacciones.json) conserva
las doce muestras, revisión y protocolo. Los diagnósticos viven en el mismo
directorio. La comparación histórica del precio conserva p95 de 5.395,91 ms;
su cálculo se esperaba mediante la misma respuesta HTTP y botón habilitado.
La [línea base](captures/aceptacion-final/rendimiento/interacciones-antes.json)
conserva las dos series que terminaron sobre `b8450659`; la serie de OT no
terminó y no se presenta como una medición. El perfil de backend pasa de 947
a 131 consultas por propuesta. Ese perfil explica el cambio; las latencias
de la tabla corresponden al navegador y a la respuesta real.

## Pase editorial del alcance

Primera ronda: stocks por lote, costos por propuesta y modelos técnicos
reutilizados. Segunda ronda: permiso equivalente por sentencia, copia JSON
independiente sin duplicación y respuesta del formulario a 180 ms. La revisión
de Ajustes corrige además su orden de títulos. Se quitan lecturas y trabajo
redundantes que retrasaban una decisión; no se retira evidencia de cálculo.

El momento de firma sigue siendo la cascada del precio con su delta exacto.
La capacidad del §8 sigue respaldada por reprecio congelado, trazas y aprobación
humana. La matriz global de P20 acredita estados y presentación; el cierre
recaptura 24 vistas de Producción con los detectores originales: ocho del
dueño con el formulario y dieciséis estados de los otros dos roles.
No quedan hallazgos de accesibilidad, consola ni desbordes en esa selección.

Las decisiones de producto y las integraciones siguen documentadas en
[valores por defecto](../decisions/valores-por-defecto.md) y
[activación](../operations/ACTIVACION.md). La base usa datos DEMO: estas medidas
de rendimiento no certifican precios ni fabricación industrial.
