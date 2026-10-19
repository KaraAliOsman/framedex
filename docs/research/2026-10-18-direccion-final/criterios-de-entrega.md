# Cuándo se considera terminado

Este contrato se ejecuta en la campaña final, después del desarrollo 01–06. No afirma que estas comprobaciones ya pasaran. El cierre debe describir el ref y árbol servido, tenant/roles usados, entradas, resultados, límites y evidencia seleccionada. Un screenshot demuestra apariencia; no demuestra por sí solo cálculo, persistencia o permisos.

## Candidata definitiva y lanzamiento

La entrega de Claude debe dejar **todo el alcance funcional implementado**, verificado en 07 y ejecutándose para revisión del dueño. Solo pueden quedar pendientes las conexiones/configuración finales de producción de Railway, Supabase y pagos, con código, migraciones y procedimiento preparados según el [prompt maestro](prompt-maestro.md). No se admite posponer flujos, persistencia, auth/RLS, IA, créditos ni lógica de cobro como «integraciones finales». Una fuente técnica imprescindible ausente tampoco es una conexión de producción: mantiene la entrega incompleta para el alcance afectado.

El cierre registra por separado: **candidata completa para revisión**, **aprobación del dueño** y **habilitación de producción pendiente/comprobada**. Solo el dueño otorga su aprobación. Tras ella se conectan los servicios finales, se prueban los circuitos reales del entorno de lanzamiento y se corrigen fallos antes de lanzar. Esas pruebas incluyen arranque/healthchecks/worker, auth/storage/RLS y migraciones en el entorno destino, y circuito de suscripción/webhook/créditos del proveedor configurado, además de los recorridos críticos manuales e IA. Las pruebas de pago se hacen con modo de prueba/sandbox cuando exista; un cobro real requiere autorización específica. No afirmar que estas pruebas ya pasaron por haber validado localmente.

## Puertas obligatorias

Estas condiciones no se compensan con una media alta de diseño:

1. Cifras calculadas por el motor y Decimal; nada inventado por UI, PDF o LLM.
2. RLS, org_id, privacidad de conversaciones y permisos en backend/worker, con casos negativos.
3. Revisiones emitidas, precio/auditoría e identidades físicas preservadas.
4. Idempotencia y concurrencia: reintentar no duplica y deshacer no pisa edición posterior.
5. Efectos externos con clic humano; Omitir todo sigue ese límite.
6. Un recorrido manual completo sobre alcance real revisado, sin IA y sin datos sintéticos rebautizados. Una biblioteca de referencias sin capacidad cotizable no satisface esta puerta.
7. Mesa/Estudio comparten trabajo y ambas funcionan en el plan base.
8. Ninguna acción principal ficticia ni encargo Completado con postcondiciones incumplidas.

Si una fuente privada o de fabricante bloquea la sexta puerta, entregar el alcance desarrollado y la evidencia exacta pendiente. Etiquetar el resultado **bloqueado para aceptación real**, sin llamarlo producto listo para fabricar o desplegar. No inventar el dato para evitar esa distinción.

## Rúbrica del producto manual

Es una rúbrica de aceptación propuesta para esta implementación, no una clasificación de competidores. Escala por fila: 0 no completa; 1 depende de intervención técnica; 2 completa con fricción relevante; 3 completa con claridad y recuperación; 4 completa y comprobada también ante error/concurrencia. NE significa no evaluado, no cero. Acompañar nota con caso/evidencia y cobertura.

| Eje | Peso | Evidencia exigida para el cierre |
|---|---:|---|
| Incorporación y catálogo real | 15 | Marca/serie/fuente, artículo y capacidad clara; primera ventana real sin DEMO. |
| Editor, aperturas y coherencia física | 20 | Selección/cara/mano, dimensiones y compatibles; 2D/3D/BOM del mismo objeto. |
| Mesa/Estudio y continuidad | 12 | Cambio de vista/ruta conserva selección, borrador, undo y formularios. |
| Precio, cotización y revisiones | 15 | Precio vigente, costos privados, documento profesional, edición permitida y emisión inmutable. |
| Materiales, corte y continuidad operativa | 12 | Necesidad y OT distinguidas; piezas reconciliadas, stock/retazos, siguiente paso por rol. |
| Claridad visual y controles | 12 | Jerarquía, selección, campos, foco, texto y estados revisados con datos reales. |
| Recuperación, permisos e historial | 10 | Persistencia, 409, respuesta perdida, aislamiento y deshacer seguro. |
| Teclado y tamaños de pantalla | 4 | Recorridos de escritorio y tareas móviles admitidas sin controles engañosos. |

