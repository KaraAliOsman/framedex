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

## SII / DTE

| Campo        | Detalle                                                                                                                                    |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Estado       | Diferida; no hay emision real sin certificados/CAF del contribuyente.                                                                      |
| Adaptador    | `backend/billing` y tablas de CAF/certificados/DTE.                                                                                        |
| Variables    | Nombres reservados por proveedor DTE/SII: `SII_ENV`, `SII_CERTIFICATE_PASSWORD`, `SII_PROVIDER_*` cuando se conecte el adaptador final.    |
| Activacion   | Cargar certificado y CAF autorizados, declarar ambiente certificacion/produccion, emitir DTE de certificacion y validar respuesta del SII. |
| Verificacion | DTE aceptado en ambiente de certificacion, XML/PDF almacenado como documento emitido e historial inmutable.                                |

## Correo con dominio propio

| Campo        | Detalle                                                                                                               |
| ------------ | --------------------------------------------------------------------------------------------------------------------- |
| Estado       | Diferida; Mailpit cubre local.                                                                                        |
| Adaptador    | Backend de notificaciones/correo que use el proveedor elegido.                                                        |
| Variables    | `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_FROM`, `EMAIL_USE_TLS`. |
| Activacion   | Verificar dominio, SPF/DKIM/DMARC, cargar credenciales del proveedor y probar magic link/cotizacion enviada.          |
| Verificacion | Correo recibido en bandeja externa, enlaces validos y sin secretos en logs.                                           |

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
