# 07 — Campaña final de pruebas, correcciones y entrega

Ejecuta esta etapa después de desarrollar 01–06. Es la campaña formal de pruebas de este encargo, según la preferencia del dueño. No vuelvas a pedirle elegir dirección ni revisar otra maqueta antes de probar la implementación real.

El resultado es una **candidata definitiva completa y ejecutable para su revisión**, quedando únicamente las conexiones/configuración finales de producción de Railway, Supabase y pagos. Sigue el alcance por servicio del [prompt maestro](../prompt-maestro.md). Ninguna función obligatoria pendiente puede etiquetarse como conexión final; si sigue bloqueada, registra que la entrega está incompleta.

## Preparar la revisión

Lee [criterios de entrega](../criterios-de-entrega.md), el registro de implementación y `.agents/skills/testing-framedex/SKILL.md`. Identifica propietario y estado del stack antes de tocarlo. Reutiliza su DB y estado cuando sean necesarios; no reseedees ni limpies `.run/`. Si las imágenes construidas siguen sirviendo código anterior, reconstruye los servicios afectados según la skill preservando los datos. Deja constancia del ref/árbol servido.

Usa roles y datos de revisión explícitos. Proline y el primer alcance real tienen que conservar fuente, reglas, costos privados y revisión competente; no uses DEMO renombrado para satisfacer el caso real. No envíes correos reales ni contraigas compras/pagos al verificar: prepara el resultado y el clic humano en entorno de revisión.

## Verificar y corregir

1. Ejecuta el recorrido manual completo sin IA, en Mesa y Estudio. Revisa los casos M01–M13 de los criterios, adaptando únicamente capacidades físicas no admitidas con un límite explícito. Recupera y corrige el fallo de aperturas, no solo el caso favorable observado antes.
2. Ejecuta A01–A17 y B01–B04 con MiMo real cuando corresponda, además de casos controlados para fallos/idempotencia. A11–A13 cubren los tres recorridos obligatorios comunes a todos los planes IA: documento a posiciones/borrador, cambios sobre selección y comparación/propagación de revisiones. A15–A17 verifican adjuntos desde popup, todos los formatos mínimos, citas persistentes, cobertura, conflictos y permisos; registra la matriz real de formatos/tareas y límites. Registra resultado, pasos humanos, correcciones y consumo; incluye ambigüedad y concurrencia. Comprueba tres autonomías, privacidad de thread, destino fijo, mismo modelo sin fallback, cuotas/packs/budget, anualidad y reservas concurrentes sin alterar ofertas reales.
3. Revisa composición y controles con el producto real en los anchos definidos, teclado, zoom y estados representativos. Contrasta decisiones de las referencias profesionales y personaje contra los contratos 05/06. Comprueba gesto, transición, repetición, tamaño óptico, reduced motion y pausa oculta; una captura quieta no acredita movimiento. Usa el renderer/documento auténtico y resultados del motor; no hagas screenshots de una historia aislada como prueba de la aplicación completa.
4. Ejecuta los seis checks del repositorio indicados en los criterios. Corrige cada fallo material y repite lo afectado hasta satisfacer las puertas y rúbricas. Los checks bloqueados quedan bloqueados, nunca aprobados por inferencia. No debilites las comprobaciones ni regeneres golden para esconder divergencias.
5. Evalúa cada eje con caso/evidencia/cobertura, separando el producto manual y las capacidades con IA. No inventes notas competitivas ni porcentajes de ahorro. Cierra críticos y altos; corrige fricciones que impiden el umbral. Si persiste un bloqueo externo real, describe el dato/permiso/acceso preciso y el alcance listo, sin fingir entrega total.

## Entregar

- Actualiza el registro y crea `docs/redesign/2026-10-18-final/acceptance.md` con ref/árbol, entorno, resultados, evidencia seleccionada, límites y pendientes externos. Mantén capturas temporales fuera del historial salvo selección deliberada, siguiendo la política del repositorio.
- Crea `docs/redesign/2026-10-18-final/production-handoff.md` con archivos y comandos verificados, servicios y variables sin secretos, orden de conexión, migraciones/recuperación y comprobaciones pendientes de Railway, Supabase y pagos. La infraestructura/configuración preparable pertenece a la entrega; no basta escribir «falta integrar». Identifica cualquier decisión de proveedor/precios todavía no aprobada como bloqueo de activación comercial.
- Actualiza la wiki según SCHEMA y su log: solo capacidades comprobadas se presentan como estado actual. Mantén investigación, intención del dueño y comportamiento verificado separados.
- Presenta cambios en una PR por el flujo del repositorio; no fusionar ni desplegar. Si faltan credenciales/acceso, conserva el diff y registra ese paso pendiente sin llamarlo PR creado.
- Deja la app ejecutándose y abre la pantalla útil para la revisión del dueño. Informa URL, dónde cambiar Mesa/Estudio y cómo abrir el popup en una cuenta con IA. El plan base debe poder revisarse por separado.
- El mensaje final explica qué se construyó, qué pruebas pasaron y los pendientes precisos de conexión. Presenta el producto real al dueño para aprobar la candidata definitiva. Después de su aprobación corresponden conexiones finales, pruebas del entorno de lanzamiento y correcciones necesarias antes del lanzamiento autorizado; esta etapa no las acredita ni activa producción. No digas «terminado» porque acabó una lista de tareas ni «listo para producción» si las puertas no están satisfechas.
