# PLAN SHOT-05 — Canvas 2D mínimo (FIXED + cotas)

**Estado:** FASE 2 — EJECUCIÓN AUTORIZADA; PD-05-01…PD-05-05 resueltas
canónicamente.
**Branch:** `shot-05`
**Base canónica:** `main @ b6587e56baa2bb3ec2d94b1dd2cd00a6f79ee964`
**Gate canónico:** dibujar G1 con números provenientes del engine en `<300 ms`,
cota editable por teclado y snapping operativo.
**Regla temporal:** `docs/PRD/PLAN_SHOTS.md` define qué parte de PRD-04, ADOBE y
ANIM pertenece a este shot.

---

## 1. Baseline Git y estado heredado

- `main`, `origin/main` y la base autorizada coincidían en
  `b6587e56baa2bb3ec2d94b1dd2cd00a6f79ee964` antes de crear la rama.
- El working tree estaba limpio.
- `shot-05` fue creada directamente desde esa base.
- SHOT-04 está cerrado; se reutilizan su shell, autenticación, tenancy, tema,
  cliente TypeScript generado y harness E2E sin reabrir sus contratos.
- `/engine` y los Golden snapshots quedan congelados y fuera del diff de SHOT-05.

## 2. Autoridad normativa leída

Se leyó, en el orden exigido:

1. `AGENTS.md`.
2. `docs/CONSTITUTION.md`.
3. `docs/PRD/PLAN_SHOTS.md`, fila SHOT-05.
4. `docs/PRD/PRD-04.md`.
5. `docs/PRD/PRD-DESIGN-SYSTEM-ADOBE.md`.
6. `docs/PRD/PRD-ANIMATIONS-INTERACTIONS.md`.
7. Frontend real de SHOT-04: rutas, `AppShell`, auth context, tema, tokens,
   telemetría, tests y configuración.
8. Cliente TypeScript generado y mutator de autenticación/organización.
9. Contrato real de `POST /api/v1/engine/calculate/`: serializers, vista,
   adapter, repository, OpenAPI y tests.
10. G1 congelado por SHOT-03: fixture, test Core, modelos y resultado del engine.

`docs/PRD/PRD-FRONTEND-APIS-COMPONENTS.md` se consultó sólo para contrastar el
contrato HTTP ya materializado; su jerarquía completa no amplía el alcance temporal
de SHOT-05.

### 2.1 Hechos congelados por las interfaces reales

- El frontend usa React 18, SVG dentro del Virtual DOM, TanStack Query y Zustand;
  no hay actualmente un store de diseño.
- `apiMutator` añade el Bearer verificado y `X-Organization-ID`; ningún componente
  debe reconstruir ese mecanismo.
- `engineCalculate(request)` acepta:
  `system_id`, `nominal_width_mm`, `nominal_height_mm`, `color` y
  `parametric_tree`.
- Las dimensiones del request y todos los resultados técnicos viajan como strings
  decimales. El endpoint rechaza números JSON para dimensiones.
- La respuesta SHOT-04 contiene exclusivamente `profile_cuts`,
  `reinforcements`, `glasses` y `hardware_items`.
- El endpoint requiere sesión tenant-bound; OWNER sigue requiriendo `aal2`.
- Los errores publicados son 400, 401, 403, 404, 409 y 422.
- El adapter vigente sólo admite color `WHITE` y tipologías ya soportadas por
  SHOT-03. SHOT-05 utilizará únicamente `FIXED`.
- La respuesta no contiene primitivas gráficas, coordenadas, espesor visual del
  marco, `calculation_hash` ni `inspector`.
- En el baseline no existe endpoint frontend para listar o resolver sistemas de
  perfiles; PD-05-05 autoriza añadir el discovery read-only mínimo.

## 3. Alcance exacto

Con PD-05-01…PD-05-05 resueltas y FASE 2 aprobada, se implementará:

1. Montar una vista S06 mínima dentro del `AppShell` protegido existente.
2. Modelar un único diseño `FIXED` compatible con G1.
3. Enviar el estado técnico mediante el cliente TypeScript generado a
   `/api/v1/engine/calculate/`.
4. Renderizar SVG puro a partir de inputs nominales humanos y resultados devueltos
   por el engine, sin fórmulas de fabricación en frontend.
5. Mostrar en SVG las cotas nominales horizontal/vertical, el paño FIXED y la
   dimensión del vidrio; mostrar FRAME, refuerzo, vidrio y junquillo en el panel
   técnico mínimo.
