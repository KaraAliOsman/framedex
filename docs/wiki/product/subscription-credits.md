---
type: synthesis
status: active
updated: 2026-10-31
volatility: medium
verified_ref: 6f78e3299d93816991fb7c2fe2a2044458fc5e7a
sources:
  - docs/wiki/sources/owner-credits-and-grokbot-2026-10-18.md
  - docs/PRD/PRD-03.md
  - docs/dekopen3/PLAN.md
---

# Suscripción SaaS, créditos y límites de IA

## P16 · Personas, roles y funciones por plan (31-10-2026)

Hecho verificado en código: `private.plan_terms` (migración
`20270217000000_plan_seats_and_features.sql`) es la única tabla de términos y la
base los aplica donde se concede acceso.

| Plan | Personas | Roles que se invitan | Funciones además de la base |
| --- | --- | --- | --- |
| Taller (`STARTER`) | 1 | — | ninguna; sin IA |
| Prueba y Pro | 3 | socio, oficina, taller | 3D para el cliente, pedidos de compra, CNC |
| Empresa y Empresa 2× | sin límite | todos | + roles, estaciones, terreno, subagentes |

- Un asiento lo ocupa una persona activa o una invitación vigente. Se aplica
  al invitar, al aceptar (el plan pudo bajar entretanto) y al reactivar.
- Bajar de plan nunca saca a nadie: solo impide nuevos asientos y nuevos
  roles. Un rol que la persona ya tenía se conserva.
- El servidor bloquea crear, enviar y mandar por correo pedidos a proveedores
  sin Pro (`plan_feature_required`); necesidades, recepción y anulación siguen.
- El asistente solo delega en subasistentes con Empresa; el portal muestra el
  3D solo si el plan del emisor lo incluye (`client_3d`).
- Interfaz: «Equipo» en Ajustes. En Taller explica que una persona hace todo,
  sin roles ni invitación; en Pro se invita por lo que hará la persona
  (socio, oficina, taller) sin pantalla de roles; en Empresa, los roles
  completos. La página de planes compara los tres y marca el actual.
- Endpoint `GET /api/v1/organization/plan/` para cualquier persona de la
  empresa: plan, asientos usados y libres, roles, funciones e IA.

## Dirección del dueño y propuesta pendiente

La [aclaración reciente](../sources/owner-credits-and-grokbot-2026-10-18.md)
confirma base manual sin IA y MiMo común a todos los planes con IA hasta cambio
expreso suyo. La diferencia principal es capacidad de consumo; pueden existir
extras profesionales concretos. DeepSeek es un candidato posterior sin validar
o configurar. Los importes 30/49/99/149 no son una oferta autorizada.

El contrato propuesto para Claude
usa cuota Q = m × U, una unidad común y multiplicadores versionados. Separa
crédito, token, costo físico, retención de saldo y presupuesto operativo.
Las tres autonomías y los tres flujos obligatorios no son una IA menos capaz
en el primer plan con IA. Esa propuesta no activa nuevos cobros o cuotas.

## Hechos estáticos, no aceptación de runtime

Inspección del 18-10-2026 en `claude/v1-implementacion`, HEAD indicado arriba
**más cambios locales extensos**; el SHA solo no reconstruye el árbol leído.

- `engine/src/dekopen_engine/billing.py` fija códigos STARTER/PRO/BUSINESS/
  BUSINESS_2X con cupos 0/2.000/6.000/12.000. No son lineales con sus precios.
- PRD-03 describe débito ceil(costo USD × 200); `ai_gateway/service.py` debita
  hoy `route.credits_cost` fijo. `usage.py` registra tokens/costo físico aparte.
  No afirmar que ya se factura por tokens reales.
- El período anual entrega hasta doce cupos mensuales mediante lifecycle; no
  doce cupos gastables al iniciar. Packs comprados no vencen y Starter puede
  conservarlos sin obtener por ello derecho a usar IA.
- El cupo de servicio usa aniversarios; el presupuesto de usage usa mes
  calendario America/Santiago. Se deben mostrar ambas ventanas.
- La reserva de usage protege capacidad del presupuesto; no es una retención
  de saldo de wallet ante dos llamadas con distintas claves.

Los archivos, símbolos y tests leídos se detallan en el contrato. No se
ejecutaron pagos, proveedores ni suites durante esta investigación.

## Construcción propuesta y compatibilidad

Reutilizar ledger/lotes y añadir reservas duraderas si faltan, sin otro saldo
autoritativo. Admisión breve bajo locks; sin locks largos durante HTTP;
liquidación/liberación idempotentes y conciliación de resultado incierto.
El costo físico persiste aunque el dominio revierta; no se inventa un cargo
comercial por existir ese costo. Historial propio y manual siguen accesibles.

Conservar precios, cuotas, períodos y política fija legacy. Una futura política
por costo medido requiere economía y migración explícitas. No derivar derechos
del monto de un webhook o de un multiplicador enviado por frontend.

La campaña 07 contrasta núcleo/modelo comunes, proporcionalidad en términos
de revisión legítimos, packs/budget, anualidad y admisión concurrente. No
confundir esta suscripción SaaS con [cobranza del taller](collections.md).
