# D04 · herrajes por familia, clase y componentes

El motor resuelve el herraje y explica sus restricciones. Una elección comprende
componentes, masa, largos cortables, manilla, color y opciones con fuente. La
revisión emitida conserva esa expansión para compra, stock, picking y mecanizado.

## Alcance comprobado

- Familias por serie y movimiento D03, clases por ancho/alto/masa y prioridad.
  La relación de aspecto, compás, manilla, combinaciones de opciones y masa
  desconocida tienen mensajes con causa. Se rechazan datos ambiguos y flotantes.
- Reglas tipadas de cantidad/largo/masa y costo Decimal. Los puntos de cierre
  cambian en el umbral exacto; las transmisiones se cortan a su largo derivado.
  Las opciones reemplazan componentes sin sumar dos veces el kit.
- Manillas/modelos/colores/artículos y altura según su autoridad. La pasiva
  mantiene su herraje y no recibe la selección activa. Una altura fuera del
  rango bloquea guardar y se puede deshacer.
- El catálogo manual conserva la autoridad existente. CSV y XLSX de la plantilla
  D01 hacen ida y vuelta exacta. SQL valida el schema finito y sus relaciones sin
  depender de pg_jsonschema, disponible de forma distinta en PostgreSQL 16.
- Seis series DEMO v4 aditivas. V1/v2/v3, precios aplicados, BOM/hashes y revisiones
  emitidas no se reescriben. El snapshot D04 conserva toda la precisión de la masa;
  el transporte histórico conserva sus bytes y escala anterior.
  La instalación limpia completa las catorce autoridades de inspección y las
  políticas de fabricación/manillas después de cargar su fuente canónica. El
  generador reproduce esa semilla y las migraciones sin modificar datos previos.
- Compra/stock consumen componentes y variantes por largo, sin duplicar el kit.
  Picking por OT y revisión agrupa SKU/largo/fuente y suma cantidades del motor.
- Mecanizados con host inequívoco, coordenadas, cara, herramienta, profundidad y
  cobertura se proyectan sobre las piezas selladas. Sin esos datos quedan
  **declarados no emitidos** y no permiten completar MACHINING. No se inventan
  coordenadas. P14 conectará la proyección neutral a la máquina configurada.
- Cliente y portal solo reciben modelo/color de manilla, opciones y marca
  sintética. La lista de ingeniería y costos no se expone por ese contrato.

## Flujos y evidencia

| Recorrido                                                                   | Resultado                                                                  | Evidencia                                                                         |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Motor → dos tamaños oscilobatientes, corredera pesada y puerta              | PASA: expansión, masa y costo exactos; corredera realmente en clase pesada | `engine/tests/golden_hardware_classes.json`                                       |
| Cantidad/largo → fronteras, masa/desconocido, ratio/compás/manilla/opciones | PASA: cada restricción con causa y eje; no se acepta BOM inválido          | `engine/tests/test_gold_cases_hardware.py`                                        |
| Plantilla oficial → CSV/XLSX → candidato → serializer                       | PASA: autoridad idéntica, Decimal exacto                                   | `backend/tests/test_hardware_classes.py`                                          |
| F6 → fuente/rango/componentes → modelo/color/opción → guardar/reabrir       | PASA: selección tipada y persistida                                        | `recorrido/inspector-f6-manilla-opciones.png`, `guardado-reapertura-opciones.png` |
| Incompatible → siguiente clase → delta/diff → aplicar → deshacer            | PASA: reparación del motor, sin mutar antes del clic                       | `recorrido/restriccion-siguiente-clase.png`, `clase-aplicar-deshacer.png`         |
| Límite de serie → división → delta/diff → aplicar → deshacer                | PASA: geometría alternativa calculada estrictamente                        | `recorrido/division-diff-motor.png`, `division-aplicar-deshacer.png`              |
| Activa/pasiva → inspector → técnica                                         | PASA: dos herrajes y sin control activo en pasiva                          | `recorrido/pareja-*.png`                                                          |
| Vacío / carga / error y reintento / sin permiso / bloqueado                 | PASA: textos y acciones explícitos; el transporte de fallos se inyecta     | `recorrido/estado-*.png`, `altura-fuera-de-rango.png`                             |
| Doce posiciones → precio → sellado → doce OT → picking                      | PASA: cada SKU/largo/fuente y cantidad coincide con el motor               | `recorrido/flujo-12-posiciones.json`, integración `test_hardware_flow.py`         |
| Revisión/OT → manager/operator/installer → picking y fuentes                | PASA: datos sellados, lectura del servidor y matriz móvil                  | `recorrido/pedido-*.png`                                                          |
| Cotización → DOC-01 y pack de producción                                    | PASA: PDF emitido y pack real rasterizados y revisados                     | `recorrido/cotizacion-12-posiciones.pdf`, `pack-herrajes.pdf`                     |
| Otra revisión cotizada → enlace local → portal                              | PASA: manilla vendible sin cremona/componentes de ingeniería               | `recorrido/portal-*.png`, `portal-fixture.json`                                   |
| Serie → ficha del kit → reglas y fuentes de clase                           | PASA: seis pares de tamaño/tema, lectura clara y fuente                    | `recorrido/catalogo-*.png`, `catalogo.json`                                       |
| Otro tenant → revisión/picking/catálogo                                     | PASA: aislamiento, permisos y publicación inmutable                        | Integración `test_hardware_classes.py`, `test_hardware_flow.py`                   |

