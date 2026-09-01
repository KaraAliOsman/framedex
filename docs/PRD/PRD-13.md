# PRD-13: AI GATEWAY, ENRUTAMIENTO Y GOBERNANZA DE PROMPTS (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (Enterprise AI Gateway & ReAct Governance Standard)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 2 (Inteligencia Asistida y Automatización)  
**Bloquea a:** PRD-09, PRD-10, PRD-14, PRD-15

---

## 1. Arquitectura del AI Gateway y Gobernanza de Producción

El AI Gateway (`backend/apps/ai_gateway/`) es el único punto de entrada para todas las operaciones de inteligencia artificial en Dekopen. Aplica los principios de **ReAct Governance**, **Pre/Post-Invocation Hooks**, **Token Budgeting** y **Prompt Versioning**.

```
[ Frontend / Canvas S06 ] ──► [ AI Gateway Django Middleware ]
                                      │
     ┌────────────────────────────────┴────────────────────────────────┐
     ▼                                                                 ▼
[ PRE-INVOCATION HOOKS ]                                      [ ENRUTADOR DE MODELOS ]
• Validación de saldo (credit_ledger)                         • Primary NLP Engine (GPT-4o / LLM estándar)
• Sanitización de inyecciones (Indirect Prompt Injection)     • Vision & OCR Engine (Gemini Vision / multimodal)
• Inyección de identidad y RLS (org_id)                       • Dual Auditor Engine (Segundo modelo independiente)
     │                                                                 │
     └────────────────────────────────┬────────────────────────────────┘
                                      │
                                      ▼
                      [ EJECUCIÓN TOOL / LLM CALL ]
                                      │
     ┌────────────────────────────────┴────────────────────────────────┐
     ▼                                                                 ▼
[ POST-INVOCATION HOOKS ]                                     [ AUDITORÍA INMUTABLE ]
• Validación de Schema JSON (Pydantic)                        • Registro en `ai_audit_logs`
• Detección de secretos o datos cruzados                      • Registro en `price_audit_logs`
• Entrega a /engine para cálculo 0.00 mm                      • Habilitación de Sacred Undo (Cmd+Z)
```

---

## 2. Técnicas de Prompting Aplicadas por Herramienta

| Tool ID | Herramienta | Técnica Canónica | Justificación de Arquitectura |
|---|---|---|---|
| **T1** | OCR de Planos (S27) | **Few-Shot Multimodal** | Ejemplos de vanos etiquetados para garantizar el formato JSON sin alucinación de cotas. |
| **T2** | Comandos NLP (Canvas) | **ReAct con Hooks** | Alternancia *Thought $\rightarrow$ Action $\rightarrow$ Observation*. La acción llama a `/engine` para diff numérico. |
| **T3** | Sugerencia de Descuentos | **Chain-of-Thought (CoT)** | Razonamiento paso a paso sobre márgenes antes de sugerir el porcentaje. |
| **T6** | Compilador de Catálogos | **Directional Stimulus** | Guías semánticas dirigidas a matrices de junquillos y holguras de perfiles. |
| **T8** | Certificado Fabricabilidad | **Self-Consistency Doble Ciego** | Auditoría dual independiente cruzando dos proveedores de IA distintos. |

---

## 3. Pre & Post-Invocation Hooks (Gobernanza a Nivel de Ejecución)

1. **Pre-Invocation:**
   - **Bloqueo Transaccional de Saldo:** `SELECT ... FOR UPDATE` sobre `credit_ledger`. Si saldo $\le 0$, cancela la llamada antes de facturar tokens.
   - **Aislamiento Multi-Tenant:** Inyecta automáticamente el `org_id` y valida que el usuario pertenezca a la organización.
2. **Post-Invocation:**
   - **El LLM jamás escribe números finales:** Todo diff paramétrico generado por el LLM se envía obligatoriamente a `/engine` para recálculo determinista a `0.00 mm`.
   - **Trazabilidad Obligatoria:** Escribe en `ai_audit_logs` con `latency_ms`, `tokens_in`, `tokens_out`, `model_name` y hash de payload.

---

## 4. Versionado de Prompts y Rate Limiting

- **Prompt Registry (FQN):** Todos los templates de prompts están versionados en código (`prompts/v1/`, `prompts/v2/`) con identificadores unívocos (ej: `dekopen:prompt:t2_nlp_command:v1.2`). Un rollback de prompt se hace en segundos sin alterar la lógica de negocio.
- **Techo de Tokens por Taller:** Cada organización tiene un límite diario de tokens para prevenir fugas de consumo en llamadas masivas.
