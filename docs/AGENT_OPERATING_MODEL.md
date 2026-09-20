# DEKOPEN — modelo operativo del agente

> **Estado:** guía operativa no normativa. La autoridad está en
> [`docs/CONSTITUTION.md`](./CONSTITUTION.md) y [`docs/PRD/PLAN_SHOTS.md`](./PRD/PLAN_SHOTS.md).

Este documento explica cómo aplicar los contratos del repositorio con el menor ruido posible.
No añade invariantes de producto ni convierte una preferencia de implementación en autoridad.

## 1. Alcance y calidad

Cada incremento debe quedar completo y mantenible dentro de su alcance autorizado. No se acepta:

- persistencia simulada, endpoints sin contrato o estados de UI desconectados;
- números técnicos inventados, placeholders ocultos o fallbacks que cambien resultados;
- mocks, stubs o excepciones tragadas en rutas de producción;
- bypass de RLS, auditoría, idempotencia, tipos Decimal o controles de seguridad;
- tests vacíos, gates debilitados o fixtures alterados para ocultar un fallo;
- implementación anticipada de shots futuros.

`DEMO_60` es un fixture sintético y nunca una autoridad de fabricante. Los documentos, cotizaciones
y planes de corte deben conservar la autoridad determinista de `/engine` y de los catálogos
certificados.

## 2. Contexto justo a tiempo

La conversación no es autoridad persistente. Carga `AGENTS.md`, Constitución, roadmap, plan
del shot si aplica, PRD afectados y código directamente relacionado. No cargues por defecto
todas las PRD, biblias concatenadas ni `docs/archive/**`.

- `docs/archive/**`: histórico no normativo.
- `DEKOPEN_BIBLIA_*.md`: vista compilada no normativa.
- `docs/PRD/*.md`: contratos activos de dominio.
- `docs/plans/**`: decisiones y evidencia del shot correspondiente.

## 3. Autonomía y detención

Actúa sin pedir una aprobación adicional para decisiones reversibles y no materiales, pruebas,
formateo, correcciones y refactorizaciones que preserven el contrato observable. Un plan es
obligatorio solo cuando una tarea necesita registrar decisiones materiales o coordinar varias
superficies; no es un ritual para cada cambio.

Detente únicamente ante:

1. una contradicción material bajo la Regla 0;
2. un vacío material bajo la Regla 20, que se marca con `[PENDIENTE-DECISIÓN]`;
3. una acción irreversible sin autorización.

Antes de escalar una decisión, termina el análisis y las comprobaciones reversibles. Si una
regla detiene el trabajo, informa `RULE SAYS` con su texto y `AGENT INTERPRETS` con el efecto
técnico.

## 4. Maker, checker y escritor único

El agente que modifica el árbol puede ejecutar los checkers deterministas y reparar sus fallos.
No puede debilitar aserciones, cambiar `scripts/check_dod.py`, silenciar warnings ni editar
Golden para fabricar un verde. El CI protegido es el veredicto independiente de integración.

El árbol canónico tiene un solo escritor. Un worktree o rama aislada se usa solo cuando separa
trabajo real; la raíz integra y resuelve cualquier conflicto.

## 5. Verificación por superficie

La evidencia se liga al SHA, gate, resultado y superficie cubierta. Un commit posterior no
invalida automáticamente evidencia previa: se vuelven a ejecutar las pruebas que el delta pueda
afectar.

| Superficie | Verificación inicial | Evidencia no invalidada automáticamente |
|---|---|---|
| Documentación | consistencia, formato, enlaces y herramienta modificada | engine, Golden, DB/RLS, backend, frontend y navegador |
| Frontend | tests afectados, lint/typecheck, build y E2E del flujo | engine y migraciones no tocados |
| Engine o matemática | regresión focalizada, suite engine, Golden `--check`, mutaciones | superficies no relacionadas |
| DB/RLS/migraciones | migraciones, pgTAP, RLS y backend afectado | superficies visuales no relacionadas |
| Documentos | contratos de PDF/XLSX y ruta de integración afectada | superficies no relacionadas |
| Cambio material transversal | gates afectados y Gauntlet canónico | — |

Amplía la verificación si el delta es más amplio, un gate falla o queda incertidumbre concreta.
No repitas un gate costoso cuando no resuelve ninguna incertidumbre nueva.

## 6. Cierre de un shot

El Gauntlet canónico es `python scripts/check_dod.py all` y es obligatorio para el head material
final de implementación de un SHOT. Los cambios documentales de cierre, un merge limpio o una
corrección contenida no lo reactivan por sí solos cuando la evidencia SHA-bound sigue cubriendo
la superficie.

La disciplina de cierre es:

1. ejecutar pruebas focalizadas mientras se implementa;
2. corregir hallazgos con una regresión y los gates afectados;
3. obtener el Gauntlet en el head material final del shot;
4. obtener los cuatro checks protegidos;
5. fusionar el head probado y verificar el CI de `main`.

Una revisión adversarial completa del head material final basta. Solo un cambio material nuevo,
una preocupación concreta o un contrato afectado justifican otra revisión completa.

## 7. Golden y contratos de IA

Golden es de solo lectura y se valida con `--check`. `make goldgen` exige una modificación
material de fórmula autorizada, actualización del PRD fuente y diff revisado.

Los PRD describen capacidades, datos, seguridad, auditoría y resultados observables. Las rutas
de IA son dinámicas; proveedor, modelo, prompt y método interno son configuración operativa o
detalles de implementación. El contrato T8 exige independencia, arbitraje determinista y
auditoría, sin congelar nombres de proveedores.
