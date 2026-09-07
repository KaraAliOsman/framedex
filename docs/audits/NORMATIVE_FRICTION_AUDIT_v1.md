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
| **Constitución del Builder** | `/docs/CONSTITUTION.md` | 23 Reglas Supremas (v1.3 MASTER) | Activo / Única Norma Suprema Inapelable |
| **Constitución Secundaria (Eliminada)** | `/docs/PRD/CONSTITUTION.md` | Duplicado secundario | ELIMINADO (Mandato Owner: Una Sola Constitución) |
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

Se identificaron duplicaciones críticas en el repositorio que confunden a los agentes de desarrollo. Siguiendo el **mandato de Autoridad Única del Owner**, se ejecutó la unificación:
1. **Una Sola Constitución:** `/docs/CONSTITUTION.md` (v1.3 MASTER) es la única autoridad constitucional. Se eliminó el duplicado secundario `/docs/PRD/CONSTITUTION.md`.
2. **Punteros Limpios:** Los 22 archivos PRD en raíz se convirtieron en punteros normativos hacia `/docs/PRD/`.
3. **Cero Pérdida de Contenido:** Se migraron los esquemas JSON T2/T3 a `PRD-10`, la geometría 3D procedimental y cinemática a `PRD-12`, y la especificación de Catálogo Global S28 a `docs/PRD/PRD-20.md`.

| Archivo Original / Activo (Canónico) | Duplicado Desfasado o Copia Secundaria | Estado del Duplicado | Acción Normativa Ejecutada |
|---|---|---|---|
| `/docs/CONSTITUTION.md` (v1.3 MASTER, 23 reglas) | `/docs/PRD/CONSTITUTION.md` | Duplicado secundario | ELIMINADO por mandato del Owner (Una Sola Constitución) |
| `/docs/PRD/PLAN_SHOTS.md` (v1.3 MASTER) | `/docs/PLAN_DE_EJECUCION_SHOTS.md` | Desfasado (v1.1.2 antiguo) | Reemplazado contenido con puntero directo a `PRD/PLAN_SHOTS.md` |
| `/docs/PRD/PRD-00.md` a `PRD-20.md` | `/docs/PRD-00.md` a `PRD-19.md` (en raíz) | Desfasados / Duplicados | Migrado contenido único (T2/T3 en PRD-10, 3D en PRD-12, Catálogo en PRD-20) y reemplazados con avisos de redirección |
| `/docs/PRD/SCREENS_SPECIFICATION_S01_S28.md` | `/docs/SCREENS_SPECIFICATION_S01_S28.md` | Desfasado (en raíz) | Reemplazado con puntero hacia `docs/PRD/SCREENS_SPECIFICATION_S01_S28.md` |
| `/docs/PRD/PRD-DESIGN-SYSTEM-ADOBE.md` | Fragmentos en `UI_UX_DESIGN_SYSTEM-ARCHIVED.md` | Histórico archivado | Mantenido archivado como registro histórico sin autoridad |
| Fuentes activas en `/docs/PRD/` | `docs/DEKOPEN_BIBLIA_COMPLETA_v1.2_MASTER.md` | Snapshot estático | Agregado disclaimer en encabezado declarándolo vista no autoritativa |
| Fuentes activas en `/docs/PRD/` | `docs/DEKOPEN_BIBLIA_COMPLETA_v1.1_MASTER.md` | Snapshot viejo | Movido formalmente a registro histórico no autoritativo |
| Fuentes activas en `/docs/PRD/` | `docs/DEKOPEN_BIBLIA_EJECUCION_v1.1.md` | Snapshot viejo | Movido formalmente a registro histórico no autoritativo |
| `/docs/PRD/FUTURE_CAPABILITIES.md` | `docs/archive/DESCARTES-NO-ALCANCE.md` | Archivo mal titulado | Reformado descartes con disclaimer de no-autoridad y reclasificación |

### 8.1. Matriz Exhaustiva de Consolidación de los 22 Archivos PRD

