# DEKOPEN — PLAN DE RESOLUCIÓN DE DUPLICACIONES NORMATIVAS (v1.0)

> **Estado:** Documento Oficial de Gobernanza Documental  
> **Ámbito:** Repositorio Dekopen (`KaraAliOsman/framedex`)  
> **Objetivo:** Erradicar la bifurcación de fuentes normativas para que agentes y desarrolladores consuman exclusivamente la fuente canónica activa.  

---

## 1. Diagnóstico del Problema de Duplicación

Durante las iteraciones de planificación previas a SHOT-01..SHOT-06, los archivos de especificación PRD se crearon inicialmente en la raíz de `/docs/` (versiones v1.0 / v1.1.0). Posteriormente, se reorganizó la documentación activa dentro del subdirectorio especializado `/docs/PRD/` (versiones v1.2 MASTER), pero los archivos antiguos en `/docs/` permanecieron en el árbol de Git.

### Consecuencias Críticas de Mantener Duplicados:
1. **Alucinación de Versiones por Agentes:** Un LLM que busque `PRD-01.md` puede abrir `docs/PRD-01.md` (antiguo, 13 KB) en lugar de `docs/PRD/PRD-01.md` (canónico, 47 KB), perdiendo las especificaciones de `hardware_kits`, rangos de vanos y enmiendas de SHOT-06.
2. **Contradicciones Fantasma:** En `docs/PRD-13.md`, el módulo se titula "Catálogo Global" (v1.1.2), mientras que en `docs/PRD/PRD-13.md` es "AI Gateway y Enrutamiento" (v1.2).
3. **Discrepancia Constitucional:** La Constitución en `docs/PRD/CONSTITUTION.md` carecía de la Regla 0 (Cero Contradicciones), presente en `docs/CONSTITUTION.md`.

---

## 2. Jerarquía Inequívoca de Autoridad de Fuentes

Se establece la siguiente regla universal de precedencia:

```text
1. /docs/CONSTITUTION.md (v1.3 MASTER)
   └─► Norma Suprema Inapelable.

2. /docs/PRD/PLAN_SHOTS.md (v1.2 MASTER)
   └─► Roadmap y Criterios de Cierre de Shots Oficiales.

3. /docs/PRD/*.md (v1.2/v1.3 MASTER)
   └─► Especificaciones Funcionales Atómicas Canónicas (ÚNICA FUENTE DE VERDAD PARA PRD).

4. /docs/plans/PLAN_SHOT-XX.md
   └─► Registro Inmutable de Decisiones y Contratos de Shots Cerrados (SHOT-01 a SHOT-06).

5. Compilaciones y Biblias Concatenadas (/docs/DEKOPEN_BIBLIA_*.md)
   └─► GENERATED VIEW / SNAPSHOT (NO NORMATIVO).

6. Archivo Histórico (/docs/archive/**)
   └─► HISTORICAL CONTEXT (CERO AUTORIDAD NORMATIVA ACTIVA).
```

---

## 3. Matriz Exhaustiva de Archivos, Duplicados y Acciones

