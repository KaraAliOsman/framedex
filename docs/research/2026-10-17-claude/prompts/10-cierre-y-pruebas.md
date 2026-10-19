# Etapa 10 — bugs, pruebas y entrega final

Ahora realiza la campaña conjunta de corrección y verificación. Lee 10-ejecucion-y-aceptacion, la lista de incidencias de implementación, 12 y las invariantes del repositorio. Preserva trabajo ajeno, sesiones y datos; sigue la skill de revisión local al preparar el stack.

1. Reproduce y corrige incidencias por impacto: integridad/seguridad/cálculo/pérdida de datos, recorrido bloqueado, interacción y presentación. Unifica causas; no arregles solo la captura.
2. Ejecuta los checks pertinentes al alcance transversal: lint, typecheck, suites y build. Si hay esquema/RLS, database gate; si hay fórmulas, goldens/mutaciones conforme a AGENTS. No debilites checks ni regeneres goldens sin revisión.
3. Completa los doce recorridos de cierre definidos en el plan, con permisos, cambios de versión, cancelación/reintento y estados de fallo. No confundir una denegación por rol con bug del importador.
4. Revisa visualmente en navegador el producto real, a tamaños de escritorio y móvil pertinentes. Si la herramienta no conecta, documenta ese límite y no afirmes una visita realizada.
5. Renderiza e inspecciona las ocho plantillas PDF, casos cortos/largos, firma opcional, numeración y edición manual/IA. Verifica concordancia entre preview, exportación y datos del motor.
6. Evalúa tareas IA con proveedor real cuando afirmes ejecución efectiva, números y alcance. Mocks se identifican como pruebas de contrato.
7. Procesa los PDF de fabricantes si están disponibles y compara con referencia por campo/página; de lo contrario conserva ese pendiente. CNC no se homologa sin máquina/documentación/prueba técnica.
8. Mide tiempos y comprensión del recorrido bajo condiciones declaradas. No presentes la meta de un minuto o quince minutos como resultado sin medir.

Después de correcciones que cambien composición, vuelve a valorar el recorrido visual y la calidad documental. Pasar una suite no garantiza que el producto sea agradable o que el dueño acepte el diseño.

Entrega un resultado concreto: comportamiento final, decisiones importantes, capturas/PDF/recibos seleccionados, validación real y límites pendientes. Actualiza wiki y prepara la PR con descripción del cambio final. No fusionar ni desplegar automáticamente; no declarar terminadas capacidades que aún son placeholders o requieren acceso externo ausente.
