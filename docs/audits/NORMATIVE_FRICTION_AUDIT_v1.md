# DEKOPEN — INFORME DE AUDITORÍA DE FRICCIÓN NORMATIVA Y REFORMA DE CAPACIDAD (v1.0)

> **Tipo de Documento:** Auditoría de Arquitectura Normativa, PRD y Gobernanza Técnica  
> **Fecha:** Septiembre 2026  
> **Estado:** Oficial / Propuesta para Aprobación del Owner  
> **Rama de Preparación:** `normative-capability-cleanup` (base: commit canónico `3900549`)  
> **Ámbito:** Totalidad documental de `/docs`, `/docs/PRD`, `/docs/archive`, `/docs/plans`, `AGENTS.md` y `README.md`  
> **Rol Emisor:** Arquitecto Normativo / PRD / Teoría de Dekopen  

---

## 1. Resumen Ejecutivo

Dekopen se fundó bajo una premisa innegociable: **tolerancia matemática de `0.00 mm` en carpintería de PVC/aluminio y cero alucinaciones técnicas en cotizaciones y órdenes de trabajo**. Para proteger esta promesa frente a las primeras olas de LLMs no deterministas, el proyecto adoptó una disciplina constitucional extrema (23 Reglas Supremas, Gauntlet determinista y rechazo por defecto).

Sin embargo, a lo largo de las iteraciones documentales (de v1.0 a v1.2), una serie de **restricciones accidentales, temporales o reactivas** se infiltraron en la documentación con lenguaje absolutista (`CANÓNICO`, `INMUTABLE`, `PROHIBIDO`, `LISTA CERRADA`, `EXACTAMENTE 28 PANTALLAS`). Al congelar decisiones accidentales de implementación como si fueran leyes físicas, se crearon barreras artificiales que amenazan con:
1. Limitar la evolución de la UX hacia flujos más ágiles en taller (pantallas unificadas, split views, drawers contextuales).
2. Prohibir permanentemente capacidades clave de negocio (3D volumétrico, cinemática de apertura, integración con maquinaria CNC/sierras, geometrías no ortogonales como bow windows o arcos, e ingesta de apuntes manuscritos de obra).
3. Degradar la capacidad resolutiva de agentes avanzados de IA (como Gemini 1.5/2.0/3.0, Claude 3.5/3.7, GPT-4o/o1/o3/5) forzándolos a detenerse ante cualquier detalle cosmético o exigir autorización humana para dependencias menores de desarrollo.
4. Generar confusión y bifurcación de la verdad debido a documentos archivados que se autoproclaman canónicos (`DESCARTES-NO-ALCANCE.md`), copias duplicadas desfasadas en la raíz de `/docs/` y múltiples Biblias concatenadas.

### El Principio Rector de la Reforma:
> **MÁXIMA CAPACIDAD + MÁXIMO RIGOR**  
> **Libertad en CÓMO** (tecnología, layout, ergonomía de componentes, tooling moderno, adaptadores de integración y razonamiento de IA).  
> **Rigor en QUÉ DEBE SER VERDAD** (0.00 mm de tolerancia, motor determinista puro, Decimal para mm y dinero, RLS multi-tenant inviolable, auditoría previa inmutable de precios e IA, idempotencia en cobros y Golden Cases verificados por Gauntlet).

---

## 2. Inventario Exhaustivo de Fuentes Auditadas

Se realizó una revisión integral sobre todos los archivos normativos, especificaciones y registros históricos del monorepo `KaraAliOsman/framedex`:

