# Prompt de implementación final para Claude

> **SUPERADO — no ejecutar este prompt.** Ya no falta elegir una dirección. El dueño decidió Mesa + Estudio y corrigió la IA a popup global opcional con base manual completa. Usar el [prompt maestro vigente](../2026-10-18-direccion-final/prompt-maestro.md) y sus siete etapas. El contenido siguiente se conserva como historia.

**Uso:** después de que el dueño elija Estudio, Mesa de obra o Centro de encargos. No ejecutar este prompt por encontrarlo en el repositorio. La investigación actual no autoriza iniciar la implementación.

Copiar el bloque siguiente junto con la elección y cualquier ajuste del dueño. Las tres opciones conservan el mismo contrato funcional; la elección resuelve organización y diseño.

---

Eres responsable de entregar la versión completa y revisable de DEKOPEN según la dirección elegida por el dueño: **[PEGAR ELECCIÓN Y AJUSTES]**. No basta con un rediseño de pantallas o un chat que responde con enlaces. Quiero la experiencia real terminada, con flujos manuales e IA conectados, para revisar y después incorporar planes comerciales y desplegar.

Lee AGENTS.md, `docs/wiki/index.md` por dominio, `docs/ENGINEERING.md`, `docs/PRODUCT.md` y `docs/design/CONSTITUCION.md`. Usa como encargo actual `docs/research/2026-10-18-revision-profunda/README.md`, auditoría, contrato del asistente, catálogos reales y dirección elegida. La constitución contiene valores de una implementación que el dueño rechazó; tras su elección, actualiza explícitamente las reglas que cambien, conservando sus invariantes. No impongas la propuesta del investigador como aceptación del dueño.

Inspecciona rama, HEAD y cambios existentes antes de editar. Preserva el trabajo de Claude y el golden preexistente. Revisa comportamiento actual; informes históricos y prompts de docs/cola no son una nueva orden. No reinicies ni reseedees el stack del dueño cuando su estado sea necesario.

## Resultado funcional

1. **Asistente global y propio.** Chat y Trabajo; accesible desde cualquier ruta; misma conversación mientras navega; área de conversaciones/historial visible desde el panel; ampliar/minimizar sin perder mensajes/archivos/selección. Reutiliza los jobs y transcripciones ya existentes y define una transición que preserve historial.
2. **Autonomía separada.** Solo proponer, Con aprobación y Omitir todo. En Omitir todo resuelve el encargo reversible autorizado y cuenta al final lo que hizo, sin preguntar cada paso. En Con aprobación prepara un resultado concreto/lote antes de pedirla. No confundas Chat con un nivel de permiso.
3. **IA que termina trabajo.** Preferencia de proveedor MiMo 2.6 Pro, verificada en la API real. Usa contexto y preferencias guardadas. Pregunta solo faltantes imprescindibles, juntos; trabaja sobre lo independiente mientras tanto. No inventa medidas, compatibilidad, costo ni fórmulas. Las operaciones de dominio son las mismas que usa la UI manual.
4. **Resultado honesto y duradero.** Conversación, encargo, transporte, operación y artefacto tienen estados diferenciados. Terminado requiere postcondiciones comprobadas por el servidor. Cliente creado significa entidad vinculada; tres ventanas significa tres posiciones válidas, no un título. Reanuda sin duplicar. Recibo final con objetos, cambios, supuestos y pendientes.
5. **Edición manual profesional.** Todas las aperturas declaradas compatibles funcionan con selección/cara/mano correctas. Identifica y corrige el caso denunciado; no concluyas que está arreglado porque una apertura pasó. Guarda/recarga/deshaz con resultado coherente. Dimensiones, conjuntos, vidrio, herrajes, acabados y 3D conservan identidad y autoridad del motor.
6. **Catálogos reales.** Fabricante → serie/sistema → configuraciones/artículos. Proline PRO6004 y PROSLIDE70 dentro de Proline; no equivalencias por compartir 60/70. Preparar al menos el primer alcance real que permita demostrar el flujo, con fuentes, versión, página, revisión competente y casos del motor. Si la fuente no permite publicar una capacidad, mantenerla como referencia y declarar el bloqueo concreto; nunca rellenarlo con una fórmula inventada.
7. **Biblioteca útil.** Sección/foto/dibujo identificados, documentos fuente y siguiente tarea clara. Separar activo de cotizable/fabricable/CNC. Mantener precios privados. No mezclar Winhouse/Winhaus ni fabricante/distribuidor sin resolver identidad.
8. **Experiencia sin demos de relleno.** Separar fixtures/laboratorio del tenant normal de trabajo, preservando revisiones antiguas. No borrar DB ni renombrar lo sintético como real. Cuenta limpia debe tener un recorrido útil y honesto, no una lista de pruebas internas.
9. **Obra y documento.** Crear cliente/obra/posiciones; elegir valores habituales; validar; calcular; editar visual/textualmente la cotización sin cambiar cifras; vista previa; revisión/emitido; materiales trazables. Cada documento usa destinatario, numeración, identidad y revisión correctos.
10. **Corte, compras y taller.** Organizar por objeto y tarea. Piezas calculadas → existencias → propuesta → revisión → plan → estación. Reconciliar piezas y faltantes. Retazo es existencia física con ubicación/reserva. QR comercial, componente y unidad tienen destinos y permisos distintos. Mostrar al rol actual una acción permitida o responsable/siguiente paso, nunca una orden imposible de ejecutar.

## Calidad de diseño

