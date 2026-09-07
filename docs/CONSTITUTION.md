# DEKOPEN — CONSTITUCIÓN DEL BUILDER (v1.3 MASTER)
**Estado:** Inmutable / Norma Suprema del Repositorio
**Aplicabilidad:** Absoluta sobre todo agente, desarrollador, commit y shot.
**Autoridad Única:** Esta es la ÚNICA Constitución del repositorio. No existen copias secundarias.
**Enmiendas:** The Constitution may only be amended by an explicit Owner-approved normative change; while active, it has highest precedence.

---

```
# DEKOPEN — CONSTITUCIÓN DEL BUILDER (23 Reglas Supremas, lee antes de escribir código)

0. REGLA CERO (CERO CONTRADICCIONES CONOCIDAS):
   Si durante cualquier SHOT se detecta una contradicción normativa material entre Constitución,
   PRD, Golden Case, esquema, código, fixture o gate, el SHOT SE DETIENE DE INMEDIATO.
   Se corrige primero la fuente normativa, se registra la decisión formal y se continúa.
   PROHIBIDO elegir silenciosamente una interpretación en temas materiales.
   Una contradicción es MATERIAL si puede modificar: dimensiones, matemática, peso, dinero,
   seguridad, RLS, permisos, auditoría, datos certificados, hardware, stock, purchase list,
   workshop cut plan, documentos emitidos, hashes, API contracts, persistence schemas,
   externally observable deterministic output, production readiness, irreversible action o
   contractual workflow state. Esto incluye algoritmos cuya elección cambie el resultado observable
   (ej: el tie-break BFD es material si cambia el plan de corte; debe congelarse/testearse).
   Para contradicciones no materiales (wording, layout, naming interno no contractual,
   ergonomía visual o preferencias de componentes reversibles), el agente puede resolver
   aplicando mejores prácticas de ingeniería y registrando el rationale en el plan del shot sin detenerlo.
   Principio de precedencia temporal: GLOBAL FLEXIBILITY DOES NOT RETROACTIVELY DESTABILIZE AN
   ACTIVE SHOT CONTRACT. Si una decisión ya quedó congelada en un PLAN_SHOT activo mediante PD aprobada
   (ej: S07 como modal en SHOT-07 bajo PD-07-27 — S07), sigue siendo contrato de ese shot y no se altera retroactivamente.

1. NÚMEROS: si un número aparece en un documento de salida, salió de /engine o de un
   campo editado por humano. JAMÁS del texto libre de un LLM.
2. engine/ es puro: sin I/O, sin Django, sin HTTP. Testeable con `pytest engine/`.
3. Decimal para todo mm y dinero. Prohibido float. CLP sin decimales; USD con 2 decimales.
4. Toda tabla de negocio lleva org_id + política RLS + test de aislamiento. Un tenant
   jamás lee precios de otro. Catálogos globales legibles por todos los usuarios.
5. Escritura de IA → fila en ai_audit_logs ANTES de aplicar el diff. Sin excepciones.
6. Parámetros de serie viven en profile_systems (desde ficha). Cero hardcoded en UI.
   Cambiar una fórmula = PR con caso de oro nuevo. Nunca "ajuste de prompt".
   Precedencia de pesos: profile_articles.weight_kg_m prevalece sobre SystemParams.pvc_weight_kg_m.
7. Casos de Oro (Gold Cases G1–G12 excepto G10 en Fase 1.5; G-Pro1 con sign-off físico).
   Ningún PR se completa con discrepancia > 0.00 mm en los casos exigidos por el Gate.
8. Un cambio de fórmula es un PR con caso de oro, no un ajuste de prompt.
9. ARQUITECTURA: DEFAULT ARCHITECTURE = MODULAR MONOLITH (apps Django por dominio, pure engine y Vite SPA).
   Una extracción de servicio NO ocurre por moda, por preferencia del agente ni por "arquitectura enterprise" abstracta.
   Puede ocurrir únicamente mediante un Architecture Decision Record (ADR) formal cuando exista evidencia material de:
   independent scaling, security/fault isolation, specialized runtime, workload independence o substantial operational benefit.
   Si la extracción constituye un cambio arquitectónico mayor: OWNER approval obligatoria.
   Actualmente NO se autoriza ningún microservicio (esto es gobernanza futura, no implementación presente).
10. Error del inspector = frase de taller + botón de corrección. Nunca un log crudo.
11. Enviar a cliente, mandar a fábrica, comprar material: requieren clic humano
    explícito. Estados lo modelan; nada automático.
12. project_versions congela números en cada emisión. Cambiar precio enviado = revisión nueva.
13. Webhooks y pagos: idempotencia obligatoria (UNIQUE provider+event_id,
    provider_payment_id). Un retry jamás cobra dos veces.
14. Código/comentarios/DB en inglés. UI solo vía claves i18n ES-CL.
15. DEPENDENCIAS (POLÍTICA DE TRES NIVELES): Approved Baseline Dependencies (PRD-00).
    - TIER A (DEV/TOOLING LOW RISK): El agente puede añadirla mediante PR sin aprobación Owner si:
      licencia compatible con la política de distribución, seguridad y compliance del proyecto (ej: MIT, Apache-2.0, BSD, ISC), mantenimiento razonable, security scan sin issue crítico,
      sin duplicación injustificada, lockfile reproducible y tests/gauntlet verdes.
    - TIER B (ORDINARY RUNTIME DEPENDENCY): El agente puede añadirla mediante PR SIN aprobación Owner si:
      no cambia la arquitectura principal, no crea un proveedor externo crítico, no altera DB/auth/infra,
      cuenta con rationale técnico documentado, revisión de licencia/seguridad/mantenimiento, impacto en bundle
      y runtime medido, lockfile reproducible y tests verdes (ej: librería UI auxiliar, parser, utility library,
      paquete helper o serializador menor; NO convertir cada paquete npm/pip de producción en decisión del fundador).
    - TIER C (STRATEGIC / CRITICAL DEPENDENCY): Requiere aprobación explícita del OWNER:
      framework principal, database, ORM principal, auth platform, payment provider, cloud provider,
      broker/queue architecture, storage architecture, observability platform, motor mayor 3D/CAD si define
      materialmente la arquitectura, servicio externo crítico de seguridad o cualquier dependencia que altere
      materialmente la arquitectura de despliegue. Siempre prohibida la duplicación absurda sin rationale.
16. Archivos: Supabase Storage con path org_id/… y URLs firmadas con expiración.
17. Prohibido inventar U_w / R_w. Solo desde ficha certificada o no se muestra.
18. offcut_inventory: schema existe, producción prohibida hasta Fase 4.
19. Cada PR cierra con: pytest ✓ · vitest ✓ · ruff ✓ · mypy engine ✓ · checklist DoD.
20. TRATAMIENTO DE GAPS:
    - MATERIAL GAP: Si la especificación omite o deja indefinido un aspecto que resulte MATERIAL according to Rule 0:
      DETENTE de inmediato y añade `[PENDIENTE-DECISIÓN]`. Rule 0 es la ÚNICA autoridad de materialidad.
      PROHIBIDO rellenar vacíos materiales con supuestos de la IA.
    - NON-MATERIAL GAP: Si el vacío NO es material según Rule 0 y es técnicamente reversible:
      la IA decide profesionalmente aplicando las mejores prácticas de ingeniería y documenta el rationale
      en el plan del shot cuando sea útil (ej: ergonomía y composición interna de componentes de UI, layout,
      naming interno o tooling menor).
21. AUDITORÍA DE PRECIOS: todo cambio de precio genera fila en price_audit_logs antes de aplicarse.
22. GENERACIÓN AUTOMATIZADA DE GOLDEN SNAPSHOTS: Los fixtures golden de cálculo (e.g.
    golden_example.json) se generan mediante /engine y nunca se editan a mano. Cualquier
    cambio en fórmulas exige regenerar con `make goldgen` e incluir el diff explícito en el PR.
```
