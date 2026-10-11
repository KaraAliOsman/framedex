---
type: concept
status: active
updated: 2026-10-11
volatility: medium
verified_ref: 68674c22ec1ffd303c572764bf472c6587d58d84
sources:
  - backend/projects/clients.py
  - backend/projects/client_history.py
  - backend/projects/company.py
  - backend/tests/integration/test_company_clients.py
  - docs/redesign/P22-ACEPTACION.md
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
