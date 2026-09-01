# REGISTRO DE ALCANCE V1 Y PUENTES A FASE 2 (3D & CNC)
**Estado:** Inmutable / Control de Alcance V1 y Roadmap V2  
**Referencia:** PRD-00, PRD-01, PLAN_SHOTS.md

---

## 1. Alcance Completo de Tipologías en Versión 1 (V1 — 100% INCLUIDAS)

Todas las geometrías y tipologías de ventanas y puertas de PVC y aluminio son **núcleo esencial de la Versión 1**:

1. **Paños Fijos (FIXED):** Geometría simple y compuesta con travesaños verticales y horizontales.
2. **Correderas (SLIDING):** 2 hojas, 3 hojas, 4 hojas, 3 rieles (3T) y monorriel con paño fijo.
3. **Oscilobatientes (TILT_TURN):** Apertura practicable interior y ventilación superior con herraje perimetral.
4. **Proyectantes / Proyección Exterior (AWNING):** Brazos de fricción y cremonas multipunto.
5. **Puertas de Entrada y Balcón (DOOR):** Cerraduras de seguridad, cilindros, manillas dobles y umbrales de aluminio.
6. **Bow Windows / Ventanas en Bahía / Esquinas en Ángulo (BAY_WINDOW & CORNER_COUPLER):**
   - Cálculo exacto de deducción geométrica por **Poste de Acople a 90°**, **Poste de Acople a 135°** y **Poste Esquinero Variable con Tubo de Acero Estructural**.
   - Despiece de marcos individuales descontando la huella del acople angular para encajar milimétricamente en el vano en ochavo o esquina.

---

## 2. Características Diferidas Exclusivamente a Fase 2 (V2 — Roadmap 18 Meses)

Únicamente dos características avanzadas quedan programadas para la Fase 2, dejando sus puentes arquitectónicos listos en V1:

1. **Visor 3D Volumétrico WebGL & Realidad Aumentada (AR):**
   - *En V1 (SHOT-19):* Se entrega el Canvas CAD 2D de alta precisión y el Enlace Web `/view/[token]` de proyecto. En SHOT-19 se deja el andamiaje del viewport preparado para activar el render 3D en V2 sin reescribir la API.
2. **Conexión Directa a Tronzadoras y Maquinaria CNC (G-Code):**
   - *En V1 (SHOT-24):* Se entregan las Listas de Corte optimizadas (DOC-03) en PDF y Excel, y se deja el endpoint stub `/api/v1/export/cnc/` preparado para habilitar los drivers binarios en V2.
