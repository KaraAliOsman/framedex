# Prompt maestro — iniciar la implementación futura

Este prompt se prepara durante una investigación sin cambios de aplicación. Se activa cuando el dueño lo entregue expresamente a Claude para iniciar el trabajo. Su presencia en el repositorio no autoriza ejecutarlo.

---

Trabaja en DEKOPEN como responsable de producto, diseño de interacción e implementación. Quiero una v1 profesional, sencilla y agradable para diseñar/cotizar ventanas PVC y aluminio, importar catálogos y continuar hacia materiales/corte. La IA debe trabajar por el usuario, usando preferencias de empresa y mostrando una muestra breve para revisar. El resultado anterior fue rechazado y revertido: no recuperes esos commits ni trates sus planes como dirección aceptada.

Empieza comprobando rama, HEAD y cambios locales. El paquete fue escrito sobre `6f78e3299d93816991fb7c2fe2a2044458fc5e7a`, con producto restaurado al estado de `edcfd2844d2c2fc7cbb0d3b543b50e9089ab9b3f`. Revalida diferencias si el checkout cambió. Preserva el cambio ajeno de `engine/tests/golden_analytics.json`, datos, sesiones y `.run/`. No reabras PR 159 ni mezcles otro trabajo.

Lee AGENTS, `docs/wiki/index.md` y el paquete `docs/research/2026-10-17-claude/`: README, 00-encargo-y-criterios, 01-evidencia-y-auditoria y 10-ejecucion-y-aceptacion. Usa 03 y 13 para recorridos y pantallas. Carga las especificaciones del dominio cuando llegues a él; no releas todos los planes históricos.

Ejecuta los prompts 01–10 en orden, con continuidad entre etapas y sin detenerte a solicitar permiso para decisiones rutinarias. Implementa capacidades completas y conserva un estado breve de trabajo para reanudar tras cambios de contexto. No termines anunciando un paso siguiente si aún puedes realizarlo. Si algo depende de un dato externo, registra el límite y avanza en lo independiente.

La dirección debe resolver navegación, jerarquía, controles y textos antes de decorar. Conserva el logo y aprovecha las bases útiles del dibujo/3D. Turquesa es un acento viable; el documento 04 propone un tema claro coherente, sujeto a tu criterio al componer. Actualiza la constitución para reflejar el encargo reciente donde existe conflicto. No atribuyas al dueño aceptación de tokens o pantallas que no vio.

Usa principios de Apple/Emil cuando tengas las skills disponibles: respuesta, continuidad, buenos valores predeterminados y detalles invisibles bien resueltos. No copies sus productos ni instales herramientas por acumularlas. Evita los patrones concretos enumerados en 11-claude-opus-5-5.

Reglas esenciales: cifras del motor y Decimal, aislamiento/RLS, revisiones emitidas inmutables, historial e idempotencia. IA del producto sin acceso a pagos, código, secretos o seguridad; herramientas de dominio y permisos del servidor. Cambios reversibles autorizados pueden prepararse/guardarse; emitir, enviar y comprometer acciones externas conserva un clic humano sobre un resultado concreto.

Dedica las etapas 01–09 a calidad y construcción. Registra los bugs incidentales sin abrir campañas de pruebas o depuración en cada pantalla. La etapa 10 concentra correcciones y pruebas requeridas antes de entregar; no debilites los checks. Resuelve anticipadamente solo bloqueos imprescindibles y registra por qué.

No inventes evidencia: falta una visita visual nueva, los PDF exactos Proline/Aluminios 2000 y homologación en máquina. Consulta 12-incidencias-y-pendientes. Metas de un minuto y quince minutos son objetivos que deberán medirse. Un mock, un enlace o un texto convincente no acreditan ejecución de la capacidad.

Al finalizar entrega la aplicación coherente, muestras reales de documentos y recorridos, resumen de validación y límites restantes. Mantén el wiki y prepara una PR revisable cuando corresponda. No fusionar ni desplegar automáticamente.
