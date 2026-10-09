---
type: concept
status: active
updated: 2026-10-08
volatility: medium
verified_ref: 230a6c93016bc4126febc85dc8c0bc9290e84cca
sources:
  - docs/redesign/P09-ACEPTACION.md
  - backend/documents/quotation.py
  - engine/src/dekopen_engine/quotation.py
  - backend/tests/integration/test_quote_document_v2.py
---

# Propuesta comercial sellada

La intención de P09 es un documento white-label que el fabricante pueda firmar:
emisor, cliente, solución, dibujos acotados, condiciones y aceptación. La
implementación verificada compone fichas por campo con densidad según cantidad,
Plex embebida y pie con folio/revisión/página/huella. Las preferencias se sellan
al emitir; una configuración posterior no cambia papel, acento ni textos.

El motor proyecta precios sellados: unitario y ajuste explicable, descuento
con autoridad y reparto exacto de hitos. No repricia la revisión. Los datos
históricos no estructurados no se convierten en condiciones numéricas. Vidrio
y Ug necesitan autoridad; una ausencia se omite del documento comercial.

Las alternativas son hasta tres revisiones anteriores del mismo proyecto y
tenant. Se copia su solución sellada sin alternativas recursivas, fuera del
total vigente. La validación usa el rol documental incluso al guardar desde
el contexto comercial; un caso PostgreSQL cubre este límite de permisos.

Cada slot PDF nuevo conserva un QR propio de la revisión. La capacidad se
cifra y su hash pertenece a una aprobación del portal. Compartir reemplaza
solo enlaces compartidos. Revocar el QR bloquea su portal y conserva el PDF.
Un fallo de render/upload revierte la aprobación y el registro de capacidad.

Véase [aceptación](../../redesign/P09-ACEPTACION.md): fixtures de 1/12/24/100,
tablas sin intersecciones, 40 páginas normales y 45 con nombres largos,
calendario/alternativas/QR e inmutabilidad por recorrido real. Es evidencia
DEMO de comportamiento, sin certificación manufacturera. Los artefactos
históricos no se regeneran para adoptar un layout nuevo.

El gate completo verifica 1.186 pgTAP, 425 integraciones y 17 E2E reales,
incluido el acceso documental de ESTIMATOR por Ajustes. Los upgrades poblados
conservan precios, hashes, emisor y snapshots. La matriz refrescada verifica
44 vistas y los recorridos oficiales 24, sin hallazgos ni desbordes.
