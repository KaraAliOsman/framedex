# DEKOPEN — BASELINE DE SUPERFICIES Y FLUJOS DE USUARIO (CAPABILITY MAP S01–S28) (v1.3 MASTER)

> **Estado:** Documento Normativo Activo — Flexible & Componible
> **Propósito:** Mapeo Canónico de Capacidades, Roles, Contratos y Superficies de Interfaz
> **Filosofía UX:** Ergonomía Adaptable de Taller, Eficiencia Operativa y Componibilidad Modular

---

## 1. Principios Constitucionales de Componibilidad y Flexibilidad

1. **IDs de Capacidad y Flujo, No Prisión de Pantallas Físicas:**
   Los identificadores `S01` a `S28` representan **capacidades funcionales y contratos de flujo del usuario**, preservados para trazabilidad histórica, roadmaps y auditoría. **NO imponen la obligación de tener exactamente 28 pantallas web aisladas**.
2. **Niveles de Flexibilidad de Superficie (`surface_flexibility`):**
   Cada capacidad se rige por uno de tres niveles formales:
   - `FIXED_BY_CONTRACT`: La ruta URL o formato es un contrato inmutable externo (autenticación, retornos de pago, enlaces públicos seguros compartidos a clientes o cola de administración central).
   - `CURRENT_BASELINE`: Superficie o formato definido como línea base para los shots actuales.
   - `FLEXIBLE`: La interfaz puede implementarse libremente como modal contextual, panel acoplable (dockable), drawer flotante, pestaña o split-screen si demuestra mejor usabilidad y velocidad de taller.
3. **Precedencia Temporal del Shot Actual (Principio Inviolable):**
   > **`GLOBAL FLEXIBILITY DOES NOT RETROACTIVELY DESTABILIZE AN ACTIVE SHOT CONTRACT.`**
   Si una decisión de interfaz ya quedó formalmente congelada en un plan de shot activo mediante resolución del Owner (ejemplo: `S07` congelado como Modal contextual en `docs/plans/PLAN_SHOT-07.md`), dicha decisión **se mantiene inmutable durante la ejecución de ese shot**. La flexibilidad global habilita la evolución en shots posteriores, jamás la desestabilización del sprint en curso.

---

## 2. Matriz Maestra de Capacidades y Superficies (S01 a S28)

