# Plan de Implementación — SHOT-01: Monorepo + CI + Tooling

## 1. Fuentes, estado observado y objetivo

- **Shot:** `SHOT-01` — Fase 0, semana 1.
- **Fuentes leídas, en orden:** `docs/CONSTITUTION.md`, `docs/PRD/PLAN_SHOTS.md` y `docs/PRD/PRD-00.md`.
- **Gate textual:** pipeline verde sobre stubs con Ruff, Mypy estricto en `engine/`, Pytest en `engine/` y `backend/`, Vitest, TypeScript, build del frontend y branch protection activa.
- **Estado inicial real:** rama `main` limpia y alineada con `origin/main`; no existen aún paquetes ejecutables `engine`, `backend` o `frontend`. Sí existen el manifiesto G, el harness, el workflow parcial, el `Makefile` y documentación.
- **Objetivo:** dejar un monorepo mínimo, ejecutable y reproducible que pruebe la instalación y el cableado de los tres módulos sin implementar reglas de negocio. El checker canónico será `python scripts/check_dod.py all` y rechazará por defecto comandos ausentes, suites ausentes, warnings y cualquier retorno distinto de cero.

### 1.1 Alineación global

- **Upstream consumido:** Constitución v1.2, gate de `PLAN_SHOTS.md`, PRD-00 disponible y `engine/tests/GOLD_CASES_MANIFEST.json` únicamente como manifiesto pre-engine.
- **Downstream:** todos los shots 02–24 dependen de la estructura, entornos, contratos de comandos y CI creados aquí. SHOT-02 usará el backend y CI; SHOT-03 extenderá el paquete puro `engine`; SHOT-04 extenderá los stubs Django/React sin que SHOT-01 adelante auth, API ni shell visual.
- **Contratos que se preservan:** `make lint`, `make typecheck`, `make test`, `make dod`, `make gauntlet`, `make goldgen` y `make shot-XX` seguirán siendo las entradas públicas del repositorio.

## 2. Alcance exacto

### 2.1 Crear

#### Raíz y Python

- `[NEW] pyproject.toml` — configuración raíz y única de Ruff, Mypy estricto y Pytest; excluye documentación/artefactos y hace que los comandos del gate sean reproducibles desde la raíz.
- `[NEW] requirements-dev.txt` — conjunto cerrado y fijado de herramientas Python necesarias para ejecutar el gate local y en CI, una vez resuelta la lista normativa pendiente.

#### Engine puro

- `[NEW] engine/pyproject.toml` — metadatos del paquete Python puro, sin dependencias de Django, red ni I/O.
- `[NEW] engine/src/dekopen_engine/__init__.py` — superficie mínima importable del paquete; no contendrá fórmulas, dimensiones, dinero ni lógica de shots futuros.
- `[NEW] engine/tests/test_package.py` — prueba no vacía del contrato de importación y metadatos del paquete. No pretende certificar G-cases ni tolerancias que corresponden a SHOT-03/06/24.

#### Backend Django mínimo

- `[NEW] backend/manage.py` — punto de entrada Django.
- `[NEW] backend/config/__init__.py` — declara el paquete de configuración.
- `[NEW] backend/config/settings.py` — settings mínimos de test/build, sin modelos, tablas, tenancy, auth, API, red ni secretos.
- `[NEW] backend/config/urls.py` — URLConf vacío; los endpoints pertenecen a SHOT-04.
- `[NEW] backend/config/wsgi.py` — bootstrap WSGI estándar.
- `[NEW] backend/tests/__init__.py` — paquete de pruebas.
- `[NEW] backend/tests/test_bootstrap.py` — prueba de arranque/configuración de Django sin crear funcionalidad de negocio.
- `[NEW] backend/requirements.txt` — dependencias backend fijadas y limitadas a las expresamente aprobadas para el scaffold.

#### Frontend React/Vite mínimo

