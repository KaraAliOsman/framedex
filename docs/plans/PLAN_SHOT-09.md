# PLAN_SHOT-09 — Autoridad documental, manufactura, compras y documentos

## Estado y proveniencia

- **Shot:** SHOT-09.
- **Cierre:** `CLOSED / PROVEN` — merge [PR #23](https://github.com/KaraAliOsman/framedex/pull/23) en `main @ 251f4417a85b9e37ffad905d84147d76f21b68f6` desde head aprobado `10615b534fcbdfb99f358a3629231c903f950ab7`; Gauntlet exit 0, Golden byte-idéntico, CI `main` run `34914566757` verde (4/4 jobs).
- **Base autoritativa real:** `main @ 7c0c18695aa29b488338811e3640474fd920647d`.
- **Rama de trabajo:** `codex/shot-09`.
- **Autoridad:** `CONSTITUTION > docs/PRD/PLAN_SHOTS.md > docs/PRD/PRD-06.md > decisiones Owner congeladas para SHOT-09 > este plan > implementación`.
- **Contrato temporal:** SHOT-09 sella exclusivamente la revisión documental inicial `REV-A`. REV-B, clonación y flujo general de revisiones pertenecen a SHOT-10.
- **Regla 0:** cero contradicciones materiales conocidas después de aplicar las enmiendas Owner de este shot.
- **Regla 20:** cero vacíos materiales. Los valores técnicos no especificados no se inventan: viven en autoridades tipadas explícitas y su ausencia o ambigüedad falla cerrado.
- **Golden inicial de solo lectura:** `calculation_hash = sha256:562cdc97337a690f09db12590ee8a99b420ebc6b7dbf9c40a4d4755132d24f21`; SHA-256 del archivo `engine/tests/golden_example.json = c21c88d66e7ee2e0049ff01f4007cdd168383595d5b2f0f001fccf743ac5bff6`.

El Owner ordenó `PLAN FIRST — THEN IMPLEMENT`; por ello este archivo registra el contrato antes de editar código ejecutable, pero no constituye una condición de espera.

## Resolución explícita de aparentes conflictos

1. `PLAN_SHOTS` y la enmienda Owner gobiernan sobre la ficha de pantalla: la identidad canónica de **S19** en SHOT-09 es **Supplier Purchasing / Purchase Requirements and Orders**. La capacidad de corte ya existente continúa bajo taller/corte y se enlaza desde S19; no se crea un segundo S19.
2. `SUPPLIER_PANEL_PO` se añade de forma aditiva al enum existente. Accesorios no crean un quinto tipo: cada línea declarada debe indicar explícitamente uno de `PROFILE`, `GLASS`, `HARDWARE` o `PANEL`; una asignación ausente o una obligación duplicada falla cerrado.
3. Ningún valor de colocación, manilla o ángulo de acero se presume. `ManufacturingPlacementPolicyV1`, `HandleRequirementPolicyV1` y la autoridad de corte de refuerzo V1 contienen valores explícitos/versionados. SHOT-09 sólo incluye autoridades sintéticas declaradas para `DEMO_60`; producción sin autoridad compatible falla cerrado.
4. La preimagen semántica de `bom_hash` tiene exactamente cuatro componentes superiores: `project_id`, `revision`, `positions`, `bom`. No existe quinto componente.
5. El Inspector se ejecuta en servidor en modo `DESIGN` durante el freeze. `GREEN` o `YELLOW` con `production_allowed=true` permiten sellar; `RED` bloquea. DOC-03 y DOC-05 exigen además completitud documental/manufacturera congelada.
6. El alcance técnico heredado sigue siendo el de SHOT-06/07. SHOT-09 documenta sólo geometría ya soportada; no amplía colores/geometrías no autorizados.

## Convenciones deterministas congeladas

### Canonicalización documental V1

`dekopen_engine.documentary_canonical` es una implementación pura separada de `dekopen_engine.snapshot.canonical_json`.

- Identificador de versión: `DOCUMENTARY_CANONICAL_V1`.
- Objetos: claves `str`, orden Unicode ascendente.
- JSON UTF-8, `ensure_ascii=false`, sin espacios, separadores `,` y `:`.
- Valores admitidos: `null`, booleano, entero seguro, texto, `Decimal` finito convertido a texto decimal fijo, UUID/fecha/fecha-hora/Enum convertidos a texto, listas/tuplas, mappings y modelos Pydantic.
- `float`, NaN/Infinity, claves no textuales y tipos no declarados se rechazan.
- `bom_hash`, `snapshot_sha256`, `purchase_projection_hash`, `order_snapshot_hash` y `file_sha256` son hex SHA-256 minúsculo de 64 caracteres, sin prefijo.
- `bom_hash_v1` canoniza exactamente:

```json
{
  "project_id": "…",
  "revision": "REV-A",
  "positions": ["…"],
  "bom": ["…"]
}
```

- `snapshot_sha256_v1` se calcula sobre el snapshot completo que contiene `bom_hash` pero no contiene su propio `snapshot_sha256`.
- `file_sha256` se calcula únicamente sobre bytes concretos del artefacto.
- Los hashes de cálculo existentes y bytes Golden no cambian.

### Coordenadas de manufactura V1

- Vista desde el interior del edificio hacia el exterior.
- Elevación cerrada.
- Origen en la esquina superior izquierda nominal del marco exterior.
- X hacia la derecha, Y hacia abajo.
- Milímetros `Decimal` exactos.
- La identidad física incluye posición, repetición, ruta topológica, ensamble, slot de hoja, rol y slot físico; jamás longitud, SKU, orden de array o cantidad agregada.

## Decisiones aprobadas PD-09-01…PD-09-19

| PD | Decisión Owner congelada | Implementación | Prueba focalizada |
|---|---|---|---|
| **PD-09-01** | `project_versions` es la única autoridad documental inmutable. SHOT-09 crea sólo `REV-A`; evidencia no actualizable, borrable ni cascade-deletable. | Migraciones `20260914000000_shot_09_documentary.sql`, `20260914000100_shot_09_demo_authorities.sql`; `backend/documents/service.py`, `repository.py`. FKs restrictivas, trigger append-only y rol backend NOLOGIN. | pgTAP update/delete/cascade; integración de freeze concurrente e idempotente. |
| **PD-09-02** | Canonicalización documental V1 pura y separada; `bom_hash`, `snapshot_sha256` y `file_sha256` son identidades distintas; preimagen BOM exacta de cuatro componentes. | `engine/src/dekopen_engine/documentary_canonical.py`, exports en `__init__.py`. | `engine/tests/test_documentary_canonical.py`: vectores byte exactos, permutaciones, rechazo float y separación de hashes. |
| **PD-09-03** | Freeze requiere una operación de pricing explícita, exactamente `APPLIED`, mismo proyecto/org y todavía idéntica al estado aplicado. No “latest”, heurística de totales ni recálculo de fórmulas SHOT-08. | FK restrictiva `project_versions.pricing_operation_id`; validación/bloqueo en `documents/service.py`; reutiliza snapshot/result de `pricing_operations`. | Integración: PREVIEW/PENDING/REJECTED/cross-tenant/stale rechazados; operación exacta preservada. |
| **PD-09-04** | `document_artifacts` registra archivos concretos inmutables por slot tipado `PROJECT_REVISION` u `ORDER`; slot ocupado retorna el existente. Bucket/key y `file_sha256` son inmutables; URL firmada no es identidad. | Tabla/constraints compuestas; `backend/documents/artifacts.py`, `storage.py`, serializers/views. | pgTAP de cross-binding; backend idempotencia y carrera; firma exactamente 3600 s y tenant ajeno denegado. |
| **PD-09-05** | Cada campo material tiene una autoridad tipada. Se congelan términos de pago, validez, cliente/contacto/entrega existentes, `location_tag`, anotaciones, estructura, pulido por vidrio y procedencia SKU. La composición es la especificación exacta por vano del árbol. | `project_documentary_inputs`, `position_documentary_inputs`; `backend/documents/serializers.py`, `repository.py`; snapshot V1. | Tests de input estricto, composición desde árbol, falta de location/pulido/procedencia y mutación post-freeze. |
| **PD-09-06** | `ManufacturingFactsV1` es derivado puro separado y consume una traza emitida mientras geometría conoce identidad física; no reconstruye desde `EngineResult` ni altera contratos/Golden/BFD. | `engine/src/dekopen_engine/manufacturing_trace.py`, `manufacturing.py`; extensión interna de `technical_facts.py` y `geometry.py` sin tocar `EngineResult`, `ProfileCut` ni `ReinforcementPiece`. | `engine/tests/test_manufacturing.py`: identidad estable, repetición, relaciones, coordenadas y hash/Golden heredado. |
| **PD-09-07** | Colocación corredera/vidrio corredera/junquillos consume `ManufacturingPlacementPolicyV1`; usuarios no entregan X/Y; ausencia/ambigüedad falla cerrado y políticas no cambian cortes/deducciones. | Tabla `manufacturing_placement_policies`; modelos/proyector en `manufacturing.py`; loader explícito en `documents/repository.py`. | Casos de política ausente/ambigua y prueba de igualdad de longitudes antes/después. |
| **PD-09-08** | `HandleIntentV1 + HandleRequirementPolicyV1 -> HandleLocationFactV1`. Intent humano sólo usa posición/vano/hoja/slot/altura/referencia vertical. Política resuelve host, X, offset, región. `handle_height_mm` legado exige confirmación/migración explícita. | Tabla `handle_requirement_policies`; intent tipado en inputs; proyector V1. | Rechazo de X/host/member ID humano, slot requerido ausente, región inválida y legado no confirmado. |
| **PD-09-09** | Cada refuerzo se enlaza en emisión a un único miembro padre. Ángulos requieren autoridad V1 explícita; no existe 90/90 ni fallback de perfil. Longitud existente sigue mandando salvo compatibilidad explícita. | Tabla `reinforcement_cut_policies`; enlace semántico y reglas en `manufacturing.py`. | Parent único, igualdad de longitudes, regla incompatible/ausente y cero fallback. |
| **PD-09-10** | Freeze genera evidencia Inspector `DESIGN` inmutable; no acepta GREEN almacenado. RED bloquea. DOC-03/05 agregan completitud. DOC-06 es checklist vacío con expectativa/tolerancia, nunca resultado fabricado. | Ejecución `compute_geometry(..., diagnostic=True)` + `inspect`; evidencia en snapshot; guardas de renderer. | Stored GREEN falso no sirve; RED bloquea; YELLOW permitido; DOC-06 no contiene medición/estado/operador/fecha completada. |
| **PD-09-11** | DOC-07 es OWNER-only y usa costos capturados en pricing APPLIED. `realized_waste={status:NOT_RECORDED,value:null}`; jamás BFD, allowance comercial o cero. | `backend/documents/renderers.py`, autorización en views, snapshot de costos exactos. | OWNER obtiene; otros roles 403 y sin bytes/costos; texto “no registrado”; valor null. |
| **PD-09-12** | XLSX es representación, no autoridad: texto decimal exacto para dimensión/área/dinero/tasa, enteros seguros cuando corresponda y texto para IDs/SKU/spec. No `float()`; workbook se verifica contra entrada congelada. | `backend/documents/xlsx.py`, normalización ZIP/metadatos determinista. | Reload openpyxl: tipos/valores exactos; bytes estables; DOC-02/04 reconcilian con snapshot. |
| **PD-09-13** | `PurchaseRequirementsV1` puro/inmutable expande `project_positions.quantity` exactamente una vez. Perfil/acero: piezas expandidas → grupos compatibles → BFD existente sin modificar → barras. | `engine/src/dekopen_engine/purchasing.py`; `purchase_projections` y `purchase_requirement_lines`; servicio de freeze. | Conservación por fuente, cantidad 1/2/N, permutación, cero pérdida/duplicado. |
| **PD-09-14** | `PhysicalStockBindingV1` prueba intercambiabilidad real. Identidad física, SKU taller y SKU compra son distintos; no pooling por texto/proveedor/longitud/SKU similar y nunca profile↔steel. | Columnas de binding explícito sobre autoridades existentes, modelo V1 y wrapper por grupo que invoca `optimize_cut` sin cambiarlo. | Pool permitido por identidad exacta; material/color/variante/perfil de corte/stock distintos y profile↔steel separados. |
| **PD-09-15** | Vidrio terminado se compra `EA` con composición/orientación/pulido/location/traza exactos; hardware `KIT_ONLY`; panel sólo `CUT_TO_SIZE/EA` explícito; accesorios requieren cobertura `DECLARED` o `NONE_REQUIRED` y no duplican obligaciones. | Tablas `glass_purchase_mappings`, `hardware_purchase_mappings`, `panel_purchase_authorities`; `AccessoryScheduleV1`; proyección V1. | Key de vidrio exacta y no rota; contenido kit no explota; panel/accesorio ausente falla; duplicado rechazado. |
| **PD-09-16** | Elegibilidad de proveedor es autoridad operacional posterior al freeze e independiente de WHAT. Selección explícita, línea completa a un proveedor, sin first/latest/cheapest/pricing-source. Evidencia exacta se congela al ordenar. | `supplier_eligibility_versions`; `backend/purchasing/service.py`, API S19. | Crear después de REV-A; cambiar selección no cambia requisito/hash/BFD; autoridad no elegida/ambigua rechazada. |
| **PD-09-17** | `orders` existente se endurece: un proveedor + versión + tipo. Un batch confirmado máximo por versión/tipo; exige todas las líneas de ese tipo, tipos diferentes independientes, cada requisito una vez. DRAFT→SENT sólo por clic explícito; generar/descargar no envía. | `purchase_allocations`, `order_allocation_batches`, `order_requirement_lines`; columnas snapshot/hash/FKs en `orders`; confirm/send transaccional. | Doble batch/línea y carreras convergen; GLASS y PROFILE confirman por separado; artifact no cambia status; send explícito sí. |
| **PD-09-18** | Scopes: DOC-01 rev PDF; DOC-02 order XLSX GLASS; DOC-03 rev PDF; DOC-04 order PDF+XLSX PROFILE; DOC-05 rev PDF de todos los grupos; DOC-06 rev PDF vacío; DOC-07 rev PDF OWNER. Render histórico sólo frozen. | `backend/documents/renderers.py`, `xlsx.py`, templates/styles y artifact service. Dependencia baseline `weasyprint` pinneada; fetch externo prohibido. | Catálogo mutado después no altera output; DOC-02/04/05 reconciliación; formatos/scope inválidos fallan. |
| **PD-09-19** | S19 es Supplier Purchasing / Purchase Requirements and Orders. Muestra requisitos, identidades, trace, bloqueos, elegibilidad, asignación, preview por tipo, órdenes, documentos y link de taller. `WORKSHOP_MANAGER` conserva propiedad operacional; no OWNER-only; cantidad/BFD read-only y confirmación deliberada. | `frontend/src/features/purchasing/*`, ruta/nav/i18n, OpenAPI/orval; backend purchasing endpoints. | Vitest de rol/tabla/asignación/confirmación/inmutabilidad; E2E manager y cross-tenant. |

## Esquema aditivo y bindings

La migración SHOT-09 no modifica archivos históricos. Añade:

- autoridades técnicas V1: `manufacturing_placement_policies`, `handle_requirement_policies`, `reinforcement_cut_policies`;
- mappings de compra: `glass_purchase_mappings`, `hardware_purchase_mappings`, `panel_purchase_authorities`;
- inputs editables pre-freeze: `project_documentary_inputs`, `position_documentary_inputs`;
- evidencia inmutable: `purchase_projections`, `purchase_requirement_lines`, `document_artifacts`;
- operación de compra: `supplier_eligibility_versions`, `purchase_allocations`, `order_allocation_batches`, `order_requirement_lines`;
- `SUPPLIER_PANEL_PO` y columnas/FKs/hashes de revisión y order snapshot sobre tablas existentes.

Todas las tablas de negocio tienen `org_id`, RLS y pruebas de aislamiento. `project_versions` expone directamente sólo columnas no confidenciales; `snapshot_json` completo queda detrás del backend para impedir fuga de costos. FKs de evidencia usan `RESTRICT`; triggers impiden UPDATE/DELETE ordinario. `documentary_backend` es `NOLOGIN`, `NOBYPASSRLS`, conserva claims verificados y recibe sólo privilegios necesarios.

Las relaciones compuestas prueban `org/project/version/bom/snapshot` tanto para proyecciones como para artefactos y órdenes. PostgreSQL valida formato, pertenencia, unicidad, estado y binding; no contiene un canonicalizador JSON paralelo.

## Orden de dependencias y slices verticales

1. **Canonicalización + DDL de evidencia.** Vectores puros, formato hash, FKs restrictivas, RLS, inmutabilidad y demo authorities explícitas.
2. **Freeze APPLIED → REV-A.** Inputs tipados, validación exacta de estado comercial, lock por proyecto, snapshot y carrera idempotente.
3. **Artifact registry + storage.** Slot locking, bytes/hash, upload inmutable y acceso firmado 3600 s.
4. **Traza semántica + ManufacturingFactsV1.** Emisión física sin cambiar BOM público ni Golden.
5. **Placement/handle/steel + Inspector.** Políticas explícitas, evidencia DESIGN y completitud.
6. **PurchaseRequirementsV1.** Expansión exacta, PhysicalStockBinding, wrapper BFD y reconciliación.
7. **Vidrio/kit/panel/accesorios.** Keys completas y fail-closed de mappings/coverage.
8. **Elegibilidad/asignación/orders.** Batch por tipo, snapshots inmutables y DRAFT→SENT humano.
9. **DOC-01…DOC-07.** Productores sólo frozen, XLSX exacto, PDF sin fetch externo y guardas por scope/rol.
10. **S19.** Flujo real de manager, blockers, asignación explícita, preview/confirmación y artefactos.
11. **Integración/adversarial.** Ataques de autoridad, tenancy, nondeterminismo, duplicación, fuga y carreras.
12. **Un Gauntlet final.** Sólo se repite si una corrección posterior afecta materialmente su cobertura.

## Verificación focalizada por slice

Los comandos se ejecutan desde raíz salvo indicación:

1. Canonical/DDL:
   - `py -3.12 -m pytest engine/tests/test_documentary_canonical.py -q`
   - `supabase test db supabase/tests/database/070_shot_09_documentary.test.sql`
2. Freeze/artifacts:
   - `py -3.12 -m pytest backend/tests/test_documents_contract.py backend/tests/integration/test_shot09_documents.py -q`
3. Manufacturing/policies:
   - `py -3.12 -m pytest engine/tests/test_manufacturing.py engine/tests/test_snapshot.py engine/tests/test_cutting.py -q`
4. Purchasing/BFD/categories:
   - `py -3.12 -m pytest engine/tests/test_purchasing.py -q`
5. Supplier/orders/documents/storage:
   - `py -3.12 -m pytest backend/tests/test_purchasing_contract.py backend/tests/integration/test_shot09_purchasing.py -q`
6. Frontend S19:
   - `npm test -- PurchasingPage` (cwd `frontend`)
   - `npm run lint` (cwd `frontend`)
   - `npm run build` (cwd `frontend`)
7. Reproducibilidad contractual:
   - `py -3.12 backend/manage.py spectacular --file backend/openapi.yaml --validate`
   - `npm run api:generate` (cwd `frontend`) y `git diff --exit-code -- backend/openapi.yaml frontend/src/api/generated`
   - `py -3.12 engine/scripts/regenerate_golden.py --check`

Cada slice se ataca además contra: autoridad incorrecta, tenant leak, lookup live/stale, orden de entrada, cantidad perdida/duplicada, money leak, race e idempotencia. Hallazgos materiales se corrigen antes de avanzar.

## Productores y reglas de representación

- Todo renderer recibe un `FrozenRevisionV1` o `FrozenOrderV1`; su interfaz no admite repositorios de catálogo.
- DOC-01 presenta jerarquía comercial para cliente y excluye costo/margen.
- DOC-03 y DOC-05 priorizan IDs físicos, cotas, referencias y legibilidad de taller a tamaño de impresión.
- DOC-06 contiene casillas sin completar y autoridad de expectativas/tolerancias, no observaciones ficticias.
- DOC-07 usa únicamente componentes de costo capturados; merma realizada se imprime como **No registrada**.
- DOC-02/04 usan texto decimal exacto y una hoja de trazabilidad completa.
- El fetcher de WeasyPrint rechaza toda URL externa; sólo HTML/CSS generado localmente y datos escapados.
- XLSX fija propiedades/ZIP para bytes repetibles y se reabre para verificar valores antes de registrar el archivo.

## DoD exacto SHOT-09

SHOT-09 es candidato a revisión Owner únicamente si:

1. Este plan contiene PD-09-01…PD-09-19, enmiendas Owner, mapa de archivos/tests y coincide con el código final.
2. La rama parte de `7c0c18695aa29b488338811e3640474fd920647d`; no hay merge a `main`.
3. Migraciones nuevas son aditivas, instalan en PostgreSQL 16 limpio y pasan upgrade poblado; ninguna migración histórica cambia.
4. `project_versions` sella una sola REV-A desde una operación APPLIED exacta y es evidencia restrictiva/append-only.
5. Vectores canónicos y los cinco namespaces de hash son exactos; todos los documentos de una revisión comparten `bom_hash`.
6. `ManufacturingFactsV1` conserva identidad/relaciones/refuerzo/manilla/infill y las coordenadas V1 sin cambiar `EngineResult`, cortes ni Golden.
7. Inspector server-side bloquea RED; GREEN almacenado no se confía; DOC-03/05 exigen completitud; DOC-06 permanece vacío.
8. `PurchaseRequirementsV1` conserva cada fuente exactamente una vez, agrupa sólo stock físicamente intercambiable y usa BFD SHOT-07 sin modificación semántica.
9. Glass/hardware/panel/accessory cumplen keys/modos/cobertura; mapping faltante falla cerrado.
10. Elegibilidad no altera WHAT; confirmación por order type es atómica, única e independiente entre tipos; send requiere acción explícita.
11. DOC-01…DOC-07 funcionan desde autoridad frozen; DOC-02/04/05 reconcilian; DOC-07 no se filtra.
12. Artifact slots y órdenes convergen bajo concurrencia; access firmado dura 3600 s y niega cross-tenant.
13. S19 es funcional, denso y claro para `WORKSHOP_MANAGER`; cantidades/BFD son read-only y órdenes confirmadas se distinguen.
14. DB gates, backend, engine, frontend lint/typecheck/build, Vitest, Playwright y adversarial tests están verdes.
15. `engine/tests/golden_example.json` conserva exactamente el hash de cálculo y SHA de archivo registrados arriba.
16. Un `py -3.12 scripts/check_dod.py all` final devuelve literalmente exit code 0, cero warnings y 20/20 mutaciones abatidas.
17. Commits son slices coherentes, la rama se publica y existe un único PR reviewable sin merge.

## Límites no implementados

Quedan fuera de SHOT-09: REV-B/sucesoras, clonación/SHOT-10, recepción/fulfillment, inventario/offcuts, cancelación/enmienda/reemplazo, batches adicionales, split parcial de líneas, explosión/compras por componente de hardware, supply forms de panel no `CUT_TO_SIZE/EA`, geometría extendida y secuenciación cronológica de taller.

## Condición de parada

Sólo se registra `RULE_0_STOP` ante una nueva contradicción material no resoluble por estas autoridades. La entrada debe usar exactamente `[PENDIENTE-DECISIÓN]`, enumerar autoridades conflictivas, invariante afectada y decisión mínima. Incertidumbre cosmética, naming interno o composición reversible de UI no detienen el shot.
