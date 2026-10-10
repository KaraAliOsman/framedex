# P13 · pack de corte y etiquetas físicas

Base `957451c9`, rama `codex/P13-pack-corte-etiquetas`. Verificación local
con Supabase, Django, worker y Chromium; catálogo y material de aceptación
marcados DEMO. Se conserva el contrato de una OT por posición.

El cortador ve la barra a escala, sus cortes en secuencia, ángulos, pieza,
origen y destino del sobrante. PDF, CSV, DXF, etiquetas y QR usan la misma
dirección física. La vista agrupada reúne ajustes iguales de sierra sin
mezclar largo, ángulo, color, función ni autoridad, y mantiene cada etiqueta.

## Papel y autoridad

El pack Carta apaisado distribuye tres barras por hoja y conserva el cierre
Decimal exacto. Los cortes estrechos usan callouts, con cuerpo de al menos
8 pt. Refuerzos y junquillos tienen sección propia y relación con su padre;
los vidrios muestran composición, posición, cantidad y medidas formateadas.
La falta de formato abre una declaración operable en Catálogo › Formatos
de lámina; no se sustituye por una medida inventada.

La declaración conserva proveedor y fuente en una variante de inventario,
sin movimiento de stock. Una declaración nueva afecta al optimizar de nuevo;
no reescribe un plan sellado. El servidor limita la escritura al dueño o
jefe de taller; los demás lectores solo consultan. DEMO procede del sistema
de catálogo. Los documentos históricos sin fuente la muestran como Sin dato.
El código de compra conserva una sola identidad física: dimensiones/despunte
o sustrato incompatibles exigen otro código. La validación se serializa por
organización/código; las alternativas del mismo área tienen orden determinista.

La organización configura Carta, A4 o rollo 100 × 50 mm y el destino de los
retazos. Cada etiqueta muestra OT, posición/unidad, función, largo/medidas,
ángulos, color, huella, QR y siguiente estación según la ruta material real.
Los junquillos y vidrios van a Vidriado y paneles; el refuerzo se incorpora
a la fabricación de su padre. El rollo lleva una etiqueta por página.

Optimizar, mediante acción humana, reserva direcciones RT deterministas.
No crea material disponible. Completar Corte registra esas identidades y su
destino; un replay no duplica retazos. Un GET de papel o etiquetas no asigna
códigos, cambia stock ni altera una revisión emitida. Los PDFs privados
responden con `Cache-Control: private, no-store`; parámetros desconocidos,
duplicados o inválidos se rechazan.

DXF AC1021 conserva UTF-8, «Junquillo», «Ñ» y coordenadas de origen sin
redondear a 0,001 mm. El parser fijado `ezdxf==1.4.3` comprueba el archivo.
[Formato genérico y columnas](../production/FORMATOS-CORTE.md) documenta
CSV, metadatos, secuencia y límites de interoperabilidad. No se afirma
compatibilidad con un formato propietario de máquina.

## Recorridos y evidencia

PASA: guardar/recargar/restaurar papel y destino; rechazo de entrada inválida
sin escritura; declarar suministro con fuente; recarga persistente; selección
física y agrupada por teclado; descargas reales de PDF/etiquetas/CSV/DXF.

La OT DEMO `OT-P-000538-REV-A-02` verifica el flujo desde el faltante hasta
material reservado mediante movimiento explícito DEMO, QR abierto por el
operario a 390 px oscuro y Corte completado. Sus cinco RT previstos entran
al inventario con el mismo código, dimensión y destino; los dos retazos
tomados pasan a consumidos. La OT anterior de P12 conserva su historia.

- [Antes, corte 1440 claro](captures/pack-corte-etiquetas/antes/corte-1440-claro.png).
- [Después, corte](captures/pack-corte-etiquetas/despues/corte-1440-claro.png),
  [formatos](captures/pack-corte-etiquetas/despues/formatos-1440-claro.png) y
  [ajustes](captures/pack-corte-etiquetas/despues/ajustes-1440-claro.png).
- [Lista impresa](captures/pack-corte-etiquetas/impresion/lista-corte.png),
  [vidrios](captures/pack-corte-etiquetas/impresion/vidrios.png),
  [etiquetas](captures/pack-corte-etiquetas/impresion/etiquetas.png) y
  [rollo](captures/pack-corte-etiquetas/impresion/etiqueta-rollo.png).
- [Resultados de impresión y QR](captures/pack-corte-etiquetas/impresion/resultados.json):
  tres barras, trece piezas, cinco retazos, tres páginas de pack, dieciocho
  QR decodificados desde píxeles y dieciocho páginas/etiquetas de rollo.
  El pack anterior ocupaba cuatro páginas para las mismas tres barras.
- [Corte por QR](captures/pack-corte-etiquetas/recorrido/02-qr-en-corte-390-oscuro.png),
  [RT físico](captures/pack-corte-etiquetas/recorrido/03-retazo-real-con-destino.png)
  y [resultado del flujo](captures/pack-corte-etiquetas/recorrido/resultados.json).
