# P19 · 3D con autoridad física

Código `94b5f151723207fa7b96a5a087a6906f471454d4`, lectura explícita de tokens
`86b79340bab710a9cc9f1336323fdd9393ce981b`, sobre
`codex/P19-3d-fisico`, desde integración `5098d4b1`.
La evidencia se conserva en [3D físico](captures/3d-fisico/).

## Modelo y alcance

El editor entrega las hojas evaluadas de D03/D08 a la misma escena que
consume el render comercial. El portal entrega los hechos sellados de la
revisión emitida. Un catálogo posterior no gobierna esa representación.
La geometría cerrada, plano, recorrido, elevación, pivote y altura de
manilla avanzados vienen del motor. La proyección flotante JS es visual;
no vuelve al motor, la BOM, el corte, el precio ni la fabricación.

Cada hoja móvil tiene control propio. Los paquetes plegables se accionan
como cadenas rígidas por grupo; la hoja de paso se abre independiente
con su paquete cerrado. Las correderas históricas leen el `travel`
declarado y conservan el decodificador de lectura de P05 donde falta.
HST eleva antes de trasladar; PSK se separa antes de recorrer el carril
y ofrece su abatimiento independiente. Guillotinas conservan plano y
recorrido vertical; pivotes usan sus ejes desplazados de catálogo.

Las hojas abatibles/pivotantes sobresalen físicamente en profundidad al
abrir: limitar toda pieza al volumen cerrado impediría cualquier apertura
real. El criterio se verifica como anclaje rígido al eje, longitud invariable
y traslación guiada contenida en el vano. El despiece cierra las hojas y
separa sólo en el eje de profundidad: marco, hoja, junquillo, vidrio,
con líneas guía. Esta interpretación preserva la física y no altera el
contrato del motor ni una revisión emitida.

Se eliminó la textura aleatoria de foliado. Los canales RGB lineales y
texturas declaradas de la carta sellada son la autoridad del color. Sin
textura o muestra fiable se declara color plano aproximado. Una sección
sin declaración conserva la representación esquemática con su etiqueta;
los herrajes son siluetas aproximadas a la coordenada de manilla del motor.
El muro y alféizar opcionales son referencias visuales, sin autoridad de
medición, montaje ni viento.

La cámara ofrece Interior, Exterior y Detalle; comienza en Interior.
No gira sola. La apertura finaliza en 240 ms y respeta reducción de movimiento.
La imagen descargada usa el render/cámara/pose visibles. Las miniaturas
comerciales usan la misma escena, poses, luces, materiales y cámara común.
DOC-01 consume SVG técnico actualmente: se conservan sus bytes históricos.

## Verificación

- 40 fixtures: 35 desde los goldens D03/D08 y cinco layouts P05
  evaluados con los parámetros D03 de corredera. Los diagramas OXXO se
  transportan como SLIDE para evaluación (el archivo de símbolos conserva
  su contrato de dibujo). Las correderas simples no emiten hechos de hoja;
  se prueba su decodificador histórico y dirección declarada. Regeneración:
  `python scripts/generate_scene3d_fixtures.py`; comprobación `--check`.
- `Product3DScene.test.ts` y `poses3d.test.ts`: 68 casos pasan. Comprueban
  pivotes anclados, recorrido/altura/carril, manillas por hoja, matrices
  comunes, planta abierta y longitud constante en toda interpolación.
- Diez pruebas de autoridad/estados en [autoridad](captures/3d-fisico/autoridad/validacion.json):
  bicolor blanco/antracita, foliado sin textura, falta de hojas evaluadas,
  contexto perdido/reintentar, vacío, carga, sin permiso y sin WebGL.
  La animación normal tiene una imagen intermedia distinta y alcanza una
  pose estable; reducción de movimiento llega directamente a la final.
- Paridad interactivo/comercial a 1.000 × 601 píxeles: diferencia media
  RGB 0,0183–0,0184 sobre 255 por rasterización de bordes. Se comparten
  geometría, cámara, material, luces, conversión y entorno.
- [40 tipologías](captures/3d-fisico/tipologias/validacion.json): cerrada,
  abierta, exterior, despiece y PNG; 38 operables y dos fijos, cero errores.
  Se inspeccionaron comparaciones de las 40, puerta, plegable, HST/PSK,
  correderas por carril y despiece. [Antes](captures/3d-fisico/antes/) conserva
  el HST sin apertura; la ampliación final corrige su tamaño a 1024 px.
- [14 recorridos](captures/3d-fisico/recorrido/validacion.json): seis editor
  (1440/1280/1024 claro/oscuro), ocho portal (incluye 390), guardar/recargar,
  abrir/abatir, Interior/Exterior/Detalle, muro, corte/despiece, teclado,
  PNG y dibujo ampliado. Cero errores/desbordes y cero Catálogo público.
- [Preservación](captures/3d-fisico/autoridad/preservacion.json): diseño,
  BOM completa y precio persistido mantienen exactamente su SHA-256 tras
  controles 3D, guardado y recarga; no se confunde con un campo ausente.