6. Editar ancho y alto por teclado con commit exclusivamente por Enter.
7. Redimensionar ancho/alto mediante grips y aplicar el snapping exterior congelado
   por PD-05-03, sin divisiones.
8. Medir y probar `<300 ms` con el contrato real congelado por PD-05-04.
9. Funcionar en Light Studio y Dark Graphite usando tokens semánticos existentes.
10. Cubrir estados loading/error de forma fail-closed y accesibilidad de teclado.

No se persistirán proyectos, posiciones ni versiones. El estado de este shot vive
en memoria de la sesión del editor.

## 4. Fuera de alcance / PROHIBIDO

- TURN, TILT_TURN, SLIDING, AWNING, DOOR o cualquier simbología de apertura que no
  sea `FIXED`.
- Crear SPLIT_H, SPLIT_V, postes, travesaños o editar topología para hacer pasar
  artificialmente el snapping.
- Hardware, G5–G7, pricing, Inspector R01–R14, BFD, OT, proyectos/versiones,
  catálogo CRUD, documentos, IA, diff IA o corrección en un clic.
- Fórmulas o cambios en `/engine`; edición o regeneración de Golden snapshots.
- Un segundo motor geométrico en el navegador.
- Konva, Fabric.js, D3 o cualquier dependencia nueva.
- Duplicar auth, active-org, RLS, generación OpenAPI o el cliente TypeScript.
- Hardcodear outputs G1 (`1006.00`, `970.00`, `910.00`, `919.00`) en código de
  producción.
- Usar resultados visuales convertidos a `number` como input de un cálculo técnico
  posterior.
- Inventar un resultado local si la API falla.
- Añadir `calculation_hash`, `inspector` u otros campos de shots futuros.
- Crear un quinto required context de CI o debilitar los cuatro existentes.

## 5. Arquitectura propuesta

```text
ReadyGuard + AppShell heredados
          |
          v
CanvasEditor2DView
  |-- Design state único (Zustand; strings decimales + BAY FIXED)
  |-- Engine request adapter (sin matemática)
  |       |
  |       v
  |   generated engineCalculate()
  |       |
  |       v
  |   apiMutator: Bearer + X-Organization-ID
  |       |
  |       v
  |   Django/RLS -> /engine -> EngineCalculateResponse
  |
  |-- TanStack Query: estado remoto de la última respuesta confirmada
  |-- CADViewportSvg: conversión exclusivamente visual string -> number
  |-- EditableDimension: draft efímero -> validación -> commit -> nuevo request
  `-- Resultados/cotas accesibles derivados de la respuesta