| Root file | Canonical candidate | Identical | Unique root content | Unique canonical content | Classification | Action |
|---|---|:---:|---|---|---|---|
| `docs/PRD-00.md` | `docs/PRD/PRD-00.md` | No | Ninguno | Decisiones D1–D30 completas, 3-tier dependencies, precedence rule | Obsolete subset | Convertido a puntero normativo |
| `docs/PRD-01.md` | `docs/PRD/PRD-01.md` | No | Ninguno | Fixture DEMO_60 completo, hardware kits, glass matrix, casos G1–G12 | Obsolete subset | Convertido a puntero normativo |
| `docs/PRD-02.md` | `docs/PRD/PRD-02.md` | No | Ninguno | DDL completo PG16/PG17, RLS `current_user_org_ids()`, tablas audit | Obsolete subset | Convertido a puntero normativo |
| `docs/PRD-03.md` | `docs/PRD/PRD-03.md` | No | Ninguno | Paddle Global (USD MoR), Flow (CLP), ledger idempotente, webhooks HMAC | Obsolete subset | Convertido a puntero normativo |
| `docs/PRD-04.md` | `docs/PRD/PRD-04.md` | No | `width_mm: number` obligatorio en todos los vanos | `width_mm?: number` opcional para vanos hijos, modelo recursivo split | Superseded minor text | Convertido a puntero normativo |
| `docs/PRD-05.md` | `docs/PRD/PRD-05.md` | No | Ninguno | Motor de costos 5 modos extendido, frontera matemática SHOT-06/SHOT-08 | Strict superset in canon | Convertido a puntero normativo |
| `docs/PRD-06.md` | `docs/PRD/PRD-06.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-07.md` | `docs/PRD/PRD-07.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-08.md` | `docs/PRD/PRD-08.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-09.md` | `docs/PRD/PRD-09.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-10.md` | `docs/PRD/PRD-10.md` | No | Esquemas JSON tipados para Tool T2 (`modify_dimensions`) y Tool T3 (`bulk_discount`) | Action-First Command Bar, protocolo Undo sagrado | Active normative unique content (schemas) | **Migrado contenido único a `docs/PRD/PRD-10.md`**; raíz convertido a puntero |
| `docs/PRD-11.md` | `docs/PRD/PRD-11.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-12.md` | `docs/PRD/PRD-12.md` | No | Extrusión 3D procedimental, cinemática de apertura (giro, oscilo, corredera), shaders | Enlace público `/view/`, tokenless bundle, exportador CAD 2D DXF | Active normative unique content (3D & kinematics) | **Consolidado en `docs/PRD/PRD-12.md` (v1.3 MASTER)** para SHOT-19; raíz convertido a puntero |
| `docs/PRD-13.md` | `docs/PRD/PRD-13.md` | No | Contenido histórico de Catálogo Global migrado a `PRD-20` | AI Gateway, white-label routing, credit caps, fallbacks (SHOT-13) | Active normative unique content (displaced module) | **Preservado en `docs/PRD/PRD-20.md`**; SHOT-20 en `PRD-20`; `docs/PRD-13.md` apunta exclusivamente a AI Gateway y `docs/PRD-20.md` a Catálogo Global |
| `docs/PRD-14.md` | `docs/PRD/PRD-14.md` | No | Ninguno | Verificación doble ciego multi-modelo (T8), sello DOC-08, QR | Superseded minor text | Convertido a puntero normativo |
| `docs/PRD-15.md` | `docs/PRD/PRD-15.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-16.md` | `docs/PRD/PRD-16.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-17.md` | `docs/PRD/PRD-17.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-18.md` | `docs/PRD/PRD-18.md` | Yes | Ninguno | Ninguno | Identical duplicate | Convertido a puntero normativo |
| `docs/PRD-19.md` | `docs/PRD/PRD-19.md` | No | Ninguno | NFR maestros v1.2 sellados, SLOs de latencia, retención de auditoría | Superseded minor text | Convertido a puntero normativo |
| `docs/PRD-ANIMATIONS-INTERACTIONS.md` | `docs/PRD/PRD-ANIMATIONS-INTERACTIONS.md` | No | Ninguno | Feedback táctil/auditivo para tablet de taller, microinteracciones framer-motion | Strict superset in canon | Convertido a puntero normativo |
| `docs/PRD-FRONTEND-APIS-COMPONENTS.md` | `docs/PRD/PRD-FRONTEND-APIS-COMPONENTS.md` | No | Ninguno | Firmas de componentes Canvas 2D, contratos SVG split nodes, tipos frontend | Obsolete subset | Convertido a puntero normativo |

### 8.2. Hashes Criptográficos SHA-256 (Before vs After)

Base evaluada: `39005492b8dbd5f7a3b90f76876a0ad6e63f3714` | Rama: `normative-capability-cleanup`

