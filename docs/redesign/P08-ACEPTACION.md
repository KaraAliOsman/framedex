# P08 · cotización guiada, emisión y acceso

Base `c77792eb`, rama `codex/P08-cotizacion-emision`. Verificación del
09-10-2026 con Supabase, Django, worker, Mailpit y Chromium locales.

La pestaña Cotización reúne un checklist accionable, los datos de cliente/obra,
las condiciones comerciales y el PDF real que recibirá el cliente. Los faltantes
abren su sección, hacen scroll, enfocan y resaltan el campo. El servidor valida
RUT módulo 11 y los requisitos comerciales, además de la autoridad del motor.
No se puede confirmar antes de cargar los bytes verificados del PDF. La acción
«Emitir y enviar al cliente» muestra revisión, total, moneda, fecha, destinatario
y consecuencia de reemplazar una revisión anterior.

## Documento y autoridad

Preparación y freeze histórico comparten composición y persistencia. El preview
es privado por organización/actor y fija fecha, condiciones, snapshot y PDF.
Su QR no está activo. Emitir vuelve a componer y exige igualdad del snapshot,
destinatario y SHA del archivo, luego copia los mismos bytes a DOC-01 sellado.
La misma transacción activa DOCUMENT y crea el correo P25. Un recibo inmutable
liga preview, revisión, artefacto, aprobación y correo. Reintentos y dos clics
concurrentes producen un solo sello y envío. Si falla la transacción, se limpian
solo objetos subidos por ese intento, conservando el preview revisado.

Las cuatro tablas nuevas llevan org_id, RLS, grants acotados, scope guards y
triggers de inmutabilidad. El vencimiento efectivo se agrega como evidencia;
no cambia identidad, fecha original ni QR de P09. Portal, correo, Hoy y ledger
consumen la misma proyección. Regenerar revoca el enlace anterior y recupera
el nuevo por recibo cifrado; el QR impreso conserva su estado revocado.
Los GET/POST públicos no cachean éxito ni errores: después de un 410 vencido,
una nueva consulta muestra la revocación efectiva.

El cambio global usa el registro único `apply_to_positions`, simulación real
de venta/validez y deshacer guardado. Se ofrecen vidrio, acabado, serie y altura
de manilla del catálogo. La altura común se expande contra destinos físicos
reales, sin asignar manilla a un fijo; francesas/correderas conservan restricciones.
Los golden históricos mantienen sus valores; se agregan dos casos de altura
común, FRENCH_COMMON_HANDLE y SLIDING_COMMON_HANDLE.

## Recorrido de aceptación

El proyecto DEMO P-000551 contiene doce posiciones reales. El recorrido pasa:
checklist y RUT inválido → precio aplicado → condiciones/antecedentes → PDF A
verificado → emisión A → respuesta perdida después del commit → recuperación
del mismo recibo/correo → copia y fallback manual → cliente abre A y solicita
cambios con comentario → Hoy y campana → sucesora B → Low-E global en doce
posiciones → aplicar/deshacer/aplicar → precio → PDF B y confirmación de
reemplazo → emisión B → A reemplazada → aprobación B.

El PDF A descargado después de B coincide byte a byte con el anterior. La
revisión anterior conserva su decisión/comentario y queda bloqueada para
edición. El fallback selecciona el enlace completo; su captura enmascara la
capacidad. No se publican sesiones, signed URLs ni PDFs con acceso activo.

Un proyecto independiente verifica modificar vencimiento, expiración pública,
regeneración, QR anterior revocado y revocación del nuevo enlace, conservando
ambas identidades. La búsqueda de llamadas en `frontend/src/features` encuentra
una sola `quotationIssue`; no queda llamada UI a freeze, compartir o enviar
QUOTE por otro camino. Las APIs históricas permanecen compatibles.

Evidencia:

- [Antes](captures/cotizacion-emision/antes/proyecto-1440-claro.png).
- [RUT pendiente](captures/cotizacion-emision/recorrido/02-rut-invalido.png),
  [respuesta perdida](captures/cotizacion-emision/recorrido/06-respuesta-perdida.png)
  y [fallback](captures/cotizacion-emision/recorrido/07-portapapeles-alternativa.png).
