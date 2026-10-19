# Fase 06 - Núcleo IA común, créditos y límites proporcionales

Implementa esta fase sobre C:/Users/alios/Downloads/framedex, preservando el trabajo local. No actives contratación ni cambies precios, cuotas congeladas o suscripciones. Desarrolla primero; las pruebas de producto y proveedor real de todas las fases se concentran en 07.

Lee AGENTS.md, el prompt maestro, 03-copiloto-y-planes.md, [04: planes, créditos y límites](../04-planes-creditos-y-limites.md) y prompts/05-copiloto.md de este paquete. El dueño quiere un plan manual completo sin IA y diferencias proporcionales de uso entre los planes IA, con posibles extras profesionales. Nuestra propuesta operativa es un mismo núcleo/calidad MiMo y control, más capacidad de consumo y extras explícitos; no atribuyas esa matriz completa como una cita literal o nueva oferta comercial aprobada.

Queda sustituida la segmentación anterior de «asistencia básica» frente a «delegación avanzada» para las capacidades principales. No retengas el comparador, las tres autonomías o la capacidad de terminar una tarea para vender una IA inferior. La coordinación profesional adicional puede ser un extra con un contrato propio; la coordinación necesaria para completar los tres recorridos de 05 pertenece al núcleo.

## Hechos y autoridad que debes preservar

PRD-03 y engine/src/dekopen_engine/billing.py tienen STARTER/PRO/BUSINESS/BUSINESS_2X, cuotas 0/2000/6000/12000 y términos monetarios congelados. El trial tiene 7 días/500 créditos totales. Los importes históricos y la referencia «anual 30/49/99/149» no autorizan nuevas tarifas ni permiten inferir total anual, moneda o cuota.

El código actual debita route.credits_cost por intercambio; PRD-03 describe ceil(costo API USD × 200). usage mide además tokens/costo físico y reserva capacidad del presupuesto en créditos, no saldo de wallet. Su presupuesto sigue el mes calendario America/Santiago; lifecycle entrega cupos por aniversarios mensuales, incluso con factura anual. No presentes estas implementaciones distintas como si ya fueran una sola política medida por tokens.

La ruta actual se elige por capacidad/organización, no necesita un modelo peor por tier. Flow, billetera, ledger, lotes, períodos y replay ya existen. Reutilízalos. La activación de pagos permanece separada. No crees Stripe, otra billetera ni un motor financiero paralelo.

## 1. Base manual completa

Conserva sin degradación, bajo permisos y autoridad física: catálogos manuales; empresa/clientes/obras; posiciones, aperturas y medidas; Estudio y Mesa sobre el mismo estado; 2D/3D, revisiones y deshacer; motor/BOM/precios; composición y PDF; cortes deterministas, stock, compras, taller y terreno.

No hagas premium la precisión, el PDF profesional, las aperturas que funcionan, una vista manual, seguridad o recuperación. Falta de datos técnicos es falta de autoridad, no motivo para comprar IA.

En el manual no montes popup, presencia, polling ni widgets IA, columnas vacías, banners obstructivos o chips bloqueados en cotización/editor. La comparación comercial puede vivir en Empresa/Planes. Si la persona conserva conversaciones de un plan anterior, ofrece acceso de lectura al historial propio desde cuenta/trabajos sin montar el lanzador ni habilitar nuevas llamadas.

Tener un plan IA tampoco abre el copiloto al entrar, navegar o cambiar vista/selección. Consultar historial, recibos, capacidades y resultados existentes, o trabajar manualmente, no consulta al modelo ni gasta créditos.

## 2. Núcleo común y extras definidos

Implementa un registro canónico del servidor. Núcleo común propuesto, con soporte real:

- copilot.chat: conversación contextual con fuentes.
- copilot.task: trabajo completo sobre el alcance delegado.
- ai.document_extract: documento compatible a candidatos, posiciones y borrador real.
- ai.catalog_draft: preparación de candidatos con evidencia, sin publicación automática.
- ai.batch_transform: cambios validados sobre ventanas/selección.
- ai.plan_compare: comparación de revisiones compatibles y propagación reversible.

Todos los planes con IA acceden al mismo núcleo implementado, con sus permisos y límites efectivos. Los tres recorridos de 05 son obligatorios de esta versión: no cierres su desarrollo con supported=false ni los relegues al nivel caro. Trial usa la misma calidad mientras tenga derecho y saldo.

