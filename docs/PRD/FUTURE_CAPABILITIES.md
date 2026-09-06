# DEKOPEN — REGISTRO ACTIVO DE CAPACIDADES FUTURAS Y ARQUITECTURA EXTENSIBLE (v1.0)

> **Estado:** Documento Normativo Activo de Visión y Preparación Arquitectónica  
> **Ámbito:** Monorepo Dekopen (Arquitectura Global)  
> **Referencia:** CONSTITUTION.md v1.3 (Principios de Capacidad y Neutralidad)  

---

## 1. Principios Constitucionales de Evolución del Producto

Dekopen establece como principios inmutables de alcance y diseño de producto:

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
> **La arquitectura actual (datos, interfaces, motor determinista y esquemas de base de datos) NO debe tomar decisiones de diseño que impidan o dificulten innecesariamente la incorporación futura de estas capacidades.**

---

## 2. Inventario de Capacidades Futuras Protegidas

### 2.1. Geometría Avanzada y Ensambles Complejos (`ADVANCED_GEOMETRY`)
- **Descripción:** Soporte para tipologías no ortogonales y arquitecturas volumétricas de carpintería:
  - **Bow Windows y Bay Windows:** Ensambles poliédricos con perfiles de acople angular regulable (ej: acoples de $90^\circ$, $135^\circ$ o bayonet variable $90^\circ - 180^\circ$).
  - **Arcos y Cúpulas:** Perfiles curvados por termoconformado con radio constante o rebajado, cálculo de desarrollo de arco milimétrico y plantillas de curvado.
  - **Ángulos Libres y Trapezoides:** Marcos y hojas con ingletes no ortogonales ($<45^\circ$ o $>45^\circ$) para cerramientos bajo techumbres inclinadas.
  - **Ensambles Compuestos Modulares:** Muros cortina ligeros y uniones continuas con perfiles de inercia y refuerzos estructurales de acero.
- **Directriz Arquitectónica:** El árbol paramétrico (`parametric_tree`) y el motor `/engine` estructuran sus nodos de manera jerárquica y abstracta (geometría de polígonos delimitados por vectores y perfiles de conexión), evitando asumir que toda ventana es un rectángulo ortogonal de cuatro lados de $90^\circ$.

---

### 2.2. Visualización 3D y Cinemática de Apertura (`3D_VISUALIZATION`)
- **Descripción:** Renderizado volumétrico fotorrealista interactivo y simulación física de movimiento:
  - **Generador Procedural R3F / Three.js:** Extrusión 3D a partir del `parametric_tree`, ensamblado procedural de marco, hoja, junquillos, termopanel y manillas.
  - **Cinemática Dinámica:** Simulación física exacta de apertura en tiempo real (giro practicable de $0^\circ$ a $90^\circ$, abatimiento oscilobatiente inferior de $0^\circ$ a $15^\circ$, deslizamiento horizontal de correderas y plegado en fuelle).
  - **Shaders PBR Realistas:** Texturas procedurales de foliados de PVC (Roble Dorado, Nogal, Gris Grafito RAL 7016) y material dieléctrico de vidrio con índice de refracción (`ior: 1.52`) y cámara de aire/gas argón.
  - **Realidad Aumentada (AR):** Inspección de la ventana a escala 1:1 en la pared del cliente final mediante WebXR / QuickLook.
- **Directriz Arquitectónica:** El motor matemático entrega las cotas de eje neutro, coordenadas de solape y planos de referencia sin sesgo 2D. La ruta `/view/[token]` y el visor cliente se diseñan como contratos extensibles.
- **Timing en Roadmap:** Declarada formalmente como `PLANNED PRODUCT CAPABILITY`. El hito de entrega específica se encuentra marcado como:
  `[PENDIENTE-DECISIÓN: ROADMAP-3D]` (El Owner determinará en su momento si se entrega en SHOT-19 o en una pista especializada posterior SHOT-25+ / V2).

---

### 2.3. Integración Industrial y Conexión a Maquinaria (`MANUFACTURING_INTEGRATION`)
- **Descripción:** Generación de archivos de corte e instrucciones para maquinaria automática de taller de PVC/aluminio:
  - **Adaptadores de Tronzadoras y Sierras Automáticas:** Exportación de listas de corte optimizadas a formatos de control industrial de fabricantes globales (ej: Elumatec, Emmegi, FOM Industrie, Schüco, Murat, Kaban).
  - **Generación de Código Máquina / G-Code / XML / CSV:** Salida estructurada de coordenadas de corte, ángulo de disco ($45^\circ / 90^\circ / 135^\circ$), avance de alimentación y compensación de ancho de corte (*kerf*).
  - **Centros de Mecanizado (CNC):** Perforaciones automatizadas de desagües, cerraduras cremona, salidas de descompresión y encajes de bisagras según la tipología y herraje resuelto en `/engine`.
  - **Trazabilidad en Planta por Código de Barras / QR:** Etiquetas industriales resistentes al taller pegadas al perfil inmediatamente tras el corte para guiar el ensamblado, soldado y acristalamiento.
