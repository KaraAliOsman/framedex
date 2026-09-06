# DEKOPEN — BASELINE DE SUPERFICIES Y FLUJOS DE USUARIO (CAPABILITY MAP S01–S28) (v1.3 MASTER)

> **Estado:** Documento Normativo Activo — Flexible & Componible  
> **Propósito:** Mapeo de Capacidades, Roles, Contratos y Viajes de Usuario (User Journeys)  
> **Filosofía UX:** Ergonomía Adaptable de Taller, Eficiencia de Clics y Componibilidad Modular  

---

## 1. Principios de Componibilidad y Flexibilidad de Interfaces

1. **Referencias de Capacidad, No Prisión de Pantallas Físicas:**
   Los identificadores `S01` a `S28` representan **capacidades funcionales y superficies del flujo de trabajo**, conservados para trazabilidad histórica, planes de shot y auditoría. **NO constituyen una restricción de tener exactamente 28 pantallas web aisladas**.
2. **Libertad de Composición para Agentes y Diseñadores:**
   Los constructores e inteligencias artificiales avanzadas están facultados para agrupar, desacoplar o componer estas capacidades según lo dicte la ergonomía real del taller de carpintería:
   - Capacidades complementarias pueden coexistir en un **Espacio de Trabajo Unificado (Dockable Workspace)**, como el Lienzo 2D (`S06`), el Inspector Técnico (`S07`) y la Consola de Comandos (`S21`).
   - Una capacidad puede implementarse como **pantalla completa, modal contextual, drawer lateral flotante, pestaña o panel acoplable**, siempre que garantice usabilidad, accesibilidad y velocidad.
   - Una superficie puede dividirse en pasos progresivos o simplificarse en una vista única si los datos demuestran mejor flujo operativo.
3. **Contratos de Enlace (Deep-Links):**
   Las rutas URL solo son obligatorias e inmutables cuando responden a un **contrato externo, seguridad o enlace compartible** (ej: `/login`, portales de clientes `/p/quote/:uuid`, visor de solo lectura `/view/:token`, o redirecciones de pasarelas de pago `/settings/billing`). Las rutas internas son adaptables según la arquitectura de navegación.

---

## 2. Matriz Maestra de Capacidades y Superficies (S01 a S28)

