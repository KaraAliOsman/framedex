---
type: concept
status: active
updated: 2026-10-06
volatility: medium
verified_ref: codex/D06-accesorios-extras
sources:
  - engine/src/dekopen_engine/extra_models.py
  - engine/src/dekopen_engine/extras.py
  - engine/tests/golden_extras.json
  - backend/projects/extras.py
  - supabase/migrations/20270103000000_accessory_services.sql
  - supabase/migrations/20270103000100_demo_extra_catalog.sql
  - docs/redesign/captures/accesorios-extras/aceptacion.md
---

# Accesorios, servicios y precio sellado

## Hechos verificados del repositorio

El catálogo declara definición, regla de cantidad, unidad, costo, venta, fuente,
compatibilidad y carácter sintético. El motor deriva largos por vuelos/lados,
cantidades por vano/hoja y servicios por área/perímetro/cantidad/zona. Los perfiles
extra tienen BOM, corte, refuerzo/tornillos cuando su autoridad los exige y traza
EXTRA. La manilla especial sustituye la manilla base. El palillaje utiliza la
cantidad y cargos de la receta D02, sin regla de largo inventada ni segundo BOM.

Los servicios pertenecen a la revisión y las plantillas se aplican a posiciones
nuevas. Clonar o crear sucesora conserva las selecciones; lo emitido conserva
autoridades, política documental y cantidades selladas. La instalación explícita
suprime el cargo histórico equivalente; reglas simultáneas de instalación se
rechazan. Cada costo completo de accesorio se cobra una vez, aunque su BOM
también sea necesario para fabricar y comprar.

El reparto por mayor remanente mantiene base + sublíneas = neto aplicado en el
quantum de moneda. La tarifa mostrada tiene un ajuste explícito cuando cantidad
por tarifa difiere del importe repartido. El margen objetivo considera posiciones
y servicios juntos. Cambio de policy durante precio/apply se rechaza mediante
lock de organización y comprobación de autoridad.

El dueño con MFA configura servicios, plantillas y política en Ajustes, con
revisión optimista e historial inmutable. Los estimadores reciben definiciones
y precios públicos; costo no viaja en las previsualizaciones de extras. Tablas y
políticas mantienen org_id y RLS. El catálogo DEMO v6 es adicional: el transporte
histórico omite los campos nuevos cuando estaban ausentes.

Las sugerencias de un ensamblaje conservan el módulo de origen y la selección
local a su árbol. El API entrega compatibilidad por módulo o acepta un módulo
explícito; una hoja móvil de otro módulo no habilita un accesorio incompatible.
`WINDOW` significa un marco completo, incluidas sus divisiones internas;
`LEAF` deriva cada hoja compatible. Un ensamblaje evalúa cada marco por módulo.

Los endpoints de precio (preview, aplicar, retirar e historial) filtran costos
por el rol resuelto del tenant. El estimador recibe venta y la causa de la
restricción, sin costos de servicios, agregados, composición, reglas de compra
ni autoridades privadas anidadas. La previsualización de cambios en lote también
omite costos para el estimador y muestra esa causa; no convierte su ausencia en
un delta cero. El dueño conserva lectura exacta. Ninguna proyección modifica el
snapshot sellado, el cálculo del motor ni las reglas RLS de compra.

La columna `profile_systems.extra_authority` queda reservada al backend. Una
función con propietario sin bypass de RLS proyecta definiciones y zonas sin
tarifas de costo para miembros; solo el gestor autorizado de la organización
solicitada recibe la autoridad completa. La API del catálogo conserva ese
contexto por organización. El motor lee la autoridad bajo un rol de backend
que mantiene las mismas claims y RLS; la ficha pública explica la restricción.

## Intención del dueño y producto

El estimador debe cobrar lo que de verdad se instala. Sugerir vierteaguas o
ensanches incluye su causa y admite aceptación, descarte y deshacer. DOC-01
mantiene extras bajo su posición, con precio o agrupados según la organización;
los servicios aparecen en el resumen comercial. P07/P09 continúan sus rediseños.

## Límites y contexto histórico

Las fichas y tarifas sintéticas no certifican producción. Contornos y vidrio sin
marco con extras sin autoridad quedan incompletos de forma explícita. Los
hallazgos heredados del editor/cromo permanecen en sus encargos de rediseño.
El [incidente del gate previo](../../operations/INCIDENTE-GATE-2026-10-06.md)
afectó una base local ajena; su evidencia se excluye de aceptación y no acredita
conservación de sus datos. D06 usa exclusivamente stacks propios y aislados.

## Investigación externa

El Musterangebot adjunto inspira la agrupación documental de sublíneas. No
aporta tarifas de producción, dimensiones de fabricación ni autoridad numérica
para este catálogo. Véase la [aceptación](../../redesign/captures/accesorios-extras/aceptacion.md)
para pruebas, capturas y reglas registradas.
