# PRD-13: AI GATEWAY, ENRUTAMIENTO Y GOBERNANZA (v1.2)
**Estado:** Bloqueado / Congelado
**Versión:** 1.2
**Fase:** 2 (Inteligencia Asistida y Automatización)
**Bloquea a:** PRD-09, PRD-10, PRD-14, PRD-15

---

## 1. Contrato del AI Gateway

El AI Gateway (backend/apps/ai_gateway/) es el único punto de entrada para operaciones de
inteligencia artificial. Expone capacidades con marca de producto, valida el contexto de
organización y resuelve cada llamada mediante la tabla dinámica ai_routes. Los nombres de
proveedores, modelos y técnicas internas son configuración operativa; no forman parte de este
PRD.

El gateway debe:

- validar saldo y permisos de forma transaccional antes de invocar una ruta;
- sanitizar entradas, inyectar identidad/RLS y evitar datos entre organizaciones;
- validar el esquema de salida y entregar cualquier diff al motor determinista /engine;
- registrar ai_audit_logs antes de aplicar una escritura, incluyendo la ruta operativa usada,
  latencia, tokens y hash del payload;
- preservar el comportamiento humano de revisión y undo donde lo exija el flujo.

## 2. Capacidades y rutas lógicas por herramienta

| Tool ID | Capacidad | Ruta lógica | Resultado observable |
|---|---|---|---|
| T1 | OCR de planos (S27) | multimodal-extraction | posiciones estructuradas, confianza y revisión humana |
| T2 | Comandos NLP de Canvas | text-command | diff paramétrico validado por /engine |
| T3 | Sugerencia de descuentos | pricing-assist | preview antes/después sin escritura directa |
| T6 | Compilación de catálogos | catalog-compilation | borrador tipado y validado antes de publicar |
| T8 | Certificado de fabricabilidad | dual-verification | dos evaluaciones independientes y arbitraje determinista |

La selección concreta de proveedor y modelo vive en ai_routes o en la configuración de runtime.
Cambiar esa selección no puede alterar los contratos de datos, auditoría, seguridad ni las
salidas deterministas.

## 3. Hooks de ejecución

1. **Pre-invocación:** bloquear saldo con SELECT ... FOR UPDATE, validar permisos y fijar el
   contexto RLS antes del request externo. Saldo insuficiente cancela la llamada.
2. **Post-invocación:** la IA nunca calcula cotas finales. Todo diff pasa por /engine para
   recálculo a 0.00 mm y validación de esquema.
3. **Auditoría:** ai_audit_logs se escribe antes de aplicar cualquier diff o cambio de datos.
   Las mutaciones de precio además requieren price_audit_logs.

## 4. Desacoplamiento operativo

Las plantillas, prompts, proveedores, modelos, límites de tokens y técnicas de inferencia son
detalles de implementación versionados junto al runtime. Pueden evolucionar sin cambiar este
PRD mientras se mantengan los resultados observables, la auditoría previa, el aislamiento y la
validación determinista.

ai_routes permite cambiar una ruta o añadir un fallback sin reescribir la lógica de negocio.
Toda ruta nueva debe conservar el contrato de la herramienta, la seguridad y la evidencia de
pruebas correspondiente.