| ID | Capacidad / Superficie | Objetivo Primario | Usuario / Rol | Deep-Link / Contrato | Formato de Implementación Sugerido |
|---|---|---|---|---|---|
| **S01** | **Autenticación y Magic Link** | Acceso seguro sin contraseñas frágiles | Todos / Público | `/login` (Obligatorio) | Pantalla limpia, centrada, con soporte OTP/Magic Link |
| **S02** | **Onboarding de Taller** | Configuración de empresa, RUT y moneda | OWNER | `/onboarding` (Obligatorio) | Wizard guiado paso a paso con validación legal |
| **S03** | **Dashboard Operativo & KPIs** | Visibilidad de margen, producción y alertas | OWNER, ESTIMATOR, MGR | `/dashboard` (Recomendado) | Tablero modular con widgets reordenables |
| **S04** | **Listado de Proyectos** | Búsqueda rápida, filtros y estados de cotización | OWNER, ESTIMATOR, MGR | `/projects` (Recomendado) | Tabla densa con atajos de teclado y vista en tarjetas |
| **S05** | **Detalle de Proyecto & Vanos** | Gestión de vanos, estado global y emisión | OWNER, ESTIMATOR, MGR | `/projects/:id` (Obligatorio) | Vista maestra con grilla de vanos y métricas sumarias |
| **S06** | **Lienzo CAD 2D Paramétrico** | Dibujo y acotación milimétrica en tiempo real | OWNER, ESTIMATOR | `/projects/:id/positions/:posId/edit` | Workspace CAD con viewport SVG interactivo pan/zoom |
| **S07** | **Inspector Técnico R01–R14** | Detección de fallas físicas y corrección 1-clic| OWNER, ESTIMATOR | Contextual a S06 (No deep-link)| Panel dockable lateral o modal emergente en S06 |
| **S08** | **Explosión BOM de Materiales** | Desglose milimétrico de perfiles, herrajes y vidrio| OWNER, ESTIMATOR, MGR | `/projects/:id/bom` | Tabla técnica exportable con agrupación por SKU |
| **S09** | **Listas de Costo y Precios** | Configuración de márgenes, mano de obra y costos| OWNER | `/pricing/cost-lists` | Grilla editable tipo hoja de cálculo con auditoría previa |
| **S10** | **Previsualización & Emisión PDF**| Congelación legal de presupuestos DOC-01 | OWNER, ESTIMATOR | `/projects/:id/quote-preview` | Visor split-screen PDF con botón de firma y emisión |
| **S11** | **Orden de Trabajo (OT)** | Instrucciones de fabricación para planta | OWNER, WORKSHOP_MANAGER | `/orders/ot/:id` | Hoja de producción con QR de vano y plano acotado |
| **S12** | **Visor 3D y Cinemática** | Visualización interactiva y simulación física | Todos / Cliente | `/viewer-3d/:posId` o integrado | Canvas R3F orbital 360° con selector de apertura y color |
| **S13** | **Catálogo de Sistemas de Perfil**| Parámetros de series, nudos e inercias | OWNER, WORKSHOP_MANAGER | `/catalogs/systems` | Vista de catálogo con explorador de perfiles y nudos |
| **S14** | **Compilador de Catálogos IA** | Ingesta asistida de catálogos en PDF/Excel | OWNER | `/catalogs/compiler` | Split-screen: PDF de fabricante vs Formulario de mapeo |
| **S15** | **Matriz Junquillo–Vidrio** | Asignación inequívoca junquillo según vidrio | OWNER, WORKSHOP_MANAGER | `/catalogs/systems/:id/glazing` | Matriz interactiva de compatibilidad dimensional |
| **S16** | **Inventario de Retazos QR** | Registro de sobrantes para reutilización | WORKSHOP_MANAGER | `/inventory/offcuts` | Vista adaptada a móvil/tablet con lector de cámara QR |
| **S17** | **Certificado de Fabricabilidad**| Sello de garantía técnica y doble ciego T8 | OWNER, ESTIMATOR | `/quality/certificates/:id` | Panel de trazabilidad con firmas hash SHA-256 |
| **S18** | **Bandeja Omnicanal (Email/WA)** | Recepción automática de pedidos y solicitudes | OWNER, ESTIMATOR | `/inbox` | Inbox conversacional con previsualizador de adjuntos |
| **S19** | **Optimizador de Corte 1D BFD** | Plan de corte de barras y minimización de merma| WORKSHOP_MANAGER | `/orders/ot/:id/cutting-plan` | Diagrama visual de barras de 6m con secuencia de corte |
| **S20** | **Billetera de Créditos IA** | Saldo, recargas y consumo de herramientas | OWNER | `/settings/wallet` | Widget de saldo con historial de transacciones y recarga |
| **S21** | **Consola Comandos & Diff (Cmd+K)**| Modificación ágil por lenguaje natural/comandos | OWNER, ESTIMATOR | Overlay en S06 (Sin ruta URL) | Barra de comandos tipo Spotlight o Drawer contextual |
| **S22** | **Editor de Plantillas PDF** | Personalización de logos, tipografía y colores | OWNER | `/settings/templates` | Editor visual con vista previa en tiempo real |
| **S23** | **Gestión de Equipo de Taller** | Asignación de roles y permisos a operarios | OWNER | `/settings/team` | Gestión de usuarios con switch de roles (RBAC) |
| **S24** | **Suscripción y Facturación** | Gestión de planes Starter/Pro/Business/B2x | OWNER | `/settings/billing` (Obligatorio)| Portal con estado de plan, facturas y checkout seguro |
| **S25** | **Configuración General & RLS** | Parámetros del taller, mermas y auditoría | OWNER | `/settings/general` | Formulario de preferencias globales y seguridad |
| **S26** | **Portal Cliente / Instalador** | Aprobación de presupuesto y ficha de montaje | Cliente Final / INSTALLER | `/p/quote/:uuid` (Obligatorio)| Interfaz ligera responsive optimizada para smartphones |
| **S27** | **Intérprete Multimodal OCR** | Extracción de vanos desde planos y apuntes | OWNER, ESTIMATOR | `/ai/extract-positions` | Split-screen: imagen de plano/apunte vs tabla editable |
| **S28** | **Moderación Catálogo Global** | Validación de sistemas de perfil comunitarios | SUPERADMIN | `/admin/queue` (Obligatorio) | Cola de revisión administrativa con diff de catálogo |

