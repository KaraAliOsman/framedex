# P25 · marca, emisor y correo

Estado: verificado localmente en `codex/P25-marca-identidad`, base `bcbd8060`.
Cuatro gates locales y Database Gate PASA. CI e integración pendientes; no se
considera integrado hasta cerrar los cuatro checks del PR.

La sección B reemplaza la O con contornos Plex Sans 600. La marca dispone de
SVG, PNG de cinco tamaños por tema y manifest verificado en el build.
El acceso y la recuperación son hojas técnicas; el onboarding de cuatro pasos
termina en la primera posición guardada y reabierta. La identidad del fabricante
se sella al emitir y se aplica a documento, portal, metadata y correo comercial.
Los cinco correos tienen plantilla real y transporte local; los comerciales
exigen revisión y confirmación, los internos requieren activación del dueño.

## Flujos y evidencia

| Recorrido | Resultado y evidencia |
| --- | --- |
| Marca 16/24/32/72/160, claro/oscuro | PASA. `recorrido/marca-*`; geometría óptica bajo 24 px. |
| Onboarding → cliente → obra → primera posición | PASA. UI real, contacto heredado, vidrio del catálogo, guardado/reapertura; `onboarding-primera-posicion.png`, `primera-posicion-guardada.png`. |
| Desconexión con edición pendiente | PASA. Conserva ubicación y borrador; comprobar conexión falla con causa y recupera al conectar. |
| Magic Link y MFA | PASA. UI → Mailpit → enlace de un uso → callback → organización. MFA real a cuatro tamaños/ambos temas, seguido de verificación por UI; no se capturan QR, secreto ni código. |
| Marca del fabricante | PASA. Color inválido se rechaza en español; blanco activa fallback AA; logo y color se guardan por UI. PDF Carta real sin palabra DEKOPEN; portal sin marca de plataforma cuando su pie está oculto. |
| Cotización y pago | PASA. Clic deshabilitado hasta confirmar, mensajes reales en Mailpit con cotización/comprobante PDF y marca del emisor; `correo-real.json`. |
| Aprobación y OT bloqueada | PASA. Decisión desde portal móvil y transición real BLOCK generan avisos internos; UNBLOCK devuelve la estación al estado previo. |
| Entrega incierta | PASA. SMTP local sin respuesta deja entrega sin confirmar; el worker no repite. UI exige comprobación humana, registra segundo intento y entrega en Mailpit. |
| Etiqueta de taller e impresión | PASA. B a 72 px en etiqueta clara/oscura y PDF real; inspección del raster impreso. |

Las cinco plantillas en `/dev/correos` no inventan importes de operación: la
vista previa declara su naturaleza. El correo real de pago usa el comprobante
sellado. Sus imágenes de identidad se comprobaron desde partes MIME reales de
Mailpit; no se presentan imágenes CID rotas como verificación del correo.

## Matrices y estados

- 84 vistas de acceso, marca, Acerca de, onboarding, 404, fallo de pantalla,
  desconexión y cinco correos: `recorrido/matriz.json`, sin desbordes ni hallazgos.
- 56 vistas adicionales de onboarding vacío/carga/error/bloqueado/sin permiso,
  selección de organización y callback vencido: `recorrido/estados.json`, sin
  hallazgos. La denegación usa el jefe de taller real. Retrasos, fallos y ausencia
  de catálogo son respuestas controladas de aceptación, sin mutaciones al servidor.
- Ocho vistas MFA reales: `recorrido/mfa.json`, sin desborde ni hallazgos.
- 32 vistas de bandeja vacía/carga/error y correo bloqueado:
  `recorrido/estados-correo.json`, sin hallazgos ni desborde del componente.
  La comparación antes/después conserva el desborde anterior de la fila de
  posición al abrir Cotización a 1440/1280; abrir el correo no lo aumenta.
- `npm --prefix frontend run ux:capture` produjo 16 registros reales para inicio
  y login: `captura/inicio/report.json` y `captura/login/report.json`, sin hallazgos.
  Se corrigió la selección de rutas del ensayo inicial que producía cero registros.
- Evidencia anterior en `antes/`: acceso, onboarding y ruta ausente. Antes la
  ruta ausente redirigía al panel; la nueva hoja explica y permite volver.

Tamaños 1440×900, 1280×800, 1024×768 y 390×844, claro y oscuro. El documento
impreso permanece claro. Intercepciones de render/catálogo/contexto y de estado
de correo se declaran; complementan recorridos y permisos reales, sin simular
éxito de una operación comercial. Los enlaces secretos se omiten en capturas.

## Gates

`make lint typecheck test build` PASA: 744 pruebas del motor (+2 xfail), 1.267
backend y 827 frontend. OpenAPI/orval reproducibles, goldens sin cambios y prueba
del build verifica manifest, entrada y dimensiones de ambas familias de íconos.
`make test-db` PASA: 80 archivos / 1.173 pgTAP, 408 integraciones y 11 E2E reales.
El esquema limpio y los upgrades poblados pasan en PostgreSQL 16. El nuevo
verificador P25 compara identidad, tres tablas completas, snapshots, hashes y
precios históricos byte a byte; conserva los defaults explícitos sin actualizar
la autoridad histórica. El stack aislado se detuvo y limpió correctamente.