- `[NEW] frontend/package.json` — scripts `lint`, `typecheck`, `test` y `build`, con solo dependencias aprobadas del stack de SHOT-01.
- `[NEW] frontend/package-lock.json` — resolución reproducible usada por `npm ci`.
- `[NEW] frontend/tsconfig.json` — TypeScript strict y referencias de build.
- `[NEW] frontend/tsconfig.app.json` — opciones estrictas para `src`.
- `[NEW] frontend/tsconfig.node.json` — opciones estrictas para la configuración Vite.
- `[NEW] frontend/vite.config.ts` — configuración de build y Vitest.
- `[NEW] frontend/eslint.config.js` — ESLint fail-closed y cero warnings.
- `[NEW] frontend/.prettierrc.json` — formato determinista.
- `[NEW] frontend/postcss.config.js` — integración mínima de Tailwind/PostCSS según la versión aprobada.
- `[NEW] frontend/tailwind.config.ts` — rutas de contenido, sin colores propios ni hexadecimales.
- `[NEW] frontend/index.html` — entrada Vite mínima.
- `[NEW] frontend/src/main.tsx` — montaje React.
- `[NEW] frontend/src/App.tsx` — stub estructural sin UI de producto ni texto visible hardcodeado.
- `[NEW] frontend/src/App.test.tsx` — smoke test Vitest del montaje del stub.
- `[NEW] frontend/src/index.css` — directivas Tailwind únicamente; cero hex fuera de tokens.
- `[NEW] frontend/src/vite-env.d.ts` — tipos de Vite.
- `[NEW] frontend/src/test/setup.ts` — setup mínimo de Vitest/DOM.

### 2.2 Modificar

- `[MODIFY] scripts/check_dod.py` — convertir el checker actual en rechazo por defecto: sin `allow_fail`, sin omitir herramientas/suites, con cada comando del gate ejecutado y reportado, propagación exacta del primer código no cero y build obligatorio.
- `[MODIFY] scripts/check_dod.sh` — mantener compatibilidad POSIX delegando en el checker Python canónico, evitando dos implementaciones divergentes.
- `[MODIFY] .github/workflows/ci.yml` — implementar los tres jobs exigidos: `Lint & Typecheck`, `Test Suite` y `Frontend Build`; instalar desde manifiestos bloqueados, usar `npm ci`, ejecutar los mismos comandos locales y fallar ante cualquier error.
- `[MODIFY] .pre-commit-config.yaml` — apuntar al checker canónico y eliminar bypasses o lógica duplicada.
- `[MODIFY] Makefile` — conservar sus entradas públicas y alinear cada target con el checker fail-closed; `dod` seguirá ejecutando exactamente `python scripts/check_dod.py all`.
- `[MODIFY] README.md` — quickstart reproducible y procedimiento verificable de branch protection para `main`, incluidos los nombres exactos de checks requeridos y la prohibición de merge directo.
- `[MODIFY] docs/plans/PLAN_SHOT-01.md` — memoria persistente del alcance aprobado, riesgos, resultados reales y cierre sin merge.

### 2.3 Prohibido

- `[PROHIBIDO]` Implementar fórmulas, geometría, BOM, optimización, precios, unidades de dinero/mm o editar/generar snapshots golden.
- `[PROHIBIDO]` Cambiar `engine/tests/GOLD_CASES_MANIFEST.json` o afirmar que G1–G12 están probados en este shot.
- `[PROHIBIDO]` Crear modelos/DDL/RLS de SHOT-02; endpoints, auth, tenancy, OpenAPI, PostHog o shell ADOBE de SHOT-04; cualquier feature de SHOT-03–24.
- `[PROHIBIDO]` Agregar dependencias fuera de la lista cerrada que apruebe el owner; usar `float` en `engine`; introducir colores hexadecimales en frontend; leer o rescatar features de `docs/archive/`.
- `[PROHIBIDO]` Modificar PRDs, la Constitución, `.env.example` o documentación duplicada fuera de este plan y README.
- `[PROHIBIDO]` Hacer merge a `main`, taggear otro shot o reescribir historial.

## 3. Cómo cada cambio satisface el gate

| Requisito del gate | Evidencia mecánica prevista |
|---|---|
| Ruff | `ruff check .` termina en 0; herramienta ausente o warnings rechazan el gate. |
| Mypy | `mypy engine/` usa modo estricto y termina en 0. |
| Pytest engine | `pytest engine/ -q` descubre al menos una prueba real y termina en 0. |
| Pytest backend | `pytest backend/ -q` arranca Django, descubre al menos una prueba real y termina en 0. |
| TypeScript | `npm run typecheck`/`npx tsc --noEmit` desde `frontend/` termina en 0. |
| Vitest | `npx vitest run` desde `frontend/` descubre al menos una prueba y termina en 0. |
| Build | `npm run build` desde `frontend/` produce el bundle y termina en 0. |
| Anti-patrones | El checker inspecciona `engine/src` por `float(` y frontend por hex crudo; cualquier hallazgo termina en 1. |
| CI | Los tres jobs ejecutan los mismos comandos con instalaciones reproducibles y no contienen `continue-on-error`, `|| true` ni retornos ignorados. |
| Branch protection | `main` exige PR y los tres nombres estables de checks; la configuración y evidencia de activación se documentan. |

