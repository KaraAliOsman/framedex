---
type: state
status: active
updated: 2026-10-17
volatility: high
verified_ref: codex/v1-experiencia
sources:
  - https://github.com/KaraAliOsman/framedex/pull/157
  - docs/cola/ESTADO.md
  - docs/redesign/acceptance-2026-10-12.md
  - docs/operations/ACTIVACION.md
---

# Estado vigente de DEKOPEN v1

## Construcción de experiencia · 17-10-2026

El dueño autorizó construir con «ahora empieza». La rama `codex/v1-experiencia`
parte de `edcfd2844d2c2fc7cbb0d3b543b50e9089ab9b3f`; su
[registro de implementación](../../ux/2026-10-17/10-implementacion.md) detalla
tema claro único, obra/biblioteca, IA de cotización y presentación, PDF por
bloques, uniones/acabados, documentos/materiales y operación. REVIEW se
reconstruyó desde la rama conservando datos y sesiones, sin ejecutar fixtures.

Campaña al cierre: 1.064 pruebas del motor, 1.583 backend, 1.147 frontend en la
corrida completa, 605 integración y 1.483 comprobaciones pgTAP pasan; el registro
separa verificaciones afectadas posteriores. PostgreSQL 16 pasa y los 19 escenarios
de navegador tienen resultado verde en su última ejecución: 16 en la corrida
general y tres en repeticiones afectadas; no es una nueva corrida completa. No es
una aceptación definitiva ni un score nuevo del harness IA. Quedan límites
explícitos de corpus fabricante/OCR regional, activos físicos, renderer PDF
separado y superficies del negocio que solo heredan base/navegación.

## Integración histórica · 12-10-2026

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