El gate local usa un checkout Linux dentro de un contenedor y un daemon Docker
separado. Se verificaron byte a byte los 80 archivos SQL y la plantilla pública
de acceso en los binds del daemon. El primer montaje de la plantilla era una
carpeta vacía y entregaba HTML de error: se corrigió el montaje, sin modificar
la extracción estricta del enlace ni sustituir el correo real por una respuesta.

## Pase editorial

Primera ronda: se convirtió Plex en contornos para conservar la firma sin
dependencia de fuentes, se corrigió ópticamente la sección pequeña y se retiraron
brillos, degradados y bucles del Orb sin cambiar su API. El onboarding de siete
pasos y su CSS se sustituyeron por cuatro decisiones, explicación y primera
posición; no desemboca en un panel vacío.

Segunda ronda: se corrigió la herencia del correo/RUT/teléfono a la obra, se
extendió la identidad del portal a favicon/Apple/título/manifest y se hizo
explícita la recuperación de entrega incierta. La revisión de contraste corrigió
deshabilitados del onboarding y enlaces de inicio; se retiraron el estilo muerto
de la marca textual, radios de 8 px y sombras ajenas a la escala en capturas de
inicio. El detector pasa de nuevo. La evidencia final del correo verifica CID.

F10: pared y tabique reconocibles en 16 px, 160 px y etiqueta impresa.
La capacidad que sube el techo conecta una primera ventana calculada con su
emisor y PDFs sellados: ninguna cifra de cotización/pago proviene de la plantilla.
Se conservan F2/F11 e inmutabilidad al cambiar la marca y al recuperar un envío.

| Rúbrica | Estado | Evidencia del alcance P25 |
| --- | --- | --- |
| R1 · números y unidades | PASA | Formateadores exactos; comprobante/PDF del motor; referencia Mono. |
| R2 · radios e inglete | PASA | Marca técnica, hoja de acceso; tokens ≤4 px. |
| R3 · jerarquía y capas | PASA | Filetes, peso y espacio; bandeja inline y una confirmación. |
| R4 · naranja | PASA | Estado que requiere persona; no CTA naranja. |
| R5 · teal | PASA | Cromo único; color del fabricante validado contra papel. |
| R6 · voz | PASA | App tutea, cliente/portal de usted; enums traducidos. |
| R7 · densidad | PASA | Office de 32 px; acceso móvil táctil; sin inspector nuevo en este encargo. |
| R8 · cinco estados | PASA | Causa/acción, matrices de estado y recuperación real. |
| R9 · papel | PASA | Hoja sobre mesa; correos/PDF claros. |
| R10 · selección | PASA | Serie con contorno/tinte y foco, sin elevación al seleccionar. |
| R11 · gramática | PASA | Láminas técnicas; elevación del motor preservada. |
| R12 · teclado/foco | PASA | Validación española, foco teal, forms/Stepper y confirmación operables. |
| R13 · movimiento | PASA | Tokens y reduced-motion; Orb estático. |
| R14 · acción principal | PASA | Una por formulario/preview; entrada repetida secundaria. |
| R15 · autoridad | PASA | PDF/comprobante sellados; previews sin importes ficticios. |
| R16 · sin efectos prohibidos | PASA | Guardas y detectores; eliminación de brillos/bucles. |
| R17 · anchos | PASA | Matrices de cuatro tamaños/ambos temas, sin desborde nuevo. |
| R18 · efecto real | PASA | Guardado, reapertura, envío, decisión, retry y eliminación de código viejo. |
| R19 · firma | PASA | B en favicon, app, acceso y etiqueta; D solo Acerca de/correo. |
| R20 · capacidad real | PASA | Primera posición y correo desde autoridad emitida, sin cálculos en plantillas. |

## Decisiones y límites

Decisiones en `docs/decisions/valores-por-defecto.md`; construcción y usos
prohibidos en `docs/design/marca.md`; activación SMTP/Supabase Auth en
`docs/operations/ACTIVACION.md`. Documentos ocultan pie y portal discreto lo
muestra por defecto; Ajustes cambia preferencias para emisiones nuevas. Avisos
internos comienzan desactivados. SMTP TLS está implementado; DNS, dominio y
credenciales productivas se conectan después de aceptar.

SMTP no garantiza recepción única ni lectura. Una entrega dudosa exige verificar
antes de reenviar; la UI explica la consecuencia. Historia sin `brand_schema`
mantiene su identidad previa. El catálogo sigue siendo DEMO; este encargo no
certifica fabricación ni rediseña las superficies pendientes P04–P24. El bundle
3D conserva su advertencia de tamaño; el build pasa sin debilitar el umbral.
El detalle de proyecto conserva un desborde anterior en la fila de posición
con Cotización abierta a 1440/1280; su comparación queda explícita en el informe
de estados y se entrega a P21. La rúbrica P25 cubre la marca y paneles añadidos.