| Documento Auditado | Ubicación en Repo | Naturaleza / Rol Declarado | Estado Normativo Detectado |
|---|---|---|---|
| **Protocolo de Agentes** | `/AGENTS.md` | Protocolo de Loop Engineering 2026 | Activo / Primario para agentes |
| **README Maestro** | `/README.md` | Guía de inicio y mapa de arquitectura | Activo / Informativo y contractual |
| **Constitución del Builder (Raíz)** | `/docs/CONSTITUTION.md` | 23 Reglas Supremas (v1.2 MASTER) | Activo / Norma Suprema (contiene Regla 0) |
| **Constitución en Subdirectorio** | `/docs/PRD/CONSTITUTION.md` | Constitución (v1.2) | Desfasado (carece de Regla 0) |
| **Plan de Ejecución de Shots (Raíz)** | `/docs/PLAN_DE_EJECUCION_SHOTS.md` | Roadmap de Shots (v1.1.2) | Desfasado respecto a v1.2 |
| **Plan Maestro de Shots (PRD)** | `/docs/PRD/PLAN_SHOTS.md` | Secuencia de 24 Shots (v1.2 MASTER) | Activo / Primario para el Roadmap V1 |
| **Playbook de Sesión** | `/docs/PLAYBOOK_SHOTS.md` | Guía operativa paso a paso | Activo / Procedimental |
| **Especificaciones PRD (Subdirectorio)** | `/docs/PRD/PRD-00.md` a `PRD-19.md` | Módulos funcionales 00 al 19 (v1.2) | Activo / Especificaciones Canónicas de Dominio |
| **PRD de Diseño Dual Adobe** | `/docs/PRD/PRD-DESIGN-SYSTEM-ADOBE.md` | Sistema de Diseño Studio Light / Dark Graphite | Activo / Normativa de Tokens y Accesibilidad |
| **PRD Frontend APIs & Components** | `/docs/PRD/PRD-FRONTEND-APIS-COMPONENTS.md` | Contratos de frontend y esquemas | Activo / Técnico |
| **PRD Animaciones & Interacciones** | `/docs/PRD/PRD-ANIMATIONS-INTERACTIONS.md` | Microinteracciones y feedback de taller | Activo / Técnico |
| **PRD Web Mobile Essential** | `/docs/PRD/PRD-WEB-MOBILE-ESSENTIAL.md` | Especificación PWA móvil, OCR y QR | Activo / Técnico |
| **Especificación de Pantallas (PRD)** | `/docs/PRD/SCREENS_SPECIFICATION_S01_S28.md` | Catálogo de Pantallas S01 a S28 (v1.1.2) | Activo / Rígido (requiere refactorización) |
| **Stack de Servicios** | `/docs/PRD/STACK_APLICACIONES_Y_SERVICIOS.md` | Inventario de servicios y herramientas | Activo / Técnico |
| **Archivos Duplicados en Raíz** | `/docs/PRD-00.md` a `PRD-19.md` | Copias residuales de versiones anteriores | Obsoleto / Riesgo de bifurcación de verdad |
| **Especificación de Pantallas (Raíz)** | `/docs/SCREENS_SPECIFICATION_S01_S28.md` | Copia desfasada de pantallas | Obsoleto / Riesgo de lectura errónea |
| **Biblias Concatenadas Master** | `docs/DEKOPEN_BIBLIA_COMPLETA_v1.2_MASTER.md` | Snapshot concatenado v1.2 | Snapshot de lectura / No autoridad independiente |
| **Biblias Anteriores** | `docs/DEKOPEN_BIBLIA_COMPLETA_v1.1_MASTER.md`, `EJECUCION_v1.1.md` | Compilaciones v1.1 | Obsoleto / Histórico |
| **Registro de Descartes** | `/docs/archive/DESCARTES-NO-ALCANCE.md` | Registro de descartes autodeclarado canónico | Falso canónico en archivo / Cero autoridad |
| **Planes de Shots Cerrados** | `/docs/plans/PLAN_SHOT-01.md` a `06.md` | Evidencia de cierre y contratos SHOT-01..06 | Histórico contractual inmutable de shots cerrados |
| **Gauntlet & Verification Scripts** | `/scripts/check_dod.py` | Juez determinista automatizado | Activo / Verificador mecánico DoD |

---

## 3. Análisis Cuantitativo y Cualitativo de Términos Restrictivos

Se ejecutó un escaneo sistemático en los archivos de `/docs` contabilizando la frecuencia de términos imperativos:

```text
CONGELADO:        188 apariciones en 60 archivos
BLOQUEADO:        143 apariciones en 58 archivos
SOLO:             107 apariciones en 32 archivos
PROHIBIDO:         89 apariciones en 28 archivos
NUNCA:             86 apariciones en 22 archivos
EXCLUSIVAMENTE:    82 apariciones en 28 archivos
CANÓNICO:          67 apariciones en 22 archivos
FASE 2:            61 apariciones en 20 archivos
EXACTAMENTE:       51 apariciones en 17 archivos
INMUTABLE:         31 apariciones en 15 archivos
LISTA CERRADA:     15 apariciones en 9 archivos
FUERA DE ALCANCE:   9 apariciones en 4 archivos
INAPELABLE:         7 apariciones en 6 archivos
TOTAL PANTALLAS:    6 apariciones en 6 archivos
NO IMPLEMENTAR:     5 apariciones en 3 archivos
24 SHOTS:           4 apariciones en 4 archivos
POSTERGADO:         1 apariciones en 1 archivo
```

