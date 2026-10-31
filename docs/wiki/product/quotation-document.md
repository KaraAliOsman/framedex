---
type: concept
status: active
updated: 2026-10-18
volatility: medium
verified_ref: 97aea5dfec6e4dddcb429a48b421c7598e758a0d
sources:
  - backend/documents/quotation.py
  - engine/src/dekopen_engine/quotation.py
  - backend/tests/integration/test_quote_document_v2.py
---

# Propuesta comercial sellada

## Árbol de trabajo v1 · 18-10-2026 (sin commit)

Esto es un hecho del árbol de trabajo en la rama `claude/v1-implementacion`. No está en
`main` ni se verificó en navegador.

- `documents/numbering.py` asigna «N.º n» por empresa:
  - el prefijo y el siguiente número son editables;
  - el siguiente número no puede quedar por debajo del más alto ya asignado;
  - el número se asigna una vez, en la primera vista previa emitible, dentro de la
    transacción de preparación.
- El snapshot sella `commercial_label` y `document_layout`. Las revisiones anteriores
  conservan el folio `COT-<código>-<rev>`.
- `documents/quotation.py` resuelve el diseño en este orden: empresa (preferencias) → obra
  (borrador) → solicitud.
  - Los bloques posiciones y resumen comercial no se pueden ocultar.
  - Un preview borrador (`quotation-draft`) lleva «Borrador», no consume número y no se
    guarda.
- `document_artifacts.layout` separa cada composición en su propio artefacto inmutable:
  ESENCIAL, PROYECTO, ALTERNATIVAS, COMPACTA, VENTANA y OBRA.

## Intención de producto posterior · 17-10-2026

El dueño pide firma/aceptación opcionales, numeración comercial sencilla y edición
manual/IA de plantillas y borradores. El plan documental
concreta tres cotizaciones, dos pedidos y tres cortes. Propone originales
estructurados versionados; no está implementado. En el ref restaurado
`6f78e329`, `quotation.py:387` añade aceptación incondicional y el folio usa
proyecto/revisión. La consulta de numeración actual no acredita configuración de
folio comercial. Emitidos siguen inmutables: cambios posteriores crean revisión
o documento relacionado, no reescriben el original. La evidencia P09 siguiente
conserva su alcance histórico.

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

Véase aceptación: fixtures de 1/12/24/100,
tablas sin intersecciones, 40 páginas normales y 45 con nombres largos,
calendario/alternativas/QR e inmutabilidad por recorrido real. Es evidencia
DEMO de comportamiento, sin certificación manufacturera. Los artefactos
históricos no se regeneran para adoptar un layout nuevo.

El gate completo verifica 1.186 pgTAP, 425 integraciones y 17 E2E reales,
incluido el acceso documental de ESTIMATOR por Ajustes. Los upgrades poblados
conservan precios, hashes, emisor y snapshots. La matriz refrescada verifica
44 vistas y los recorridos oficiales 24, sin hallazgos ni desbordes.
