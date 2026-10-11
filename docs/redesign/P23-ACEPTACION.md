# P23 · Despacho, terreno y postventa

Verificado en `codex/P23-terreno-postventa`, desde `c7cbb218`, con Supabase
local propio, Auth real, Django, worker y Chromium. La integración y sus
recuentos finales se añaden después de los gates; esta evidencia no los sustituye.

## Resultado y recorridos

Despacho planifica por fecha, franja y equipo; registra cada bulto antes de
salir y emite la GD con la dirección física de P13. El instalador abre Terreno,
su agenda privada, la obra y la unidad exacta escaneada. Checklist, foto,
incidencia y recepción con nombre/RUT/firma producen un acta privada inmutable.
El jefe diagnostica y autoriza por separado remake, compra adicional o servicio.
Las decisiones no se liberan desde el teléfono ni por una incidencia automática.

- Planificación → carga → salida/GD → entrega → instalación → daño → acta →
  diagnóstico → RM: PASA en navegador real, a 390 px.
- Medición de tres puntos → foto → revisión del estimador → diff del motor →
  borrador correctivo: PASA. El caso verificado proyecta Δ neto de $1.923;
  la revisión aprobada y sus documentos conservan sus bytes.
- Regulación → diagnóstico → visita de servicio → foto/firma/acta → cierre:
  PASA. Un servicio no acredita instalación de otra unidad.
- Faltante → autorización de material de la pieza sellada → OC adicional →
  envío → recepción útil → cierre: PASA en PostgreSQL. Conserva las capacidades
  y asignaciones originales; no libera ni reutiliza su compra.
- Cancelación antes de salida → liberación de bultos → nueva agenda: PASA.
  Después de salir, la cancelación no sustituye el retorno con evidencia.
- Mala conexión, incluso con `navigator.onLine=true` → recarga → acción local
  → pérdida de la respuesta después del commit → replay: PASA. Dos solicitudes
  conservan un UUID y producen una incidencia. La cola no cambia el payload.
- Actor/organización, membresía, segundo factor, unidad, QR adversario,
  recepción parcial y autoridad histórica: regresiones PostgreSQL PASA.

## Evidencia visual

[Antes](captures/terreno-postventa/antes/) conserva 24 vistas del ref base.
[Despacho](captures/terreno-postventa/ux/despacho-matriz/) y
[Terreno](captures/terreno-postventa/ux/terreno-matriz/) cubren 1440×900,
1280×800, 1024×768 y 390×844, claro/oscuro: 40 vistas, cero hallazgos o
desbordes. [Estados](captures/terreno-postventa/estados/) registra vacío,
carga, error de transporte, sin permiso y bloqueo con causa.
[Recorrido](captures/terreno-postventa/recorrido/) y
[sin conexión](captures/terreno-postventa/offline/) conservan capturas y
verificación del replay. Los PNG se comprimen sin modificar sus píxeles.

`servicio-prueba.pdf` es el acta final de servicio, una página Carta, con
firma de tinta oscura y elevación DIN del renderer común. `acta-prueba.pdf`
y `guia-prueba.pdf` conservan la primera emisión del ensayo: dos páginas y
firma clara en la primera acta. Son evidencia histórica inmutable; el renderer
nuevo y la firma sobre papel se verifican sin reemplazar esos documentos.
`guia-renderer-actual-preview.pdf` verifica el renderer final sobre el payload
sellado: una página Carta, QR de 22 mm y franja Mañana en español. La tabla
de bultos reúne los totales cuando hay varias unidades; se quitó el resumen
duplicado que enviaba la firma a una segunda página.
El QR final también se decodifica desde los píxeles del PDF a 110 dpi y
reconcilia exactamente OT y unidad.

## Pase editorial, dos rondas

Primera ronda: se retiró el cierre ciego de instalación en Producción y se
conectó Terreno; se eliminó el enlace duplicado de salida; se hizo explícita
la diferencia entre guardar en el teléfono y sincronizar con acceso vigente.

Segunda ronda: controles y contraste usan tokens y densidad según persona;
la firma conserva tinta oscura sobre papel; la recarga distingue red degradada
de acceso revocado. Se quitó CSS muerto, el aviso de sincronizar cero registros
y el `main` anidado en la oficina. Los selectores tienen nombres accesibles.
La última revisión impide que una respuesta tardía recree evidencia local
después de salir; la regresión usa IndexedDB real y conserva la cola vacía.

F9 presenta una unidad por pantalla con elevación/ubicación/checklist. F2
reconcilia los bytes del QR con el bulto exacto. La idea del §8 conecta una
medición contextual con el diff del motor y conoce perfil, vidrio, herraje y
piezas de una incidencia usando la revisión sellada, aunque cambie el catálogo.