El harness también verificará que los directorios, manifiestos y suites obligatorios existan. Un repositorio vacío o una herramienta no instalada no podrá producir un falso verde.

## 4. Secuencia de construcción tras aprobación

1. Crear/cambiar a la rama `shot-01` desde el `main` limpio actual.
2. Resolver los `[PENDIENTE-DECISIÓN]` antes de instalar o fijar dependencias.
3. Crear el scaffold Python/engine/backend y sus smoke tests.
4. Crear el scaffold frontend, lockfile y sus comprobaciones estrictas.
5. Endurecer el checker, luego alinear Makefile, pre-commit y CI.
6. Documentar y activar branch protection; capturar evidencia verificable.
7. Ejecutar `python scripts/check_dod.py all`. Reparar dentro del alcance hasta exit code 0; a la tercera repetición de la misma causa, detenerse en MODO DIAGNÓSTICO con las tres trazas, hipótesis y opciones.
8. Revisar el diff completo, confirmar que no se tocaron fórmulas/golden y realizar commits convencionales atómicos.
9. Push de `shot-01`, publicar el resumen de cada comando con su salida real y esperar `MERGE`.

Commits previstos, ajustables solo para mantener atomicidad real:

1. `chore(engine): scaffold pure python package`
2. `chore(app): scaffold backend and frontend stubs`
3. `ci: enforce fail-closed shot-01 gate`
4. `docs: document shot-01 branch protection`

## 5. Estrategia de verificación

- **Checker canónico:** `python scripts/check_dod.py all`.
- **Comandos observables incluidos:** `ruff check .`, `mypy engine/`, `pytest engine/ -q`, `pytest backend/ -q`, frontend ESLint con cero warnings, `npx tsc --noEmit`, `npx vitest run` y `npm run build`.
- **Pruebas negativas del harness:** antes del cierre se demostrará que un comando no cero y una suite ausente hacen fallar el checker; no se dejarán mutaciones deliberadas en el commit.
- **Golden:** no aplica; SHOT-01 no toca fórmulas. No se ejecutará `make goldgen` ni se modificará ningún snapshot.
- **Cierre:** solo exit code 0 real del checker, CI remota verde, branch protection confirmada y push de `shot-01`. No merge.

## 6. Riesgos y decisiones pendientes

- `[PENDIENTE-DECISIÓN — BLOQUEANTE]` `docs/PRD/PRD-00.md` declara que la lista cerrada de dependencias está en §10, pero el archivo real termina en §5. `PLAN_SHOTS.md` sí nombra Python tooling, Django 5.1, DRF 3.15, drf-spectacular, pytest-django, React 18, Vite, Tailwind CSS, TypeScript 5.6 y Vitest, pero no fija el conjunto/versiones compatibles de paquetes auxiliares (por ejemplo, adapter de Vite para React, ESLint, DOM de tests y PostCSS). Antes de Fase 2, el owner debe aportar/restaurar §10 o aprobar explícitamente el manifiesto/lockfile exacto; el builder no lo inventará.
- `[PENDIENTE-DECISIÓN — BLOQUEANTE PARA CIERRE]` La estación no tiene GitHub CLI instalado y el estado real de branch protection no pudo consultarse por esa vía. Debe confirmarse si la activación se hará con una sesión GitHub autenticada disponible o manualmente por el owner; documentación sin activación no satisface el gate.
- **Entorno local:** Python es 3.14.4 y Node 24.14.0, mientras la CI existente usa Python 3.12 y Node 20; Ruff, Mypy y Pytest no están instalados globalmente. Se usará un entorno local aislado y las versiones CI bloqueadas, sin depender de instalaciones globales.
- **Riesgo de falso verde actual:** `scripts/check_dod.py` usa retornos ignorados y omite herramientas/suites ausentes; `scripts/check_dod.sh` contiene `|| true`; la CI actual no tiene job de build. El endurecimiento fail-closed es parte inseparable de SHOT-01.
- **Riesgo de alcance:** el repositorio contiene documentos y variables de shots futuros. Se conservarán intactos y no se convertirán en implementación anticipada.