| ID | Capacidad / Superficie | Objetivo Primario (User Goal) | Roles | Deep-Link / Contrato | Superficie Base Actual | Flexibilidad |
|---|---|---|---|---|---|:---:|
| **S01** | **Autenticación y Magic Link** | Acceso seguro sin passwords vulnerables | Público / Todos | `/login` | Pantalla de login limpia | `FIXED_BY_CONTRACT` |
| **S02** | **Onboarding de Taller** | Registro fiscal, RUT, logo y moneda | OWNER | `/onboarding` | Wizard guiado paso a paso | `FIXED_BY_CONTRACT` |
| **S03** | **Dashboard Operativo & KPIs** | Visibilidad de margen, volumen y alertas | OWNER, ESTIMATOR, MGR | `/dashboard` | Tablero de métricas modular | `CURRENT_BASELINE` |
| **S04** | **Listado de Proyectos** | Búsqueda y gestión de cotizaciones | OWNER, ESTIMATOR, MGR | `/projects` | Grilla tabular con filtros | `CURRENT_BASELINE` |
| **S05** | **Detalle de Proyecto & Vanos** | Gestión de vanos, estados y emisión | OWNER, ESTIMATOR, MGR | `/projects/:id` | Maestro-detalle con cards | `FIXED_BY_CONTRACT` |
| **S06** | **Lienzo CAD 2D Paramétrico** | Edición geométrica en tiempo real a 0.00mm | OWNER, ESTIMATOR | `/projects/:id/positions/:posId/edit` | Workspace CAD SVG viewport | `CURRENT_BASELINE` |
| **S07** | **Inspector Técnico R01–R14** | Detección de fallas físicas y fix 1-clic | OWNER, ESTIMATOR | Contextual a S06 (sin URL) | Modal contextual en S06 | `CURRENT_BASELINE` |
| **S08** | **Explosión BOM de Materiales** | Desglose milimétrico de perfiles y vidrio | OWNER, ESTIMATOR, MGR | `/projects/:id/bom` | Tabla técnica exportable | `FLEXIBLE` |
| **S09** | **Listas de Costo y Precios** | Precios de compra, MO y márgenes | OWNER | `/pricing/cost-lists` | Hoja de cálculo con auditoría | `CURRENT_BASELINE` |
| **S10** | **Previsualización & Emisión PDF**| Congelación legal de cotización DOC-01 | OWNER, ESTIMATOR | `/projects/:id/quote-preview` | Visor split-screen PDF | `CURRENT_BASELINE` |
| **S11** | **Orden de Trabajo (OT)** | Ficha de corte y ensamble para planta | OWNER, WORKSHOP_MANAGER | `/orders/ot/:id` | Hoja de manufactura DOC-03 | `CURRENT_BASELINE` |
| **S12** | **Visor 3D y Cinemática** | Inspección 3D orbital y animación giro | Todos / Cliente | `/view/:token` o integrado | Canvas 3D orbital interactivo | `CURRENT_BASELINE` |
| **S13** | **Catálogo de Sistemas de Perfil**| Series de perfiles, nudos y accesorios | OWNER, WORKSHOP_MANAGER | `/catalogs/systems` | Explorador de series técnicas | `FLEXIBLE` |
| **S14** | **Compilador de Catálogos IA** | Mapeo asistido de fichas de fabricante | OWNER | `/catalogs/compiler` | Split-screen PDF vs Catálogo | `FLEXIBLE` |
| **S15** | **Matriz Junquillo–Vidrio** | Compatibilidad espesor vidrio vs junquillo| OWNER, WORKSHOP_MANAGER | `/catalogs/systems/:id/glazing` | Matriz bidimensional interactiva | `FLEXIBLE` |
| **S16** | **Inventario de Retazos QR** | Registro de sobrantes $\ge 600\text{ mm}$ | WORKSHOP_MANAGER | `/inventory/offcuts` | Vista móvil con escaneo QR | `FLEXIBLE` |
| **S17** | **Certificado de Fabricabilidad**| Sello de calidad T8 con hash SHA-256 | OWNER, ESTIMATOR | `/quality/certificates/:id` | Panel de trazabilidad DOC-08 | `FLEXIBLE` |
| **S18** | **Bandeja Omnicanal (Email/WA)** | Recepción centralizada de cotizaciones | OWNER, ESTIMATOR | `/inbox` | Inbox con preview de adjuntos | `CURRENT_BASELINE` |
| **S19** | **Optimizador de Corte 1D BFD** | Secuencia de corte de barras y merma | WORKSHOP_MANAGER | `/orders/ot/:id/cutting-plan` | Mapa visual de barras cortadas | `CURRENT_BASELINE` |
| **S20** | **Billetera de Créditos IA** | Saldo, recarga y consumo auditado | OWNER | `/settings/wallet` | Widget de saldo y transacciones | `FLEXIBLE` |
| **S21** | **Consola Comandos NLP (Cmd+K)**| Edición rápida con lenguaje natural | OWNER, ESTIMATOR | Overlay en S06 (sin URL) | Command bar flotante / Drawer | `FLEXIBLE` |
| **S22** | **Editor de Plantillas PDF** | Personalización estética de presupuestos | OWNER | `/settings/templates` | Editor visual con vista previa | `FLEXIBLE` |
| **S23** | **Gestión de Equipo de Taller** | Invitaciones y asignación de roles RBAC | OWNER | `/settings/team` | Tabla de usuarios y permisos | `FLEXIBLE` |
| **S24** | **Suscripción y Facturación** | Gestión de planes Starter/Pro/Business | OWNER | `/settings/billing` | Portal de pagos Flow/Paddle | `FIXED_BY_CONTRACT` |
| **S25** | **Configuración General & RLS** | Parámetros globales de taller y mermas | OWNER | `/settings/general` | Formulario de preferencias | `CURRENT_BASELINE` |
| **S26** | **Portal Cliente / Instalador** | Aprobación online y ficha de montaje | Cliente / INSTALLER | `/p/quote/:uuid` o `/view/:token`| Portal read-only responsive | `FIXED_BY_CONTRACT` |
| **S27** | **Intérprete Multimodal OCR** | Ingesta de planos, tablas y apuntes | OWNER, ESTIMATOR | `/ai/extract-positions` | Split-screen plano vs grilla | `CURRENT_BASELINE` |
| **S28** | **Moderación Catálogo Global** | Verificación comunitaria sin precios | SUPERADMIN | `/admin/queue` | Cola admin con diff de series | `FIXED_BY_CONTRACT` |

