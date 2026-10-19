# Planes, créditos y límites: una misma IA con distinta capacidad de uso

18-10-2026 · contrato de dirección y propuesta técnica. Revisión estática de `claude/v1-implementacion`, HEAD `6f78e329`, más cambios locales. No se ejecutaron proveedores, pruebas de producto, pagos ni cambios de suscripción. Este documento no publica una oferta comercial.

## 1. Autoridad y categorías de evidencia

| Categoría | Qué gobierna |
|---|---|
| **Decisión explícita del dueño** | El plan más barato es el cotizador manual completo, sin IA. Todos los planes IA usan MiMo hasta que el dueño decida cambiarlo; aclaró «me refería a créditos». La diferencia principal es capacidad de uso, con orientación proporcional y posibles extras profesionales. Esto no convierte una matriz absoluta de todas las funciones idénticas en una cita del dueño. |
| **Referencia histórica del dueño** | Pagar aproximadamente el doble para disponer del doble de límite es una orientación de proporcionalidad. «Anual 30/49/99/149» es una pequeña referencia; no confirma moneda, precio total anual, mensual equivalente, impuestos, cuotas ni tarifa de lanzamiento. No se convierte en checkout ni se calculan totales a partir de ella. |
| **Hecho comprobado del repositorio** | PRD-03, catálogo puro del motor, billetera, períodos, ofertas y gateway contienen contratos concretos, con divergencias descritas aquí. Que exista una función o un test no demuestra aceptación en ejecución. |
| **Propuesta operativa de este paquete** | Mismo núcleo/calidad MiMo y control en los planes IA, unidades proporcionales de cuota y extras profesionales explícitos de coordinación/operación. Es nuestra matriz de implementación apoyada en la intención del dueño; no una cita literal, nueva oferta aprobada o permiso para migrar contratos. Incluye resolución separada de disponibilidad, reservas y medición trazables. |

La selección vigente es **MiMo 2.6 Pro para todos los planes IA**, hasta una instrucción futura expresa del dueño. «DeepSeek Flash 4.1» es únicamente un candidato futuro mencionado por él: este paquete no valida su nombre comercial, existencia, disponibilidad o compatibilidad ni lo configura. Un cambio de plan, falta de crédito, timeout o bucle de agente no autoriza cambiar modelo/proveedor o hacer fallback silencioso.

La propuesta operativa sustituye la segmentación de IA por «asistencia básica» frente a «delegación avanzada» para las capacidades principales. Documento a posiciones/borrador, cambios de ventanas y comparación/propagación de revisiones pertenecen al núcleo común de la versión y se desarrollan en [05](prompts/05-copiloto.md). La fase [06](prompts/06-planes.md) no puede convertir esos flujos en una IA peor para el plan menor. La coordinación profesional adicional puede ser un extra; los pasos encadenados necesarios para completar cualquier flujo común no lo son.

## 2. Qué existe realmente

