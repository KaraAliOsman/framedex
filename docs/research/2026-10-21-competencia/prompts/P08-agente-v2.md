# P08 · Agente DEKOPEN v2: hace el trabajo, con cifras del motor

**Rama:** `gpt/dk2-p08-agente` · **Depende de:** P07 · **Siguiente:** P09

## Objetivo

Que el agente convierta una solicitud (texto, WhatsApp pegado, correo, voz,
plano, foto) en una **obra con ventanas, precio y PDF borrador**, que haga
cambios por conversación, que revise antes de emitir y que deje todo lo externo
a un clic humano. Cada cifra viene del motor y cada dato enlaza a su origen.

Especificación completa: `05-agente-ia.md` (principios §1, automatizaciones 1–7
§2, autonomía §3, interfaz §4, contrato §5, métricas §6). Mockups:
`mockups/Agente.dc.html`, `mockups/Hoy.dc.html` (tarjeta de lo preparado).
Revisa `backend/ai_gateway/` (proveedor MiMo, créditos, `agent.py`),
`backend/jobs/`, `engine/src/dekopen_engine/design_operations.py`,
`frontend/src/features/assistant/` y `docs/ai/OPERACIONES.md`.

## Decisión pendiente del dueño

Popup global vs barra Ctrl K + panel lateral (`04` §6). Implementa barra + panel
detrás de la bandera `agente_panel_lateral` activada por defecto; el popup
actual sigue disponible si se apaga.

## Qué construir

1. **Herramientas = API del producto**, con validación del servidor y del motor:
   `crear_obra`, `buscar_o_crear_cliente`, `agregar_ventana`,
   `modificar_ventana(operaciones)`, `calcular_precio`, `generar_pdf_borrador`,
   `revisar_cotizacion`, `importar_tabla_serie`, `comparar_lista_precios`,
   `consultar_datos(métrica, filtros)`. Cada herramienta declara si es reversible
   y si es externa (las externas nunca se ejecutan sin clic).
2. **Trazabilidad de origen:** cada ventana o valor creado por el agente guarda
   `origin_ref` (frase del mensaje, celda del Excel, página y recuadro del PDF,
   foto) y se muestra resaltado en la vista de la obra (ver mockup: marcas de
   color en el mensaje original enlazadas a cada ventana). Supuestos explícitos
   (p. ej. alto estándar de puerta) en una tarjeta «Supuestos que conviene confirmar».
3. **Planos/PDF → cuadro de vanos** con doble lectura y discrepancias marcadas;
   **foto → ventana aproximada** marcada «para cotizar, no para fabricar».
4. **Trabajos con postcondiciones:** un trabajo solo termina como «Listo» si se
   cumplen sus postcondiciones (p. ej. la obra tiene N ventanas con precio y PDF).
   Si no, termina «Incompleto» con lo que falta. Resumen final con lo hecho,
   supuestos y **Deshacer todo** (para lo reversible).
5. **Autonomía:** Proponer · Hacer y avisar · Hacer todo (`05` §3). Créditos y
   presupuesto según la política vigente (`backend/billing/`).
6. **Interfaz:** barra de comandos Ctrl K (buscar, navegar, pedir), panel lateral
   por obra con historial persistente, adjuntos arrastrables, tarjetas de
   progreso; **bandeja de revisión** (en Hoy) con lo que el agente preparó.
7. **Evaluación:** carpeta `backend/tests/ai_eval/` con ≥ 30 casos anonimizados
   (mensajes, planos y fotos de prueba creados por ti, sin datos reales de
   clientes) con resultado esperado; script que mide ventanas correctas,
   supuestos marcados y **cero cifras no provenientes del motor**. Corre en un
   job de CI no bloqueante con respuestas grabadas (sin llamar al proveedor real).

## Criterios de aceptación

- [ ] e2e con proveedor simulado: pegar el WhatsApp del mockup → obra con 4
      ventanas en PRO6004, precio del motor, 2 supuestos marcados, PDF borrador;
      nada enviado; **Deshacer todo** deja la obra como estaba.
- [ ] Prueba que falla si un documento contiene una cifra que no viene del motor.
- [ ] Prueba de seguridad: ninguna herramienta externa se ejecuta sin la
      confirmación humana registrada en el servidor (no basta el prompt).
- [ ] Evaluación grabada ≥ 90 % de ventanas correctas en el set; reporte en la PR.
- [ ] Todo verde; wiki (`assistant-work.md`, `ai-provider.md`) y ESTADO.md.
