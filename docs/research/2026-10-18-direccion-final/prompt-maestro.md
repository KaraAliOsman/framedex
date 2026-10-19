# Prompt maestro para Claude — versión final de DEKOPEN

Este documento es el encargo que el dueño copiará a Claude. Encontrarlo en el repositorio no autoriza ejecutarlo durante la fase de investigación de Codex. **No requiere elegir otra dirección.**

---

Implementa la versión completa y revisable de DEKOPEN siguiendo `docs/research/2026-10-18-direccion-final/README.md`. El dueño ha decidido: **Mesa de obra como vista inicial recomendada + Estudio elegible; mismo sistema, mismos datos; producto manual completo sin IA; copiloto opcional en popup global para los planes con IA.** El usuario trabaja y puede delegar al copiloto cuando lo necesite. El sistema no es un chat.

No entregues otro mockup ni solo CSS. Construye los flujos reales sobre el trabajo existente. El diseño anterior es una referencia de problemas, no un diseño aprobado. El objetivo es una versión que el dueño pueda usar y revisar, con calidad profesional en composición, comportamiento, datos y documentos.

**Condición de entrega aclarada por el dueño:** deja todo el alcance de esta versión implementado e integrado, como candidata definitiva para su revisión. Solo pueden quedar pendientes las conexiones y configuración finales de producción de **Railway, Supabase y pagos**, y las pruebas de lanzamiento que dependen de ellas. No uses esa excepción para posponer lógica, persistencia, autenticación, permisos, IA, créditos, documentos ni recorridos del producto. No se solicita otro prototipo ni una fase posterior de desarrollo funcional.

## Arranque y autoridad

1. Lee `AGENTS.md`, inspecciona `git status --short`, rama y HEAD. Preserva todos los cambios preexistentes de Claude y los goldens ya modificados. No hagas reset, clean ni reemplazos masivos. Anota tu punto de partida.
2. Lee `docs/wiki/index.md` y selecciona rutas por dominio. Consulta `docs/ENGINEERING.md`, `docs/PRODUCT.md`, `docs/design/CONSTITUCION.md`, la dirección final y los seis contratos de este paquete (01–06, distintos de los siete prompts). Usa cada contrato en su área. La decisión explícita reciente del dueño prevalece en intención de producto: reconcilia las reglas antiguas afectadas como parte de 01. Las fórmulas y los permisos siguen sus fuentes de autoridad técnicas.
3. Consulta la auditoría y las referencias del dossier de revisión profunda solo donde informen la tarea. Los prompts antiguos de 17-10, tres direcciones, docs/cola y el prompt anterior de 18-10 están superados donde contradicen este encargo; no son asignaciones adicionales.
4. Crea un registro de implementación en `docs/redesign/2026-10-18-final/implementation-ledger.md`: área, estado real, archivos afectados, resultado observable, bloqueos y evidencia final. No conviertas esta lista en un sustituto de desarrollar.

## Decisiones que debes implementar

