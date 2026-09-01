# PRD-03: GESTIÓN DE TENANCY, AUTENTICACIÓN, FACTURACIÓN Y BILLETERA DE CRÉDITOS (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.2 (Congelada y Bloqueada tras Auditoría Final)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 0 (Fundacional)  
**Bloquea a:** PRD-05 a PRD-17

---

## 1. Arquitectura de Autenticación y Control de Acceso

Dekopen implementa una capa de autenticación delegada en **Supabase Auth** con mecanismos de inicio de sesión sin contraseña (Magic Link) y autenticación multifactor (MFA/TOTP) obligatoria para el rol `OWNER`.

```
+---------------+      1. SignIn OTP       +----------------+
|  Usuario      | -----------------------> | Supabase Auth  |
|  (Navegador)  | <----------------------- | (Magic Link)   |
|               |      2. Email con Link   +----------------+
|               |                                  |
|               |      3. Valida JWT               v
|               | -----------------------> +----------------+
|               | <----------------------- | Django API     |
+---------------+   {org_id, role, saldo}  | (/api/v1/auth) |
                                           +----------------+
```

---

## 2. Facturación y Pasarelas de Pago Multi-Región

- **Chile (CL):** **Flow.cl** (Suscripciones nativas con Webpay Plus, Servipag y Khipu). Moneda de cobro local CLP ajustada por tipo de cambio con buffer del 5% e IVA incluido.
- **Internacional (US/EU/Resto):** **Paddle** (Merchant of Record - MoR que gestiona automáticamente Sales Tax, VAT y facturación internacional sin carga impositiva para el taller). Moneda ancla oficial: **USD**.
- **LatAm Expansión (MX, CO, PE, AR):** MercadoPago (Fase 2+).

---

## 3. Planes de Suscripción Oficiales

| Parámetro | Trial | Starter | Profesional ⭐ | Business | Business 2x |
|---|---|---|---|---|---|
| **Mensual** | — | USD 39 | USD 69 | USD 129 | USD 149 |
| **Anual (billed annually)** | — | USD 35/mo | USD 59/mo | USD 99/mo | USD 129/mo |
| **Total anual** | — | USD 420 | USD 708 | USD 1.188 | USD 1.548 |
| **Usuarios Incluidos** | 1 | 2 | 3 | 5 | 5 |
| **Créditos IA / mes** | 500 (techo total trial) | 0 | 2.000 | 6.000 | 12.000 |
| **Motor 0.00 mm, 2D SVG, BOM, corte 1D, PDF/OT/Excel, pedido** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **OCR planos, compilador, comandos, plantillas PDF** | — | — | ✓ | ✓ | ✓ |
| **Certificado doble ciego (v1.5), Autopilot (v2), comparador, soporte prioritario** | — | — | — | ✓ | ✓ |
| **Diferenciador** | Prueba completa 7 días | El motor completo. Sin IA, por elección. | **MÁS POPULAR** | Todo el producto | Solo 2× créditos. Nada más. |

- **Trial:** 7 días sobre Profesional completo, sin tarjeta, techo duro de 500 créditos totales. Signup directo a Starter = 0 créditos. Al expirar el trial, downgrade automático a Starter (*el motor de cálculo nunca se bloquea*).
- **Usuario Extra:** USD 12/mes (USD 10/mes en ciclo anual), en todos los planes pagos.
- **Cláusula de Grandfathering Estándar:** Todo cambio futuro en precios de lista garantiza precio congelado por 12 meses para suscriptores activos.
- **Founding 50 (Excepción de Precio de por Vida):** Los primeros 50 suscriptores anuales (`founding_member = TRUE`) congelan su tarifa de por vida (`price_locked = TRUE`), protegida contra incrementos futuros de tarifa o reajustes por IPC. Respaldada en `tenancy_organizations.founding_member` y `subscriptions.founding_member`.

---

## 4. Billetera y Consumo de Créditos de IA (Medición Dinámica por Tokens Reales)

