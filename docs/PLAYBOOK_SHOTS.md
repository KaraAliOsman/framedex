# PLAYBOOK DE SHOTS

> Guía breve de ejecución. La Constitución, los PRD activos y el roadmap son la autoridad; este
> archivo no los duplica.

## Antes de cambiar código

- Lee `AGENTS.md`, `docs/CONSTITUTION.md`, `docs/PRD/PLAN_SHOTS.md`, el plan del shot si
  aplica y los archivos afectados.
- Escribe o actualiza `docs/plans/PLAN_SHOT-XX.md` cuando la tarea tenga decisiones
  materiales, varias superficies o un gate de shot que registrar. Un cambio reversible y
  contenido puede avanzar sin un plan separado.
- Identifica el contrato observable, la superficie de prueba y cualquier `[PENDIENTE-DECISIÓN]`.

## Durante la implementación

- Mantén el alcance del shot y la calidad de producción dentro de ese alcance.
- Usa pruebas focalizadas y el checker determinista; corrige los fallos sin debilitar sus
  aserciones.
- Mantén Golden en modo lectura. Solo una modificación autorizada de fórmula permite
  `make goldgen`.
- Registra en el plan la evidencia relevante junto con el SHA y la superficie cubierta.

## Verificación

Selecciona los gates por el delta:

| Delta | Comprobación mínima |
|---|---|
| Documentación o harness | consistencia, formato y la herramienta modificada |
| Frontend | tests afectados, lint/typecheck, build y E2E afectado |
| Engine o matemática | regresión, suite engine, Golden `--check` y mutaciones afectadas |
| DB/RLS | migraciones, pgTAP, RLS y backend afectado |
| Transversal o cierre material de shot | gates afectados y Gauntlet canónico |

El Gauntlet (`python scripts/check_dod.py all`) es obligatorio para el head material final de
implementación de un SHOT. No se repite por un commit documental, un merge limpio o una
corrección contenida cuya evidencia SHA-bound siga vigente. Los cuatro checks protegidos de CI
son la decisión independiente de integración.

## Cierre

Verifica que el head del PR es el SHA probado, espera CI protegido verde, fusiona mediante PR y
comprueba el CI de `main`. Una revisión adversarial completa basta; solo un cambio material
nuevo o una preocupación concreta exige repetirla.

Para iniciar un scaffold mínimo usa:

```text
python scripts/new_shot.py SHOT-XX
```

El scaffold no impone aprobación humana, un prompt universal ni un Gauntlet para cada commit.
