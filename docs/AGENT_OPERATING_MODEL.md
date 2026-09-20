# DEKOPEN — referencia de verificación

> **No normativa.** [AGENTS.md](../AGENTS.md) es el mapa. La [Regla 19](./CONSTITUTION.md)
> define evidencia, cierre y reuso; este archivo solo ayuda a elegir comprobaciones.

Cada incremento queda completo dentro de su alcance: sin persistencia simulada, mocks en
producción ni números inventados. No se adelantan shots para completar funciones diferidas.

## Selección de comprobaciones

Ejecuta desde la raíz con dependencias instaladas; para frontend, desde `frontend/`.
Los resultados se registran con SHA, comando, resultado y superficie cubierta.

| Delta | Comprobaciones pertinentes |
|---|---|
| Documentación sin cambio de comportamiento | Diff, consistencia, enlaces y formato de archivos modificados |
| Scripts de desarrollo | Casos de éxito/error/no sobrescritura, lint y pruebas directas de la herramienta |
| Frontend | Componentes afectados, lint/typecheck, build y E2E del flujo afectado |
| Engine/matemática | Regresión, suite engine, Golden `--check`, mutaciones de fórmulas/contratos afectados |
| DB/RLS/migración | Migraciones, pgTAP, aislamiento e integración del backend afectado |
| Documentos de salida | Contratos PDF/XLSX e integración afectada |
| Cambio transversal/cierre material de shot | Gauntlet canónico según Regla 19 |

Un cambio de contrato en Markdown se evalúa por el comportamiento esperado que cambia.
Una revisión limpia previa no necesita repetirse salvo nuevo delta material o preocupación
concreta; un hallazgo necesita corrección, regresión y gates afectados.

## Comandos

```text
pytest engine/ -q
python -m engine.scripts.regenerate_golden --check
python scripts/check_dod.py lint
python scripts/check_dod.py typecheck
python scripts/check_dod.py database
python scripts/check_dod.py all
```

En `frontend/`: `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build`.
Consulta `frontend/package.json` y los tests existentes para elegir el E2E.
Los gates completos están implementados en `scripts/check_dod.py`; `make dod` ejecuta `all`.

CI protegido exige **Lint & Typecheck**, **Test Suite**, **Frontend Build** y **Database Gate**.
El informe de cierre identifica el head probado, PR, merge, CI de `main` y evidencia reutilizada.
Ni el relato del agente ni un segundo agente sustituyen al checker determinista.
