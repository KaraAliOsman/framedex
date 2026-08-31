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
- **Internacional (US/EU/Resto):** **Paddle** (Merchant of Record - MoR que gestiona Sales Tax y VAT). Moneda ancla oficial: **USD**.
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
- **Cláusula de Grandfathering:** Todo cambio futuro en los precios de lista de las suscripciones exige un aviso previo de 60 días a los clientes y garantiza el precio congelado por 12 meses para suscriptores activos.

---

## 4. Billetera y Consumo de Créditos de IA

### 4.1. Conversión Interna Privada y Saldo Cero
- **Conversión Interna Privada:** 200 créditos = USD 1 de costo API real ($1\text{ crédito} = \text{USD } 0.005$). Esta equivalencia es estrictamente privada y nunca visible en la UI.
- **Saldo Cero:** Al agotarse los créditos, las funciones de IA se pausan. **El motor de cálculo, diseñador 2D, cotizador manual, corte 1D y exportación de PDFs siguen 100% operativos** (*retención, no castigo*).

### 4.2. Packs de Recarga de Emergencia
| Pack | Precio | Créditos Incluidos |
|---|---|---|
| **Top-up 1.000** | USD 15 | 1.000 créditos |
| **Top-up 3.000** | USD 40 | 3.000 créditos |
| **Top-up 7.500** | USD 90 | 7.500 créditos |

### 4.3. Tabla de Consumo por Herramienta de IA

| Tool ID | Función | Operación Realizada | Costo en Créditos | Justificación de Costo API |
|---|---|---|---|---|
| `T1` | `extract_positions(file)` | OCR multimodal de plano/pliego y extracción de vanos | **10 créditos** por plano | Gemini Flash OCR multimodal |
| `T2` | `propose_window_command(text)` | Interpretación NLP de instrucción de diseño geométrico | **4 créditos** | Mutación paramétrica tipada |
| `T3` | `apply_pricing_command(mode,params)` | Cálculo y preview de ajuste comercial por comando | **3 créditos** | Diff comercial |
| `T4` | `missing_questions(ctx)` | Diagnóstico de variables faltantes para cotización | **2 créditos** | Consulta quirúrgica |
| `T5` | `explain_item(bom_line)` | Explicación técnica de taller de una partida de material | **1 crédito** | Micro-explicación |
| `T6` | `compile_catalog(file)` | Compilación completa de catálogo técnico desde PDF | **25 + 2 créditos / pág** *(mín 25)* | Extracción profunda de tablas y matrices |
| `T7` | `propose_compatibility_edge(a,b)` | Sugerencia de compatibilidad perfil-herraje | **2 créditos** | Grafo de herrajes |
| `T8` | `cross_verify_certificate(pos)` | Doble verificación cruzada con modelo alternativo | **50 créditos** | Doble modelo LLM independiente (~$0.25) |
| `T9` | `draft_autopilot(request)` | Generación integral de cotización borrador desasistida | **30 + 2 créditos / pág** | Pipeline completo multimodal + BOM |
| `T10` | `compare_plans(v1,v2)` | Análisis de diferencias entre dos versiones de plano | **8 créditos** | Comparativa visual de planos |
| `T11` | `margin_alert(ctx)` | Detección preventiva de márgenes comerciales negativos | **1 crédito** | Análisis financiero de riesgo |
| `T12` | `forecast_materials(h)` | Pronóstico de compra de barras según histórico | **5 créditos** | Modelo predictivo de compras |