Mantén MiMo 2.6 Pro como selección vigente explícita del dueño para todos los planes IA, hasta que él decida cambiarla, y la misma política de transporte/modelo por capacidad. No cambies ante un fallo, falta de saldo o por tier; no uses fallback silencioso. «DeepSeek Flash 4.1» es solo un candidato futuro mencionado por el dueño: no valides su nombre/disponibilidad ni lo configures ahora. No asocies a un tier un modelo menor, menos herramientas, un contexto mutilado o menos verificación. Los límites técnicos reales del formato/proveedor son comunes. Dividir un lote por volumen conserva la calidad y la capacidad de reanudar cada bloque.

Chat/Trabajo, Solo proponer/Con aprobación/Omitir todo, historial, citas, privacidad, destino, checkpoints, recibo y deshacer seguro son estándar común. No se cobra por omitir aprobaciones rutinarias ni se introduce fricción artificial en el plan IA menor.

Para extras futuros, usa IDs separados y resultado concreto. ai.workflow_delegate o ai.operational_analysis pueden describir coordinación profesional adicional entre muchas obras o análisis especializados, si tienen soporte y contrato explícitos. No uses esos IDs para bloquear los pasos encadenados que necesita cualquier tarea común o uno de los tres recorridos obligatorios. Una llamada al modelo no puede autoetiquetarse como un extra para ampliar derechos.

No publiques extras ficticios: pronóstico sin datos/método, certificado sin autoridad, conector industrial sin homologación o agente que solo escribe texto. Cuando un extra no exista, informa su falta; esa honestidad no excusa dejar incompleto el núcleo requerido. Conserva derechos legítimos existentes: no retires una función ya concedida porque su nuevo nombre parezca premium.

## 3. Resolución única de capacidades, límites y disponibilidad

Añade GET /api/v1/capabilities/ con autenticación y organización activas verificadas. No acepta org/rol/plan/multiplicador como autoridad desde el cuerpo. Regenera OpenAPI/orval; el cliente generado no se edita a mano.

La resolución distingue:

- Derecho a IA: manual sin IA o núcleo IA común; origen/vigencia verificados.
- Supported: soporte técnico real por capacidad y formato.
- Permission/scope: acciones y objetos permitidos al actor.
- Extras: grants específicos legítimos, cuando existan.
- Límites: unidad, cuota incluida, alcance, ventana, versión y procedencia.
- Saldos: por origen, total utilizable, reservas activas y gastable.
- Presupuesto operativo: tope, consumo/reservas y sus propias fechas.
- Availability/reason_code: proveedor, saldo, presupuesto, cola o estado incierto, separados de contratación y permisos.
- Terms_version, quota_policy_version y consumption_policy_version: suficientes para invalidar caché y atribuir una operación a su contrato.

Los nombres exactos de campos se cierran en el esquema común; no mantengas objetos ad hoc diferentes por pantalla. No expongas claves, prompts privados, tarifas secretas ni datos ajenos.

No colapses todo a ai_available. Una capacidad contratada con saldo cero sigue contratada. Proveedor ausente no es plan insuficiente. Falta de permiso no se arregla comprando créditos. La lectura de resolución no prueba credenciales, llama al proveedor, concede créditos, reinicia ventanas ni crea una suscripción.

El frontend solo refleja esta autoridad; gates del servidor y worker se aplican igualmente aunque el cliente conserve un resultado antiguo.

## 4. Cuotas proporcionales sin migración comercial implícita

Implementa una política de límites versionada que pueda resolver cuota Q = m × U, con unidad y multiplicador enteros autorizados. La estructura ilustrativa 1/2/3 unidades del contrato 04 no son ofertas nuevas ni mapeo automático de PRO/BUSINESS/BUSINESS_2X. Leer parámetros desde la autoridad comercial persistida, nunca calcular derechos dividiendo el importe pagado.

Ahora devuelve y conserva los cupos vigentes 0/2000/6000/12000. La tabla actual no es proporcional a sus importes; no anuncies que ya cumple «doble precio, doble uso». Preparar el resolvedor proporcional no habilita cambiar PLAN_ALLOWANCES/product_terms, ofertas o clientes existentes. Los nuevos valores y su migración comercial quedan documentados para activación posterior, sin pedir otra elección de diseño.

La cuota incluida es un otorgamiento por ventana, no otro tope que bloquee saldo comprado. El saldo de la organización es compartido por sus actores autorizados; añadir usuario no concede más créditos ni permisos. Un pack añade saldo conservando su origen, no un plan o un extra. Starter conserva packs pero no ejecuta IA.

Si se aprueban límites de páginas, volumen, concurrencia o almacenamiento, cada uno declara unidad, ventana y si escala con el multiplicador. No inventes números ahora ni prometas que todos los límites se duplican. El volumen se procesa por bloques recuperables; no recortes la profundidad necesaria para cumplir el encargo.

