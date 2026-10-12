# Marca DEKOPEN · la sección de perfil

La dirección B del estudio de identidad es la firma del producto: una sección
hueca sustituye la O de DEKOPEN. La constitución manda sobre los estudios
históricos, incluidas sus propuestas de degradado y animación del Orb.

## Construcción

La grilla tiene 24 × 24 unidades. El exterior ocupa toda la grilla, con radio de
2 unidades; la pared tiene 2,5 unidades. Un tabique de 2 unidades, centrado en
x = 8, divide el hueco a un tercio del ancho. Los huecos usan `fill-rule:evenodd`.
La marca tiene una sola tinta: grafito sobre claro, paper sobre oscuro; el
favicon claro usa teal-800. No depende de una fuente instalada.

El logotipo usa IBM Plex Sans SemiBold 600, mayúsculas, con tracking de 0,06 em.
`scripts/build_brand_assets.py` convierte la fuente WOFF2 autoalojada en
contornos y ajusta la altura de las mayúsculas a 24 unidades. La O ocupa el mismo
alto y se reemplaza por la sección. El generador conserva el resto de los glifos
Plex; `wordmarkGeometry.ts` alimenta el componente React y los SVG de distribución.

| Uso | Mínimo | Protección |
| --- | --- | --- |
| Marca aislada | 16 px | 6 unidades de la grilla por lado |
| Logotipo | 72 px de ancho | Un cuarto de su altura por lado |
| Bloqueo de documento | 80 px de ancho | Un cuarto de la altura de letra por lado |

Por debajo de 24 px la pared crece de 2,5 a 3 unidades y el tabique de 2 a 2,25
unidades. Su centro continúa en x = 8. A 16 px se obtienen dos píxeles de pared
y 1,5 de tabique; se conservan los dos huecos. El SVG del favicon emplea esta
geometría óptica porque una pestaña lo muestra a 16 px. Los PNG de 32 a 512 px
usan la geometría normal. La prueba visual está en `/dev/marca`, con tamaños
16, 24, 32, 72 y 160 en ambos temas.

La zona de protección pertenece al contenedor: una superficie estrecha puede
usar la marca aislada, pero nunca reducir el logotipo bajo 72 px ni estirarlo.

## Aplicación

`BrandMark`, `Wordmark` y `DocLockup` viven en `frontend/src/brand/Brand.tsx`.
La cota de la dirección D pertenece exclusivamente a Acerca de y correos
internos. El shell, acceso, onboarding y etiquetas usan el logotipo B.
Las láminas de vacío son dibujos distintos de la marca: elevación sin posiciones,
barra sin cortes, hoja ausente y conexión interrumpida.

El Orb mantiene su API y su vínculo con trabajos reales. Grafito y una órbita
teal forman su cuerpo; aprobación, error y finalización conservan sus estados
semánticos. Sus poses son estáticas. No tiene brillos ni bucles decorativos.

DOC-01, portal y correos al cliente usan el emisor sellado. El color solicitado
debe ser hexadecimal de seis caracteres y alcanzar 4,5:1 contra paper; de lo
contrario se usa teal-800 y Ajustes avisa. Las preferencias de atribución se
sellan al emitir: documentos ocultos, portal visible y discreto por defecto.
Una modificación posterior no cambia documentos ni enlaces de revisiones
anteriores. Una emisión nueva sin identidad dice «Emisor sin identificar».

## Usos prohibidos

| Ejemplo rechazado | Motivo | Uso válido |
| --- | --- | --- |
| O tipográfica junto a la sección | Duplica la O y cambia el nombre | La sección reemplaza la O |
| Sección girada, en perspectiva o con pared afinada | Pierde la geometría del perfil | Grilla original y tinta plana |
| Logotipo de 48 px | Se pierde el tabique | Marca aislada de 16 px o logotipo de 72 px |
| Gradiente, resplandor, sombra o contorno del logotipo | Contradice la constitución | Relleno monocromo |
| Cota D en todos los encabezados | Convierte la firma en decoración | B en producto; D en Acerca de/correo |
| Marca de plataforma en un correo comercial | El fabricante es el emisor | Logo/nombre/color sellados de la organización |
| Cambiar el logo de un PDF antiguo | Rompe la autoridad emitida | Nueva revisión con identidad nueva |

## Reproducción

Ejecute el generador Python en el entorno de desarrollo y después
`node frontend/scripts/build-brand-icons.mjs`. El segundo comando rasteriza en
Chromium las variantes claras/oscuras 16/32/180/192/512 y el bloqueo PNG del
correo. Los PNG se commitean; el build no requiere red ni conversión de fuentes.
`manifest.webmanifest` declara DEKOPEN, teal-800 y g-50. La app actualiza favicon,
ícono Apple y color de tema al cambiar tema; el portal adopta el logo del emisor
y un favicon neutral cuando no hay logo.
