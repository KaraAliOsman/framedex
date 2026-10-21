# Auditoría de DEKOPEN · 21-10-2026

Auditoría hecha por Claude como director de producto, diseño y tecnología. Base:
`main` en `0207763c` (después de las PR 160, 161 y 162), REVIEW local en
`http://127.0.0.1:5179` con los cinco roles y el portal, código del repositorio
y el estado vigente del wiki. Las cifras de esta página se midieron el 21-10-2026.

## Veredicto en una frase

DEKOPEN tiene un **motor serio y un esqueleto de SaaS correcto**, pero como
producto es una **demo sobredimensionada**. Hace cientos de cosas a medias y no
logra la única que el dueño necesitaba el primer día: cargar **su** serie
(Proline PRO6004), poner **sus** precios, dibujar una ventana y obtener un corte,
una lista de materiales y una cotización correctos, rápido y sin pelear con el
programa.

## Lo que se midió

| Medida | Valor | Lectura |
|---|---:|---|
| Líneas de frontend (sin tests ni código generado) | 101 020 | Interfaz enorme para el valor entregado |
| Líneas de backend Python (sin tests ni migraciones) | 83 770 | Dominio sobremodelado |
| Líneas del motor | 18 851 | Es la parte valiosa |
| Migraciones SQL | 192 | Esquema muy fragmentado |
| Operaciones del API | 364 | Superficie inmanejable para un equipo pequeño |
| Rutas de la aplicación | 40 | Navegación dispersa |
| Textos de interfaz (claves i18n) | 3 308 | Demasiado texto en pantalla |
| Apariciones de «Sin dato» en la interfaz | 323 | La experiencia está dominada por lo que falta |
| Apariciones de «DEMO» | 304 | El producto se presenta como demo |
| «fuente» / «sellad» / «autoridad» | 224 / 93 / 57 | Jerga de ingeniería interna expuesta al usuario |

## El caso de uso central, recorrido

**Objetivo del dueño:** cotizar y cortar ventanas Proline PRO6004 con precios propios.

1. **Catálogo.** Proline aparece como «Referencia · no cotizable»: tiene artículos
   citados de un PDF, pero ninguna regla de descuento, junquillo, herraje ni
   precio que el motor acepte. Para que una serie cotice, el sistema exige una
   escalera de «autoridades» (técnica → compra → fabricación → proceso → CNC)
   con procedencia por dato. Un carpintero no sabe completar eso, y la interfaz
   no le dice en una pantalla qué cifras faltan ni le deja escribirlas en una tabla.
2. **Editor.** Solo las series DEMO sintéticas permiten dibujar con precio. Con
   ellas el editor funciona (apertura, vidrio, 3D, cotas), pero el usuario no
   puede usar su serie real.
3. **Precio.** Cada ventana muestra «Falta calcular el precio» hasta pasar por
   listas de costo auditadas, reglas comerciales y aplicación explícita. Para
   un taller pequeño son demasiados pasos y conceptos: costo, lista, regla,
   proyección, aplicación, aprobación.
4. **Cotización.** Existe el PDF borrador rápido y la emisión formal, pero la
   emisión exige preparación documental, condiciones y precio aplicado. El camino
   feliz «dibujé → mando cotización» no cabe en un minuto.
5. **Corte.** La hoja de corte existe (DOC-05) y la optimización también, pero
   dependen de la autoridad de fabricación de la serie, que la serie real no tiene.

**Conclusión:** la cadena se corta en el paso 1. Todo lo demás (taller,
compras, terreno, analítica, portal, créditos IA) está construido sobre datos
que el cliente real no puede producir.

## ¿Están bien los cálculos?

Revisé el despiece guardado de una ventana fija PVC DEMO de 1200 × 1100 mm:

| Pieza | Motor | Cálculo del oficio | ¿Coincide? |
|---|---|---|---|
| Marco horizontal | 1206 mm × 2, 45°/45° | 1200 + 2 × 3 mm de soldadura | Sí |
| Marco vertical | 1106 mm × 2, 45°/45° | 1100 + 2 × 3 mm | Sí |
| Refuerzo de acero | 1176 mm × 2 | barra de marco − 30 mm | Sí |
| Vidrio 4-16-4 | 1100 × 1000 mm, 1,10 m², 22 kg | luz − holguras declaradas; 8 mm de vidrio × 2,5 kg/m²·mm | Sí |