---

## 3. Especificación Detallada por Capacidad

### S01 · Autenticación y Magic Link
- **User Goal:** Iniciar sesión o autenticarse de forma segura y sin fricción mediante Magic Link o Google OAuth.
- **Roles:** Público / Todos los usuarios.
- **Required Information:** Email corporativo o personal del usuario.
- **Business & Security Constraints:** Cero contraseñas en texto plano; sesión gestionada mediante Supabase Auth con emisión de JWT estricto que encapsula `org_id`, `role` y `user_id`.
- **Deep-Link Requirement:** `FIXED_BY_CONTRACT` en `/login`.
- **Current Baseline Surface:** Pantalla centrada de login minimalista.
- **Surface Flexibility:** `FIXED_BY_CONTRACT`.

### S02 · Onboarding de Organización y Taller
- **User Goal:** Configurar los datos de la empresa recién creada: RUT fiscal, razón social, moneda base (CLP/USD) y logotipo.
- **Roles:** OWNER exclusivamente.
- **Required Information:** RUT/Tax ID válido, razón social, dirección de taller, moneda de operación.
- **Business & Security Constraints:** Creación de registro inmutable en `tenancy_organizations` y membresía inicial con rol OWNER.
- **Deep-Link Requirement:** `FIXED_BY_CONTRACT` en `/onboarding`.
- **Current Baseline Surface:** Formulario wizard secuencial de tres pasos.
- **Surface Flexibility:** `FIXED_BY_CONTRACT`.

### S03 · Dashboard Operativo y KPIs de Taller
- **User Goal:** Monitorear métricas de salud del taller: volumen cotizado en el mes, margen bruto promedio, vanos en cola de producción y atajos rápidos.
- **Roles:** OWNER, ESTIMATOR, WORKSHOP_MANAGER.
- **Required Information:** Resumen consolidado de proyectos, métricas de taller calculadas por backend.
- **Business & Security Constraints:** Filtrado estricto por `org_id`.
- **Deep-Link Requirement:** Recomendado en `/dashboard`.
- **Current Baseline Surface:** Tablero de tarjetas analíticas y accesos directos.
- **Surface Flexibility:** `CURRENT_BASELINE`.

### S04 · Listado y Búsqueda de Proyectos
- **User Goal:** Localizar, filtrar y clasificar proyectos según estado (Borrador, Cotizado, En Fabricación, Terminado) y cliente.
- **Roles:** OWNER, ESTIMATOR, WORKSHOP_MANAGER.
- **Required Information:** Lista de proyectos con conteo de vanos, total neto, cliente y fecha.
- **Business & Security Constraints:** Paginación eficiente y aislamiento RLS total.
- **Deep-Link Requirement:** `/projects`.
- **Current Baseline Surface:** Tabla con búsqueda en tiempo real y vista en tarjetas.
- **Surface Flexibility:** `CURRENT_BASELINE`.

### S05 · Detalle de Proyecto y Grilla de Vanos
- **User Goal:** Gestionar las aberturas (posiciones) de un proyecto, agregar nuevos vanos, duplicar vanos y emitir cotización.
- **Roles:** OWNER, ESTIMATOR, WORKSHOP_MANAGER.
- **Required Information:** ID de proyecto, lista de posiciones con cotas exteriores, serie de perfiles y precio neto unitario.
- **Business & Security Constraints:** Contrato maestro de navegación del proyecto.
- **Deep-Link Requirement:** `FIXED_BY_CONTRACT` en `/projects/:id`.
- **Current Baseline Surface:** Grilla de tarjetas de vanos con previsualización SVG miniatura y barra de resumen económico.
- **Surface Flexibility:** `FIXED_BY_CONTRACT`.

### S06 · Lienzo CAD 2D Paramétrico
- **User Goal:** Dibujar y editar visualmente la geometría de una ventana en tiempo real con tolerancia matemática garantizada de `0.00 mm`.
- **Roles:** OWNER, ESTIMATOR.
- **Required Information:** `parametric_tree` JSON de la posición seleccionada, serie de perfiles activa, cotas de ancho y alto.
- **Business & Security Constraints:** Todo recálculo proviene de `/engine` determinista. Cero float en coordenadas de cota.
- **Deep-Link Requirement:** `/projects/:id/positions/:posId/edit`.
- **Current Baseline Surface:** Workspace CAD completo con viewport SVG infinito, pan/zoom y cotas dinámicas editables.
- **Surface Flexibility:** `CURRENT_BASELINE`.

