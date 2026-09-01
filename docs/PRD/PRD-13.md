# PRD-13: AI GATEWAY, ENRUTAMIENTO Y GOBERNANZA DE PROMPTS (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (Enterprise AI Gateway & White-Label Router Standard)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 2 (Inteligencia Asistida y Automatización)  
**Bloquea a:** PRD-09, PRD-10, PRD-14, PRD-15

---

## 1. Arquitectura del AI Gateway y Suite White-Label

El AI Gateway (`backend/apps/ai_gateway/`) es el único punto de entrada para todas las operaciones de inteligencia artificial en Dekopen. Aplica **White-Labeling absoluto** (los usuarios de los talleres nunca ven nombres de proveedores crudos) y enruta el 99% de las tareas al motor principal ultra-eficiente:

```
[ Frontend / Canvas S06 ] ──► [ AI Gateway Django Middleware ]
                                      │
     ┌────────────────────────────────┴────────────────────────────────┐
     ▼                                                                 ▼
[ PRE-INVOCATION HOOKS ]                                      [ ENRUTADOR DINÁMICO (ai_routes) ]
• Validación transaccional de saldo                           • Dekopen Neural Core™ (GPT 5.6 Luna - 99%)
• Sanitización de inyecciones                                 • Dekopen Vision CAD™ (Gemini 3.7 High)
• Inyección de identidad y RLS (org_id)                       • Dekopen Titan Engine™ (Sol / Kimi Opt-In)
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

## 2. Técnicas de Prompting y Enrutamiento por Herramienta

| Tool ID | Herramienta | Capa de IA (Marca Propia) | Modelo Backend Configurado | Técnica Canónica |
|---|---|---|---|---|
| **T1** | OCR de Planos (S27) | **Dekopen Vision CAD™** | `gemini-3.7-high` | **Few-Shot Multimodal** (extracción JSON de vanos). |
| **T2** | Comandos NLP (Canvas) | **Dekopen Neural Core™** | `gpt-5.6-luna-xhigh-max` | **ReAct con Hooks** (diff paramétrico $\rightarrow$ `/engine`). |
| **T3** | Sugerencia de Descuentos | **Dekopen Neural Core™** | `gpt-5.6-luna-xhigh-max` | **Chain-of-Thought (CoT)** (análisis de márgenes). |
| **T6** | Compilador de Catálogos | **Dekopen Matrix Reader™** | `gemini-3.7-high` / `kimi-k3` | **Directional Stimulus** (holguras y junquillos). |
| **T8** | Certificado Fabricabilidad | **Doble Verificador Ciego** | `gpt-5.6-luna` vs `gpt-5.6-sol` | **Self-Consistency Dual** (cero discrepancia $>0.00\text{ mm}$). |

---

## 3. Pre & Post-Invocation Hooks (Gobernanza a Nivel de Ejecución)

1. **Pre-Invocation:**
   - **Bloqueo Transaccional de Saldo:** `SELECT ... FOR UPDATE` sobre `credit_ledger`. Si el saldo de puntos es $\le 0$, cancela la llamada antes de realizar el request HTTP a la API.
   - **Aislamiento Multi-Tenant:** Inyecta automáticamente el `org_id` y valida permisos RLS.
2. **Post-Invocation (Escudo Matemático):**
   - **El LLM jamás calcula cotas finales:** Todo diff generado por la IA se envía obligatoriamente a `/engine` para recálculo determinista a `0.00 mm`.
   - **Trazabilidad Inmutable:** Escribe en `ai_audit_logs` con `latency_ms`, `tokens_in`, `tokens_out`, `model_name` y hash de payload antes de mutar la BD.

---

## 4. Versionado de Prompts y Registro Desacoplado

- **Prompt Registry (FQN):** Todos los templates de prompts están versionados en código (`prompts/v1/`) con identificadores unívocos (ej: `dekopen:prompt:t2_nlp_command:v1.2`). 
- **Enrutador Dinámico (D16):** Si en el futuro aparece un modelo más eficiente al mismo costo, se actualiza la tabla `ai_routes` o las variables de entorno sin alterar la lógica de negocio ni re-desplegar el core.
