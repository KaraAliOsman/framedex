# Activacion de integraciones externas diferidas

Este indice no contiene secretos. Los valores reales se cargan como variables de entorno en el proveedor de despliegue o en el entorno local protegido.

## Railway / hosting

| Campo        | Detalle                                                                                                                                                               |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Estado       | No conectado en este programa local.                                                                                                                                  |
| Adaptador    | Configuracion de servicios `railway*.toml` y variables de entorno de Django/Vite.                                                                                     |
| Variables    | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `CORS_ALLOWED_ORIGINS`, `ALLOWED_HOSTS`, `SECRET_KEY`, `RAILWAY_GIT_COMMIT_SHA`.    |
| Activacion   | Crear proyecto Railway, conectar repo, configurar servicios frontend/backend/worker, cargar variables por ambiente y ejecutar migraciones/seed segun runbook vigente. |
| Verificacion | `GET /health/ready/`, login real, emision de DOC-01 sandbox y revision de logs backend/worker sin errores.                                                            |

## Flow

| Campo        | Detalle                                                                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Estado       | Diferida; usar sandbox hasta aprobacion del dueno.                                                                                               |
| Adaptador    | `backend/billing` con proveedor Flow configurado por entorno.                                                                                    |
| Variables    | `FLOW_API_URL`, `FLOW_API_KEY`, `FLOW_SECRET_KEY`, `BILLING_CALLBACK_ORIGIN`, `BILLING_FRONTEND_ORIGIN`, `FLOW_MERCHANT_TIMEZONE`.               |
| Activacion   | Crear comercio sandbox, cargar llaves, configurar URL de retorno/callback, ejecutar pago de prueba y luego repetir con credenciales productivas. |
| Verificacion | Crear enlace de pago, completar pago sandbox, confirmar idempotencia de callback y estado visible en proyecto/portal.                            |

La cobranza del proyecto usa sus propias credenciales, guardadas por el dueño
en **Ajustes › Flow** (`org_payment_integrations`). Las variables `FLOW_*`
del servidor pertenecen a la billetera de la plataforma; no habilitan el cobro
de una fábrica. Configure en backend `BILLING_CALLBACK_ORIGIN` con HTTPS público
y `BILLING_FRONTEND_ORIGIN` con el frontend, o declare el retorno del pagador
en la integración de la organización. La creación entrega a Flow el callback
`/api/v1/projects/flow/confirm/<enlace>/` y el retorno `/pago/retorno`.

1. Cree un comercio en el sandbox oficial, guarde API key y secret en Ajustes
   y active la conexión de la organización. Nunca copie llaves al frontend.
2. Emita una revisión CLP, registre un anticipo y cree el enlace por el saldo.
   Complete el pago sandbox y compruebe un único movimiento y recibo. Reenvíe
   el callback y use **Verificar**: la recuperación consulta el pedido y no
   vuelve a crear el cobro. Compruebe un rechazo y un enlace vencido.