### S07 · Inspector Técnico y Corrección en 1 Clic (R01–R14)
- **User Goal:** Validar la fabricabilidad de la ventana contra las 14 reglas canónicas (límites de peso, holgura de junquillo, relación de aspecto) y corregir problemas en 1 clic.
- **Roles:** OWNER, ESTIMATOR.
- **Required Information:** Hallazgos generados por el motor de reglas en `/engine`, código de regla (R01–R14), severidad y acción de reparación recomendada.
- **Business & Security Constraints:** Mensajes en lenguaje comprensible de taller; botón de fix que emite una mutación determinista.
- **Deep-Link Requirement:** No requiere deep-link (superficie contextual acoplada al editor).
- **Current Baseline Surface:** Modal contextual superpuesto en S06 (congelado por resolución PD-07-02 de SHOT-07).
- **Surface Flexibility:** `CURRENT_BASELINE` (congelado en SHOT-07; posterior a SHOT-07 puede evolucionar a panel lateral acoplable).

### S08 · Explosión BOM y Despiece Milimétrico
- **User Goal:** Visualizar el despiece técnico completo de la ventana: barras de PVC cortadas a 45°/90° con pérdida de fusión, refuerzos de acero, metros de burlete, termopaneles y kits de herrajes.
- **Roles:** OWNER, ESTIMATOR, WORKSHOP_MANAGER.
- **Required Information:** BOM estructurado generado por `/engine/despiece.py`.
- **Business & Security Constraints:** Precisión decimal milimétrica estricta (`0.00 mm`).
- **Deep-Link Requirement:** `/projects/:id/bom`.
- **Current Baseline Surface:** Tabla técnica tabular con filtros por categoría de material.
- **Surface Flexibility:** `FLEXIBLE` (puede embeberse como pestaña en S05 o pantalla completa).

### S09 · Listas de Costo y Precios de Taller
- **User Goal:** Configurar los costos de adquisición de perfiles, vidrios y herrajes por proveedor, costo horario de taller y márgenes de ganancia.
- **Roles:** OWNER exclusivamente.
- **Required Information:** Listas de costos activas por proveedor, coeficientes de mano de obra y márgenes por tipo de cliente.
- **Business & Security Constraints:** Aislamiento RLS inviolable. Todo cambio de precio exige registro previo en `price_audit_logs` (Regla 21).
- **Deep-Link Requirement:** `/pricing/cost-lists`.
- **Current Baseline Surface:** Grilla editable con confirmación de cambios.
- **Surface Flexibility:** `CURRENT_BASELINE`.

### S10 · Previsualización y Emisión de Cotización PDF (DOC-01)
- **User Goal:** Revisar el presupuesto oficial con membrete y condiciones comerciales antes de congelarlo legalmente en `project_versions`.
- **Roles:** OWNER, ESTIMATOR.
- **Required Information:** Datos comerciales del proyecto, cliente, validez de oferta y deslose neto/IVA.
- **Business & Security Constraints:** La emisión congela un registro inmutable en `project_versions` con hash SHA-256 (Regla 12).
- **Deep-Link Requirement:** `/projects/:id/quote-preview`.
- **Current Baseline Surface:** Pantalla partida con visor PDF de alta fidelidad y panel de metadatos.
- **Surface Flexibility:** `CURRENT_BASELINE`.

### S11 · Orden de Trabajo de Taller (OT) (DOC-03)
- **User Goal:** Entregar al jefe de taller y operarios las instrucciones de fabricación con planos acotados, medidas de corte de refuerzos y orificios de desagüe.
- **Roles:** OWNER, WORKSHOP_MANAGER.
- **Required Information:** Ficha de fabricación generada por backend a partir de la versión congelada del proyecto.
- **Business & Security Constraints:** Contrato de taller inviolable; no modificable tras su pase a producción sin orden de rectificación.
- **Deep-Link Requirement:** `/orders/ot/:id`.
- **Current Baseline Surface:** Documento de manufactura imprimible con código QR de trazabilidad por vano.
- **Surface Flexibility:** `CURRENT_BASELINE`.