---

## 3. Especificación Detallada por Capacidad

### S01 · Autenticación y Acceso Seguro
- **Objetivo:** Permitir el ingreso instantáneo sin contraseñas vulnerables mediante Magic Links y Google OAuth.
- **Roles:** Acceso público.
- **Seguridad:** Supabase Auth con emisión de JWT que encapsula `org_id` y rol de usuario. Cero contraseñas en texto plano.
- **Contrato URL:** `/login`.

### S02 · Onboarding y Configuración de Organización
- **Objetivo:** Recolectar datos fiscales de la carpintería (RUT/RUC/Tax ID), moneda predeterminada (CLP/USD), nombre comercial y logotipo.
- **Roles:** OWNER únicamente.
- **Contrato URL:** `/onboarding`. Al completar, transiciona a `S03`.

### S03 · Dashboard Operativo y Centro de Control de Taller
- **Objetivo:** Mostrar indicadores clave de desempeño (KPIs): volumen cotizado en el mes, margen promedio ponderado, vanos en cola de fabricación y alertas de stock de barras.
- **Roles:** OWNER, ESTIMATOR, WORKSHOP_MANAGER.
- **Composición:** Tarjetas analíticas interactivas con acceso rápido a proyectos recientes y atajo `Cmd+K` para crear cotizaciones.

### S04 · Listado y Gestión de Proyectos
- **Objetivo:** Búsqueda instantánea, filtrado por estado (Borrador, Cotizado, Aprobado, En Fabricación, Terminado) y gestión masiva de cotizaciones.
- **Roles:** OWNER, ESTIMATOR, WORKSHOP_MANAGER.
- **Contrato URL:** `/projects`.

### S05 · Detalle de Proyecto y Grilla de Vanos
- **Objetivo:** Centro neurálgico del proyecto. Muestra la lista de vanos (posiciones), dimensiones nominales exterior marco, tipología, serie de perfiles, color y valor neto.
- **Roles:** OWNER, ESTIMATOR, WORKSHOP_MANAGER.
- **Contrato URL:** `/projects/:id`. Permite añadir vanos manualmente, clonar vanos existentes o importar lotes vía `S27`.

### S06 · Editor 2D / Canvas SVG Paramétrico
- **Objetivo:** Editor visual en tiempo real de la geometría de la abertura. El usuario altera anchos, alturas y travesaños, recalculando el árbol paramétrico en `/engine` a tolerancia `0.00 mm`.
- **Roles:** OWNER, ESTIMATOR.
- **Contrato URL:** `/projects/:id/positions/:posId/edit`.
- **Integración de Superficie:** Coexiste idealmente en un mismo espacio de trabajo con `S07` (Inspector) y `S21` (Comandos).

### S07 · Inspector Técnico y Corrección en 1 Clic
- **Objetivo:** Ejecutar las 14 reglas canónicas de validación técnica (R01 a R14) verificando límites de peso por herraje, holgura de junquillo, relación de aspecto de hojas y compatibilidad de perfiles.
- **Roles:** OWNER, ESTIMATOR.
- **UX:** Muestra mensajes en lenguaje comprensible de taller con un botón de corrección automática en 1 clic (ej: *"La hoja excede 80 kg; cambiar a herraje pesado de 130 kg"*). No requiere ruta independiente; se recomienda implementarlo como panel lateral acoplable o modal contextual.

### S08 · Explosión BOM y Despiece Milimétrico
- **Objetivo:** Generar la lista exhaustiva de materiales requeridos para el proyecto: perfiles de PVC cortados con pérdida de fusión, refuerzos de acero galvanizado, vidrios termopanel, kits de herraje y metros de burlete.
- **Roles:** OWNER, ESTIMATOR, WORKSHOP_MANAGER.
- **Contrato URL:** `/projects/:id/bom`. Exportable a PDF y Excel.

