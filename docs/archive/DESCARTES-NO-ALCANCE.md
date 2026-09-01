# REGISTRO CANÓNICO DE DESCARTES Y FUNCIONALIDADES FUERA DE ALCANCE (V1)
**Estado:** Inmutable / Archivo de Control de Alcance  
**Referencia Normativa:** PRD-00 §5.4, §7.2 y CONSTITUTION.md (Regla 20)

Este documento registra formalmente todas las ideas, conceptos o características exploratorias que quedan **ESTRICTAMENTE FUERA DE ALCANCE** para los 24 shots de Dekopen V1. La IA constructora tiene **PROHIBIDO** crear modelos, tablas, rutas, componentes o código para cualquiera de estos puntos.

---

## 1. Características Técnicas y Geométricas Fuera de V1

1. **Bow Windows / Bay Windows / Arcos / Ángulos Libres:**
   - **Estado:** FUERA DE V1 según PRD-00 §5.4 y §7.2.
   - **Instrucción:** NO construir en V1. El motor `/engine` soporta exclusivamente las tipologías canónicas: Fijo (`FIXED`), Proyectante (`AWNING`), Oscilobatiente (`TILT_TURN`), Correderas 2/3/4 hojas (`SLIDING_2L/3L/4L`), Monorriel (`SLIDING_MONO`) y Puertas batientes/multipunto (`DOOR_ENTRY`/`DOOR_DOUBLE`).
2. **Conexión Directa a Maquinaria CNC / Tronzadoras Industriales (G-Code):**
   - **Estado:** FUERA DE ALCANCE 18 MESES según PRD-00 §5.4 y §5.5.
   - **Instrucción:** NO construir drivers ni generadores G-code en el monorepo en V1.
3. **Visor 3D Volumétrico WebGL & Realidad Aumentada (AR):**
   - **Estado:** FUERA DE ALCANCE en V1 (Postergado a Fase 2).
   - **Instrucción:** En V1 (SHOT-19) se entrega exclusivamente el Canvas CAD 2D vectorial y el Enlace Web de Proyecto `/view/[token]`.
4. **OCR Manuscrito de Cuaderno de Obra:**
   - **Estado:** FUERA DE ALCANCE.
   - **Instrucción:** El OCR de la Tool T1 (SHOT-15 / Pantalla S27) se enfoca exclusivamente en **planos arquitectónicos en PDF y cuadros de vanos impresos**.
5. **Envío Directo de PDF Comercial por WhatsApp:**
   - **Estado:** FUERA DE ALCANCE en V1.
   - **Instrucción:** La cotización comercial (DOC-01) se genera mediante WeasyPrint y se descarga como PDF oficial o se consulta vía enlace web seguro.

---

## 2. Gobernanza de Modelos y Pasarelas

1. **AI Router Agnóstico (D16):**
   - El router lee la tabla `ai_routes` en base de datos.
   - Modelos estándar: `OPENAI_API_KEY` para tareas NLP/cálculo, `GOOGLE_AI_API_KEY` (Gemini) para OCR visual de planos, y proveedor secundario independiente para el arbitraje de doble ciego T8.
   - Prohibido hardcodear nombres comerciales inventados en el código.
2. **Pasarelas de Pago:**
   - **Chile:** Flow.cl (CLP).
   - **Internacional:** **Paddle** como Merchant of Record (USD).