### S12 · Visor 3D y Cinemática de Apertura
- **User Goal:** Visualizar interactivamente la ventana en 3D volumétrico, inspeccionar acabados y simular dinámicamente sus aperturas (practicable, oscilo, corredera).
- **Roles:** Universal / Clientes y Taller.
- **Required Information:** Geometría de componentes generada desde `parametric_tree`, shaders de materiales y vectores de pivoteo cinemático.
- **Business & Security Constraints:** No expone despiece interno ni costos de taller en el bundle público.
- **Deep-Link Requirement:** Embebido en portal cliente `/view/:token` o ruta técnica `/viewer-3d/:posId`.
- **Current Baseline Surface:** Canvas 3D interactivo con controles orbitales y selector de apertura.
- **Surface Flexibility:** `CURRENT_BASELINE` (integrado oficialmente en SHOT-19).

### S13 · Catálogo de Sistemas de Perfiles y Herrajes
- **User Goal:** Explorar los sistemas de perfiles habilitados para el taller (ej: series de 60mm, 70mm, correderas y batientes) con sus geometrías de nudo.
- **Roles:** OWNER, WORKSHOP_MANAGER.
- **Required Information:** Registro de series en `profile_systems`, artículos y kits de herrajes asociados.
- **Business & Security Constraints:** Parámetros leídos de base de datos certificada (Regla 6).
- **Deep-Link Requirement:** `/catalogs/systems`.
- **Current Baseline Surface:** Catálogo visual con acordeones por serie.
- **Surface Flexibility:** `FLEXIBLE`.

### S14 · Compilador Asistido de Catálogos por IA
- **User Goal:** Cargar un catálogo técnico nuevo en PDF o Excel y asistirse con IA para mapear artículos, nudos y descuentos a la base de datos.
- **Roles:** OWNER.
- **Required Information:** Documento PDF/Excel subido, mapeador de columnas y extractor semántico.
- **Business & Security Constraints:** Los datos extraídos deben verificarse contra el caso de oro antes de activarse para cotizar.
- **Deep-Link Requirement:** `/catalogs/compiler`.
- **Current Baseline Surface:** Split-screen: visor de documento a la izquierda, formulario de asignación a la derecha.
- **Surface Flexibility:** `FLEXIBLE`.

### S15 · Matriz Junquillo–Vidrio
- **User Goal:** Definir la regla biunívoca que asigna el junquillo adecuado según el espesor total de vidrio (ej: junquillo curvo 18mm para DVH 24mm).
- **Roles:** OWNER, WORKSHOP_MANAGER.
- **Required Information:** Rango de espesores de acristalamiento y SKUs de junquillo compatibles.
- **Business & Security Constraints:** Evita el armado de termopaneles sin presión de sellado adecuada.
- **Deep-Link Requirement:** `/catalogs/systems/:id/glazing`.
- **Current Baseline Surface:** Matriz bidimensional interactiva editable.
- **Surface Flexibility:** `FLEXIBLE`.

### S16 · Inventario y Registro de Retazos QR (Offcuts)
- **User Goal:** Registrar retazos sobrantes de barras con longitud $\ge 600\text{ mm}$ e imprimirles código QR para reutilización en corte 1D.
- **Roles:** WORKSHOP_MANAGER.
- **Required Information:** Longitud remanente en mm, SKU de perfil, color y código de ubicación en estantería.
- **Business & Security Constraints:** Cumple con el ciclo de estados `AVAILABLE -> RESERVED -> CONSUMED`.
- **Deep-Link Requirement:** `/inventory/offcuts`.
- **Current Baseline Surface:** Vista web-móvil adaptada para tablets de taller con lector de cámara QR.
- **Surface Flexibility:** `FLEXIBLE`.

### S17 · Panel de Certificado de Fabricabilidad (DOC-08)
- **User Goal:** Consultar la certificación técnica del proyecto tras superar el doble ciego T8, con hash criptográfico y sello QR de garantía.
- **Roles:** OWNER, ESTIMATOR.
- **Required Information:** Registro en `quality_certificates`, hash de cálculo, logs de verificación de ambos agentes evaluadores.
- **Business & Security Constraints:** Inmutabilidad de la firma criptográfica SHA-256.
- **Deep-Link Requirement:** `/quality/certificates/:id`.
- **Current Baseline Surface:** Panel de auditoría técnica con visor del certificado descargable.
- **Surface Flexibility:** `FLEXIBLE`.