- [Campana](captures/cotizacion-emision/recorrido/12-campana-cambios.png),
  [diff Low-E](captures/cotizacion-emision/recorrido/13-vidrio-global-impacto.png)
  y [B aprobada](captures/cotizacion-emision/recorrido/19-revision-b-aprobada.png).
- [Vencimiento](captures/cotizacion-emision/enlaces/03-portal-vencido-390.png),
  [regeneración](captures/cotizacion-emision/enlaces/05-regenerado.png) y
  [revocación](captures/cotizacion-emision/enlaces/08-portal-regenerado-revocado-390.png).
- [Matriz específica](captures/cotizacion-emision/matriz/matriz.json),
  [captura oficial de proyecto](captures/cotizacion-emision/ux-proyecto-detalle/report.json),
  [portal](captures/cotizacion-emision/ux-portal-aprobada/report.json) y
  [Hoy](captures/cotizacion-emision/ux-panel/report.json).

## Dos rondas editoriales

Primera ronda:

1. Se retiran compartir desde el encabezado, mailto/WhatsApp y el compositor
   QUOTE externo. Preparación, confirmación, recibo y recuperación comparten
   una sola región. Se conserva el compositor de pagos y el historial P25.
2. Se reemplaza el muro técnico inicial con checklist que enfoca el faltante;
   posiciones y condiciones avanzadas quedan plegadas. Cliente/dirección se
   completan sin alterar la autoridad de precios ni una revisión sellada.
3. Se sustituye la emisión sin vista por el PDF real privado, con verificación
   de bytes, confirmación concreta y replay de un recibo persistente.

Segunda ronda:

1. Se separa vigencia comercial de vigencia de acceso, preservando P09. Se
   añaden defaults configurables e historia append-only, reintento cifrado,
   microcopy pública de usted y no-cache tras detectar un 410 reutilizado.
2. La matriz corrige contraste de checks/decisión pública y ayudas menores
   de 11 px en Ajustes; fechas/huellas usan Mono. El error de transporte
   conserva causa y reintento sin borrar los antecedentes.
3. La inspección corrige densidad a 1024: cliente/obra en dos columnas,
   checklist persistente y espacio bajo el shell. Ocho campos caben sin scroll;
   el PDF real conserva el papel y controles de revisión, con captura dentro
   del viewport que evita desplazar artificialmente los elementos sticky.

F11 aparece en la revisión preparada y en el historial sellado; F2 conserva
huella de BOM/PDF en detalles y cajetín real. La idea del §8 funciona:
checklist que se cumple con los datos de obra y exactamente el PDF a emitir.

## Rúbrica y gates

Matriz específica: 74 vistas sin hallazgos ni desbordes; teclado PASA.
Captura oficial: 24 vistas entre proyecto, portal y Hoy, sin nuevos hallazgos,
desbordes ni errores HTTP/consola. Se cubren 1440×900, 1280×800, 1024×768 y
390×844 para Hoy/portal, en claro y oscuro. Las 126 capturas PNG se comprimen
sin pérdida y se verifica igualdad de todos sus píxeles (17.406.022 bytes).

