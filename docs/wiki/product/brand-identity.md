---
type: concept
status: active
updated: 2026-10-08
volatility: medium
verified_ref: codex/P25-marca-identidad
sources:
  - docs/design/marca.md
  - docs/redesign/P25-ACEPTACION.md
  - backend/notifications/
  - supabase/migrations/20270108000000_brand_and_mail.sql
---

# Marca, emisor y correo

La dirección B sustituye la O del logotipo por una sección de perfil. Los
contornos proceden de Plex Sans 600 autoalojada; la geometría óptica del favicon
conserva pared y tabique a 16 px. La cota D pertenece a Acerca de y correo
interno. El Orb conserva su API y estados de trabajos, con poses estáticas,
grafito y una órbita teal. La constitución prevalece sobre los brillos y bucles
del estudio histórico. Esta es intención de identidad aplicada en código;
no aporta autoridad de fabricación.

El onboarding guarda un borrador por organización y llega a una posición
real. Ofrece series visibles para el motor, explica las no cotizables y guarda
el contacto tanto en cliente como en obra. Una respuesta perdida solo adopta
una coincidencia reciente, única y con todos los campos enviados. Cambio de
organización invalida respuestas antiguas; desconectarse conserva el editor.

El emisor se sella en la revisión nueva. Logo, color, atribución documental y
del portal siguen el snapshot; modificar Ajustes no reescribe una emisión.
El color requiere 4,5:1 contra paper y, si falla, cae a teal-800 con aviso.
Por defecto el documento oculta atribución y el portal la muestra discretamente.
El portal adopta también título e íconos del fabricante; al salir restaura
la identidad de la aplicación. El correo comercial siempre usa al fabricante.
Los snapshots históricos sin `brand_schema` mantienen su contrato anterior.

Cotización y comprobante requieren destinatario y documento revisados, más
confirmación humana. La outbox cifra el mensaje y adjunta PDFs verificados por
SHA-256; el job solo contiene su identificador. Aprobar o bloquear una OT genera
un aviso interno únicamente después de activar su destinatario en Ajustes.
Supabase Auth envía el enlace de acceso con su propia plantilla y transporte.

El worker confirma `DISPATCHING` en base de datos antes de contactar SMTP.
Dos workers compiten sobre la misma fila; los intentos son append-only. Un fallo
previo al contacto es `FAILED`; una respuesta perdida o worker interrumpido es
`UNCERTAIN` y no autoriza reenvío automático. La recuperación humana comprueba
ausencia y la generación de intento, conserva contenido y deja otro intento.
`SENT` significa aceptación SMTP: no acredita recepción ni lectura. Un worker
tardío no puede sobrescribir el estado de un intento ya recuperado.

El sandbox usa Mailpit local. El adaptador SMTP exige TLS y mantiene su clave
de cifrado fuera de la interfaz. Dominio, DNS y credenciales productivas son
activación posterior: véase [ACTIVACION](../../operations/ACTIVACION.md).
Las capturas verificadas resuelven imágenes CID desde los bytes MIME recibidos;
los enlaces de un uso y del portal se omiten en la evidencia publicada.