### S18 · Bandeja de Entrada Omnicanal (Email & WhatsApp)
- **User Goal:** Centralizar solicitudes de presupuesto entrantes desde emails o mensajes de WhatsApp y convertirlas en proyectos borradores.
- **Roles:** OWNER, ESTIMATOR.
- **Required Information:** Mensaje entrante, remitente, archivos adjuntos (PDFs de planos o fotos de vanos).
- **Business & Security Constraints:** Tareas en segundo plano desacopladas; creación de proyectos siempre en estado `DRAFT`.
- **Deep-Link Requirement:** `/inbox`.
- **Current Baseline Surface:** Bandeja estilo correo electrónico con visor lateral de mensajes y adjuntos.
- **Surface Flexibility:** `CURRENT_BASELINE`.

### S19 · Optimizador y Mapa de Corte 1D (BFD)
- **User Goal:** Calcular el patrón de corte óptimo barra por barra mediante Best Fit Decreasing, minimizando la merma y generando el pedido comercial DOC-04/DOC-05.
- **Roles:** WORKSHOP_MANAGER.
- **Required Information:** Lista de piezas de PVC requeridas con sus ángulos de corte (45°/90°) y longitud de barra comercial (6.00 m).
- **Business & Security Constraints:** Descuento obligatorio de pérdida de soldadura por fusión ($3.00\text{ mm}$ estándar) y ancho de disco (*kerf*). Algoritmo determinista con tie-break congelado.
- **Deep-Link Requirement:** `/orders/ot/:id/cutting-plan`.
- **Current Baseline Surface:** Diagrama interactivo de barras de corte con código de barras por pieza.
- **Surface Flexibility:** `CURRENT_BASELINE`.

### S20 · Billetera y Consumo de Créditos IA
- **User Goal:** Visualizar el saldo de créditos para operaciones de IA (OCR, diffs de comandos), historial de consumo auditado y compra de recargas.
- **Roles:** OWNER exclusivamente.
- **Required Information:** Saldo de créditos en `tenancy_organizations`, transacciones en ledger de facturación.
- **Business & Security Constraints:** Inmunidad ante saldo cero: agotar créditos suspende herramientas de IA pero **jamás** bloquea el motor 2D ni la emisión de PDFs.
- **Deep-Link Requirement:** `/settings/wallet`.
- **Current Baseline Surface:** Widget de saldo con tabla de auditoría y botón de recarga vía pasarela.
- **Surface Flexibility:** `FLEXIBLE`.

### S21 · Consola de Comandos NLP y Diff Preview (Cmd+K)
- **User Goal:** Ejecutar modificaciones geométricas o comerciales mediante comandos rápidos de teclado o lenguaje natural con previsualización antes/después y soporte de `Cmd+Z` (Undo).
- **Roles:** OWNER, ESTIMATOR.
- **Required Information:** Texto del comando del usuario, `current_tree` y contexto de cotización.
- **Business & Security Constraints:** El LLM solo propone diffs tipados (Tools T2/T3); el cálculo de cotas y precios lo realiza exclusivamente `/engine`.
- **Deep-Link Requirement:** No requiere URL (superficie flotante superpuesta).
- **Current Baseline Surface:** Command Bar flotante desplegable con modal de previsualización comparativa antes/después.
- **Surface Flexibility:** `FLEXIBLE`.

### S22 · Personalizador de Plantillas de Presupuesto
- **User Goal:** Personalizar el aspecto estético de las cotizaciones PDF (colores institucionales, logotipo del taller, bloques de condiciones y disclaimers protegidos).
- **Roles:** OWNER.
- **Required Information:** Configuración de estilos CSS seguros, imágenes de cabecera y términos de pago.
- **Business & Security Constraints:** Se prohíbe la inyección de código que altere los totales calculados por el motor.
- **Deep-Link Requirement:** `/settings/templates`.
- **Current Baseline Surface:** Editor de opciones visuales con previsualizador PDF interactivo.
- **Surface Flexibility:** `FLEXIBLE`.

