# Valores por defecto del programa DEKOPEN v1

Fuente inicial: `docs/design/CONSTITUCION.md`, seccion 11. Los encargos siguientes deben mantener esta tabla cuando implementen o cambien un valor configurable.

| Decision                   | Valor por defecto                                                                                               | Donde se cambia                   | Estado      | Encargo que la implementa |
| -------------------------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------- | ----------- | ------------------------- |
| Papel de los documentos    | Carta                                                                                                           | Ajustes > Documentos              | por defecto | P09                       |
| Anticipo                   | 50 % al aprobar, saldo contra entrega                                                                           | Ajustes > Condiciones comerciales | por defecto | P08                       |
| Validez de la cotizacion   | 15 dias corridos                                                                                                | Ajustes > Condiciones comerciales | por defecto | P08                       |
| Garantia                   | Texto plantilla editable, sin plazo inventado: "[completar plazo]" visible solo en Ajustes, nunca impreso vacio | Ajustes > Condiciones comerciales | por defecto | P08                       |
| Plazo de entrega           | Calculado desde la carga de produccion si existe; si no, campo obligatorio por cotizacion                       | Cotizacion                        | por defecto | P08                       |
| Banda de margen            | Objetivo 35 %, minimo 25 %; bajo el minimo requiere aprobacion del dueno                                        | Ajustes > Precios                 | por defecto | P07                       |
| IVA                        | 19 %, precios netos en la app y total con IVA en el documento                                                   | Ajustes > Impuestos               | por defecto | P07                       |
| Pie "Generado con DEKOPEN" | Oculto en documentos del cliente (white-label); visible solo en el portal, discreto                             | Ajustes > Documentos              | por defecto | P09                       |
| Nombre del asistente       | "Asistente DEKOPEN" con el Orb. No se usa "STARWIN"                                                             | Ajustes > Marca                   | por defecto | P17                       |
| Marca de la app            | Direccion B del estudio de identidad (`DEKOPEN` con la O como seccion de perfil)                                | P25                               | por defecto | P25                       |
| Moneda                     | CLP; USD y UF opcionales                                                                                        | Ajustes > Moneda                  | por defecto | P07                       |
| Catalogo                   | Demo con precios aleatorios de semilla fija, marcado DEMO en todas partes                                       | Catalogo > Importar               | por defecto | D01/P16                   |

## P01 · contratos de presentación (2026-10-05)

Estos contratos técnicos aplican la constitución; no son preferencias comerciales configurables:

- Redondeo visible `ROUND_HALF_UP`, con strings Decimal y `BigInt`. Los payloads conservan la precisión recibida del backend mediante `decimalInputValue`.
- Texto atenuado pequeño: `text-small-muted` con AA. Se conserva g-500 para guías/anotaciones grandes; las unidades pequeñas usan la tinta accesible.
- Aperturas: prevalece la constitución §3.6 sobre el vértice inverso del estudio histórico. Vista interior por defecto; exterior reflejada y discontinua.
- Densidad: controles de 32 px en oficina, 44 px en taller, 40 px en documento y 44 px en documento móvil. El muestrario permite revisar las tres; los encargos de superficie conectarán la densidad y su tema al contexto de uso.

Las decisiones y los mecanismos se detallan en [Sistema v2](../design/SISTEMA-V2.md).

## D01 · autoridad e ingesta (2026-10-05)

- Catálogo de arranque: cinco series sintéticas y precios con semilla `20261005`.
  La semilla es una propiedad reproducible del fixture; el dueño carga y revisa sus
  fuentes en Catálogo › Importar. La selección de sistema y acabado es configurable
  por producto. Una importación no certifica automáticamente el catálogo.
- Sin autoridad de corte o límites, el producto nuevo se bloquea con causa y fuente
  faltante. No se adoptan descuentos ni capacidades silenciosos. El dueño los
  declara en Catálogo › Sistema › Parámetros o mediante la plantilla.
- Revisión: dueño o encargado de taller, con diff, confirmación explícita y
  procedencia. El estimador consulta. Los costos conservan el permiso de precios
  del dueño. Deshacer es atómico y se bloquea al usarse una autoridad.
- Productos guardados: preservar las fórmulas anteriores mediante autoridad
  histórica. No recalcular documentos emitidos; no mover catálogos comerciales ni
  composiciones mixtas. Las series históricas no se ofrecen a productos nuevos.
- MiMo de texto: admitir PDF con texto, planilla, correo y texto pegado. Una foto o
  escaneo sin texto muestra la limitación; no se simula OCR. IA3 verificará la ruta
  multimodal antes de habilitarla. El proveedor se configura en el backend y su
  credencial permanece exclusivamente en el entorno.

## D02 · vidrio y seguridad (2026-10-05)

- Las reglas de NCh 135/2 empiezan vacías. **Revisar ejemplos DEMO** propone zonas
  sintéticas de puerta, paño lateral, antepecho bajo y paño grande, con fuente y
  aviso. No transcribe ni certifica una norma. El dueño o encargado revisa el diff
  y configura fuente, zona, clases y obligatoriedad en Ajustes › Reglas de vidrio,
  o importa la norma aportada mediante Catálogo › Importar › Reglas de vidrio.
