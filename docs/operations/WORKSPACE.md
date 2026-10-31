# Mantenimiento del workspace

El repositorio guarda solo lo actual: código, pruebas, fixtures, migraciones,
CI y los documentos que describen el producto vigente. La navegación de entrada
está en `AGENTS.md` y `docs/wiki/index.md`; el plan vigente en
`docs/dekopen3/PLAN.md`.

La limpieza del 31-10-2026 retiró del checkout la cola v1 (`docs/cola/`), los
informes de aceptación y capturas por fase (`docs/redesign/`), la investigación
en bruto (`docs/research/`), informes fechados, evals antiguas y los scripts de
verificación de una sola vez: unos 3.400 archivos y 460 MB. Todo se recupera
desde Git en `588e6332`; la síntesis útil sigue en la wiki.

## Qué conservar

- Motor, goldens, tests, API generada, migraciones, seed, CI y dependencias.
- Constitución, PRD, decisiones, wiki de producto y fuentes del dueño.
- Guía de revisión, ACTIVACION, recuperación y operación de IA.
- Fixtures usados como entrada por herramientas, incluso cuando son PNG o PDF.
- `.env`, bases/volúmenes, perfiles de navegador y archivos de propiedad del stack.

## Estado local de esta estación Windows

Inventariado el 12-10-2026; estas rutas ignoradas existen solo en esta estación:

| Ruta | Uso que impide borrarla como temporal |
|---|---|
| `.run/brave/` | Seis perfiles, sesiones, factor MFA local y acceso al portal del cliente |
| `.run/prepare_brave.py`, `.run/iniciar_brave_dekopen.py`, `.run/brave-login.html` | Preparación y reapertura de las sesiones |
| `.run/Abrir-DEKOPEN.ps1`, `.run/Abrir-cliente-DEKOPEN.ps1`, `.run/Crear-accesos-DEKOPEN.ps1` | Accesos del escritorio y su mantenimiento |
| `.run/p20-review-refs.json` | Referencia que consume el preparador de Brave |
| `.run/review/` | Propiedad y configuración de Supabase REVIEW, incluida una plantilla montada en Docker |
| `.run/cola-stack/`, `.run/bin/` | Configuración y wrapper de Supabase PRIMARY |
| `.run/wsl-tests/` | Disco de una distribución WSL registrada; estar detenida no lo vuelve descartable |
| `.run/linux-packages/`, `.run/evalbin/` | Dependencias y wrapper de la alternativa Linux local |
| `.run/p20_static.py`, `frontend/dist/` | Servidor de revisión anterior que seguía activo durante el inventario |
| `.venv/`, `frontend/node_modules/`, `node_modules/` | Dependencias locales instaladas |

También se conservan estados de fixture leídos por scripts versionados y copias
de seguridad locales. Un clon nuevo prepara su stack con `scripts/start_local.ps1`;
estos archivos privados no se copian ni se incorporan a Git.

REVIEW sirve el producto en `http://127.0.0.1:5179` y Mailpit en
`http://127.0.0.1:25364`. Usa API, worker y web propios `framedex-review`.
El acceso del escritorio «DEKOPEN - Iniciar y abrir todos los roles» depende de
los launchers de la tabla. Las credenciales se leen en memoria desde `.env`.

## Regla para futuros encargos

1. Guarde capturas, trazas, logs, informes de aceptación y copias de checkout
   en `.run/`; no se versionan. El PR describe la verificación.
2. Conserve entradas de regresión en carpetas de fixtures.
3. Antes de borrar, resuelva las rutas, compruebe lectores y montajes, y proteja
   bases, secretos, perfiles y propiedad. No aplique limpieza global a `.run/`
   ni podas generales de Docker.
4. Al retirar un documento, quite o reescriba sus enlaces y deje el SHA
   recuperable en la wiki. No reescriba el historial de Git.

## Búsqueda por tarea

`AGENTS.md` y las rutas por dominio de [la wiki](../wiki/index.md) dirigen al
código, sus pruebas y la especificación pertinente. La historia retirada está
en Git y nunca es un mandato nuevo.

`.rgignore` omite de búsquedas generales el cliente/OpenAPI generado, goldens
JSON, payloads de evals y el log cronológico. Conserva visibles código,
pruebas, migraciones, PRD, wiki de dominio y fixtures. Son exclusiones de búsqueda;
no cambian el seguimiento de Git ni las entradas de generadores o tests.

Empiece con `rg --files <carpeta-del-dominio>` y búsquedas de símbolo/error
dentro de esas carpetas. Para lo excluido, abra un archivo conocido directamente
o use `rg --no-ignore <patrón> <carpeta-específica>`. Evite un `--no-ignore`
global que vuelva a recorrer dependencias, sesiones o datos privados.

La receta actual de stack está en
[testing-framedex](../../.agents/skills/testing-framedex/SKILL.md), basada en
`review_stack.py`, `dev_fixture.py` y la guía de revisión. La receta anterior
se conserva en un enlace a Git; sus rutas de otra estación, defectos de fases
antiguas y recuperación manual de Auth no son el procedimiento vigente.
