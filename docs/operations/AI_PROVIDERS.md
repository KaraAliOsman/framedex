# Proveedores de inteligencia artificial

Las diez rutas de `ai_routes` usan por defecto `MIMO` y
`primalabs-ai/MiMo-V2.6-Pro`. El dueño con MFA configura proveedor, modelo,
tiempo, reintentos, herramientas y tarifa por organización para `design_assist`,
`agent`, `context_assist` y `catalog_import` en **Ajustes › Inteligencia artificial**.
El resto del producto conserva nombres de negocio. Ninguna API envía una
credencial o dirección del proveedor al navegador.

## Entorno del servidor y del worker

```text
AI_GATEWAY_MIMO_API_KEY=<credencial privada del servidor>
AI_GATEWAY_MIMO_BASE_URL=https://api.primalabs.ai/v1
AI_GATEWAY_MIMO_MODEL=primalabs-ai/MiMo-V2.6-Pro
AI_GATEWAY_MOCK_ENABLED=0
```

Son los nombres existentes `AI_GATEWAY_{P}_*`. Cargue las variables en memoria
al iniciar Django y el worker; nunca registre sus valores, las copie a archivos
auxiliares o las ponga en `VITE_*`. El modelo de entorno sirve como configuración
inicial; una ruta guardada por el dueño tiene prioridad. La auditoría conserva
el modelo efectivo, incluyendo el informado por la respuesta del proveedor.

`AI_GATEWAY_{P}_PROTOCOL=openai|http` fuerza el transporte. MiMo, OpenAI,
OpenRouter, DeepSeek y Qwen usan `/chat/completions`; el genérico usa `/invoke`
con `input`, `tools`, `tool_choice` y `response_schema`.
`AI_GATEWAY_{P}_TIMEOUT_S`, si se declara, añade un techo de despliegue entre
1 y 600 segundos. Cada capacidad tiene un límite entre 1 y 180 segundos
(60 por defecto) que incluye descarga, fallback y reintentos.

El modo de prueba necesita **dos decisiones explícitas**: el flag en `1` y
una ruta a `MOCK`. Ni `DEBUG` ni pytest lo habilitan. La interfaz muestra
«Modo de prueba». El flag no sustituye las rutas reales: MiMo sigue siendo el
proveedor local aunque el entorno permita pruebas. Los tests habilitan el
flag explícitamente con un fixture.

## Herramientas, recuperación y entradas

- El agente envía los esquemas del registro de IA2 como funciones nativas y
  devuelve los resultados con sus `tool_call_id`. Las consultas cacheadas
  también vuelven al modelo. La última ronda exige una respuesta final.
- En automático solo un rechazo explícito de `tools` o `tool_choice` permite
  volver a JSON estricto. El esquema viaja como instrucción confiable y se
  valida con JSON Schema. Un modelo inválido, una credencial rechazada o un
  HTTP 400 arbitrario nunca activan el fallback.
- Hasta dos reintentos con esperas de 0,25 y 0,5 segundos, solo ante transporte
  transitorio o HTTP 408/429/500/502/503/504. La clave incluye organización y
  `operation_key`; el tiempo total no se reinicia.
- Imágenes: partes multimodales. MiMo rechazó el PDF directo en el sondeo de
  IA3. D01 extrae el texto literal; las páginas sin texto se renderizan con
  `pypdfium2`: máximo 20 páginas, 8 millones de píxeles por página y 12 MiB de
  imágenes. Una URL escrita como texto nunca se presenta como archivo leído.
- La lectura visual sigue siendo una propuesta. Sin evidencia literal no
  alcanza confianza alta ni publica autoridad técnica: conserva revisión y
  diff de D01. La ruta de catálogo permite otro modelo de visión.

SSRF conserva HTTPS, resolución pública fijada, Host/SNI y un límite de
respuesta de 1 MiB. Las causas se traducen a lenguaje de negocio. Ni cuerpos
de error, prompts o cabeceras entran en logs.

## Presupuesto y costo

El presupuesto mensual usa **créditos de solicitudes**, según el precio de
cada capacidad, y el mes calendario de America/Santiago. Vacío: sin límite
adicional; cero: bloquea llamadas. La reserva se serializa por organización
e incluye solicitudes en curso y respuestas pagadas, incluso si el dominio
revierte después. Un timeout o fallo ambiguo conserva una reserva prudente.
El bloqueo avisa al dueño; las funciones manuales siguen disponibles.
Los débitos de IA anteriores a la migración también cuentan, desde su auditoría
inmutable y sin duplicar intercambios nuevos. Si esa historia no tiene medición
física completa, los tokens y el costo mensual quedan «Sin dato».

`ai_provider_usage` conserva metadatos físicos sin contenido por una conexión
independiente del rollback. Cada fallo tiene su propio intento. Intercambios
terminales y `ai_usage_events` son inmutables. Auditoría y débito mantienen
la transacción atómica original. Una llamada pagada cuyo dominio revirtió
no se repite con la misma clave: se revisa en Trabajos y se inicia una nueva
solicitud explícita.

El dueño declara **ambas** tarifas en USD por millón de tokens desde su
contrato. El motor calcula con Decimal y golden. Sin tarifa o tokens medidos:
«Sin dato», con causa; nunca tarifa inventada ni cero como sustituto. Cada
intercambio conserva su tarifa original. Billetera de créditos y costo
estimado del proveedor son magnitudes distintas.

## Verificación y observabilidad

«Probar conexión» ejecuta E03 reducido de IA1: operaciones sobre una copia,
oráculo exacto de 1 800 × 1 350 mm y evaluación del motor. No cambia proyectos.
Conserva un fallo del oráculo aunque HTTP responda bien y admite otra prueba.

`/jobs` filtra capacidad y estado, muestra costo y herramientas ejecutadas.
El dueño ve la organización; cada miembro ve sus llamadas. El polling existente
publica «Consultando proyecto», «Calculando con el motor» y «Preparando propuesta»
con commits separados y guard de lease. Los logs `ai_provider_exchange` y
`ai_provider_job` agregan modelo, latencia, rondas, tokens y resultado sin contenido.

IA1 sigue revirtiendo catálogo, proyectos, auditoría y billetera. El informe
separa el delta físico esperado; ninguna tabla de dominio pierde su comprobación
de aislamiento. Evidencia y límites: `docs/ai/IA3-ACEPTACION.md`.
