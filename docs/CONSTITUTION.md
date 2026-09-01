# DEKOPEN — CONSTITUCIÓN DEL BUILDER (v1.2)
**Estado:** Inmutable / Norma Suprema del Repositorio  
**Aplicabilidad:** Absoluta sobre todo agente, desarrollador y commit.

---

```
# DEKOPEN — CONSTITUCIÓN DEL BUILDER (no negociable, lee antes de escribir código)

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
   Ningún PR se completa con discrepancia > 0.00 mm.
8. Un cambio de fórmula es un PR con caso de oro, no un ajuste de prompt.
9. Monolito modular (apps Django por dominio). Prohibido microservicios.
10. Error del inspector = frase de taller + botón de corrección. Nunca un log crudo.
11. Enviar a cliente, mandar a fábrica, comprar material: requieren clic humano
    explícito. Estados lo modelan; nada automático.
12. project_versions congela números en cada emisión. Cambiar precio enviado = revisión nueva.
13. Webhooks y pagos: idempotencia obligatoria (UNIQUE provider+event_id,
    provider_payment_id). Un retry jamás cobra dos veces.
14. Código/comentarios/DB en inglés. UI solo vía claves i18n ES-CL.
15. Dependencias: SOLO la lista cerrada (PRD-00 §6). Nuevo dep = decisión explícita del owner.
16. Archivos: Supabase Storage con path org_id/… y URLs firmadas con expiración.
17. Prohibido inventar U_w / R_w. Solo desde ficha certificada o no se muestra.
18. offcut_inventory: schema existe, producción prohibida hasta Fase 4.
19. Cada PR cierra con: pytest ✓ · vitest ✓ · ruff ✓ · mypy engine ✓ · checklist DoD.
20. Si el spec tiene un hueco: DETENTE y añade [PENDIENTE-DECISIÓN]. No rellenes con supuestos.
21. AUDITORÍA DE PRECIOS: todo cambio de precio genera fila en price_audit_logs antes de aplicarse.
22. GENERACIÓN AUTOMATIZADA DE GOLDEN SNAPSHOTS: Los fixtures golden de cálculo (e.g.
    golden_example.json) se generan mediante /engine y nunca se editan a mano. Cualquier
    cambio en fórmulas exige regenerar con `make goldgen` e incluir el diff explícito en el PR.
```
