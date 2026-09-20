# DEKOPEN — mapa operativo del repositorio

Este archivo es una guía breve de navegación. La autoridad normativa del producto y del
sistema está en [`docs/CONSTITUTION.md`](docs/CONSTITUTION.md); este mapa no la replica.

## Autoridad y contexto

Lee solo lo necesario, en este orden:

1. `AGENTS.md` para ubicar la tarea.
2. `docs/CONSTITUTION.md` para invariantes y materialidad.
3. `docs/PRD/PLAN_SHOTS.md` para secuencia, alcance y gates.
4. `docs/plans/PLAN_SHOT-XX.md` si existe un shot activo o cerrado cuyo contrato afecte la tarea.
5. Los PRD y archivos de código directamente afectados.

`docs/PRD/*.md` contiene los contratos de dominio activos. `docs/AGENT_OPERATING_MODEL.md`
contiene disciplina operativa no normativa. `docs/archive/**` y `DEKOPEN_BIBLIA_*.md` son
registros o vistas históricas no autoritativas; no se cargan por defecto.

## Invariantes que no se pueden inferir de forma segura

- Todas las dimensiones, cantidades y valores monetarios usan `Decimal`; `/engine` es puro,
  determinista y sin I/O.
- La tolerancia matemática exigida es `0.00 mm`. Los números de salida provienen de `/engine`
  o de un campo humano explícito.
- Las tablas de negocio están aisladas por PostgreSQL RLS y `current_user_org_ids()`.
- Las escrituras de IA se auditan antes de aplicar el diff y los cambios de precio antes de
  aplicarse; los pagos y webhooks son idempotentes.
- La UI usa tokens semánticos CSS; no se añaden hexadecimales crudos.
- Golden es de solo lectura por defecto. `make goldgen` requiere cambio de fórmula autorizado.

## Autonomía y límites

Resuelve de forma autónoma decisiones reversibles y no materiales, corrección de fallos,
formateo, pruebas y refactorizaciones que preserven contratos observables. Planificar es útil
cuando la tarea tiene decisiones materiales o varias superficies; no es una aprobación humana
obligatoria para cada cambio reversible.

Detente solo ante una contradicción material bajo la Regla 0, un vacío material bajo la Regla
20 (inserta `[PENDIENTE-DECISIÓN]`) o una acción irreversible sin autorización. Si una regla
del repositorio te detiene, informa por separado `RULE SAYS` y `AGENT INTERPRETS`.

El árbol canónico tiene un solo escritor. Usa una rama o worktree aislado cuando exista una
razón real para separar trabajo; integra los cambios en la raíz.

## Verificación y cierre

Selecciona las pruebas por la superficie afectada y conserva evidencia ligada al SHA: cambios
documentales requieren consistencia/formato; frontend, engine, DB/RLS, documentos y navegador
requieren sus gates afectados. Una modificación más amplia o incertidumbre concreta justifica
subir el nivel de verificación.

El Gauntlet canónico (`python scripts/check_dod.py all`) es obligatorio para el head material
final de implementación de un SHOT. No se repite automáticamente por commits documentales,
por un merge limpio ni por cambios contenidos cuya evidencia SHA-bound siga vigente. Los cuatro
checks protegidos de CI son el veredicto independiente de integración.

## Comandos de referencia

```text
python scripts/check_dod.py all       # Gauntlet de cierre de shot
python scripts/new_shot.py SHOT-XX    # scaffold mínimo de plan
pytest engine/ -q                     # suite del motor
ruff check .                          # lint Python
cd frontend; npm test                 # suite frontend
```

No se cambia el comportamiento de producto, las fórmulas, Golden, RLS, auditoría o contratos
para hacer pasar un checker. Los PR protegidos se fusionan solo con sus checks requeridos en
verde; después se verifica el CI de `main`.
