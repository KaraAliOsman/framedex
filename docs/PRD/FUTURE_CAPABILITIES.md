# DEKOPEN — REGISTRO ACTIVO DE CAPACIDADES FUTURAS Y ARQUITECTURA EXTENSIBLE (v1.3 MASTER)

> **Estado:** Documento Normativo Activo de Visión y Preparación Arquitectónica
> **Ámbito:** Monorepo Dekopen (Arquitectura Global y Roadmap)
> **Referencia:** CONSTITUTION.md v1.3 (Principios de Capacidad, Neutralidad y Desacoplamiento)

---

## 1. Principios Constitucionales de Evolución del Producto

Dekopen consagra como principios inmutables de alcance y diseño de producto:

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           LEYES DE ALCANCE Y CAPACIDAD                           │
├──────────────────────────────────────────────────────────────────────────────────┤
│  1. OUT OF CURRENT SHOT != OUT OF PRODUCT                                        │
│     (Lo que no se construye en el sprint/shot actual NO está fuera del producto) │
│                                                                                  │
│  2. NOT IMPLEMENTED != REJECTED                                                  │
│     (Lo que aún no está implementado NO ha sido rechazado)                      │
│                                                                                  │
│  3. NOT IN THE CURRENT 24-SHOT ROADMAP != PERMANENTLY PROHIBITED                 │
│     (Lo que no está en los primeros 24 shots NO está prohibido permanentemente)   │
│                                                                                  │
│  4. PERMANENT REJECTION REQUIRES EXPLICIT OWNER SIGN-OFF                         │
│     (Una funcionalidad solo puede declararse PERMANENTEMENTE RECHAZADA mediante  │
│      decisión explícita y formal del OWNER, jamás por falta de tiempo o dogma)   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Regla Arquitectónica de No-Bloqueo:
> **La arquitectura actual (datos, interfaces, motor determinista `/engine` y esquemas de base de datos) NO debe tomar decisiones de diseño que impidan o dificulten innecesariamente la incorporación futura de estas capacidades.**

---

## 2. Inventario de Capacidades Futuras Protegidas (Sin Ataduras Tecnológicas)

### 2.1. Geometría Avanzada y Ensambles Complejos (`ADVANCED_GEOMETRY`)
- **Estado Normativo:** `FUTURE CAPABILITY — UNSCHEDULED`.
- **Descripción:** Soporte para tipologías no ortogonales y ensambles volumétricos de carpintería:
  - **Bow Windows y Bay Windows:** Ensambles poliédricos con perfiles de acople angular regulable (acoples de $90^\circ$, $135^\circ$ o bayoneta variable).
  - **Arcos y Cúpulas:** Perfiles curvados por termoconformado, desarrollo de arco milimétrico y cálculo de radio.
  - **Ángulos Libres y Trapezoides:** Marcos y hojas con ingletes no ortogonales ($<45^\circ$ o $>45^\circ$) para techumbres inclinadas.
  - **Ensambles Compuestos Modulares:** Muros cortina ligeros y acopladores de inercia con refuerzos estructurales.
- **Directriz de Contención:** La arquitectura actual no debe bloquear deliberadamente estas geometrías. **Sin embargo, NO se amplían el alcance de SHOT-07 ni los Casos de Oro (G1–G12) actuales**.

---

### 2.2. Visualización Técnica 3D y Cinemática de Apertura (`3D_VISUALIZATION`)
- **Estado Normativo:** `PLANNED PRODUCT CAPABILITY — RESOLVED IN ROADMAP (SHOT-19)`.
- **Resolución Oficial del Owner:** La visualización 3D pertenece formalmente a **`SHOT-19`**.
- **Alcance Canónico en SHOT-19:**
  1. Enlace Web en Vivo / Público (`/view/[token]`).
  2. Exportador CAD 2D (`.dxf`) según roadmap vigente.
  3. Visualización técnica 3D interactiva del vano.
  4. Cinemática de apertura dinámica (giro practicable, abatimiento basculante/oscilobatiente y traslación corredera).
