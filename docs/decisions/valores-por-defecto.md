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
