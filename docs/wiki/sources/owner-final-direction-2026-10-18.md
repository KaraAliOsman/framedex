---
type: source
status: active
updated: 2026-10-18
volatility: low
sources:
  - owner correction after reviewing three concepts, 2026-10-18
  - owner original PRD attachment b8dca4f1-0c32-4aa3-824c-68bad9f2bf23
  - docs/research/2026-10-18-direccion-final/README.md
---

# Corrección final del dueño: manual, dos vistas y popup

## Autoridad y alcance

Fuente: mensaje posterior a la comparación Estudio/Mesa/Centro del 18-10-2026.
El dueño prefiere la opción 2 (Mesa), conserva también la 1 (Estudio) y pide que
la persona elija con cuál trabajar. Aclara que el usuario trabaja y la IA puede
ponerse en su lugar **cuando se le pide**. Solicita varios subagentes, revisar
competencia/trabajos y entregar la opción final y prompts listos para Claude.
Esta fase autoriza investigación/especificación, no ejecutar el rediseño.

## Decisiones explícitas y lectura operativa

- Mesa y Estudio son vistas del mismo producto; Mesa es la recomendada al inicio.
  No se interpreta como dos bases de datos, dos tarifas o dos temas.
- La IA es copiloto completo opcional en popup, disponible sobre cualquier ruta.
  No es panel fijo incrustado en la cotización ni reemplaza el inspector.
- El plan principal no tendrá IA. Debe ser un cotizador manual excelente por sí
  mismo; los planes superiores necesitan valor sustancial por trabajo delegado.
- Conservar Chat/Trabajo y Omitir todo, además de las políticas de propuesta y
  aprobación. «Omitir todo» no modifica las invariantes del motor o clic humano.
- Los conceptos anteriores parecen demos y no alcanzan la calidad profesional
  esperada. Elegir su estructura no aprueba sus píxeles, tarjetas ni paneles.
- Desarrollo como prioridad, pruebas al final. No campañas nuevas por etapa;
  conservar las comprobaciones obligatorias y cerrar fallos al terminar.
- No volver a presentar las tres alternativas como elección pendiente.

Interpretación documentada: «el cliente elige» se refiere al usuario del SaaS
que decide su vista de trabajo, sin cambiar el portal del comprador. La base
incluye ambas vistas. Las diferencias comerciales exactas de planes/precios no
quedan aprobadas por esta corrección.

## Contradicciones identificadas

`docs/PRODUCT.md` aún sitúa AI-native/core interface como identidad y la
Constitución aún exige asistente compartiendo riel. Esos mandatos de intención
quedan subordinados a la corrección del dueño; Claude debe reconciliarlos en la
implementación. No se han cambiado silenciosamente en esta fase documental.
Los invariantes de ingeniería siguen vigentes.

Los USD 39/69/aprox.149 del PRD original son antecedentes; la plataforma actual
ya tiene billing/entitlements. No autorizan nuevos cobros, cuotas ni migrar
clientes. MiMo 2.6 Pro sigue como preferencia sujeta a verificación real.

## Entrega asociada

La [aclaración posterior de créditos, modelo y personaje](owner-credits-and-grokbot-2026-10-18.md)
precisa MiMo común hasta cambio expreso del dueño y diferencias de consumo;
los importes son referencia. También centra la fidelidad a Grok Bot en el
personaje animado y pide ampliar referencias profesionales. El paquete fue
actualizado con esas decisiones; no se implementó producto.

[Dirección y paquete final](../../research/2026-10-18-direccion-final/README.md),
[prompt maestro](../../research/2026-10-18-direccion-final/prompt-maestro.md) y
[síntesis](../research/final-direction-2026-10-18.md). No prueban implementación.
