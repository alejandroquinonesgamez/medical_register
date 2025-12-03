#!/usr/bin/env python3
"""
Script para generar imágenes PNG desde archivos Mermaid (.mmd)

Convierte diagramas Mermaid (.mmd) a imágenes PNG usando la API pública de mermaid.ink.
No requiere instalación local de Node.js ni Mermaid CLI.

Uso:
    python scripts/generate_mermaid_image.py <archivo.mmd> [archivo.png]

Ejemplo:
    python scripts/generate_mermaid_image.py docs/mockups/user-manual.mmd

Si no se especifica la ruta de salida, usa el mismo nombre del archivo con extensión .png.
"""

import os
import sys
import base64
import urllib.request
import urllib.error
from pathlib import Path

def generate_mermaid_image(mmd_file_path, output_png_path=None):
    """
    Genera una imagen PNG desde un archivo Mermaid
    
    Args:
        mmd_file_path: Ruta al archivo .mmd
        output_png_path: Ruta donde guardar el PNG (opcional, por defecto mismo nombre con .png)
    """
    
    # Leer el archivo Mermaid
    mmd_path = Path(mmd_file_path)
    if not mmd_path.exists():
        print(f"❌ Error: No se encontró el archivo {mmd_file_path}")
        return 1
    
    with open(mmd_path, 'r', encoding='utf-8') as f:
        mermaid_code = f.read().strip()
    
    # Si no se especifica la ruta de salida, usar el mismo nombre con extensión .png
    if output_png_path is None:
        output_png_path = mmd_path.with_suffix('.png')
    else:
        output_png_path = Path(output_png_path)
    
    print(f"📊 Generando imagen desde: {mmd_path}")
    print(f"   Guardando en: {output_png_path}")
    print()
    
    # Codificar el código Mermaid en base64 para la API
    # La API de mermaid.ink espera el código Mermaid codificado en base64
    mermaid_base64 = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
    
    # URL de la API de mermaid.ink
    api_url = f"https://mermaid.ink/img/{mermaid_base64}"
    
    try:
        print("⏳ Conectando con mermaid.ink para generar la imagen...")
        
        # Descargar la imagen usando urllib
        with urllib.request.urlopen(api_url, timeout=30) as response:
            if response.status == 200:
                # Guardar la imagen
                with open(output_png_path, 'wb') as f:
                    f.write(response.read())
                
                print(f"✅ Imagen generada exitosamente: {output_png_path}")
                return 0
            else:
                print(f"❌ Error: La API devolvió el código {response.status}")
                return 1
            
    except urllib.error.HTTPError as e:
        print(f"❌ Error HTTP: {e.code} - {e.reason}")
        return 1
    except urllib.error.URLError as e:
        print(f"❌ Error al conectar con la API: {e}")
        print()
        print("💡 Soluciones:")
        print("   1. Verifica tu conexión a Internet")
        print("   2. Verifica que el código Mermaid sea válido")
        return 1
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python generate_mermaid_image.py <archivo.mmd> [archivo.png]")
        print()
        print("Ejemplo:")
        print("  python generate_mermaid_image.py docs/mockups/user-manual.mmd")
        print("  python generate_mermaid_image.py docs/mockups/user-manual.mmd docs/mockups/user-manual.png")
        return 1
    
    mmd_file = sys.argv[1]
    png_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    return generate_mermaid_image(mmd_file, png_file)


if __name__ == '__main__':
    sys.exit(main())

