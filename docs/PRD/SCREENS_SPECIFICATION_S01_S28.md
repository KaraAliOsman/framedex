# DEKOPEN — BASELINE DE SUPERFICIES Y FLUJOS DE USUARIO (CAPABILITY MAP S01–S28) (v1.3 MASTER)

> **Estado:** Documento Normativo Activo — Flexible & Componible a Nivel de Atributos
> **Propósito:** Mapeo Canónico de Capacidades, Roles, Contratos y Superficies de Interfaz
> **Filosofía UX:** Ergonomía Adaptable de Taller, Eficiencia Operativa y Componibilidad Modular

---

## 1. Principios Constitucionales de Componibilidad y Flexibilidad por Atributos

1. **Separación de Existencia de Capacidad vs Superficie Física:**
   No se confunde "la capacidad debe existir" con "debe ser para siempre una pantalla física independiente".
   Los identificadores `S01` a `S28` representan **capacidades de negocio, roles y contratos de flujo**. La forma física de renderizado (página dedicada, modal contextual, drawer lateral, dockable panel o split-screen) se define con flexibilidad ergonómica.

2. **Gobernanza a Nivel de Atributos (Attribute-Level Governance):**
   Ninguna capability se clasifica en bloque como rígida. Cada S-ID desglosa formalmente:
   - **Capability Requirement:** Existencia mandatoria de la función en el sistema.
   - **User Goal:** Propósito de valor que el usuario cumple en este paso.
   - **Role Contract:** Restricciones de acceso y permisos RBAC (`FIXED_BY_CONTRACT`).
   - **Route / Deep-Link Contract:** Necesidad de URL accesible externamente (`FIXED_BY_CONTRACT` para URLs contractuales como `/login`, `/view/:token`, `/admin/queue`; `CURRENT_BASELINE` para URLs internas; o `NONE_INTERNAL` para herramientas contextuales).
   - **Security Contract:** Aislamiento RLS, validación JWT, blindaje de datos privados.
   - **Required Information:** Datos mínimos requeridos para operar.
   - **Current Surface Baseline:** Formato visual de referencia implementado.
   - **Surface Flexibility:** Grado de libertad de layout, widgets y composición (generalmente `FLEXIBLE`).

3. **Precedencia Temporal del Shot Actual (Principio Inviolable):**
   > **`GLOBAL FLEXIBILITY DOES NOT RETROACTIVELY DESTABILIZE AN ACTIVE SHOT CONTRACT.`**
   Si una decisión de interfaz ya quedó formalmente congelada en un plan de shot activo mediante resolución aprobada (ejemplo: `S07` congelado temporalmente como Modal contextual en `docs/plans/PLAN_SHOT-07.md` bajo `PD-07-27 — S07`), dicha decisión **se mantiene inmutable durante la ejecución de ese shot**. La flexibilidad global habilita la evolución futura, jamás la desestabilización del shot en curso.

---

## 2. Matriz Maestra de Capacidades y Atributos (S01 a S28)