Pesos = 100. Umbral de cierre técnico: puertas satisfechas, todos los ejes evaluados, ninguna fila menor de 3 y ningún fallo crítico/alto sin resolver. No autoconceder un 10/10 ni afirmar aprobación estética del dueño: el producto real se deja abierto para su revisión.

## Rúbrica adicional del copiloto

Solo aplica a los planes con IA. La falta de créditos o proveedor no empeora la aceptación del producto manual. Las autonomías son controles de ejecución para capacidades habilitadas, no beneficios que se venden como «menos seguridad».

| Eje | Peso | Evidencia exigida |
|---|---:|---|
| Resultado del encargo | 30 | Postcondiciones del servidor y objetos válidos, no solo texto o enlaces. |
| Popup, personaje y continuidad del hilo | 15 | Sin columna reservada; navegar, cerrar/abrir y recargar conserva trabajo privado. Figura y movimiento fieles a la referencia Grok Bot según 06, ligados al job real y accesibles. |
| Chat/Trabajo y tres autonomías | 15 | Diferencia observable entre propuesta, aprobación agrupada y ejecución reversible sin pausas. |
| Fallos, reanudación y concurrencia | 15 | Checkpoint y reintento sin duplicación; edición manual protegida. |
| Contexto, preguntas y recibo | 10 | Destino fijo; faltantes agrupados; recibo verificable sin especulación. |
| Capacidades, presupuesto y proveedor real | 10 | Gates de servidor y worker; MiMo real; costo/reserva/consumo distinguibles. |
| Permisos y efectos externos | 5 | Sin ampliación de rol; clic humano para consecuencias externas. |

Pesos = 100; mismo umbral y evidencia. Los criterios de proveedor real no se satisfacen con un stub. Los tests deterministas siguen siendo útiles para errores y aislamiento, pero no sustituyen ese recorrido.

## Casos finales concretos

