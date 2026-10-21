# P01 · Catálogo v2: origen de valores, niveles de uso y plantillas (backend + motor)

**Rama:** `gpt/dk2-p01-catalogo-v2` · **Depende de:** nada · **Siguiente:** P02

## Objetivo

Que una serie real pueda **cotizar con valores sugeridos visibles** y **fabricar
solo cuando estén confirmados**, sustituyendo la escalera de «autoridades» que
hoy deja a Proline PRO6004 como «Referencia · no cotizable». Esta fase entrega
el modelo de datos, la lógica y el API; la interfaz va en P02–P03.

Especificación: `docs/research/2026-10-21-competencia/03-catalogo-y-calculo.md`
(§2 origen, §3 niveles, §4 plantillas, §8 precio no entra aquí).

## Antes de empezar

1. Crea `docs/dekopen2/ESTADO.md` con la tabla de fases P01–P11 y su estado.
2. Ejecuta `make lint`, `make typecheck`, `make test` en `main` y anota en
   ESTADO.md cualquier fallo previo (la auditoría menciona dos casos dorados en
   rojo históricos: verifica si siguen; si están rojos, arréglalos primero en un
   commit separado explicando la causa, sin regenerar goldens a ciegas).
3. Lee: `backend/catalogs/readiness.py`, `backend/catalogs/authority.py`,
   `backend/engine_api/repository.py` (`SystemParamsRepository`),
   `engine/src/dekopen_engine/models.py`, `catalog_rules.py`,
   `catalog_authority.py`, y las migraciones de catálogo en `supabase/migrations/`.

## Qué construir

1. **Origen por valor.** Cada parámetro de regla de serie (descuentos por rol,
   soldadura, holguras, junquillo por espesor, refuerzos, reglas de herraje,
   traslapes, recargos de color) guarda `origin ∈ {MANUAL, WORKSHOP, SUGGESTED}`
   más `source_ref` (p. ej. «pág. 14» o archivo), `set_by`, `set_at`, y valor
   anterior en historial. «Falta» = sin fila. Reutiliza las tablas/registros de
   procedencia existentes si encajan; si no, crea una migración nueva
   (`NUMERIC` para cifras, `org_id` + RLS, pruebas pgTAP en `supabase/tests/`).
   Mapea los registros de autoridad actuales a estos orígenes (MANUAL cuando hay
   documento revisado; WORKSHOP cuando lo confirmó un usuario).
2. **Plantillas por familia** como **datos versionados** (no código): al menos
   «PVC practicable 60–70 mm», «PVC corredera 60–80 mm», «Aluminio practicable RPT»
   y «Aluminio corredera tradicional LatAm». Cada plantilla define valores típicos
   del oficio marcados SUGGESTED. Una serie nueva puede crearse desde plantilla.
   Pon los valores en un JSON bajo `backend/catalogs/templates/` o en seed SQL,
   con una prueba que valide su esquema. Valores con criterio de oficio y
   comentados (por ejemplo soldadura PVC 3,0 mm por extremo; refuerzo = barra − 30 mm;
   holgura de vidrio 5 mm por lado). Si dudas de un valor, déjalo marcado
   SUGGESTED con nota «revisar con fabricante»; nunca lo presentes como MANUAL.
3. **Niveles de uso** que reemplazan `catalog_readiness` en el contrato del API:
   `DRAWABLE`, `QUOTABLE`, `MANUFACTURABLE`, `MACHINE_READY` (ver §3). Calcula para
   cada serie: nivel actual, lista de pendientes `{campo, regla, origen, acción}`
   y conteo de sugeridos por confirmar. QUOTABLE se alcanza con valores SUGGESTED;
   MANUFACTURABLE exige cero SUGGESTED sin confirmar y serie verificada (la
   verificación llega en P03: deja el campo `verified_at` y la comprobación lista).
   Mantén `quote_ready` en la respuesta como alias de compatibilidad = QUOTABLE,
   y marca el campo antiguo como obsoleto en el OpenAPI.
4. **Motor:** el motor sigue recibiendo parámetros resueltos. Añade solo lo
   necesario para que el resultado lleve `assumptions: [{rule, value, origin}]`
   cuando algún parámetro usado sea SUGGESTED (para la nota interna «calculada
   con N valores sugeridos»). Sin cambiar ninguna fórmula: los casos dorados
   existentes deben seguir idénticos.
5. **Bloqueos por dependencia:** producción (`backend/production/`), hoja de
   corte y optimización consultan MANUFACTURABLE; precio y cotización consultan
   QUOTABLE. Un pendiente solo bloquea lo que depende de él.
6. **API:** endpoints para leer la ficha de serie completa por pestañas
   (perfiles, reglas, herrajes, vidrios/colores, tipologías, precios), editar
   celdas en lote (con historial), confirmar sugeridos en lote, crear serie desde
   plantilla y obtener el nivel con pendientes. Regenera `backend/openapi.yaml`
   y el cliente orval.

## Criterios de aceptación

- [ ] Prueba de integración: crear «Proline PRO6004» desde la plantilla PVC
      60–70 mm + perfiles mínimos → nivel QUOTABLE → el motor calcula precio y
      despiece de una ventana 1200 × 1100 abatible y devuelve `assumptions` no vacío.
- [ ] Confirmar todos los sugeridos + `verified_at` → MANUFACTURABLE; antes de eso,
      crear OT u hoja de corte devuelve un error claro con la lista de pendientes.
- [ ] Todas las tablas nuevas con `org_id` + RLS y prueba pgTAP de aislamiento.
- [ ] `make lint typecheck test` en verde; casos dorados sin cambios.
- [ ] OpenAPI y cliente regenerados; CI en verde.
- [ ] ESTADO.md y wiki (`docs/wiki/product/catalog-authority.md`) actualizados.

## Fuera de alcance

Interfaz (P02–P03), importación con IA (P03/P08), precio simple (P04).
