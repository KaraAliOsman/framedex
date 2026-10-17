---
type: state
status: active
updated: 2026-10-17
volatility: high
verified_ref: dca9454bd7989f57a3f1b001bf1920b3f83a0a8d
sources:
  - https://github.com/KaraAliOsman/framedex/pull/159
  - docs/ux/2026-10-17/11-reconstruccion.md
  - https://github.com/KaraAliOsman/framedex/pull/157
  - docs/cola/ESTADO.md
  - docs/redesign/acceptance-2026-10-12.md
  - docs/operations/ACTIVACION.md
---

# Estado vigente de DEKOPEN v1

## Segunda reconstrucción de experiencia · 17-10-2026

El dueño autorizó implementar y luego rechazó la primera dirección. La rama
`codex/v1-experiencia`, [PR #159](https://github.com/KaraAliOsman/framedex/pull/159),
reconstruye la experiencia desde `0c3d2cbb`: tema luminoso blanco/tinta azul,
controles reconocibles, Hoy/Obras, biblioteca con materiales heredados,
lienzo/inspector, IA compartida entre página y panel, fotos privadas y PDF v2.
El [registro vigente](../../ux/2026-10-17/11-reconstruccion.md) distingue prompts
autoejecutados, código, investigación, pruebas, fallos corregidos y límites.
La [primera implementación](../../ux/2026-10-17/10-implementacion.md) queda como
historia; no acredita aceptación de esta segunda dirección.

La campaña de cierre registra 2.662 pruebas motor/backend y dos xfail esperados,
1.167 frontend en 106 archivos, corridas afectadas posteriores, 612 integración
y 1.483 pgTAP en 97 archivos. PostgreSQL 16 limpio y actualizaciones pobladas
pasan. El registro vigente conserva por separado las corridas de navegador.
No se suman repeticiones como pruebas únicas ni se atribuyen resultados
históricos a esta reconstrucción.

REVIEW se reconstruyó sin fixture/reset, conservando datos y sesiones. La
inspección incluye 1.440×900, 1.280×800, 1.024×768 y 390×844. Dos muestras
sintéticas recorrieron API/Storage privado y se restauraron con auditoría.
Un encargo real de IA sobre una sola ventana devolvió la venta indicativa del
motor, mantuvo el diseño guardado y no emitió/envió. No es un score nuevo del
harness IA ni una medición de aprendizaje en quince minutos.

Proline y Aluminios 2000 siguen sin adjuntarse; faltan corpus fabricante/OCR
regional y activos físicos aprobados. El PDF usa un renderer separado y conserva
versiones antiguas selladas. La IA modifica campos autorizados, sin código
arbitrario ni alteración de emitidos. Clientes, cobranza y analítica heredan la
base/navegación, sin reconstrucción completa de su composición específica. No
se declara aceptación definitiva ni superioridad universal sobre competidores.

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