Solo la autoridad de plataforma o un evento comercial verificado puede otorgar derechos/límites. Un OWNER de taller puede restringir su presupuesto, no autoelevar el plan o asignarse un extra. Para revisión usa grants explícitos del operador, auditados y aislados, nunca bypass por DEBUG o campos del cliente.

## 5. Reservas y consumo con compatibilidad financiera

Conserva la política efectiva de débito fijo por route.credits_cost. Identifícala como legacy_route_v1 —o un identificador equivalente único— y sella su versión, ruta e importe por operación. No cambies el histórico ni actives una fórmula por tokens desde esta fase.

Mantén separados créditos debitados, capacidad del presupuesto operativo, retenciones de saldo, tokens y costo de proveedor. Este último usa Decimal y tarifa explícita sellada; Sin dato no es cero. Una operación física fallida o una propuesta revertida puede tener costo de proveedor sin un débito comercial final: no cambies esa regla legacy por confundir ambas contabilidades.

Corrige la admisión concurrente. La comprobación actual de saldo antes de HTTP no lo retiene frente a otra clave. Reutiliza ledger/lotes y añade, si falta, reserva duradera de créditos gastables relacionada con usuario/job/operación/lotes. No construyas un segundo saldo: gastable = saldo utilizable menos reservas activas. En legacy, retén el costo fijo vigente antes de admitir cada intercambio, junto a la comprobación del presupuesto operativo.

La admisión sucede en transacción breve con locks de orden consistente, fuera de la transacción larga de dominio; HTTP va sin locks financieros abiertos. Evita que la escritura independiente de consumo espere a un lock que retiene su propio agente. Persistir medición física y reserva debe soportar caída del proceso sin depender del popup.

Liquida/reutiliza/libera una sola vez según el resultado y la política vigente. Un resultado final se recupera antes de crear una nueva reserva. Un timeout incierto no libera y repite automáticamente una llamada quizá cobrada; conserva causa y vía de conciliación. El recibo no promete costo cero ni devolución donde no hay evidencia.

Las retenciones no alargan la vida de créditos mensuales para iniciar nuevos pasos. Conservan el origen de los intercambios ya admitidos; vence saldo libre y concilia lo retenido. El remanente liberado después de su vencimiento también vence. Sigue el contrato 04 para mantener ledger/lotes consistentes, sin convertirlo en crédito fresco ni en pack.

El trabajo compuesto comprueba saldo/budget/techo en cada nueva ronda. Omitir todo no aumenta el techo autorizado. Presupuesto o saldo insuficiente guarda checkpoint y permite continuar manualmente; no abre checkout, compra packs, aumenta presupuesto o cambia modelo para abaratar por su cuenta.

El objetivo metered_cost_v1 del documento 04 queda como propuesta versionada pendiente de aprobación económica/migración. El factor 200 de PRD-03 no demuestra margen ni fija tarifa MiMo. No lo actives, cambies redondeo o conviertas débitos legacy en tokens para hacer coincidir la narrativa. La implementación actual puede quedar completa con reservas correctas, medición honesta y política legacy explícita.

## 6. Ciclos y cambios de plan

Conserva lifecycle como autoridad de períodos y su conciliación idempotente. Facturación anual significa un cobro anual y hasta doce entregas mensuales por aniversario; no crédito anual gastable por adelantado. Mantén anclaje de fin de mes y zona del período; no sustituir por intervalos de treinta días.

El crédito mensual no usado vence; los packs comprados no vencen y se consumen después de los lotes que caducan antes. El trial conserva 7 días/500 totales, termina al expirar o activar pago y no se apila con el cupo pagado.

El presupuesto operativo actual sigue mes calendario America/Santiago. Devuelve esa ventana aparte de la de servicio. Cambiar tier/frecuencia no reinicia consumo, extiende trial ni borra reservas. Un plan mayor no aumenta el presupuesto puesto por el dueño.

Upgrade requiere evidencia del proveedor y suplemento idempotente; Flow resuelve prorrateo monetario. Conserva la fórmula financiera vigente, incluida su semántica de período. Registra el caso de upgrade anual para 07; no lo cambies a otra fórmula de prorrateo porque parezca más intuitiva.

Downgrades/frecuencia/cancelación voluntaria respetan el fin del período pagado. Entre planes IA sigue disponible el mismo núcleo, con nuevos límites efectivos cuando corresponda. A Starter no se admiten nuevas llamadas, pero conserva manual, historial y saldo comprado. Si el nuevo plan aún permite una tarea y hay presupuesto, no la rechaces solo porque hubo downgrade.

Conserva eventos, compensaciones, precios y fuentes históricas. No anunciar implementación total de grandfathering por tener founding_member: registra la diferencia entre promesa del PRD y código observado y prepara su conciliación comercial sin alterar suscriptores.

## 7. Gates en todo camino y recuperación

