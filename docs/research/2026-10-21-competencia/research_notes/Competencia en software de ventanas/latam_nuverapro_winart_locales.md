# Software de cotización y fabricación de ventanas en LatAm y España: NuveraPRO, Winart, WinMaker 10 y alternativas locales

Notas de investigación, 21-10-2026. Fuente principal: páginas oficiales de cada proveedor, consultadas hoy salvo que se indique otra fecha. Leyenda: **[V]** = hecho verificado con URL; **[I]** = inferencia; **[Dueño]** = experiencia contada por el dueño de DEKOPEN, sin verificación externa.

Aclaración de nombres:
- **"Winart"** es el software de **Haustek S.A. (Chile)**, empresa de Winhouse Chile, que distribuye perfiles de PVC. No es un producto español.
- **"WinMaker 10"** es de **Lepton Sistemas (Buenos Aires, Argentina)**. Las búsquedas por "WinMaker" a secas devuelven sobre todo el gestor de ventanas Linux "Window Maker", que no tiene relación.
- **Proline**, la marca del perfil PRO6004 con el que falló NuveraPRO según el dueño, es un **extrusor turco de PVC** (Izmir). No es Rehau. Más detalle en la sección NuveraPRO.

---

## 1. Por producto: módulos, flujo completo, plataforma, precio y presencia por país

### Takeaway
El mercado hispano para talleres pequeños tiene tres tipos de producto:
- **Cotizadores web simples por suscripción** con precios en moneda local: NuveraPRO (Chile), Alum (Colombia), winDOS (España), Luminio (EE. UU./hispano).
- **Software gratuito o de marca atado a un extrusor o distribuidor**: Winart/Haustek, la app de Indalum México, OP 2.1 de Alsafex, la versión gratis de Open2D2 con datos de FEXA y WinMaker Aluar Web.
- **Programas de escritorio Windows más completos**, con producción, stock y conexión CNC: WinMaker 10, OP 2.1/Megevand, Optiglass, GAIA PRODUCTOR, Sicar2 y Prefsuite.

Ningún producto revisado ofrece a la vez catálogo local verificado, motor de despiece auditable, compras e instalación en una web moderna. Solo Luminio anuncia funciones de IA.

### Cited Findings

