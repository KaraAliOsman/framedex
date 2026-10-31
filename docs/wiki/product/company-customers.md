---
type: concept
status: active
updated: 2026-10-22
volatility: medium
verified_ref: e317edb9b76b4346e33aa3b60b4783b4cc2f0a99
sources:
  - P02d gpt/dk2-p02d-lenguaje-ejemplos, corrección de vigencia de la vista previa, 2026-10-22
  - P22 PR https://github.com/KaraAliOsman/framedex/pull/148, CI 4/4 sobre f55db702b6f24b39da3f6b279a895833758461a4, squash e317edb9b76b4346e33aa3b60b4783b4cc2f0a99, 2026-10-11
  - P22 revisión a3bffc10c4ea43f9bec221a47ecaaefbe2b15bfa, gates completos y tres recorridos reales, 2026-10-11
  - backend/projects/clients.py
  - backend/projects/client_history.py
  - backend/projects/company.py
  - backend/tests/integration/test_company_clients.py
---

# Empresa, clientes y ajustes

La ficha distingue persona, empresa y tipo histórico desconocido. Valida RUT
nuevo, detecta duplicados canónicos dentro de la organización y conserva
contactos con rol, direcciones de obra y notas con autor/fecha. Una fusión
compara ambas fichas, exige motivo, confirmación y revisiones vigentes. El
bloqueo compartido serializa cambios de hijos y fusión; las copias conservan
procedencia. El origen queda como alias histórico, sin reescribir proyectos,
cotizaciones ni sus documentos. RUT distintos no vacíos impiden fusionar.

Elegir dirección de obra copia texto al proyecto y exige pertenencia a la
ficha y organización. Facturación y entrega son campos distintos. El dossier
sigue aliases y consulta la elección aceptada de P10, revisiones, ledger y
documentos reales. El motor agrega saldos con Decimal por moneda; una obra
sin importe acreditado conserva «Sin dato» y no aporta cero a una suma.

Una edición explícita del texto de entrega desvincula la dirección maestra,
incluso si la API parcial conserva el mismo selector o se escribe con RLS.
Seleccionar otra dirección vuelve a copiarla; las revisiones selladas se
conservan. El directorio filtra, cuenta y pagina en SQL, y carga contactos y
direcciones de la página por lote. Solo el filtro de saldo consulta acuerdos
y pagos por lote y usa las proyecciones del motor por moneda, sin descargar
documentos ni sustituir los importes desconocidos. La regresión real verifica
mil coincidencias, aliases y el límite de consultas.

Las estaciones se crean o actualizan por su código dentro de la organización.
Editar conserva ese código, la misma identidad y el número de filas; cancelar
restaura el formulario de creación. El guardado anuncia que quedará activa.

Ajustes presenta una sección por tarea. Identidad legal, usuarios y política
de acceso son del dueño; marca y condiciones pertenecen a dueño/estimador.
Los roles de planta conservan acceso de cuenta y sus controles táctiles.
La moneda de empresa propone el cálculo nuevo, sin reinterpretar precios
aplicados, tarifas laborales ni revisiones emitidas. `quotation_currency`
mantiene esa preferencia; `currency` conserva la autoridad base. El cálculo
convierte USD→CLP únicamente con snapshot de cambio declarado y el buffer
contractual del 5 %. Un costo local CLP cotizado en USD se divide por la
observación explícita CLP/USD, sin reserva de importación. El replay conserva
esa fuente; no supone tasas. Numeración lee secuencias reales, solo como
referencia sin reserva. Estaciones y rutas reutilizan la autoridad de planta.

El PDF vivo usa una revisión real, validada por su huella, y el renderer DOC-01
común. Cambiar marca, papel, pie, vigencia y condiciones conserva el precio
y moneda sellados; esa preparación no modifica el artefacto histórico. Sin
obra o revisión hay una causa y destino para resolverla. Guardar identidad
comparte su revisión con Marca antes de anunciar éxito y conserva su borrador.
La vigencia propuesta en la vista previa usa explícitamente el día de
`America/Santiago`, igual que Preparar emisión, independientemente de la zona
activa de Django. Dos regresiones con reloj fijo a ambos lados de medianoche
verifican el PDF real sin cambiar la revisión sellada.

El dueño siempre exige segundo factor. La preferencia adicional exige MFA
a los demás y se aplica en API y RLS, manteniendo el bootstrap mínimo para
configurarlo. La invitación cifra su capability en la outbox, vence en siete
días y exige correo vivo verificado y clic humano de aceptación. Provisionar
Auth no crea membresía. La primera aceptación prevalece; desactivar o revocar
conserva auditoría y no puede evitarse con un enlace anterior.

El alta inicial confirma Empresa, Comercial y Documentos antes de guiar
serie, cliente, obra y posición. Los valores sugeridos son editables y su
efecto se explica; no se inventa un precio para la miniatura. Integraciones
consume los estados comprobados de los adaptadores y las instrucciones de
[ACTIVACION](../../operations/ACTIVACION.md). Hosting, dominio, SMTP, Flow y
DTE productivos conservan su activación externa. Los fixtures siguen DEMO.

La propagación de identidad fija y restaura tanto el JWT JSON como el subject
individual que usa PostgreSQL, incluyendo solicitudes anidadas y workers.
La proyección privada `stock_incoming` entrega solo cantidades e identidad
física al lector autorizado; el estimador no recibe órdenes ni precios
de proveedor. Las regresiones usan Auth real y prueban aislamiento.
