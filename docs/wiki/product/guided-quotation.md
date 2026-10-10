---
type: concept
status: active
updated: 2026-10-09
volatility: medium
verified_ref: e841ae294f2a9fc849b4f9d0847beceecf1fb07c
sources:
  - docs/cola/prompts/P08-cotizacion-emision.md
  - backend/documents/issuance.py
  - backend/tests/integration/test_guided_quotation.py
  - frontend/tests/e2e/auth.spec.ts, SHOT-10, e841ae29
  - docs/redesign/P08-ACEPTACION.md
---

# Cotización guiada y enlace del documento

## Hechos verificados

La pestaña Cotización guía desde los datos de cliente/obra hasta el PDF real,
su confirmación y el sello. El checklist enfoca el campo exacto, abre los
antecedentes plegados y declara los bloqueos de precio/fabricación. El backend
valida RUT módulo 11, correo, dirección, vigencia y condiciones comerciales.
El rango del cuerpo del RUT conserva los cinco a ocho dígitos del contrato
tributario existente; el cuerpo nulo y un verificador incorrecto se rechazan.
El calendario calcula montos mediante el motor; no convierte texto en dinero.

La preparación compone la misma revisión que la emisión histórica, con fecha
fijada, preferencias y autoridad congeladas. Su PDF se guarda privado y su QR
no concede acceso al cliente hasta emitir. La confirmación liga destinatario,
huella del PDF y del snapshot. La emisión vuelve a componer, compara huellas
y verifica los bytes antes de sellar exactamente el archivo revisado.

Una transacción activa el enlace DOCUMENT, conserva el artefacto y crea el
outbox P25. El recibo inmutable por preview permite recuperar una respuesta
perdida sin otro sello ni correo. Dos clics concurrentes convergen al mismo
recibo. Una falla de transacción elimina únicamente uploads propios del
intento. Las APIs históricas de freeze se conservan para sus consumidores;
la UI tiene una sola llamada a `quotationIssue` y retira compartir/enviar
cotización por rutas alternativas. La cobranza conserva su compositor de pago.

SHOT-10 verifica SENT como aceptación SMTP y encuentra un único Message-ID,
destinatario y asunto en el Mailpit aislado. Su único adjunto PDF conserva SHA
y bytes de la vista previa; el PDF A se recupera idéntico después de emitir B.
La recepción sandbox no afirma lectura humana ni entrega única de SMTP real.

## Vigencia y decisiones

La vigencia comercial inicial es 15 días corridos, propuesta desde la fecha
local de Chile. La revisión privada del PDF dura 30 minutos. Ambas se cambian
en Ajustes > General > Documentos, con límites de 1–365 días y 5–60 minutos.
Una preparación histórica conserva su fecha o su ausencia: no se completa
retroactivamente. Cambiar la obra o condiciones exige otro PDF.

El vencimiento efectivo del acceso procede de un historial append-only.
Nunca altera el vencimiento original, identidad DOCUMENT, QR ni PDF de P09.
Portal, outbox, Hoy e historial consultan la misma proyección. Regenerar revoca
el acceso anterior y crea un SHARE para la misma revisión, con recibo cifrado;
un reintento recupera ese enlace. No cambia el QR del PDF ya sellado.
Éste muestra honestamente la revocación. Los errores y respuestas públicas
usan no-store/no-cache para volver a verificar el estado después de un 410.

El estado del enlace conserva vistas, decisión y comentario. La solicitud
de cambios llega a Hoy y campana; una sucesora conserva la decisión anterior
y el PDF original. Los cambios globales de vidrio, acabado, serie o manilla
usan `apply_to_positions` del registro IA2, con simulación del motor,
precio/validez y deshacer. La altura común expande solo destinos físicos
con manilla; francesas y correderas mantienen sus restricciones reales.

## Intención y límites

El objetivo del dueño es emitir sin sorpresas, con F11 (sello) y F2 (huella),
un checklist que se cumple al completar la obra y la vista del PDF real.
Windowmaker inspira los cambios globales; no es autoridad técnica.
El board histórico no sustituye la gramática DIN de la constitución.

DEMO no certifica fabricación. Emitir cotización no libera OT con evidencia
incompleta ni sin confirmación humana. P10 cubre el portal completo y P11 la
cobranza. SMTP externo se activa con ACTIVACION.md; Mailpit permite el recorrido
sandbox. La aceptación no afirma entrega única de SMTP ni lectura humana del
correo: conserva el estado explícito de la infraestructura P25.