3. Declare la vigencia en **Ajustes › General › Cobranza e integraciones**
   (7 días por defecto, 1–90). El timeout enviado a Flow se expresa en segundos,
   según [la API oficial](https://developers.flow.cl/api#tag/payment/paths/~1payment~1create/post).
4. Tras aceptar el sandbox, cambie URL y llaves al comercio productivo. Verifique
   una operación autorizada, webhook HTTPS e idempotencia antes de distribuir
   enlaces a clientes. Un pago real verificado se registra aunque otra cobranza
   haya reducido el saldo; el exceso queda explícito para conciliación humana.

Sin conexión, **Crear enlace de prueba** recorre creación, retorno y confirmación
con una capacidad opaca y caducidad. No contacta Flow; movimientos, recibos y
saldos conservan la marca simulada. No acredita dinero real.

## SII / DTE

| Campo        | Detalle                                                                                                                                    |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Estado       | Diferida; no hay emision real sin certificados/CAF del contribuyente.                                                                      |
| Adaptador    | `backend/billing` y tablas de CAF/certificados/DTE.                                                                                        |
| Variables    | Nombres reservados por proveedor DTE/SII: `SII_ENV`, `SII_CERTIFICATE_PASSWORD`, `SII_PROVIDER_*` cuando se conecte el adaptador final.    |
| Activacion   | Cargar certificado y CAF autorizados, declarar ambiente certificacion/produccion, emitir DTE de certificacion y validar respuesta del SII. |
| Verificacion | DTE aceptado en ambiente de certificacion, XML/PDF almacenado como documento emitido e historial inmutable.                                |

El adaptador existente de `backend/projects/sii.py` genera factura 33 y nota
de crédito 61 con CAF/certificado de la organización; `sii_envio.py` envía y
consulta el estado oficial. No hay firma ni certificación nuevas en P11.

1. En Ajustes › Certificado digital cargue el PFX vigente con su contraseña;
   en Ajustes › SII registre los CAF autorizados. No publique estos archivos.
2. Configure backend/worker con `SII_WS_ENVIO_URL`, `SII_WS_STATUS_URL` y
   `SII_WS_TOKEN` del transporte oficial autorizado. Las variables genéricas
   del índice anterior no sustituyen estas interfaces existentes.
3. Complete la certificación del contribuyente y luego declare certificado y
   activación en **Cobranza e integraciones**. El estado solo muestra conexión
   con certificado vigente, declaración de certificación y transporte de envío.
4. Emita/envíe un DTE de prueba y consulte aceptado, reparos o rechazado. Una
   respuesta perdida exige revisión humana antes de reenviar. Conserve XML,
   PDF y estado inmutables; verifique también una nota de crédito.

La boleta tributaria 39 real **no está soportada** por el timbrador existente.
Conecte un proveedor DTE autorizado que implemente ese contrato antes de usarla
tributariamente. La boleta interna y el simulador 39 sí permiten revisar el
flujo; no se ofrecen como una boleta SII. Los documentos internos siempre
declaran «Documento interno — no válido como documento tributario electrónico».
Las pruebas `SIM-…` de 33/39/61 viven en una evidencia separada, no consumen CAF,
no generan TED ni XML tributario y no contactan SII.

## Correo con dominio propio

P25 deja dos transportes: las notificaciones comerciales salen del worker Django;
los enlaces de acceso salen de Supabase Auth. Ambos usan Mailpit en local. El
estado y la bandeja se consultan en Ajustes › Integraciones › Correo. Un dominio
externo queda «No conectado» hasta configurar SMTP en el servidor.

1. Verifique el dominio del remitente con el proveedor e instale SPF, DKIM y
   DMARC. Use un remitente del fabricante para conservar la identidad de los
   correos al cliente. Obtenga host, puerto y credenciales SMTP.
2. Cargue exclusivamente en backend y worker `MAIL_PROVIDER=smtp`,
   `MAIL_FROM_ADDRESS`, `MAIL_SMTP_HOST`, `MAIL_SMTP_PORT`, `MAIL_SMTP_USER` y
   `MAIL_SMTP_PASSWORD`. Use `MAIL_SMTP_STARTTLS=true` para puerto 587 o
   `MAIL_SMTP_SSL=true` y `MAIL_SMTP_STARTTLS=false` para puerto 465. El adaptador
   rechaza SMTP sin TLS. Declare `DEKOPEN_PUBLIC_APP_URL` con el origen HTTPS.
3. Genere una `MAIL_ENCRYPTION_KEY` aleatoria de alta entropía y manténgala igual
   en backend/worker. Producción exige declararla. Respalde la clave con acceso
   restringido: los correos sellados dependen de ella; cambiarla sin conservar la
   anterior vuelve ilegibles los envíos pendientes. No se muestra en Ajustes.
4. En Supabase Auth configure el SMTP y remitente del mismo proveedor, Site URL
   y URL de retorno `/auth/callback`. Copie como plantilla Magic Link el HTML de
   `supabase/templates/magic-link.html`; la imagen está en `/mail-lockup.png` del
   frontend publicado. Confirme que el enlace se usa una sola vez y entra en la
   organización esperada. Para el CLI local, `supabase/config.toml` ya referencia
   la plantilla; configure `MAIL_SANDBOX_HOST`/`MAIL_SANDBOX_PORT` con su Mailpit.
5. El dueño configura logo, nombre y color en Ajustes › Identidad. Un color sin
   contraste AA cae a teal-800 con aviso. Indique un correo de encargado y active
   los avisos internos si los necesita. Estas preferencias no alteran emisiones
   antiguas. El emisor documental y sus pies se sellan en la revisión nueva.
6. Emita una cotización con correo del cliente, abra su vista previa y el
   **PDF sellado**. Si falta, use **Preparar PDF de la cotización** y ábralo
   antes de confirmar **Enviar al cliente**. El servidor exige el SHA revisado;
   una respuesta perdida conserva la misma intención incluso tras recargar.
   Compruebe HTML,
   texto, PDF adjunto y enlace de la revisión. Registre un pago y repita la vista
   previa/envío del comprobante. Apruebe desde el portal y bloquee una estación
   de ensayo para comprobar los dos avisos internos.
7. Compruebe los cinco correos en una bandeja externa y la bandeja de Ajustes.
   «Aceptado por el servidor» significa aceptación SMTP, no lectura ni entrega
   final. Una respuesta perdida muestra «Entrega sin confirmar». Revise servidor
   y destinatario antes de confirmar **Comprobé que no llegó; reenviar**. No hay
   reenvío automático de una entrega dudosa; el mismo envío mantiene su contenido,
   destinatario e identificador de mensaje y registra otro intento.

El sandbox solo entrega a Mailpit local y nunca contacta al destinatario externo.
Los enlaces del portal se cifran en la outbox y no se publican en jobs ni logs.
SMTP no ofrece exactamente una entrega: el control explícito de recuperación es
parte del contrato. Una cotización reemplazada/vencida o un pago anulado fallan
en la comprobación previa al envío y requieren resolver su causa.
Si el enlace del correo venció o fue revocado, **Preparar nuevo correo** abre la
cotización para revisar y confirmar otro envío con enlace nuevo. El registro
anterior se conserva. Un pago anulado no permite reenviar su comprobante.

## Webhooks productivos

| Campo        | Detalle                                                                                                  |
| ------------ | -------------------------------------------------------------------------------------------------------- |
| Estado       | Diferida; endpoints locales y jobs deben probarse con payloads firmados antes de produccion.             |
| Adaptador    | Vistas backend por integracion, jobs idempotentes y auditoria.                                           |
| Variables    | `WEBHOOK_SIGNING_SECRET_*`, mas las variables especificas de cada proveedor.                             |
| Activacion   | Registrar endpoints publicos, configurar secreto de firma, activar reintentos del proveedor y monitoreo. |
| Verificacion | Reenvio del mismo evento no duplica efectos y eventos fuera de orden quedan auditados.                   |

## Proveedor de IA

| Campo        | Detalle                                                                                                                       |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Estado       | Conectado por entorno local; no se debe exponer al frontend ni al repo.                                                       |
| Adaptador    | `backend/ai_gateway/providers.py` con convencion `AI_GATEWAY_{PROVIDER}_*`.                                                   |
| Variables    | `AI_GATEWAY_MIMO_API_KEY`, `AI_GATEWAY_MIMO_BASE_URL`, `AI_GATEWAY_MIMO_MODEL`, `AI_GATEWAY_ROUTE_PROVIDER`.                  |
| Activacion   | Cargar variables en backend y worker, seleccionar proveedor MIMO en rutas IA y ejecutar una consulta controlada.              |
| Verificacion | Job IA termina con proveedor real, auditoria queda registrada y ningun valor secreto aparece en logs, HTML o bundle frontend. |

## Vidrios: norma y fichas del proveedor (D02)

1. Obtenga la norma NCh 135/2 que su organización puede usar y la fuente/página de
   cada regla. En la décima hoja **Reglas de vidrio** de `catalogo-v1.xlsx`, declare
   código, nombre, zona, clases admitidas, umbrales, fuente, `synthetic=false` y
   `mandatory` según su decisión. No copie tablas de la norma sin permiso.
2. Importe la hoja en Catálogo › Importar, revise sus candidatos y el diff, y
   publique con el dueño o encargado de taller. También puede mantener las reglas
   en Ajustes › Reglas de vidrio. Los ejemplos DEMO no sirven como regla oficial.
3. Obtenga del vidriero composiciones, códigos de compra, propiedades Ug/g/TL,
   clase, límites y fuentes. Publique recetas desde el compositor o la hoja
   Vidrios. Para un laminado, cargue el espesor y la densidad de cada PVB con su
   fuente: el sistema conserva **Sin dato** cuando falten.
4. Cargue costos por m² y SKU/unidad de templado, pulido, perforación y palillaje,
   incluidos mínimo facturable y costos por metro o cruce. Revise una cotización y
   la explicación de sus cargos antes de emitirla.
5. Configure `DEKOPEN_PUBLIC_APP_URL` con el origen público de la aplicación,
   reinicie backend/worker y descargue un pedido de una OT sellada. Escanee una
   etiqueta como encargado de taller y compruebe proyecto, revisión, pieza y BOM.
6. Compare PDF/CSV con el BOM sellado. Acuerde la precisión con el proveedor si
   aparecen cortes decimales; no los redondee. El templado se solicita a la medida
   exacta. Un vidrio con contorno necesita adjuntar el plano de fabricación.

No se envía el pedido a terceros desde esta superficie. Descargarlo y revisarlo
son acciones locales; cualquier envío futuro conserva el clic humano explícito.

## Aperturas: capacidades, encuentros y manillas (D03)

1. Obtenga del proveedor las aperturas fabricables por serie y versión, con su
   fuente: movimiento, bisagras, dirección, uso ventana/puerta y rol de hoja.
   Declare las capacidades en Catálogo › Ficha de serie o en la hoja Sistemas
   de la plantilla; vincule los kits de esa misma autoridad.
2. Para una francesa o puerta doble, registre inversor, encuentro, deducciones
   y fuente. La pasiva necesita falleba sin manilla de accionamiento. No sustituya
   el inversor por un montante ni publique una capacidad con herrajes retirados.
3. Registre la regla de manilla: referencia de altura, límites, distancia al
   borde de cierre y fuente. Revise las coordenadas y el rango que deriva el
   motor; una altura universal de la organización no reemplaza esta autoridad.
4. Importe, revise el diff y publique con el dueño o encargado. Verifique la
   apertura en vista interior, guardar/reabrir, precio y documento. Confirme con
   el fabricante toda medida decimal del encuentro sin redondearla.
5. Complete los datos estructurales y de fabricación antes de liberar a
   producción. Una cotización DEMO incompleta y una carga ficticia de prueba no
   acreditan inercia ni cumplimiento de viento para una obra.

Las series DEMO v3 no modifican v1/v2. Un SKU compartido conserva su tarifa exacta;
una unidad o tarifa distinta debe tener su autoridad comercial identificable.

## Herrajes: familias, clases y mecanizados (D04)

1. Obtenga la ficha del fabricante por serie y movimiento, con familia, clase,
   rangos de ancho/alto, masa admitida, relación de aspecto y altura mínima del
   compás. Declare su prioridad y fuente en `class_authority` de **Herrajes** en
   la plantilla. Los kits históricos pueden seguir su camino anterior.
2. Registre cada SKU y código de compra, cantidad por umbral, largo fijo o
   deducción, masa unitaria o por metro y costo/unidad. Un componente cortable
   debe conservar su largo y la unidad de precio correspondiente. No declare dos
   tarifas diferentes para el mismo SKU/unidad sin una autoridad identificable.
3. Registre modelos/colores de manilla y su artículo, referencia y rango de
   altura. Las opciones vendibles indican componentes añadidos o reemplazados,
   precio y fuente. Una certificación RC necesita evidencia del fabricante.
4. Importe, revise el diff y publique por clic del dueño o encargado. Compruebe
   dos tamaños, umbrales de cantidad/masa, F6, elegir/deshacer y guardar/reabrir.
   Cotice, emita una revisión y compare picking por SKU y largo con su BOM.
5. Para mecanizar, aporte pieza/ámbito anfitrión, lado físico, cara, coordenadas,
   herramienta, profundidad y cobertura de cantidad de la ficha. Lo incompleto
   permanece **declarado no emitido**; completar la estación exige resolverlo
   en catálogo y emitir una nueva revisión, sin modificar la ya sellada.
6. Conecte herramientas y máquina siguiendo P14, compruebe su programa frente a
   la ficha y una pieza de ensayo. Las series DEMO v4 y sus packs no certifican
   fabricación ni reemplazan la validación del fabricante.

## Colores y acabados por caras (D05)

1. Obtenga la carta y las reglas técnicas del fabricante por sistema: códigos,
   nombres, proceso, base de PVC, caras permitidas, muestra lineal y fuente.
   Declare RAL/brillo o anodizado cuando corresponda. Indique aproximación;
   agregue una textura local solo si la ficha la aporta.
2. Declare combinaciones, holgura de vidrio, refuerzo obligatorio, límites de
   posición/hoja, colores compatibles de manilla y días adicionales. No use los
   valores sintéticos DEMO para fabricar ni invente un plazo ausente.
3. Complete **Colores y SKU por color** para cada perfil/combinación: SKU de
   compra, fabricante, identidad física, color de stock, regla de corte, versión
   y unidad. Mantenga separado el acabado real del acero. Registre existencias
   con esa misma autoridad; una barra blanca no cubre una ventana bicolor.
4. Declare recargo por metro de perfil, porcentaje del costo o fijo por posición,
   moneda y fuente; complete costo/lista vigente y reglas comerciales. Revise el
   delta calculado contra la combinación base antes de cotizar.
5. Importe o edite con dueño/encargado, revise el diff y publique por clic.
   Compruebe interior/exterior, igual caras, manillas, guardar/reabrir, precio,
   PDF y portal. Compare el color con una muestra física del fabricante.
6. Emita una revisión nueva y verifique compras, reservas y optimización por
   combinación. Conserve las revisiones anteriores y su carta sellada. Las
   series DEMO v5 son autoridades adicionales, sin certificación.

## Accesorios, servicios y plantillas (D06)

1. Obtenga la ficha y tarifa del fabricante para vierteaguas, ensanche,
   tapajuntas, mosquiteros y accesorios. Declare la compatibilidad por apertura,
   regla por vano/hoja/lado, vuelos y fuente en Catálogo › Ficha de serie o en
   `extra_authority` de la plantilla. Palillaje y cruces usan la receta D02.
2. Para perfiles, complete artículo por rol, corte, masa y refuerzo cuando
   corresponda, más SKU comercial por acabado. Para accesorios unitarios,
   declare su artículo y unidad de compra. Compruebe un vano y una hoja reales
   contra la ficha; una medida derivada no acredita fabricación sin autoridad.
3. El dueño con MFA declara servicios y tarifas completas en Ajustes › Extras y
   servicios: instalación por perímetro/área/cantidad, sellado, retiro, andamio y
   flete fijo/por zona. Registre costo, venta, moneda y fuente. Declare conversión
   vigente si la cotización usa otra moneda; no adopte cero por falta de tarifa.
4. Configure las plantillas para posiciones nuevas y elija sublíneas con precio
   o precio agrupado. Revise el diff y guarde con motivo. Verifique una posición
   nueva y una de otra serie; lo incompatible debe explicar su causa.
5. Cotice un proyecto con cantidades mayores que uno, revise base/sublíneas y
   ajustes, servicios y fuente. Aplique con clic humano y emita una revisión.
   Compruebe ambos PDF y que ensanches/vierteaguas llegan al BOM, compra y plan
   de corte de la OT. Cambios posteriores requieren una revisión nueva.
6. Las series DEMO v6 y sus precios sintéticos no certifican producción ni
   reemplazan fichas reales. No requieren una credencial externa adicional:
   requieren datos de proveedor y tarifas de instalación revisados por la empresa.

## Proveedor de IA, presupuesto y costo (IA3)

1. Configure `AI_GATEWAY_MIMO_API_KEY`, `AI_GATEWAY_MIMO_BASE_URL` y
   `AI_GATEWAY_MIMO_MODEL` solo en el servidor y el worker, con los nombres y
   modelo de [AI_PROVIDERS.md](AI_PROVIDERS.md). Reinicie ambos procesos. La
   credencial local ya permite aceptación real; nunca la copie al frontend.
2. En producción declare `AI_GATEWAY_MOCK_ENABLED=0`. Para un entorno de prueba,
   habilite el flag y elija explícitamente una ruta de prueba en Ajustes. El
   flag por sí solo no cambia MiMo ni depende de DEBUG.
3. El dueño con MFA revisa las cuatro capacidades en Ajustes › Inteligencia
   artificial y ejecuta «Probar conexión». El caso mínimo valida medidas y
   motor en una copia, sin cambiar proyectos. Sin credencial, siga la causa
   del panel y configúrela en el servidor; ninguna clave se muestra en la app.
4. Declare ambas tarifas de su contrato en USD por millón de tokens, si quiere
   costo monetario. No use tarifas sintéticas de tests. Dejar ambas vacías
   conserva «Sin dato» y no altera llamadas anteriores.
5. Configure el presupuesto mensual en créditos de solicitudes y compruebe el
   bloqueo suave y el aviso. Revise Trabajos con filtro de capacidad/estado y
   abra «¿De dónde sale?» para ver herramientas ejecutadas y tiempo.
6. Para catálogos escaneados confirme la lectura contra el fabricante antes
   de publicar. El transporte renderiza las páginas sin texto y acepta visión;
   esa lectura no certifica una autoridad técnica. Puede elegir un modelo de
   visión distinto para catálogo en los mismos ajustes.

## Propuesta DOC-01 y portal (P09)

1. Configure `DEKOPEN_PUBLIC_APP_URL` en servidor/worker con la URL pública
   HTTPS del frontend. El QR emitido fija ese destino; pruebe un PDF de una
   nueva revisión antes de entregarlo. No reemita ni modifique PDFs históricos.
2. Mantenga estable la clave de cifrado de correo `MAIL_ENCRYPTION_KEY` del
   servidor/worker: también protege la capacidad del QR. Siga su procedimiento
   de secretos y respaldos, sin enviarla al frontend ni incluirla en git.
3. En Ajustes › General configure identidad/logo y Documentos: papel, acento,
   pie, hitos de pago y condiciones reales de la empresa. Obtenga composiciones
   y Ug de fichas revisadas del proveedor. DEMO no acredita certificación.
4. Emita con clic humano, abra el PDF y compruebe QR, revisión y total. Cree un
   enlace compartido y verifique que el QR sigue vigente. Pruebe revocación en
   una cotización de aceptación y confirme que el portal queda bloqueado.
5. Configure almacenamiento y jobs según las secciones existentes. No se
   necesita proveedor nuevo para QR: el portal existente sirve la revisión y
   el artefacto inmutable conserva sus bytes después de cambios de preferencias.

## Compras, recepción y retazos (P15)

1. Configure correo/almacenamiento/worker según las secciones anteriores. En el
   sandbox el PDF de la OC llega solo a Mailpit. Antes de activar SMTP, compruebe
   remitente, dominio y TLS con una OC de aceptación; verifique el archivo adjunto
   y la bandeja de correo de la revisión en Compras.
2. Declare la elegibilidad del proveedor con RUT, contacto/correo, materiales y
   fuente vigente. Revise asignaciones, cantidades y precios antes de crear OC.
   Cambiar un proveedor no modifica las órdenes ya selladas.
3. Configure en Ajustes › General › Documentos el rack inicial de retazos y los
   días de alerta. Etiquete racks físicos con esos nombres. Registre guía, fecha,
   lote, rack y dañados al recibir; no ingrese lo dañado como material útil.
4. Revise suministros/color/largo de barras y declare formatos/sustratos de
   lámina desde autoridad real. Los retazos manuales deben corresponder a ese
   suministro; no se aceptan identidades o medidas arbitrarias.
5. Complete el recorrido de aceptación: OT → necesidades → OC → envío humano →
   recepción parcial → stock → reserva → Corte → RT con QR/rack. Compruebe actor
   y documento en el libro de movimientos. Una cantidad fuera de la capacidad
   sellada exige revisar la planificación o emitir una revisión adicional.
6. Una respuesta SMTP perdida no autoriza un reenvío automático. Compruebe la
   ausencia de entrega y confirme la recuperación en la bandeja. Una OC cancelada
   no se envía; conserve su historia y revise la compra nueva.

## Mecanizado · autoridad de planta

1. En Producción › OT › Mecanizado › Máquinas y herramientas declare datos
   del manual y del montaje físico: capacidad, ejes, controlador, carrera,
   margen, todas las mordazas revisadas, fuente y herramientas disponibles.
2. Para cada código de herramienta declare tipo, diámetro, largo útil,
   profundidad máxima y operaciones que admite. Para cada perfil revise el
   montaje ligado a su sección sellada, origen inicial y orientación de carga.
   No copie la autoridad DEMO de aceptación a una máquina productiva.
3. Revise operaciones emitidas y pendientes, luego la comparación de programa.
   Confirme el intercambio y verifique su manifiesto. Una revisión de plan o
   autoridad puede reemplazar el programa; el historial conserva sus bytes.
4. La salida implementada es intercambio neutro. Conectar una CNC requiere un
   postprocesador declarado del fabricante y validación física específica.
   DEKOPEN no envía este intercambio a una máquina ni inventa su formato.
   Falta de patrón, Y/Z, herramienta, profundidad, sujeción u orientación
   bloquea; completar esas autoridades no se sustituye por un valor estimado.