- `ux:capture`: [editor](captures/3d-fisico/ux/posicion-edicion/report.json)
  y [portal](captures/3d-fisico/ux/portal-vigente/report.json), 16 vistas sin
  hallazgos, errores HTTP/consola o desbordes. Token público sustituido en
  reportes; credenciales y utilidades locales no se publican.
- [281 PNG](captures/3d-fisico/compresion.json) comprimidos sin cambiar
  píxeles; la última compresión ahorra 107.032 bytes adicionales. `make lint`, `make typecheck`, `make test` y `make build`: PASA sobre el código final.
  Motor 1.006 + dos xfail históricos, backend 1.544 y frontend 1.122 en 98
  archivos; goldens byte a byte y 40 fixtures reproducibles. No cambió SQL/RLS;
  los cuatro checks de GitHub siguen como condición del merge.

## Pase editorial

Primera ronda: se reemplazó el control global por hojas independientes y
paquetes físicos; se borró el foliado aleatorio para respetar el recurso de
catálogo; se amplió el visor y sus controles se plegaron en Hojas. Se elimina
la representación gris fija de las aperturas avanzadas y el código anterior
de poses/materiales que ya no se consume.

Segunda ronda: se corrigió el cierre tapado al ampliar; se igualó la conversión
de color de visor/exportación, con bordes esquemáticos compartidos; se conservó
el decodificador de corredera simple al verificar que su motor no emite hechos
de hoja. Se ajustó Detalle a la manilla abierta y la voz de portal/oficina.

Momento de firma: abrir una hoja sobre su eje/carril real en 240 ms, con
reducción de movimiento. Capacidad del §8: cara interior/exterior y hoja
individual con bicolor sellado. La ampliación pliega temporalmente la planta
para dar espacio al 3D y la recupera al reducir/cerrar. Se inspeccionó el
resultado a 1440/1280/1024 claro/oscuro y portal 390.

| Ítem | Resultado | Evidencia |
|---|---|---|
| R1 · números | PASA | Cotas/precios del editor heredados en Mono; el visor no introduce cifras de fabricación. |
| R2 · radios | PASA | Tokens ≤ 4 px en controles/hoja; capturas y guardas. |
| R3 · jerarquía | PASA | Un visor sobre la zona de dibujo, borde y toolbar plegable. |
| R4 · naranja | PASA | Marca/aviso DEMO heredados; controles sin CTA naranja. |
| R5 · croma | PASA | Cromo teal/grafito; acabado físico desde carta, sin tintado por tema. |
| R6 · voz | PASA | Hoja, marco, manilla; portal/oficina distinguidos en ayuda y errores. |
| R7 · densidad | PASA | Hojas plegadas; ampliación con altura útil > 220 px y planta restaurable; inspector heredado. |
| R8 · estados | PASA | Autoridad: vacío, carga, error/reintentar, sin permiso y bloqueado, además de sin WebGL. |
| R9 · papel | PASA | Técnica heredada; estudio neutro independiente del tema en ambas caras. |
| R10 · selección | PASA | Contorno de módulo/hoja, sin resplandor; editor claro/oscuro. |
| R11 · apertura | PASA | 40 tipologías, ejes/carriles, manillas y paridad con planta del motor. |
| R12 · teclado | PASA | Foco canvas, flechas/zoom y botones; recorrido completo por teclado. |
| R13 · movimiento | PASA | 240 ms, interpolación rígida y prueba real de reducción de movimiento. |
| R14 · acción | PASA | Guardar conserva la primacía del editor; descarga local secundaria. |
| R15 · autoridad | PASA | Hechos motor/sellados, falta explícita; secciones/colores/herrajes aproximados etiquetados. |
| R16 · slop | PASA | Sin textura aleatoria, degradado, blur ni giro automático; guardas intactas. |
| R17 · tamaños | PASA | 14 recorridos y 16 UX, cero desbordes/errores; portal 390 y visor ampliado 1024 inspeccionados. |
| R18 · utilidad | PASA | Abrir/abatir/paso, cámaras, muro, corte/despiece, reducir/cerrar, export y recuperación probados. |
| R19 · firma | PASA | Apertura real en su eje/recorrido, en el mismo lenguaje que técnica/planta. |
| R20 · capacidad | PASA | Hoja individual y bicolor interior blanco/exterior antracita desde carta sellada. |

## Límites

La autoridad DEMO conserva su condición sintética. Un render no acredita
un fabricante, rendimiento térmico ni montaje real. Los documentos emitidos
no se reescriben. El portal histórico sin sección sellada muestra la
aproximación explícita y no consulta Catálogo vivo para rellenarla.

## Cierre de integración

PR [#151](https://github.com/KaraAliOsman/framedex/pull/151), squash
`ff210e7a439b861349d1d602c4137ebe4e65d0c8` en `integracion/v1`. Cuatro checks
PASA sobre `6bd3ff012f7c411c4dc34cee4c879180e119295a`, [corrida de CI](https://github.com/KaraAliOsman/framedex/actions/runs/38180492649).
El enlace temporal del fixture se revocó y el stack propio se detuvo.
Copilot informó falta de cuota; CodeRabbit no revisa esta base. El pase
editorial y la revisión de código propios se mantienen como evidencia.
