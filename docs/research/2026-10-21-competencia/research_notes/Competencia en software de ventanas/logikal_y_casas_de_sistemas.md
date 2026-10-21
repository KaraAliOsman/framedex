# Orgadata/Forterro Logikal, Schüco SchüCal y herramientas de las casas de sistemas (aluminio/PVC)

Fecha de investigación: 2026-10-21. Fuentes: webs oficiales (logikal-software.com, help.orgadata.com, schueco.com, wicona.com, hivecpq.com), prensa sectorial (interempresas.net, glasstimes.co.uk, specificationonline.co.uk). Casi todo el material es de los propios fabricantes. Se encontraron muy pocas opiniones independientes de usuarios.

Convención: en «Cited Findings» solo van hechos con URL. «Inferences» son conclusiones mías. «Gaps» recoge lo que no se pudo verificar.

---

## 1. Módulos y flujo completo (proyecto → catálogo → editor → cortes → herrajes → vidrio → optimización → precio → oferta → producción → CNC → compras → estática/térmica)

### Takeaway
Logikal (Orgadata, hoy Forterro Logikal GmbH) es el estándar independiente de las casas de sistemas. Es un ERP técnico de escritorio para Windows: más de 450 catálogos de proveedores mantenidos por el propio Forterro, un editor de «posiciones» basado en una rejilla (grid) con un «logic check» de compatibilidad, cálculo de material, mano de obra y precio, oferta, pedidos, CNC, MES, estática, Uw, huella de carbono y BIM. SchüCal (Schüco) y WICTOP (Hydro/WICONA) cubren el mismo flujo, pero cada uno solo para su marca. Las demás casas (Reynaers, Cortizo, Rehau) usan software de terceros adaptado (Preference/PrefSuite, un paquete comprado + Hive CPQ) o portales y configuradores parciales.

### Cited Findings