### S09 · Gestión de Listas de Costo y Precios
- **Objetivo:** Administrar los costos de compra de materiales por proveedor, costo horario de operarios de taller e instalación, y definir las reglas de margen de venta.
- **Roles:** OWNER exclusivamente.
- **Seguridad:** Protegido por RLS estricto (`org_id`). Toda modificación dispara un registro previo e inmutable en `price_audit_logs` (Regla 21).

### S10 · Vista Previa y Congelación de Cotización PDF (DOC-01)
- **Objetivo:** Previsualizar el presupuesto comercial con desglose de ítems, términos comerciales, plazo de entrega y valor total. Al presionar *"Emitir Cotización"*, se congela una revisión inmutable en `project_versions` con hash SHA-256 (Regla 12).
- **Roles:** OWNER, ESTIMATOR.
- **Contrato URL:** `/projects/:id/quote-preview`.

### S11 · Orden de Trabajo de Taller (OT) (DOC-03)
- **Objetivo:** Instrucciones de manufactura para los maestros operarios. Detalla medidas exteriores de corte, orificios de desagüe, altura de manilla y códigos de herraje.
- **Roles:** OWNER, WORKSHOP_MANAGER.
- **Contrato URL:** `/orders/ot/:id`.

### S12 · Visor 3D y Simulación Cinemática
- **Objetivo:** Generar la representación volumétrica fotorrealista de la ventana con materiales PBR y simulación de apertura interactiva (giro, oscilo y corredera) para elevar la tasa de cierre comercial.
- **Roles:** Acceso universal (público si se accede vía enlace de proyecto).
- **Contrato URL:** `/viewer-3d/:posId` o embebido en portal cliente.
- **Nota de Roadmap:** Capacidad formalmente planificada (`[PENDIENTE-DECISIÓN: ROADMAP-3D]`).

### S13 · Catálogo de Perfiles, Series y Kits de Herrajes
- **Objetivo:** Visualización y personalización de las series de perfiles de PVC disponibles para el taller (ej: Eurovent, Kömmerling, Rehau, Deceuninck, Aluplast).
- **Roles:** OWNER, WORKSHOP_MANAGER.
- **Contrato URL:** `/catalogs/systems`.

### S14 · Compilador de Catálogos Asistido por IA
- **Objetivo:** Acelerar el alta de nuevos catálogos de fabricantes mediante el análisis de PDFs técnicos y tablas de accesorios, extrayendo dimensiones de nudo y descuentos de perfiles.
- **Roles:** OWNER.
- **UX:** Pantalla partida que compara el documento técnico con las propiedades mapeadas en base de datos.

### S15 · Matriz Junquillo–Vidrio
- **Objetivo:** Configurar la tabla de correspondencia dimensional que determina qué junquillo corresponde a cada espesor total de vidrio (DVH o simple) para garantizar la presión de estanqueidad.
- **Roles:** OWNER, WORKSHOP_MANAGER.
- **Contrato URL:** `/catalogs/systems/:id/glazing`.

### S16 · Inventario y Registro de Retazos QR
- **Objetivo:** Registrar las barras cortadas sobrantes con longitud $\ge 600\text{ mm}$, etiquetándolas con código QR para que el optimizador BFD las reutilice en futuras órdenes de trabajo.
- **Roles:** WORKSHOP_MANAGER.
- **UX:** Optimizada para dispositivos móviles con escaneo de cámara integrado.

### S17 · Panel de Certificado de Fabricabilidad
- **Objetivo:** Mostrar la garantía de calidad del vano tras superar la verificación cruzada doble ciego T8, emitiendo el sello de trazabilidad matemática y certificado DOC-08 con código QR.
- **Roles:** OWNER, ESTIMATOR.
- **Contrato URL:** `/quality/certificates/:id`.

### S18 · Bandeja de Entrada Omnicanal (Email & WhatsApp)
- **Objetivo:** Centralizar solicitudes de cotización entrantes desde correos o mensajes de clientes, extrayendo automáticamente adjuntos para convertirlos en proyectos borradores.
- **Roles:** OWNER, ESTIMATOR.
- **Contrato URL:** `/inbox`.

