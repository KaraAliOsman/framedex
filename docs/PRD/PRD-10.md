# PRD-10: CO-PILOTO DE ACCIÓN DIRECTA (CMD+K), DIFFS VISUALES Y DESHACER SAGRADO (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (Action-First UX Standard — Estilo Codex / Antigravity)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 2 (Comandos y Diffs Paramétricos)  
**Bloquea a:** PRD-11

---

## 1. Filosofía de Interacción: Cero Chatbot, Acción Pura

En Dekopen, la inteligencia artificial **NO es una ventana de chat flotante ni un bot conversacional con saludos**. Es un **operador de acción directa integrado en el Canvas** diseñado bajo la interacción de herramientas como Codex, Claude Code y Antigravity:

1. **Cero Saludos o Texto de Relleno:** La IA no responde con explicaciones largas. Modifica el dibujo técnico o el presupuesto en milisegundos.
2. **Barra de Comandos `Cmd + K` (o `Ctrl + K`):** Acceso instantáneo desde cualquier pantalla para transformar ventanas o precios sin navegar por menús.
3. **Diffs Visuales Antes / Después:** Toda propuesta de cambio genera una vista previa con delta de costo antes de aplicarse.
4. **El Deshacer Sagrado (`Cmd + Z`):** Toda mutación ejecutada por la IA se puede revertir con una sola tecla.

---

## 2. Flujo de Trabajo de la Barra de Comandos (`Cmd + K`)

```
[ Usuario presiona Cmd+K ] ──► [ Input Flotante Minimalista en Canvas ]
                                             │
                       [ "dividir en 3 hojas, centro oscilobatiente" ]
                                             │
                                             ▼
                      [ AI Gateway (Tool T2: Parse Command) ]
                                             │
                                             ▼
                          [ Cálculo en /engine (0.00 mm) ]
                                             │
                                             ▼
                    ┌─────────────────────────────────────────────────┐
                    │          MODAL DE DIFF VISUAL (200 ms)          │
                    ├─────────────────────────────────────────────────┤
                    │ • Antes (Rojo): 2 Hojas Correderas ($180.000)   │
                    │ • Propuesta (Verde): 3 Cuerpos OB ($215.000)    │
                    │                                                 │
                    │ [ Tab / Enter: Aceptar ]    [ Esc: Descartar ]  │
                    └─────────────────────────────────────────────────┘
```

---

## 3. Comandos de Precios y Rentabilidad (Tool T2 / T3)

La IA traduce lenguaje natural a parámetros de `/engine` sin inventar aritmética:

| Comando del Usuario | Interpretación de la IA | Acción en `/engine` |
|---|---|---|
| *"Ponle 200% de ganancia a este proyecto"* | `mode: MARGIN_PERCENT, value: 200.0` | Recalcula el precio de venta manteniendo el costo de materiales intacto. |
| *"Calcula a 200 mil por m² en ventanas nogal"* | `mode: TARGET_M2, value: 200000.0, filter: {color: 'nogal'}` | Despeja el margen necesario para que el precio final por $m^2$ sea exacto. |
| *"Aplica 15% de descuento a los fijos del 2do piso"* | `mode: DISCOUNT_PERCENT, value: 15.0, filter: {type: 'FIXED', floor: 2}` | Aplica descuento de línea sin alterar las demás ventanas. |
| *"¿Qué cambiarías para bajar 10% el costo?"* | `tool: T9_ALTERNATIVES, goal: COST_REDUCTION_10` | Propone alternativas de optimización de perfil o vidrio en el modal de Diff. |

---

## 4. Tareas en Segundo Plano sin Bloqueo de UI (*Non-Blocking Workers*)

Cuando se procesan operaciones pesadas (como la lectura de un PDF de planos con 15 vanos en S27):
1. **La interfaz nunca se congela:** El usuario puede seguir dibujando o cotizando.
2. **Notificación Discreta en Barra de Estado:**  
   `[ ⚡ 15 vanos extraídos del plano • 13 seguros / 2 para revisar ] -> [ Revisar e Importar ]`
3. **Auditoría Obligatoria:** Todo cambio registra una fila en `ai_audit_logs` con el payload antes/después para permitir reversión infinita.