| ID / Componente | Archivo Canónico Activo (Tier 1–3) | Duplicado Desfasado en Raíz `/docs/` | Copia en Biblia Concatenada | Copia Archivada Histórica | Información Única Detectada y Consolidada | Acción Normativa Requerida |
|---|---|---|---|---|---|---|
| **Constitución** | `/docs/CONSTITUTION.md` (v1.3) | `/docs/PRD/CONSTITUTION.md` | Sección 1 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Regla 0 estaba solo en raíz. Se unificaron ambas en v1.3. | **Sincronizar:** Ambas rutas reflejan v1.3 idéntica. |
| **Plan Maestro Shots**| `/docs/PRD/PLAN_SHOTS.md` | `/docs/PLAN_DE_EJECUCION_SHOTS.md` | Sección 25 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | `PLAN_DE_EJECUCION` contenía versión desfasada v1.1.2. | **Puntero:** Archivo en raíz redirige a `PRD/PLAN_SHOTS.md`. |
| **PRD-00 (Arquitectura)**| `/docs/PRD/PRD-00.md` (10.4 KB) | `/docs/PRD-00.md` (6.6 KB) | Sección 2 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | `docs/PRD/` contiene D1–D30 y enmiendas P1–P6. | **Puntero / Reemplazo:** Declarar `docs/PRD/` como única fuente. |
| **PRD-01 (Engine)** | `/docs/PRD/PRD-01.md` (47.4 KB) | `/docs/PRD-01.md` (13.8 KB) | Sección 3 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | `docs/PRD/` contiene especificación de kits y DEMO_60 completa. | **Puntero / Reemplazo:** Raíz desfasada sustituida por puntero. |
| **PRD-02 (DDL / DB)** | `/docs/PRD/PRD-02.md` (30.8 KB) | `/docs/PRD-02.md` (24.8 KB) | Sección 4 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | `docs/PRD/` contiene DDL actualizado para PG16/PG17. | **Puntero / Reemplazo:** Raíz desfasada sustituida por puntero. |
| **PRD-03 (Tenancy/Bill)**| `/docs/PRD/PRD-03.md` (11.5 KB) | `/docs/PRD-03.md` (5.7 KB) | Sección 5 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | `docs/PRD/` incluye especificación completa de Paddle y Flow. | **Puntero / Reemplazo:** Raíz desfasada sustituida por puntero. |
| **PRD-04 (Lienzo 2D)** | `/docs/PRD/PRD-04.md` (6.2 KB) | `/docs/PRD-04.md` (4.5 KB) | Sección 6 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | `docs/PRD/` detalla dimensiones nominales y split nodes. | **Puntero / Reemplazo:** Raíz desfasada sustituida por puntero. |
| **PRD-05 (Costos)** | `/docs/PRD/PRD-05.md` (6.8 KB) | `/docs/PRD-05.md` (6.0 KB) | Sección 7 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | `docs/PRD/` incluye frontera matemática SHOT-06 / SHOT-08. | **Puntero / Reemplazo:** Raíz desfasada sustituida por puntero. |
| **PRD-06 (Salidas DOC)**| `/docs/PRD/PRD-06.md` (6.6 KB) | `/docs/PRD-06.md` (6.6 KB) | Sección 8 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Idénticos en contenido base. | **Puntero / Reemplazo:** Raíz redirige a `docs/PRD/`. |
| **PRD-07 (Inspector)** | `/docs/PRD/PRD-07.md` (2.4 KB) | `/docs/PRD-07.md` (2.4 KB) | Sección 9 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Idénticos en contenido base. | **Puntero / Reemplazo:** Raíz redirige a `docs/PRD/`. |
| **PRD-08 (Compilador)**| `/docs/PRD/PRD-08.md` (2.4 KB) | `/docs/PRD-08.md` (2.4 KB) | Sección 10 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Idénticos en contenido base. | **Puntero / Reemplazo:** Raíz redirige a `docs/PRD/`. |
| **PRD-09 (OCR Multimodal)**| `/docs/PRD/PRD-09.md` (2.1 KB) | `/docs/PRD-09.md` (2.1 KB) | Sección 11 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Idénticos en contenido base. | **Puntero / Reemplazo:** Raíz redirige a `docs/PRD/`. |
| **PRD-10 (Cmd+K Diff)** | `/docs/PRD/PRD-10.md` (3.9 KB) | `/docs/PRD-10.md` (4.3 KB) | Sección 12 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | `docs/PRD/` contiene estándar Action-First v1.2. | **Puntero / Reemplazo:** Raíz desfasada sustituida por puntero. |
| **PRD-11 (Templates)** | `/docs/PRD/PRD-11.md` (4.5 KB) | `/docs/PRD-11.md` (4.5 KB) | Sección 13 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Idénticos en contenido base. | **Puntero / Reemplazo:** Raíz redirige a `docs/PRD/`. |
| **PRD-12 (3D / CAD)** | `/docs/PRD/PRD-12.md` (2.2 KB) | `/docs/PRD-12.md` (3.4 KB) | Sección 14 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Raíz tenía spec R3F 3D v1.1. Se consolidó en `FUTURE_CAPABILITIES`. | **Consolidación:** 3D vive en `FUTURE_CAPABILITIES`; raíz redirige. |
| **PRD-13 (Gateway/Cat)**| `/docs/PRD/PRD-13.md` (4.3 KB) | `/docs/PRD-13.md` (1.4 KB) | Sección 15 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Raíz era Catálogo Global viejo; `docs/PRD/` es AI Gateway v1.2. | **Puntero / Reemplazo:** Raíz desfasada sustituida por puntero. |
| **PRD-14 (Certificado)**| `/docs/PRD/PRD-14.md` (2.7 KB) | `/docs/PRD-14.md` (1.7 KB) | Sección 16 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | `docs/PRD/` contiene especificación de agentes doble ciego v1.2. | **Puntero / Reemplazo:** Raíz desfasada sustituida por puntero. |
| **PRD-15 (Autopilot)** | `/docs/PRD/PRD-15.md` (1.6 KB) | `/docs/PRD-15.md` (1.6 KB) | Sección 17 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Idénticos en contenido base. | **Puntero / Reemplazo:** Raíz redirige a `docs/PRD/`. |
| **PRD-16 (Retazos QR)** | `/docs/PRD/PRD-16.md` (3.0 KB) | `/docs/PRD-16.md` (3.0 KB) | Sección 18 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Idénticos en contenido base. | **Puntero / Reemplazo:** Raíz redirige a `docs/PRD/`. |
| **PRD-17 (Bandeja Inbox)**| `/docs/PRD/PRD-17.md` (3.1 KB) | `/docs/PRD-17.md` (3.1 KB) | Sección 19 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Idénticos en contenido base. | **Puntero / Reemplazo:** Raíz redirige a `docs/PRD/`. |
| **PRD-18 (Founding 50)**| `/docs/PRD/PRD-18.md` (5.2 KB) | `/docs/PRD-18.md` (5.2 KB) | Sección 20 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | Idénticos en contenido base. | **Puntero / Reemplazo:** Raíz redirige a `docs/PRD/`. |
| **PRD-19 (NFR / Sec)** | `/docs/PRD/PRD-19.md` (5.0 KB) | `/docs/PRD-19.md` (4.0 KB) | Sección 21 en Biblia v1.2 | `BIBLIA-v1.1.2-SEALED.md` | `docs/PRD/` contiene NFR maestro v1.2 sellado. | **Puntero / Reemplazo:** Raíz desfasada sustituida por puntero. |
| **Pantallas S01–S28** | `/docs/PRD/SCREENS_SPECIFICATION_S01_S28.md` | `/docs/SCREENS_SPECIFICATION_S01_S28.md` | Sección 24 en Biblia v1.2 | `SCREENS_SPECIFICATION_S01_S26-ARCHIVED.md` | Raíz era v1.1.2 rígida. Sustituida por puntero a Capability Map v1.3. | **Puntero:** Raíz redirige a `PRD/SCREENS_SPECIFICATION_S01_S28.md`. |
| **Frontend APIs** | `/docs/PRD/PRD-FRONTEND-APIS-COMPONENTS.md` | `/docs/PRD-FRONTEND-APIS-COMPONENTS.md` | Sección 23 en Biblia v1.2 | Ninguna | `docs/PRD/` contiene contratos actualizados para SHOT-04/05/06. | **Puntero / Reemplazo:** Raíz redirige a `docs/PRD/`. |
| **Animaciones & UI** | `/docs/PRD/PRD-ANIMATIONS-INTERACTIONS.md` | `/docs/PRD-ANIMATIONS-INTERACTIONS.md` | Sección 24 en Biblia v1.2 | Ninguna | `docs/PRD/` contiene microinteracciones actualizadas. | **Puntero / Reemplazo:** Raíz redirige a `docs/PRD/`. |
| **Capacidades Futuras**| `/docs/PRD/FUTURE_CAPABILITIES.md` | `/docs/FUTURE_CAPABILITIES.md` (puntero) | Ninguna | `DESCARTES-NO-ALCANCE.md` (reformado) | Rescata 3D, CNC, arcos, manuscrito y WhatsApp como capacidades oficiales. | **Activo:** Nuevo pilar normativo de extensibilidad. |

---

## 4. Política de Redirección Limpia de Archivos Sueltos en Raíz

Para evitar que herramientas de búsqueda global o agentes LLM lean los archivos desactualizados en la raíz de `/docs/`, se implementa la siguiente política estandarizada:

Cada archivo `docs/PRD-XX.md` contiene un encabezado unificado de puntero normativo:

```markdown
# [ID]: [NOMBRE DE ESPECIFICACIÓN] (PUNTERO NORMATIVO)

> **Ubicación Canónica Activa:** [`docs/PRD/[ID].md`](./PRD/[ID].md)

Este documento en la raíz de `/docs/` es un puntero normativo de redirección.
La especificación canónica, actualizada y autorizada vive exclusivamente en:

👉 [**docs/PRD/[ID].md**](./PRD/[ID].md)
```

Esto garantiza:
1. Cero pérdida de historial en Git.
2. Inmunidad inmediata ante agentes que busquen en `/docs/`.
3. Autoridad centralizada al 100% en [`/docs/PRD/`](file:///c:/Users/alios/Downloads/dekopen/docs/PRD/).
