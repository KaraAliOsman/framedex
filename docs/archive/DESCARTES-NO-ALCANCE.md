# REGISTRO HISTÓRICO DE DECISIONES DE ALCANCE INICIAL (NO NORMATIVO — ARCHIVADO)

> **Estado:** `ARCHIVED — NON-NORMATIVE — NO ACTIVE AUTHORITY`  
> **Naturaleza:** Registro Histórico de Delimitación de Alcance de Shots Iniciales  
> **Autoridad Normativa Activa:** CERO. Este archivo es estrictamente referencial y de contexto histórico.  
> **Documentos Activos que Prevalecen:** [`docs/CONSTITUTION.md`](../CONSTITUTION.md) y [`docs/PRD/FUTURE_CAPABILITIES.md`](../PRD/FUTURE_CAPABILITIES.md).  

---

## ⚠️ Declaración Constitucional de Archivo

Este documento se conserva en `docs/archive/` con fines de trazabilidad histórica.
1. **No posee autoridad normativa activa** para bloquear, vetar o limitar la evolución de Dekopen.
2. La regla rectora de producto establece:
   - `OUT OF CURRENT SHOT != OUT OF PRODUCT`
   - `NOT IMPLEMENTED != REJECTED`
   - `NOT IN THE CURRENT 24-SHOT ROADMAP != PERMANENTLY PROHIBITED`
3. Ninguna funcionalidad puede considerarse "permanentemente prohibida" sin una decisión explícita y formal del **OWNER**.

---

## 1. Reclasificación de Capacidades Inicialmente Pospuestas

A continuación se registra la resolución y clasificación arquitectónica oficial de las funcionalidades postergadas durante la planificación temprana:

### 1.1. Bow Windows / Bay Windows / Arcos / Ángulos Libres
- **Clasificación Oficial:** `FUTURE CAPABILITY — UNSCHEDULED` (Capacidad Futura No Programada para V1).
- **Alcance en V1:** En los primeros 24 shots, el motor `/engine` se enfoca en las tipologías ortogonales canónicas: Fijo (`FIXED`), Proyectante (`AWNING`), Oscilobatiente (`TILT_TURN`), Correderas (`SLIDING_2L/3L/4L/MONO`) y Puertas batientes (`DOOR_ENTRY`/`DOOR_DOUBLE`).
- **Preparación Arquitectónica:** El árbol paramétrico (`parametric_tree`) y el motor determinista estructuran sus tipos y dependencias de forma abstracta para permitir futuras tipologías poliédricas y arcos sin romper el modelo de dominio.

### 1.2. Conexión a Maquinaria CNC / Tronzadoras Industriales (G-Code)
- **Clasificación Oficial:** `FUTURE MACHINE-INTEGRATION CAPABILITY` (Capacidad Futura de Integración Industrial).
- **Alcance en V1:** En V1 no se construyen drivers para maquinaria física específica.
- **Preparación Arquitectónica:** El optimizador de corte 1D (BFD) entrega sus resultados a través de interfaces desacopladas:
  `BFD / Cut Plan ──> Machine Adapter Interface ──> Exportador Específico (G-Code / Elumatec / Emmegi / XML)`.

### 1.3. Visor 3D Volumétrico WebGL & Realidad Aumentada (AR)
- **Clasificación Oficial:** `PLANNED PRODUCT CAPABILITY` (Capacidad de Producto Planificada).
- **Especificación de Referencia:** Diseñada en `docs/PRD/PRD-12.md` mediante React Three Fiber (R3F), cinemática de apertura y materiales PBR.
- **Decisión de Roadmap:** `[PENDIENTE-DECISIÓN: ROADMAP-3D]`. El Owner definirá oportunamente si la experiencia 3D se integra en el hito de SHOT-19 o en una pista especializada de extensión (SHOT-25+ / V2). Su estatus como capacidad de producto es oficial y permanente.

### 1.4. Ingesta de Apuntes y Croquis Manuscritos de Obra
- **Clasificación Oficial:** `SUPPORTED MULTIMODAL INPUT CLASS WITH CONFIDENCE / HUMAN REVIEW` (Clase Multimodal Soportada con Niveles de Confianza).
- **Especificación de Referencia:** Conforme a `docs/PRD/PRD-09.md` y `docs/PRD/PRD-WEB-MOBILE-ESSENTIAL.md`.
- **Mecanismo Operativo:** No se rechaza ningún apunte por ser manuscrito. Se clasifica mediante el semáforo de confianza: lecturas dudosas se resaltan en **Amarillo** o **Rojo** para confirmación humana en pantalla split-screen, manteniendo la tolerancia de `0.00 mm`.

### 1.5. Envío y Notificaciones Comerciales por WhatsApp
- **Clasificación Oficial:** `FUTURE OMNICHANNEL CAPABILITY` (Capacidad Futura Omnicanal).
- **Alcance en V1:** V1 genera el PDF comercial oficial (DOC-01) y el enlace seguro `/view/[token]`. La integración directa con WhatsApp Business API para entrega automatizada de presupuestos queda habilitada arquitectónicamente para integración post-V1.

---

## 2. Gobernanza de Modelos y Pasarelas

1. **AI Router Agnóstico:**
   - Desacoplado mediante la tabla `ai_routes` en base de datos.
   - Proveedores estándar: modelos NLP/cálculo, modelos de visión multimodal y arbitraje cruzado doble ciego T8.
2. **Pasarelas de Pago:**
   - **Chile:** Flow.cl (CLP).
   - **Internacional:** **Paddle** como Merchant of Record (USD).
