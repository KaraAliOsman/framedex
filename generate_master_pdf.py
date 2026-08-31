import os
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Skip cover page
        
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header
        self.drawString(40, letter[1] - 30, "DEKOPEN — BIBLIA DE EJECUCIÓN Y SUITE MAESTRA (v1.1)")
        self.drawRightString(letter[0] - 40, letter[1] - 30, "Tolerancia 0.00 mm • [HASH-RECALCULAR-AL-EMITIR]")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(40, letter[1] - 34, letter[0] - 40, letter[1] - 34)
        
        # Footer
        self.line(40, 40, letter[0] - 40, 40)
        self.drawString(40, 28, "Confidencial • Documento Único Integral para IA Constructora")
        self.drawRightString(letter[0] - 40, 28, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()

def clean_inline_md(text):
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Re-enable simple formatting
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<font face="Courier" color="#0284C7"><b>\1</b></font>', text)
    return text

def build_pdf():
    docs_dir = r'c:\Users\alios\Documents\antigravity\vibrant-hertz\docs'
    md_file = os.path.join(docs_dir, 'DEKOPEN_BIBLIA_COMPLETA_v1.1_MASTER.md')
    pdf_file = os.path.join(docs_dir, 'DEKOPEN_BIBLIA_COMPLETA_v1.1_MASTER.pdf')
    
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=48,
        bottomMargin=48
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0F172A'),
        alignment=1, # Center
        spaceAfter=15
    ))
    styles.add(ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#3B82F6'),
        alignment=1,
        spaceAfter=30
    ))
    styles.add(ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        'H3',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2563EB'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        'ListBulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1E293B'),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    ))
    styles.add(ParagraphStyle(
        'CodeBlock',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor('#0F172A'),
        backColor=colors.HexColor('#F8FAFC'),
        borderColor=colors.HexColor('#CBD5E1'),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#1E293B')
    ))
    styles.add(ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#FFFFFF')
    ))

    story = []
    
    # 1. COVER PAGE
    story.append(Spacer(1, 100))
    story.append(Paragraph("DEKOPEN", styles['CoverTitle']))
    story.append(Paragraph("BIBLIA DE EJECUCIÓN Y SUITE MAESTRA COMPLETA (v1.1)", styles['CoverSubtitle']))
    story.append(HRFlowable(width="60%", thickness=2, color=colors.HexColor('#2563EB'), spaceAfter=40))
    
    story.append(Paragraph("<b>Versión Oficial:</b> 1.1 (Congelada y Bloqueada)", styles['CoverMeta']))
    story.append(Paragraph("<b>Hash de Integridad Normativa:</b> [HASH-RECALCULAR-AL-EMITIR]", styles['CoverMeta']))
    story.append(Paragraph("<b>Fecha de Compilación:</b> 30 de Agosto de 2026", styles['CoverMeta']))
    story.append(Paragraph("<b>Destinatario:</b> Agente Constructor / IA de Implementación y Equipo de Desarrollo", styles['CoverMeta']))
    story.append(Paragraph("<b>Motor Matemático:</b> Tolerancia 0.00 mm • Decimal Estricto • Monolito Django + React SVG", styles['CoverMeta']))
    
    story.append(Spacer(1, 80))
    story.append(Paragraph("<i>Este documento consolida la totalidad de especificaciones técnicas, fórmulas canónicas, esquemas DDL con RLS, contratos de API, diseño dual Adobe CAD, reglas de taller y casos de oro congelados G1–G12.</i>", styles['CoverMeta']))
    story.append(PageBreak())
    
    # Parse Markdown content
    lines = md_text.split('\n')
    idx = 0
    total_lines = len(lines)
    
    in_code_block = False
    code_lines = []
    
    while idx < total_lines:
        line = lines[idx]
        
        # Check code block
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                raw_code = '\n'.join(code_lines)
                # Split large code blocks if needed or use Preformatted
                story.append(Preformatted(raw_code, styles['CodeBlock']))
            idx += 1
            continue
            
        if in_code_block:
            code_lines.append(line)
            idx += 1
            continue
            
        stripped = line.strip()
        
        if not stripped:
            idx += 1
            continue
            
        # Divider
        if stripped in ['---', '***', '===']:
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceBefore=8, spaceAfter=8))
            idx += 1
            continue
            
        # Headers
        if stripped.startswith('# '):
            story.append(Paragraph(clean_inline_md(stripped[2:]), styles['H1']))
            idx += 1
            continue
        elif stripped.startswith('## '):
            story.append(Paragraph(clean_inline_md(stripped[3:]), styles['H2']))
            idx += 1
            continue
        elif stripped.startswith('### '):
            story.append(Paragraph(clean_inline_md(stripped[4:]), styles['H3']))
            idx += 1
            continue
        elif stripped.startswith('#### '):
            story.append(Paragraph(clean_inline_md(stripped[5:]), styles['H3']))
            idx += 1
            continue
            
        # Table parsing
        if stripped.startswith('|') and stripped.endswith('|'):
            table_rows = []
            while idx < total_lines and lines[idx].strip().startswith('|') and lines[idx].strip().endswith('|'):
                row_str = lines[idx].strip()
                # Skip markdown separator row like |---|---|
                if re.match(r'^\|[\s\-:|]+\|$', row_str):
                    idx += 1
                    continue
                cells = [c.strip() for c in row_str.split('|')[1:-1]]
                table_rows.append(cells)
                idx += 1
                
            if table_rows:
                # Build ReportLab Table
                col_count = max(len(r) for r in table_rows)
                # Normalize row cell count
                norm_rows = []
                for r_idx, r in enumerate(table_rows):
                    r_cells = []
                    for c_idx in range(col_count):
                        cell_val = r[c_idx] if c_idx < len(r) else ""
                        style = styles['TableHead'] if r_idx == 0 else styles['TableCell']
                        r_cells.append(Paragraph(clean_inline_md(cell_val), style))
                    norm_rows.append(r_cells)
                
                # Available width = 612 - 80 = 532 pt
                usable_width = 532
                col_w = usable_width / col_count
                t = Table(norm_rows, colWidths=[col_w] * col_count)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(Spacer(1, 4))
                story.append(t)
                story.append(Spacer(1, 6))
            continue
            
        # Lists
        if stripped.startswith(("- ", "* ")):
            bullet_text = f"• {clean_inline_md(stripped[2:])}"
            story.append(Paragraph(bullet_text, styles['ListBulletCustom']))
            idx += 1
            continue
        elif re.match(r'^\d+\.\s', stripped):
            num_match = re.match(r'^(\d+\.)\s(.*)', stripped)
            if num_match:
                prefix = num_match.group(1)
                rest = num_match.group(2)
                story.append(Paragraph(f"<b>{prefix}</b> {clean_inline_md(rest)}", styles['ListBulletCustom']))
            idx += 1
            continue
            
        # Standard paragraph
        story.append(Paragraph(clean_inline_md(stripped), styles['Body']))
        idx += 1

    print("Compiling PDF with NumberedCanvas...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF Generated successfully at: {pdf_file}")
    print(f"Size: {os.path.getsize(pdf_file)} bytes")

if __name__ == '__main__':
    build_pdf()