- Una regla es recomendación salvo obligatoriedad explícita. La ausencia de
  altura sobre el piso provoca revisión, sin presumir una altura segura.
- Masa del PVB: sin espesor, densidad y fuente no se muestra un peso estimado. El
  proveedor aporta esos campos en el compositor; Ug, g, transmisión y clase
  permanecen **Sin dato** hasta recibir su ficha. Las variantes exigen publicación
  revisada antes de asignarse al producto.
- El mínimo facturable y los recargos se configuran por producto mediante sus
  autoridades de precio. Un proceso declarado sin tarifa no se cotiza como gratis.
- El pedido mantiene los decimales del motor cuando existan y pide confirmar esa
  precisión con el vidriero. Las medidas enteras se imprimen sin decimales. No hay
  preferencia de redondeo que cambie la autoridad de fabricación.
- Las etiquetas enlazan a la aplicación mediante `DEKOPEN_PUBLIC_APP_URL`,
  configurada en el entorno de backend. El QR identifica el infill sellado y
  conserva el acceso autenticado del taller.

## D03 · aperturas y manillas (2026-10-06)

- Vista interior por defecto y gramática DIN de la constitución §3.6. El tablero
  histórico de iconos no cambia el lado de bisagras ni de manilla. La dirección
  se elige en la apertura compatible; la vista exterior continúa en P05.
- No se infieren capacidades ni alturas en un catálogo antiguo. El dueño o
  encargado configura movimiento, dirección, rol, kits, fuente, encuentro con
  inversor y regla de manilla en Catálogo › Ficha de serie o en su importación.
  Las nuevas autoridades DEMO v3 son versiones separadas y no certificadas.
- La altura de manilla toma centro, borde inferior o superior **de la regla
  declarada**. El estimador la edita dentro del rango del motor en Avanzado; las
  manillas de banderola/proyectante quedan en su borde de cierre y una pasiva no
  lleva manilla de accionamiento. No se usa una altura universal en Ajustes:
  corresponde al sistema/herraje, cuya fuente es configurable en Catálogo.
- La precisión del encuentro puede producir medios centésimos exactos. El
  motor conserva esos valores; los formatos de presentación no redondean el
  BOM ni el documento sellado a una autoridad distinta.

## D04 · herrajes y fabricación (2026-10-06)

- Clase automática: la prioridad pertenece a la familia de catálogo y solo se
  usa si la masa y las restricciones son decidibles. El técnico puede fijar una
  clase compatible en Avanzado, con diff, precio de herrajes y deshacer. Las
  prioridades y fuentes se revisan/importan en Catálogo; no hay capacidad global
  ficticia en Ajustes.
- Manilla, color y altura proceden de la clase. El rango es editable según su
  ficha; alturas fijas o referidas al borde superior se mantienen fijas. No se
  asigna una manilla activa a la hoja pasiva. D05 ampliará acabados de perfiles.
- Las opciones se ofrecen solamente si la fuente las declara. Un dato RC
  requiere su fuente; la seguridad sintética DEMO no acredita una clase RC.
- El delta corresponde a herrajes netos por hoja, incluida merma/margen vigente.
  La división añade otra hoja y montante: su precio total se confirma cotizando.
  No se presenta el delta parcial como precio final de la posición.
- Sin coordenadas, cara, herramienta, profundidad, cobertura o pieza inequívoca,
  el mecanizado queda declarado no emitido y bloquea completar esa estación. El
  proveedor configura la autoridad mediante la plantilla de Catálogo. P14 la
  conecta a las máquinas; no se adopta un mecanizado por defecto.

## D05 · carta por caras (2026-10-06)

- Vista interior por defecto. La exterior usa su muestra física y conserva el
  sentido de apertura respecto del observador. La cotización declara ambas
  caras; el PDF comercial dibuja interior. El cliente puede cambiar de cara en
  el portal sin modificar su revisión.
- La combinación guardada identifica stock/compra. Interior y exterior nunca
  se suman como dos artículos; la base de PVC y el acero tienen sus identidades
  declaradas. El dueño o encargado configura esta autoridad en Catálogo ›
  Ficha de serie o en la plantilla/importación, con fuente y diff.
- La primera combinación de la carta es la referencia del delta de precio.
  El catálogo permite cambiar su orden y regla por metro, porcentaje o fijo.
  El delta usa merma/margen comercial vigente; una tarifa o moneda desconocida
  muestra Sin dato. No hay un recargo universal oculto en Ajustes.
- Sin textura del fabricante se usa la muestra lineal declarada, marcada como
  aproximada; no se inventa grano ni brillo emisivo. Los límites, refuerzo y
  días adicionales son datos revisables de catálogo. Un plazo no declarado
  permanece Sin dato. DEMO v5 nunca acredita una ficha productiva.