- **Mesa y Estudio:** dos composiciones del mismo trabajo. Mesa prioriza conjunto, posiciones y excepciones; Estudio el diseño de una posición. Ambas están incluidas en la base manual. Reutiliza editor, operaciones, borrador, historial y modelo; conserva selección/revisión al cambiar. Galería/tabla no equivale a Mesa/Estudio.
- **Manual completo:** empresa/valores habituales → cliente/obra → posiciones → diseño/medidas/aperturas/vidrio/color → motor/precio → documento/revisión → materiales/corte/operación según rol. No requiere IA ni conexión a un modelo. Conserva las capacidades manuales existentes que sí funcionan.
- **Popup global IA:** cerrado inicialmente, accesible desde cualquier ruta; no reserva una columna, no reemplaza inspector, no encoge el lienzo. Cerrar, minimizar, ampliar y navegar conserva conversación, adjuntos y trabajo. Historial visible y espacio ampliado voluntario. No crear un nuevo hilo por ruta.
- **Chat y Trabajo:** Chat responde/prepara; Trabajo ejecuta con herramientas de dominio. Tres autonomías separadas: Solo proponer, Con aprobación y Omitir todo. En Omitir todo resuelve lo reversible autorizado sin aprobaciones por paso y entrega recibo final. Pregunta solo faltantes imprescindibles y juntos; avanza lo independiente.
- **Objetivo terminado:** el servidor comprueba postcondiciones. Cliente es una entidad vinculada; tres ventanas son tres posiciones válidas; precio solicitado tiene cálculo vigente. La respuesta terminada del modelo no marca el encargo Completado. Usa checkpoints e idempotencia para recuperar fallos sin duplicar.
- **Contexto y concurrencia:** el hilo sigue a la persona; cada encargo fija sus destinos al enviarse. Navegar no redirige escrituras. Conservar ediciones manuales posteriores; ante conflicto no sobrescribir ni deshacer silenciosamente.
- **MiMo 2.6 Pro:** selección vigente común a todos los planes con IA hasta que el dueño la cambie. Verificar identificador, herramientas, límites y transporte real sin exponer secretos. No introducir fallback silencioso. DeepSeek Flash 4.1 es candidato futuro mencionado por el dueño, sin validar ni configurar. Mantener el protocolo independiente del proveedor; un stub no acredita la conexión real.
- **Tres recorridos IA obligatorios:** documento/listado o plano con cotas explícitas a posiciones y PDF borrador reales; cambios por encargo sobre ventanas; comparación de revisiones compatibles con diferencias aplicables. El prompt 05 los concreta. No se sustituyen por links, marketing o supported=false. Registrar soporte honesto para extras no permite dejar estos tres sin implementar.
- **Plan base y planes superiores:** base manual completo, ambas vistas, sin llamadas al proveedor. Todos los planes con IA comparten modelo, núcleo, tres autonomías y los tres recorridos obligatorios; se diferencian por consumo disponible y extras profesionales concretos. Sigue el contrato 04: créditos proporcionales con términos versionados, sin modificar cuotas/precios legacy ni convertir «anual 30/49/99/149» en oferta. Reutiliza billing/entitlements; no aprovisiones cobros.
- **Diseño profesional:** aplica 02 + 05; cada referencia debe justificar una decisión concreta de jerarquía, selección, inspector o documento. Conserva lenguaje e identidad de DEKOPEN. El dueño no ha aprobado los píxeles anteriores.
- **Personaje:** sigue 06 para alta fidelidad a Grok Bot en silueta, ojos, gestos y movimiento. La petición se centra en el personaje animado, con conversación adaptada a DEKOPEN. Sustituye conscientemente la placa/brillo/órbita actual, integra estados reales y no cambies el cotizador por una app de bots.
- **Catálogos reales:** fabricante → serie → configuración/artículo. Priorizar Proline del dueño con códigos exactos y fuentes; no fusionar series por 60/70. Winhouse/Winhaus requiere resolver identidad. Referencia comercial, cotizable, fabricable y CNC son capacidades distintas. Imágenes técnicas útiles, sin fotos de stock que finjan productos.
- **Demos:** retirar del recorrido normal, conservar fixtures/laboratorio e historia. No borrar la DB ni rebautizar DEMO como Proline. Preparar y verificar un alcance real publicable; cualquier falta externa se registra exactamente, sin inventar valores ni afirmar aceptación técnica.
- **Aperturas y editor:** corregir la regresión denunciada y distinguir incompatibilidad, bloqueo por revisión/precio, cálculo y ancho. Comprobar cara/mano/hoja y persistencia, no solo que cambia un icono. Motor, 2D, 3D, BOM y documento describen el mismo objeto.
- **Documento y operación:** documento comercial profesional y editable en contenido/composición, cifras canónicas; corte, stock, taller y QR con objeto, revisión, permiso y siguiente acción claros. Reutiliza lo que ya existe antes de crear módulos nuevos.

