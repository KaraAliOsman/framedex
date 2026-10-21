# Catálogo y cálculo · especificación de producto

**Problema que resuelve:** hoy una serie real (Proline PRO6004) no puede cotizar
ni cortar porque el sistema exige «autoridades» con procedencia por dato que un
taller no sabe aportar. Esta especificación reemplaza la escalera de bloqueos
por una **ficha de serie editable con valores de fábrica**, sin perder trazabilidad
ni exactitud.

**Regla de oro:** las cifras las calcula siempre el motor (`engine/`, `Decimal`,
tolerancia 0,00 mm). Ni la IA ni la interfaz calculan. Lo que cambia es **de
dónde salen los parámetros** y **cuándo se permite usar cada uno**.

## 1. Modelo mental para el usuario

```
Fabricante (Proline, Rehau, Indalum, Alumco…)
└── Serie (PRO6004 · PVC 60 mm · 4 cámaras · practicable)
    ├── Perfiles ........ marco, hoja, junquillo, travesaño, inversor, refuerzo…
    ├── Reglas .......... descuentos, soldadura, holguras de vidrio, refuerzos
    ├── Herrajes ........ kits por apertura y tabla de rangos por tamaño de hoja
    ├── Vidrios ......... espesores admitidos → junquillo según espesor total
    ├── Colores ......... acabados, recargos, refuerzo/stock por color
    ├── Tipologías ...... ventanas que esta serie sabe fabricar (fija, abatible, corredera…)
    └── Precios ......... los del taller: por barra, kg, metro o unidad
```

El usuario ve **una ficha por serie** con seis pestañas: *Perfiles · Reglas ·
Herrajes · Vidrios y colores · Tipologías · Precios*. Cada pestaña es una
**tabla editable** (estilo hoja de cálculo, con pegar desde Excel), no un
formulario con decenas de campos sueltos.

## 2. Origen de cada valor (reemplaza «autoridad/fuente»)

Cada valor lleva una **etiqueta de origen**, visible como un punto de color
junto a la cifra y explicada al pasar el mouse:

| Origen | Cuándo se usa | Color | ¿Bloquea? |
|---|---|---|---|
| **Del manual** | Extraído del PDF del fabricante y revisado (con página) | Verde | Nunca |
| **Del taller** | Escrito o confirmado por el usuario | Azul | Nunca |
| **Sugerido** | Valor de fábrica de una plantilla por familia (p. ej. «PVC 60 mm europeo») | Ámbar | Permite cotizar; pide confirmar antes de **fabricar** |
| **Falta** | Sin valor posible | Rojo | Bloquea solo lo que depende de él, con un botón «Completar» |

- La interfaz **nunca** dice «autoridad», «sellado», «fuente» ni «procedencia».
  Dice «Del manual · pág. 14», «Lo puso Juan el 21-10», «Sugerido — confírmalo».
- El historial (quién, cuándo, valor anterior) se conserva en la base de datos,
  igual que hoy, pero se muestra solo al abrir el detalle de la celda.

## 3. Niveles de uso de una serie (reemplaza la escalera de readiness)

| Nivel | Requisito | Lo que habilita |
|---|---|---|
| **Lista para dibujar** | Perfiles con rol y ancho visible | Editor, 2D/3D, medidas |
| **Lista para cotizar** | Reglas y precios con valor (sugerido o real) | Precio, cotización PDF, portal |
| **Lista para fabricar** | Reglas sin «sugeridos» pendientes de confirmar + serie verificada (§6) | Hoja de corte, optimización, OT, compras |
| **Lista para máquina** | Mapa de operaciones CNC | Exportación CNC (módulo avanzado) |

- El nivel se muestra como **una sola etiqueta** en la serie («Lista para cotizar ·
  faltan 3 confirmaciones para fabricar») con un botón que lleva exactamente a
  las celdas pendientes.
- Una cotización hecha con valores sugeridos lleva una nota interna (no en el
  PDF del cliente): «Calculada con 2 valores sugeridos». Al pasar a producción
  se exige confirmarlos.

## 4. Plantillas de fábrica por familia

DEKOPEN incluye plantillas con valores típicos del oficio, editables y
marcadas como «Sugerido»:

| Plantilla | Valores incluidos (ejemplos, todos editables) |
|---|---|
| PVC practicable 60–70 mm | soldadura 3 mm por extremo; refuerzo = barra − 30 mm; holgura vidrio 5 mm por lado; junquillo por espesor total; herraje oscilobatiente por tabla de alto de hoja |
| PVC corredera 60–80 mm | traslapes de hojas, descuento de enganche, holgura de riel, ruedas por peso |
| Aluminio practicable con rotura de puente | corte a 45°, escuadras, holguras de vidrio, descuentos de hoja sobre marco |
| Aluminio corredera tradicional (línea 20/25/5000 tipo LatAm) | descuentos clásicos de hoja = (ancho − traslape) / 2, rieles, felpas por metro |