La autorización de un efecto combina membresía/tenant, permiso de dominio, derecho IA común o extra real, política delegada, autoridad/versiones y saldo/presupuesto/proveedor. Aplícala en POST y reanudación, invoke, diseño/contexto/catálogo, enqueue, worker, herramientas, aplicar y reintentar.

No basta ocultar botones o comprobar solo agent. El registro conoce el efecto real de cada herramienta; el modelo no elige un ID para colar una mutación, cambiar de plan, invadir otra obra o usar un extra. La capacidad manual se autoriza por su propio servicio y no necesita saldo IA.

Revalida al ejecutar/reanudar y antes de efectos. El cambio de preferencia de autonomía solo afecta tareas nuevas; no reinterpreta la autorización sellada del job en curso. Revocación de rol/derecho o vencimiento puede impedir nuevos pasos; conserva los checkpoints y presenta recibo fiel.

Historial y resultados propios se leen sin llamadas ni saldo. Aplicar manualmente una propuesta almacenada o deshacer el cambio propio usa el servicio manual con rol/versión/auditoría, sin comprar IA. Documentos emitidos y ediciones posteriores están protegidos en todos los planes.

## 8. Presentación de planes y uso

Consume el contrato único en AppShell, popup, acciones contextuales e importación. Segmenta caché por organización/persona/versiones y limpia al cambiar identidad; nunca adoptes datos del tenant anterior.

En Empresa/Planes usa «Manual completo» y «La misma IA, más capacidad de uso». La tabla de planes IA muestra el núcleo común, créditos incluidos/ventana y extras reales, sin vender IA más inteligente, mejores aperturas, más control o un modelo superior por precio. No uses «básico solo pregunta / caro sí trabaja».

Muestra cuota incluida y próxima entrega, saldo que vence, packs conservados, reservas y saldo gastable; presupuesto con sus fechas. Separa estimación de cargo final. Los usuarios ven sus datos permitidos; administrar consumo no abre conversaciones privadas de otra persona.

Proveedor y presupuesto conservan permisos OWNER/MFA y credenciales de servidor. El usuario recibe causas y acciones útiles, sin exponer transportes o secretos. El valor se demuestra con los tres resultados reales de 05 en todos los planes IA, volumen ampliado y extras verificables, no con un simulacro premium.

## 9. Límites comerciales y cierre de desarrollo

No crees productos o precios en Flow/Stripe/Paddle, ni enlaces reales de pago, packs, suscripciones, autopago, ajustes FX/impuestos o cambios de renovación. No modifiques importes, cuotas congeladas o saldos para simular el ejemplo proporcional. Contratación futura necesita tabla y economía aprobadas, términos versionados, compatibilidad/grandfathering, sandbox y activación humana.

Fuentes: engine billing; backend/billing/wallet.py, lifecycle.py, offers.py, commerce.py, changes.py, settlement.py; ai_gateway/service.py, usage.py, configuration.py, handlers.py y herramientas; frontend AppShell/asistente/billing; migraciones RLS. Mantén Decimal, inmutabilidad, idempotencia y cliente API generado desde backend. No debilites guards.

No ejecutes suites, E2E, navegador, MiMo, pagos ni carga ahora. Prepara para 07:

- Manual completo en Mesa/Estudio, cero solicitudes al proveedor y cero widgets/polling IA.
- Todos los planes IA completan los tres recorridos de 05 con mismo núcleo/modelo/control y sus cuotas propias; no una IA menor por precio.
- Tres autonomías en el plan IA menor y en el mayor, sin diferencias de seguridad o fricción artificial.
- Resolver proporciones con términos auditados de revisión, sin activar nuevas tarifas ni cambiar cuotas legacy.
- Cupo incluido, pack y presupuesto separados; igual unidad de débito bajo igual uso/política en distintos planes.
- Dos admisiones concurrentes con saldo para una; reserva/liberación/liquidación/replay sin doble llamada ni débito.
- Vencimiento de lote con reserva; timeout incierto; rollback de dominio con medición física persistida.
- Mensual/anual, aniversario/fin de mes/zona, doce entregas separadas, renovación duplicada y upgrade anual.
- Downgrade IA a IA y a manual; revocación durante queue/run/resume; historial y packs conservados.
- Rol sin derecho, derecho sin rol, proveedor ausente, saldo/budget cero, otro tenant y extra real no concedido.
- El cliente no amplía cuotas, permisos o plan; navegar no cambia ofertas ni concede créditos.

Entrega archivos, contrato de resolución/límites, compatibilidad efectiva, política de consumo vigente, divergencias comerciales y escenarios pendientes de 07. No declares capacidad premium validada, nueva oferta publicada, cobro activo ni lanzamiento por terminar esta fase.