- **Directriz de No Tech Lock-In:** El visor debe entregar visualización técnica interactiva y cinemática de apertura con materiales fieles al PVC y vidrio, **sin atarse rígidamente a un framework, motor o biblioteca gráfica específica**.
- **Realidad Aumentada (AR):** La Realidad Aumentada completa en campo permanece como `FUTURE CAPABILITY` posterior post-V1, salvo decisión explícita del Owner.

---

### 2.3. Integración Industrial y Salidas de Manufactura (`MANUFACTURING_INTEGRATION`)
- **Estado Normativo:** `FUTURE MANUFACTURING CAPABILITY`.
- **Descripción:** Conexión del plan de corte optimizado con maquinaria automática de planta:
  - **Adaptadores de Máquina Desacoplados:** Interfaces para exportación a sierras automáticas, tronzadoras y centros de mecanizado (CNC) de diversos fabricantes (ej: Elumatec, Emmegi, FOM Industrie, Schüco, Murat, Kaban).
  - **Formatos y Protocolos:** Salida estructurada mediante adaptadores a G-code, XML, CSV o protocolos propietarios según corresponda a cada máquina.
  - **Mecanizados Automáticos:** Coordenadas de perforaciones para desagües, cerraduras cremona y bisagras.
  - **Trazabilidad en Planta:** Etiquetas industriales con código de barras o QR para seguimiento en línea de producción.
- **Directriz de Contención:** El dominio de corte (BFD) entrega datos puros que servirán como input a adaptadores futuros. **NO se agrega protocolo de máquina, ni drivers, ni G-code a SHOT-07**. Se elimina únicamente el veto permanente.

---

### 2.4. Ingesta Multimodal Tolerante (`MULTIMODAL_INTAKE`)
- **Estado Normativo:** `SUPPORTED MULTIMODAL INPUT CLASS WITH CONFIDENCE / HUMAN REVIEW`.
- **Declaración Explícita:** **`HANDWRITTEN INPUT IS NOT PROHIBITED`**.
- **Clases de Entrada:** Planos arquitectónicos en PDF o imagen, cuadros de vanos, fotografías, croquis de terreno, cuadernos de obra y documentos mixtos con anotaciones manuscritas.
- **Semántica de Confianza y Bloqueo:** `Confidence bands and import-blocking semantics inherit the currently active PRD-09 contract.`
- **Gobernanza:** Este catálogo no duplica ni fija umbrales numéricos de confianza; si PRD-09 evoluciona en el futuro, esta capacidad hereda automáticamente las bandas activas sin desincronización. Prohibido alucinar precisión: la revisión humana en pantalla partida garantiza la tolerancia matemática final de `0.00 mm`.

---

### 2.5. Comunicación y Flujos Omnicanal (`OMNICHANNEL_WORKFLOWS`)
- **Estado Normativo:** `FUTURE OMNICHANNEL CAPABILITY`.
- **Descripción:** Integración con canales de mensajería comercial (WhatsApp Business API, correo entrante inteligente) para recepción de solicitudes y distribución de cotizaciones interactivas.

---

## 3. Principio de Neutralidad Tecnológica y de IA (AI-Capability-Neutral)

1. **Especificar QUÉ y no CÓMO:** Los PRDs definen contratos de datos, invariantes geométricas, esquemas JSON y validaciones de seguridad. No congelan prompts efímeros, nombres comerciales de modelos ni cadenas de pensamiento internas.
2. **Sin Dependencia de Proveedor Único:** Prohibido hardcodear dependencias de un único proveedor de IA o tecnología. El sistema utiliza enrutamiento agnóstico.
3. **Evolución sin Ruptura Constitucional:** Los modelos de IA futuros más capaces deben elevar la precisión y velocidad del producto sin requerir reescribir la Constitución ni las especificaciones normativas.
4. **Intención Arquitectónica (`DO NOT UNNECESSARILY PRECLUDE THIS CAPABILITY`):** Este documento preserva la capacidad de evolución del sistema frente a dogmas o restricciones innecesarias. No prescribe cómo debe implementarse cada tecnología (`THIS IS HOW IT MUST BE BUILT`), sino que salvaguarda que las decisiones arquitectónicas presentes no impidan la incorporación fluida de capacidades futuras.