| Fuente inspeccionada | Hecho estático | Consecuencia para este encargo |
|---|---|---|
| [PRD-03](../../PRD/PRD-03.md), secciones 3 y 4 | Planes, usuarios, créditos, trial, packs, promesas futuras y fórmula de consumo por tokens | Separar términos existentes de funciones futuras y de la última corrección del dueño. |
| [billing del motor](../../../engine/src/dekopen_engine/billing.py), líneas 46–60 | Precios y cuotas congelados; códigos STARTER/PRO/BUSINESS/BUSINESS_2X | No sustituir importes o cuotas para hacerlos coincidir con una nueva tabla visual. |
| [wallet](../../../backend/billing/wallet.py), líneas 85–130 | Débito entero por auditoría; lotes; consumo por vencimiento; saldo no negativo; Starter/inactivo sin IA | Conservar ledger, lotes, replay y separación entre saldo propio y derecho a usar IA. |
| [lifecycle](../../../backend/billing/lifecycle.py), service_windows/reconcile | Un período anual entrega hasta doce cupos en aniversarios mensuales, con fin de mes anclado; no doce cupos gastables el primer día | Facturación anual y renovación de créditos son relojes distintos. |
| [settlement](../../../backend/billing/settlement.py) y [commerce](../../../backend/billing/commerce.py) | Concesión idempotente tras pago verificado; packs y períodos tienen autoridades separadas | Un retorno de navegador, factura de ajuste o reintento no concede créditos por sí solo. |
| [offers](../../../backend/billing/offers.py), provision/get | Oferta del operador con términos del motor y FX explícito; get comprueba concordancia | Una tabla nueva en frontend no crea una oferta válida. El código tampoco acepta parámetros comerciales arbitrarios enviados por el taller. |
| [service](../../../backend/ai_gateway/service.py), _route/invoke | Selección de ruta por capacidad/organización; no rama de modelo por plan en esa función. Débito actual = route.credits_cost por intercambio exitoso auditado | Mantener calidad común y describir el consumo actual con honestidad. |
| [usage](../../../backend/ai_gateway/usage.py), begin/finish/summary | Reserva capacidad del presupuesto operativo en créditos; conserva tokens y costo físico fuera del rollback de dominio | Esa reserva no es una retención de créditos gastables en la billetera. Costo físico y débito comercial pueden diferir. |
| [usage.month_start](../../../backend/ai_gateway/usage.py), líneas 74–76 | El presupuesto operativo se cuenta por mes calendario de America/Santiago | No presentarlo como si fuera automáticamente la ventana mensual de la suscripción. |
| [configuration](../../../backend/ai_gateway/configuration.py) | Presupuesto y tarifas explícitas por organización/capacidad, credenciales en servidor | No obtener una tarifa contractual del nombre MiMo ni de una cifra comercial encontrada en internet. |
| [activación](../../operations/ACTIVACION.md) | Flow de plataforma existente y activación productiva diferida; cobranza del taller usa una integración distinta | No crear Stripe, confundir ambas credenciales ni iniciar cobros en este trabajo. |

Los [tests de lifecycle](../../../backend/tests/integration/test_shot11_lifecycle.py) describen cupos anuales mensuales, vencimiento y packs; los [tests de operaciones IA](../../../backend/tests/integration/test_ai_provider_operations.py) describen reserva de presupuesto y consumo físico que sobrevive al rollback. Se leyeron como contratos; no se ejecutaron durante esta revisión.

### Catálogo monetario y de créditos vigente en código

Todos los importes de la tabla son **USD de lista netos del contrato existente**, no una oferta nueva. El equivalente mensual anual se obtiene del total anual del PRD; se factura el total anual.

| Código | Mensual existente | Total anual existente | Equivalente mensual anual del PRD | Créditos incluidos por ventana de servicio |
|---|---:|---:|---:|---:|
| STARTER | 39 | 420 | 35 | 0 |
| PRO | 69 | 708 | 59 | 2.000 |
| BUSINESS | 129 | 1.188 | 99 | 6.000 |
| BUSINESS_2X | 149 | 1.548 | 129 | 12.000 |

TRIAL no es otro precio de suscripción: el PRD y la migración de wallet establecen 7 días y 500 créditos **totales**, sin tarjeta. Signup directo a Starter no recibe ese saldo. Al terminar, el producto manual sigue disponible. La activación pagada termina el crédito de trial, sin apilarlo como saldo comprado.

Packs existentes: PACK_1000 = USD 15 / 1.000 créditos; PACK_3000 = USD 40 / 3.000; PACK_7500 = USD 90 / 7.500. Los comprados no vencen; no se renombra su origen ni se les asigna caducidad para forzar una actualización.

PRD-03 enumera 2/3/5/5 usuarios para Starter/Pro/Business/Business 2x, extras y grandfathering. Esa tabla no demuestra que todos esos límites o protecciones se encuentren implementados: en el alcance leído hay campos founding_member en organización/suscripción, pero no se encontró price_locked ni una regla de grandfathering ejecutable. Conservar compromisos y evidencia; no anunciar una garantía automática inexistente ni borrar derechos históricos.

