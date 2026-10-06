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