#### NuveraPRO (Chile), análisis profundo
- **Empresa y posicionamiento [V]:** cotizador online para carpinterías de PVC y aluminio con sede en Santiago. Se presenta como el cotizador "más simple y poderoso del mercado". Equipo publicado: Marcelo Vera (CEO), Cristina López (capacitación) y Francisco Herrera (ventas). Contacto: info@nuverapro.com y WhatsApp +56 9 5332 8289. — [NuveraPRO](https://www.nuverapro.com/cotizadorpvcaluminio/)
- **Plataforma [V]:** aplicación web; el login se titula "Cotizador Online Aluminio y PVC". La recuperación de contraseña usa `cfgLoginRecordar.aspx`, así que corre sobre ASP.NET WebForms [I: stack antiguo]. El login mostraba el contador "usuarios últimas 24 horas: 297" (21-10-2026). — [NuveraPRO login](https://www.nuverapro.com/)
- **Salidas [V]:** cotización para el cliente con logo, listado de materiales para comprar al proveedor, resumen de vidrios para encargar, pautas de corte e "informes instantáneos". Dice que cubica y gestiona proyectos. — [NuveraPRO](https://www.nuverapro.com/cotizadorpvcaluminio/)
- **Flujo oficial en 6 pasos, "en menos de 10 minutos" [V]:**
  1. Crear la cuenta (con prueba).
  2. Configurar la empresa: logo y datos.
  3. Elegir marcas y series. Cada proveedor de PVC cuenta como una marca; todas las series de aluminio van juntas bajo "Gestión VAP Aluminio".
  4. Dibujar la ventana o puerta con medidas y tipo; el sistema calcula y arma la cotización.
  5. Generar informes: cotización, materiales, pautas de corte y vidrios.
  6. Pedir soporte por WhatsApp.

  Fuente: [Primeros pasos](https://www.nuverapro.com/cotizadorpvcaluminio/primeros-pasos.html)
- **Precio mensual + IVA [V]**, sin moneda explícita (CLP por contexto [I]):

  | Marcas | Precio |
  |---|---|
  | 1 | $25.000 |
  | 2 | $27.500 |
  | 3 | $30.000 |
  | 4 o más | $32.500 |

  El aluminio cuenta como una sola marca con todas sus series. No hay contratos ni límite de usuarios o dispositivos, y se anuncian descuentos por plan. Incluye prueba gratis de 15 días y "soporte y capacitación permanente". — [NuveraPRO](https://www.nuverapro.com/cotizadorpvcaluminio/)
  - [I] Equivale a unos USD 25–35 al mes, según el tipo de cambio.
- **Catálogo [V]:** dice trabajar con "las principales marcas y series del mercado" y con "pautas de corte oficiales de los principales proveedores de PVC". La página "Marcas & Series" no nombra ningún proveedor: remite a WhatsApp o correo para confirmar si uno es compatible. — [Marcas](https://www.nuverapro.com/cotizadorpvcaluminio/marcas.html)
- **Videos tutoriales [V]**, todos en el canal [@nuverapro](https://www.youtube.com/@nuverapro):
  - "¿Que es NuveraPRO?, el Cotizador para puertas & ventanas de PVC o Aluminio" — [YouTube](https://www.youtube.com/watch?v=HAAbXcBtVRA)
  - "Primer cotización de nuverapro". El buscador lo fechaba unos 774 días atrás [I: cerca de agosto-septiembre de 2024]. — [YouTube](https://www.youtube.com/watch?v=IIoSggP9JDA)
  - "Agregar Marcas a nuverapro.com" — [YouTube](https://www.youtube.com/watch?v=2Fn3Npl10_0)
  - "Emitir informes en nuverapro.com" — [YouTube](https://www.youtube.com/watch?v=mhqNagRm4Vg)
  - La descripción del canal promete "ejemplos reales, errores comunes y uso práctico".
- **Experiencia del dueño de DEKOPEN [Dueño]:** falló en precios, configuración y continuidad. Los cortes de Proline PRO6004 salían sin el orden correcto y con precios propios de NuveraPRO, no los del fabricante.
- **Qué es el PRO6004 [V]:** serie de Proline PVC (Turquía).
  - Datos técnicos del fabricante: perfil de 60 mm, 4 cámaras, 2 burletes, vidriado de 4 a 32 mm, Uf 1,49 W/m²K y norma TS 5358 / EN 12608-B. — [Proline PVC](https://www.prolinepvc.com/es/perfiles-de-pvc-serie-pro6004/); [Proline EN](https://www.prolinepvc.com/en/urun/pro6004-series); [Proline Pvc en TİM, Izmir](https://delegations.tim.org.tr/event/chile-peru-colombia-mexico-virtual-trade-delegation/company/proline-mrpan-bright-fox)
  - En Chile lo vende Aluminios & PVC 2000 (teléfono +56, "Ltda."). Códigos: PRO 04 (hoja puerta interior), PRO 05/06/08 (junquillos DVH o vidrio simple), PRO 12 (batiente inversora) y accesorios. Precios publicados de $143 a $89.571 por ítem, según color y variante. — [Aluminios 2000, Línea PRO6004](https://aluminios2000.com/categorias/linea-pro-6004/)
  - Proline participó en una misión comercial virtual hacia Chile, Perú, Colombia y México. — [TİM](https://delegations.tim.org.tr/event/chile-peru-colombia-mexico-virtual-trade-delegation/company/proline-mrpan-bright-fox)

#### Winart, de Haustek S.A. (Chile, PVC)
- **Funciones [V]:** software 100% online para fabricantes de ventanas de PVC. Hace presupuestos, cubicación y pautas de corte. Muestra costos y márgenes reales por negocio. Genera informes para pedir perfiles, herrajes y termopaneles, y optimiza cortes. — [Haustek Winart](https://haustek.cl/winart/)
- **Documentos que emite [V]:** hoja de fijación, lista de material, pedido de accesorios, perfiles y vidrios, paño de ventana, paño de vidrio, optimización de corte, plano de ejecución y presupuesto al cliente. — [Haustek Winart](https://haustek.cl/winart/)
- **Precio y acceso [V]:** gratis, pero solo para clientes de Haustek, sin límite de usuarios por empresa. El ejecutivo comercial coordina la instalación remota y la capacitación. Quien no es cliente escribe a winart@haustek.cl. Hay video de presentación y tutorial, sin manual escrito público. — [Haustek Winart](https://haustek.cl/winart/)
- **Relación con Winhouse [V]:** Winhouse Chile, empresa de Haustek, distribuye sistemas de perfiles de PVC. — [Winhouse Chile](https://winhouse-chile.cl/)
- [I] Es una herramienta de fidelización del distribuidor: sirve si compras perfiles a Haustek/Winhouse, no para un taller que trabaja con varias marcas.

#### WinMaker 10, de Lepton Sistemas (Argentina)
- **Funciones [V]:**
  - Diseño de frentes y planos de topologías.
  - Optimización de cortes de perfiles y vidrios.
  - Órdenes de producción y presupuesto.
  - Stock de perfiles, vidrios y accesorios.
  - Listas de precios desde sus bases, que se recalculan al cambiar el costo de la materia prima.
  - Multiusuario y multimoneda (pesos, dólares, reales, euros).
  - Pasar un presupuesto a otra marca o línea con un clic.
  - Integración con un sistema de gestión comercial y exportación de cortes a máquinas CNC.

  Fuente: [Lepton](https://www.lepton.com.ar/web/productos/software-para-carpinteria-de-aluminio-y-pvc)
- **Plataforma [V]:** escritorio Windows (desde Windows 7). Recomienda i5 de 8.ª generación, 8 GB de RAM, GPU dedicada de 1 GB o más, 50 GB de disco, un puerto USB libre [I: probable llave física de licencia] e internet. — [Lepton](https://www.lepton.com.ar/web/productos/software-para-carpinteria-de-aluminio-y-pvc)
- **Versiones y precio [V]:** sale una versión mayor cada unos 2 años; actualizarse es pago pero opcional, y las mejoras dentro de la versión son gratis. Precio solo por WhatsApp o correo. Hay distribuidores, sin nombres publicados. — [Lepton](https://www.lepton.com.ar/web/productos/software-para-carpinteria-de-aluminio-y-pvc)
- **Productos hermanos [V]:** WinMaker Starter, "WinMaker Web" gratuito (noticia del 16-05-2017), "Winmaker Aluar Web" (noticia del 21-12-2018), Lepton Optimizer, Lepton Pack y TabMaker. — [Lepton](https://www.lepton.com.ar/web/productos/software-para-carpinteria-de-aluminio-y-pvc)

#### Otros productos de Chile
- **Sistema Zeta, de VEXZETA Superfachadas (dominio .cl) [V]:** se dibuja el diseño y la lista de materiales sale automáticamente. Incluye cotización de aluminio y PVC, pautas de corte optimizadas, órdenes de compra, organización de producción y creación de líneas y diseños propios. Se paga por año de servicio, con soporte, capacitación online y actualizaciones gratis ("muy fáciles de instalar") [I: probable programa de escritorio]. No publica precio; ofrece demo. — [Vexzeta](https://vexzeta.cl/software/)

#### Argentina
- **OP 2.1, de Megevand Soft (+54; también "MegevandSoft México") [V]:**
  - Diseño, presupuestos, costos, optimizador lineal de perfiles y de superficies (vidrios, paños).
  - Etiquetas, pedidos a proveedores, gráficos 3D a escala y archivos para máquinas de corte.
  - Stock, permisos por usuario y cuatro formas de calcular la mano de obra (por m², unidad, tarea o perímetro).
  - Cortinas de enrollar. Se puede pedir que carguen una marca que falte.
  - Licencias "Home" (cupos limitados) y "Professional" (ilimitada). Demo de 10 días. Sin precios publicados.

  Fuente: [Megevand](https://megevandsoft.com/mexico/)
- **OP 2.1 distribuido por Alsafex, extrusora argentina [V]:** licencia gratis por 6 meses al registrarse. Trae los sistemas propios de Alsafex: Niza, Mediterránea, Delta Plus, Tradicional Plus, Frente Integral y Frame. — [Alsafex](https://alsafex.com.ar/software-op-2-1/)
- **OP 2.1 en otros canales [V]:** también lo ofrecen Flamia y la escuela MDT, que vende un curso grabado. — [Flamia](https://www.flamia.com.ar/software.php); [MDT](https://www.mdtargentina.com/curso/grabacion-op21)
- **Open2D2, de Germán Massacesi (© 2021) [V]:**
  - Cada abertura se programa con sus descuentos, perfiles y accesorios, y con eso se arman obras.
  - Emite presupuestos, órdenes de producción, pedidos y planillas de corte optimizadas.
  - Informes de desperdicio, gestor de recortes y gestión de clientes, obras y proveedores.
  - Hay licencias en México, Uruguay, Chile y Colombia.
  - La versión gratuita trae la línea "General" de FEXA; la PRO incluye todos los sistemas FEXA.

  Fuente: [Open2D2](https://emanuelalu2011.wixsite.com/open2d2)
- **Pca-Net 2.5, de Abernetica [V]:** programa de cálculo de aberturas de aluminio que dice cubrir "todas las líneas existentes en Argentina". La página dio 404 el 21-10-2026, así que la descripción viene solo del snippet del buscador [I: producto posiblemente discontinuado]. — [Abernetica](https://abernetica.com.ar/pca250.html)

#### México
- **Optiglass [V]:** escritorio Windows (instalador .exe), con teléfono +52.
  - Cotización, optimización de cortes de vidrio y aluminio, despiece, análisis de sobrantes y reportes de costo.
  - Marcas: Cuprum, Indalum y Extrusiones Metálicas. Líneas: EuroVent, Panorama 2" y 3", EuroAlum y Línea Española.
  - Planes de renta sin montos publicados. Un mes de prueba con capacitación.

  Fuente: [Optiglass](https://optiglass-software.com/)
- **SEIA (Software Experto en Ingeniería de Aluminio) [V]:** se presenta como "el mejor software en México" para cancelería. Dice traer fórmulas de armado para 120 modelos y las líneas Panorama y Eurovent. — [SEIA](https://aluminioseia.wixsite.com/seia/software)
  - Se vende a crédito vía Kueski Pay, con despiece, órdenes de corte, precios unitarios y sobrantes. — [Kueski Pay](https://www.kueskipay.com/para-ti/tiendas/sysinfo-mx)
- **AL Calculadora [V]:** "hecho en México por alumineros", para Android (Google Play) y Windows (.exe).
  - Optimización de cortes de mayor a menor con reutilización de sobrantes.
  - Cotizador con márgenes, creador de fórmulas y descuentos propios, y base de precios personal.
  - Funciona sin conexión. Planes mensual y anual pagados por Google Play, sin montos publicados.

  Fuente: [AL Calculadora](https://al-calculadora.vercel.app/)
- **App Indalum, del extrusor mexicano (gratis, iOS y Android) [V]:** a partir de medidas y estilo calcula descuentos de perfiles, herrajes, medida de vidrio y tipo de corte, para la línea Euroalum. También busca perfiles por clave y muestra distribuidores, catálogos y guías de armado. — [Indalum](https://indalum.com.mx/en/indalum-facilita-la-labor-de-los-alumineros-con-app/); [App Store](https://apps.apple.com/us/app/indalum/id1541789564?l=es-MX); [Google Play](https://play.google.com/store/apps/details?id=com.indalum.app&hl=en_US)
- **Instalador.mx (Android) [V]:** cotizaciones, desglose automático de material, cortes optimizados y reportes con fotos para fabricantes de aluminio. — [Google Play](https://play.google.com/store/apps/details?id=com.incodesa.instaladormx&hl=en_US)
- **Alusystem Software [V]:** cotizador por suscripción para ventanas, puertas y barandales de aluminio y vidrio templado; según un resumen de buscador opera desde EE. UU. El índice dio 404 el 21-10-2026. — [Alusystem TyC](http://www.alusystemsoftware.com/TyC.aspx)

#### Colombia
- **Alum Software [V]:** web (builder.alumsoftware.com y app.alumsoftware.com), precios en COP y pago con Wompi.
  - Módulos: comercial (cotizaciones, proformas, versiones, descuentos), producción (optimización de pedidos y perfiles en barra de 6 m, planos) y parametrización (precios, costos, historial de precios).
  - Flujo: subir o importar la lista de precios de perfiles Alumina, cotizar, generar despiece, BOM y planos, y exportar pedidos.
  - Planes por año:

    | Plan | Precio | Usuarios | Cotizaciones/año |
    |---|---|---|---|
    | Standard | COP 900.000 | 2 | 250 |
    | Premium | COP 1.500.000 | 3 | 600 (y 600 optimizaciones) |
    | Profesional | COP 2.500.000 | 5 | 3.000 (y 50 diseños nuevos) |

  - Dice tener "+400 empresas" y "+35% ventas" (marketing). Sin prueba gratis, solo demo.

  Fuente: [Alum](https://alumsoftware.com/)
- **Apps Android pequeñas, sin precios verificados [V]:**
  - "Cotizador de Ventanas" y "Despiece de ventanas" de AlejandroDev1020, con unas 1.000 descargas cada una. — [Cotizador](https://play.google.com/store/apps/details?id=com.alejodev.cotizadorventanas); [Despiece](https://play.google.com/store/apps/details?id=com.alejoDev.Despiece&hl=en_US)
  - "Ventanapp", para sistemas P65, P92, tradicional y salomónica. — [Google Play](https://play.google.com/store/apps/details?id=com.edcloser.winap&hl=en_US)
  - "CalcuVent", con anuncios. — [Google Play](https://play.google.com/store/apps/details?id=cal.calcuvent&hl=en_US)

#### Pan-hispano, nuevo en el mercado
- **Luminio, de zGenWare LLC [V]:** web, PWA, Android, iPhone, Windows y Linux.
  - Hojas de corte con deducciones propias, cotización profesional y cobro online (Stripe, Klarna, Afterpay; depósito y saldo).
  - Hojas de compra, calendario de producción, roles y exportación a Excel.
  - Funciones de IA: chat con voz, diseño a partir de texto y análisis de materiales por foto.
  - Planes en USD por mes: Básico 24,99 (30 créditos de IA), Premium 34,99 (80) y Universe 69,99 (100). Prueba de 10 días.
  - No menciona extrusores ni líneas.

  Fuente: [Luminio](https://luminio.app/)

#### España
- **winDOS [V]:** web 100% en la nube (© 2022, teléfono +34), pensada para tablet y móvil.
  - Módulos: diseño en configurador gráfico, presupuestos (con series cargadas o manuales), producción (materiales, hojas de fabricación, cortes y optimización con un clic), pedidos, facturación y usuarios con permisos.
  - El configurador se puede incrustar en la web del taller, y hay un portal de captación (cambia-tus-ventanas.com).
  - Cuota mensual sin licencia, sin monto publicado. Prueba de 7 días.

  Fuente: [winDOS](https://windosweb.com/)
- **GAIA PRODUCTOR Aluminio, de Gaia Servicios Informáticos SL (Alicante y Madrid) [V]:**
  - Escritorio más "PRODUCTOR web" sincronizado y la app Android eAlbaranes.
  - Dice tener 30 módulos: contabilidad, SEPA, factura electrónica, SII, stock, marcado CE, cálculo térmico CTE y etiqueta de eficiencia (EEV).
  - Cada licencia incluye datos de 3 proveedores de perfiles.
  - Se ofrece en alquiler, renting a 3 años o compra con 6 meses de mantenimiento. Sin precios publicados.

  Fuente: [GAIA](https://www.gaia-soft.com/programas/productor-aluminio/)
- **Sicar2, de CIN [V]:** presupuestos, pedidos, facturas, listas de corte, producción y conexión a máquinas; DXF y optimización en varias longitudes de barra (anuncio de 2016). — [Interempresas](https://www.interempresas.net/Pintura/162453-Sicar2-la-aplicacion-informatica-para-la-gestion-de-carpinterias-de-aluminio-y-PVC-de-CIN.html)
- **Software de Cortizo [V, material de 2010]:** despiece, presupuestos, optimización, stock, compras, facturación y conexión a máquinas, con base de datos de sistemas Cortizo. — [Interempresas](https://www.interempresas.net/Construccion/38201-Cortizo-lanza-un-software-de-gestion-integral-de-carpinteria.html)
- **Prefsuite, de Preference [V, caso de éxito del proveedor]:** usado por un fabricante español de aluminio y PVC con familias de sistemas, PrefCAM para máquinas y PrefCIM en planta. — [Interempresas](https://www.interempresas.net/Construccion/151441-Inrialsa-compromiso-de-entrega-y-calidad.html)
- **Winperfil [V]:** aparece como requisito en ofertas de empleo de administrativos de carpintería de aluminio en España; sin datos oficiales encontrados. — [Infojobs](https://www.infojobs.net/ofertas-trabajo/winperfil)
- **Klaes [V, abril de 2026]:** ERP alemán "Klaes Professional", del presupuesto a la entrega, presente en prensa española del sector. — [Interempresas](https://www.interempresas.net/Construccion/627590-Klaes-software-robusto-y-en-continua-evolucion-para-los-fabricantes-de-ventanas.html)

### Inferences
- [I] En el segmento de talleres pequeños de Chile compiten de verdad NuveraPRO (pago, varias marcas), Winart (gratis para clientes Haustek/Winhouse) y Sistema Zeta. Los ERP españoles o alemanes (Prefsuite, Klaes, GAIA) apuntan a fábricas medianas y grandes, con otros precios.
- [I] El precio de referencia del segmento web pequeño queda entre USD 25 y 35 al mes: NuveraPRO cobra $25.000–32.500 CLP, Luminio USD 24,99–34,99 y Alum entre COP 900.000 y 2,5 millones al año. Un SaaS nuevo que cobre mucho más tendrá que justificarlo con resultados claros, como menos errores, catálogo correcto o cobro integrado.
- [I] La competencia más dura en precio es el software gratuito de los extrusores y distribuidores (Winart, la app Indalum, OP 2.1 de Alsafex, Open2D2 con FEXA). A cambio, encierra al taller en una sola marca.
- [I] NuveraPRO agrupa todo el aluminio bajo "Gestión VAP Aluminio" y no publica qué marcas de PVC soporta. Junto con lo que contó el dueño (orden de corte y precios del PRO6004), esto sugiere que la fidelidad por serie es su punto débil.

### Gaps
- No encontré la lista pública de marcas y series de NuveraPRO. Tampoco confirmé si Proline PRO6004 aparece como marca soportada ni cómo define el "orden" de corte. Requiere una cuenta de prueba de 15 días.
- No hay precios públicos de WinMaker 10, Optiglass, OP 2.1, Sistema Zeta, winDOS, GAIA, SEIA ni AL Calculadora.
- No encontré productos con presencia propia y clara en Perú. Las búsquedas por Perú no dieron software local, y la presencia peruana de los demás no está confirmada.
- No verifiqué si Indalum Chile, Alumco o Rehau Chile ofrecen cotizadores propios. Ninguna búsqueda devolvió un software oficial de esas marcas en Chile.

---

## 2. Interfaz y experiencia de uso, capturas, tutoriales y manuales

### Takeaway
Casi todos los productos se aprenden con videos de YouTube y soporte por WhatsApp, no con manuales escritos. En la información pública, la interfaz va del ASP.NET clásico (NuveraPRO) y el escritorio Windows con exigencias de hardware (WinMaker 10, Optiglass) a webs táctiles (winDOS) y PWA con IA (Luminio). Faltó evidencia visual directa: las páginas de YouTube y Google Play no devolvieron su contenido al fetcher.

### Cited Findings
- **NuveraPRO [V]:** login con "Bienvenido/a!" y "Ingresar ó Registrese", y URL `.aspx`. — [NuveraPRO](https://www.nuverapro.com/)
  - El menú público tiene Inicio, Precios, Marcas & Series, Contacto y 1eros Pasos.
  - La única captura en "Primeros pasos" se llama `SeleccionaItem.jpg` [I: muestra el paso de elegir un tipo de ventana de un catálogo de ítems].
  - Fuente: [Primeros pasos](https://www.nuverapro.com/cotizadorpvcaluminio/primeros-pasos.html)
- **Tutoriales de NuveraPRO [V]:** ver la lista de videos en la sección 1. Los títulos muestran el modelo mental del producto: dar de alta marcas, cotizar y luego emitir informes. — [Canal](https://www.youtube.com/@nuverapro)
  - También aparece un video "CotizaPro - Pasos Iniciales". No verifiqué si tiene relación con NuveraPRO. — [YouTube](https://www.youtube.com/watch?v=8x-z2xzlTFw)
- **Winart [V]:** la página muestra una captura del inicio, otra de un técnico trabajando con perfiles junto a la pantalla, un video de presentación oficial y un tutorial paso a paso. No ofrece manual descargable. — [Haustek Winart](https://haustek.cl/winart/)
- **WinMaker 10 [V]:** pide GPU dedicada, así que trabaja con gráficos pesados (frentes y planos). "Panel de Tareas" para descargar mejoras. Hay un manual de Leptonpack sobre modificar piezas en 3D, fechado el 05-06-2024. — [Lepton](https://www.lepton.com.ar/web/productos/software-para-carpinteria-de-aluminio-y-pvc)
- **winDOS [V]:** pensado para que el vendedor cotice, negocie y cierre en casa del cliente desde una tablet. — [winDOS](https://windosweb.com/)
- **Luminio [V]:** PWA multiplataforma con chat y voz de IA, diseño a partir de texto y análisis por foto. — [Luminio](https://luminio.app/)
- **Open2D2 [V]:** sitio hecho en Wix, tutoriales en YouTube, biblioteca compartida de más de 90 aberturas y un "Centro de descargas". — [Open2D2](https://emanuelalu2011.wixsite.com/open2d2)
- **OP 2.1 [V]:** ofrece interfaz "amigable", visualización 3D y soporte remoto. MDT vende un curso grabado del programa. — [Alsafex](https://alsafex.com.ar/software-op-2-1/); [MDT](https://www.mdtargentina.com/curso/grabacion-op21)
- **AL Calculadora [V]:** tiene "constructor visual de piezas" y "curso oficial"; el desarrollador se difunde por TikTok (@josueftm). — [AL Calculadora](https://al-calculadora.vercel.app/)
- **Scribd [V]:** no encontré manuales de WinMaker, NuveraPRO ni Winart. La búsqueda solo devolvió documentos sin relación. — [Scribd, resultado no relacionado](https://www.scribd.com/document/685810000/Window)

### Inferences
- [I] Que existan cursos pagados (MDT para OP 2.1, el "curso oficial" de AL Calculadora) y "capacitación permanente" (NuveraPRO, Winart con ejecutivo comercial) indica que estas herramientas no se explican solas. Configurar series y descuentos exige un experto.
- [I] Los productos de escritorio con licencia física (WinMaker, Optiglass, OP 2.1) dificultan trabajar en terreno y entre varias personas. Los productos web (NuveraPRO, Winart, winDOS, Alum, Luminio) lo resuelven, pero con una interfaz de formularios antigua o sin profundidad técnica.

### Gaps
- No pude obtener capturas, duración, marcas de tiempo, fechas exactas, número de vistas ni comentarios de los videos: YouTube y Google Play no devolvieron contenido al fetcher. Hay que revisarlos a mano con navegador.
- No encontré manuales en PDF ni Scribd de NuveraPRO, Winart ni WinMaker 10.

---

## 3. Manejo del catálogo: catálogos precargados de extrusores locales y series y precios propios

### Takeaway
El catálogo es el centro de la competencia, y se resuelve de cuatro maneras:
- **El extrusor o distribuidor carga y regala su catálogo**, con un solo proveedor: Winart/Haustek, OP 2.1/Alsafex, FEXA en Open2D2, Indalum Euroalum y Winmaker Aluar Web.
- **El proveedor del software mantiene varias marcas** y cobra por marca: NuveraPRO.
- **El usuario importa su lista de precios**: Alum con Alumina, AL Calculadora y Luminio con deducciones propias.
- **Bases preconfiguradas con recálculo por costo**: WinMaker y GAIA.

Ningún producto publica cómo verifica que los descuentos y el orden de corte coincidan con el manual oficial de cada serie.

### Cited Findings
- **NuveraPRO [V]:**
  - Cada proveedor de PVC es una marca facturable; todo el aluminio es una sola marca, "Gestión VAP Aluminio".
  - Dice usar "pautas de corte oficiales de los principales proveedores de PVC", sin nombrarlos.
  - El paso 3 de la puesta en marcha incluye "tipos de precio" según el resumen del buscador. La página no los describe.
  - Fuentes: [Marcas](https://www.nuverapro.com/cotizadorpvcaluminio/marcas.html); [NuveraPRO](https://www.nuverapro.com/cotizadorpvcaluminio/); [Primeros pasos](https://www.nuverapro.com/cotizadorpvcaluminio/primeros-pasos.html)
  - [Dueño] Con Proline PRO6004 aplicó precios propios en vez de los del usuario o proveedor, y el orden de corte salió mal.
- **Winart [V]:** catálogo de PVC de Haustek. No nombra las series. — [Haustek Winart](https://haustek.cl/winart/)
- **WinMaker 10 [V]:** listas de precios armadas desde las bases de WinMaker que se recalculan al cambiar el costo de la materia prima. Cambia de marca o línea con un clic. — [Lepton](https://www.lepton.com.ar/web/productos/software-para-carpinteria-de-aluminio-y-pvc)
- **Open2D2 [V]:** permite ingresar cualquier extrusora, línea, perfil o accesorio. — [Open2D2](https://emanuelalu2011.wixsite.com/open2d2)
  - Su biblioteca comunitaria comparte descuentos de líneas argentinas: Herrero, Ekonal, Modena 1 y 2, A30, A40, A40RPT, Altezza, Rotonda 640 y 750, Nordical, HA62, L220, Delta Plus y Tradicional Plus.
  - Los sistemas de FEXA los carga esa empresa.
- **OP 2.1 [V]:** Alsafex mantiene sus propias líneas dentro del programa. — [Alsafex](https://alsafex.com.ar/software-op-2-1/)
  - Megevand carga a pedido las marcas que no están en su base. — [Megevand](https://megevandsoft.com/mexico/)
- **Optiglass [V]:** Cuprum, Indalum y Extrusiones Metálicas, con líneas EuroVent, Panorama y EuroAlum. — [Optiglass](https://optiglass-software.com/)
- **SEIA [V]:** dice traer fórmulas de armado para 120 modelos (Panorama, Eurovent). — [SEIA](https://aluminioseia.wixsite.com/seia/software)
- **App Indalum [V]:** solo la línea Euroalum. — [Indalum](https://indalum.com.mx/en/indalum-facilita-la-labor-de-los-alumineros-con-app/)
- **Alum [V]:** importa la lista de precios de perfiles Alumina, el extrusor colombiano, y guarda historial de precios. — [Alum](https://alumsoftware.com/)
- **AL Calculadora [V]:** creador de fórmulas y descuentos, más fórmulas precargadas para piezas comunes. Admite varias listas de precios por línea o proveedor. — [AL Calculadora](https://al-calculadora.vercel.app/)
- **GAIA [V]:** 3 proveedores de perfiles por licencia, de 9 de aluminio, 1 de herrajes y 1 de PVC disponibles. No los nombra. — [GAIA](https://www.gaia-soft.com/programas/productor-aluminio/)
- **Herramienta comunitaria [V]:** "Indalum Tool / mundocalculador", hecha por MundoCanceles, es open source en GitHub. Calcula despiece y cotizaciones con catálogos de perfiles y herrajes, costos editables y PDF. No es oficial de Indalum. — [GitHub](https://github.com/mundocanceles/mundocalculador.io); [Demo](https://mundocanceles.github.io/mundocalculador.io/)
- **Mercado de perfiles en Chile [V]:** Rehau dice llevar 30 años en Chile. — [Rehau Chile](https://www.rehau.com/downloads/637144/folleto-ventanas-rehau-chile.pdf)
  - Una tesis de la Universidad de Chile (2021) nombra a VEKA, Veratec, Kömmerling y Deceuninck como proveedores de perfiles de PVC. — [Repositorio U. de Chile](https://repositorio.uchile.cl/handle/2250/194345)
  - Proline (Turquía) entra vía distribuidores como Aluminios 2000. — [Aluminios 2000](https://aluminios2000.com/categorias/linea-pro-6004/)

### Inferences
- [I] En Chile conviven extrusores locales de aluminio y muchos perfiles de PVC importados (alemanes, belgas y turcos). Un catálogo que solo cubra las marcas grandes deja fuera a los talleres que compran series importadas más baratas, como Proline. Es justo el caso que el dueño vio fallar en NuveraPRO.
- [I] Que la biblioteca comunitaria de Open2D2 exista y que AL Calculadora tenga un creador de fórmulas muestra la demanda: los carpinteros quieren cargar sus propios descuentos sin depender del proveedor, y compartirlos.
- [I] Ningún producto muestra trazabilidad de la fórmula: de qué manual sale cada descuento, quién lo validó y en qué versión. Es un hueco directo para el motor determinista con golden cases de DEKOPEN.

### Gaps
- No encontré qué series de Indalum Chile, Alumco o Proline Chile están precargadas en NuveraPRO, Winart o Sistema Zeta.
- No verifiqué si Indalum Chile o Alumco publican sus "pautas de corte" en formato digital.

---

## 4. Quejas y elogios de los usuarios

### Takeaway
No encontré reseñas independientes públicas (Capterra, foros o hilos indexados de Facebook) sobre NuveraPRO, Winart, WinMaker 10 ni los demás productos de nicho. Lo disponible son testimonios y cifras de los propios proveedores, más la experiencia directa del dueño de DEKOPEN. Esa falta de evidencia también es un dato.

### Cited Findings
- **NuveraPRO [V]:** su página no muestra testimonios. — [NuveraPRO](https://www.nuverapro.com/cotizadorpvcaluminio/)
  - [Dueño] Fallas en precios, configuración y continuidad: orden de corte del PRO6004 incorrecto y precios propios.
- **Alum [V, testimonios del proveedor]:**
  - Cristian Correa dice haber pasado "de 40 horas a 5 minutos por despiece" y ahorrado cerca de COP 10.000.000.
  - Vidrios Aacer dice haber pasado de 3 personas a 1 en la optimización de cortes.
  - Fuente: [Alum](https://alumsoftware.com/)
- **Advertencia de Vendomia, ERP de carpintería metálica [V, material de un proveedor]:** dice que los programas gratuitos suelen ser muy básicos y no gestionan por proyecto. — [Vendomia](https://vendomia.com/blog/software-carpinteria/)
- **Apps en Google Play [V]:** las fichas consultadas no mostraron reseñas al fetcher. Son apps de bajo volumen (unas 1.000 descargas en Cotizador de Ventanas, Despiece y CalcuVent; unas 10.000 en Qwind). — [Cotizador de Ventanas](https://play.google.com/store/apps/details?id=com.alejodev.cotizadorventanas); [Qwind](https://play.google.com/store/apps/details?id=com.qwind.exquisite.windows&hl=en_US)
- **Señales de lo que se valora, por lo que los proveedores destacan [V]:**
  - Sin contratos y sin límite de usuarios (NuveraPRO). — [NuveraPRO](https://www.nuverapro.com/cotizadorpvcaluminio/)
  - Funcionar sin conexión (AL Calculadora). — [AL Calculadora](https://al-calculadora.vercel.app/)
  - Gratuidad (Winart, la app Indalum, OP 2.1 de Alsafex por 6 meses). — [Haustek](https://haustek.cl/winart/); [Alsafex](https://alsafex.com.ar/software-op-2-1/)
  - Soporte por WhatsApp (NuveraPRO, Lepton, Megevand). — [Lepton](https://www.lepton.com.ar/web/productos/software-para-carpinteria-de-aluminio-y-pvc); [Megevand](https://megevandsoft.com/mexico/)

### Inferences
- [I] Los dolores que se repiten se deducen de lo que los proveedores prometen resolver: las horas de despiece manual, el desperdicio de barra, los precios desactualizados (WinMaker recalcula por costo de materia prima; Alum guarda historial de precios) y la dependencia de un experto para configurar.
- [I] La experiencia del dueño con NuveraPRO encaja con el riesgo estructural de un catálogo mantenido por el proveedor del software sin trazabilidad: cuando una serie no es de las grandes, el orden y los descuentos pueden no coincidir con el manual del extrusor.

### Gaps
- Los grupos de Facebook de carpinteros de aluminio y PVC (Chile, Argentina, México) no están indexados para búsqueda web. Hay que revisarlos a mano con sesión iniciada.
- No pude obtener comentarios de YouTube de los canales de NuveraPRO, Haustek, Lepton ni Open2D2.
- No hay perfiles en Capterra ni en G2 de estos productos de nicho LatAm. Solo existen para ERP mayores.

---

## 5. Brechas donde un SaaS web moderno con IA podría ganar con claridad

### Takeaway
Las mayores oportunidades son cinco:
1. **Fidelidad verificable por serie**, incluidos el orden de corte y los descuentos del manual oficial, también para series importadas como Proline.
2. **Precios del propio taller** con historial y recálculo.
3. **Flujo continuo**: cotización, orden de producción, compras, instalación y cobro, hoy repartido entre varias herramientas.
4. **Web y móvil de verdad**, sin llave USB ni Windows.
5. **IA útil y segura**: dictado, foto o croquis a ventana configurada, sin que la IA invente números.

Luminio ya promete IA y cobro, pero sin catálogo técnico de extrusores.

### Cited Findings
- **Funciones de IA [V]:** solo Luminio anuncia chat, diseño por texto y análisis por foto. — [Luminio](https://luminio.app/)
  - NuveraPRO, Alum, winDOS, AL Calculadora y Optiglass no mencionan IA. — [NuveraPRO](https://www.nuverapro.com/cotizadorpvcaluminio/); [Alum](https://alumsoftware.com/); [winDOS](https://windosweb.com/); [AL Calculadora](https://al-calculadora.vercel.app/); [Optiglass](https://optiglass-software.com/)
- **Cobro integrado [V]:** solo Luminio (Stripe, Klarna, Afterpay). — [Luminio](https://luminio.app/)
  - winDOS factura dentro del programa. — [winDOS](https://windosweb.com/)
  - NuveraPRO no anuncia compras, producción ni cobro: termina en informes. — [NuveraPRO](https://www.nuverapro.com/cotizadorpvcaluminio/)
- **Escritorio pesado [V]:** WinMaker 10 exige Windows, GPU dedicada, 50 GB de disco y puerto USB. — [Lepton](https://www.lepton.com.ar/web/productos/software-para-carpinteria-de-aluminio-y-pvc)
  - Optiglass se instala con un .exe. — [Optiglass](https://optiglass-software.com/)
- **Catálogo opaco [V]:** NuveraPRO no publica sus marcas soportadas. — [Marcas](https://www.nuverapro.com/cotizadorpvcaluminio/marcas.html)
  - Winart no nombra series. — [Haustek](https://haustek.cl/winart/)
- **Normativa y eficiencia [V]:** solo GAIA (España) anuncia marcado CE, cálculo térmico y etiqueta energética. — [GAIA](https://www.gaia-soft.com/programas/productor-aluminio/)
  - Proline publica el Uf del PRO6004 (1,49 W/m²K), un dato que un cotizador podría usar. — [Proline](https://www.prolinepvc.com/en/urun/pro6004-series)

### Inferences
- [I] **Catálogo trazable por serie** (versión, manual de origen, golden case por serie), con apertura a series de nicho o importadas y validación al 0,01 mm. Ataca directamente la falla que vivió el dueño y que ningún competidor documenta.
- [I] **Precio de lista del taller primero.** El cotizador nunca debería imponer "precios propios" del proveedor del software. Faltan importación de listas (como Alum con Alumina), historial y recálculo masivo (como WinMaker), de forma transparente.
- [I] **Continuidad del flujo.** NuveraPRO y Winart terminan en informes. Hay espacio para órdenes de producción, compras con proveedores reales, agenda de instalación y cobro con medios locales de Chile (Webpay, transferencia), no solo Stripe.
- [I] **IA con límites claros.** La IA traduce intención (voz, foto, croquis o texto del cliente) a una configuración, pero el motor determinista calcula todos los números. Es un contraste deliberado con la "IA de diseño por texto" de Luminio, que no muestra cómo garantiza la exactitud.
- [I] **Precio.** El ancla del mercado está en USD 25–35 al mes (NuveraPRO, Luminio). La gratuidad del software de distribuidores (Winart, Indalum, Alsafex) obliga a demostrar el ahorro concreto: horas de despiece y desperdicio de barra.
- [I] **Comunidad.** La biblioteca compartida de Open2D2 (más de 90 aberturas) indica que una biblioteca de tipologías por serie, revisada y versionada, puede ser una ventaja de red.

### Gaps
- No hay datos de cuota de mercado ni de número de clientes verificados para ningún producto. El "+400 empresas" de Alum y los 297 usuarios en 24 horas de NuveraPRO son cifras de los propios proveedores.
- Falta comprobar con una cuenta de prueba qué tan bien resuelve NuveraPRO las series de aluminio chilenas (Indalum, Alumco) y si permite editar el orden de corte o los descuentos.