### Diagnóstico Cualitativo:
- **Sobrecarga de "Inmutabilidad":** La palabra `INMUTABLE` o `BLOQUEADO` se aplicó indiscriminadamente a encabezados de documentos completos (incluso borradores preliminares), lo que impedía corregir errores tipográficos, ajustar rutas o refactorizar código sin invocar violaciones ficticias de la Constitución.
- **Uso de "Prohibido" para decisiones de fase:** Se utilizó `PROHIBIDO` para indicar que una funcionalidad no pertenece al shot actual (ej: "Prohibido 3D en V1", "Prohibido CNC en 18 meses"), confundiendo *secuencia de entrega* con *veto arquitectónico permanente*.
- **"Canónico" e "Inapelable" en Artefactos de Diseño:** `PRD-00` calificó a `PRD-DESIGN-SYSTEM-ADOBE.md` como "canónico e inapelable" no solo para tokens de color y contraste, sino insinuando que el layout CAD de escritorio no puede adaptarse a tablets, pantallas táctiles o flujos simplificados de taller.

---

## 4. Sistema Taxonómico de Clasificación de Restricciones (A–F)

Cada restricción identificada en el repositorio se clasifica obligatoriamente en uno de seis niveles:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             TAXONOMÍA DE RESTRICCIONES DEKOPEN                                   │
└──────────────────────────────────┬───────────────────────────────────────────────────────────────┘
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
[ A. Guardrails de Seguridad ] [ B. Autoridad de Dominio ] [ C. Alcance del Shot Actual ]
  • Tolerancia 0.00 mm           • Pérdida de fusión soldadura • "No hacer 3D en SHOT-07"
  • Decimal en mm y dinero       • Capacidad de carga herraje  • Válido como foco de sprint
  • Aislamiento RLS multi-tenant • Fichas certificadas PVC     • NUNCA limita el producto
  • Auditoría previa obligatoria • Fórmulas físicas aprobadas  • OUT OF SHOT != OUT OF PRODUCT
      │                            │                            │
      └────────────────────────────┼────────────────────────────┘
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
[ D. Defaults de Arquitectura] [ E. Baselines de UX/Flujo]  [ F. Restricciones Obsoletas/Dañinas ]
  • Monolito modular por defecto • Superficies de capacidad   • Archivo autoproclamado canónico
  • Puede evolucionar con ADR    • Viajes del usuario (S01..) • Veto eterno a 3D, CNC, arcos
  • No microservicios por moda   • Libertad en layout/drawers • 28 pantallas físicas congeladas
  • Tecnologías base aprobadas   • Composición ergonómica     • Parálisis por gaps no materiales
