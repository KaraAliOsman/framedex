# PRD-13: AI GATEWAY, ENRUTAMIENTO Y GOBERNANZA DE PROMPTS (v1.2)
**Estado:** Bloqueado / Congelado
**Versión:** 1.2 (Enterprise AI Gateway & White-Label Router Standard)
**Fase:** 2 (Inteligencia Asistida y Automatización)
**Bloquea a:** PRD-09, PRD-10, PRD-14, PRD-15

---

## 1. Arquitectura del AI Gateway y Suite White-Label

El AI Gateway (`backend/apps/ai_gateway/`) es el único punto de entrada para todas las operaciones de inteligencia artificial en Dekopen. Aplica **White-Labeling absoluto** (los usuarios de los talleres nunca ven nombres de proveedores crudos) y selecciona la capacidad requerida mediante `ai_routes`. La distribución de tráfico y los modelos son configuración operativa:

```
[ Frontend / Canvas S06 ] ──► [ AI Gateway Django Middleware ]
                                      │
     ┌────────────────────────────────┴────────────────────────────────┐
     ▼                                                                 ▼
[ PRE-INVOCATION HOOKS ]                                      [ ENRUTADOR DINÁMICO (ai_routes) ]
• Validación transaccional de saldo                           • Dekopen Neural Core™ (asistencia de texto)
• Sanitización de inyecciones                                 • Dekopen Vision CAD™ (visión multimodal)
• Inyección de identidad y RLS (org_id)                       • Dekopen Titan Engine™ (capacidad ampliada opt-in)
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

## 2. Capacidades por herramienta

| Tool ID | Herramienta | Capa de IA (Marca Propia) | Contrato observable |
|---|---|---|---|
| **T1** | OCR de Planos (S27) | **Dekopen Vision CAD™** | Extracción JSON de vanos; confianza y revisión según PRD-09. |
| **T2** | Comandos NLP (Canvas) | **Dekopen Neural Core™** | Diff paramétrico enviado a `/engine`, según PRD-10. |
| **T3** | Sugerencia de Descuentos | **Dekopen Neural Core™** | Preview de ajuste comercial; cálculos en `/engine`. |
| **T6** | Compilador de Catálogos | **Dekopen Matrix Reader™** | Extracción de holguras y junquillos validada según PRD-08. |
| **T8** | Certificado Fabricabilidad | **Doble Verificador Ciego** | Modelos distintos, doble ciego y arbitraje determinista según PRD-14. |

Las capacidades y sus contratos son normativos; los nombres concretos de modelo/proveedor y
los métodos de prompting son configuración e implementación. No se prescriben cadenas de
pensamiento ni se crean nuevos identificadores de ruta en este documento.

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

- **Prompt Registry (FQN):** Los templates están versionados con identificadores unívocos y trazables. La ruta `prompts/v1/` y el formato `dekopen:prompt:t2_nlp_command:v1.2` son ejemplos de implementación; el texto del prompt no es un contrato de dominio.
- **Enrutador Dinámico (D16):** Si en el futuro aparece un modelo más eficiente al mismo costo, se actualiza la tabla `ai_routes` o las variables de entorno sin alterar la lógica de negocio ni re-desplegar el core.
