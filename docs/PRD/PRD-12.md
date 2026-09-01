# PRD-12: ENLACE EN VIVO PARA CLIENTES Y EXPORTADOR CAD 2D .DXF (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (V1: Live Portal & 2D CAD • V2: 3D WebGL & AR)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 3 (Salidas Comerciales y Enlaces en Vivo)  
**Bloquea a:** PRD-13

---

## 1. Misión del Módulo de Salidas Digitales

Entregar a los talleres dos herramientas comerciales de alto impacto que reemplazan los presupuestos estáticos en papel:
1. **Enlace Web en Vivo para Clientes y Constructoras (`/view/[token]`):** Portal interactivo para que el cliente final o la constructora revise la cotización desde su celular sin descargar archivos.
2. **Exportador de Planos Técnicos 2D (.DXF):** Descarga instantánea de secciones de perfiles y elevaciones en formato compatible con AutoCAD para arquitectos.
*(Nota de Alcance: El visor 3D volumétrico WebGL y la Realidad Aumentada AR están programados para la Versión 2).*

---

## 2. Especificación del Enlace Web en Vivo (`/view/[token]`)

Ruta pública de solo lectura protegida con token criptográfico UUID:
- **Seguridad Inviolable:** El bundle de JavaScript y las respuestas de API **NO contienen costos de compra, fórmulas de margen ni despiece interno del taller**. Solo exponen dimensiones exteriores, tipo de apertura, color, vidrio y precio de venta final.
- **Interactividad Comercial:** El cliente puede aprobar el presupuesto directamente desde su teléfono o solicitar ajustes.
- **Acciones Disponibles:**
  - `Descargar Cotización Oficial (PDF DOC-01)`
  - `Aceptar Presupuesto y Solicitar Anticipo`
  - `Ver Plano Técnico Vectorial (SVG)`

---

## 3. Exportador de Planos CAD 2D (.DXF)

Utiliza la librería en Python `ezdxf` en el backend para generar planos vectoriales limpios:
- **Capa 0 (Estructura):** Geometría exterior del vano y marco con cotas milimétricas.
- **Capa 1 (Hojas y Perfiles):** Líneas de perfilería de PVC y refuerzos de acero.
- **Capa 2 (Vidrios y Junquillos):** Polígonos de vidrio con espesor y etiquetas de composición (ej: `5-12-5`).
- **Capa 3 (Simbología de Apertura):** Líneas discontinuas normalizadas que indican el sentido de apertura (interior/exterior/corredera).