## 3. Divergencias que no deben ocultarse

1. **Recorte de funciones por plan.** PRD-03 reserva comparador/Autopilot futuro a Business. La dirección operativa adoptada sustituye ese corte para las capacidades principales compartidas. No convierte en implementado el certificado doble ciego, un pronóstico o un Autopilot de cualquier alcance.
2. **La tabla actual no es proporcional al precio.** Las cuotas IA vigentes tienen razón 1:3:6. Los precios mensuales 69/129/149 no tienen esa razón; tampoco los equivalentes anuales 59/99/129. No afirmar «doble precio, doble uso» sobre esos contratos. Su migración es comercial, no un cambio de copy.
3. **PRD versus débito actual.** El PRD exige ceil(costo API USD × 200); service.invoke usa el entero route.credits_cost. usage mide tokens/costo por separado. No afirmar que la fórmula del PRD ya cobra en producción ni cambiar silenciosamente el ledger histórico.
4. **Margen no demostrado.** El factor 200 convierte una unidad de costo en créditos, pero no demuestra un margen comercial uniforme. Incluso los packs del PRD tienen relaciones precio/costo referencial distintas. Suscripciones incluyen además el software manual, soporte, comisiones e impuestos. No llamar «margen 2x» a una rentabilidad medida sin esa contabilidad.
5. **Reserva de presupuesto versus billetera.** El control previo actual evita saldo negativo al liquidar, pero su comprobación de saldo antes de HTTP no retiene ese saldo frente a otra operación con clave distinta. La reserva de usage protege un presupuesto configurado; no constituye por sí sola la reserva del saldo comercial. Es un riesgo de llamadas concurrentes sin saldo final suficiente, no evidencia de saldo negativo ya observado.
6. **Dos ventanas distintas.** Los cupos siguen el aniversario del período; el presupuesto operativo actual usa mes calendario Santiago. Cambiar de plan no debe reiniciar caprichosamente ninguno. Mostrar los dos rangos.
7. **Upgrade anual.** lifecycle calcula actualmente el suplemento usando el tiempo restante del período pagado, aunque la entrega se haga mensual. Es una semántica estática concreta; no dar por probado el comportamiento de upgrade anual a mitad de ventana. La campaña 07 debe contrastarlo con su autoridad vigente, sin cambiar una fórmula congelada por intuición.

## 4. Núcleo común de todos los planes con IA

La diferencia principal es **cuánto trabajo se puede consumir**, manteniendo la misma herramienta. El paquete común debe incluir, cuando la operación esté implementada:

- MiMo 2.6 Pro como selección vigente del dueño para todos los planes IA y la misma política de transporte/modelo por capacidad. Solo una decisión futura expresa del dueño cambia esa selección; no existe fallback silencioso ni versión deliberadamente inferior por precio.
- Chat y Trabajo, las tres autonomías, popup/historial, contexto y destino, fuentes, recibos, checkpoints, reanudación y deshacer seguro.
- Documento/listado compatible a posiciones y borrador canónico; comandos y cambios de ventanas/selección; comparación de revisiones compatibles con evidencia y propagación reversible.
- Preparación de catálogo y pasos de coordinación necesarios para completar tareas comunes que realmente existan, con las mismas reglas de autoridad y permiso.
- La misma verificación del motor, privacidad, RLS, validación, profundidad necesaria para cumplir el encargo y recuperación.

IDs comunes propuestos: copilot.chat, copilot.task, ai.document_extract, ai.catalog_draft, ai.batch_transform y ai.plan_compare. No separar document_extract o plan_compare en un tier más inteligente. ai.workflow_delegate y ai.operational_analysis pueden identificar extras específicos de coordinación profesional o análisis especializado, si su alcance adicional y soporte son reales; no deben apropiarse de los pasos necesarios para terminar el núcleo. Un límite técnico por formato/modelo se aplica por igual; un límite de volumen divide el trabajo en bloques recuperables sin degradar cada bloque.