- [Matriz](captures/pack-corte-etiquetas/matriz/resultados.json): dieciséis
  vistas de corte/formatos y ocho agrupadas a 1440/1280/1024/390, claro/oscuro,
  sin desborde de página ni errores JavaScript; carga, error/reintento, vacío,
  bloqueado y sin permiso comprobados. Las respuestas retenidas/de error
  existen solo en el harness de aceptación, no en el producto.
- [Auditor de Producción](captures/pack-corte-etiquetas/ux-produccion/index.html)
  y [auditor de formatos](captures/pack-corte-etiquetas/ux-formatos-lamina/index.html):
  ocho capturas por ruta, cero hallazgos finales. Los reportes vacíos de una
  selección de ruta errónea se retiraron y no se cuentan como evidencia.

## Dos rondas editoriales

Primera ronda: (1) se reemplazó la paginación que repartía tres barras en cuatro
páginas por una lámina compacta; (2) se recuperaron QR y huella en el papel y
se evitó la colisión de cortes estrechos; (3) se corrigieron la relación padre
y el destino físico de los retazos, sin fabricar direcciones al imprimir.

Segunda ronda: (1) se eliminaron botones repetidos de variantes, usando un
selector de orden y una acción por documento; (2) se construyó el destino
real para formatos de lámina, con fuente, contraste oscuro y todos los campos
visibles a 390 px; (3) se corrigieron rollo, «Junquillo» y la estación real
según material. Se retiró la línea ornamental que restaba alto a la etiqueta.

F2 aparece en todas las hojas y etiquetas. La idea del §8 funciona con el plan
del motor: barra a escala → secuencia/ángulos → dirección de pieza → etiqueta
en ese orden → retazo con código y lugar de destino.

## Rúbrica del alcance P13

| Regla | Resultado | Evidencia |
|---|---|---|
| R1 | PASA | Plex Mono tabular, mm/×/porcentaje formateados y cierre exacto. |
| R2 | PASA | Tokens de radio existentes; papel y etiquetas rectangulares. |
| R3 | PASA | Jerarquía por bordes, peso y espacio; sin elevación nueva. |
| R4 | PASA | Naranja acotado a identidad/atención y geometría, sin CTA naranja. |
| R5 | PASA | Teal en acciones y selección; claro y oscuro verificados. |
| R6 | PASA | Marco, junquillo, refuerzo, vidrio y destinos en español; glosario exhaustivo. |
| R7 | PASA | Taller con secuencia visible y papel de tres barras por hoja. |
| R8 | PASA | Cinco estados, causas de falta de formato/material y acción disponible. |
| R9 | PASA | Lámina técnica sobre mesa; el papel conserva contraste. |
| R10 | PASA | Pieza seleccionada por contorno y tinte con inspector físico. |
| R11 | PASA | Iconografía común y extremos de corte; no se altera DIN de elevaciones. |
| R12 | PASA | Selección/impresión por teclado y foco visible. |
| R13 | PASA | Sin animación añadida; respeta tokens y movimiento reducido. |
| R14 | PASA | Una acción por pack/etiquetas; orden de impresión consolidado. |
| R15 | PASA | Plan motor/autoridad sellada; Sin dato y causa para fuente/formato ausentes. |
| R16 | PASA | Sin degradado, blur, brillo ni color de IA. |
| R17 | PASA | Anchos/temas comprobados; formatos móviles sin tabla recortada. |
| R18 | PASA | Descargas, declaración, guardar/recargar y destino QR ejercitados. |
| R19 | PASA | Huella F2 en hoja/etiqueta y barra a escala. |
| R20 | PASA | Orden común de PDF/CSV/DXF/etiquetas/QR y alta real de RT al completar. |

## Verificación técnica

Los tests renderizan las 113 OT de revisiones de 1/12/100 posiciones, respetando
una OT por posición. Verifican páginas ≤ ceil(barras/3) + dos secciones,
tipografía, bbox sin recorte/colisión, cierre Decimal, Unicode, precisión,
agrupación sin mezcla y paridad entre artefactos. La regresión focal de
producción/inventario/OpenAPI pasa 169 tests; la regresión de orden independiente
de filas se añade durante el cierre. No cambia ninguna fórmula del
motor ni se regeneran goldens.

Los resultados finales de los gates locales y CI se incorporan antes del merge.

## Decisiones y límites

[Valores configurables](../decisions/valores-por-defecto.md): Carta como papel
inicial de etiquetas y Recepción de retazos como destino inicial. Las medidas
de lámina siempre requieren declaración con fuente; no existe formato oculto.

El material de aceptación es sintético y declarado DEMO. La verificación
documental no certifica una máquina ni sustituye su perfil/postprocesador.
Los formatos históricos sin fuente conservan su aviso. Los planes anteriores
sin dirección RT prevista requieren reoptimización humana antes de Corte;
imprimir no reescribe su historia. No se añade una integración externa nueva.