| ID | Capacidad | User Goal | Role Contract | Route / Deep-Link Contract | Security Contract | Current Surface Baseline | Surface Flexibility |
|---|---|---|---|---|---|---|:---:|
| **S01** | **Autenticación & Magic Link** | Acceso seguro sin contraseñas | Público / Todos (`FIXED_BY_CONTRACT`) | `/login` (`FIXED_BY_CONTRACT`) | Supabase Auth JWT con `org_id` | Pantalla de login limpia | Layout: `FLEXIBLE` • Composición: `FLEXIBLE` |
| **S02** | **Onboarding de Taller** | Registro inicial de taller y moneda | OWNER (`FIXED_BY_CONTRACT`) | `/onboarding` (`CURRENT_BASELINE`) | Creación atómica tenant + RLS | Wizard paso a paso | Layout: `FLEXIBLE` • Flujo: `FLEXIBLE` |
| **S03** | **Dashboard Operativo & KPIs** | Visibilidad de margen y volumen | OWNER, ESTIMATOR, MGR (`FIXED_BY_CONTRACT`) | `/dashboard` (`CURRENT_BASELINE`) | RLS tenant isolation | Tablero de tarjetas/gráficos | Layout: `FLEXIBLE` • Cantidad widgets: `FLEXIBLE` |
| **S04** | **Listado de Proyectos** | Búsqueda y gestión de cotizaciones | OWNER, ESTIMATOR, MGR (`FIXED_BY_CONTRACT`) | `/projects` (`CURRENT_BASELINE`) | RLS `current_user_org_ids()` | Grilla tabular con filtros | Layout: `FLEXIBLE` • Densidad: `FLEXIBLE` |
| **S05** | **Detalle Proyecto & Vanos** | Gestión de vanos, estados y emisión | OWNER, ESTIMATOR, MGR (`FIXED_BY_CONTRACT`) | `/projects/:id` (`FIXED_BY_CONTRACT`) | Transición de estados controlada | Maestro-detalle con cards | Layout: `FLEXIBLE` • Composición: `FLEXIBLE` |
| **S06** | **Lienzo CAD 2D Paramétrico** | Edición geométrica en tiempo real | OWNER, ESTIMATOR (`FIXED_BY_CONTRACT`) | `/projects/:id/positions/:posId/edit` (`CURRENT_BASELINE`) | Validación matemática `/engine` 0.00mm | Workspace CAD SVG viewport | Layout: `FLEXIBLE` • Paneles: `FLEXIBLE` |
| **S07** | **Inspector Técnico R01–R14** | Detección de fallas y fix 1-clic | OWNER, ESTIMATOR (`FIXED_BY_CONTRACT`) | Contextual a S06 (`NONE_INTERNAL`) | Reglas físicas R01–R14 puras | Modal contextual en S06 | Temporal SHOT-07: `MODAL` (PD-07-27) • Global: `FLEXIBLE` |
| **S08** | **Explosión BOM de Materiales** | Desglose milimétrico de perfiles | OWNER, ESTIMATOR, MGR (`FIXED_BY_CONTRACT`) | `/projects/:id/bom` (`CURRENT_BASELINE`) | BOM SHA-256 inmutable | Tabla técnica exportable | Layout: `FLEXIBLE` (tab, drawer o página) |
| **S09** | **Listas de Costo y Precios** | Precios de compra, MO y márgenes | OWNER (`FIXED_BY_CONTRACT`) | `/pricing/cost-lists` (`CURRENT_BASELINE`) | `price_audit_logs` obligatorio | Hoja de cálculo con celdas | Layout: `FLEXIBLE` • Composición: `FLEXIBLE` |
| **S10** | **Previsualización & Emisión PDF**| Congelación legal de cotización DOC-01 | OWNER, ESTIMATOR (`FIXED_BY_CONTRACT`) | `/projects/:id/quote-preview` (`CURRENT_BASELINE`) | Inmutabilidad `project_versions` | Visor split-screen PDF | Layout: `FLEXIBLE` • Drawer/Modal: `FLEXIBLE` |
| **S11** | **Orden de Trabajo (OT)** | Ficha de corte para planta | OWNER, WORKSHOP_MANAGER (`FIXED_BY_CONTRACT`) | `/orders/ot/:id` (`CURRENT_BASELINE`) | Clic humano obligatorio | Hoja DOC-03 de taller | Layout: `FLEXIBLE` • Formato: `FLEXIBLE` |
| **S12** | **Visor 3D y Cinemática** | Inspección 3D orbital y apertura | Todos / Cliente (`FIXED_BY_CONTRACT`) | `/view/:token` o integrado (`CURRENT_BASELINE`) | Sin costos ni despiece interno | Canvas 3D interactivo | Layout: `FLEXIBLE` • Engine: `FLEXIBLE` |
| **S13** | **Catálogo de Perfiles** | Series técnicas, nudos y accesorios | OWNER, WORKSHOP_MANAGER (`FIXED_BY_CONTRACT`) | `/catalogs/systems` (`CURRENT_BASELINE`) | Blindaje RLS de perfiles propios | Explorador de series | Layout: `FLEXIBLE` • Composición: `FLEXIBLE` |
| **S14** | **Compilador de Catálogos IA** | Mapeo asistido de fichas proveedor | OWNER (`FIXED_BY_CONTRACT`) | `/catalogs/compiler` (`CURRENT_BASELINE`) | `ai_audit_logs` previo | Split-screen PDF vs Catálogo | Layout: `FLEXIBLE` • Paneles: `FLEXIBLE` |
| **S15** | **Matriz Junquillo–Vidrio** | Compatibilidad espesores | OWNER, WORKSHOP_MANAGER (`FIXED_BY_CONTRACT`) | `/catalogs/systems/:id/glazing` (`CURRENT_BASELINE`) | Verificación estricta de holguras | Matriz bidimensional | Layout: `FLEXIBLE` • Componente: `FLEXIBLE` |
| **S16** | **Inventario de Retazos QR** | Control de sobrantes $\ge 600\text{ mm}$ | WORKSHOP_MANAGER (`FIXED_BY_CONTRACT`) | `/inventory/offcuts` (`CURRENT_BASELINE`) | Ciclo RESERVED $\rightarrow$ CONSUMED | Vista móvil con escáner QR | Layout: `FLEXIBLE` • App/Web: `FLEXIBLE` |
| **S17** | **Certificado Fabricabilidad**| Sello de calidad T8 con hash | OWNER, ESTIMATOR (`FIXED_BY_CONTRACT`) | `/quality/certificates/:id` (`CURRENT_BASELINE`) | Doble ciego multi-modelo | Panel de trazabilidad DOC-08 | Layout: `FLEXIBLE` • Formato: `FLEXIBLE` |
| **S18** | **Bandeja Omnicanal (Email/WA)** | Captura de solicitudes | OWNER, ESTIMATOR (`FIXED_BY_CONTRACT`) | `/inbox` (`CURRENT_BASELINE`) | Sanitización de adjuntos | Inbox con preview lateral | Layout: `FLEXIBLE` • Composición: `FLEXIBLE` |
| **S19** | **Optimizador de Corte 1D** | Secuencia de corte de barras y merma | WORKSHOP_MANAGER (`FIXED_BY_CONTRACT`) | `/orders/ot/:id/cutting-plan` (`CURRENT_BASELINE`) | Algoritmo BFD determinista | Mapa visual de barras | Layout: `FLEXIBLE` • Composición: `FLEXIBLE` |
| **S20** | **Billetera de Créditos IA** | Saldo, recarga y consumo auditado | OWNER (`FIXED_BY_CONTRACT`) | `/settings/wallet` (`CURRENT_BASELINE`) | Ledger transaccional estricto | Widget de saldo e historial | Layout: `FLEXIBLE` • Modal/Página: `FLEXIBLE` |
| **S21** | **Consola Comandos (Cmd+K)** | Edición rápida con lenguaje natural | OWNER, ESTIMATOR (`FIXED_BY_CONTRACT`) | Contextual en S06 (`NONE_INTERNAL`) | Undo sagrado + Diff previo | Overlay flotante / Drawer | Layout: `FLEXIBLE` • Composición: `FLEXIBLE` |
| **S22** | **Editor Plantillas PDF** | Personalización estética presupuestos | OWNER (`FIXED_BY_CONTRACT`) | `/settings/templates` (`CURRENT_BASELINE`) | Números protegidos inviolables | Editor visual con vista previa | Layout: `FLEXIBLE` • Componente: `FLEXIBLE` |
| **S23** | **Gestión Equipo de Taller** | Invitaciones y roles RBAC | OWNER (`FIXED_BY_CONTRACT`) | `/settings/team` (`CURRENT_BASELINE`) | Validación estricta de pertenencia | Tabla de usuarios y roles | Layout: `FLEXIBLE` • Formato: `FLEXIBLE` |
| **S24** | **Suscripción y Facturación** | Gestión de plan de la plataforma | OWNER (`FIXED_BY_CONTRACT`) | `/settings/billing` (`FIXED_BY_CONTRACT`) | Webhooks idempotentes Flow/Paddle| Portal de planes y pagos | Layout: `FLEXIBLE` • Composición: `FLEXIBLE` |
| **S25** | **Configuración General** | Parámetros de taller y mermas | OWNER (`FIXED_BY_CONTRACT`) | `/settings/general` (`CURRENT_BASELINE`) | Validación de rangos numéricos | Formulario de preferencias | Layout: `FLEXIBLE` • Tabs: `FLEXIBLE` |
| **S26** | **Portal Cliente / Instalador** | Aprobación online y montaje | Cliente / INSTALLER (`FIXED_BY_CONTRACT`) | `/view/:token` o `/p/quote/:uuid` (`FIXED_BY_CONTRACT`) | Sin márgenes ni despiece interno | Portal responsive read-only | Layout: `FLEXIBLE` • Composición: `FLEXIBLE` |
| **S27** | **Intérprete Multimodal OCR** | Ingesta de planos y cuadernos | OWNER, ESTIMATOR (`FIXED_BY_CONTRACT`) | `/ai/extract-positions` (`CURRENT_BASELINE`) | Semáforo de confianza PRD-09 | Split-screen plano vs grilla | Layout: `FLEXIBLE` • Composición: `FLEXIBLE` |
| **S28** | **Moderación Catálogo Global** (PRD-20) | Verificación sin precios | SUPERADMIN (`FIXED_BY_CONTRACT`) | `/admin/queue` (`FIXED_BY_CONTRACT`) | Cero lectura de costos ajenos | Cola admin con diff de series | Layout: `FLEXIBLE` • Composición: `FLEXIBLE` |

