#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descargar y parsear la estructura completa del ASVS 4.0.3 desde GitHub
"""

import re
import json
import urllib.request
from pathlib import Path
from typing import Dict, List

ASVS_403_FILES = {
    'V1': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x12-V1-Architecture.md',
    'V2': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x13-V2-Authentication.md',
    'V3': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x14-V3-Session-Management.md',
    'V4': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x15-V4-Access-Control.md',
    'V5': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x16-V5-Validation-Sanitization-Encoding.md',
    'V6': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x17-V6-Cryptography-At-Rest.md',
    'V7': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x18-V7-Error-Logging.md',
    'V8': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x19-V8-Data-Protection.md',
    'V9': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x1A-V9-Communications.md',
    'V10': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x1B-V10-Malicious.md',
    'V11': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x1C-V11-Business-Logic.md',
    'V12': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x1D-V12-Files-Resources.md',
    'V13': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x1E-V13-API.md',
    'V14': 'https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/en/0x1F-V14-Configuration.md',
}

def download_and_parse_asvs():
    """Descargar y parsear la estructura completa del ASVS 4.0.3"""
    structure = {}
    
    for category, url in ASVS_403_FILES.items():
        print(f"Descargando {category}...")
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                content = response.read().decode('utf-8')
            
            # Parsear requisitos
            requirements = parse_requirements(content, category)
            structure[category] = requirements
            
            print(f"  ✓ {category}: {len(requirements)} requisitos encontrados")
        except Exception as e:
            print(f"  ✗ Error descargando {category}: {e}")
    
    return structure

def parse_requirements(content: str, category: str) -> Dict:
    """Parsear requisitos del contenido Markdown"""
    requirements = {}
    
    # Buscar patrones de requisitos (ej: V5.1.1, V5.1.2, etc.)
    # Patrón: V\d+\.\d+\.\d+ seguido de descripción
    pattern = r'(V\d+\.\d+\.\d+)\s*[:\-]?\s*(.+?)(?=\nV\d+\.\d+\.\d+|\n\n|$)'
    
    matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        req_id = match.group(1)
        description = match.group(2).strip()
        
        # Limpiar descripción
        description = re.sub(r'\n+', ' ', description)
        description = re.sub(r'\s+', ' ', description)
        description = description.strip()
        
        if description:
            requirements[req_id] = description
    
    return requirements

if __name__ == '__main__':
    structure = download_and_parse_asvs()
    
    # Guardar estructura
    output_file = Path(__file__).parent / 'asvs_403_structure.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Estructura guardada en: {output_file}")
