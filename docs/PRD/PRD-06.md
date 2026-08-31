# PRD-06: GENERACIÓN DE DOCUMENTOS DE SALIDA (PDF, EXCEL, OT Y CORTE 1D) (v1.1.0)
**Estado:** Bloqueado / Congelado  
**Fase:** 1 (Núcleo)  
**Bloquea a:** PRD-11, PRD-14, PRD-15

---

## 1. Misión y Principio de Integridad Documental

Toda la documentación emitida por Dekopen se deriva estrictamente del cálculo determinista de `/engine`. 

### Regla del Hash de Integridad BOM
Antes de generar cualquier documento (comercial, de taller o de compras), el sistema calcula el hash `SHA-256` del snapshot JSON del proyecto y su BOM:
$$\text{BOM\_HASH} = \text{SHA256}(\text{project\_id} + \text{revision} + \text{positions\_json} + \text{bom\_json})$$
Este hash se incrusta como código de verificación en el pie de página de todos los documentos emitidos. Si el hash no coincide exactamente entre la cotización del cliente, la OT del taller y la orden de compra de vidrios, el documento es rechazado automáticamente por no coincidencia de versión.

---

## 2. Inventario de Documentos del Sistema

| ID | Documento | Formato / Motor | Destinatario | Contenido Clave |
|---|---|---|---|---|
| **DOC-01** | **Cotización Comercial Formal** | PDF (WeasyPrint) | Cliente Final / Arquitecto | Membrete de empresa, renders vectoriales 2D (SVG), desglose de vanos, especificación de vidrios y colores, totales neto/IVA/bruto, condiciones de pago y validez de oferta. |
| **DOC-02** | **Planilla de Pedido de Vidrios** | Excel `.xlsx` (openpyxl) | Fábrica de Termopaneles / Vidriería | Pestaña estandarizada con vanos, composición exacta, anchos, altos, cantidades, m² totales, cantos pulidos y etiquetas de ubicación. |
| **DOC-03** | **Orden de Trabajo de Taller (OT)** | PDF (WeasyPrint) | Jefe de Taller / Operarios | Planos técnicos acotados con cotas de corte exterior, medidas de refuerzo de acero, orificios de desagüe, altura de manillas y matriz de ensamble. |
| **DOC-04** | **Pedido de Barras y Perfiles** | PDF + Excel | Distribuidor de Perfilería | Consolidado de barras comerciales de $6.00\text{ m}$ por SKU y color, barras de acero galvanizado y accesorios. |
| **DOC-05** | **Hoja de Optimización de Corte 1D** | PDF (WeasyPrint) | Operario de Tronzadora / Sierra | Secuencia de corte barra por barra, IDs de piezas, longitudes exactas con pérdida de fusión, ángulos (45°/90°) y retazos resultantes. |
| **DOC-06** | **Checklist de Calidad y Control Final** | PDF (WeasyPrint) | Control de Calidad en Taller | Hoja de verificación física: escuadra de diagonales ($\le 1.0\text{ mm}$), estanqueidad de burletes, desagües destapados, calibración de herraje. |
| **DOC-07** | **Informe Ejecutivo de Costos y Margen** | PDF (Solo Propietario) | Dueño de Empresa / Gerencia | Desglose confidencial de costo de materiales, mano de obra, mermas reales, margen bruto por posición y rentabilidad consolidada. |

---

## 3. Especificación Técnica de WeasyPrint (HTML/CSS Pautado)

Los PDFs se compilan renderizando plantillas HTML con estilos CSS pautados compatibles con la especificación W3C Paged Media:

```css
@page {
  size: letter portrait;
  margin: 15mm 12mm 20mm 12mm;
  @top-left {
    content: "Dekopen ERP • Sistema de Fabricación";
    font-family: 'Inter', sans-serif;
    font-size: 8pt;
    color: #64748b;
  }
  @top-right {
    content: "Proyecto: " attr(data-project-code);
    font-family: 'Inter', sans-serif;
    font-size: 8pt;
    font-weight: bold;
    color: #1e293b;
  }
  @bottom-left {
    content: "Verificación de Integridad: " attr(data-bom-hash);
    font-family: monospace;
    font-size: 7pt;
    color: #94a3b8;
  }
  @bottom-right {
    content: "Página " counter(page) " de " counter(pages);
    font-family: 'Inter', sans-serif;
    font-size: 8pt;
    color: #64748b;
  }
}

.avoid-break {
  page-break-inside: avoid;
}
```

---

## 4. Estructura de la Planilla Excel de Vidrios (`DOC-02` - openpyxl)

El archivo `.xlsx` generado para la vidriería cumple estrictamente con el formato estándar de la industria:

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def generate_glass_order_excel(project_data, glasses_list) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pedido Vidrios"
    
    # Encabezado Corporativo
    ws.merge_cells('A1:H1')
    ws['A1'] = f"PEDIDO DE CRISTALES / TERMOPANELES — {project_data['code']}"
    ws['A1'].font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
    ws['A1'].fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    
    # Columnas Técnicas
    headers = [
        "Ítem", "Posición", "Vano", "Composición Vidrio", 
        "Ancho (mm)", "Alto (mm)", "Cantidad", "Área Unitaria (m²)", "Área Total (m²)"
    ]
    ws.append(headers)
    
    for row_idx, g in enumerate(glasses_list, start=3):
        ws.append([
            row_idx - 2,
            g['position_index'],
            g['bay_index'],
            g['composition'],
            float(g['width_mm']),
            float(g['height_mm']),
            g['quantity'],
            float(g['area_m2']),
            f"=G{row_idx}*H{row_idx}" # Fórmula Excel nativa
        ])
    
    # Fila de Totales
    last_row = len(glasses_list) + 2
    ws.append(["TOTALES", "", "", "", "", "", f"=SUM(G3:G{last_row})", "", f"=SUM(I3:I{last_row})"])
    return save_virtual_workbook(wb)
```

---

## 5. Hoja de Optimización de Corte 1D (`DOC-05`)

Para cada tipo de perfil (Marco, Hoja, Travesaño, Junquillo), la hoja de corte muestra el mapa gráfico y numérico de utilización:

```
================================================================================
PERFIL: MARCO PRINCIPAL 60mm (SKU: PF-DEMO-60-BL) | BARRA: 6000 mm | COLOR: BLANCO
TOTAL BARRAS REQUERIDAS: 4 BARRAS | APROVECHAMIENTO: 94.2% | MERMA: 5.8%
================================================================================
BARRA #1: [Despunte: 15mm] 
  ├── [Pos 1 - Marco Inf]  1006 mm  (45°/45°) -> Refuerzo: 970 mm
  ├── [Pos 1 - Marco Sup]  1006 mm  (45°/45°) -> Refuerzo: 970 mm
  ├── [Pos 1 - Marco Izq]  1006 mm  (45°/45°) -> Refuerzo: 970 mm
  ├── [Pos 1 - Marco Der]  1006 mm  (45°/45°) -> Refuerzo: 970 mm
  ├── [Pos 2 - Marco Inf]   806 mm  (45°/45°) -> Refuerzo: 770 mm
  ├── [Pos 2 - Marco Sup]   806 mm  (45°/45°) -> Refuerzo: 770 mm
  └── [Retazo Sobrante: 320 mm] (Kerf acumulado: 24mm | Despunte fin: 15mm)
--------------------------------------------------------------------------------
```

---

## 6. Almacenamiento y Seguridad de Archivos

1. **Bucket:** Supabase Storage (`bucket: documents`).
2. **Ruta:** `org_{org_id}/projects/{project_id}/{revision_code}/{document_type}_{hash}.pdf`.
3. **Acceso:** Exclusivamente a través de URLs firmadas con expiración máxima de $3600\text{ segundos}$ ($1\text{ hora}$) generadas por el backend tras validar la sesión del usuario.