Extras muy profesionales posibles: coordinación operativa especializada entre muchas obras, análisis especializado con datos y método, implantación acompañada, soporte contractual, integración empresarial o conector específico con mantenimiento acordado. Son candidatos, no funciones ni precios aprobados. Cualquier extra futuro necesita resultado y contrato propios, con la misma calidad del modelo y las mismas garantías. No usar como extra: Omitir todo, fuentes, privacidad, historial, undo, modelo mejor, que el agente termine, aperturas, PDF profesional o precisión.

## 5. Cuotas proporcionales y unidades comprensibles

**Propuesta recomendada:** una cuota común de créditos por organización, compartida entre sus usuarios autorizados. Los asientos definen quién puede entrar; no multiplican implícitamente el saldo ni conceden permiso. El mismo intercambio bajo la misma política de consumo usa la misma unidad en todos los planes IA.

Definir una unidad base U de créditos por ventana y un multiplicador entero m: **cuota incluida Q = m × U**. Para mostrar proporcionalidad pueden representarse niveles IA de 1, 2 y 3 unidades; es un ejemplo de estructura, no asignación de cuotas ni ofertas a PRO/BUSINESS/BUSINESS_2X. U y los multiplicadores de lanzamiento se fijan desde una versión comercial autorizada, con consumo real medido. El plan manual tiene Q = 0 y no habilita llamadas.

Si una futura comparación comercial anuncia el doble de precio y uso, comprobar Q2 = 2 × Q1 sobre la misma moneda, impuestos, frecuencia y definición de límite. Un descuento anual no es otro modelo ni reduce la cuota mensual. La frase histórica orienta la claridad comercial; no autoriza una fórmula que recalcula derechos a partir del importe de un webhook o de un campo del navegador.

La cuota incluida es un **otorgamiento mensual**, no un segundo techo que inutiliza créditos de packs comprados. Consumir primero lotes próximos a vencer y luego packs; al agotarse el cupo incluido puede continuar con saldo comprado válido si el plan mantiene IA y el presupuesto del dueño lo permite. Un pack añade saldo, no un plan, un rol o un extra.

Para cada límite declarar: unidad, alcance (organización/persona/job), ventana con fechas, si cuenta uso o concede saldo, política de renovación, procedencia y versión. Separar:

| Dimensión | Tratamiento recomendado |
|---|---|
| Créditos incluidos | Principal diferencia proporcional por unidades. |
| Presupuesto de seguridad del dueño | Tope operativo independiente; aumentar plan no lo aumenta ni lo reinicia. |
| Techo autorizado de un encargo | Protege un trabajo compuesto; cada nueva ronda comprueba remanente. Omitir todo no es gasto ilimitado. |
| Páginas/archivos/volumen de proceso | No prometer equivalencia fija entre página y crédito. Si hay límite comercial, cuantificarlo y permitir bloques con checkpoint; no ocultarlo como «IA básica». |
| Contexto y límites del modelo | Capacidad técnica común; no truncar evidencia o herramientas por precio para producir respuestas peores. |
| Paralelismo/cola | Solo si se define expresamente como capacidad operativa; nunca perder trabajo ni fingir un error para ralentizar un plan. No inventar una cifra ahora. |
| Usuarios/almacenamiento/soporte | Condiciones separadas y explícitas del contrato, conservando los compromisos existentes. No todos los límites se duplican automáticamente. |

En esta implementación, resolver cuotas existentes desde sus fuentes y preparar la política versionada de unidades. No reemplazar las cuotas congeladas por el ejemplo 1:2:3 ni retirar saldo a clientes para fabricar una tabla proporcional.

## 6. Crédito, token, costo y reserva no son lo mismo