```

### Definición Operativa:
- **A — SAFETY / CORRECTNESS GUARDRAIL:** Inviolable. Si se debilita, el sistema colapsa matemáticamente o compromete la seguridad y datos de los clientes. Cero tolerancia a cambios.
- **B — DOMAIN AUTHORITY:** Gobierna las realidades físicas, químicas y normativas de la carpintería de PVC/aluminio. Modificable únicamente cuando cambie la ficha técnica de un fabricante o una norma chilena/latinoamericana (ej. NCh).
- **C — CURRENT SHOT SCOPE:** Protege el enfoque del shot en ejecución. Limita *lo que se construye hoy*, pero **jamás** veta lo que Dekopen soportará en el futuro. Principio: `OUT OF CURRENT SHOT != OUT OF PRODUCT`.
- **D — IMPLEMENTATION DEFAULT:** Establece la preferencia de ingeniería sensata (ej: monolito modular, librerías estándar). No es dogma constitucional; puede evolucionar mediante un Architecture Decision Record (ADR) fundado.
- **E — UX BASELINE:** Define los contratos funcionales, permisos y flujos de usuario que la aplicación debe satisfacer. No congela el número de pantallas físicas, la anatomía exacta de un modal ni las pestañas visuales.
- **F — OBSOLETE / HARMFUL CONSTRAINT:** Restricción artificial, dogma accidental o herencia histórica que frena la innovación, la automatización y la inteligencia de agentes. **Debe eliminarse o reescribirse de inmediato**.

---

## 5. Matriz de Scoring Exhaustivo de Reglas

Evaluación de cada una de las 23 Reglas Constitucionales y restricciones clave de PRDs:

| Regla / Restricción | Fuente | Beneficio Principal | Costo / Fricción para el Agente | Riesgo si se Elimina | Clasificación | Acción Recomendada |
|---|---|---|---|---|:---:|:---:|
| **Regla 0: Cero Contradicciones** | `CONSTITUTION.md` §0 | Evita asunciones silenciosas en temas críticos | Parálisis total ante diferencias cosméticas o tipográficas | Alucinación o desvíos silenciosos | **A / F** | **NARROW** (Distinguir Material vs No-Material) |
| **Regla 1: Números del Engine** | `CONSTITUTION.md` §1 | Elimina alucinaciones en cotizaciones y cortes | Exige llamar al motor determinista para todo número | Errores de corte en taller de \$10,000+ USD | **A** | **KEEP** (Inviolable) |
| **Regla 2: Engine Puro** | `CONSTITUTION.md` §2 | Testeabilidad instantánea sin DB/HTTP (`<1s`) | Prohíbe acceder a ORM o APIs dentro de `/engine` | Acoplamiento sucio y tests lentos | **A** | **KEEP** (Inviolable) |
| **Regla 3: Decimal Obligatorio** | `CONSTITUTION.md` §3 | Cero errores de redondeo IEEE-754 en mm y dinero | Verificación rigurosa de tipos en Python/SQL | Ventanas descuadradas por 0.1 mm; dinero perdido | **A** | **KEEP** (Inviolable) |
| **Regla 4: RLS y org_id** | `CONSTITUTION.md` §4 | Aislamiento multi-tenant total en DB | Requiere tests de aislamiento en cada tabla | Filtración de costos y clientes entre talleres | **A** | **KEEP** (Inviolable) |
| **Regla 5: Auditoría IA Previa** | `CONSTITUTION.md` §5 | Trazabilidad completa de acciones de LLM | Exige inserción en `ai_audit_logs` antes de aplicar diffs | Acciones irreversibles opacas no auditables | **A** | **KEEP** (Inviolable) |
| **Regla 6: Fichas en DB (Cero Hardcode)** | `CONSTITUTION.md` §6 | Flexibilidad de sistemas de perfiles sin rebuild | Requiere sembrar catálogos en base de datos | UI mintiendo sobre parámetros físicos reales | **B** | **KEEP** (Inviolable) |
| **Regla 7: Casos de Oro (0.00 mm)** | `CONSTITUTION.md` §7 | Garantía matemática de no-regresión | Tests estrictos que fallan ante desvío de 0.01 mm | Pérdida del valor nuclear de Dekopen | **A** | **KEEP** (Inviolable) |
| **Regla 8: Cambio de Fórmula = PR + Oro** | `CONSTITUTION.md` §8 | Disciplina de ingeniería en cambios de lógica | Prohíbe "arreglar fórmulas ajustando prompts" | Regresiones ocultas en cálculos industriales | **A** | **KEEP** (Inviolable) |
| **Regla 9: Monolito vs Microservicios** | `CONSTITUTION.md` §9 | Simplicidad operativa y despliegue rápido | Prohibición absoluta dogmática de por vida | Sobreingeniería temprana y microservicios por moda | **D** | **DEMOTE_TO_DEFAULT** (Default monolito; microservicio requiere ADR) |
| **Regla 10: Errores Humanos de Taller** | `CONSTITUTION.md` §10 | Operarios de taller entienden los problemas | Requiere mapear excepciones técnicas a lenguaje taller | Operarios bloqueados por stacktraces de Python | **E** | **KEEP** (Inviolable) |
| **Regla 11: Clic Humano Explícito** | `CONSTITUTION.md` §11 | Evita envíos/compras automáticas erróneas | Exige modelar estados intermedios y confirmaciones | Órdenes de compra no deseadas a proveedores | **A** | **KEEP** (Inviolable) |
| **Regla 12: project_versions Congelado** | `CONSTITUTION.md` §12 | Presupuestos emitidos son inmutables legalmente | Requiere crear nueva revisión si cambian precios | Disputas legales con clientes por precios cambiantes | **A** | **KEEP** (Inviolable) |
| **Regla 13: Idempotencia de Pagos** | `CONSTITUTION.md` §13 | Cero cobros dobles en retries de webhooks | Exige UNIQUE por provider+event_id en DB | Cobros duplicados y contracargos bancarios | **A** | **KEEP** (Inviolable) |
| **Regla 14: Código en Inglés, UI ES-CL** | `CONSTITUTION.md` §14 | Estándar global de código + localización correcta | Exige claves i18n para textos de usuario | Spanglish caótico en base de datos y UI | **D** | **KEEP** (Inviolable) |
| **Regla 15: Dependencias Cerradas** | `CONSTITUTION.md` §15 | Previene bloatware, vulnerabilidades y licencias GPL | Bloquea dependencias menores de testing o tooling | Descontrol de dependencias y riesgos de seguridad | **D / F** | **NARROW** (Baseline aprobado + política de bajo riesgo sin founder) |
| **Regla 16: Storage Seguro (URLs Firmadas)**| `CONSTITUTION.md` §16 | Planos y PDFs confidenciales protegidos | Requiere generar tokens temporales de acceso | Archivos y planos de clientes expuestos públicamente | **A** | **KEEP** (Inviolable) |
| **Regla 17: U_w / R_w Certificados** | `CONSTITUTION.md` §17 | Cumplimiento estricto de norma térmica/acústica | Prohíbe estimaciones inventadas por LLM | Demandas por incumplimiento de aislamiento térmico | **B** | **KEEP** (Inviolable) |
| **Regla 18: offcut_inventory Controlado** | `CONSTITUTION.md` §18 | Evita complejidad de optimización de retazos prematura | Mantiene la tabla dormida hasta su shot formal | Foco disperso en algoritmos de retazos antes de BFD | **C** | **KEEP** (Ámbito de Shot respetado) |
| **Regla 19: Cierre con Gauntlet (DoD)** | `CONSTITUTION.md` §19 | Detiene código roto antes de llegar a main | Exige suites 100% verdes sin warnings | Deuda técnica masiva y regresiones silentes | **A** | **KEEP** (Inviolable) |
| **Regla 20: Spec Gap = DETENTE** | `CONSTITUTION.md` §20 | Evita que la IA invente lógica de negocio | Detiene al agente ante decisiones triviales de UI | Alucinación de reglas comerciales | **A / F** | **NARROW** (Gaps materiales vs autonomía de implementación) |
| **Regla 21: Auditoría de Precios** | `CONSTITUTION.md` §21 | Trazabilidad histórica de listas de precios | Exige registrar en `price_audit_logs` previo a mutar | Pérdida de control sobre quién alteró márgenes | **A** | **KEEP** (Inviolable) |
| **Regla 22: Golden Snapshots Automatizados**| `CONSTITUTION.md` §22 | Cero edición manual propensa a error en fixtures | Exige correr `make goldgen` para regenerar snapshots | Fixtures desincronizados del motor real | **A** | **KEEP** (Inviolable) |
| **Veto Canónico en Archivo** | `DESCARTES-NO-ALCANCE.md` | Ninguno (nació como nota histórica temporal) | Pretende prohibir permanentemente 3D, CNC, arcos | Falsa creencia de que Dekopen jamás crecerá | **F** | **SUPERSEDE / MOVE_TO_ARCHIVE** |
| **Total Pantallas: Exactamente 28** | `SCREENS_SPECIFICATION_S01_S28.md` | Catálogo de capacidades inicial | Impide unir pantallas en workspaces ágiles o dividir | Diseños obsoletos y UX rígida de escritorio | **E / F** | **DEMOTE_TO_DEFAULT / REFACTOR** |
| **Design System Inapelable en Layout** | `PRD-00` §2.1 | Consistencia visual inicial | Impide explorar layouts modernos o adaptables | Bloqueo de innovación en experiencia de usuario | **E / F** | **NARROW** (Tokens/Accesibilidad sí; layout flexible) |

---

## 6. Auditoría y Resolución de Contradicciones Concretas

### 6.1. Capacidad 3D y Cinemática de Apertura
- **Conflicto:**
  - `PRD-12` (v1.1.0) especificó un visor procedural 3D con React Three Fiber, materiales PBR y cinemática de apertura (practicable, oscilobatiente, corredera).
  - `docs/PRD/PLAN_SHOTS.md` (v1.2) difirió el visor 3D WebGL a V2, priorizando el visor vectorial 2D y exportador CAD DXF para SHOT-19.
  - `DESCARTES-NO-ALCANCE.md` sentenció que el 3D volumétrico y AR estaban "ESTRICTAMENTE FUERA DE ALCANCE" de forma canónica.
  - `AGENTS.md` (en el diagrama de flujo 360°) incluye "Visor 3D R3F (SHOT-19)".
- **Resolución Normativa:**
  - El 3D volumétrico y la simulación interactiva de apertura son **capacidades oficiales planificadas de Dekopen (`PLANNED PRODUCT CAPABILITY`)**.
  - No están descartadas ni prohibidas. La arquitectura del motor y del frontend debe mantener sus estructuras limpias para soportar extrusión 3D desde el `parametric_tree`.
  - Para la secuencia de ejecución de los 24 shots, el timing específico se documenta formalmente como:
    `[PENDIENTE-DECISIÓN: ROADMAP-3D] (Elección de Founder: entrega en SHOT-19 o pista especializada V2/SHOT-25+)`.

### 6.2. OCR Manuscrito de Cuaderno de Obra
- **Conflicto:**
  - `DESCARTES-NO-ALCANCE.md` declaró que el OCR manuscrito estaba prohibido y fuera de alcance, limitando el OCR a PDFs vectoriales limpios y tablas impresas.
  - `PRD-09.md` (§2) y `PRD-WEB-MOBILE-ESSENTIAL.md` reconocen explícitamente la lectura de textos manuscritos, clasificándolos con confianza **Amarilla (70%–89%)** y exigiendo confirmación humana en interfaz split-screen.
- **Resolución Normativa:**
  - Los apuntes y croquis de obra manuscritos son una realidad cotidiana en los talleres de carpintería de Latinoamérica.
  - El ingreso multimodal de Dekopen reconoce el manuscrito como:
    `SUPPORTED MULTIMODAL INPUT CLASS WITH CONFIDENCE / HUMAN REVIEW`.
  - No se alucinan lecturas con falsa precisión: toda lectura manuscrita ambigua se marca en amarillo o rojo para revisión del cotizador, pero **jamás se rechaza o prohíbe a nivel de arquitectura**.

### 6.3. Catálogo Físico de 28 Pantallas
- **Conflicto:**
  - `SCREENS_SPECIFICATION_S01_S28.md` se autotitula "ESPECIFICACIÓN CANÓNICA" con "Total Pantallas: 28", detallando tablas fijas con rutas individuales.
  - En aplicaciones profesionales de ingeniería, forzar 28 pantallas web completas genera fragmentación (ej: obligar a ir a otra página completa solo para ver una matriz de junquillo o un inspector).
- **Resolución Normativa:**
  - Los códigos `S01` a `S28` se redefinen como **referencias de capacidades y flujos del usuario (Capability & Surface References)**.
  - Se libera el diseño para que los agentes y diseñadores puedan agrupar superficies en paneles acoplables (dockable workspaces), modales contextuales, drawers o tabs, siempre que se satisfagan los requerimientos de permisos, datos y deep-links contractuales.

### 6.4. Autoridad Normativa de la Carpeta Archive
- **Conflicto:**
  - El archivo `docs/archive/DESCARTES-NO-ALCANCE.md` se autotituló "REGISTRO CANÓNICO... Inmutable", ejerciendo autoridad de veto sobre shots activos.
- **Resolución Normativa:**
  - Se instituye la regla constitucional: **Todo archivo dentro de `docs/archive/**` es estrictamente `HISTORICAL / NON-NORMATIVE`**.
  - Ningún archivo archivado puede detener un shot, invocar Regla 0, limitar el alcance actual ni prohibir capacidades futuras.

### 6.5. Gestión de Dependencias (Regla 15)
- **Conflicto:**
  - La Regla 15 actual establece: *"Dependencias: SOLO la lista cerrada (PRD-00 §6). Nuevo dep = decisión explícita del owner."*
  - Esto obliga a detener el desarrollo y consultar al fundador para añadir herramientas estándar de testing, plugins de linter, utilidades de conversión de formatos (ej: DXF, geometrías) o paquetes menores con licencia permisiva.
- **Resolución Normativa:**
  - Se evoluciona hacia una **Política de Dependencias Aprobadas y de Bajo Riesgo**.
  - Los ingenieros y agentes pueden incorporar dependencias que cumplan criterios rigurosos de salud, compatibilidad de licencias y cero impacto en rendimiento. La aprobación del Owner se reserva exclusivamente para cambios estructurales mayores (frameworks, base de datos, proveedores de nube).

### 6.6. Monolito Modular vs Microservicios (Regla 9)
- **Conflicto:**
  - La Regla 9 actual establece: *"Monolito modular... Prohibido microservicios."*
  - Aunque previene la sobreingeniería, redactarlo como un veto constitucional eterno bloquea futuras optimizaciones de escala (ej: aislar un motor de optimización de corte computacionalmente intensivo en un worker independiente de Go/Rust o separar un microservicio de renderizado 3D).
- **Resolución Normativa:**
  - Se redefine como **Default Arquitectónico: Monolito Modular**.
  - Se prohíben microservicios reactivos o por moda, pero se permite la segregación justificada mediante un ADR formal cuando existan límites objetivos de escalabilidad o seguridad.

### 6.7. Tratamiento de Gaps de Especificación (Regla 20)
- **Conflicto:**
  - La Regla 20 actual declara: *"Si el spec tiene un hueco: DETENTE y añade [PENDIENTE-DECISIÓN]. No rellenes con supuestos."*
  - Interpretada de forma literal, detiene a agentes ante elecciones menores de implementación interna (nombre de un helper, uso de un Sheet vs Modal, estructura de un hook).
- **Resolución Normativa:**
  - Se delimita con precisión: `[PENDIENTE-DECISIÓN]` es mandatorio para **vacíos de dominio material** (dinero, fórmulas de cálculo, RLS, permisos, flujos irreversibles).
  - Para decisiones de implementación interna, UI, ergonomía y refactorización, el agente tiene plena autonomía para resolver guiado por buenas prácticas, evidencia del repositorio y tests.

### 6.8. Sistema de Diseño Adobe (PRD-DESIGN-SYSTEM-ADOBE)
- **Conflicto:**
  - `PRD-00` llama a `PRD-DESIGN-SYSTEM-ADOBE.md` "documento CANÓNICO e inapelable", sugiriendo que la composición espacial de la pantalla de escritorio CAD de 1920px no puede adaptarse a tablets de taller ni a flujos móviles simplificados.
- **Resolución Normativa:**
  - Se consagra el principio: **`DESIGN SYSTEM = CONSTRAINT SYSTEM, NOT A FIXED MOCKUP`**.
  - Los tokens de color, semántica, contraste WCAG AAA, escalas tipográficas y variables CSS son normativos e inviolables (cero colores hardcodeados fuera de variables). Sin embargo, el layout espacial, la disposición de paneles y los puntos de corte adaptativos pueden evolucionar libremente para maximizar la usabilidad del operario de taller.

---

## 7. Mapa Unificado de Jerarquía de Autoridad Documental

Para erradicar cualquier ambigüedad sobre qué documento prevalece ante una discrepancia, se establece una pirámide de autoridad estricta de seis niveles:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             PIRÁMIDE DE AUTORIDAD NORMATIVA DEKOPEN                              │
└──────────────────────────────────┬───────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │  NIVEL 1: CONSTITUCIÓN DEL BUILDER               │
          │  Archivo: /docs/CONSTITUTION.md                  │
          │  Autoridad: Suprema, Universal, Inapelable       │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │  NIVEL 2: PLAN MAESTRO DE SHOTS (ROADMAP V1)     │
          │  Archivo: /docs/PRD/PLAN_SHOTS.md                │
          │  Autoridad: Secuencia de Ejecución y Gates       │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │  NIVEL 3: ESPECIFICACIONES TÉCNICAS ACTIVAS      │
          │  Ruta: /docs/PRD/*.md                            │
          │  Autoridad: Dominio, Fórmulas, APIs y Contratos  │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │  NIVEL 4: PLANES Y REGISTROS DE SHOTS CERRADOS   │
          │  Ruta: /docs/plans/PLAN_SHOT-XX.md (01 a 06)     │
          │  Autoridad: Resoluciones históricas inmutables   │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │  NIVEL 5: COMPILACIONES Y BIBLIAS SNAPSHOT       │
          │  Archivos: DEKOPEN_BIBLIA_COMPLETA_*.md          │
          │  Autoridad: NO NORMATIVA (Vistas de solo lectura)│
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │  NIVEL 6: ARCHIVO HISTÓRICO Y DESCARTES          │
          │  Ruta: /docs/archive/**                          │
          │  Autoridad: CERO AUTORIDAD ACTIVA (Contexto solo)│
          └──────────────────────────────────────────────────┘
```

### Reglas de Precedencia Operativa:
1. **Supremacía Constitucional:** Ningún PRD, plan de shot, mockup o decisión técnica puede contradecir la Constitución (`/docs/CONSTITUTION.md`).
2. **Autoridad Única de Especificaciones:** La carpeta oficial de PRDs es exclusivamente `/docs/PRD/`. Los archivos desfasados sueltos en la raíz de `/docs/` carecen de autoridad y están subordinados a `/docs/PRD/`.
3. **Biblias Concatenadas son Derivadas:** Las "Biblias Master" concatenadas son snapshots de conveniencia para lectura humana o prompts monolíticos. Si un fragmento de una Biblia contradice a un archivo individual activo en `/docs/PRD/`, **prevalece siempre el archivo activo en `/docs/PRD/`**.
4. **Cero Autoridad en Archivo:** La carpeta `/docs/archive/**` almacena memoria histórica. Ningún agente puede citar un archivo en `archive/` para vetar una funcionalidad, rechazar un shot o frenar el desarrollo.
5. **Resolución de Conflictos Normativos:** Toda contradicción material se resuelve elevando a la fuente de nivel superior inmediatamente superior.

---

## 8. Plan de Resolución de Duplicaciones Normativas

Se identificaron duplicaciones críticas en el repositorio que confunden a los agentes de desarrollo. El siguiente cuadro define la acción inmediata para cada documento:

| Archivo Original / Activo (Canónico) | Duplicado Desfasado o Copia Secundaria | Estado del Duplicado | Acción Normativa Requerida |
|---|---|---|---|
| `/docs/CONSTITUTION.md` (v1.2 MASTER, 23 reglas) | `/docs/PRD/CONSTITUTION.md` | Desfasado (omite Regla 0) | Sincronizar `/docs/PRD/CONSTITUTION.md` con la versión oficial v1.3 |
| `/docs/PRD/PLAN_SHOTS.md` (v1.2 MASTER) | `/docs/PLAN_DE_EJECUCION_SHOTS.md` | Desfasado (v1.1.2 antiguo) | Reemplazar contenido con puntero directo a `PRD/PLAN_SHOTS.md` |
| `/docs/PRD/PRD-00.md` a `PRD-19.md` | `/docs/PRD-00.md` a `PRD-19.md` (en raíz) | Desfasados (v1.1.0/v1.1.2) | Reemplazar con avisos de redirección hacia `docs/PRD/` |
| `/docs/PRD/SCREENS_SPECIFICATION_S01_S28.md` | `/docs/SCREENS_SPECIFICATION_S01_S28.md` | Desfasado (en raíz) | Reemplazar con puntero hacia `docs/PRD/SCREENS_SPECIFICATION_S01_S28.md` |
| `/docs/PRD/PRD-DESIGN-SYSTEM-ADOBE.md` | Fragmentos en `UI_UX_DESIGN_SYSTEM-ARCHIVED.md` | Histórico archivado | Mantener archivado como registro histórico sin autoridad |
| Fuentes activas en `/docs/PRD/` | `docs/DEKOPEN_BIBLIA_COMPLETA_v1.2_MASTER.md` | Snapshot estático | Agregar disclaimer en encabezado declarándolo vista no autoritativa |
| Fuentes activas en `/docs/PRD/` | `docs/DEKOPEN_BIBLIA_COMPLETA_v1.1_MASTER.md` | Snapshot viejo | Mover formalmente a registro histórico no autoritativo |
| Fuentes activas en `/docs/PRD/` | `docs/DEKOPEN_BIBLIA_EJECUCION_v1.1.md` | Snapshot viejo | Mover formalmente a registro histórico no autoritativo |
| `/docs/PRD/FUTURE_CAPABILITIES.md` | `docs/archive/DESCARTES-NO-ALCANCE.md` | Archivo mal titulado | Reformar descartes con disclaimer de no-autoridad y reclasificación |

---

## 9. Análisis de Riesgos y Mitigaciones

| Riesgo Detectado | Probabilidad | Severidad | Mitigación Incorporada en esta Reforma |
|---|:---:|:---:|---|
| **Alucinación de Cálculos:** Que un agente use la mayor libertad de UI para generar números con LLM | Nula | Catastrófica | Regla 1 (`engine/` puro, números deterministas) y Regla 3 (`Decimal`) permanecen 100% blindadas e inmutables. |
| **Bypass de Seguridad Multi-Tenant:** Que se relajen políticas de aislamiento RLS | Nula | Catastrófica | Regla 4 (`org_id` + RLS obligatorios) y tests de pgTAP en CI permanecen inviolables. |
| **Rotura del Flujo de SHOT-07:** Que esta reforma altere el alcance de BFD o el Inspector | Nula | Alta | El alcance funcional de SHOT-07 no se modifica. El trabajo documental se aísla en el worktree `normative-capability-cleanup`. |
| **Lectura de Documentos Viejos:** Que un LLM lea un PRD suelto en la raíz y use una fórmula vieja | Media | Media | Plan de resolución de duplicaciones redirige inequívocamente todo consumo a `/docs/PRD/`. |
| **Sobreingeniería en Dependencias:** Que se añadan paquetes npm/python innecesarios | Baja | Media | Política de dependencias exige justificación técnica, chequeo de licencias y cero duplicación. |

---

## 10. Conclusión y Recomendación de Adopción

La auditoría demuestra de forma concluyente que:
1. Las salvaguardas que hacen invencible a Dekopen (exactitud matemática de `0.00 mm`, `Decimal`, motor determinista, aislamiento RLS y auditoría inmutable) **no requieren rigidez dogmática en aspectos de layout, tooling o visión de producto**.
2. Al eliminar el falso veto del archivo `DESCARTES-NO-ALCANCE.md`, refactorizar el catálogo de pantallas hacia un mapa de capacidades y otorgar criterio a los agentes para resolver contradicciones no materiales, Dekopen gana una **arquitectura flexible, preparada para agentes avanzados de IA y con capacidad de expansión hacia manufactura CNC y 3D**, manteniendo su tolerancia de error exactamente en `0.00 mm`.
