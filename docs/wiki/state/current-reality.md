---
type: state
status: active
updated: 2026-10-17
volatility: high
verified_ref: edcfd2844d2c2fc7cbb0d3b543b50e9089ab9b3f
sources:
  - https://github.com/KaraAliOsman/framedex/pull/157
  - docs/cola/ESTADO.md
  - docs/redesign/acceptance-2026-10-12.md
  - docs/operations/ACTIVACION.md
---

# Estado vigente de DEKOPEN v1

## Reversión del rediseño · 17-10-2026

El dueño rechazó ambas iteraciones de `codex/v1-experiencia` y ordenó revertir
los cambios. El código del producto vuelve a
`edcfd2844d2c2fc7cbb0d3b543b50e9089ab9b3f`, anterior a este trabajo. Se conservan
la limpieza previa y el cambio local ajeno de `golden_analytics.json`. La
dirección y los prompts del rediseño quedan retirados; no constituyen una nueva
instrucción ni aceptación del dueño. La evidencia histórica se conserva en
[Git](https://github.com/KaraAliOsman/framedex/tree/d97245987276784c9195662657cd807109c89fa1/docs/ux/2026-10-17).

REVIEW sirve las imágenes reconstruidas del código restaurado, sin fixture/reset
ni borrado de datos o sesiones. Las migraciones aditivas ya aplicadas a la base
local conservan sus datos e historial; el código anterior no usa sus capacidades.
Los resultados descritos más abajo pertenecen a la integración histórica de v1.

## Integración histórica

`main` contiene el programa completo mediante
[PR #157](https://github.com/KaraAliOsman/framedex/pull/157), squash
`2db4e13171884b93a989e68508a55f5590f9b34d`, mergeado el 12-10-2026 por instrucción del dueño.
GitHub registra SUCCESS para Lint & Typecheck, Test Suite, Frontend Build y
Database Gate en sus dos corridas. La [cola](../../cola/ESTADO.md) registra
39 encargos mergeados y ninguno bloqueado.

La consulta de refs, PR y archivos durante la limpieza confirma la integración.
Las verificaciones funcionales siguientes son resultados históricos de P20;
no se repitieron pruebas ni una auditoría del producto en esta limpieza.

## Alcance aceptado y límites

La [aceptación final](../../redesign/acceptance-2026-10-12.md) conserva los
catorce recorridos, la rúbrica editorial, los refs y los límites de cada medición.
La matriz UX tiene 912 vistas; dominio, 175 posiciones positivas y 35 rechazos
por junquillo ausente. La suite MiMo real conserva 21/26 casos PASA, E/J 18/21
y cinco fallos. Estas cifras describen la muestra ejercitada por P20.

Los datos DEMO y los adaptadores sandbox no acreditan fabricación industrial,
certificación térmica, dinero real ni documentos tributarios productivos.
SII 39, tarifas de compra autorizadas, fuentes de fabricante, tarifas/presupuesto
de IA, correo externo y calibración CNC conservan sus límites explícitos.
La carga fría de WebGL se informa por separado de la interacción caliente.

Para uso del dueño: [guía](../../GUIA-REVISION.md) y
[conexiones de activación](../../operations/ACTIVACION.md).
Para riesgos: [known-risks](../quality/known-risks.md).

## Dónde continuar por dominio

El [índice de la wiki](../index.md) enlaza las páginas de producto: catálogo,
vidrio, aperturas, herrajes, colores, extras, vano, dibujo/3D, proyecto, precios,
emisión/portal, IA, producción, compras, CNC, terreno, empresa y analítica.
Estas páginas conservan decisiones, fuentes, reglas y verificación por encargo.
Los informes de aceptación por ID permanecen en `docs/redesign/` y las
aceptaciones D01–D07/IA1–IA3 en sus carpetas originales.

Antes de afirmar comportamiento actual, compruebe el ref objetivo, el código,
las migraciones y los PR posteriores. Para números manda el motor y el catálogo
con autoridad; para esquema/tenant mandan migraciones y RLS. La wiki conserva
conocimiento, según [SCHEMA](../SCHEMA.md), sin reemplazar esas fuentes.

## Entorno local y mantenimiento

La estación Windows del dueño tiene REVIEW en `127.0.0.1:5179`, correo local en
`127.0.0.1:25364`, perfiles Brave independientes y MiMo configurado. La limpieza
conserva sus archivos privados y servicios, sin renovar sesiones ni llamar a IA.
El detalle y la lista de protección están en
[WORKSPACE](../../operations/WORKSPACE.md); no presuma que `.run/` es descartable.

El [mapa de evidencia](../../redesign/captures/README.md) distingue aceptación
conservada y capturas históricas retiradas. Los mapas extensos de fases anteriores
se reemplazaron por esta síntesis para evitar repetir estados ya superados.
El [estado anterior completo](https://github.com/KaraAliOsman/framedex/blob/2db4e13171884b93a989e68508a55f5590f9b34d/docs/wiki/state/current-reality.md)
permanece en Git: conserva historia y fuentes, sin presentarlas como estado actual.
El [log](../log.md) sigue siendo append-only.