El flujo HTTP repite cuatro casos tres veces, con cantidades 1/2/3. Usa vidrio
con autoridad de seguridad: sus correderas pueden resolver la clase estándar.
El golden de corredera pesada usa otra receta y comprueba la clase pesada real;
el nombre de un caso no se presenta como prueba de su capacidad.

El PDF al cliente tiene siete páginas y el pack catorce. Se revisaron todas,
incluidas picking y causas de mecanizados no emitidos. La cotización declara
DEMO en todas sus páginas y vista interior en las elevaciones. El pack deriva
cortes/componentes de la revisión y del plan optimizado. La carga estructural
del ensayo es ficticia y no acredita viento para una obra.

## Pase editorial: dos rondas

Primera ronda:

1. Se eliminó el selector/ranking paralelo de kits del frontend y su código
   muerto. La resolución única del motor ocupa el inspector del paño.
2. F6 muestra medida, peso, rango, fuente y reglas de cada componente. La
   ingeniería permanece plegada; el resumen básico no pide datos derivables.
3. La reparación por clase o división muestra diff y delta antes de aplicar;
   ambas acciones se deshacen. Se retiró la selección silenciosa de una familia.

Segunda ronda:

1. Se quitaron decimales sobrantes y se normalizó el peso en los mensajes.
   **Peso con herraje** muestra una cifra útil; la precisión exacta queda en
   Detalles técnicos y en el BOM, sin redondear la autoridad.
2. Los controles nuevos usan radios de token. Las reglas de catálogo conservan
   contraste aun en consulta, fuentes desplegables y cantidades Mono. Los SKU
   codificados quedan en Detalles técnicos del catálogo y de stock.
3. Picking usa filas que envuelven texto en móvil. Acciones de taller envuelven
   sus botones y tienen objetivo de 44 px. El mecanizado incompleto explica sus
   datos faltantes y la acción de completar catálogo/nueva revisión.
   Las dos consultas de herrajes usan esqueleto y cargador de cota tras un segundo;
   se comprobó la espera demorada y la llegada del resultado real en editor/taller.

Momento de firma: F6 **¿Por qué este kit?** deriva peso/rango/componentes/fuente.
Idea que sube el techo: siguiente clase o división aceptada por el motor, con
precio neto de herrajes, diff previo y deshacer.

