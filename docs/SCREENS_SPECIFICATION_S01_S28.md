# ESPECIFICACIÓN CANÓNICA DE PANTALLAS (S01 – S28) (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Total Pantallas:** 28 pantallas completas  
**Stack UI:** React 18 + Tailwind CSS + TanStack Query + Zustand

---

## Índice y Mapeo de Rutas de Pantallas (S01 a S28)

| ID | Nombre de Pantalla | Ruta Frontend | Roles con Acceso |
|---|---|---|---|
| **S01** | Inicio de Sesión y Magic Link | `/login` | Público / Todos |
| **S02** | Configuración de Organización (Onboarding) | `/onboarding` | OWNER |
| **S03** | Dashboard Operativo y KPIs de Taller | `/dashboard` | OWNER, ESTIMATOR, WORKSHOP_MANAGER |
| **S04** | Listado de Proyectos y Cotizaciones | `/projects` | OWNER, ESTIMATOR, WORKSHOP_MANAGER |
| **S05** | Detalle de Proyecto y Grilla de Vanos | `/projects/:id` | OWNER, ESTIMATOR, WORKSHOP_MANAGER |
| **S06** | Editor 2D / Canvas SVG Paramétrico | `/projects/:id/positions/:posId/edit` | OWNER, ESTIMATOR |
| **S07** | Inspector Técnico y Corrección en 1 Clic | Modal en `/positions/:id/edit` | OWNER, ESTIMATOR |
| **S08** | Explosión BOM y Despiece Milimétrico | `/projects/:id/bom` | OWNER, ESTIMATOR, WORKSHOP_MANAGER |
| **S09** | Gestión de Listas de Costo y Precios | `/pricing/cost-lists` | OWNER |
| **S10** | Vista Previa y Congelación de Cotización PDF | `/projects/:id/quote-preview` | OWNER, ESTIMATOR |
| **S11** | Orden de Trabajo de Taller (OT) | `/orders/ot/:id` | OWNER, WORKSHOP_MANAGER |
| **S12** | Visor 3D Esquemático de Ventana | `/viewer-3d/:posId` | Todos / Enlace Público |
| **S13** | Catálogo de Perfiles, Series y Kits de Herrajes | `/catalogs/systems` | OWNER, WORKSHOP_MANAGER |
| **S14** | Compilador de Catálogos Asistido por IA | `/catalogs/compiler` | OWNER |
| **S15** | Matriz Junquillo–Vidrio | `/catalogs/systems/:id/glazing` | OWNER, WORKSHOP_MANAGER |
| **S16** | Inventario y Registro de Retazos QR | `/inventory/offcuts` | WORKSHOP_MANAGER |
| **S17** | Panel de Certificado de Fabricabilidad | `/quality/certificates/:id` | OWNER, ESTIMATOR |
| **S18** | Bandeja de Entrada Omnicanal (Email/WA) | `/inbox` | OWNER, ESTIMATOR |
| **S19** | Optimizador y Mapa de Corte 1D / Compras | `/orders/ot/:id/cutting-plan` | WORKSHOP_MANAGER |
| **S20** | Billetera y Consumo de Créditos IA | `/settings/wallet` | OWNER |
| **S21** | Consola de Comandos NLP y Diff Preview | Drawer flotante en S06 | OWNER, ESTIMATOR |
| **S22** | Personalizador de Plantillas PDF | `/settings/templates` | OWNER |
| **S23** | Gestión de Usuarios y Roles de Taller | `/settings/team` | OWNER |
| **S24** | Suscripción y Facturación (Starter / Profesional / Business / Business 2x) | `/settings/billing` | OWNER |
| **S25** | Configuración General y Políticas RLS | `/settings/general` | OWNER |
| **S26** | Portal Público de Firma de Cotizaciones / Vista Instalador | `/p/quote/:uuid` | Cliente Final / INSTALLER |
| **S27** | Intérprete Multimodal de Planos OCR | `/ai/extract-positions` | OWNER, ESTIMATOR |
| **S28** | Cola de Moderación de Catálogo Global | `/admin/queue` | SUPERADMIN |
