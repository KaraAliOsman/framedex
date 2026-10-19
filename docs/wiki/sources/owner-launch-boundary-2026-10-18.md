---
type: source
status: active
updated: 2026-10-18
volatility: low
sources:
  - owner clarification of final implementation and launch boundary, 2026-10-18
---

# Aclaración del dueño: versión definitiva y conexiones finales

## Decisión explícita

El dueño precisa: «tiene que dejarlo listo todo solo faltando integraciones
finales de railway supagbase y pagos», para probar una vez aprobada la versión
definitiva antes de lanzar. La aclaración amplía la definición de entrega de
los prompts para Claude; no ordena ejecutar ahora el rediseño, conectar cuentas
de producción, cobrar ni desplegar.

## Aplicación al encargo

- Todo el alcance funcional debe quedar implementado y ejecutable para revisión.
  Las tres excepciones son conexiones/configuración finales de producción de
  Railway, Supabase y pagos. Railway queda identificado; no implica Ruby on Rails.
- Código, persistencia, migraciones, auth/RLS, lógica de suscripciones/créditos,
  integración del proveedor de pagos vigente y MiMo real pertenecen a la versión
  funcional. No se aplazan como «integraciones finales».
- La preparación de configuración y el procedimiento de conexión deben estar
  incluidos. Credenciales/cuentas de producción, dominios y activación comercial
  aprobada quedan para la conexión final, sin publicar secretos ni inventar precios.
- Se mantiene desarrollo 01–06 y comprobación técnica/corrección 07. El dueño
  revisa y aprueba la candidata ejecutable; tras ello se conectan los servicios
  finales y se hacen las pruebas del entorno de lanzamiento antes de publicar.
  Esas pruebas no sustituyen el cierre técnico local ni se declaran ya aprobadas.
- Una función obligatoria o fuente técnica imprescindible ausente mantiene la
  entrega incompleta. No se convierte en una cuarta excepción ni se oculta como
  configuración de infraestructura.

La separación entre candidata para revisión, aprobación humana y habilitación
de producción es la aplicación operativa de esta intención. No acredita que
Claude haya construido o validado el producto, ni aprueba tarifas/proveedores
comerciales aún no decididos.

## Documentos actualizados

[Prompt maestro](../../research/2026-10-18-direccion-final/prompt-maestro.md),
[cierre 07](../../research/2026-10-18-direccion-final/prompts/07-cierre-qa.md),
[criterios](../../research/2026-10-18-direccion-final/criterios-de-entrega.md)
y [síntesis](../research/final-direction-2026-10-18.md).