### S23 · Gestión de Equipo de Taller y Roles (RBAC)
- **User Goal:** Invitar colaboradores de la carpintería y asignarles roles con permisos granulares (Owner, Estimator, Workshop Manager, Installer).
- **Roles:** OWNER exclusivamente.
- **Required Information:** Email del invitado y rol seleccionado.
- **Business & Security Constraints:** Control estricto de acceso; solo el Owner puede asignar o revocar roles de administración y precios.
- **Deep-Link Requirement:** `/settings/team`.
- **Current Baseline Surface:** Tabla de usuarios con estados de invitación y switches de permisos.
- **Surface Flexibility:** `FLEXIBLE`.

### S24 · Suscripción y Facturación (Planes Dekopen)
- **User Goal:** Gestionar el plan de suscripción mensual/anual (Starter, Profesional, Business, Business 2x), actualizar medios de pago y descargar facturas.
- **Roles:** OWNER exclusivamente.
- **Required Information:** ID de cliente en pasarela de pago (Flow CLP o Paddle USD), estado de suscripción.
- **Business & Security Constraints:** Idempotencia absoluta en webhooks de facturación (Regla 13).
- **Deep-Link Requirement:** `FIXED_BY_CONTRACT` en `/settings/billing`.
- **Current Baseline Surface:** Panel de suscripción con botones de checkout seguro y tabla de facturas.
- **Surface Flexibility:** `FIXED_BY_CONTRACT`.

### S25 · Configuración General y Políticas de Taller
- **User Goal:** Configurar parámetros operativos del taller: holgura estándar de instalación, tolerancia de escuadra, pérdida de fusión y margen de merma.
- **Roles:** OWNER.
- **Required Information:** Parámetros guardados en configuración de la organización.
- **Business & Security Constraints:** Modificaciones registradas con trazabilidad de usuario.
- **Deep-Link Requirement:** `/settings/general`.
- **Current Baseline Surface:** Formulario de preferencias generales de taller.
- **Surface Flexibility:** `CURRENT_BASELINE`.

### S26 · Portal Público de Aprobación de Cotización / Vista Instalador
- **User Goal:** Permitir que el cliente final revise y apruebe online la cotización desde su smartphone, o que el instalador en obra consulte medidas de montaje.
- **Roles:** Cliente Final / INSTALLER.
- **Required Information:** Token criptográfico UUID de acceso público de solo lectura.
- **Business & Security Constraints:** Seguridad estricta: **el bundle de JavaScript y las respuestas de API JAMÁS contienen costos de compra, fórmulas de margen ni despiece interno del taller**.
- **Deep-Link Requirement:** `FIXED_BY_CONTRACT` en `/p/quote/:uuid` o `/view/:token`.
- **Current Baseline Surface:** Interfaz web ligera y responsive optimizada para smartphones.
- **Surface Flexibility:** `FIXED_BY_CONTRACT`.

### S27 · Intérprete Multimodal OCR de Planos y Croquis
- **User Goal:** Subir un plano arquitectónico, tabla de vanos o croquis manuscrito de obra y extraer automáticamente los vanos hacia un borrador revisable en menos de 5 minutos humanos.
- **Roles:** OWNER, ESTIMATOR.
- **Required Information:** Archivo PDF o imagen en alta resolución subido por el usuario.
- **Business & Security Constraints:** Los apuntes manuscritos son soportados con semáforo de certeza (Verde/Amarillo/Rojo). Toda lectura ambigua exige confirmación humana en split-screen; no se inventan cotas.
- **Deep-Link Requirement:** `/ai/extract-positions`.
- **Current Baseline Surface:** Split-screen con plano interactivo a la izquierda y tabla editable a la derecha.
- **Surface Flexibility:** `CURRENT_BASELINE`.

### S28 · Cola de Moderación de Catálogo Global
- **User Goal:** Revisar y aprobar solicitudes de publicación comunitaria de series de perfiles sin exponer costos privados de ningún taller.
- **Roles:** SUPERADMIN exclusivamente.
- **Required Information:** Serie de perfiles enviada a revisión comunitaria, resultados de validación de casos de oro G-cases a 0.00 mm.
- **Business & Security Constraints:** Blindaje de costos: el superadministrador jamás tiene acceso a los precios ni proveedores del taller solicitante.
- **Deep-Link Requirement:** `FIXED_BY_CONTRACT` en `/admin/queue`.
- **Current Baseline Surface:** Cola de tareas de moderación con diff dimensional de catálogo.
- **Surface Flexibility:** `FIXED_BY_CONTRACT`.
