#!/usr/bin/env python3
"""
Script para generar el PDF del informe de seguridad con fecha en el nombre.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

def generate_pdf_report():
    """Generar PDF del informe de seguridad con fecha"""
    
    # Rutas
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / "docs"
    informes_dir = docs_dir / "informes"
    report_md = docs_dir / "INFORME_SEGURIDAD_ASVS.md"
    
    # Crear carpeta de informes si no existe
    informes_dir.mkdir(parents=True, exist_ok=True)
    
    # Verificar que existe el archivo
    if not report_md.exists():
        print(f"❌ Error: No se encontró el archivo {report_md}")
        return 1
    
    # Generar nombre del PDF con fecha
    fecha = datetime.now().strftime("%Y%m%d")
    pdf_name = f"INFORME_SEGURIDAD_ASVS_{fecha}.pdf"
    pdf_path = informes_dir / pdf_name
    
    print(f"📄 Generando PDF: {pdf_name}")
    print(f"   Desde: {report_md}")
    print(f"   Hacia: {pdf_path}")
    print()
    
    # Intentar usar diferentes métodos de conversión
    success = False
    
    # Método 1: Usar markdown2pdf (si está disponible)
    try:
        from markdown2pdf import convert_md_to_pdf
        print("   Método: markdown2pdf")
        convert_md_to_pdf(str(report_md), str(pdf_path))
        success = True
        print("   ✅ PDF generado con markdown2pdf")
    except ImportError:
        print("   ⚠️  markdown2pdf no disponible")
    except Exception as e:
        print(f"   ❌ Error con markdown2pdf: {e}")
    
    # Método 2: Usar markdown + weasyprint (si está disponible)
    if not success:
        try:
            import markdown
            from weasyprint import HTML, CSS
            from markdown.extensions import tables, codehilite, extra
            
            print("   Método: markdown + weasyprint")
            
            # Leer el archivo Markdown
            with open(report_md, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convertir Markdown a HTML
            md = markdown.Markdown(extensions=['extra', 'tables', 'codehilite'])
            html_content = md.convert(md_content)
            
            # Agregar estilos CSS
            html_doc = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: 'DejaVu Sans', Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #254F6D;
            border-bottom: 3px solid #254F6D;
            padding-bottom: 10px;
            margin-top: 0;
            page-break-after: avoid;
        }}
        h2 {{
            color: #254F6D;
            margin-top: 25px;
            border-bottom: 2px solid #ccc;
            padding-bottom: 5px;
            page-break-after: avoid;
        }}
        h3 {{
            color: #555;
            margin-top: 20px;
            page-break-after: avoid;
        }}
        h4 {{
            color: #666;
            margin-top: 15px;
            page-break-after: avoid;
        }}
        p {{
            margin: 8px 0;
            text-align: justify;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 9pt;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #254F6D;
            overflow-x: auto;
            page-break-inside: avoid;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            page-break-inside: avoid;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #254F6D;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        strong {{
            color: #254F6D;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ccc;
            margin: 20px 0;
        }}
        blockquote {{
            border-left: 4px solid #254F6D;
            padding-left: 15px;
            margin: 15px 0;
            color: #555;
            font-style: italic;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
            
            # Generar PDF con weasyprint
            HTML(string=html_doc).write_pdf(pdf_path)
            success = True
            print("   ✅ PDF generado con weasyprint")
            
        except ImportError as e:
            print(f"   ⚠️  weasyprint o markdown no disponible: {e}")
        except Exception as e:
            import traceback
            print(f"   ❌ Error con weasyprint: {e}")
            traceback.print_exc()
    
    # Método 3: Usar reportlab directamente (más básico)
    if not success:
        try:
            import markdown
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
            from html.parser import HTMLParser
            import re
            from html import unescape
            
            print("   Método: markdown + reportlab")
            
            # Leer el archivo Markdown
            with open(report_md, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convertir Markdown a HTML
            md = markdown.Markdown(extensions=['extra', 'tables'])
            html_content = md.convert(md_content)
            
            # Crear el PDF
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=72)
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#254F6D'),
                spaceAfter=12,
                leading=22,
            )
            
            h2_style = ParagraphStyle(
                'CustomH2',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#254F6D'),
                spaceAfter=10,
                spaceBefore=12,
            )
            
            # Función para limpiar HTML básico y convertir a texto plano
            def clean_html(html_text):
                # Remover etiquetas HTML
                text = re.sub(r'<[^>]+>', '', html_text)
                # Decodificar entidades HTML
                text = unescape(text)
                # Limpiar espacios múltiples
                text = re.sub(r'\s+', ' ', text).strip()
                return text
            
            # Procesar el contenido HTML
            story = []
            lines = html_content.split('\n')
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if not line:
                    story.append(Spacer(1, 6))
                    i += 1
                    continue
                
                # Procesar títulos
                if '<h1>' in line:
                    text = clean_html(line)
                    if text:
                        story.append(Paragraph(text, title_style))
                elif '<h2>' in line:
                    text = clean_html(line)
                    if text:
                        story.append(Paragraph(text, h2_style))
                elif '<h3>' in line:
                    text = clean_html(line)
                    if text:
                        story.append(Paragraph(text, styles['Heading3']))
                elif '<h4>' in line:
                    text = clean_html(line)
                    if text:
                        story.append(Paragraph(text, styles['Heading4']))
                # Procesar tablas (básico)
                elif '<table' in line:
                    # Buscar el cierre de la tabla
                    table_lines = [line]
                    j = i + 1
                    while j < len(lines) and '</table>' not in lines[j]:
                        table_lines.append(lines[j])
                        j += 1
                    if j < len(lines):
                        table_lines.append(lines[j])
                    
                    # Extraer filas de la tabla
                    table_html = '\n'.join(table_lines)
                    rows_match = re.findall(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
                    table_data = []
                    for row in rows_match:
                        cells = re.findall(r'<t[dh]>(.*?)</t[dh]>', row, re.DOTALL)
                        table_data.append([clean_html(cell) for cell in cells])
                    
                    if table_data:
                        # Crear tabla en reportlab
                        table = Table(table_data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#254F6D')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                        ]))
                        story.append(table)
                        story.append(Spacer(1, 12))
                    
                    i = j + 1
                    continue
                # Procesar párrafos normales
                elif '<p>' in line or line and not line.startswith('<'):
                    text = clean_html(line)
                    if text and len(text) > 2:
                        story.append(Paragraph(text, styles['Normal']))
                        story.append(Spacer(1, 6))
                # Procesar listas (básico)
                elif '<li>' in line:
                    text = clean_html(line)
                    if text:
                        text = '• ' + text
                        story.append(Paragraph(text, styles['Normal']))
                
                i += 1
            
            # Generar PDF
            doc.build(story)
            success = True
            print("   ✅ PDF generado con reportlab")
            
        except ImportError as e:
            print(f"   ⚠️  reportlab no disponible: {e}")
        except Exception as e:
            import traceback
            print(f"   ❌ Error con reportlab: {e}")
            traceback.print_exc()
    
    # Método 4: Usar pandoc (si está disponible en el sistema)
    if not success:
        try:
            import subprocess
            
            print("   Método: pandoc (sistema)")
            result = subprocess.run(
                ['pandoc', str(report_md), '-o', str(pdf_path), '--pdf-engine=xelatex'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                success = True
                print("   ✅ PDF generado con pandoc")
            else:
                print(f"   ❌ Error con pandoc: {result.stderr}")
        except FileNotFoundError:
            print("   ⚠️  pandoc no está instalado")
        except Exception as e:
            print(f"   ❌ Error ejecutando pandoc: {e}")
    
    if success:
        print()
        print(f"✅ PDF generado exitosamente: {pdf_path}")
        return 0
    else:
        print()
        print("❌ Error: No se pudo generar el PDF con ningún método disponible")
        print()
        print("💡 Soluciones:")
        print("   1. Instalar weasyprint: pip install weasyprint markdown")
        print("   2. Instalar reportlab: pip install reportlab markdown")
        print("   3. Instalar pandoc: https://pandoc.org/installing.html")
        return 1

if __name__ == '__main__':
    sys.exit(generate_pdf_report())