**Logikal: empresa, escala y propiedad**
- 12-01-2026: Orgadata anuncia que pasa a operar bajo la marca Forterro. Forterro compró Orgadata AG y antes el BM Group (software de ventanas, puertas y fachadas en Reino Unido e Irlanda). Bernd Hillbrands, fundador de Orgadata, dirige la unidad de negocio dentro de Forterro. Productos que se mantienen: Logikal, Logikal MES, Unilink y SimplyTag. Forterro dice dar servicio a «more than 25,000 industrial businesses» (cifra del grupo, no de Logikal), con más de 2.500 empleados — [Logikal/Forterro news](https://www.logikal-software.com/en/news/orgadata-to-operate-under-forterro-name)
- 14-07-2026: cambio de razón social de Orgadata Software-Dienstleistungen AG a Forterro Logikal GmbH, con sede en Leer (Alemania) — [Orgadata Becomes Forterro Logikal GmbH](https://www.logikal-software.com/en/news/orgadata-umfirmierung); [FAQ](https://www.logikal-software.com/en/faq)
- Más de 18.000 usuarios (fabricantes, proyectistas y arquitectos), más de 450 proveedores o catálogos y «almost 600 colleagues» en la unidad — [logikal-software.com](https://www.logikal-software.com/en/). El software lleva 30 años en el mercado — [Logikal front](https://www.logikal-software.com/en/logikal-front)
- Un PDF de Würth habla de más de 18.000 licencias en uso en el mundo — [Würth in Logikal (PDF)](https://www.wuerth.de/web/media/downloads/pdf/Orgadata-Wuerth_in_Logikal.pdf)

**Logikal: mapa de módulos (web oficial)**
- Soluciones listadas: Design & Calculation, CNC Integration, Ordering (cálculo de necesidades de material y preparación de pedidos), Digitalised Production (MES), BIM, CAD Integration, Planning & Preparation, Component Labelling, Configurators, Custom Solutions/Dataservice e Interfaces. SimplyTag pone un QR en cada elemento con sus datos de producto y sirve para el marcado CE — [logikal-software.com](https://www.logikal-software.com/en/)
- Licencia por módulos: «basic version with core functions» ampliable con módulos y catálogos. Módulos citados: CNC, CAD Suite 2D, 3D Interface, BIM, Machining and bar drawings, Fabrication phases. Los catálogos de proveedor se contratan por suscripción («subscribe to the product catalogues relevant to your business») — [FAQ](https://www.logikal-software.com/en/faq)
- Manuales de la ayuda online: Installation & Setup, Home screen, Project centre, Input of elements, Cross sections, Estimation & Labour hours, Printouts, 2D Optimisation, Grid price list, Statics, CAD, CNC, Database, Settings, Interfaces, MES, Standards & Regulations, Dataservices, Orgadata ID y SimplyTag — [help.orgadata.com/documentation](https://help.orgadata.com/en/documentation/)

**Logikal: catálogos y modelo de datos**
- Datos técnicos y comerciales de más de 450 proveedores y más de 7 millones de artículos (perfiles, herrajes, vidrio, accesorios). Forterro mantiene datos técnicos y precios de forma continua y los entrega por descargas de actualización. Se pueden seguir usando listas de precios antiguas o descuentos por proyecto. Los precios de artículo se ajustan con descuentos, recargos, «multis» o precios por kg — [FAQ](https://www.logikal-software.com/en/faq)
- Logikal 14: los catálogos se guardan en repositorios separados por fabricante, con copias de seguridad automáticas — [Newsletter 14](https://help.orgadata.com/en/news/newsletter/newsletter-14/)
- Hay casas de sistemas que distribuyen Logikal con su catálogo: Alspec y Criterion Industries (Australia), Senior Architectural (Reino Unido, con «LogiKal Lite»), Sheerline — [Alspec](https://alspec.com.au/logikal); [Criterion](https://www.criterionindustries.com.au/pages/logikal); [Senior, 23-04-2019](https://www.seniorarchitectural.co.uk/?p=19333); [Glass Times – Sheerline](https://glasstimes.co.uk/products/sheerline-announces-logikal-integration/)
- LogiKal Lite (2019): versión reducida para el mercado residencial, exclusiva para la red de Senior. Se adapta a cada cliente con solo las funciones que necesita y elementos personalizados en la oferta. El desarrollador afirma que se generan ofertas «within an hour of setting up the system» — [Senior Architectural, 2019](https://www.seniorarchitectural.co.uk/?p=19333)

**Logikal: estructura proyecto → posición → elemento**
- En el Project centre se crean proyectos, posiciones, posiciones alternativas, posiciones de material, de texto y de herraje, «position frameworks», plantillas de elemento, biblioteca de posiciones, gestión de elementos, división de posiciones, fases y fases de fabricación. También se gestionan los artículos de proyecto (vidrio, paneles, perfiles, conexiones a muro y herrajes de proyecto), opciones de artículo (restos de longitud, restos de cantidad, longitudes especiales, perfiles compuestos, longitudes de barra), lugares de montaje, buscar y reemplazar, variables de proyecto, historial de posición y textos de comentario — [Project centre](https://help.orgadata.com/en/documentation/project-centre/)
- Logikal 14: fases de fabricación asignables por separado a muros cortina e inserciones separadas, y papelera de reciclaje de posiciones por proyecto — [Newsletter 14](https://help.orgadata.com/en/news/newsletter/newsletter-14/)

**Logikal: editor de elementos («Input of elements»)**
- Rejilla (Grid): definir campos en ancho y alto, transferir la rejilla desde otra posición, entrada libre, medidas de obra, inclinaciones (pitches), arcos, poner y borrar perfiles, montantes y travesaños, esquinas de vidrio, acoplamientos, perfiles añadidos, persianas, FFL (nivel de suelo terminado) y forjados — [Grid](https://help.orgadata.com/en/documentation/input-of-elements/windows-and-doors/grid/)
- Insertar montante: pestaña **Edit** → **Mullions** → posición medida desde la izquierda. Travesaño: **Transoms** → posición medida desde el FFL. En un campo parcial: **Mullion/Transom in partial field** → seleccionar el campo en el dibujo → indicar el número → **OK** — [Mullions and transoms](https://help.orgadata.com/en/documentation/input-of-elements/windows-and-doors/grid/mullions-and-transoms/)
- Elemento: tipo/función de hoja, selección de inserción (incluida puerta push-pull), propiedades de sistema, de posición y de perfil, montantes y travesaños. Herrajes: paquetes, bisagras, cierres, operación, cilindro, plan de cableado, cadena, selección con color. Acristalamiento: ventiladores en vidrio, junquillos/barrotillos, unión vidrio-vidrio. Artículos y datos adicionales. Herramientas de interfaz: vista 2D, vista 3D, dibujos de sección, banderas (flags), bloques de texto, cotas, lista de piezas, perfil favorito, invertir sentido de apertura — [Input of elements](https://help.orgadata.com/en/documentation/input-of-elements/)
- El «logic check» valida la compatibilidad de perfiles, herrajes, accesorios y requisitos técnicos: «Every element must be technically viable before it can be estimated, quoted or manufactured». El coste de material, producto y mano de obra sale del diseño, con tiempos y recargos «transparentes». Se pueden comparar variantes técnica y comercialmente. La estática y el valor U entran en el cálculo — [Design & Calculation](https://www.logikal-software.com/en/solutions/design-calculation)
- Avisos automáticos de datos faltantes, combinaciones inválidas y colisiones. Módulo CAD para formas especiales, conexiones a muro y piezas a medida. Oferta exportable, enviable o sincronizable con el ERP «en un clic» — [Logikal front](https://www.logikal-software.com/en/logikal-front)
- Logikal 14: colores de proveedor con propiedades filtrables (sistema de color, calidad, textura, brillo, ámbito de uso); diagramas de hoja en PVC que muestran el rango de refuerzo permitido según ancho y alto de hoja; cilindro preferido elegido a mano; vistas 2D/3D interior, exterior, lateral, superior e inferior; ajustes de sección organizados en pestañas (vista, acotación, exportación, capas) — [Newsletter 14](https://help.orgadata.com/en/news/newsletter/newsletter-14/)

**Logikal: optimización, CNC, MES, compras**
- «2D Optimisation» reparte cortes rectangulares de chapa en distintos formatos (formatos base, restos, áreas, trabajos, importación). Muestra hojas necesarias y desperdicio por hoja y total. Se abre desde Inicio → Programs → 2D-Optimisation. La página no trata la optimización de barras — [2D Optimisation](https://help.orgadata.com/en/documentation/2d-optimisation/)
- Changelog 12.6.1.1101 (15-12-2025): nuevo formato de sierra Rotox ZGS 317, códigos NC en formatos XML de Mecal, transferencia del conector Schüco CC 800, aviso al generar el fichero de máquina, cambios de cantidad vía interfaz ERP externa, importación a HiCAD, precios de myWarema/ROMAConnect y Declaración de Prestaciones (DoP) con elementos cortafuego — [Logikal Changelog](https://help.orgadata.com/en/news/changelog/logikal-changelog/)
- Changelog 14.0.2.204 (16-10-2026): módulo de estática italiano (cargas de viento), informe de predimensionado estático para todas las posiciones, CSV para el ERP Qomet. 12.6.1.1202 (23-01-2026): corrección del Uw en marcos separados (elevadoras-correderas). La mayoría de las entradas son correcciones de errores («again») — [Logikal Changelog](https://help.orgadata.com/en/news/changelog/logikal-changelog/)
- Logikal 14 CNC: vista 3D del mecanizado con sólidos y acabado del perfil — [Newsletter 14](https://help.orgadata.com/en/news/newsletter/newsletter-14/)
- Logikal MES: envía órdenes y datos a máquinas y estaciones, sigue el estado en tiempo real, analiza métricas y automatiza el control de producción en fábrica (FPC) y el marcado CE. El fabricante afirma «up to 20% more efficiently» en taller y presupuestos «up to 20% faster» — [Logikal front](https://www.logikal-software.com/en/logikal-front)
- Configuradores integrados de terceros dentro del flujo: vidrio (configuradores de los vidrieros conectados), buzones, protección solar y paneles de puerta. Lo elegido pasa a la posición — [Configurators](https://www.logikal-software.com/en/solutions/configurators)

**Logikal: normativa, estática y térmica**
- Logikal 14: Uw de barrotillos georgianos según EN ISO 10077-1; huella de carbono de producto (PCF) por posición según EN 15804, con categorías GWP; informe único de vigilancia de puertas cortafuego y cortahumo — [Newsletter 14](https://help.orgadata.com/en/news/newsletter/newsletter-14/)
- El manual de estática de la ayuda online figura como «currently being worked on» (sin contenido) — [Structural analysis](https://help.orgadata.com/en/documentation/structural-analysis/)
- Webinars «Logikal Essentials» sobre estática y proveedores alternativos de herrajes (14 y 28 de abril de 2026) — [Events](https://help.orgadata.com/en/news/events/)

**Schüco SchüCal (aluminio) y PolyCal (PVC)**
- SchüCal calcula sistemas de ventana, puerta, plegable, corredera, fachada y jardín de invierno, con oferta y pedido integrados, tiempos de producción y montaje, y «digital heart» de Schüco. Los datos pasan a SchüCad next, Fabrication Data Center, E.R.Plus | SE y Schüco Connect. El módulo MCO controla centros de mecanizado (CNC). Los nuevos sistemas llegan por service packs. Tiene más de 6.000 usuarios en el mundo — [Schüco UK – SchüCal](https://www.schueco.com/uk/fabricators/digital-solutions/schuecal)
- Funciones que aparecen en la serie de vídeos «Now»: salida con variantes (y aprobación de la variante elegida), bloqueo de proyectos y artículos, estados y marcas con filtros, optimización de ajustes, cálculo estático previo desde una fachada de catálogo, cálculo de U, nuevo modo MCO (entalladuras, procesamiento en serie) y archivado para acelerar SchüCal — [Schüco Digital Expert «Now»](https://www.schueco.com/se/tillverkare/min-arbetsplats/digital-expert/now)
- PolyCal (PVC-U): entrada de elementos, cálculo, optimización de corte, «position check» contra las directrices de fabricación de Schüco, datos maestros (colores, herrajes), sección, estática, control de máquina y barandillas antiacaída. Precio bajo petición — [Schüco PolyCal](https://schueco.com/de-en/fabricators/digital-solutions/polycal)

**Hydro/WICONA WICTOP (Technal también es de Hydro)**
- WICTOP: software de diseño 3D para carpintería metálica. Cubre criterios técnicos de pedido, cálculo de precios, preparación del trabajo y control de fabricación. Calcula los valores U con un método validado por ift Rosenheim. Se instala en local, en red o «como solución cloud». Versión citada: 8.1 — [Búsqueda: wicona.com/wictop](https://wicona.com/wictop) (las páginas wicona.com/en/wictop y /en/uk/... devolvieron 404 al consultarlas; datos tomados del resumen del buscador)
- No encontré ninguna herramienta propia de Technal que se pueda verificar — ver Gaps.

**Reynaers**
- ReynaPro: plataforma de diseño y configuración para configurar, detallar y presupuestar toda la gama Reynaers. Incluye dibujos técnicos, ofertas, listas de corte, enlace a EOS y módulo CNC — [Glass Times – Future proofing aluminium](https://glasstimes.co.uk/featured-articles/future-proofing-aluminium/)
- ReynaPro es un paquete de cálculo y producción comprado y adaptado. Problemas que describe el caso: los cambios del cliente final obligaban a volver al fabricante; las opciones y condiciones de cada instalador se mantenían a mano; la versión «ReynaPro Installer» era demasiado compleja para comerciales y solo funcionaba desde un PC enlazado. ReynaQuote (sobre Hive CPQ) funciona en tablet y móvil; el fabricante decide qué sistemas y opciones se ofrecen; el instalador añade instalación y remates; una corredera compleja se configura en unos 20 s; casi no requiere formación. Reynaers tiene unas 70 líneas de producto y más de 4.000 partners — [Hive CPQ – Reynaers](https://hivecpq.com/en/customer-cases/reynaers)
- Docu Portal (equivalente a 20.000 páginas de catálogo) y Hardware Configurator (julio 2025); Access Control Configurator (enero 2026) en el portal del cliente — [Specification Online, 17-07-2025](https://mail.specificationonline.co.uk/articles/2025-07-17/reynaers-launches-new-digital-document-portal-and-hardware-configurator); [Specification Online – Access control](https://mail.specificationonline.co.uk/articles/reynaers-eases-specification-of-access-controls-with-its-configurator-tool)

**Cortizo (muy relevante para el mundo hispanohablante)**
- 2010: Cortizo Software, desarrollado con Preference. Módulos: despieces y presupuestación, optimización, stock, compras, facturación y albaranes, conexión a máquinas de corte y mecanizado, secciones con exportación a AutoCAD, etiquetas CE y un módulo de fachada ligera (despiece a partir de alto, ancho y modulación) — [Interempresas, 04-03-2010](https://www.interempresas.net/Construccion/38201-Cortizo-lanza-un-software-de-gestion-integral-de-carpinteria.html)
- 2024: Cortizo Software «se basa en PrefSuite» (Preference) y PrefCAM incorpora las reglas de mecanizado de Cortizo. Al aceptar un pedido genera automáticamente lotes, archivos y listados y los envía a tronzadoras y centros de mecanizado (objetivo «taller sin papel»). Otros componentes: PrefCIM (trazabilidad en tiempo real) y «Cortizo Cloud», una plataforma web con actualizaciones mensuales, 3D, secciones, detalles de esquina y realidad virtual. Herramientas de Preference: PrefWeb (configurador online), PrefBIM y PrefVR — [Interempresas, 19-02-2024](https://www.interempresas.net/Construccion/541085-Cortizo-Preference-colaboran-jornada-optimizacion-produccion-conexion-maquinaria.html)
- Cortizo Lab y Cortizo Center: cálculos técnicos (transmitancia, acústica, AEV, cargas de viento y nieve, elementos finitos) — [resumen del buscador; cortizo.com](https://www.cortizo.com/ficheros/paginasinline/MTc0NDAxOTkyOF85Ml9pbnNfc2VydmljaW9fdGVjbmljb19lbg,,/) (no verificado en detalle)

**Rehau, Aluprof y otros**
- REHAU CONNECT+ es la plataforma central para fabricantes, distribuidores y arquitectos, desde la consulta hasta el servicio (Fensterbau Frontale 2026). Anuncios: integración GAEB asistida por IA para licitaciones y «Rack.ID» para gestionar racks; configurador 3D para particulares (2024) — [Interempresas – Rehau Window Solutions](https://www.interempresas.net/Quimica/623482-Rehau-Window-Solutions-apuesta-por-soluciones-integrales-y-digitales.html?R=625518); [Interempresas – configurador 3D](https://www.interempresas.net/Piscinas/536948-Rehau-ofrece-a-sus-clientes-un-configurador-de-ventanas-3D-para-particulares.html)
- Aluprof: configurador B2B online gratuito para socios comerciales, limitado a fachadas SkyFlow y pérgolas MB-OPENSKY 140. Permite registrar clientes, modificar ofertas antes del pedido y trabajar desde el móvil — [Aluprof newsletter B2B (PDF)](https://aluprof.com/files/documents/newsletter_konfigurator_B2B_DE.pdf)
- Klaes (software independiente que también es de Forterro): ERP para ventanas. En 2016 tenía 220 empleados, 26 idiomas, más de 7.000 clientes y unas 35.000 licencias en más de 50 países — [Interempresas – Klaes](https://www.interempresas.net/Construccion/627590-Klaes-software-robusto-y-en-continua-evolucion-para-los-fabricantes-de-ventanas.html); [Forterro – Klaes](https://www.forterro.com/en/windows-and-doors/klaes)

### Inferences
- Patrón de mercado: las casas de sistemas pequeñas y medianas no desarrollan su software. Externalizan el motor (Logikal, Preference/PrefSuite, un paquete comprado en el caso de Reynaers) y como mucho añaden una capa comercial (Hive CPQ, PrefWeb) o portales documentales. Schüco y Hydro/WICONA son las únicas con motor propio de peso.
- Forterro concentra ahora Logikal, Klaes y BM Group. Es un consolidador con mucha cuota en Europa. Para LatAm esto apunta a un servicio local escaso, con riesgo de precios de grupo (inferencia, sin datos de precio).
- Modelo de datos implícito en Logikal: Proveedor/catálogo → Sistema → (perfiles, herrajes en «paquetes», juntas/accesorios, vidrio como artículo o configurador externo) → Proyecto → Fase → Posición (elemento, material, texto, herraje, alternativa) → Elemento con rejilla (campos, montantes, travesaños) → inserciones (hojas con tipo/función) → herrajes y vidrio → artículos adicionales y variables de proyecto. DEKOPEN puede usar esta jerarquía como referencia.
- La optimización de barras (1D) no aparece documentada en el índice público de Logikal: solo la 2D de chapa. Lo más probable es que viva dentro de los pedidos y los impresos (inferencia; ver Gaps).

### Gaps
- Manual completo de las listas de corte (descuentos y ángulos) y de la optimización 1D de barras en Logikal: no localizado en la ayuda pública.
- Detalle de la estática en Logikal: la página de ayuda está vacía («being worked on»).
- Herramienta propia de Technal: no encontré ninguna verificable (en Francia, las ofertas de empleo citan Logikal, Chacal, Easywin, Onaya, Prodevis).
- Software de fabricante de Kömmerling/profine y de Deceuninck: no encontré fuentes en esta búsqueda.
- Si Aluprof publica sus datos en Logikal: no confirmado.
- No verifiqué qué paquete compró Reynaers como base de ReynaPro (el caso de Hive no lo nombra).

---

## 2. Diseño de interfaz (pantallas, menús, ribbons, paneles, editor, 2D/3D, documentos) y material de formación

### Takeaway
Logikal es una aplicación Windows clásica tipo Office: barra de herramientas de acceso rápido, ribbon con pestañas, barra de direcciones jerárquica, lista de proyectos con panel de información a la derecha, área de posiciones en vista de mosaicos o lista, y un editor de elementos con pestaña «Edit» y diálogos numéricos (montante «a X mm desde la izquierda»). La ayuda y los vídeos oficiales existen, pero no encontré manuales en Scribd/Yumpu ni vídeos con marcas de tiempo verificables.

### Cited Findings
- Pantalla de inicio de Logikal: barra de navegación a la izquierda (ajustes, bases de datos, servicio), barra de título con el proyecto activo, área de usuario con botón «?» (ayuda online), acceso rápido a programas arriba, proyectos recientes en el centro con favoritos, newsfeed (cambios de software, artículos, vídeos) y próximos eventos (formaciones, webinars, ferias) — [Home screen](https://help.orgadata.com/en/documentation/home-screen/)
- Project centre (11 zonas): (1) barra de acceso rápido (nuevo, guardar, buscar, deshacer, rehacer); (2) búsqueda con ámbito «carpeta actual / todas»; (3) pestaña «General» para volver a inicio; (4) **ribbon** con todas las funciones, plegable; (5) **barra de direcciones** con navegación atrás/adelante/arriba por niveles; (6) pestañas laterales «Projects» y «Fabrication Phases»; (7) lista de proyectos con arrastrar y soltar; (8) panel de información del proyecto a la derecha; (9) área de posiciones con vista **Tiles/List**; (10) menú contextual; (11) barra de estado con el directorio del proyecto — [User interface project centre](https://help.orgadata.com/en/documentation/project-centre/user-interface-project-centre/)
- El Project centre tiene página propia de atajos de teclado — [Project centre](https://help.orgadata.com/en/documentation/project-centre/)
- Editor de elementos: la rejilla se edita desde la pestaña **Edit** (Mullions, Transoms, Mullion/Transom in partial field) con selección del campo en el «position drawing» y diálogo numérico — [Mullions and transoms](https://help.orgadata.com/en/documentation/input-of-elements/windows-and-doors/grid/mullions-and-transoms/)
- Logikal 14: controles de vista 2D/3D (interior, exterior, lateral, superior, inferior) y ajustes de sección en pestañas — [Newsletter 14](https://help.orgadata.com/en/news/newsletter/newsletter-14/)
- Hay un Demo Tour en el navegador, sin instalación — [FAQ](https://www.logikal-software.com/en/faq). Hay prueba gratuita y demo tras rellenar un formulario — [Logikal front](https://www.logikal-software.com/en/logikal-front)
- Ayuda en alemán, inglés (Reino Unido y EE. UU.), español, francés, italiano, neerlandés, polaco, turco, checo y griego. El acceso se hace con login en downloads.orgadata.myforterro.com — [help.orgadata.com](https://help.orgadata.com/en/). La FAQ cita 11 idiomas de interfaz y todas las monedas — [FAQ](https://www.logikal-software.com/en/faq)
- Formación de Logikal en EE. UU.: curso básico online en 5 partes (Parte 1: crear dos marcos de storefront, informe de estimación y de pedido; Parte 2: borrar perfiles de marcos y crear «knee walls») — [resumen del buscador: Orgadata US trainings](https://orgadata.com/us/en/support/trainings.html) (redirige a logikal-software.com; no lo verifiqué al completo)
- Serie de vídeos SchüCal «Now» (#01–#13) con los temas listados en la sección 1. Schüco remite a su canal de YouTube para los tutoriales; los changelogs están en «My Workplace» — [Schüco «Now»](https://www.schueco.com/se/tillverkare/min-arbetsplats/digital-expert/now); [Schüco UK – SchüCal](https://www.schueco.com/uk/fabricators/digital-solutions/schuecal)
- SchüCad next se compara en directo con AutoCAD al dibujar una conexión a muro (Now #10) — [Schüco «Now»](https://www.schueco.com/se/tillverkare/min-arbetsplats/digital-expert/now)

### Inferences
- El editor de Logikal es «de formulario más dibujo»: el dibujo sirve para seleccionar y la geometría se introduce con números en diálogos, no por manipulación directa (arrastrar montantes). Es una oportunidad clara para un editor web con manipulación directa, cotas editables in situ y vista previa en vivo.
- La navegación en cinco niveles (Inicio → Project centre → Proyecto → Posición → Input of elements), con ribbon y barra de direcciones, delata una aplicación densa pensada para técnicos de oficina técnica, no para vendedores. El caso Reynaers lo confirma: tuvieron que construir una capa CPQ aparte para comerciales.

### Gaps
- No encontré manuales «LogiKal manual» ni «SchüCal manual» en Scribd/Yumpu/Issuu (la búsqueda solo devolvió resultados no relacionados).
- No pude verificar títulos ni marcas de tiempo concretas de vídeos de YouTube (Orgadata/Schüco). El buscador no indexa bien los vídeos.
- Sin capturas descritas de los impresos (oferta PDF, listas de corte, etiquetas) de Logikal ni de SchüCal; existe la sección «Printouts» de la ayuda, pero no la consulté en detalle.

---

## 3. Licencias, precio, plataforma y movimientos recientes (cloud, IA, BIM/IFC, paramétrico)

### Takeaway
Logikal y SchüCal siguen siendo **escritorio Windows**, con licencias por módulos, catálogos por suscripción y dongle (Logikal). No publican precios. Los movimientos de 2026 son la marca Forterro, la promesa de «invertir en cloud» sin producto cloud anunciado, el piloto de IA MyForterro.ai en DACH desde diciembre de 2026, el BIM con ida y vuelta Revit/IFC, la huella de carbono y el informe de ciberseguridad A+. SchüCal tiene tres niveles (basic/advanced/enterprise) y solo 64 bits desde 2023 R2.

### Cited Findings
- Logikal 14.0.2.204 (16-10-2026) sigue publicándose como versión de escritorio. En la 12.6.1.1201 (15-01-2026), copiar e importar proyectos «within networks» es más rápido — [Logikal Changelog](https://help.orgadata.com/en/news/changelog/logikal-changelog/)
- Gestión de licencias con dongle monopuesto y dongle de servidor; requisitos de sistema para cliente, servidor, red/internet y «entornos no soportados» — [System requirements](https://help.orgadata.com/en/docs/system-requirements/); [help.orgadata.com](https://help.orgadata.com/en/)
- Precio: la FAQ no publica precios de software, módulos ni catálogos — [FAQ](https://www.logikal-software.com/en/faq)
- Cloud: Forterro dice que la integración permite «accelerate investments in cloud technologies», sin detalles ni fecha — [Forterro news](https://www.logikal-software.com/en/news/orgadata-to-operate-under-forterro-name)
- IA: MyForterro.ai conecta modelos de IA con los datos operativos del software Forterro (optimización de producción, automatización, acceso al conocimiento, apoyo a decisiones). Para Logikal hay «a pilot phase… in the DACH… region in December» (diciembre de 2026, según la cabecera); no hay funciones concretas ni precio — [MyForterro.ai for Logikal users](https://www.logikal-software.com/en/news/myforterro-ai-for-logikal-users)
- BIM: Logikal importa huecos y cantidades del modelo Revit, diseña y presupuesta, y devuelve datos de componente (color, U, secciones) como «3D model» y «digital twin». Se menciona IFC solo como título de enlace — [BIM with Logikal](https://www.logikal-software.com/en/solutions/bim-with-logikal)
- Logikal 14: auditoría independiente y pentest con calificación «A+»; PCF según EN 15804 — [Newsletter 14](https://help.orgadata.com/en/news/newsletter/newsletter-14/)
- SchüCal: licencias basic, advanced y enterprise, con precio bajo oferta vía My Workplace. 64 bits desde 2017; la versión de 32 bits se abandona a partir de 2023 R2 (verano de 2023). La página no menciona ningún plan cloud — [Schüco UK – SchüCal](https://www.schueco.com/uk/fabricators/digital-solutions/schuecal)
- WICTOP se ofrece en local, en red o como «cloud solution» (v8.1) — [resumen del buscador: wicona.com](https://wicona.com/wictop)
- Cortizo Cloud: plataforma web con actualizaciones mensuales (2024) — [Interempresas, 2024](https://www.interempresas.net/Construccion/541085-Cortizo-Preference-colaboran-jornada-optimizacion-produccion-conexion-maquinaria.html)
- REHAU: integración GAEB asistida por IA anunciada para Frontale 2026 — [Interempresas – Rehau](https://www.interempresas.net/Quimica/623482-Rehau-Window-Solutions-apuesta-por-soluciones-integrales-y-digitales.html?R=625518)
- Referencia de precio en otro segmento: Onaya (presupuestos online para carpintería en Francia) desde 2.500 € sin IVA — [resumen del buscador: Batiproduits](https://www.batiproduits.com/fiche/produits/solution-en-ligne-pour-edition-de-devis-destinee-p69087133.html)

### Inferences
- A octubre de 2026 no existe un «Logikal web» ni un «SchüCal cloud» públicos. La ventana para un SaaS web nativo sigue abierta, sobre todo en LatAm.
- El modelo de dongle + catálogo por suscripción + módulos crea fricción de alta y coste recurrente doble (software y datos). Un SaaS con catálogo incluido y precio por puesto sería un diferenciador (inferencia, sin precios verificados).
- La IA de los incumbentes está en fase de piloto genérico de grupo, no integrada en el editor ni en la oferta.

### Gaps
- No hay precios públicos de Logikal, SchüCal, PolyCal, WICTOP ni Cortizo Software. No los invento.
- No pude consultar los requisitos exactos de sistema (sistema operativo, base de datos, terminal server) en las subpáginas.
- No hay anuncio de IFC nativo detallado ni de motor paramétrico abierto en Logikal.

---

## 4. Fortalezas, debilidades y quejas de usuarios

### Takeaway
La fortaleza principal es el dato: más de 450 catálogos mantenidos, validación técnica de compatibilidades y la cadena completa hasta CNC, MES, CE y normativa (Uw, estática, cortafuego, PCF). Las debilidades visibles son la complejidad (no apto para comerciales), el escritorio atado a un PC, la pila de módulos y un changelog lleno de regresiones. No hay reseñas independientes públicas de Logikal ni de SchüCal.

### Cited Findings
- Fortaleza: el «logic check» impide presupuestar o fabricar elementos técnicamente inviables — [Design & Calculation](https://www.logikal-software.com/en/solutions/design-calculation)
- Fortaleza: catálogos mantenidos por el proveedor del software (más de 7 millones de artículos) — [FAQ](https://www.logikal-software.com/en/faq)
- Testimonios del fabricante: Metallbau Windeck («work faster and more flexibly») y ASGE Rümenapp (32 personas) — [Logikal front](https://www.logikal-software.com/en/logikal-front)
- Debilidad documentada (caso Reynaers con un paquete de escritorio): demasiado complejo para comerciales y personal con poco conocimiento técnico; solo funcionaba desde un PC enlazado («many people had to visit the office»); mantenimiento manual de las condiciones de cada instalador; reprocesos de la oferta por parte del instalador — [Hive CPQ – Reynaers](https://hivecpq.com/en/customer-cases/reynaers)
- Señal de calidad: muchas entradas del changelog 2025-2026 son correcciones de funciones que dejaron de funcionar (impresos, selección de herrajes en la entrada de elementos, vidrio de proyecto, estática italiana, CSV para el ERP) — [Logikal Changelog](https://help.orgadata.com/en/news/changelog/logikal-changelog/)
- Señal de rendimiento: Schüco dedica un vídeo a «make SchüCal faster through archiving» — [Schüco «Now» #01](https://www.schueco.com/se/tillverkare/min-arbetsplats/digital-expert/now)
- La ficha de Logikal en Capterra NZ no tiene valoraciones de usuarios — [Capterra NZ](https://www.capterra.co.nz/software/1077696/Logikal)

### Inferences
- Pain points que se deducen: (a) curva de aprendizaje y dependencia de formación; (b) trabajo atado a la oficina; (c) regresiones entre versiones; (d) rendimiento que se degrada con proyectos acumulados; (e) coste de módulos y catálogos; (f) lo comercial (oferta para cliente final, dealers) mal resuelto, lo que lleva a las casas a añadir CPQ aparte.
- El sesgo de catálogo de marca (SchüCal solo Schüco, WICTOP solo WICONA, Cortizo Software solo Cortizo) obliga a fabricantes multimarca a tener varios programas. Logikal resuelve eso en Europa, pero en LatAm los perfiles locales probablemente no están en sus 450 catálogos (inferencia, sin verificar).

### Gaps
- No encontré quejas en Reddit, foros alemanes (Metallbau), G2/Capterra con reseñas ni grupos de LinkedIn. Tampoco reseñas de SchüCal.
- No hay datos de NPS, churn ni tiempo medio de implantación.

---

## 5. Qué hay que igualar sí o sí y dónde un SaaS web con IA puede ser claramente mejor

### Takeaway
Lo mínimo para competir: catálogo sistema → perfiles, herrajes y vidrio con reglas de compatibilidad, editor de rejilla con hojas y tipos de apertura, despiece y lista de corte exactos, precio con recargos, colores y mano de obra, oferta PDF, pedidos, optimización, etiquetas/QR y exportación a sierra/CNC, más Uw y estática básicos. Las brechas que se pueden atacar: web y móvil, edición directa, capa comercial para vendedores y clientes, catálogos LatAm, onboarding sin formación, IA integrada en el flujo y precios transparentes.

### Cited Findings (base para la lista de paridad)
- Paridad funcional observada en Logikal: posiciones alternativas y variantes; posiciones de material, texto y herraje; plantillas y biblioteca de posiciones; fases de fabricación; restos y longitudes de barra; variables de proyecto; historial de posición — [Project centre](https://help.orgadata.com/en/documentation/project-centre/)
- Rejilla con inclinaciones, arcos, acoplamientos, persianas y FFL; herrajes en paquetes con cilindro y bisagras; vidrio con barrotillos — [Input of elements](https://help.orgadata.com/en/documentation/input-of-elements/)
- Formatos de máquina (Rotox, Mecal XML), interfaces ERP (Qomet), DoP y CE — [Logikal Changelog](https://help.orgadata.com/en/news/changelog/logikal-changelog/); MES con FPC y CE — [Logikal front](https://www.logikal-software.com/en/logikal-front)
- Uw según EN ISO 10077-1, PCF según EN 15804, informes cortafuego — [Newsletter 14](https://help.orgadata.com/en/news/newsletter/newsletter-14/)
- Variantes en la oferta con aprobación de la variante elegida (SchüCal) — [Schüco «Now» #13](https://www.schueco.com/se/tillverkare/min-arbetsplats/digital-expert/now)
- Lo que el mercado ha tenido que añadir aparte: CPQ móvil para dealers e instaladores, en el que el fabricante controla qué se ofrece (ReynaQuote/Hive) — [Hive CPQ – Reynaers](https://hivecpq.com/en/customer-cases/reynaers); configurador web (PrefWeb) y Cortizo Cloud — [Interempresas, 2024](https://www.interempresas.net/Construccion/541085-Cortizo-Preference-colaboran-jornada-optimizacion-produccion-conexion-maquinaria.html)

### Inferences (oportunidades para DEKOPEN)
1. **Web nativa y multiusuario**, sin dongle ni instalación: los incumbentes siguen en escritorio Windows (Logikal 14, SchüCal 64 bits). Solo WICTOP y Cortizo mencionan «cloud».
2. **Editor con manipulación directa** (arrastrar montantes, dividir campos en partes iguales, cotas editables en el lienzo) frente al patrón ribbon + diálogo numérico de Logikal.
3. **Dos caras del mismo motor**: modo técnico (oficina técnica) y modo vendedor o cliente (CPQ simple en móvil), con el fabricante controlando qué sistemas y opciones expone. Es justo el problema que Reynaers resolvió con un parche (Hive) sobre un software comprado.
4. **Catálogos LatAm** (perfiles y herrajes locales, PVC y aluminio chilenos) cargables por el propio fabricante, con versionado de precios inmutable. Los incumbentes dependen del mantenimiento del proveedor del software.
5. **IA aplicada al flujo, no como chat genérico**: leer planos y licitaciones (REHAU ya apunta a GAEB con IA), proponer posiciones desde fotos o PDF, revisar ofertas y explicar cambios de precio, siempre con números salidos del motor determinista. MyForterro.ai sigue en piloto genérico (DACH, diciembre de 2026).
6. **Fiabilidad visible**: los changelogs llenos de regresiones sugieren valorar los goldens o tests de regresión de cálculo como argumento comercial («0,00 mm de tolerancia, cada versión verificada»).
7. **Precio transparente y onboarding sin formación**: ningún incumbente publica precios, y Logikal y SchüCal se apoyan en cursos de varias partes.
8. **Paridad necesaria a medio plazo**: exportación a sierras y CNC habituales en LatAm, etiquetas o QR por elemento (tipo SimplyTag), Uw según EN ISO 10077-1 o la norma chilena equivalente, estática de predimensionado y BIM/IFC básico para licitaciones grandes.

### Gaps
- Sin datos de cuota de mercado de Logikal o SchüCal en Chile o LatAm. No verifiqué si Cortizo Software/PrefSuite está presente en Chile.
- Sin información verificada sobre los formatos de máquina más usados por fabricantes chilenos.