| Concepto | Qué representa | Qué no debe afirmarse |
|---|---|---|
| Crédito comercial | Unidad entera del ledger, concedida por trial/período/compra/compensación legítimos | Que es un token, un peso o un saldo retirable de dinero. |
| Tokens y otras unidades del proveedor | Medición física del intercambio realmente informado | Que una página, ventana o mensaje siempre consume lo mismo. |
| Costo de proveedor | Decimal según unidades reales y tarifa explícita sellada | Que equivale al precio cobrado al suscriptor o al margen. |
| Reserva de wallet | Retención temporal de créditos gastables para trabajo admitido | Que ya es un débito final o una nueva billetera. |
| Capacidad del presupuesto operativo | Uso/reservas que limita nuevas llamadas, incluso ciertas fallidas | Que debe coincidir siempre con los débitos comerciales confirmados. |

Para la política actual, registrar explícitamente **legacy_route_v1** como identidad lógica: débito por route.credits_cost. Conservar el entero cobrado y la tarifa/ruta sellada. Esta versión no se convierte retrospectivamente en consumo por tokens.

**Objetivo técnico propuesto, no activado:** una política metered_cost_v1 que use costo físico con tarifa sellada y un factor común K créditos/USD. PRD-03 propone K = 200; no es una tarifa MiMo ni una rentabilidad garantizada. Antes de adoptarlo se necesita validar su economía y aprobar la migración comercial. La fase 06 prepara la separación y mantiene legacy_route_v1 como comportamiento efectivo existente.

En ese objetivo, costo USD = suma(unidades reales × tarifa explícita por unidad), con Decimal. Si la tarifa viene por millón de tokens se normaliza a esa unidad. La política debe incluir categorías realmente facturadas —entrada, salida, caché u otras, cuando existan datos— sin inventar tarifas. Para evitar penalizar el fraccionamiento interno, una operación facturable agrega sus intercambios y redondea a créditos una sola vez al cierre/checkpoint que su contrato declare; no suma redondeos ocultos por cada herramienta. Guardar esa granularidad y el factor en la versión, sin reinterpretar las operaciones legacy por llamada.

Tarifa o uso desconocido permanece **Sin dato**. No cobrar dinámicamente un costo inventado, convertirlo en cero o usar la reserva completa como cargo final sin política expresa. Una ruta legacy puede seguir con su débito fijo autorizado aunque su costo físico sea desconocido; el recibo distingue ambos hechos.

## 7. Admisión, reserva y liquidación

La corrección de concurrencia debe conservar ledger/lotes y añadir retenciones duraderas, si faltan, con org/persona/job/operación, política de consumo y asignación a lotes. **Disponible gastable = saldo utilizable de lotes − retenciones activas**. No modificar credits_balance por fuera de su ledger ni mantener un segundo saldo autoritativo.

1. Resolver derecho IA común, permiso, implementación real, destino/versiones y ventana. Recuperar una respuesta final existente antes de reservar o llamar.
2. En una transacción breve y con orden de locks consistente, admitir solo si queda saldo gastable y presupuesto operativo suficientes. Para legacy_route_v1 la reserva por intercambio es el costo fijo vigente. Un trabajo compuesto reserva/admite por bloques y respeta su techo; no inicia todas sus rondas por haber superado una comprobación inicial.
3. Persistir la admisión y soltar locks antes de HTTP. Evitar que una transacción larga de agente bloquee su propia escritura independiente de consumo.
4. Registrar el intercambio físico aun si después se rechaza una propuesta o se revierte el dominio. Relacionar reserva, uso, auditoría y recibo mediante IDs estables.
5. Liquidar una sola vez el débito que corresponde a la política comercial efectiva; liberar el remanente una sola vez. En legacy, un fallo no se transforma en cargo nuevo porque exista costo físico. Conservar su medición y la semántica vigente de auditoría/débito.
6. Un timeout o worker caído deja un estado recuperable. Si el proveedor puede haber cobrado, marcar uso incierto y conciliar; no liberar/repetir ciegamente por reloj ni anunciar costo cero. La expiración de una retención no autoriza otra llamada automática.