Las plantillas se cargan como **datos** (`supabase/seed.sql` o un JSON versionado),
no como código. Una serie nueva arranca copiando una plantilla.

## 5. Alta de una serie en 10 minutos (flujo guiado)

1. **Elegir fabricante y serie** desde la biblioteca LatAm precargada (§7) o «Crear».
2. **Subir el manual o lista de precios** (PDF, foto, Excel). La IA extrae tablas
   de perfiles, descuentos y precios en bloques pequeños, **dos veces de forma
   independiente**, y solo muestra para revisión las celdas donde no coinciden
   (patrón Ruh AI / ExtractBench, ver informe). Los números se convierten a `Decimal` en código, no en el modelo.
3. **Completar con plantilla:** lo que el manual no trae se rellena con la
   plantilla de familia (ámbar).
4. **Poner precios del taller:** pegar desde Excel o escribir el precio por barra/kg.
   Mapeo de columnas asistido.
5. **Verificar con una ventana de prueba** (§6).
6. **Listo para cotizar.**

## 6. Verificación de la serie («ventana de prueba»)

Para dar confianza sin pedir autoridades:

- El usuario elige una ventana de referencia (p. ej. 1200 × 1100 abatible) y el
  sistema muestra el **despiece calculado** al lado de una columna vacía
  «Según tu manual / tu experiencia».
- Si el usuario confirma o corrige las medidas, las correcciones actualizan las
  reglas (con origen «Del taller») y la serie queda **verificada**.
- Cada serie verificada genera automáticamente un **caso dorado** propio del
  taller (el mismo mecanismo de `engine/tests/test_gold_cases_*`, pero guardado
  como dato del tenant) que se recalcula en cada cambio de reglas: si un cambio
  altera la ventana de prueba, se avisa antes de guardar.

## 7. Biblioteca LatAm precargada

Fase 1 (Chile): Proline PRO6004 y PRO7005 (vía Aluminios & PVC 2000), líneas
Indalum y Alumco de aluminio más vendidas, Rehau y Winhouse. Fase 2: Aluar
(Argentina), Cuprum (México), Alumina/Colombia. Cada serie precargada trae
perfiles, reglas «Del manual» cuando hay manual público y «Sugerido» cuando no,
**sin precios** (los precios siempre son del taller).

Las series DEMO sintéticas se mueven a un espacio «Ejemplos» fuera de la lista
principal y no se cuentan en los indicadores.

## 8. Precio (simple primero, profundo después)

- **Modo simple (por defecto):** costo de materiales (barras/kg/m/unidades a precio
  del taller) + mano de obra por m² o por ventana + instalación + margen %.
  Una sola pantalla «Cómo calculo mis precios» en Empresa.
- **Modo avanzado:** listas de costo con vigencia, recargos por color, matrices,
  bandas de margen y aprobación de descuento (lo que existe hoy) — oculto hasta
  que el usuario lo active.
- El precio de cada ventana se calcula **automáticamente** en cuanto la serie
  está «Lista para cotizar». Desaparece el paso explícito «Aplicar precio» del
  flujo normal; la aplicación queda registrada al emitir la cotización.

## 9. Lo que se conserva del sistema actual

- Todo el motor: geometría, aperturas avanzadas, herrajes por reglas, vidrios
  compuestos, despiece, optimización (`nesting.py`, `cutting.py`), pesos, térmica.
- Los invariantes: `Decimal`, `org_id` + RLS, revisiones emitidas inmutables,
  historial de cambios de catálogo.
- Las autoridades actuales pasan a ser **implementación interna** de los niveles
  de §3: el mapeo de «Del manual / Del taller / Sugerido» a los registros de
  procedencia existentes se hace en el backend.

## 10. Criterios de aceptación medibles

1. Un taller nuevo carga Proline PRO6004 desde su PDF y lista de precios y
   emite su primera cotización en **≤ 15 minutos** sin ayuda.
2. La ventana de prueba de 1200 × 1100 abatible PRO6004 coincide al milímetro
   con el despiece que el usuario confirma.
3. Cero apariciones de «autoridad», «sellado», «fuente», «procedencia» en la interfaz.
4. «Sin dato» desaparece como estado normal: se reemplaza por «Sugerido» o
   «Completar» con acción directa.
5. Los casos dorados existentes siguen verdes; cada serie verificada suma el suyo.
