# Edición de PDF externos — evaluación (etapa 06)

Fecha: 2026-10-18. Categoría: **investigación externa basada en conocimiento previo**.
No se descargó ni integró ninguna dependencia, y no se verificaron precios ni versiones actuales.

## Separación decidida

- **Documentos propios** (cotización, corte, pedidos): DEKOPEN edita el *original
  estructurado*, es decir el diseño, los bloques, los textos y la presentación (`document_layout`),
  y vuelve a renderizar con el mismo contrato de exportación. No se edita un PDF propio.
- **PDF externos** (catálogos de proveedor, planos del cliente): son evidencia. Hoy se
  inventarían, renderizan e importan; no se modifican.

## Opciones de edición real de contenido PDF

| Opción | Qué permite | Licencia | Encaje |
|---|---|---|---|
| Apryse WebViewer (antes PDFTron) + módulo de edición de contenido | Edita texto e imágenes existentes en el navegador y reorganiza páginas | Comercial, por desarrollo y despliegue; precio por cotización | Técnicamente adecuada; se paga aunque se use poco |
| Nutrient Web SDK (antes PSPDFKit) + editor de contenido | Edita texto e imágenes, formularios y páginas | Comercial; precio por cotización | Equivalente a Apryse |
| pdf.js (Mozilla) | Visor con anotaciones (texto libre, tinta, sello) | Apache-2.0 | **No es edición de contenido**: solo agrega capas encima |
| pdf-lib / pypdf | Operaciones programáticas: unir, dividir, rellenar formularios, agregar contenido | MIT / BSD | No editan el texto existente de forma general |

## Conclusión

- No se llama «edición» a las anotaciones. Ninguna opción abierta edita el contenido
  existente de forma fiable.
- La edición real de PDF externos queda **pendiente de una decisión del dueño**
  sobre licencia y presupuesto (Apryse o Nutrient). Se pidió una prueba con un PDF de
  proveedor real antes de comprometerse.
- Mientras tanto, el flujo útil sigue siendo **importar → corregir los datos en DEKOPEN
  → emitir un documento propio**.