Las retenciones asociadas a lotes que vencen solo cubren intercambios admitidos antes del vencimiento. No habilitan pasos nuevos después del fin de ciclo. El saldo libre vence según su contrato; una retención pendiente se concilia conservando su origen y el remanente liberado después del vencimiento también vence. No convertirlo en pack o en crédito del siguiente mes. La implementación necesita preservar saldo/lotes/ledger durante esa transición, sin extender derechos de uso a partir de una retención huérfana.

Cancelar detiene nuevos pasos y reconcilia lo ya ejecutado. No borra consumo físico ni promete reembolso. Reintentar un resultado completado reutiliza su respuesta y no llama ni debita de nuevo. Una operación inconclusa no se confunde con otra nueva porque se reabrió el popup.

## 8. Ciclos, anualidad y cambios

| Evento | Contrato que se conserva | Propuesta y cuidado de implementación |
|---|---|---|
| Mensual | Cupo de servicio por aniversario; el saldo mensual no usado vence | Mostrar inicio, fin, cuota, usado/reservado y próximo otorgamiento. No usar «30 días» como sustituto del calendario. |
| Anual | Cobro anual; hasta 12 entregas mensuales; mismo cupo mensual del plan | No entregar doce meses al inicio, ni multiplicar el saldo actual por doce, ni anunciar un total anual como si fuera gastable hoy. |
| Trial | 7 días y techo total 500; expiración o pago termina su saldo | Mismo núcleo IA mientras haya derecho/cupo; no usar un modelo peor para el trial. |
| Pack | Crédito comprado no vence; requiere un plan con IA para consumirlo | Starter puede conservarlo sin usar IA; reactivar no crea un segundo pack. |
| Upgrade | Evidencia del proveedor y suplemento idempotente; Flow calcula prorrateo monetario | Mantener la fórmula vigente. Una política futura que prorratee cuota mensual debe usar la ventana de servicio declarada, nunca introducir esa modificación en contratos legacy por accidente. |
| Downgrade/frecuencia/cancelación voluntaria | Efecto en el límite pagado según lifecycle; packs e historia preservados | No cortar prematuramente un período pagado. Entre planes IA, conservar núcleo y cambiar solo los límites/extra válidos al entrar en vigor. |
| Fin de derecho o saldo/presupuesto agotado | No nuevas llamadas no autorizadas; el producto manual continúa | Revalidar también en worker/resume. Si el nuevo plan sigue autorizando la misma tarea y queda presupuesto, no bloquearla solo por llamarse downgrade. |
| Reembolso/compensación | Causa y autoridad excepcionales; historia inmutable | Asiento compensatorio trazable; no editar ledger ni conceder crédito desde un fallo de interfaz. |

El presupuesto calendario del dueño sigue su ventana actual America/Santiago salvo una migración explícita de esa política. La UI muestra esa fecha junto a las fechas de servicio. Cambiar frecuencia, modelo o plan no pone a cero artificialmente el consumo operativo ni borra reservas pendientes.

## 9. Contrato de servidor y presentación

Una resolución canónica entrega al frontend: versión de términos/cuota/consumo, derecho IA común, capacidades realmente soportadas, permisos, extras declarados, cuota incluida y ventana, saldos por origen, reservas y gastable, presupuesto y su ventana, próxima entrega y causas. La autoridad deriva de membresía y contratos persistidos. Ningún org/plan/multiplicador enviado por el cliente concede derechos.

Reason codes separados: sin derecho IA, capacidad no implementada, permiso insuficiente, saldo gastable insuficiente, presupuesto agotado, proveedor ausente, cola/límite técnico y operación incierta. Un caso no se resuelve ofreciendo una compra equivocada. Leer este contrato o historial no consulta al proveedor.

En Empresa/Planes: **Manual completo** y **La misma IA, más capacidad de uso**. Cada plan IA enumera el mismo núcleo; la tabla compara créditos, períodos y extras reales. Todos usan MiMo mientras esa sea la decisión vigente. No vende «IA más inteligente», control completo exclusivo, terminación exclusiva o mejor precisión. Mostrar consumo con sus unidades: saldo disponible, retenido, cupo incluido que vence y packs conservados. El costo del proveedor puede quedar en administración autorizada; no confundirlo con una factura al cliente.