| Regla | Resultado | Evidencia |
|---|---|---|
| R1 | PASA | Medidas/Δ con formateadores comunes y Mono tabular. |
| R2 | PASA | Radios de tokens; papel conserva el inglete común. |
| R3 | PASA | Jerarquía por líneas; agenda, unidad y decisión sin capas decorativas. |
| R4 | PASA | Naranja solo requiere persona; acciones usan teal. |
| R5 | PASA | Cromo común en ambos temas. |
| R6 | PASA | Obra, bulto, posición, regulación, Mañana/Tarde; sin enums visibles. |
| R7 | PASA | Oficina compacta, terreno 16 px y controles de al menos 44 px. |
| R8 | PASA | Cinco estados ejercitados, causas y siguiente acción. |
| R9 | PASA | Firma/papel claros y acta con renderer documental común. |
| R10 | PASA | Posición elegida con contorno y tinte; edición mediante controles. |
| R11 | PASA | Escáner común, dibujos y símbolos DIN compartidos. |
| R12 | PASA | Labels explícitos y foco tokenizado; firma también permite limpiar. |
| R13 | PASA | Sin movimiento ornamental; reduce-motion común. |
| R14 | PASA | Una decisión por etapa: registrar, recibir o autorizar. |
| R15 | PASA | Ingeniería sellada, diff del motor y garantía explícita; faltantes con causa. |
| R16 | PASA | Sin degradados, blur, brillo ni morado IA. |
| R17 | PASA | Matrices sin hallazgos/desbordes en los cuatro tamaños. |
| R18 | PASA | Cada carga, foto, firma, compra, RM y servicio tiene efecto persistente. |
| R19 | PASA | F9 una posición; F2 escaneo abre la unidad exacta. |
| R20 | PASA | Medición → revisión con diff real; trazabilidad desde snapshot sellado. |

## Autoridad, decisiones y límites

La garantía exige días e inicio declarados en las condiciones aprobadas.
Texto libre no produce una fecha; se muestra Sin dato. La aprobación usa la
elección real de P10. Entrega/instalación usan el primer hecho firmado de la
unidad exacta, no la última acta ni un servicio. El cálculo de plazo es puro
y tiene golden. Emitir un acta parcial no acredita toda la OT.

La copia IndexedDB pertenece a actor+organización y se elimina al salir o
cambiar de actor u organización. No guarda costos, elecciones de oficina ni URLs firmadas.
La lectura directa de SQL concede metadatos, con RLS; el JSON sellado solo
se proyecta desde la API. El payload JSON de un acta se decodifica antes
de filtrar la autoridad comercial, incluso cuando el driver lo entrega como texto.
El service worker solo conserva código/fuentes y la página `/field`; nunca
API, Auth, evidencia ni capacidades. Revocar acceso impide sincronizar y
abrir recursos nuevos; una copia ya descargada puede verse sin señal hasta
que ese teléfono reciba la revocación o cierre sesión.

Se requieren HTTPS, Storage privado y asignaciones reales para terreno
productivo, según [ACTIVACION](../operations/ACTIVACION.md). Fotos y firmas
locales son datos personales: use teléfonos protegidos y cierre la sesión
al cambiar de responsable. El catálogo del fixture sigue DEMO; no acredita
certificación ni autoridad técnica real. No se conectó una ruta automática
de vehículo ni una emisión fiscal productiva: se preserva la GD interna y
los adaptadores existentes. Las decisiones se registran en
[valores por defecto](../decisions/valores-por-defecto.md).

## Gates locales finales

Código `c0d12cd8ca8ad7c391ba8bbb350c2971418fd800`: lint, typecheck, test y build PASA. 914 tests de motor (+2 xfail preexistentes), 1494 backend, 1026 frontend; golden anteriores intactos y byte check PASA. Database Gate completo: 1427 pgTAP en 94 archivos, 549 integraciones, 19 Auth E2E y doce programas de upgrades poblados PostgreSQL 16. Las concesiones ambientales de Supabase se revocan antes de asignar lectura al navegador; RLS y triggers conservan su autoridad. Los procesos propios están detenidos y el fixture se conserva. CI y squash se registran al integrar.
La comprobación de garantía usa el mismo ámbito privado que workspace/Hoy; la regresión exige además que su consulta directa desde authenticated sea denegada. Los permisos del navegador permanecen limitados a metadatos.

## Correcciones de la revisión del PR

Las siete observaciones publicadas se verificaron contra el código. La agenda
conserva el identificador del viaje y rechaza otra salida abierta de la misma
OT, incluso con unidades disjuntas. Salida, entrega y cancelación verifican
ese identificador, estado y carga bajo bloqueo; una modificación desde
Producción no permite cancelar otro saldo.

Un servicio agenda una unidad por visita: trabajo, foto y acta acreditan la
misma unidad. El selector sustituye la selección anterior y explica la causa.
Las comprobaciones, medidas y datos de incidencia se validan antes de subir
la foto. Los archivos nuevos tienen una dirección propia del intento; una
excepción del renderer, SQL o cierre de la transacción HTTP los compensa sin
borrar evidencia sellada. La regresión conserva fotos anteriores byte a byte.

Una RM de terreno conserva su diagnóstico aunque la OT tenga una falla QC
anterior. El instalador registra evidencia; diagnóstico, cancelación de
salidas y cierre de postventa permanecen en oficina. La autorización precede
también al replay. La garantía consulta la aprobación inmutable de la revisión
elegida, incluida una visita de medición agendada antes del acuerdo. No cambia
el contrato P10: aprobar después de liberar producción sigue rechazado.

Cambiar de organización elimina agenda y fotos pendientes de la organización
anterior antes de resolver la siguiente. Las respuestas tardías no restauran
esa copia; otra organización y otro actor conservan su propio ámbito. Las
regresiones ejercitan IndexedDB y el componente de sesión de la app, con el segundo
contexto aún sin resolver.
