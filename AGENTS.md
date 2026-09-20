# DEKOPEN — mapa del repositorio

## Autoridad y navegación

Precedencia: [Constitución](docs/CONSTITUTION.md) → [roadmap y gates](docs/PRD/PLAN_SHOTS.md)
→ PRD de dominio en `docs/PRD/` → decisiones del plan de shot. El orden de lectura se adapta
a la tarea: abre Constitución, gate y plan cuando afectes sus contratos; después, solo los PRD
y código necesarios. No cargues todas las PRD ni compilaciones por defecto.

- `docs/PRD-*.md` son punteros a las fuentes activas.
- `docs/plans/PLAN_SHOT-XX.md` conserva decisiones aprobadas y evidencia. La flexibilidad futura
  no reabre decisiones congeladas de shots activos/cerrados; consulta las que afecten al cambio.
- `docs/QUALITY_SCORE.md` es un mapa informativo de lo probado, no un contrato.
- `docs/AGENT_OPERATING_MODEL.md` es referencia de comandos, no otra política.
- `docs/archive/**`, `docs/audits/**` y `DEKOPEN_BIBLIA_*.md` son históricos no normativos;
  sus instrucciones de procedimiento no gobiernan trabajo nuevo.
- `docs/PRD/STACK_APLICACIONES_Y_SERVICIOS.md` clasifica arquitectura, baseline y beneficios;
  no convierte selecciones temporales en contratos nuevos.

## Invariantes locales

- `/engine` es puro, sin I/O; dimensiones y dinero usan `Decimal`, con tolerancia `0.00 mm`.
- Los números de salida provienen de `/engine` o de campos humanos explícitos.
- RLS PostgreSQL y `current_user_org_ids()` aíslan tenants; auditoría de IA/precios precede
  a escrituras. Emisión, fábrica y compras requieren la acción humana del contrato.
- `DEMO_60` es sintético, nunca ficha certificada ni autoridad comercial.
- UI mediante i18n ES-CL y tokens semánticos CSS; Golden es solo lectura por defecto.
  Regenerarlo requiere cambio de fórmula autorizado y diff auditado (Regla 22).

## Autonomía y finalización

Resuelve decisiones reversibles no materiales sin aprobación adicional. Usa planes cuando
ayuden a registrar alcance, dependencias o decisiones; no son un ritual de aprobación.
Ante contradicción o vacío material, aplica Reglas 0/20 y registra `[PENDIENTE-DECISIÓN]`.
Si una regla detiene el trabajo, cita archivo/texto (`RULE SAYS`) y efecto (`AGENT INTERPRETS`).
Las acciones irreversibles necesitan autorización; no se elude PR ni CI protegido.

Un escritor por worktree. El trabajo genuinamente independiente puede usar otros worktrees
y ramas aislados; los cambios integrados conservan contratos y se verifican por su delta.

La **Regla 19** es la política única de verificación: pruebas por superficie, evidencia ligada
al SHA, Gauntlet al cierre material de un shot y CI protegido como veredicto de integración.
Finaliza al satisfacer los gates aplicables y registrar evidencia vigente; no repitas pruebas
por un commit documental o merge limpio. No debilites checkers, tests ni protección.

## Comandos importantes

```text
python scripts/check_dod.py all                 # Gauntlet de cierre material de SHOT
python scripts/check_dod.py lint                # lint y guards constitucionales
python -m engine.scripts.regenerate_golden --check
python scripts/new_shot.py SHOT-XX              # scaffold opcional; no inicia el shot
```

Los comandos por superficie están en [el modelo operativo](docs/AGENT_OPERATING_MODEL.md).