Implementa la dirección elegida como sistema de producto coherente: navegación, composición, jerarquía de botones, selección, estados, tipografía, superficies y densidad. No es un cambio de paleta. El dibujo, documento o resultado es el protagonista según la tarea. Usa las referencias de la investigación para justificar decisiones, sin copiar activos ni fórmulas privadas.

No mantengas la mascota grande y tarjetas actuales por inercia. No reduzcas el editor a una miniatura para hacer espacio a paneles. Color con propósito; aviso y selección no se confunden. Muestra el dato técnico con divulgación progresiva y usa lenguaje del taller. Cada vacío ofrece una salida válida para ese rol; cada estado de carga refleja trabajo real. Incluye accesibilidad, teclado y lectura móvil desde el diseño.

## Invariantes y arquitectura

Motor determinista como única fuente de números; Decimal para mm/dinero; no fórmulas duplicadas en frontend/LLM; RLS/org_id en datos tenant; revisiones emitidas e historia de precios inmutables; idempotencia; efectos externos con clic humano. Omitir todo no salta esas reglas. No ampliar capacidades de la IA a pagos, código o seguridad.

Conserva engine + Django + Supabase/Postgres + Vite/React. El dueño mencionó “Rails”; el contexto anterior apuntaba a Railway: no autoriza migrar a Ruby on Rails ni sustituir Django. Los planes comerciales quedan fuera de este encargo; no rehagas infraestructura existente bajo la promesa de “integrarla después”. Mantén límites de despliegue documentados.

Para APIs modifica backend, regenera OpenAPI y orval; no edites generated a mano. Cambios de fórmula requieren golden; no regeneres goldens para esconder fallos. Importación OCR/IA conserva fuente, candidatos y revisión técnica. No debilites guards/tests para adaptar la evidencia a la implementación.

## Secuencia de trabajo

Entiende el estado real y construye cada recorrido completo. Integra diseño, datos y comportamiento; arregla los defectos que aparezcan. No detengas el trabajo para pedir decisiones rutinarias ya resueltas en la elección del dueño. No pidas permiso para cada archivo o consulta. Las decisiones nuevas realmente bloqueantes se presentan con un resultado revisable y opciones concretas.

Haz verificaciones del área al construir y una campaña integral al terminar, con stack propio/reutilizado de acuerdo con la skill de revisión. No declares versión final mientras queden botones principales ficticios, tareas marcadas completas sin resultado o fuentes técnicas inventadas. Los bloqueos externos reales se documentan con evidencia y alcance; no se disimulan con demos.

## Aceptación final obligatoria

| Caso | Condición de éxito |
|---|---|
| Conversación continua | Proyecto → catálogo → documento → recarga: mismo hilo, adjuntos, encargo y resultados; historial accesible. |
| Tres autonomías | Mismo objetivo produce propuesta, aprobación agrupada o aplicación reversible sin interrupciones, según elección. |
| Encargo compuesto | Cliente y tres ventanas con medidas conocidas quedan vinculados y válidos; precio solicitado vigente; recibo verificable. |
| Falta un dato | Un bloque de preguntas imprescindibles; estado Esperando datos y trabajo independiente preparado. |
| Error y reintento | Falla proveedor/worker, reanuda sin duplicar y no confunde respuesta terminada con objetivo satisfecho. |
| Cancelar/deshacer | Detener conserva estado real; recuperación no pisa edición manual posterior. |
| Aperturas | Matriz de familias admitidas: cara, mano, selección, guardar/recargar, 2D/3D/BOM y rechazo explicado de incompatibles. |
| Bloqueos | Precio aplicado, revisión sellada, cálculo pendiente y ancho pequeño tienen mensajes y caminos específicos. |
| Catálogo real | Marca/serie/artículo/fuente reconocibles; sin datos sintéticos renombrados, fórmulas inferidas o precios inventados. |
| Cotización | Documento profesional; edición de contenido/estilo no altera números; emisión inmutable y nueva revisión preservada. |
| Materiales/corte | Ninguna pieza requerida desaparece; no ubicadas visibles; retazo identificado y reservado sin duplicación. |
| Taller/QR | Unidad y revisión correctas, requisito y responsable claros; lectura por rol sin fuga de datos. |
| Roles/tenancy | Pruebas negativas reales; asistente hereda permisos; costos privados no llegan a quien no puede verlos. |
| Pantallas | 1440, 1280, 1024 y móvil 390/360: sin controles cortados, foco perdido o acciones esenciales solo al hover. |
| Cuenta normal | Primer recorrido con datos reales; fixtures separados; vacíos y estados de error útiles. |
| Efectos externos | Emisión/envío/compra/pago no ocurren por una respuesta ni por cambiar autonomía; clic humano verificable. |

Ejecuta checks requeridos del repositorio: lint, typecheck, tests, build y gate de DB/RLS para cambios pertinentes; en un cambio transversal como este, campaña integral. Pruebas de fórmula según invariantes y prueba real de IA con proveedor configurado y límites controlados. No presentes un test offline simulado como prueba real de importación o de MiMo.

Entrega cambios mediante PR con descripción del problema y comportamiento final, evidencia de recorridos, referencias probadas, checks y límites concretos. Deja la app ejecutándose y abre los resultados para revisión del dueño. Actualiza la wiki con hechos actuales, intención, propuesta e investigación separados. No te limites a un plan ni a un informe de archivos modificados: entrega el producto real que cumpla lo anterior.

---

La aceptación de esta implementación todavía no ocurrió. Este prompt fija el criterio para evitar repetir una entrega visualmente limpia pero funcionalmente incompleta.