| Rúbrica | Resultado | Evidencia del alcance D04                                         |
| ------- | --------- | ----------------------------------------------------------------- |
| R1      | PASA      | Mono, unidades, formatos exactos sin decimales sobrantes          |
| R2      | PASA      | Radios nuevos r-1; bordes de token                                |
| R3      | PASA      | Herrajes dentro del inspector, sin otra superficie flotante       |
| R4      | PASA      | Naranja solo ante bloqueo o revisión humana                       |
| R5      | PASA      | Teal en controles, selección y foco                               |
| R6      | PASA      | Nombres del taller, modelo/color/opciones y códigos plegados      |
| R7      | PASA      | Resumen compacto; componentes/fuentes en Avanzado                 |
| R8      | PASA      | Cinco estados y reintento, causa y acción                         |
| R9      | PASA      | Vista interior sobre papel; documentos verificables               |
| R10     | PASA      | Selección conserva contorno, tinte y manijas del editor           |
| R11     | PASA      | Manilla del lado de cierre; correderas y pasivas conservan física |
| R12     | PASA      | F6/foco, campos nativos accesibles y deshacer comprobados         |
| R13     | PASA      | Sin animación ornamental nueva ni demoras artificiales            |
| R14     | PASA      | Revisión previa y una aplicación por propuesta                    |
| R15     | PASA      | Regla/fuente por número; masa o precio ausente dice Sin dato      |
| R16     | PASA      | Sin degradado, blur, brillo ni morado en la superficie nueva      |
| R17     | PASA      | Matriz exigida; picking/portal incluyen 390 px                    |
| R18     | PASA      | Guardar/reabrir, diff/aplicar/undo, picking y descargas reales    |
| R19     | PASA      | F6 explica la resolución única del motor                          |
| R20     | PASA      | Clase siguiente/división con cálculo y delta reales               |

La rúbrica evalúa la superficie nueva. Los reportes completos conservan hallazgos
anteriores del editor/producción/ficha de serie para P04/P12/P13/P16. El desborde
del editor a 390 px ya existe en su línea base; este encargo exige ese tamaño en
portal y taller, que pasan. `base-poblada-*` usa el frontend de `4d50de83` sobre
los mismos datos locales para distinguir aumento de filas de cambio de estilos.
La comparación final se conserva en `comparacion.json`.

## Gates y reproducción

Gates generales comprobados: 605 motor y dos xfail históricos, 1 174 backend,
715 frontend en 62 archivos; lint, typecheck y build pasan. La base limpia pasa
el lint SQL, 1 008 comprobaciones pgTAP en 72 archivos y 294 pruebas de integración.
Los once recorridos Chromium y todos los upgrades poblados PostgreSQL 16 pasan;
`make test-db` termina en PASA. D04 comprueba diez tipologías anteriores con BOM,
hash, dinero aplicado, snapshot emitido y catálogo histórico intactos. El gate
local usa Django en 18000 por la reserva de 8000 de Docker Desktop; adapta solo
el transporte del clon aislado, sin quitar ninguna comprobación ni cambiar la app.
Los cuatro checks de CI se registran después de verificar el head publicado.
Los goldens históricos no cambian; el nuevo se generó con `make goldgen` y se
revisó la expansión, masa, costos y ambos encuentros de corredera.

Con el stack de la skill y `.env` cargado solo en memoria:

```text
python scripts/verify_hardware_flow.py
python scripts/verify_hardware_flow.py --portal-only
node --experimental-strip-types frontend/scripts/verify-d04.mjs
node --experimental-strip-types frontend/scripts/verify-d04.mjs --catalog-only
```

`--downstream-only` reanuda taller/portal y conserva las capturas del editor ya
verificadas. Los tokens quedan solo en memoria; no hay env, secretos ni enlaces
de acceso público en la evidencia. No se envía ningún mensaje a terceros.

## Decisiones, activación y riesgos

Véanse `docs/decisions/valores-por-defecto.md`, la wiki de herrajes y
`docs/operations/ACTIVACION.md`. La prioridad/rango/altura procede del catálogo;
no hay una capacidad universal oculta. El delta identificado es de herrajes por
hoja con merma/margen vigente, no el precio completo de perfil/vidrio/instalación.
Después de dividir se cotiza la posición completa.

Los catálogos sintéticos no certifican fabricante, clase RC ni coordenadas.
Sin esas fichas, mecanizar permanece bloqueado con causa. D05 amplía acabados de
perfiles, D06 accesorios, D08 otros movimientos y P14 máquinas. Estas fronteras
no se anuncian como capacidades terminadas por D04. No se activa una integración
externa ni se sustituye la revisión de un proveedor por un ensayo DEMO.