- **Adjuntos en el popup:** incorpora documentos, imágenes y demás formatos realmente compatibles en Chat/Trabajo, con múltiples fuentes, preview, persistencia, límites y evidencia navegable. El mínimo y los adaptadores se especifican en [03](03-copiloto-y-planes.md#adjuntos-multimodales--ampliación-explícita-del-dueño) y en 05, sección 3.1. No posponerlo como integración final ni fingir lectura completa o soporte universal. Las ampliaciones de innovación se distinguen de este requisito explícito.

## Construcción en orden

Ejecuta los prompts de `docs/research/2026-10-18-direccion-final/prompts/` en este orden:

1. `01-fundamentos.md`
2. `02-dos-vistas.md`
3. `03-editor-cotizacion.md`
4. `04-operacion-documentos.md`
5. `05-copiloto.md`
6. `06-planes.md`
7. `07-cierre-qa.md`

Son etapas de un único encargo continuo. No pares entre ellas para pedir otra elección, permiso para editar archivos ni aprobar decisiones rutinarias. Puedes delegar trabajos independientes si tu entorno lo permite, manteniendo contratos y responsabilidad de integración. Si se corta tu contexto, el registro permite continuar sin reiniciar ni marcar falsamente terminado.

**Desarrollo primero:** en 01–06 implementa de forma continua y conserva el proyecto compilable. No montes baterías de pruebas, campañas visuales ni informes de aceptación por etapa. Las pruebas formales, proveedor real, recorridos, correcciones y checks obligatorios se concentran en 07. Los errores de compilación o integración que impidan construir se corrigen cuando aparezcan. No difieras deliberadamente un problema técnico conocido que invalida lo siguiente.

## Bar de calidad

Aplica el contrato visual por tarea: lienzo, documento o colección como protagonista; selección reconocible; acción primaria inequívoca; bordes de control visibles; color con significado; estados con causa y salida; foco/teclado; anchos útiles; copia en español de taller. No reduzcas detalles importantes para que todo se vea vacío y uniforme. Elimina los caminos realmente sustituidos, preservando capacidades y enlaces existentes.

Para cada cambio relevante de presentación registra brevemente Before | After | Why con su propósito. No introduzcas una segunda librería o motor de formularios solo por estética. Las referencias competitivas aportan patrones y capacidades; no autorizan copiar activos ni reglas privadas.

## Invariantes y operación

Motor puro como única fuente de números calculados. Decimal en medidas y dinero. RLS/org_id y permisos reales, también en herramientas IA. Revisiones emitidas e historia de precios inmutables. Pagos idempotentes. Emisión, envío, publicación de catálogo, compra/pago y demás efectos externos conservan clic humano explícito. Omitir todo no omite estos límites ni las validaciones del motor. La IA no controla código, seguridad o pagos.

Mantén engine + Django + Supabase/Postgres + React/Vite. El dueño confirma **Railway** para la conexión final de despliegue; no se solicita migrar a Ruby on Rails. API: backend primero, generar OpenAPI y orval, nunca editar clientes generados a mano. Fórmulas nuevas requieren casos golden; no regenerar goldens para ocultar regresiones ni tocar los cambios previos sin causa revisable.

Antes de limpiar archivos lee `docs/operations/WORKSPACE.md`. `.run/` contiene sesiones y propiedad del stack. Para revisión local usa `.agents/skills/testing-framedex/SKILL.md`; reutiliza el stack del dueño si su estado importa. Las imágenes construidas no se actualizan solas por editar fuente. Si necesitas reconstruir, preserva DB y estado; no reseedees ni destruyas datos para conseguir capturas limpias.

## Qué puede quedar para la conexión final

Prepara durante el desarrollo los contratos, código y archivos necesarios; en 07 verifica su coherencia y documenta el procedimiento exacto, sin activar servicios de producción:

| Servicio | Debe quedar construido antes de entregar | Único pendiente admisible de conexión |
|---|---|---|
| Railway | Configuración de build/arranque compatible con la arquitectura, web/API/worker y dependencias que use el repo, healthchecks, variables documentadas y procedimiento de migración/recuperación. Reutilizar lo existente y verificarlo. | Aprovisionar o vincular el proyecto de producción, cargar secretos, fijar dominios/orígenes y ejecutar el despliegue autorizado. |
| Supabase | Persistencia real en revisión con Postgres/Supabase, migraciones, RLS, roles y contratos de auth/storage usados por el producto. Inventario ordenado de migraciones y pasos de aplicación; nunca reconstruir datos comerciales con fixtures. | Vincular el proyecto de producción y sus credenciales, configurar URLs/proveedores/buckets pertinentes y aplicar las migraciones mediante el procedimiento preparado. |
| Pagos | Suscripciones, derechos, créditos, checkout/webhooks del proveedor vigente, firmas, idempotencia y recuperación implementados; validación disponible de sandbox y contratos. Mantener ofertas y saldos históricos. | Conectar cuenta/credenciales y endpoints de producción, cargar precios aprobados y verificar el circuito final autorizado. No inventar proveedor ni importes si siguen sin decisión. |

Deja en `docs/redesign/2026-10-18-final/production-handoff.md` servicios, variables sin valores secretos, archivos, comandos, orden de conexión, dependencias, verificaciones y recuperación. Cada pendiente nombra el dato/acceso concreto; «integrar backend», «conectar IA», «hacer persistencia» o «terminar pagos» no son pendientes de configuración admisibles. Si el proveedor de pagos o una condición comercial imprescindible sigue sin decisión, indícalo como bloqueo de activación comercial, sin simular una integración terminada. MiMo pertenece a la versión funcional y su revisión real en 07; no se posterga como cuarta integración.

Secuencia de cierre: **desarrollo completo 01–06 → comprobación técnica y correcciones 07 → revisión/aprobación del dueño de la candidata definitiva → conexiones finales de producción → pruebas de lanzamiento y correcciones necesarias → lanzamiento autorizado**. La aprobación se pide sobre el producto ejecutable, sin revisiones rutinarias entre etapas. Las pruebas posteriores a la conexión no sustituyen la validación técnica de 07. La candidata aprobada sigue pendiente de habilitación de producción hasta completar esas conexiones y pruebas; un fallo exige corrección antes de lanzar.

## Entrega final

Completa 07 y corrige los fallos hasta satisfacer `criterios-de-entrega.md`. Entrega el cambio por PR siguiendo el repositorio, sin fusionar ni desplegar por iniciativa propia. Si tu entorno carece de acceso para crear PR, conserva el diff y da la instrucción exacta pendiente; no lo presentes como PR creado.

Deja la aplicación funcionando para el dueño, identifica URL y ref/árbol realmente servido, y explica cómo ver Mesa, Estudio y el popup. Si el servidor usa imágenes antiguas, reconstruye el alcance necesario siguiendo la skill antes de anunciar que los cambios ya se ven. Entrega la candidata definitiva con informe breve de validación, evidencia real y `production-handoff.md`. El objetivo es que solo falten las conexiones finales indicadas y sus pruebas de lanzamiento. Si queda una función obligatoria o una fuente imprescindible sin resolver, la entrega es incompleta: registra el bloqueo exacto, no lo escondas como integración. No declares versión lista para producción ni “mejor del mercado” basándote en mocks, stubs o checks incompletos.
