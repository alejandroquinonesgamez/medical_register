#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar el PDF del informe de seguridad ASVS con fecha en el nombre.

Lee el archivo docs/INFORME_SEGURIDAD.md y lo convierte a PDF.
El PDF se guarda en docs/informes/ con el formato: INFORME_SEGURIDAD_YYYYMMDD.pdf

El informe está basado en OWASP ASVS versión 4.0.3 y OWASP WSTG (Web Security Testing Guide).
Fuente oficial: https://github.com/OWASP/ASVS/tree/v4.0.3/4.0/

Intenta usar múltiples métodos de conversión (en orden de preferencia):
1. markdown2pdf
2. markdown + weasyprint
3. markdown + reportlab
4. pandoc (si está instalado en el sistema)

Usado por:
- make pdf_report / .\\make.ps1 pdf_report
- Endpoint /api/defectdojo/generate-pdf
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path

def remove_emojis(text):
    """Eliminar emojis del texto para el PDF"""
    # Patrón para eliminar emojis Unicode comunes y variantes
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended-A
        "\U00002139"  # information source (ℹ)
        "\U00002122"  # trade mark sign (™)
        "\U000021A9"  # leftwards arrow with hook (↩)
        "\U0000231A"  # watch (⌚)
        "\U000023E9"  # fast-forward button (⏩)
        "\U000023EC"  # fast down button (⏬)
        "\U000023F0"  # alarm clock (⏰)
        "\U000023F3"  # hourglass done (⏳)
        "\U000025FD"  # white medium-small square (◽)
        "\U00002614"  # umbrella with rain drops (☔)
        "\U00002615"  # hot beverage (☕)
        "\U00002648"  # aries (♈)
        "\U00002649"  # taurus (♉)
        "\U0000264A"  # gemini (♊)
        "\U0000264B"  # cancer (♋)
        "\U0000264C"  # leo (♌)
        "\U0000264D"  # virgo (♍)
        "\U0000264E"  # libra (♎)
        "\U0000264F"  # scorpius (♏)
        "\U00002650"  # sagittarius (♐)
        "\U00002651"  # capricorn (♑)
        "\U00002652"  # aquarius (♒)
        "\U00002653"  # pisces (♓)
        "\U0000267F"  # wheelchair symbol (♿)
        "\U00002693"  # anchor (⚓)
        "\U000026A1"  # high voltage (⚡)
        "\U000026AA"  # white circle (⚪)
        "\U000026AB"  # black circle (⚫)
        "\U000026B0"  # coffin (⚰)
        "\U000026B1"  # funeral urn (⚱)
        "\U000026C4"  # snowman without snow (⛄)
        "\U000026C5"  # sun behind cloud (⛅)
        "\U000026CE"  # ophiuchus (⛎)
        "\U000026D4"  # no entry (⛔)
        "\U000026EA"  # church (⛪)
        "\U000026F2"  # fountain (⛲)
        "\U000026F3"  # flag in hole (⛳)
        "\U000026F5"  # sailboat (⛵)
        "\U000026FA"  # tent (⛺)
        "\U000026FD"  # fuel pump (⛽)
        "\U00002705"  # check mark (✅)
        "\U0000270A"  # raised fist (✊)
        "\U0000270B"  # raised hand (✋)
        "\U0000270C"  # victory hand (✌)
        "\U0000270D"  # writing hand (✍)
        "\U0000270F"  # pencil (✏)
        "\U00002712"  # black nib (✒)
        "\U00002714"  # heavy check mark (✔)
        "\U00002716"  # heavy multiplication x (✖)
        "\U0000271D"  # latin cross (✝)
        "\U00002721"  # star of david (✡)
        "\U00002728"  # sparkles (✨)
        "\U00002733"  # eight-spoked asterisk (✳)
        "\U00002734"  # eight-pointed star (✴)
        "\U00002744"  # snowflake (❄)
        "\U00002747"  # sparkle (❇)
        "\U0000274C"  # cross mark (❌)
        "\U0000274E"  # negative squared cross mark (❎)
        "\U00002753"  # question mark ornament (❓)
        "\U00002754"  # white question mark ornament (❔)
        "\U00002755"  # white exclamation mark ornament (❕)
        "\U00002757"  # heavy exclamation mark symbol (❗)
        "\U0000275B"  # heavy left-pointing angle quotation mark ornament (❛)
        "\U0000275C"  # heavy right-pointing angle quotation mark ornament (❜)
        "\U0000275D"  # heavy left-pointing angle quotation mark ornament (❝)
        "\U0000275E"  # heavy right-pointing angle quotation mark ornament (❞)
        "\U00002761"  # heavy heart exclamation mark ornament (❡)
        "\U00002763"  # heavy black heart (❣)
        "\U00002764"  # black heart suit (❤)
        "\U00002765"  # rotated heavy black heart bullet (❥)
        "\U00002766"  # floral heart (❦)
        "\U00002767"  # rotated floral heart bullet (❧)
        "\U00002796"  # heavy minus sign (➖)
        "\U00002797"  # heavy division sign (➗)
        "\U000027A1"  # black rightwards arrow (➡)
        "\U000027B0"  # curly loop (➰)
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended-A
        "\U0000203C"  # double exclamation mark (‼)
        "\U00002049"  # exclamation question mark (⁉)
        "\U0000204A"  # tironian sign et (⁊)
        "\U00002122"  # trade mark sign (™)
        "\U00002139"  # information source (ℹ)
        "\U000021A9"  # leftwards arrow with hook (↩)
        "\U000021AA"  # rightwards arrow with hook (↪)
        "\U0000231A"  # watch (⌚)
        "\U0000231B"  # hourglass (⌛)
        "\U000023E9"  # fast-forward button (⏩)
        "\U000023EA"  # fast reverse button (⏪)
        "\U000023EB"  # fast up button (⏫)
        "\U000023EC"  # fast down button (⏬)
        "\U000023ED"  # next track button (⏭)
        "\U000023EE"  # last track button (⏮)
        "\U000023EF"  # play or pause button (⏯)
        "\U000023F0"  # alarm clock (⏰)
        "\U000023F1"  # stopwatch (⏱)
        "\U000023F2"  # timer clock (⏲)
        "\U000023F3"  # hourglass done (⏳)
        "\U000023F8"  # pause button (⏸)
        "\U000023F9"  # stop button (⏹)
        "\U000023FA"  # record button (⏺)
        "\U000025FD"  # white medium-small square (◽)
        "\U000025FE"  # black medium-small square (◾)
        "\U00002614"  # umbrella with rain drops (☔)
        "\U00002615"  # hot beverage (☕)
        "\U00002648"  # aries (♈)
        "\U00002649"  # taurus (♉)
        "\U0000264A"  # gemini (♊)
        "\U0000264B"  # cancer (♋)
        "\U0000264C"  # leo (♌)
        "\U0000264D"  # virgo (♍)
        "\U0000264E"  # libra (♎)
        "\U0000264F"  # scorpius (♏)
        "\U00002650"  # sagittarius (♐)
        "\U00002651"  # capricorn (♑)
        "\U00002652"  # aquarius (♒)
        "\U00002653"  # pisces (♓)
        "\U0000267F"  # wheelchair symbol (♿)
        "\U00002693"  # anchor (⚓)
        "\U000026A1"  # high voltage (⚡)
        "\U000026AA"  # white circle (⚪)
        "\U000026AB"  # black circle (⚫)
        "\U000026B0"  # coffin (⚰)
        "\U000026B1"  # funeral urn (⚱)
        "\U000026C4"  # snowman without snow (⛄)
        "\U000026C5"  # sun behind cloud (⛅)
        "\U000026CE"  # ophiuchus (⛎)
        "\U000026D4"  # no entry (⛔)
        "\U000026EA"  # church (⛪)
        "\U000026F2"  # fountain (⛲)
        "\U000026F3"  # flag in hole (⛳)
        "\U000026F5"  # sailboat (⛵)
        "\U000026FA"  # tent (⛺)
        "\U000026FD"  # fuel pump (⛽)
        "\U00002705"  # check mark (✅)
        "\U0000270A"  # raised fist (✊)
        "\U0000270B"  # raised hand (✋)
        "\U0000270C"  # victory hand (✌)
        "\U0000270D"  # writing hand (✍)
        "\U0000270F"  # pencil (✏)
        "\U00002712"  # black nib (✒)
        "\U00002714"  # heavy check mark (✔)
        "\U00002716"  # heavy multiplication x (✖)
        "\U0000271D"  # latin cross (✝)
        "\U00002721"  # star of david (✡)
        "\U00002728"  # sparkles (✨)
        "\U00002733"  # eight-spoked asterisk (✳)
        "\U00002734"  # eight-pointed star (✴)
        "\U00002744"  # snowflake (❄)
        "\U00002747"  # sparkle (❇)
        "\U0000274C"  # cross mark (❌)
        "\U0000274E"  # negative squared cross mark (❎)
        "\U00002753"  # question mark ornament (❓)
        "\U00002754"  # white question mark ornament (❔)
        "\U00002755"  # white exclamation mark ornament (❕)
        "\U00002757"  # heavy exclamation mark symbol (❗)
        "\U0000275B"  # heavy left-pointing angle quotation mark ornament (❛)
        "\U0000275C"  # heavy right-pointing angle quotation mark ornament (❜)
        "\U0000275D"  # heavy left-pointing angle quotation mark ornament (❝)
        "\U0000275E"  # heavy right-pointing angle quotation mark ornament (❞)
        "\U00002761"  # heavy heart exclamation mark ornament (❡)
        "\U00002763"  # heavy black heart (❣)
        "\U00002764"  # black heart suit (❤)
        "\U00002765"  # rotated heavy black heart bullet (❥)
        "\U00002766"  # floral heart (❦)
        "\U00002767"  # rotated floral heart bullet (❧)
        "\U00002796"  # heavy minus sign (➖)
        "\U00002797"  # heavy division sign (➗)
        "\U000027A1"  # black rightwards arrow (➡)
        "\U000027B0"  # curly loop (➰)
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended-A
        "\U0000203C"  # double exclamation mark (‼)
        "\U00002049"  # exclamation question mark (⁉)
        "\U0000204A"  # tironian sign et (⁊)
        "\U00002122"  # trade mark sign (™)
        "\U00002139"  # information source (ℹ)
        "\U000021A9"  # leftwards arrow with hook (↩)
        "\U000021AA"  # rightwards arrow with hook (↪)
        "\U0000231A"  # watch (⌚)
        "\U0000231B"  # hourglass (⌛)
        "\U000023E9"  # fast-forward button (⏩)
        "\U000023EA"  # fast reverse button (⏪)
        "\U000023EB"  # fast up button (⏫)
        "\U000023EC"  # fast down button (⏬)
        "\U000023ED"  # next track button (⏭)
        "\U000023EE"  # last track button (⏮)
        "\U000023EF"  # play or pause button (⏯)
        "\U000023F0"  # alarm clock (⏰)
        "\U000023F1"  # stopwatch (⏱)
        "\U000023F2"  # timer clock (⏲)
        "\U000023F3"  # hourglass done (⏳)
        "\U000023F8"  # pause button (⏸)
        "\U000023F9"  # stop button (⏹)
        "\U000023FA"  # record button (⏺)
        "\U000025FD"  # white medium-small square (◽)
        "\U000025FE"  # black medium-small square (◾)
        "\U00002614"  # umbrella with rain drops (☔)
        "\U00002615"  # hot beverage (☕)
        "\U00002648"  # aries (♈)
        "\U00002649"  # taurus (♉)
        "\U0000264A"  # gemini (♊)
        "\U0000264B"  # cancer (♋)
        "\U0000264C"  # leo (♌)
        "\U0000264D"  # virgo (♍)
        "\U0000264E"  # libra (♎)
        "\U0000264F"  # scorpius (♏)
        "\U00002650"  # sagittarius (♐)
        "\U00002651"  # capricorn (♑)
        "\U00002652"  # aquarius (♒)
        "\U00002653"  # pisces (♓)
        "\U0000267F"  # wheelchair symbol (♿)
        "\U00002693"  # anchor (⚓)
        "\U000026A1"  # high voltage (⚡)
        "\U000026AA"  # white circle (⚪)
        "\U000026AB"  # black circle (⚫)
        "\U000026B0"  # coffin (⚰)
        "\U000026B1"  # funeral urn (⚱)
        "\U000026C4"  # snowman without snow (⛄)
        "\U000026C5"  # sun behind cloud (⛅)
        "\U000026CE"  # ophiuchus (⛎)
        "\U000026D4"  # no entry (⛔)
        "\U000026EA"  # church (⛪)
        "\U000026F2"  # fountain (⛲)
        "\U000026F3"  # flag in hole (⛳)
        "\U000026F5"  # sailboat (⛵)
        "\U000026FA"  # tent (⛺)
        "\U000026FD"  # fuel pump (⛽)
        "\U00002705"  # check mark (✅)
        "\U0000270A"  # raised fist (✊)
        "\U0000270B"  # raised hand (✋)
        "\U0000270C"  # victory hand (✌)
        "\U0000270D"  # writing hand (✍)
        "\U0000270F"  # pencil (✏)
        "\U00002712"  # black nib (✒)
        "\U00002714"  # heavy check mark (✔)
        "\U00002716"  # heavy multiplication x (✖)
        "\U0000271D"  # latin cross (✝)
        "\U00002721"  # star of david (✡)
        "\U00002728"  # sparkles (✨)
        "\U00002733"  # eight-spoked asterisk (✳)
        "\U00002734"  # eight-pointed star (✴)
        "\U00002744"  # snowflake (❄)
        "\U00002747"  # sparkle (❇)
        "\U0000274C"  # cross mark (❌)
        "\U0000274E"  # negative squared cross mark (❎)
        "\U00002753"  # question mark ornament (❓)
        "\U00002754"  # white question mark ornament (❔)
        "\U00002755"  # white exclamation mark ornament (❕)
        "\U00002757"  # heavy exclamation mark symbol (❗)
        "\U0000275B"  # heavy left-pointing angle quotation mark ornament (❛)
        "\U0000275C"  # heavy right-pointing angle quotation mark ornament (❜)
        "\U0000275D"  # heavy left-pointing angle quotation mark ornament (❝)
        "\U0000275E"  # heavy right-pointing angle quotation mark ornament (❞)
        "\U00002761"  # heavy heart exclamation mark ornament (❡)
        "\U00002763"  # heavy black heart (❣)
        "\U00002764"  # black heart suit (❤)
        "\U00002765"  # rotated heavy black heart bullet (❥)
        "\U00002766"  # floral heart (❦)
        "\U00002767"  # rotated floral heart bullet (❧)
        "\U00002796"  # heavy minus sign (➖)
        "\U00002797"  # heavy division sign (➗)
        "\U000027A1"  # black rightwards arrow (➡)
        "\U000027B0"  # curly loop (➰)
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text)