- **Aritmética:** correcta y exacta (`Decimal`, tolerancia 0,00 mm), con 97
  archivos de prueba y casos dorados que congelan las fórmulas. Es el activo más
  valioso del repositorio y se conserva.
- **El problema no es la aritmética, es el dato.** Las reglas (descuentos por
  rol, holguras de junquillo, tablas de herraje por tamaño de hoja, refuerzo por
  color y largo) solo existen para el catálogo DEMO sintético. Para una serie
  real no hay forma práctica de cargarlas. Eso es lo que el dueño percibe como
  «no sé cómo estarán los cálculos».
- **Riesgo abierto:** dos casos dorados figuran en rojo desde antes de esta fase
  y `test-db` solo corre en CI. Deben quedar verdes antes de reconstruir.

## Problemas por capa

### Producto
- **Prioridades invertidas:** se construyeron CNC, analítica de cohortes,
  cierres inmutables de costos, rectificaciones de terreno y créditos por lote
  antes de que funcionara «mi serie, mis precios, mi cotización».
- **Exceso de conceptos:** revisión sellada, autoridad, fuente, preparación
  documental, proyección, aplicación, aprobación, Mesa/Estudio, encargo, recibo.
  Cada uno tiene sentido técnico; juntos hacen el programa inusable para un taller.
- **Bloqueos en lugar de valores sugeridos:** cuando falta un dato, el sistema
  se niega y muestra «Sin dato». Los líderes del rubro proponen un valor de
  fábrica editable y marcan que es supuesto.

### Experiencia y diseño
- La rehechura visual de las PR 160–162 dejó una base limpia (tokens, tipografía,
  controles segmentados, búsqueda en píldora, tarjetas). Pero la **arquitectura
  de información** sigue siendo la del sistema anterior: muchas pestañas,
  paneles plegables, textos explicativos largos y estados de error en primer plano.
- No hay un **flujo guiado** de alta de serie, ni importación de lista de precios
  en Excel con mapeo de columnas como paso principal del onboarding.
- La IA es una ventana flotante, no el motor del flujo: no carga catálogos por
  sí sola de punta a punta, no convierte un plano en obra lista para cotizar ni
  prepara la cotización completa con un clic de aprobación.

### Ingeniería
- 200 mil líneas para una demo implican alto costo de cambio. Hay módulos que
  conviene **congelar o retirar** del producto visible (CNC, cohortes, cierres
  de costos, rectificación de terreno, Laboratorio con 45 series DEMO).
- Invariantes buenos que se conservan: motor único de cifras, `Decimal` en mm y
  dinero, `org_id` + RLS, revisiones inmutables, pagos idempotentes, clic humano
  para efectos externos.

## Qué se conserva, qué se rehace y qué se retira

| Conservar | Rehacer | Retirar del producto visible |
|---|---|---|
| Motor determinista y casos dorados | Modelo de catálogo: tabla editable de reglas con valores sugeridos | Laboratorio con 45 series DEMO en la lista principal |
| Supabase + RLS, multi-empresa, roles | Onboarding: «carga tu serie y tus precios» en 10 minutos | Cierres inmutables de costos y cohortes en la navegación |
| Revisiones inmutables y portal del cliente | Precio: costo + margen en una pantalla, aplicado de forma automática | Escalera CNC (dejar como módulo avanzado) |
| Símbolos DIN, 2D/3D, PDF real | Editor: biblioteca de tipologías + inspector simple | Jerga «autoridad / sellado / fuente» en la interfaz |
| Pagos idempotentes y créditos IA | Copiloto: agente que opera todo el flujo con aprobación | Más de un camino para la misma tarea |

## Causa raíz

El sistema se diseñó desde la **auditabilidad** («nunca inventar una cifra») y
no desde el **trabajo del taller** («cotizar hoy»). Ambas cosas son compatibles:
un valor sugerido de fábrica, visible y editable, no es una cifra inventada si
queda marcado y trazado. El rediseño debe partir del trabajo, con la auditoría
por debajo, no al revés.