| ID | Recorrido | Condición verificable |
|---|---|---|
| M01 | Cuenta/empresa preparada sin derechos IA → primera obra. | No hay llamadas al proveedor, banners obstructivos ni campo que exija IA. Cliente se vincula como entidad. |
| M02 | Catálogos → Proline → serie → artículo/fuente. | Jerarquía reconocible, código exacto, sección útil, versión/página; DEMO fuera del recorrido habitual. |
| M03 | Añadir/configurar/guardar una ventana real. | Fuente y reglas revisadas; guardar/recargar conserva diseño y resultado válido del motor. |
| M04 | Mesa → Estudio → editor amplio → Mesa. | Misma selección/obra/revisión, filtros y retorno; no duplica posición ni borra undo o borrador. |
| M05 | Cambiar mano/cara/apertura en familias soportadas. | Tabla de casos según autoridad publicada; apertura compatible persiste, incompatible explica causa. No inventar familias para completar una captura. |
| M06 | Comparar 2D/3D/BOM/documento. | Módulos, carriles, movimiento, manilla, medidas y acabados coherentes desde la cara indicada. |
| M07 | Precio aplicado/revisión emitida/cálculo pendiente/ancho pequeño. | Causas distintas con siguiente paso permitido; no desbloquear escritura para ocultar el problema. |
| M08 | Lote de posiciones y comparación manual. | Alcance explícito, diff, aplicar, undo seguro; comparar no requiere generar con IA. |
| M09 | Revisar precio y cotización; editar presentación; emitir sucesora. | Números canónicos, costos protegidos, PDF legible, primera revisión intacta, numeración/cliente correctos. |
| M10 | Necesidad → stock/retazos → corte → estación. | Misma revisión/OT; requeridas = ubicadas + no ubicadas; reservas sin duplicación y explicación del faltante. |
| M11 | QR comercial, pieza y unidad. | Cada uno abre objeto y alcance correctos; no revela otro tenant ni usa un QR genérico para todo. |
| M12 | Compras/recepción parcial/terreno en los recorridos afectados. | Cantidades y estado reales, acción por rol, ningún stock o compromiso inventado por diseño. |
| M13 | Borrador sin guardar → otra posición → recarga/409. | Guardar/Descartar/Cancelar; recuperar solo con identidad demostrable; conflicto conserva el trabajo humano. |
| A01 | Abrir/cerrar popup con editor e inspector abiertos. | No encoge lienzo ni cierra inspector; foco vuelve al invocador; cierre no cancela trabajo. |
| A02 | Chat → preparar → Hacer en Trabajo. | Chat no muta; transferencia en mismo hilo con contexto/archivos/destino visible. |
| A03 | Mismo objetivo en tres autonomías. | Propuesta sin aplicar; un lote con aprobación; Omitir todo ejecuta sin aprobaciones intermedias reversibles. |
| A04 | Crear cliente + tres posiciones + borrador de cotización. | Usar medidas/serie/costos conocidos; tres posiciones válidas vinculadas; estado final según postcondiciones. |
| A05 | Mismo objetivo con dimensión imprescindible ausente. | Pregunta agrupada, trabajo independiente comprobable, Esperando datos/Parcial; nunca Completado 0/3. |
| A06 | Navegar a otra obra durante ejecución. | Hilo continúa; no redirige escritura al contexto nuevo; recibo vincula objetos originales. |
| A07 | Timeout/worker/proveedor/cancelar/reanudar. | Estado persistido, sin duplicados/cobros duplicados; lo aplicado y lo pendiente se distinguen. |
| A08 | Edición manual posterior y deshacer IA. | No sobrescribe ni restaura versión vieja; ofrece salida concreta ante conflicto. |
| A09 | Revocar rol/downgrade/agotar presupuesto. | Revalidación en backend/worker; bloquear llamadas/efectos que ya no estén autorizados y todas las nuevas llamadas si se agotó presupuesto. Historial legible y manual disponible por sus permisos. |
| A10 | Preparar emisión/envío/publicación. | Resultado listo y clic humano específico; autonomía no amplía permiso. Usar entorno de revisión, sin efectos reales no solicitados. |
| A11 | Documento/listado o plano con cotas → posiciones y PDF borrador. | Evidencia por campo, IDs reales, cálculo/BOM/precio cuando sus datos estén completos y PDF canónico accesible; reintento sin duplicación. Probar una ambigüedad y un faltante. |
| A12 | Cambiar medidas/apertura/vidrio/acabado/cantidad sobre selección explícita. | Mismas operaciones que manual; resultados coherentes en Mesa/Estudio, políticas aplicadas y control de concurrencia/deshacer. |
| A13 | Dos revisiones compatibles → diferencias → borrador actualizado. | Correspondencias explícitas, altas/bajas/cambios con fuente anterior/nueva; ambiguos pendientes; recálculo y emitidos intactos. |
| A14 | Personaje en reposo, cola, pensamiento, trabajo, espera, revisión, éxito y fallo. | Comparación con referencia 06: silueta/ojos/ritmo; transiciones continuas; pausa oculta y reduced motion; no repite éxito tras recarga ni consume proveedor por animar. |
| B01 | Mismo encargo en todos los planes con IA. | Mismo MiMo vigente, herramientas principales y tres autonomías. Cambia capacidad de consumo; ningún fallback silencioso o modelo peor por precio. |
| B02 | Cupo incluido, pack, presupuesto y reserva. | Origen, fechas y saldo gastable claros; agotar cupo permite usar pack válido bajo derecho/budget. Starter conserva packs sin poder llamar IA. |
| B03 | Anualidad y doble renovación. | Hasta doce entregas mensuales idempotentes; no doce cupos disponibles el primer día. Contrastar aniversarios/fin de mes con presupuesto calendario Santiago. |
| B04 | Dos llamadas concurrentes con saldo para una; timeout incierto y cancelación. | Admisión/retenciones duraderas, ninguna llamada nueva sin saldo reservado, liquidación/replay sin duplicación; consumo físico no desaparece con rollback de dominio. |

A11–A13 son recorridos obligatorios del prompt 05 y comunes a todos los planes con IA. Para cada uno registrar proveedor real, resultado, pasos humanos, correcciones necesarias y consumo medido. No se aceptan como funciones terminadas por tener un ID registrado, una demo o supported=false. Los importes, multiplicadores de lanzamiento y activación comercial siguen pendientes; no bloquean construir/revisar el núcleo común y los límites legacy mediante grants legítimos de plataforma. B01–B04 siguen el [contrato de créditos](04-planes-creditos-y-limites.md), sin publicar ofertas, ejecutar cobros ni cambiar saldos históricos.