| Archivo en Raíz `/docs/` | SHA-256 Base (`3900549`) | SHA-256 Actual (Puntero Reformado) | SHA-256 Canónico Activo (`docs/PRD/`) |
|---|---|---|---|
| `docs/PRD-00.md` | `f43b8e217cda3bab0380ffccefbc3b1ae6465c7d70a6df48aabffa6df0fae840` | `8c6e48417583f0a783e3312096a7b18d74204db34e7f5a22ad13d1acd15e22a2` | `b00d966009af43b5cf4c87701a1bdc730cb871461c81994e4f65ac76000b1781` |
| `docs/PRD-01.md` | `824d33be065e2bf05b628e915fe3d6e2cc3b9788e0ce9c4795305adc4c6da80c` | `3aec399dc5ee2e2d50095a85c1b85532312b76699057fa52a47207435a3a03b6` | `c26e8e711edd70eebc3a6ac1d1da12166423781ddc5cd69c7125e1525ca072b6` |
| `docs/PRD-02.md` | `bc6d43088dc3511c5160b3cef9d8fd5d31135fc2ac9d9237bd4ddd7fc22c39f6` | `acb521ba0dd7d29dace44567dcbd6957a1a5db136f3b23e6c9dd7327e0584068` | `666f668b0421fc47bea9d8b06378d335d509869a89d5f5350bdb4400e71d2f0b` |
| `docs/PRD-03.md` | `6acd37d2b580af3d0119017c81d08230fb3950f1b3f2e73abd12f50c3fac8fed` | `771aed969b15cba34d7ad19e7def8256dfaecdd8ef4c9598568cda770bc7e6a0` | `962a329d75bcebd37de1cff7ada6eef303b0dcd762ee30aa97871b7830a882cb` |
| `docs/PRD-04.md` | `c6b97f45ed0d7a75543c071b4e0a5b2bb3f0b358a5641c84cd9aa338a4e6ffa2` | `ea3aadd28b871e0f431f3fb8a4a0d45d95cb1643d97c545a12f33b5972a06edd` | `772a62f02ccf352e06fc0e7020a940419b3142cdebd3281155a4b8720af98cbc` |
| `docs/PRD-05.md` | `a499bb79ec0cbd73c67ff94ea4fc780a1e2978efbd30197c2d9394c755dd9fcc` | `6e1dee35ad8a935b1eb85181d1b9d0b64e32a5b7904a299b6968ad345cf31573` | `0b87c8c16299f29d646fdfb6d10e3960e0e39d76031b7169b2cb06213322b378` |
| `docs/PRD-06.md` | `865749db44bc78bf43865a51aeecc8ae0cc71f82f9d48431f4e56c686b72bca9` | `0f84a0d6283d38e9d6302e2a3b606ee28791b897dd1efa79a7b8198c46a3f97c` | `d9fbd6cbe9eccba233cfeb146c0195129f2a8f0df2a0c40c755c0a26b46dcd80` |
| `docs/PRD-07.md` | `c8724d24dd9e8976a354984c05d17a71228888b2dafd1a43730151c5da67b7e2` | `13bc39f78a2acd0c973eac34b39a620b182acd27774700c4e602a86e84b960fd` | `4bad02371886827f83e59504e3750f6fa216f4009cf09110cc7925d872b5f7d2` |
| `docs/PRD-08.md` | `04bfef8209fd31562b3320841ef2e3940569aa2a92f6731b98e21229be127466` | `55f825d336151958590b3431be5141ada3dd92979ba598e9c1b94c0a97c71df0` | `ad9418e7d06f1bee346482f2fa12fcb3eae268e23c5755716a0edfb85bb0aec6` |
| `docs/PRD-09.md` | `287a6fd2bc72e3c2070477f187d1879bc1b1f25293a6512268166078386d987f` | `3ffc7f7ec3d2499ac09c322956e2410a9899a71ec6598b4f048a5079171dfa5b` | `16601e31f80f491bb2d0f8aed756883cf4004cdb444e4b53b2e6311f9fd47266` |
| `docs/PRD-10.md` | `18bf30c05f5faae4d2a0c1882523259c3dfed7593b2ed37df705f27596d6ba62` | `0a8cd22822e2abc49c8da1a36357ca6ae8f59835d28b1c9258eff70e66f03461` | `fd18211ad2e8ed17faea096770effb6f74ff2ba83e7b75641d2a7cb0f1e562f3` |
| `docs/PRD-11.md` | `a9fecc34b9e8e5887341b78d62a4199f54727d7698c3caae8f718716eea5456a` | `5e63c279ebf8e9ad623d51f14ba34e74f18186d49da4ae7704aaa6ac2225c9a3` | `a4025adcf01712c65eb5f5b03cd0e01cd009db02e2e8fb78a6ccf9b771ca9590` |
| `docs/PRD-12.md` | `8c7fcba1e2a2ff75db15bf68d8df5a944ad89a7da9331d34f25476274969d805` | `2d9de462a28139b2672f479b5b7299ebc31fd10339f9b3a94e97e2d580a19b93` | `bbedaf29b77ee18cdac067380a72a9eba92aeb03ab463342428fe6969fb679c5` |
| `docs/PRD-13.md` | `f4258ac98bb2e6206a7d377dc290213945dbe5acdfa43a121c2a74bcde777810` | `63e17c6d47cebd18fa9e7dd0e58be3579d6058a9862b3f03ca6980b0db2510a8` | `b5815dbd1d7ca657312b9962e973081323ed8857597b2a73ee9815f9d266fc9d` |
| `docs/PRD-14.md` | `96dc6b3ad5ea934b3e1dbaee1ef9a65d3641d5800e42525419bad4fa3101b382` | `188ef45ec8ee9d87e31913d01398467e98c4a29f72161d6254a95cb06bb0804d` | `5ca4b19663a74f4a8fd7b08f235ae905956058b361082505dbed37e7e95b1052` |
| `docs/PRD-15.md` | `bf3675c1c53a9a67371506fab6be2c6f630a1911b52f913de28e4dbf5afb5602` | `6e16f6b05f4d41446357e047a9e6524ff8363c4754ddfc90976de5dfda0714e0` | `c9cb69fa3d6112be0acad1ccbea14962ca06a5aec4f902f9cc8c6d47a5900dcb` |
| `docs/PRD-16.md` | `7d4fc9bfb5162b41ccf012717d20745dd01a3ff6d18ff03f48b1e68aa9614eaf` | `4a742d711339b2e3dbeac29033f385df44f8041cc877880008ab8b7d829f16e4` | `f57ba556410ea18763f3f7ff77f8d7742d4f143d932bfc527e0d57028f054f33` |
| `docs/PRD-17.md` | `2dc43ccfa56a1a63c6500ef4b3a2576a6f524a30cea6a43480ef23c7e3e32920` | `eb216e069f502aa9d1d0164db518ecd28952df25cf27127988f60d5a10afc14c` | `8fc2ba1157ef850018ad85ef6f45e153df03ac23196b44329429f46f434255e4` |
| `docs/PRD-18.md` | `920d48bb36e59bcbe888c268a2805dd39e02d478b3be6f5db7e4cf3c471fead1` | `fcbbb3bc0908baaafbe1b8a5c23d9beb2e3d5cb412a8ec51079383b09aeff142` | `eb792794f907836cb82de7dec05771680d33977944a60728d62ff68a91981f4d` |
| `docs/PRD-19.md` | `c15c24f4a37f9a500ba3df8985a3d6e30d6cbe1290cda830b688a01eed73f0ac` | `a146eba5a289c311dbb5540f246804db10cef1f30fcb587250f241b27ec9d101` | `d73c4ab8b6a65332197dc01ed3c217dc12a34a0e881dd38bb1afc6ea7789010a` |
| `docs/PRD-ANIMATIONS-INTERACTIONS.md` | `943fcbc9a4f13bad828fcab9577115142370aad51f30708c21e7ca96f1092f10` | `97571a6832db9b268420103c013b36cf8b2279ebeaf9d51ceed8a785d6b0f670` | `3942350fc7c624eb6840143ce856519646e943bc3b416d0d4b88ce8eccd563fe` |
| `docs/PRD-FRONTEND-APIS-COMPONENTS.md` | `7be7c61ed7c2d6b1028b606ff1ec28f094c9543772f55428ada3c250cca55646` | `bc43c70b82194cd6dbf3c74fb34d1e7ab00beeaa5c029f4995a40606e16df26c` | `e2af7bc4616502accf08e9492d60b0c22bda9d7b7b1d89110bc5c76fbc2cb290` |

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
