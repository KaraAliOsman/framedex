# P07 · Enviar cotización, portal del cliente y revisión antes de emitir

**Rama:** `gpt/dk2-p07-cotizacion` · **Depende de:** P06 · **Siguiente:** P08

## Objetivo

De «terminé de dibujar» a «el cliente la recibió» en menos de un minuto, con un
PDF bello, condiciones editables en línea y un portal donde el cliente acepta,
firma y paga el anticipo.

Especificación: `04-experiencia-y-diseno.md` §2 (F3), §3.5, §3.7; `05-agente-ia.md`
automatización 6. Mockups: `mockups/Enviar.dc.html`, `mockups/Portal.dc.html`.
Revisa `backend/documents/` (emisión, `quick_drafts.py`, renderers),
`backend/portal/`, `frontend/src/features/projects/QuotationDocument.tsx`,
`features/portal/PortalQuotePage.tsx`, `backend/billing/` (pagos).

## Qué construir

1. **Pantalla Enviar cotización:** PDF real a pantalla completa (renderizado por
   el backend, el mismo de la emisión) + columna derecha con condiciones
   editables (validez, anticipo, plazo, nota) que se reflejan al instante en la
   vista previa; panel de **revisión automática** (reglas: vidrio de seguridad
   donde la norma o la regla del taller lo exige, margen bajo el mínimo, hojas
   fuera de rango, condiciones faltantes, supuestos sin confirmar) con enlace a
   cada ventana; canal **WhatsApp | Correo | Enlace**; botón **Enviar a <cliente>**.
2. **Emitir y enviar en un solo clic humano:** al enviar se emite la revisión
   inmutable (registrando la aplicación del precio de P04), se genera el enlace
   del portal y se envía por el canal elegido (WhatsApp: abre `wa.me` con el
   texto y el enlace prellenados; correo: SMTP existente; enlace: copiar).
3. **PDF:** diseño limpio (logo, datos del taller, cliente, tabla con miniatura
   vectorial por ventana, totales neto/IVA/total, condiciones). Plantilla
   editable desde Empresa › Documentos (sin IA). La nota interna de supuestos
   nunca aparece en el PDF del cliente.
4. **Portal del cliente (móvil primero):** marca del taller, total grande,
   anticipo, ventanas con dibujo y 3D, condiciones, alternativas si las hay,
   **Aceptar y pagar anticipo** (firma con nombre y RUT, pago con el proveedor
   configurado o simulado en local), **Pedir un cambio** con comentario.
5. **Avisos:** la aceptación aparece en Hoy con **Pasar a taller**.

## Criterios de aceptación

- [ ] e2e: obra lista → Enviar → cambiar validez (se ve en el PDF) → enviar por
      enlace → abrir portal en 390 × 844 → aceptar con firma → pago simulado →
      Hoy muestra la aceptación.
- [ ] La revisión automática detecta un baño sin vidrio de seguridad en un caso de prueba.
- [ ] Una revisión emitida no cambia si después se editan precios o reglas.
- [ ] `mobile-native` aplicado al portal; capturas comparadas con los mockups.
- [ ] Todo verde (incluido Database Gate); wiki (`quotation-document.md`,
      `customer-proposals.md`) y ESTADO.md.
