# Mantenimiento del workspace

La limpieza del 12-10-2026 conserva el código y las autoridades del producto.
La navegación de entrada está en `AGENTS.md` y `docs/wiki/index.md`; el estado
vigente resumido está en `docs/wiki/state/current-reality.md`.

Se retiraron 6.979 archivos históricos del checkout y 34.146 temporales locales:
3,86 GiB en conjunto. Los primeros se recuperan desde Git; los segundos, desde
la Papelera de Windows. La medición corresponde al workspace, sin vaciar la
Papelera ni reescribir el historial. El recibo local está en
`.run/cleanup-2026-10-12.json`.

## Qué conservar

- Motor, goldens, tests, API generada, migraciones, seed, CI y archivos de dependencia.
- Constitución, PRD, decisiones, fuentes, adjuntos de la cola y wiki. La cola
  terminada conserva contratos y PR/SHA; no se vuelve a ejecutar como arranque.
- Guía de revisión, ACTIVACION, aceptación final y sus recibos/evidencia.
- Fixtures usados como entrada por herramientas, incluso cuando son PNG o PDF.
- `.env`, bases/volúmenes, perfiles de navegador y archivos de propiedad del stack.

Las capturas de rondas anteriores se consultan desde el commit anterior a la
limpieza, enlazado en [el mapa de evidencia](../redesign/captures/README.md).
Los informes históricos conservan sus resultados y límites. La wiki cronológica
es append-only; las decisiones anteriores no se borran silenciosamente.

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

1. Guarde capturas exploratorias, trazas, logs y copias de checkout en `.run/`.
2. Seleccione evidencia que explique el cambio: informe, fuente/ref, límites y
   las imágenes necesarias. Los PNG/PDF/HTML nuevos de `docs/redesign/captures/`
   están ignorados; use `git add -f` únicamente para esa selección revisada.
3. Conserve entradas de regresión en carpetas de fixtures y el informe de la
   última aceptación. Retire duplicados de cobertura y registros parciales si
   ya existe el informe completo.
4. Antes de borrar, resuelva las rutas, compruebe lectores y montajes, y proteja
   bases, secretos, perfiles y propiedad. No aplique limpieza global a `.run/`
   ni podas generales de Docker. Un borrado de una distribución WSL requiere
   tratar también su registro y sus datos; esta limpieza la conserva.
5. Actualice los enlaces a archivos retirados hacia un SHA recuperable y deje
   el resultado medido en la wiki. No reescriba el historial de Git para reducir
   el tamaño: la reducción corresponde al checkout y a temporales locales.

`.rgignore` omite los payloads de capturas en búsquedas generales. Para leerlos,
abra la ruta concreta o use `rg --no-ignore docs/redesign/captures/`.