### 4.1. Algoritmo de Cálculo y Débito Dinámico por Tokens
El sistema **NO cobra tarifas fijas hardcodeadas**. Cada llamada a una herramienta de IA (Tools T1 a T12) se debita en tiempo real según los **tokens reales consumidos** devueltos por el proveedor (`tokens_in` y `tokens_out`):

1. **Cálculo del Costo API Real (USD):**
   $$\text{Costo API} = (\text{tokens\_in} \times \text{precio\_in}) + (\text{tokens\_out} \times \text{precio\_out})$$
2. **Conversión a Créditos Dekopen (con Margen 2x de Ganancia):**
   $$\text{Créditos a Debitar} = \lceil \text{Costo API en USD} \times 200 \rceil$$
   *(Equivalencia: \$1 USD de costo API = 100 créditos base. Con margen comercial 2x = 200 créditos por cada \$1 USD de costo API).*
3. **Saldo Cero:** Al agotarse los créditos, las funciones de IA se pausan. **El motor de cálculo `/engine`, diseñador 2D, cotizador manual, corte 1D y exportación de PDFs siguen 100% operativos** (*retención, no castigo*).

### 4.2. Packs de Recarga de Créditos (Margen Comercial 2x)
| Pack | Precio al Cliente | Costo API Real | Créditos Incluidos |
|---|---|---|---|
| **Top-up 1.000** | USD 15 | ~$5 USD | 1.000 créditos |
| **Top-up 3.000** | USD 40 | ~$15 USD | 3.000 créditos |
| **Top-up 7.500** | USD 90 | ~$37.5 USD | 7.500 créditos |

### 4.3. Tabla de Consumo Promedio Estimado (Referencial para Marketing)
*Nota técnica: Los siguientes valores son promedios referenciales de consumo típico para comunicación al cliente. El débito en base de datos (`credit_ledger`) siempre se calcula de forma dinámica según los tokens reales.*

| Tool ID | Función | Operación Realizada | Consumo Promedio Estimado | Modelo Asignado |
|---|---|---|---|---|
| `T1` | `extract_positions(file)` | OCR multimodal de plano PDF y extracción de vanos | **~10 créditos** / plano | Dekopen Vision CAD™ (Gemini 3.7) |
| `T2` | `propose_window_command(text)` | Interpretación NLP de instrucción de diseño geométrico | **~4 créditos** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T3` | `apply_pricing_command(mode,params)` | Cálculo y preview de ajuste comercial por comando | **~3 créditos** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T4` | `missing_questions(ctx)` | Diagnóstico de variables faltantes para cotización | **~2 créditos** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T5` | `explain_item(bom_line)` | Explicación técnica de taller de una partida de material | **~1 crédito** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T6` | `compile_catalog(file)` | Compilación completa de catálogo técnico desde PDF | **~25 + 2 cr / pág** | Dekopen Matrix Reader™ (Kimi k3) |
| `T7` | `propose_compatibility_edge(a,b)` | Sugerencia de compatibilidad perfil-herraje | **~2 créditos** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T8` | `cross_verify_certificate(pos)` | Doble verificación cruzada con modelo alternativo | **~50 créditos** | Doble Verificador (Luna vs Sol) |
| `T9` | `draft_autopilot(request)` | Generación integral de cotización borrador desasistida | **~30 + 2 cr / pág** | Pipeline completo multimodal |
| `T10` | `compare_plans(v1,v2)` | Análisis de diferencias entre dos versiones de plano | **~8 créditos** | Dekopen Vision CAD™ (Gemini 3.7) |
| `T11` | `margin_alert(ctx)` | Detección preventiva de márgenes comerciales negativos | **~1 crédito** | Dekopen Neural Core™ (GPT 5.6 Luna) |
| `T12` | `forecast_materials(h)` | Pronóstico de compra de barras según histórico | **~5 créditos** | Dekopen Neural Core™ (GPT 5.6 Luna) |