def generate_pdf_report():
    """Generar PDF del informe de seguridad con fecha"""
    
    # Rutas
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / "docs"
    informes_dir = docs_dir / "informes"
    report_md = docs_dir / "INFORME_SEGURIDAD.md"
    
    # Crear carpeta de informes si no existe
    informes_dir.mkdir(parents=True, exist_ok=True)
    
    # Verificar que existe el archivo
    if not report_md.exists():
        print(f"❌ Error: No se encontró el archivo {report_md}")
        return 1
    
    # Generar nombre del PDF con fecha
    fecha = datetime.now().strftime("%Y%m%d")
    pdf_name = f"INFORME_SEGURIDAD_{fecha}.pdf"
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
        import tempfile
        
        print("   Método: markdown2pdf")
        
        # Leer el archivo Markdown y eliminar emojis
        with open(report_md, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Eliminar emojis del contenido para el PDF
        md_content = remove_emojis(md_content)
        
        # Crear archivo temporal sin emojis
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(md_content)
            tmp_md_path = tmp_file.name
        
        try:
            convert_md_to_pdf(tmp_md_path, str(pdf_path))
            success = True
            print("   ✅ PDF generado con markdown2pdf")
        finally:
            # Eliminar archivo temporal
            os.unlink(tmp_md_path)
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
            
            # Eliminar emojis del contenido para el PDF
            md_content = remove_emojis(md_content)
            
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
            
            # Eliminar emojis del contenido para el PDF
            md_content = remove_emojis(md_content)
            
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
            
            # Leer el archivo Markdown y eliminar emojis
            with open(report_md, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Eliminar emojis del contenido para el PDF
            md_content = remove_emojis(md_content)
            
            # Crear archivo temporal sin emojis
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(md_content)
                tmp_md_path = tmp_file.name
            
            try:
                result = subprocess.run(
                    ['pandoc', tmp_md_path, '-o', str(pdf_path), '--pdf-engine=xelatex'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            finally:
                # Eliminar archivo temporal
                os.unlink(tmp_md_path)
            
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