| Revisión | Resultado | Evidencia del alcance P08 |
|---|---|---|
| R1 · números, unidades y formatos | PASA | Montos/fechas/huellas usan formateadores compartidos y Mono tabular. |
| R2 · radios e inglete | PASA | Tokens de hasta 4 px; inglete limitado al PDF/hoja de revisión. |
| R3 · jerarquía y capas | PASA | Tres regiones delineadas, checklist/PDF persistentes, sin capas en competencia. |
| R4 · uso de naranja | PASA | Marca y aviso de antecedentes humanos; acción de emisión teal. |
| R5 · croma de interfaz | PASA | Grafito/teal de tokens; semánticos para estados con texto. |
| R6 · vocabulario y voz | PASA | Estimador tuteado; portal de usted; estados y campos en español. |
| R7 · densidad | PASA | Ocho campos totalmente visibles bajo el shell a 1024×768. |
| R8 · cinco estados | PASA | Matriz vacío, carga retenida, error/reintento, sin permiso y bloqueo de precio. |
| R9 · papel sobre mesa | PASA | PDF real en Chromium, papel claro dentro de mesa en ambos temas. |
| R10 · selección | PASA | Selección global con control/contorno y tinte; sin elevación decorativa. |
| R11 · iconos y apertura | PASA | Gramática DIN común P05/P09 conservada en el PDF y miniaturas. |
| R12 · teclado y foco | PASA | Checklist abre antecedentes, hace scroll y enfoca el campo; recorrido de teclado PASA. |
| R13 · movimiento | PASA | Tokens y reduced-motion; cargador de cota, sin shimmer. |
| R14 · acción principal | PASA | Preparación en antecedentes; una confirmación y una emisión en región PDF. |
| R15 · fuente de números | PASA | Precio, validez y diff proceden del motor; falta de autoridad no se convierte en cero. |
| R16 · ausencia de efectos prohibidos | PASA | Detector oficial/específico y guardas sin hallazgos en el alcance. |
| R17 · anchos y recortes | PASA | Cero desbordes en las 74 vistas; historial y portal a 390. |
| R18 · acciones reales | PASA | Única llamada UI a quotationIssue; copia/fallback, PDF, controles y undo verificados. |
| R19 · firma | PASA | F11 en revisión/sello e historial; F2 en cajetín y detalles de huella. |
| R20 · capacidad del §8 | PASA | Checklist accionable y emisión de los mismos bytes del PDF revisado. |

## Verificación técnica

Fuente de implementación `d6bf84f4f9b4aa6ecdef3dfe16b86f39ec86bcbe`,
con regresión de RUT histórico en `fb5b82d11c18e50fe9856e3b5e8b63023a27eef6`.
Gate nativo completo: `make lint`, `make typecheck`, `make test` y `make build`
PASA; 848 tests del motor (+2 xfail), 1.434 backend y 954 frontend. OpenAPI/orval
reproducibles, guardas y golden byte check PASA. Los nueve golden de operaciones
anteriores conservan exactamente sus valores; se añaden dos casos físicos.
El RUT conserva el rango histórico de cinco a ocho dígitos del contrato SII,
incluidos los casos módulo 11 de cinco y seis dígitos, sin admitir cuerpo nulo.

El gate SMTP toma el puerto declarado del proyecto aislado, fuerza el proveedor
sandbox y descarta credenciales MAIL heredadas. Seis regresiones comprueban
aislamiento y rechazo de autoridad inválida. El E2E permanente, en
`e841ae29`, verifica preview, confirmación y emisión A/B. Espera SENT (aceptación
SMTP), encuentra un único correo en el Mailpit del gate por Message-ID, asunto
y destinatario, y comprueba SHA y bytes de su adjunto contra el PDF revisado.
Conserva los bytes de A después de B. El E2E focal pasa; no presume lectura
humana ni relaja confirmación o revisión del visor real.

Database Gate completo PASA sobre `e841ae29`: 86 archivos / 1.249 pgTAP,
455 integraciones PostgreSQL, 19 E2E y migraciones/seed en PostgreSQL 16 con
los diez verificadores de upgrade. El teardown confirma puertos 8000/5173
libres y detiene solo el stack del gate. Cuatro checks de CI y squash se
registran después de su resultado; ESTADO sigue en curso hasta integrar.

## Defaults, sandbox y límites

Vigencia comercial 15 días (1–365) y revisión del PDF 30 minutos (5–60),
configurables en Ajustes > General > Documentos; fechas históricas conservadas.
Anticipo 50/50 y condiciones se editan por organización o cotización y se sellan.
No se inventa plazo, garantía ni autoridad térmica. Véase
[valores por defecto](../decisions/valores-por-defecto.md).

Correo usa el adaptador existente con Mailpit sandbox. SMTP de dominio propio
requiere [activación](../operations/ACTIVACION.md); el estado de entrega incierta
P25 permanece explícito. El catálogo DEMO no certifica fabricación y una
cotización no libera producción sin antecedentes/confirmación. Layout DOC-01
permanece en P09; portal completo y cobranza corresponden a P10/P11.
