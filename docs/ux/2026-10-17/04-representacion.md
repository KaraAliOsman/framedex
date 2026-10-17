# Representación: que una ventana parezca una ventana real

[Volver al plan](README.md)

## Resultado buscado

Una ventana debe comunicar sistema, construcción, apertura, vidrio y acabado en
miniatura, al editarla y al presentarla. Una vista técnica debe servir para
entender la geometría; una comercial debe ayudar a imaginar el producto. Ambas
proceden del mismo modelo evaluado.

No se propone usar imágenes generadas por IA como reemplazo del producto
paramétrico. Pueden servir como referencia de ambiente, nunca como prueba de
dimensiones, compatibilidad, sección o fabricación.

## Diagnóstico confirmado

| Observación | Evidencia | Trabajo necesario |
|---|---|---|
| Nogal exterior aparece marrón plano en el caso revisado | Stack REVIEW, [captura](evidencia/editor-3d.jpg) | Revisar activo, carga, fallback, UV y luz; no culpar solo al color. |
| El producto se ve pequeño en un escenario grande | Misma captura | Encuadre por límites visibles y tarea. |
| Extremos rectos en el perfil 3D | Comentario y `memberBar` de `Product3DScene.ts` | Representar corte/encuentro declarado. |
| Existen texturas y material físico | `finishMaterials3d.ts` | Completar datos/activos y su mapeo; no reescribir por desconocimiento. |
| Extrusión sin mapeo propio por mm en módulos inspeccionados | `scene3dGeometry.ts` | Coordenadas UV ligadas al miembro y su acabado. |
| SVG 2D ya contiene lógica de uniones/acoples | `ProductFrontSvg.tsx` | Mejorar geometría/jerarquía donde falle; conservar lo correcto. |
| Secciones del demo no bastan para mostrar un producto comercial real | Catálogo/fixture observado | Preparar sistemas reales con autoridad y activos. |

## Arquitectura visual común

```text
Modelo de producto + catálogo versionado + resultado del motor
                           ↓
   miembros · secciones · juntas · caras · vidrio · herrajes · poses
                           ↓
             escena/elevación común con identidad estable
               ↙               ↓                  ↘
        SVG técnico       escena 3D          vista comercial
               ↘               ↓                  ↙
          editor · miniaturas · PDF · portal · materiales
```

El renderer convierte a coordenadas gráficas para dibujar; los números de cotas,
cortes, cantidades y precios siguen viniendo del resultado Decimal. El float
gráfico no se convierte en una nueva autoridad de fabricación.

## Uniones y encuentros

La solución no es dibujar diagonales de 45° en todos los rincones. Hay ingletes,
uniones a testa, soldadura, uniones mecánicas, encuentros en T, postes, inversores,
acoples y distintas familias de marco/hoja/umbral.

| Encuentro | Comportamiento visual | Dato que debe gobernarlo |
|---|---|---|
| Esquina de marco/hoja con inglete | Extremos y línea de junta coherentes; veta sigue cada barra | Tipo y ángulo de unión del sistema/resultado. |
| Soldado PVC | Junta perceptible a escala apropiada, sin simular un herraje inexistente | Unión y acabado declarados; apariencia representativa. |
| Testa mecánica aluminio | Continuidad y tapado correctos, sin diagonal ficticia | Conexión de los perfiles. |
| Montante/travesaño | Intersección coherente con qué miembro pasa y cuál llega | Regla de encuentro y orientación. |
| Doble hoja / inversor | Solape, apertura activa/pasiva y cierre legibles | Composición y apertura del producto. |
| Corredera | Carriles, solapes y hojas en su plano de desplazamiento | Sistema, carril y mano. |
| Umbral/puerta | Zócalo, umbral y continuidad adecuados al sistema | Componente real, no marco repetido. |
| Conjunto angular/bow | Acople visible y orientación en planta | Módulos, ángulos y acoples del motor. |

En 3D, elegir una representación determinista de extremos por planos de corte o
mallas paramétricas; evitar una dependencia CSG pesada si las formas se pueden
construir directamente. La estrategia exacta se decide con las secciones del
catálogo real. Resolver normales, caras internas, solapes y z-fighting como parte
del modelado, no con trazos que oculten errores de malla.

Si falta el dato de junta, el sistema puede dibujar una representación esquemática
honesta. No publicar una supuesta solución de fabricación deducida de un render.

## Secciones y profundidad

- Usar contornos reales con sus huecos/cámaras cuando estén disponibles y
  confirmados. Respetar origen, ejes, cara interior y orientación del perfil.
- Separar nivel de detalle: miniatura sencilla, editor medio, sección ampliada
  detallada. Mantener dimensiones y silhouette coherentes entre niveles.
- La sección debe abrirse desde el elemento y señalar dónde corta, con escala,
  orientación y leyenda de materiales.
- Mostrar refuerzo, juntas y calzos cuando existan datos y sean relevantes para
  esa vista. No representar todos los productos con las mismas cajas.
- Un PDF con un croquis sin escala no permite derivar una sección industrial
  exacta. Puede aportar una ilustración con fuente y estado pendiente.
