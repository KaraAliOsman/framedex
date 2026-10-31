---
type: synthesis
status: active
updated: 2026-10-18
volatility: medium
verified_ref: 6f78e3299d93816991fb7c2fe2a2044458fc5e7a
sources:
  - docs/wiki/sources/owner-credits-and-grokbot-2026-10-18.md
  - docs/PRD/PRD-03.md
---

# Suscripción SaaS, créditos y límites de IA

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
