# PRD-12: LIVE PORTAL CLIENTE, EXPORTADOR CAD 2D .DXF Y VISOR 3D TÉCNICO (v1.3 MASTER)
**Estado:** Bloqueado / Congelado
**Versión:** 1.3 (SHOT-19: Live View • CAD 2D .DXF • 3D Técnico y Cinemática • AR diferida post-V1)
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`
**Fase:** 3 (Salidas Digitales y Experiencia Visual)
**Bloquea a:** PRD-13

---

## 1. Misión del Módulo de Salidas Digitales (SHOT-19)

Entregar a los talleres tres herramientas comerciales y técnicas de alto impacto para la interacción con constructoras y clientes finales:
1. **Enlace Web en Vivo para Clientes (`/view/[token]`):** Portal interactivo para que el cliente final o la constructora revise la cotización desde cualquier dispositivo.
2. **Exportador de Planos Técnicos 2D (.DXF):** Descarga de secciones de perfiles y elevaciones en formato compatible con CAD para proyectistas y arquitectos.
3. **Visor 3D Técnico y Cinemática de Apertura:** Visualización volumétrica interactiva generada a partir del `parametric_tree` de `/engine` con simulación dinámica de apertura.
*(Nota de Alcance: La Realidad Aumentada [AR] en terreno permanece como Future Capability diferida a post-V1).*

---

## 2. Contratos Normativos Vinculantes (Binding Architecture Contracts)

Los siguientes requerimientos constituyen el contrato formal de SHOT-19 y no admiten variación sin un cambio normativo aprobado:

### 2.1. Seguridad Absoluta del Live Viewer (`/view/[token]`)
- **Blindaje de Precios y Costos:** El bundle de frontend y las respuestas de API en la ruta pública `/view/` **JAMÁS deben contener costos de compra, listas de materiales con precio mayorista, fórmulas de margen ni despiece interno de taller**.
- **Datos Permitidos:** Únicamente dimensiones nominales exteriores, tipo de apertura, color/acabado comercial, tipo de vidrio y precio final de venta aprobado.
- **Acciones Disponibles:** Descarga de Cotización Oficial (PDF DOC-01), aprobación con solicitud de anticipo, vista de plano SVG e inspección 3D técnica.

### 2.2. Contrato de Exportación CAD 2D (.DXF)
- Generación backend determinista de archivos `.dxf` con capas estandarizadas:
  - `Capa 0 (Estructura):` Geometría exterior del vano y marco con cotas milimétricas.
  - `Capa 1 (Hojas y Perfiles):` Contornos de perfilería y refuerzos.
  - `Capa 2 (Vidrios y Junquillos):` Geometría de acristalamiento y etiqueta de composición.
  - `Capa 3 (Simbología de Apertura):` Indicación normalizada de sentido de apertura.

### 2.3. Contrato de Visualización 3D y Cinemática
- **Fidelidad Geométrica:** Todo modelo 3D se construye a partir del `parametric_tree` determinista generado por `/engine`, respetando dimensiones, holguras y perfiles calculados.
- **Cinemática Paramétrica:** Soporte de interacción dinámica que simule el movimiento de las hojas según su tipología de apertura (giro practicable, abatimiento proyectante/oscilobatiente y traslación corredera).
- **Rendimiento:** Carga fluida en navegadores de escritorio y dispositivos móviles modernos sin degradar la capacidad de respuesta de la aplicación.

---

## 3. Línea Base de Implementación (Non-Binding Reference Baseline)

Los siguientes elementos representan referencias arquitectónicas y de diseño recomendadas, pero **NO constituyen un candado tecnológico contractual**:

### 3.1. Motor de Renderizado y Framework Gráfico
- **Referencia Técnica:** El agente o equipo puede implementar el visor utilizando Three.js, React Three Fiber (R3F), Babylon.js, WebGPU o renderizadores WebGL estándar según idoneidad técnica, huella de bundle y desempeño en producción.
- **Materiales PBR y Shaders:** Los acabados visuales (satinado blanco, vetas de madera, antracita mate o vidrio dieléctrico reflectivo) son líneas base de referencia estética; su implementación interna mediante shaders o materiales estándar queda abierta a la ergonomía técnica.

### 3.2. Rangos de Cinemática de Referencia (Baseline Examples)
Los siguientes valores son ejemplos de referencia para la animación interactiva, no leyes físicas inmutables:
- *Practicable (Giro):* Rotación de manilla $\approx 90^\circ$ y apertura de hoja de $0^\circ$ hasta $\approx 90^\circ$ sobre el eje de bisagras.
- *Oscilobatiente (Abatimiento):* Rotación de manilla $\approx 180^\circ$ y basculamiento interior de $0^\circ$ hasta $\approx 15^\circ$ sobre el eje horizontal.
- *Corredera (Traslación):* Desplazamiento horizontal de la hoja sobre su guía hasta el límite de apertura.
