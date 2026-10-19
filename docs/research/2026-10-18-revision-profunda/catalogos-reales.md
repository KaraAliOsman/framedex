# Catálogos reales y experiencia por fabricante

El objetivo es que la biblioteca normal tenga proveedores y series reconocibles, útiles para trabajar. Un PDF público aporta evidencia; no publica automáticamente un sistema fabricable. Esta fase no importó, modificó ni borró datos operativos.

## Jerarquía visible

```text
Catálogos
  Proline
    PRO6004
      Configuraciones compatibles
      Perfiles / refuerzos / juntas / junquillos
      Vidrios / herrajes / acabados
      Documentos fuente y versión
    PROSLIDE70
      ...
  Winhouse
    Diamond 60
    Opal 70
  Indalum
    Superba 33 RPT
    Superba 44 RPT
```

Es una propuesta basada en familias publicadas; no declara que todas estén implementadas ni homologadas para la empresa del usuario. “60” o “70” son agrupaciones de lectura; la clave técnica conserva el código exacto. Una serie corredera no se fusiona con una practicable por compartir profundidad nominal. Distribuidor, fabricante y titular de la fuente se identifican por separado.

## Fuentes públicas concretas

| Fabricante/fuente | Referencia | Uso y límite |
|---|---|---|
| Proline | [Productos](https://www.prolinepvc.com/en/products) | Permite identificar PRO6004, familias 70 y PROSLIDE70, entre otras. No se supone equivalencia entre familias. |
| Proline | [Catálogo PDF](https://www.prolinepvc.com/catalogue/Proline_PVC_Catalogue.pdf) | Edición impresa identificada 20200303; no se etiqueta como la más reciente sin confirmación. |
| Proline en Chile | [Distribuidor](https://www.proline-pvc.com/) | Dominio y función comercial distintos del fabricante; confirmar quién mantiene datos locales. |
| Winhouse | [Biblioteca técnica](https://www.winhouse.com.tr/en-us/architects-engineers/technical-brochures) | Fuente de folletos de series; no demuestra correspondencia con cualquier marca similar. |
| Winhouse | [Diamond 60](https://www.winhouse.com.tr/en-us/pvc-window-and-door-system/diamond-60-pvc-series/main-profiles) y [Opal 70](https://www.winhouse.com.tr/en-us/pvc-window-and-door-system/opal-70-series-pvc-windows/main-profiles) | Puntos de partida para dos fichas de serie con perfiles identificados. |
| Winhouse | [Catálogo](https://www.winhouse.com.tr/cmsfiles/documents/winhouse-en.pdf?v=43) | Conservar versión/fecha del archivo obtenido antes de extraer reglas. |
| Deceuninck Chile | [Catálogos](https://www.deceuninck.cl/nuestros_catalogos.html), [medios](https://deceuninck.cl/nuestros_medios.html) | Referencia local de presentación y documentación; aprobar sistema y artículos concretos por separado. |
| Térmico Perfiles | [Centro técnico](https://termicoperfiles.cl/centro-tecnico/catalogos) | Fuente local de aluminio; verificar sistema y edición por documento. |
| Indalum | [Catálogos](https://www.indalum.cl/fabricantes-minisite/catalogos/40), [manuales](https://www.indalum.cl/arquitectos/manuales/39) | Separar página comercial de detalle de fabricación vigente. |
| Indalum | [Superba 33 RPT corredera](https://indalum.cl/soluciones/puertas-ventanas/superba-33-rpt-ventana-corredera-antepecho-y-piso-cielo/4-5), [Superba 44 RPT](https://indalum.cl/soluciones/puertas-ventanas/superba-44-rpt-ventana-fija-proyectante-y-abatible/4-6) | Dos familias de uso distinto; no derivar apertura por el nombre sin receta aprobada. |

El nombre dicho por el dueño, “Vinhaus”, es ambiguo. **Winhouse** de Turquía, **Winhaus.cl** y la relación comercial “Winhouse by Haustek” no se equiparan automáticamente. El importador debe resolver identidad/fuente antes de crear una marca duplicada o atribuirle datos de otra empresa.

## Material Proline del dueño

La investigación anterior identificó `CATALOGO-PERFILES-DE-PVC.pdf` (24 páginas, SHA256 `b2732493f1981cbc0f7a595104a1603bbc4bafe76a6e625ab5a3119bfe755cfe`) y las planillas de corte (25 páginas, SHA256 `bf16d500eae5b7f2af9bef2f983b987acc4e0fda63c6c8fa499ed47ae4ac816f`). Véase [prueba fechada](../2026-10-17-claude/prueba-catalogos-proline-2026-10-18.md).

Contienen material vectorial/codificación problemática; lectura visual necesaria. Los 18 casos de corte son **ejemplos**, no fórmulas generales. Se habían detectado `#NAME?` en páginas 15–16 y títulos inconsistentes en 19–21 de las planillas. La prueba anterior usó provider simulado offline: no fue una publicación real ni validación de fabricante. Estos defectos deben conservarse como incidencias de origen, no corregirse silenciosamente con la IA.

## Qué contiene cada ficha útil

Marca: identidad, material, responsable y series. Serie: nombre exacto, sección reconocible con código, foto de aplicación atribuida cuando exista, configuraciones compatibles y documentos. Configuración: dibujo de apertura desde cara declarada, medidas admitidas por fuente y componentes necesarios. Artículo: código, unidad, largo/suministro, sección, acabado y procedencia. Cada recurso puede tener una versión distinta.

Si falta foto, usar una sección técnica o dibujo fiel identificado; no una foto genérica que sugiera un producto inexistente. Imágenes con derechos desconocidos se enlazan o se usan en investigación local; su redistribución pública necesita permiso o licencia. La UI no debe esperar a una imagen decorativa para ser útil.

Separar tres asuntos: **disponibilidad comercial**, **preparación para cotizar/fabricar/CNC**, y **versión de evidencia**. Una ficha puede estar disponible y faltar una receta. “Referencia” es un estado válido y debe ofrecer la siguiente tarea concreta. No usar una etiqueta verde “Listo” para todo.

## Incorporación de una serie real

1. Registrar fabricante, distribuidor y documento exacto con huella, versión, página e idioma.
2. Extraer candidatos con unidad y referencia; OCR produce candidatos, no autoridad. Mostrar imagen original y campo resultante juntos.
3. Resolver códigos/duplicados y relacionar perfiles, juntas, refuerzos, vidrio y herrajes por evidencia. Lo desconocido sigue sin dato.
4. Revisar fórmulas, holguras, mecanizados y límites con persona competente y fuentes. Un ejemplo no autoriza extrapolar.
5. Construir casos de referencia: dimensiones, apertura, BOM, cortes y vidrio; cálculo determinista y comparación explícita con la evidencia.
6. Publicar una versión para el alcance verificado; habilitar producción/CNC solamente con su autoridad requerida. Cambios posteriores no alteran revisiones emitidas.
7. Incorporar **precios privados de la empresa**, unidad, moneda y vigencia. Precio público de internet no sustituye costo negociado ni margen.

Primer alcance recomendado: Proline PRO6004 y PROSLIDE70 **en etapas de preparación separadas**, más una familia de aluminio priorizada según disponibilidad de datos. No prometer 15 marcas fabricables solo porque hay 15 PDF descargables.

## Retirada de demos del recorrido normal

Propuesta futura: tenants de prueba conservan sus fixtures; el tenant de trabajo inicia con fabricantes reales y estados honestos. Sistemas sintéticos quedan en laboratorio de pruebas con filtro explícito, sin borrar referencias históricas ni relabelar DEMO como real. Migraciones y filtros deben preservar cálculo de revisiones antiguas y autoridad de cada versión.

Aceptación: buscar Proline muestra una marca y sus series; no una lista de clones. Abrir una serie muestra configuración, sección y documento útil. Puede completarse una cotización manual/IA sobre una serie real publicada, y el usuario distingue claramente qué está habilitado para fabricar.