En popup/recibo: resultado, créditos efectivamente debitados y reserva vigente cuando la haya; estimaciones identificadas. El historial de otra persona sigue privado aunque un OWNER administre gasto. Con saldo cero/proveedor ausente se consulta la historia propia. Tras pasar a manual, acceso histórico desde cuenta/trabajos sin reintroducir widgets de IA en el cotizador.

## 10. Compatibilidad y alcance de desarrollo

- Mantener códigos, precios, packs, períodos pagados, asientos y auditoría históricos. Términos nuevos son versionados; no se deducen del monto cobrado ni de la palabra Business.
- Implementar el núcleo común para todos los planes con IA según la dirección operativa de este paquete. Esto no altera importes/cuotas ni habilita IA en Starter; elimina el recorte de capacidades principales por precio.
- Resolver límites existentes y preparar unidades proporcionales para futuras ofertas autorizadas. No activar el ejemplo de multiplicadores ni cambiar PLAN_ALLOWANCES/product_terms para conseguirlo.
- Conservar legacy_route_v1, presupuesto Santiago y lifecycle hasta una migración comercial explícita. Preparar observabilidad y reservas correctas no equivale a activar metered_cost_v1.
- No cambiar Flow/Paddle/Stripe, precios, FX, impuestos, renovaciones o suscriptores. No ejecutar compras de packs ni otorgar saldos de demostración como si fueran pagos.
- Registrar las divergencias del PRD para su conciliación; ninguna fórmula financiera se modifica en una fase de diseño por interpretación de un texto histórico.

Lo pendiente para la activación comercial son parámetros y migraciones: importes, U/multiplicadores aprobados, economía de la unidad, términos de anualidad/descuento, elegibilidad de extras, compatibilidad/grandfathering y política de consumo futura. La implementación continúa con el núcleo común y los límites definidos aquí; no requiere pedir otra elección de diseño ni atribuir al dueño una identidad absoluta de todas las funciones.

## 11. Casos reservados para la campaña 07

Sin ejecutar pruebas de producto durante 01–06, preparar estos casos para 07:

- Manual con cero derecho IA: ambas vistas y flujo completo, sin proveedor ni widgets de IA.
- Todos los planes IA: mismo MiMo vigente/política de selección, tres autonomías y los tres recorridos obligatorios de 05; cambia cuota/volumen, no la calidad del contrato. Sin fallback silencioso; el candidato DeepSeek futuro no se activa.
- Igual uso físico/política implica igual unidad de débito entre planes; resolver cuotas proporcionales con términos de revisión autorizados sin publicar nuevas ofertas.
- Mensual/anual, fin de mes, zona horaria, entrega tardía/repetida y límites de ventanas: una sola concesión; anual no entrega doce cupos al inicio.
- Cupo incluido agotado con pack disponible; pack preservado tras Starter y al reactivar; presupuesto del dueño sigue siendo un tope separado.
- Dos llamadas concurrentes con saldo para una: admitir una y conservar una causa recuperable para la otra; ninguna llamada pagada nueva se inicia sin reserva suficiente.
- Reserva, cancelación, caída de worker, respuesta incierta y vencimiento del lote: sin doble gasto, extensión del crédito ni borrado de medición física.
- Diferencia entre rollback de dominio, débito comercial y costo físico; datos desconocidos siguen desconocidos; replay no cobra ni consulta de nuevo.
- Upgrade anual a mitad de ventana, downgrade entre planes IA, paso a manual y cambio de frecuencia: vigencia correcta, historia conservada y sin ampliación de permisos.
- Núcleo común no es un bypass: otro tenant, rol revocado, extra no contratado y grant falsificado siguen rechazados en backend/worker.

La revisión documental puede comprobar enlaces y consistencia. Las suites, navegador, MiMo real y evidencia de aceptación pertenecen a 07. Este informe no declara ninguna de esas pruebas aprobada.