---

## 3. Especificación Detallada de Atributos por Capacidad

### S01 · Autenticación y Magic Link
- **Capability ID:** `S01`
- **User Goal:** Iniciar sesión de forma segura y sin contraseñas mediante Magic Link o Google OAuth.
- **Role Contract:** Público / Todos los usuarios (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/login` (`FIXED_BY_CONTRACT`).
- **Security Contract:** Supabase Auth con emisión de JWT estricto (`org_id`, `role`, `user_id`).
- **Required Information:** Email corporativo o de usuario.
- **Current Surface Baseline:** Pantalla de login limpia y minimalista.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Composición de componentes: `FLEXIBLE` (puede integrarse como modal o página).

### S02 · Onboarding de Organización y Taller
- **Capability ID:** `S02`
- **User Goal:** Registrar los datos fiscales, moneda base y taller del usuario nuevo.
- **Role Contract:** Rol `OWNER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/onboarding` (`CURRENT_BASELINE`).
- **Security Contract:** Creación atómica de tenant en `organizations` y membresía inicial con RLS habilitado.
- **Required Information:** Nombre del taller, RUT/tax ID, logo, moneda (CLP/USD).
- **Current Surface Baseline:** Wizard paso a paso de bienvenida.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Composición: `FLEXIBLE` (wizard, accordion o formulario único).

### S03 · Dashboard Operativo & KPIs
- **Capability ID:** `S03`
- **User Goal:** Supervisar indicadores de volumen, margen estimado, cotizaciones pendientes y actividad del taller.
- **Role Contract:** Roles `OWNER`, `ESTIMATOR`, `WORKSHOP_MANAGER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/dashboard` (`CURRENT_BASELINE`).
- **Security Contract:** Consultas filtradas 100% por tenant (`current_user_org_ids()`).
- **Required Information:** Resumen agregado de cotizaciones, montos en moneda local y órdenes activas.
- **Current Surface Baseline:** Tablero de métricas con tarjetas y gráficos de resumen.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Cantidad y disposición de widgets: `FLEXIBLE`.

### S04 · Listado de Proyectos
- **Capability ID:** `S04`
- **User Goal:** Buscar, filtrar y acceder a las cotizaciones y proyectos existentes.
- **Role Contract:** Roles `OWNER`, `ESTIMATOR`, `WORKSHOP_MANAGER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/projects` (`CURRENT_BASELINE`).
- **Security Contract:** Aislamiento multi-tenant estricto mediante RLS.
- **Required Information:** Lista de proyectos con estado, cliente, fecha y monto total.
- **Current Surface Baseline:** Grilla tabular interactiva con filtros rápidos.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Densidad de información: `FLEXIBLE` (tabla, lista de cards o split view).

### S05 · Detalle de Proyecto y Gestión de Vanos
- **Capability ID:** `S05`
- **User Goal:** Gestionar los vanos de una obra, cambiar estados y coordinar la emisión de documentos.
- **Role Contract:** Roles `OWNER`, `ESTIMATOR`, `WORKSHOP_MANAGER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/projects/:id` (`FIXED_BY_CONTRACT`).
- **Security Contract:** Control de transición de estados de proyecto y bloqueo de edición en estados congelados.
- **Required Information:** Metadatos del proyecto, lista de vanos con cotas y estado comercial.
- **Current Surface Baseline:** Vista maestro-detalle con cards de vanos y barra de acciones.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Composición de controles: `FLEXIBLE`.

### S06 · Lienzo CAD 2D Paramétrico
- **Capability ID:** `S06`
- **User Goal:** Diseñar y dimensionar aberturas de PVC/aluminio con recálculo paramétrico en tiempo real a 0.00 mm.
- **Role Contract:** Roles `OWNER`, `ESTIMATOR` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/projects/:id/positions/:posId/edit` (`CURRENT_BASELINE`).
- **Security Contract:** Todo cálculo numérico se delega al motor `/engine`; prohibido inventar holguras en frontend.
- **Required Information:** Árbol paramétrico (`parametric_tree`), dimensiones totales, sistema de perfil y vidrio.
- **Current Surface Baseline:** Editor CAD con viewport SVG interactivo y cotas editables.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Paneles acoplables o flotantes: `FLEXIBLE`.

### S07 · Inspector Técnico R01–R14
- **Capability ID:** `S07`
- **User Goal:** Detectar transgresiones normativas y físicas (límites de vidrio, peso de hoja, holgura) y corregir en 1 clic.
- **Role Contract:** Roles `OWNER`, `ESTIMATOR` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** Herramienta contextual integrada en S06 (`NONE_INTERNAL`).
- **Security Contract:** Validación determinista de 14 reglas físicas; advertencias de seguridad ineludibles.
- **Required Information:** Árbol geométrico y lista de infracciones técnicas emitidas por el Inspector.
- **Current Surface Baseline:** Modal contextual disparado por botón de advertencias en S06.
- **Surface Flexibility:**
  - *Contrato Temporal de SHOT-07:* `MODAL` (congelado por `PD-07-27 — S07` en `PLAN_SHOT-07.md`).
  - *Flexibilidad Global Futura:* `FLEXIBLE` (puede evolucionar a drawer lateral, panel dockable o split view en shots posteriores).

### S08 · Explosión BOM de Materiales
- **Capability ID:** `S08`
- **User Goal:** Inspeccionar el desglose cuantitativo milimétrico de barras de perfil, junquillos, vidrio y herrajes.
- **Role Contract:** Roles `OWNER`, `ESTIMATOR`, `WORKSHOP_MANAGER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/projects/:id/bom` (`CURRENT_BASELINE`).
- **Security Contract:** El hash SHA-256 de la lista de materiales debe ser reproducible y determinista.
- **Required Information:** Lista de piezas, longitudes de corte a 0.00 mm, tipo de ángulo y áreas de vidrio.
- **Current Surface Baseline:** Tabla técnica exportable a Excel y PDF.
- **Surface Flexibility:** Layout: `FLEXIBLE` (pestaña en S05, modal contextual o página completa).

### S09 · Listas de Costo y Precios
- **Capability ID:** `S09`
- **User Goal:** Gestionar los costos de compra de insumos, costo de mano de obra y márgenes de ganancia.
- **Role Contract:** Rol exclusivo `OWNER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/pricing/cost-lists` (`CURRENT_BASELINE`).
- **Security Contract:** Registro obligatorio en `price_audit_logs` ANTES de mutar cualquier valor; RLS absoluto.
- **Required Information:** Códigos de artículos, proveedor, costo unitario en moneda local y factor de merma.
- **Current Surface Baseline:** Hoja de cálculo interactiva con celdas de edición rápida.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Composición: `FLEXIBLE`.

### S10 · Previsualización & Emisión PDF
- **Capability ID:** `S10`
- **User Goal:** Revisar y congelar la cotización oficial comercial (DOC-01) antes del envío al cliente.
- **Role Contract:** Roles `OWNER`, `ESTIMATOR` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/projects/:id/quote-preview` (`CURRENT_BASELINE`).
- **Security Contract:** Al emitir, genera un registro inmutable en `project_versions` con hash criptográfico.
- **Required Information:** Datos del cliente, cotización calculada, condiciones de pago y notas técnicas.
- **Current Surface Baseline:** Visor split-screen con previsualización del PDF en tiempo real.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Mecanismo de previsualización: `FLEXIBLE` (drawer, modal o página).

### S11 · Orden de Trabajo (OT)
- **Capability ID:** `S11`
- **User Goal:** Generar la orden de manufactura para el taller con listas de corte y secuencias de armado.
- **Role Contract:** Roles `OWNER`, `WORKSHOP_MANAGER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/orders/ot/:id` (`CURRENT_BASELINE`).
- **Security Contract:** La transición a estado "En Producción" exige confirmación humana explícita.
- **Required Information:** Plan de corte, lista de herrajes, vidrios y etiquetas de identificación.
- **Current Surface Baseline:** Ficha técnica imprimible DOC-03.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Formato de presentación: `FLEXIBLE`.

### S12 · Visor 3D y Cinemática
- **Capability ID:** `S12`
- **User Goal:** Visualizar el vano en 3D con simulación interactiva de apertura para validación o venta.
- **Role Contract:** Todos los usuarios / Cliente final (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** Integrado en `/view/:token` o visor interno (`CURRENT_BASELINE`).
- **Security Contract:** Sin costos ni despiece interno en el bundle de datos expuesto.
- **Required Information:** `parametric_tree` geométrico y acabados de superficie.
- **Current Surface Baseline:** Canvas WebGL orbital 360° con controles táctiles.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Engine de renderizado: `FLEXIBLE` (Three.js, R3F, Babylon.js o equivalente).

### S13 · Catálogo de Sistemas de Perfil
- **Capability ID:** `S13`
- **User Goal:** Administrar las series de carpintería disponibles en el taller (marcos, hojas, travesaños).
- **Role Contract:** Roles `OWNER`, `WORKSHOP_MANAGER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/catalogs/systems` (`CURRENT_BASELINE`).
- **Security Contract:** Los sistemas privados de una organización están aislados de otras mediante RLS.
- **Required Information:** Parámetros geométricos de perfiles, nudos y restricciones mecánicas.
- **Current Surface Baseline:** Explorador de series con fichas técnicas.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Composición: `FLEXIBLE`.

### S14 · Compilador de Catálogos IA
- **Capability ID:** `S14`
- **User Goal:** Extraer automáticamente datos de perfiles y nudos desde catálogos PDF de fabricantes.
- **Role Contract:** Rol `OWNER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/catalogs/compiler` (`CURRENT_BASELINE`).
- **Security Contract:** Registro en `ai_audit_logs` de la respuesta multimodal antes de aplicar a la base de datos.
- **Required Information:** Catálogo PDF del extrusor y mapeo de parámetros.
- **Current Surface Baseline:** Interfaz dividida (PDF a la izquierda, formulario estructurado a la derecha).
- **Surface Flexibility:** Layout: `FLEXIBLE`, Flujo de validación: `FLEXIBLE`.

### S15 · Matriz Junquillo–Vidrio
- **Capability ID:** `S15`
- **User Goal:** Configurar las combinaciones permitidas entre paquetes de vidrio y junquillos de retención.
- **Role Contract:** Roles `OWNER`, `WORKSHOP_MANAGER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/catalogs/systems/:id/glazing` (`CURRENT_BASELINE`).
- **Security Contract:** Validación estricta: ninguna cotización puede usar una combinación no autorizada en matriz.
- **Required Information:** Espesores de vidrio (monolítico o DVH) y códigos de junquillo con sus descuentos.
- **Current Surface Baseline:** Matriz bidimensional interactiva de selección rápida.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Componente de edición: `FLEXIBLE`.

### S16 · Inventario de Retazos QR
- **Capability ID:** `S16`
- **User Goal:** Registrar y reutilizar sobrantes de barras $\ge 600\text{ mm}$ mediante etiquetas con código QR.
- **Role Contract:** Rol `WORKSHOP_MANAGER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/inventory/offcuts` (`CURRENT_BASELINE`).
- **Security Contract:** Ciclo de vida estricto: `AVAILABLE` $\rightarrow$ `RESERVED` $\rightarrow$ `CONSUMED`.
- **Required Information:** Longitud remanente, código de perfil, color, ubicación en rack y QR.
- **Current Surface Baseline:** Vista optimizada para tablet/móvil con acceso a cámara para escaneo.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Formato de escaneo: `FLEXIBLE`.

### S17 · Certificado de Fabricabilidad
- **Capability ID:** `S17`
- **User Goal:** Consultar la verificación técnica independiente de un proyecto con sello doble ciego.
- **Role Contract:** Roles `OWNER`, `ESTIMATOR` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/quality/certificates/:id` (`CURRENT_BASELINE`).
- **Security Contract:** Concordancia 100% entre modelos evaluadores; hash SHA-256 incorruptible DOC-08.
- **Required Information:** Identificador de proyecto, fecha de análisis, discrepancias y firma criptográfica.
- **Current Surface Baseline:** Panel de auditoría de calidad con QR de validación pública.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Composición: `FLEXIBLE`.

### S18 · Bandeja Omnicanal (Email / WhatsApp)
- **Capability ID:** `S18`
- **User Goal:** Recibir y transformar solicitudes de cotización entrantes por correo o mensajería en borradores.
- **Role Contract:** Roles `OWNER`, `ESTIMATOR` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/inbox` (`CURRENT_BASELINE`).
- **Security Contract:** Sanitización estricta de adjuntos; las cotizaciones generadas inician SIEMPRE como `DRAFT`.
- **Required Information:** Mensaje del cliente, archivos adjuntos (PDF/imágenes) y datos de contacto.
- **Current Surface Baseline:** Bandeja de correo con vista previa lateral y botón "Convertir a Cotización".
- **Surface Flexibility:** Layout: `FLEXIBLE`, Disposición de paneles: `FLEXIBLE`.

### S19 · Optimizador de Corte 1D (BFD)
- **Capability ID:** `S19`
- **User Goal:** Visualizar el aprovechamiento de barras de perfil estándar y la secuencia de cortes con mínima merma.
- **Role Contract:** Rol `WORKSHOP_MANAGER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/orders/ot/:id/cutting-plan` (`CURRENT_BASELINE`).
- **Security Contract:** Salida generada por algoritmo BFD determinista con tolerancia de `0.00 mm`.
- **Required Information:** Lista de piezas de la OT, longitud de barra base ($6.0\text{ m}$) y ancho de corte de sierra.
- **Current Surface Baseline:** Diagrama de barras longitudinales con codificación por color y reporte de merma.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Modo de visualización: `FLEXIBLE`.

### S20 · Billetera de Créditos IA
- **Capability ID:** `S20`
- **User Goal:** Monitorear el saldo de créditos, recargar paquetes y consultar la auditoría de consumos.
- **Role Contract:** Rol `OWNER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/settings/wallet` (`CURRENT_BASELINE`).
- **Security Contract:** Ledger inmutable; todo débito corresponde a un evento registrado en `ai_audit_logs`.
- **Required Information:** Saldo disponible, historial de recargas, consumos por operación y alertas de umbral.
- **Current Surface Baseline:** Widget de saldo con tabla de transacciones recientes.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Modal o sección dentro de configuración: `FLEXIBLE`.

### S21 · Consola de Comandos NLP (Cmd+K)
- **Capability ID:** `S21`
- **User Goal:** Modificar vanos o aplicar descuentos mediante instrucciones en lenguaje natural con previsualización.
- **Role Contract:** Roles `OWNER`, `ESTIMATOR` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** Herramienta contextual overlay sobre S06 (`NONE_INTERNAL`).
- **Security Contract:** Protocolo de Undo sagrado; ninguna tool de lenguaje escribe números directos (solo diff paramétrico hacia `/engine`).
- **Required Information:** Texto del comando, diff generado antes/después y confirmación de aplicación.
- **Current Surface Baseline:** Barra de comando flotante centrada (estilo Spotlight) con modal diff.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Composición: `FLEXIBLE` (drawer, command bar o modal).

### S22 · Editor de Plantillas PDF
- **Capability ID:** `S22`
- **User Goal:** Personalizar colores, tipografías y notas comerciales en el PDF de cotización sin alterar cifras.
- **Role Contract:** Rol `OWNER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/settings/templates` (`CURRENT_BASELINE`).
- **Security Contract:** Bloques protegidos: los cálculos de totales y descuentos son inalterables por el usuario.
- **Required Information:** Selector de plantilla, paleta de colores, logo de taller y pie de página.
- **Current Surface Baseline:** Editor visual con vista previa sincronizada.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Componentes de edición: `FLEXIBLE`.

### S23 · Gestión de Equipo de Taller
- **Capability ID:** `S23`
- **User Goal:** Invitar colaboradores, asignar roles (Admin, Cotizador, Taller) y revocar accesos.
- **Role Contract:** Rol exclusivo `OWNER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/settings/team` (`CURRENT_BASELINE`).
- **Security Contract:** RLS estricto; ningún usuario puede otorgarse roles superiores a su nivel.
- **Required Information:** Lista de miembros, emails, roles asignados y estado de invitación.
- **Current Surface Baseline:** Tabla de administración de usuarios.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Formato: `FLEXIBLE`.

### S24 · Suscripción y Facturación de Plataforma
- **Capability ID:** `S24`
- **User Goal:** Gestionar el plan mensual/anual de Dekopen, medios de pago y descargar facturas del servicio.
- **Role Contract:** Rol exclusivo `OWNER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/settings/billing` (`FIXED_BY_CONTRACT`).
- **Security Contract:** Integración segura con pasarelas de pago (Flow en Chile, Paddle internacional) con webhooks HMAC.
- **Required Information:** Plan activo, próximo cobro, método de pago y comprobantes fiscales.
- **Current Surface Baseline:** Portal de planes con toggle mensual/anual y botón de checkout.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Composición: `FLEXIBLE`.

### S25 · Configuración General y Parámetros
- **Capability ID:** `S25`
- **User Goal:** Ajustar parámetros generales del taller: merma estándar, holguras de instalación por defecto y moneda.
- **Role Contract:** Rol `OWNER` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/settings/general` (`CURRENT_BASELINE`).
- **Security Contract:** Validación estricta de rangos numéricos; prohibido ingresar valores negativos o incongruentes.
- **Required Information:** Porcentajes de merma, holgura perimetral por defecto ($10\text{ mm}$), moneda y datos de contacto.
- **Current Surface Baseline:** Formulario de ajustes agrupado por pestañas.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Organización en tabs o acordeones: `FLEXIBLE`.

### S26 · Portal Cliente / Instalador
- **Capability ID:** `S26`
- **User Goal:** Proveer al cliente final o al instalador en obra una vista de solo lectura de las aberturas y su ubicación.
- **Role Contract:** Cliente final / Instalador (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/view/:token` o `/p/quote/:uuid` (`FIXED_BY_CONTRACT`).
- **Security Contract:** Vista 100% solo lectura, blindada contra exposición de costos de taller o despiece interno.
- **Required Information:** Plano exterior, cotas de vano, ubicación en la obra y estado de fabricación/instalación.
- **Current Surface Baseline:** Portal web responsive optimizado para teléfonos móviles en terreno.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Composición: `FLEXIBLE`.

### S27 · Intérprete Multimodal OCR
- **Capability ID:** `S27`
- **User Goal:** Extraer cuadros de vanos desde planos arquitectónicos en PDF, imágenes o cuadernos de obra.
- **Role Contract:** Roles `OWNER`, `ESTIMATOR` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/ai/extract-positions` (`CURRENT_BASELINE`).
- **Security Contract:** Semáforo de confianza según contrato activo de PRD-09; celdas rojas bloquean la importación hasta confirmación humana.
- **Required Information:** Documento PDF/imagen, cajas de selección de vanos y grilla de datos extraídos.
- **Current Surface Baseline:** Interfaz split-screen con visor de documento interactivo y tabla editable.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Composición: `FLEXIBLE`.

### S28 · Cola de Moderación de Catálogo Global
- **Capability ID:** `S28`
- **Normative PRD:** [`PRD-20: Catálogo Global y Moderación Administrativa`](./PRD-20.md) (SHOT-20).
- **User Goal:** Revisar y aprobar series de perfiles enviadas por organizaciones para publicación en el catálogo comunitario.
- **Role Contract:** Rol exclusivo `SUPERADMIN` (`FIXED_BY_CONTRACT`).
- **Route / Deep-Link Contract:** `/admin/queue` (`FIXED_BY_CONTRACT`).
- **Security Contract:** Aislamiento absoluto: los administradores **no pueden** consultar precios privados de ningún tenant desde esta cola.
- **Required Information:** Lista de solicitudes de publicación, diferencias geométricas de perfiles y resultado de tests.
- **Current Surface Baseline:** Grilla de cola de revisión con comparador dimensional y botón de firma.
- **Surface Flexibility:** Layout: `FLEXIBLE`, Composición: `FLEXIBLE`.