- **Directriz Arquitectónica:** El módulo de optimización de corte 1D (BFD) separa rígidamente la lógica de optimización pura del formato de salida:
  `[Corte Optimizado / CutPlan] ──> [Machine Adapter Interface] ──> [Driver Específico (Elumatec/FOM/GCode)]`.

---

### 2.4. Ingesta Multimodal Tolerante y Asistida (`MULTIMODAL_INTAKE`)
- **Descripción:** Captura de información de vanos desde múltiples fuentes heterogéneas de obra y arquitectura:
  - **Planos Arquitectónicos Impresos y Digitales:** Extracción mediante visión artificial de cuadros de vanos, acotaciones y especificaciones técnicas desde archivos PDF o imágenes en alta resolución.
  - **Cuadernos de Obra y Croquis Manuscritos:** Reconocimiento de cotas y notas manuscritas tomadas en terreno por instaladores y maestros de taller.
  - **Fotografías de Fachadas y Vanos Existentes:** Detección de aperturas preexistentes con rectificación de perspectiva y referencia métrica conocida.
- **Directriz de Calidad y Confianza:**
  - Se prohíbe el rechazo dogmático de fuentes manuscritas o de baja resolución.
  - Se adopta el modelo de **Semáforo de Certeza y Validación Humana**:
    - **Verde ($\ge 90\%$ de certeza):** Texto tipográfico nítido y coherencia geométrica confirmada $\rightarrow$ Precarga sugerida.
    - **Amarillo ($70\% - 89\%$ de certeza):** Manuscrito legible, tipografía con artefactos o inferencia por escala $\rightarrow$ Celda destacada en amarillo que requiere tab/clic humano de validación en pantalla split-screen.
    - **Rojo ($<70\%$ de certeza):** Ambigüedad severa $\rightarrow$ Celda vacía que exige ingreso manual explícito por el cotizador.

---

### 2.5. Comunicación y Operación Omnicanal (`OMNICHANNEL_WORKFLOWS`)
- **Descripción:** Conexión fluida con los canales comerciales reales que utilizan los talleres y sus clientes:
  - **WhatsApp Business API:** Envío automatizado de enlaces seguros de cotización (`/view/[token]`), notificaciones de cambio de estado ("Tu ventana entró a fabricación") y recepción de fotos/solicitudes de cotización directo a la bandeja de entrada.
  - **Bandeja de Correo Inteligente (Inbound Request):** Procesamiento de emails con adjuntos que ingresan automáticamente como borradores de cotización pendientes de revisión.
- **Directriz Arquitectónica:** Los canales de comunicación son capas de transporte desacopladas que interactúan exclusivamente con la API REST mediante webhooks firmados y tareas en segundo plano.

---

## 3. Principio de Neutralidad de Capacidades de IA (AI-Capability-Neutral)

Para que Dekopen aproveche continuamente la rápida evolución de los modelos fundacionales de inteligencia artificial (LLMs, razonamiento visual y multimodal), las especificaciones de PRD se rigen bajo el siguiente estándar:

1. **Especificar QUÉ y no CÓMO:** Los PRDs definen:
   - Esquemas de datos de entrada y salida (JSON Schemas / Pydantic models).
   - Invariantes de negocio y restricciones de validación.
   - Guardrails de seguridad y auditoría en base de datos.
   - Límites de autoridad (qué puede proponer la IA y qué exige confirmación humana).
2. **Desacoplamiento de Modelos y Proveedores:**
   - Prohibido acoplar el código o la arquitectura a nombres comerciales efímeros. La tabla `ai_routes` y el router agnóstico desacoplan las llamadas a modelos.
   - Las mejoras en la capacidad de razonamiento de los modelos futuros deben elevar la precisión y velocidad del producto sin exigir reescrituras de la Constitución ni de las especificaciones funcionales.
3. **Estrategia ante Limitaciones Temporales:**
   - Si una tecnología o modelo actual tiene limitaciones de precisión (ej: OCR manuscrito complejo o geometría tridimensional en dispositivos de baja gama), la solución **NUNCA** es prohibir la funcionalidad.
   - La solución es implementar **confidence scoring, interfaces de validación split-screen y fallbacks elegantes**, permitiendo que cuando los modelos maduren, el flujo se vuelva automáticamente más autónomo.

---

## 4. Extensibilidad Post-24 Shots

El Plan Maestro de 24 Shots (`docs/PRD/PLAN_SHOTS.md`) define el **Roadmap de Ejecución Inicial Canónico (V1)**.
- **No es el límite final del producto Dekopen.**
- Una vez concluidos los 24 shots, el desarrollo continuará mediante **Shots de Extensión (`SHOT-25+`)**, tracks de integración especializada de maquinaria, geometrías complejas y nuevas superficies operativas según las prioridades estratégicas del Owner.
