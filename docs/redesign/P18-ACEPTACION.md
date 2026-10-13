# P18 · térmica con autoridad

Código `5b786e7af6555b7fdb8e40399a604c3c909d94dc`, rama
`codex/P18-termico-oguc`, desde integración `c777b165`.
Evidencia: [antes proyecto](https://github.com/KaraAliOsman/framedex/blob/2db4e13171884b93a989e68508a55f5590f9b34d/docs/redesign/captures/termico-oguc/antes-proyecto.png),
[antes catálogo](https://github.com/KaraAliOsman/framedex/blob/2db4e13171884b93a989e68508a55f5590f9b34d/docs/redesign/captures/termico-oguc/antes-catalogo.png),
[matriz](https://github.com/KaraAliOsman/framedex/tree/2db4e13171884b93a989e68508a55f5590f9b34d/docs/redesign/captures/termico-oguc/matriz),
[estados](https://github.com/KaraAliOsman/framedex/tree/2db4e13171884b93a989e68508a55f5590f9b34d/docs/redesign/captures/termico-oguc/estados),
[ux:capture](https://github.com/KaraAliOsman/framedex/tree/2db4e13171884b93a989e68508a55f5590f9b34d/docs/redesign/captures/termico-oguc/ux) y
[DOC-01](https://github.com/KaraAliOsman/framedex/tree/2db4e13171884b93a989e68508a55f5590f9b34d/docs/redesign/captures/termico-oguc/documento).

## Resultado y límites

Uw usa las áreas visibles de la geometría del motor y fuentes revisadas para
Uf, Ug, Ψg y g. Las clases se ligan al espécimen exacto, con vidrio y herraje.
DEMO, fuentes ausentes, vencidas o contradictorias nunca acreditan cumplimiento.
La reglamentación se transcribió desde el DS15/2024 original y se cotejó contra
OGUC MINVU de marzo de 2026, con citas y hashes conservados.

El estimador declara la unidad térmica y abre F6 para conocer entradas y
certificados. El motor deriva OGT y gobierna por el mayor Uw de cada orientación.
La alternativa compara el catálogo visible evaluable con precio y propone
el menor neto indicativo compatible, con Δ y revisión humana. Aplicar y deshacer
usan las mismas operaciones del editor. No extiende el mínimo al mercado ni
reemplaza la tarifa aplicada o descuentos de una cotización emitida.

Anexo opcional DOC-01: valores y fuentes sellados al emitir. Una revocación
posterior conserva informe y PDF byte a byte. Las emisiones nuevas no imprimen
un Ug no revisado desde propiedades genéricas; los históricos conservan su
representación. El panel y anexo no acreditan cumplimiento completo del edificio.

No se implementan FEM, Up de rellenos opacos, térmica de paños solapados,
conjuntos sin método ni extensión de ensayo por rango. No se infiere zona por
comuna. Catálogo de fabricante, ensayos originales, revisión profesional y
plan de descontaminación son datos que el responsable conecta por obra.

## Verificación

- 57 pruebas focales: motor, documentos, serializers e integración PostgreSQL. Casos manuales:
  fijo `Uw=1.36624`, abatible `Uw=1.4265936`, dividido `Uw=1.4744`; áreas visibles
  distintas de corte y contexto decimal ambiental adverso. El golden se generó
  por `make goldgen`; los anteriores conservan sus bytes normalizados.
- Todas las celdas y fronteras de las tablas oficiales se cotejan con el fixture.
  Cada entrada ausente, fuente inválida, fachada no declarada, cantidad y
  orientación equivocada conserva una causa sin fabricar un número.
- Revocación con PDF idéntico, inmutabilidad de fuentes/inputs, RLS entre
  empresas y alternativa barata frente a otra más cara: pruebas PostgreSQL.
- Navegador: 1440×900, 1280×800 y 1024×768, ambos temas; completos, incumplimiento,
  DEMO, catálogo, F6, diff, aplicar y deshacer. Taller consulta, operario sin
  permiso y revisión sellada bloquean escritura también en HTTP.
- `ux:capture`: 16 vistas de proyecto/catálogo, incluyendo 390, sin hallazgos,
  errores HTTP/consola ni desbordes. DOC-01 de cuatro páginas inspeccionado,
  fuentes y resultados legibles sin colisiones.
- Gates de código: lint, tipos, tests y build PASA sobre el código final.
  Motor 1.052 (+2 xfail históricos), backend 1.551 y frontend 1.131.
  Database Gate completo PASA: 1.451 pgTAP y 16 térmicos adicionales sobre la
  misma base limpia, 558 integraciones, 19 E2E y upgrades poblados PG16.
  Docker Desktop tiene una fuente de bind distinta al runtime nativo: se
  sincronizó el archivo térmico y se ejecutaron sus 16 aserciones explícitas.
  El CI del PR vuelve a recorrer el repo completo antes de integrar.
- 69 PNG comprimidos con hash de píxeles conservado, 34 estados de matriz,
  nueve adicionales y cuatro trazas F6 finales sin hallazgos. La última prueba
  de alternativa verifica un candidato más barato que otro con distinto SKU
  de compra y costo; muestra un Δ monetario real, sin empate de tarifas.

## Pase editorial

Primera ronda: fuentes con norma, laboratorio y alcance explícitos; posiciones
compactas con ingeniería plegable; ubicación sin default silencioso. Se quitó
la repetición de causas generales en cada posición y la tabla de números sin
documento. Segunda ronda: clases ligadas al espécimen exacto; acciones de guardar
solo al existir cambios; precisión visible y traza explicando el redondeo. Se
quitó el Ug genérico sin autoridad de las emisiones nuevas y se corrigió el
destino de Catálogo. El momento de firma es F6 y la idea superior funciona como
alternativa del motor con Δ, simulación y deshacer.

| R | Resultado | Evidencia |
|---|---|---|
| R1 | PASA | Mono, unidades, coma decimal y precisión de presentación |
| R2 | PASA | Tokens y radios comunes ≤4 px |
| R3 | PASA | Filetes, peso y espacio; sin tarjetas anidadas |
| R4 | PASA | Naranja reservado a marca/intervención humana |
| R5 | PASA | Teal común en controles y enlaces |
| R6 | PASA | Taller y español; IDs técnicos fuera del texto visible |
| R7 | PASA | Posiciones compactas y formulario por sección |
| R8 | PASA | Vacío, carga, error, permiso y sellado/pendiente con causa |
| R9 | PASA | Lámina DOC-01 y elevación sobre papel |
| R10 | PASA | Selección del diff común, sin brillo |
| R11 | PASA | Dibujo compartido y símbolo de apertura del motor |
| R12 | PASA | Controles nativos etiquetados y foco común visible |
| R13 | PASA | Movimiento del sistema y reducción respetada |
| R14 | PASA | Guardar al cambiar; aplicar solo al revisar |
| R15 | PASA | Fuentes, alcance y Sin dato sin ceros suplentes |
| R16 | PASA | Guardas sin degradado, blur, brillo ni morado |
| R17 | PASA | Matriz y ux:capture sin desborde |
| R18 | PASA | API real, declarar/revisar/revocar y aplicar/deshacer |
| R19 | PASA | F6 explica cálculo y certificados |
| R20 | PASA | Alternativa mínima evaluable con Δ del motor |

Decisiones: [defaults P18](../decisions/valores-por-defecto.md).
Activación: [datos térmicos](../operations/ACTIVACION.md).
No requiere un proveedor remoto nuevo; conserva las integraciones sandbox
ya construidas y la IA real configurada en el entorno, sin publicar credenciales.