### S19 · Optimizador y Mapa de Corte 1D / Pedido de Barras
- **Objetivo:** Ejecutar el algoritmo Best Fit Decreasing (BFD) para calcular el patrón de corte óptimo barra por barra, minimizando el desperdicio de PVC/aluminio y generando el pedido consolidado DOC-04/DOC-05.
- **Roles:** WORKSHOP_MANAGER.
- **Contrato URL:** `/orders/ot/:id/cutting-plan`.

### S20 · Billetera y Consumo de Créditos IA
- **Objetivo:** Consultar el saldo disponible de créditos de cómputo para herramientas de visión y optimización, historial de consumos auditados y botón de recarga inmediata.
- **Roles:** OWNER exclusivamente.
- **Contrato URL:** `/settings/wallet`. Inmunidad ante saldo cero (la plataforma base nunca se bloquea si se agotan los créditos).

### S21 · Consola de Comandos NLP y Diff Preview (Cmd+K)
- **Objetivo:** Permitir modificaciones ultrarrápidas mediante atajos de teclado y lenguaje natural (ej: *"cambiar todas las hojas a termopanel 4-12-4"*), mostrando siempre un diff visual antes de aplicar cambios y soportando deshacer sagrado (Undo/Cmd+Z).
- **Roles:** OWNER, ESTIMATOR.
- **Formato:** Overlay flotante contextual desplegable sobre cualquier pantalla de diseño.

### S22 · Personalizador de Plantillas de Documentos
- **Objetivo:** Ajustar el diseño visual de los presupuestos PDF (DOC-01), encabezados, firmas y bloques protegidos de disclaimer legal.
- **Roles:** OWNER.
- **Contrato URL:** `/settings/templates`.

### S23 · Gestión de Equipo de Taller y Permisos
- **Objetivo:** Invitar miembros del taller y asignar roles granulares (Owner, Estimator, Workshop Manager, Installer).
- **Roles:** OWNER.
- **Contrato URL:** `/settings/team`.

### S24 · Suscripción y Facturación (Planes Dekopen)
- **Objetivo:** Administrar la suscripción mensual/anual de la plataforma (Starter, Profesional, Business, Business 2x), descargar facturas y gestionar métodos de pago con pasarelas (Flow CLP / Paddle USD).
- **Roles:** OWNER exclusivamente.
- **Contrato URL:** `/settings/billing` (Contrato obligatorio de retorno de pago).

### S25 · Configuración General y Políticas de Taller
- **Objetivo:** Definir holguras de instalación por defecto, pérdida de soldadura por fusión ($3.00\text{ mm}$ estándar), margen de merma presupuestaria y visualización de auditoría.
- **Roles:** OWNER.
- **Contrato URL:** `/settings/general`.

### S26 · Portal Público de Aprobación / Vista de Instalador
- **Objetivo:** Interfaz pública read-only y responsive para smartphones donde el cliente final aprueba el presupuesto, o donde el instalador en obra revisa las medidas de fijación y nivelación.
- **Roles:** Cliente Final / INSTALLER.
- **Seguridad Inviolable:** El bundle de JS y la respuesta de API **JAMÁS contienen costos de compra, márgenes comerciales ni despiece interno del taller**.
- **Contrato URL:** `/p/quote/:uuid` o `/view/[token]` (Obligatorio e inmutable).

### S27 · Intérprete Multimodal de Planos y Croquis OCR
- **Objetivo:** Procesar planos arquitectónicos, tablas impresas o croquis manuscritos de obra para extraer automáticamente vanos y cargarlos como borrador revisable en menos de 5 minutos humanos.
- **Roles:** OWNER, ESTIMATOR.
- **UX:** Pantalla split-screen: izquierda imagen o plano original con marcadores interactivos; derecha grilla editable con celdas semaforizadas (Verde, Amarillo de validación, Rojo de ingreso manual).
- **Contrato URL:** `/ai/extract-positions`.

### S28 · Cola de Moderación de Catálogo Global
- **Objetivo:** Interfaz administrativa central para verificar y publicar sistemas de perfiles creados por la comunidad de talleres sin filtrar costos internos de ninguna organización.
- **Roles:** SUPERADMIN exclusivamente.
- **Contrato URL:** `/admin/queue`.