```

La ruta canónica es `/projects/demo/positions/g1/edit`. `demo` y `g1` son sólo
bootstrap de navegación, no filas persistidas. La vista descubre DEMO_60 mediante
`GET /api/v1/engine/systems/`; no se implementará SHOT-10 por anticipación.

### 5.1 Componentes previstos en FASE 2

| Componente/módulo | Responsabilidad única |
|---|---|
| `CanvasEditor2DView` | Orquestar estado, request, respuesta, estados fail-closed y composición dentro del shell. |
| `CADViewportSvg` | Renderizar el paño fijo, cristal y cotas permitidas como SVG semántico. |
| `EditableDimension` | Ofrecer edición realmente operable por teclado según PD-05-02. |
| `CanvasTechnicalResults` | Mostrar exclusivamente los resultados G1 autorizados por PD-05-01; no será el Inspector futuro. |
| `canvasStore` | Mantener una sola autoridad de inputs técnicos del diseño. |
| `useEngineCalculation` | Llamar al cliente generado y exponer loading/success/error; sin reimplementar HTTP. |
| `presentationGeometry` | Convertir strings técnicos a números sólo para viewBox/coordenadas de pantalla. |
| `snapping` | Algoritmo puro de resize exterior: 50 mm dentro de ±12 px, 10 mm fuera, 0.01 mm con Snap OFF y desempate HALF_UP. |

Se preferirán componentes pequeños bajo `frontend/src/features/canvas/`. No se
creará una jerarquía completa de Inspector, tool palettes, hojas o mullions que el
gate no necesita.

## 6. Modelo de estado

### 6.1 Autoridad técnica única

El store de diseño contendrá una sola copia comprometida de:

```text
systemId                 <- único DEMO_60 descubierto en runtime
nominalWidthMm           <- string decimal humano, inicialmente G1 1000.00
nominalHeightMm          <- string decimal humano, inicialmente G1 1000.00
color                    <- WHITE, único color admitido y color de G1
parametricTree           <- BAY/FIXED de G1, sin width/height duplicados
```

El árbol mínimo de G1 conserva `id`, `type=BAY`, `opening_type=FIXED`,
`glass_thickness_mm="4.00"` y `glass_spec="4 Float Incoloro"`. El adapter del backend aplica las
dimensiones nominales top-level; por ello no se copiarán también dentro del árbol.

### 6.2 Estado que no es autoridad de diseño

- El texto incompleto mientras se edita una cota es un draft local del input. Sólo
  Enter o `pointerup` de un resize puede promover un candidate, y únicamente una
  respuesta 200 lo consolida como input aceptado.
- La respuesta del engine permanece en la caché de TanStack Query y no se copia a
  otro store.
- `selection` es estado efímero de foco del único BAY; no modifica geometría.
- `viewport` es estado puramente visual. Escala y offsets jamás vuelven al request.
- Loading/error son estados de la operación, no resultados técnicos.

## 7. Flujo G1: UI → API → SVG

1. La vista protegida consulta `GET /api/v1/engine/systems/`, selecciona exactamente
   una fila `code=DEMO_60 && is_demo=true` y toma su `id` runtime.
2. El store forma el input G1: `1000.00 × 1000.00`, `WHITE`, BAY `FIXED`, vidrio
   `4.00`, spec `4 Float Incoloro`.
3. `useEngineCalculation` construye `EngineCalculateRequestRequest` usando strings
   sin convertir a `number`.
4. `engineCalculate()` realiza el POST; `apiMutator` añade sesión y active-org.
5. Django valida JWT/tenant/RLS, carga el catálogo efectivo y delega la matemática
   al engine puro.
6. La respuesta se conserva con sus strings exactos.
7. Selectores por `role`, `bay_id` y colección alimentan texto/cotas y atributos SVG.
8. Sólo `presentationGeometry` convierte dimensiones necesarias a `number` para
   `viewBox`, escala y coordenadas visuales.
9. Esos números de presentación no pueden actualizar el store técnico ni producir
   cortes, refuerzos, vidrio o junquillos.

Los expectations de tests congelan G1:

- nominal: `1000 × 1000 mm`;
- FRAME cut: `1006.00 mm`;
- frame reinforcement: `970.00 mm`;
- glass: `910.00 × 910.00 mm`;
- glazing bead: `919.00 mm`.

Los cuatro outputs sólo pueden aparecer como expectations/fixtures de tests. El
código de producción debe obtenerlos de `EngineCalculateResponse`.

## 8. Frontera Decimal/string → render number

- Request, store y texto técnico conservan strings decimales.
- No se añade una librería decimal.
- Para coordenadas SVG se permite una conversión explícita y aislada a `number`,
  validando que sea finita y positiva donde corresponda.
- La conversión sirve exclusivamente para transformación SVG, escala, offsets y
  hit targets.
- Ningún valor convertido se serializa de vuelta al request.
- La edición y el snapping cambian milímetros mediante una representación decimal
  exacta basada en strings/unidades enteras de centésimas y desempate HALF_UP, no
  mediante aritmética binaria como autoridad.

## 9. Modelo de cotas

- SHOT-05 edita tanto `nominal_width_mm` como `nominal_height_mm`.
- La unidad es `mm`; la forma aceptada/enviada es string decimal con máximo dos
  decimales. Tras una respuesta 200 se muestra siempre con dos decimales
  (`1000` → `1000.00`, `1000.5` → `1000.50`).
- La validación cliente protege únicamente transporte: finito, positivo y
  representable por `DecimalField(max_digits=10, decimal_places=2)`, rango
  sintáctico `0.01`–`99999999.99 mm`. No declara fabricabilidad.
- Cada cota entra en edición al recibir foco mediante Tab o click.
- Enter valida y envía un POST candidate. Sólo un 200 consolida el valor aceptado.
- Escape descarta el candidate, restaura el último aceptado y no llama a la API.
- Tab conserva navegación accesible estándar. Blur sin Enter descarta y restaura;
  nunca hace commit implícito.
- Un rechazo backend conserva el último input aceptado, no genera fallback y
  presenta el error contractual sin asociar la respuesta vieja al candidate.
- Los nombres accesibles exactos son `Ancho nominal (mm)` y `Alto nominal (mm)`;
  el foco visible usa `--theme-cyan-tool`.

## 10. Modelo de snapping

PD-05-03 separa dos contratos:

- El snapping histórico de ANIM §3 sigue reservado para divisiones SPLIT/MULLION,
  incluidos centro 50% y vano mínimo 250 mm. No se implementa aquí.
- SHOT-05 añade dos grips de presentación sobre el FIXED: uno redimensiona el ancho
  exterior y otro el alto exterior. El árbol sigue siendo un único BAY/FIXED.
- Durante drag existe sólo un preview no autoritativo. `pointerup` produce candidate,
  envía un POST y únicamente un 200 consolida el input.
- Snap ON: convertir puntero a candidate mm con el transform actual; obtener el
  múltiplo de 50 mm más cercano; si su distancia visual es `<=12 px`, usarlo; fuera
  de ese radio, cuantizar al múltiplo de 10 mm más cercano.
- Snap OFF: cuantizar exclusivamente a `0.01 mm`.
- Todo desempate usa ROUND_HALF_UP implementado con aritmética decimal exacta; queda
  prohibido usar `Math.round()` como autoridad.
- La escala altera cuántos mm representan 12 px, pero el radio visual permanece
  exactamente 12 px.
- La guía de snapping se muestra durante la atracción y consume tokens semánticos.
- El candidate visual nunca calcula cortes: siempre vuelve como string al endpoint.

## 11. Modelo de viewport

- Es obligatorio un zoom-to-fit inicial legible de G1 y los transforms necesarios
  para resize/snapping; su transformación es presentación pura y efímera.
- Wheel zoom 20–500%, middle-button pan, space+drag y shortcut F no son gate de
  SHOT-05 y se difieren.
- La futura navegación interactiva podrá reemplazar/extender ese estado sin tocar
  el design state.
- No se afirmará cumplimiento integral de ANIM §2 en SHOT-05.

## 12. Performance budget

Contrato congelado por PD-05-04:

1. Precondición: sesión autenticada, active-org y sistema resueltos, editor cargado y
   G1 inicial visible. No incluye Magic Link, TOTP, navegación, bootstrap de org ni
   discovery inicial.
2. Ejecutar en Chromium Playwright, un worker, contra Vite, Django y
   Supabase/PostgreSQL reales levantados por el harness existente.
3. Una edición de warm-up no contabilizada y cinco ediciones secuenciales medidas.
4. Inicio con `performance.now()` inmediatamente antes de consolidar Enter o
   `pointerup` válidos.
5. Final en el primer `requestAnimationFrame` posterior a POST, aceptación del
   resultado remoto, SVG actualizado y cotas/panel correspondientes a la misma
   revisión.
6. Incluye cliente generado, HTTP, JWT, RLS, DB, `/engine`, response, React y SVG.
7. Cada muestra debe ser estrictamente `<300.00 ms`; `300.00 ms` falla. No se usa
   promedio, mediana ni p95.
8. Sin retries que oculten la primera medición. Si falla, se registran las cinco
   duraciones disponibles para diagnóstico.
9. Ausencia de servidor, sesión, sistema, respuesta o marca visible falla; no hay
   skips ni mocks para este gate.

## 13. Loading y errores fail-closed

| Estado | Comportamiento propuesto |
|---|---|
| Primer cálculo | SVG técnico vacío; estado `aria-live`/`role=status`; `aria-busy=true`. |
| Recálculo | La dimensión comprometida cambia, el resultado anterior deja de presentarse como vigente y el canvas queda pending hasta éxito. |
| 400 | Mensaje i18n de entrada inválida; no cálculo local. |
| 401 | Mensaje i18n de sesión no válida; sin resultados técnicos. |
| 403 | Mensaje i18n de acceso/MFA; sin resultados técnicos. |
| 404 | Mensaje i18n de sistema no visible; sin resultados técnicos. |
| 409 | Mensaje i18n de selección de organización; sin resultados técnicos. |
| 422 | Mensaje i18n de contrato no soportado; sin fallback a otra tipología. |
| Red/5xx | Mensaje i18n de engine no disponible; sin outputs estimados. |

El último resultado exitoso puede permanecer en caché interna, pero no se dibuja
como resultado vigente mientras el request actual esté pending o failed.

## 14. Theme y accesibilidad

- Canvas, cota, foco, guía de snapping, superficies y errores consumirán variables
  `--theme-*`; no habrá hex fuera de `tokens.css`.
- Se probarán Light Studio y Dark Graphite mediante el `ThemeProvider` existente.
- SVG tendrá nombre accesible y grupos/valores identificables sin depender de color.
- La cota será un control de teclado real, no un elemento SVG con `onKeyDown`
  decorativo.
- Enter/Escape/Tab, blur y foco se probarán con la semántica congelada por PD-05-02.
- No se utilizará una captura pixel-perfect como única evidencia de exactitud.

## 15. Archivos previstos y contribución al gate

### 15.1 Cambios normativos previos a la implementación

| Acción | Archivo | Propósito |
|---|---|---|
| CREAR/ACTUALIZAR | `docs/plans/PLAN_SHOT-05.md` | Memoria persistente del alcance, arquitectura, gate y PD-05-01…05 resueltas. |
| MODIFICAR | `docs/PRD/PRD-ANIMATIONS-INTERACTIONS.md` | Separar el snapping de divisiones futuro del resize exterior de SHOT-05 sin alterar la fórmula histórica. |
| MODIFICAR | `docs/PRD/PRD-FRONTEND-APIS-COMPONENTS.md` | Congelar el contrato read-only de discovery de sistemas. |

### 15.2 Cambios autorizados para FASE 2

| Acción prevista | Archivo/ruta | Aporte al gate |
|---|---|---|
| CREAR | `frontend/src/features/canvas/CanvasEditor2DView.tsx` | Ensambla flujo G1 y estados visibles. |
| CREAR | `frontend/src/features/canvas/CADViewportSvg.tsx` | Dibuja el fijo y cotas mediante SVG puro. |
| CREAR | `frontend/src/features/canvas/EditableDimension.tsx` | Gate de edición por teclado. |
| CREAR | `frontend/src/features/canvas/CanvasTechnicalResults.tsx` | Expone outputs autorizados del engine sin construir Inspector. |
| CREAR | `frontend/src/features/canvas/canvasStore.ts` | Autoridad única de inputs técnicos. |
| CREAR | `frontend/src/features/canvas/useEngineCalculation.ts` | Integra TanStack Query con el cliente generado. |
| CREAR | `frontend/src/features/canvas/presentationGeometry.ts` | Aísla la conversión visual a `number`. |
| CREAR | `frontend/src/features/canvas/snapping.ts` | Gate de snapping exterior resuelto en PD-05-03. |
| CREAR | Tests colocados junto a los módulos anteriores | Pruebas puras y de interacción sensibles a cambios. |
| CREAR | `frontend/tests/e2e/canvas.spec.ts` | G1 y performance contra Auth/API/DB/engine reales. |
| CREAR | `frontend/src/features/canvas/canvas.css` | Layout y SVG dual mediante tokens. |
| MODIFICAR | `frontend/src/App.tsx` | Monta `/projects/demo/positions/g1/edit` con los guards heredados y carga la vista Canvas de forma diferida. |
| CREAR | `frontend/src/app/DashboardPage.tsx` | Expone la acción Dashboard `Abrir Demo G1` sin crear persistencia de proyectos. |
| MODIFICAR | `frontend/src/i18n/es-CL.ts` | Añade todo texto visible mediante claves ES-CL. |
| MODIFICAR | `frontend/src/index.css` | Integra los estilos del Canvas bajo los tokens y temas heredados. |
| MODIFICAR | `frontend/package.json` | Mantiene el gate Prettier estricto y reproducible con los finales de línea del checkout Windows, sin cambiar dependencias. |
| MODIFICAR | `scripts/check_dod.py` | Añade guards fail-closed simples para artefactos/tests de SHOT-05 y evita outputs G1 hardcodeados en producción. |
| MODIFICAR | `scripts/check_auth_e2e.py` | Conserva toda la evidencia E2E real en salida UTF-8 también bajo el host Windows. |
| MODIFICAR | `backend/engine_api/serializers.py` | Publica el response mínimo de sistemas visibles. |
| MODIFICAR | `backend/engine_api/repository.py` | Lista sistemas RLS-visibles con orden determinista y cuatro campos permitidos. |
| MODIFICAR | `backend/engine_api/views.py` | Añade GET tenant-bound con el mismo JWT/MFA/RLS que calculate. |
| MODIFICAR | `backend/engine_api/urls.py` | Registra `GET /api/v1/engine/systems/`. |
| MODIFICAR | `backend/tests/test_engine_api.py` y tests de integración RLS | Verifica contrato, orden, aislamiento y auth del discovery. |
| MODIFICAR | `backend/config/settings.py` | Mantiene la descripción OpenAPI neutral y vigente para el límite auth/tenant + engine. |
| REGENERAR | `backend/openapi.yaml`, `frontend/src/api/generated/` | Publica y consume el contrato mediante drf-spectacular/Orval, sin edición manual del cliente. |

No se prevén cambios en dependencias, `package-lock.json`, migraciones, seed, RLS,
`.github/workflows/ci.yml` ni `/engine`.

## 16. Resoluciones canónicas PD-05-01…PD-05-05

### PD-05-01 — RESUELTA: valores G1 visibles

- SVG obligatorio: cota nominal horizontal `1000.00 mm`, cota nominal vertical
  `1000.00 mm`, paño `FIXED` y vidrio `910.00 × 910.00 mm`.
- Las cotas nominales proceden del estado paramétrico de entrada.
- La dimensión del vidrio procede exclusivamente de
  `EngineCalculateResponse.glasses`.
- `CanvasTechnicalResults` muestra FRAME cut `1006.00 mm`, FRAME reinforcement
  `970.00 mm`, glass `910.00 × 910.00 mm` y glazing bead `919.00 mm`.
- El panel no muestra Inspector, pricing, hardware, BFD, hash ni OT.
- Los outputs `1006.00`, `970.00`, `910.00`, `919.00` están prohibidos como
  constantes de producción y sólo aparecen como expectations/fixtures de tests.
- Un test sentinel cambia la respuesta mock a otros valores y exige que SVG/panel
  cambien sin reconstruirlos con fórmulas frontend.

### PD-05-02 — RESUELTA: contrato de cota editable

- Se editan ancho y alto, cuya única autoridad aceptada es `nominal_width_mm` y
  `nominal_height_mm` del estado paramétrico.
- Unidad `mm`; transporte como string decimal con máximo dos decimales. Tras éxito,
  se muestran siempre dos decimales.
- Rango sintáctico cliente: `0.01`–`99999999.99 mm`, finito, positivo y compatible
  con `DecimalField(max_digits=10, decimal_places=2)`. No afirma fabricabilidad; la
  autoridad final es backend + `/engine`.
- Tab enfoca cada cota. Al foco entra en edición.
- Enter valida, envía nuevo POST y sólo un 200 consolida el valor.
- Escape descarta/restaura sin POST. Tab navega normalmente. Blur sin Enter descarta
  y no hace commit implícito.
- Un rechazo conserva el último input aceptado, muestra el error y no promueve el
  candidate ni inventa geometría.
- Nombres accesibles exactos: `Ancho nominal (mm)` y `Alto nominal (mm)`; foco
  visible obligatorio.

### PD-05-03 — RESUELTA: snapping exterior sin MULLION

- ANIM §3 original permanece como snapping futuro de postes/travesaños, centro 50%
  y mínimo 250 mm. Nada de ello se implementa en SHOT-05.
- SHOT-05 ofrece un grip horizontal y uno vertical que sólo cambian candidates de
  las cotas exteriores de un único BAY/FIXED.
- Drag es preview no autoritativo; sólo `pointerup` crea POST y un 200 consolida.
- Snap ON: puntero → candidate mm con el transform; múltiplo de 50 mm más cercano;
  snap a 50 si queda dentro de `±12 px`; en otro caso múltiplo de 10 mm más cercano.
- Snap OFF: candidate cuantizado a `0.01 mm`.
- Desempate exacto ROUND_HALF_UP. `Math.round()` no es autoridad.
- La escala cambia el threshold equivalente en mm sin alterar los 12 px visuales.
- Se permite matemática pura de presentación para snapping, pero el candidate vuelve
  como string al engine y jamás calcula cortes localmente.

### PD-05-04 — RESUELTA: gate real `<300 ms`

- Precondición: usuario autenticado, active-org y sistema resueltos, editor cargado y
  G1 visible; excluye Magic Link, TOTP, navegación, org bootstrap y discovery.
- Inicio: `performance.now()` justo antes de consolidar Enter o `pointerup` válido.
- Fin: primer `requestAnimationFrame` después de POST, aceptación de server state,
  SVG nuevo y cotas/panel de la misma revisión.
- Incluye generated client, HTTP, JWT, RLS, DB, `/engine`, response, React y SVG.
- Chromium Playwright contra Vite/Django/Supabase/PostgreSQL reales, dentro de `Test
  Suite` existente.
- Una warm-up no medida y cinco muestras medidas, secuenciales.
- Cada muestra debe ser `<300.00 ms`; exactamente `300.00` falla. Sin promedio,
  mediana, p95 ni retry que oculte un resultado.
- Ante fallo se registran las cinco duraciones disponibles. Timeout/ausencia de
  infraestructura no se transforma en skip.

### PD-05-05 — RESUELTA: discovery runtime y ruta S06

- Ruta canónica: `/projects/:id/positions/:posId/edit`; bootstrap SHOT-05 exacto:
  `/projects/demo/positions/g1/edit`. Los parámetros no representan filas ni
  autorizan GET/save/autosave/versionado.
- Dashboard añade la acción visible `Abrir Demo G1`.
- El UUID DEMO_60 está prohibido como autoridad productiva del frontend. El valor
  determinista `3067da09-3119-5ad0-a1d5-498cd2dfd753` sólo puede ser expectation de
  test.
- Se añade `GET /api/v1/engine/systems/`, read-only, con el mismo JWT, active-org,
  OWNER aal2 y contexto RLS de calculate.
- Sólo devuelve sistemas `is_active=TRUE` visibles para la organización activa,
  globales o propios, ordenados por `is_demo DESC`, `code ASC`, `id ASC`.
- Cada elemento expone exclusivamente `id`, `code`, `name`, `is_demo`.
- La vista exige exactamente una coincidencia `code === "DEMO_60" && is_demo ===
  true`; cero produce `demo_system_unavailable`, más de una
  `demo_system_ambiguous`. Nunca elige la primera.
- OpenAPI y Orval se regeneran; el frontend consume sólo el cliente generado.
- El estado inicial usa el ID descubierto, `1000.00 × 1000.00`, `WHITE` y BAY/FIXED
  con vidrio `4.00`, spec `4 Float Incoloro`.
- Zustand mantiene inputs, draft, selection, viewport y snap enabled; TanStack Query
  es autoridad del resultado y no se copia la respuesta completa a Zustand.

**Resultado normativo:** no quedan `[PENDIENTE-DECISIÓN]` conocidos tras estas cinco
resoluciones. Cualquier vacío nuevo durante FASE 2 reactiva Regla 20 y detiene el
shot.

## 17. Estrategia de tests

### 17.1 Tests puros Vitest

- Conversión de strings a coordenadas sólo visuales; rechazo fail-closed de valores
  no finitos/no válidos.
- Selectores de respuesta por role/bay sin constantes G1 de producción.
- Algoritmo de snapping exacto y tests de borde conforme a PD-05-03.
- Mutación de una centésima debe cambiar el resultado esperado y fallar
  frente a una expectation anterior.

### 17.2 React Testing Library

- La vista usa valores sentinel devueltos por el cliente mockeado; cambiar la
  respuesta cambia SVG/texto. Esto prueba que no hay outputs G1 duplicados.
- Flujo focus → edición → confirmación → request nuevo → respuesta → SVG/cota.
- Escape, Tab, inválidos, loading y cada familia de error publicada.
- Nombre accesible, foco visible y estado `aria-busy`/live.
- Mismo contenido técnico en light/dark.

Los mocks aquí aíslan interacción, no sustituyen el gate E2E real.

### 17.3 Playwright E2E real

- Reutiliza Supabase CLI, Mailpit, sesión ESTIMATOR real, membership real, Django y
  Vite del harness SHOT-04.
- El setup de test puede usar service-role sólo para crear/consultar fixtures; la
  aplicación y sus queries normales nunca lo reciben.
- Obtiene el sistema DEMO_60 real conforme a PD-05-05.
- Observa el POST real, comprueba strings de request y respuesta, y luego verifica
  atributos/texto SVG G1.
- Ejecuta edición de cota y comprueba segundo POST y actualización sincronizada.
- Ejecuta el benchmark acordado en PD-05-04.
- Alterna light/dark y verifica que el SVG continúa visible mediante tokens, además
  de datos técnicos; screenshot no será la única aserción.

## 18. Matriz Gate → evidencia/test 1:1

| Gate | Evidencia obligatoria | Tipo | Estado normativo |
|---|---|---|---|
| G1 visible | E2E real observa discovery, request G1 y respuesta API; DOM/SVG muestra nominal, FIXED, vidrio y panel completo. Test RTL sentinel demuestra ausencia de constantes. | Playwright + RTL | Resuelto PD-05-01/05 |
| Números del engine | Trazabilidad `engineCalculate` → response strings → selectores → SVG; guard rechaza outputs G1 hardcodeados en source de producción. | Vitest + checker + E2E | Resuelto PD-05-01 |
| Cota editable por teclado | Width y height: focus, draft, Escape/blur sin POST, Enter con POST, éxito/error transaccional y SVG/cota sincronizados. | RTL + Playwright | Resuelto PD-05-02 |
| Snapping operativo | 50 mm en ±12 px, 10 mm fuera, OFF a 0.01, HALF_UP, escala y drag/pointerup real. | Vitest + Playwright | Resuelto PD-05-03 |
| `<300 ms` | Warm-up + cinco muestras reales input commit → primer frame coherente; cada una estrictamente `<300.00 ms`. | Playwright | Resuelto PD-05-04/05 |
| Tema dual | Canvas, cotas, grips, guía y panel legibles/identificables en Light Studio y Dark Graphite, usando tokens. | RTL + Playwright | Resuelto |
| Shell navegable | Dashboard `Abrir Demo G1` → ruta canónica protegida, sin persistencia ni duplicar auth/tenancy/theme. | RTL + Playwright | Resuelto PD-05-05 |

## 19. CI y Gauntlet

Se conservan exactamente estos contexts:

1. `Lint & Typecheck` — Ruff, ESLint, TypeScript, Prettier, mypy y guards.
2. `Test Suite` — engine/backend/Vitest y Playwright real; aquí entra el gate Canvas.
3. `Frontend Build` — build Vite de producción.
4. `Database Gate` — RLS/pgTAP/PostgreSQL 16 heredados, sin cambios funcionales.

No se espera modificar `.github/workflows/ci.yml`: los nuevos tests bajo las rutas
existentes son descubiertos por Vitest/Playwright y el checker actual. El checker se
extenderá de forma simple y fail-closed, sin parser complejo ni `allow_fail`.

Antes del cierre de FASE 2 se ejecutará `python scripts/check_dod.py all` hasta
obtener EXIT CODE 0 real. También se verificará de forma individual:

- Ruff;
- mypy;
- backend pytest;
- engine pytest sin cambios en G1–G4/xfails;
- frontend typecheck;
- Vitest;
- ESLint;
- Prettier check;
- build producción;
- Playwright E2E real;
- Database Gate/pgTAP;
- OpenAPI/client drift.

## 20. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación planificada |
|---|---|---|
| Hardcodear G1 para “pasar” visualmente | Verifier theater y divergencia futura | Sentinel test + E2E real + guard en checker. |
| Convertir strings a `number` y devolverlos al request | Pérdida de precisión técnica | Módulo de presentación unidireccional y tests de frontera. |
| Implementar split/mullion para snapping | Adelanto de SHOT-06+ | Snapping exterior separado por PD-05-03 y guard de alcance. |
| UUID DEMO_60 inválido | 404 en integración real | Discovery RLS real por PD-05-05; E2E prohíbe UUID productivo hardcodeado. |
| Doble autoridad Zustand/Query/local state | Canvas y cota desincronizados | Inputs comprometidos sólo en store; response sólo en Query; draft sólo local. |
| Resultado viejo visible durante recálculo | Usuario interpreta geometría stale como vigente | Ocultar/marcar no vigente y fallar cerrado hasta respuesta actual. |
| Benchmark flaky | Gate falso positivo/negativo | Contrato explícito de entorno, reloj, warm-up y muestras en PD-05-04. |
| Pixel snapshot pasa con números incorrectos | Evidencia matemática insuficiente | Assertions de strings/atributos + interacción + E2E real. |
| Romper SHOT-04 | Regresión de auth/tenant/MFA | Reusar guards/mutator; suites SHOT-04 siguen obligatorias. |
| Hex o estilos monomodo | Incumplimiento ADOBE | Tokens semánticos y tests light/dark. |

## 21. Alineación con shots anteriores y futuros

- Consume SHOT-02: DEMO_60 global y RLS.
- Consume SHOT-03: G1 y engine determinista sin modificarlo.
- Consume SHOT-04: auth, active-org, endpoint, cliente, PostHog base, shell y tema.
- Entrega a shots posteriores una vista/rendering mínimo extensible, pero no añade
  sus tipologías ni reglas.
- SHOT-06 conserva engine total/hardware; SHOT-07 conserva Inspector/BFD; SHOT-10
  conserva persistencia de proyectos/versiones y catálogo manual.

## 22. Contradicciones conocidas y condición de continuación

**Contradicciones conocidas tras las resoluciones: NO.**

- PD-05-03 separó formalmente snapping de divisiones futuro y snapping exterior de
  SHOT-05.
- PD-05-05 reemplazó el UUID ejemplificado como fuente runtime por discovery RLS
  read-only, conservando el UUID sólo como expectation de test.
- PD-05-01, PD-05-02 y PD-05-04 fijaron evidencia visible, edición y performance.

**Condición de continuación satisfecha:** FASE 2 está autorizada. Si aparece un
nuevo vacío normativo real, se registra `[PENDIENTE-DECISIÓN]` y el shot se detiene.