- La geometría comercial puede tener un tratamiento visual de arista sutil,
  sin alterar el tamaño técnico ni introducir descuentos de corte.

## Acabados y materiales

### Biblioteca de activos

Cada acabado necesita nombre humano, fabricante/referencia cuando exista, caras
admitidas, muestra visual y procedencia del activo. Para madera/foliado: textura
realista con escala y dirección; para lacado/polvo: base y rugosidad adecuadas;
para anodizado: reflejo y respuesta metálica razonables.

Preferir activos del proveedor o de producción propia con derecho de uso. Un
catálogo puede contener una muestra pequeña insuficiente para texturizar una
barra sin repetición evidente: se conserva como muestra, no se promete un PBR
completo extraído mágicamente.

### Mapeo y luz

| Aspecto | Decisión |
|---|---|
| Dirección | Veta paralela al eje longitudinal de cada perfil; rotación coherente en horizontales. |
| Escala | Repetición en unidades de modelo/mm, con tamaño de muestra declarado. |
| Esquinas | Cada barra conserva su veta hasta el inglete; no estirar una textura única alrededor del marco. |
| Dos caras | Interior/exterior/base asignados por cara; cantos y caras de sección coherentes. |
| Color | Gestión de espacio de color para base color; mapas de datos tratados como datos. |
| Material | Rugosidad/metallic/normal sobrios cuando haya activos; no convertir blanco PVC en cromo. |
| Luz | Entorno neutro, sombras suaves y exposición estable; comparar acabados bajo la misma luz. |
| Fallback | Color representativo cuando falta mapa, con indicación contextual breve. |
| Captura | Esperar activos antes de producir una miniatura final; no guardar el fallback como textura definitiva. |

El color en pantalla y en impresión es una representación; la muestra física
sigue siendo referencia de elección fina. Esta aclaración puede vivir en el
muestrario/documento, sin un aviso enorme permanente en el editor.

### Selector de acabado

Muestrario con muestras reales, nombre y referencia; búsqueda; interior/exterior
claros; opción «igual en ambas caras»; compatibilidad filtrada; vista previa sobre
la selección. Distinguir acabado base, laminado/foliado, pintura y herraje.
Los cambios de costo se obtienen del motor/política de precios y se muestran
antes de aplicar un cambio amplio.

## Vidrio y apertura

El vidrio necesita bordes y profundidad adecuados a la composición, reflejo
controlado y transparencia suficiente para entender la ventana. Evitar azul/cian
saturado como sustituto universal. Bajo emisivo, opaco, satinado, panel y laminado
pueden necesitar tratamientos distintos, siempre con leyenda y datos reales.

El dibujo de apertura se mantiene en 2D con una gramática consistente y una vista
declarada. En 3D, bisagras/manilla/hoja deben moverse con la pose correcta. Una
corredera no gira como practicable. Una oscilobatiente necesita sus poses, no un
simple giro intercambiable. Mostrar margen de recorrido y colisiones solo si hay
soporte geométrico suficiente; no vender una animación como simulación certificada.

## Vistas que merecen existir

| Vista | Objetivo | Contenido prioritario |
|---|---|---|
| Diseño 2D | Medir, dividir, seleccionar, configurar | Cotas necesarias, aperturas, uniones y selección discreta. |
| Presentación 3D | Entender aspecto y movimiento | Materiales, encuadre, apertura y caras. |
| Técnica | Comprobar construcción | Secciones, miembros, referencias y datos respaldados. |
| Sección / detalle | Comprender encuentro | Plano de corte, escala y componentes. |
| Materiales | Localizar lo que se fabrica/compra | Selección cruzada y cantidades con alcance. |
| Documento comercial | Vender sin sobrecarga industrial | Imagen limpia, medidas/rasgos pactados y precio. |

No mantener pestañas redundantes que solo cambian una etiqueta. Muro, detalle,
despiece o corte se abren si aportan algo a esa tarea.

## Familia representativa de diseño

La implementación debe trabajar con una colección pequeña pero variada que
exponga problemas reales: fijo, practicable, oscilobatiente, doble hoja con
inversor, corredera de varios paños/carriles, puerta con umbral, composición con
montante/travesaño, conjunto angular, arco y producto con dos caras de acabado.
Familias HST/PSK/plegable/pivot/vertical deben usar sus datos reales cuando estén
disponibles; no se aprueban por parecerse a otra familia.

Persianas, mosquiteros, ventilación, paneles, zócalos y accesorios visibles se
incluyen cuando el catálogo/modelo los soporte. Antes de prometerlos como una
carencia implementable, verificar contrato, geometría y BOM actuales. Un accesorio
que modifica luz/paso no puede ser una pegatina sin consecuencia.

## Criterios de terminación del trabajo visual

En la campaña final: reconocer familia/apertura sin leer un enum; distinguir
acabados; comprobar las dos caras; ver encuentros sin fisuras ficticias; comparar
miniatura/editor/PDF/portal de la misma revisión; verificar que selección/cotas
no tapan el producto; y revisar apertura real en varios dispositivos.

No se exige una suite de screenshots por cada ajuste. Se diseña sobre esta
colección durante la construcción y se concentra la aceptación al final.