Usar OWNER/ESTIMATOR/operario y un usuario de otra organización donde el alcance lo necesite. Reutilizar la fixture y cuentas de revisión de la skill, sin mezclar prueba con datos comerciales del dueño. No ampliar a familias, máquinas o proveedores sin evidencia para inflar cobertura.

## Adjuntos: casos adicionales A15–A17

La [ampliación de adjuntos](03-copiloto-y-planes.md#adjuntos-multimodales--ampliación-explícita-del-dueño) pertenece a la candidata y al núcleo común de todos los planes IA. No basta admitir la extensión en un selector. Registrar en la entrega una matriz por formato/tarea, límites del pipeline y cobertura realmente comprobada; los formatos mínimos del contrato deben funcionar.

| Caso | Acción | Resultado observable |
|---|---|---|
| A15 | Adjuntar varios archivos desde popup; preview, retirar uno, navegar, minimizar y recargar. | Persisten fuentes subidas y vínculos al turno correcto; subida interrumpida visible. Abrir/ver/recuperar no llama MiMo. Citas abren original/región tras caducar URL temporal; sin acceso cruzado ni compartir el hilo automáticamente. |
| A16 | Usar ejemplos de PDF textual, escaneado y mixto, PNG/JPEG/WebP, XLSX/CSV, DOCX y TXT/Markdown. | Contenido útil llega a Chat/Trabajo; celdas/párrafos/regiones trazables. Cubrir documento que exige varios lotes, ilegible, protegido/no soportado y límite excedido. No se omite contenido silenciosamente ni se declara lectura completa con cobertura parcial. Consumo/reserva/reintento se concilian. |
| A17 | Encargo con fuentes contradictorias, dimensión ausente e instrucciones maliciosas dentro de un archivo. | La evidencia se conserva, usa autoridad establecida o agrupa la excepción material y continúa lo independiente. No inventa mm/precios, no sigue instrucciones del archivo que amplían alcance, no publica catálogo ni produce efectos externos por adjuntar. Las tres autonomías mantienen estos límites. |

Las bibliotecas entre conversaciones, el análisis transversal de fuentes y el marcado libre del dibujo siguen siendo recomendaciones de innovación. Estos casos verifican el alcance explícito de adjuntos y los tres recorridos ya comprometidos.

## Calidad visual y evidencia seleccionada

Revisar en 1440, 1280 y 1024 px las tareas de escritorio; 390 y 360 px las tareas móviles admitidas. En anchos donde el CAD conserva lectura técnica, la UI debe declararlo y permitir el resto de tareas móviles. Inspeccionar con teclado y zoom. El popup no debe quedar fuera de viewport ni tapar irrecuperablemente la acción Guardar.

Cubrir al menos: Mesa poblada y vacía, Estudio con selección/apertura, marca/serie con fuente y faltante, documento con varias páginas, materiales/corte por rol y copiloto abierto/minimizado/ampliado con resultado/error. Añadir nombres largos, sin precio, campo inválido y una colección grande realista mediante datos de prueba explícitos. No hace falta crear una suite nueva que replique CSS para cada control.

Cada hallazgo registra problema, impacto, causa, corrección y evidencia después. Prioridades: crítico = seguridad/cifra/historia/efecto externo; alto = no termina recorrido o pierde trabajo; medio = fricción o ambigüedad relevante; bajo = pulido. Críticos y altos cerrados antes de anunciar entrega. Los medios que afectan los ejes deben corregirse para alcanzar 3; la preferencia estética final pertenece al dueño.

## Checks y entrega

Ejecutar en la campaña final `make lint`, `make typecheck`, `make test`, `make test-db`, `make test-mutations` y `make build` conforme al repositorio y al entorno disponible. Inspeccionar y corregir errores sin debilitar guards, tests, RLS o umbrales. Si el entorno bloquea un check, registrar comando, causa y alcance no comprobado; no marcarlo aprobado ni afirmar cierre integral. Tras corregir, repetir lo afectado y los checks necesarios para recuperar confianza; no repetir baterías sin nueva causa.

Resultado de entrega: diff/PR revisable, registro de implementación, matriz de casos con evidencia, límites de fuente/capacidad, configuración pendiente de despliegue y app abierta. Incluir URL, rama, SHA y cambios locales que sirve el stack; explicar si fue reconstruido. La aceptación de producto no equivale a homologación de máquina, certificación térmica ni autorización de fabricación de fuentes incompletas.
