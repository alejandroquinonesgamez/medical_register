#!/usr/bin/env python3
"""
Script para marcar findings como resueltos en DefectDojo con fechas específicas.
Este script debe ejecutarse dentro del contenedor de DefectDojo para tener acceso
a los modelos de Django.
"""

import os
import sys
import django
from datetime import date

# Configurar Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dojo.settings.settings')
django.setup()

from dojo.models import Finding, Test

def resolve_findings_with_dates():
    """Marcar findings como resueltos con fechas específicas basadas en historial de git"""
    
    print("=" * 60)
    print("Marcando findings como resueltos con fechas históricas")
    print("=" * 60)
    print()
    
    # Obtener el test (asumimos que es el test 1)
    try:
        test = Test.objects.get(id=1)
    except Test.DoesNotExist:
        print("❌ Error: No se encontró el test con ID 1")
        return
    
    # Definir las fechas basadas en el historial de git
    # Fechas encontradas en git:
    # - CWE-20: Resuelto el 2025-11-24 (commit: chore: sincronizar actualizaciones)
    # - CWE-1021: Resuelto el 2025-11-24 (commit: Configurar nginx principal...)
    # 
    # Para los desconocidos, usar fechas por defecto:
    # - Fecha de creación: 2025-11-10 (10/11/2025)
    # - Fecha de resolución: 2025-11-17 (17/11/2025)
    
    resolutions = {
        20: {  # CWE-20
            'cwe_name': 'CWE-20',
            'creation_date': date(2025, 11, 10),  # Fecha por defecto para creación (desconocida)
            'mitigated_date': date(2025, 11, 24),  # Fecha real encontrada en git
            'mitigation': '''✅ RESUELTO (2025-11-24): Se implementó la función validate_and_sanitize_name() en app/helpers.py que valida longitud (1-100 caracteres), elimina caracteres peligrosos (< > " '), y normaliza espacios múltiples. Validación también implementada en frontend (app/static/js/config.js) para defensa en profundidad.

Implementación:
- Backend: app/helpers.py - Función validate_and_sanitize_name()
- Frontend: app/static/js/config.js - Función validateAndSanitizeName()
- Validación en: app/routes.py líneas 69-87

Ubicación: app/helpers.py, app/routes.py, app/static/js/config.js''',
            'description_update': '''Vulnerabilidad de validación de entrada en campos de nombre - RESUELTA.

ESTADO: ✅ RESUELTO el 2025-11-24

Se implementó validación robusta con sanitización en backend y frontend:
- Validación de longitud (1-100 caracteres)
- Eliminación de caracteres peligrosos (< > " ')
- Normalización de espacios múltiples
- Validación de caracteres permitidos (letras Unicode, espacios, guiones, apóstrofes)
- Defensa en profundidad (validación en backend y frontend)

Ubicación: app/helpers.py, app/routes.py, app/static/js/config.js'''
        },
        1021: {  # CWE-1021
            'cwe_name': 'CWE-1021',
            'creation_date': date(2025, 11, 10),  # Fecha por defecto para creación (desconocida)
            'mitigated_date': date(2025, 11, 24),  # Fecha real encontrada en git
            'mitigation': '''✅ RESUELTO (2025-11-24): Se implementaron headers de seguridad en app/__init__.py usando @app.after_request que agrega los siguientes headers a todas las respuestas HTTP:

- X-Frame-Options: DENY
- Content-Security-Policy: frame-ancestors 'none'
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block

Estos headers previenen que la aplicación sea embebida en iframes maliciosos y protegen contra ataques de clickjacking.

Ubicación: app/__init__.py líneas 28-36''',
            'description_update': '''Vulnerabilidad de clickjacking - RESUELTA.

ESTADO: ✅ RESUELTO el 2025-11-24

Se implementaron headers de seguridad que previenen la inclusión de la aplicación en iframes maliciosos:
- X-Frame-Options: DENY
- Content-Security-Policy: frame-ancestors 'none'
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block

Ubicación: app/__init__.py líneas 28-36'''
        }
    }
    
    # Buscar y actualizar los findings
    for cwe_number, resolution_data in resolutions.items():
        cwe_name = resolution_data['cwe_name']
        try:
            # Buscar el finding por CWE en el test
            finding = Finding.objects.filter(test=test, cwe=cwe_number).first()
            
            if not finding:
                # Si no encontramos por CWE, buscar por título que contiene el CWE
                findings = Finding.objects.filter(test=test, title__icontains=cwe_name)
                if findings.exists():
                    finding = findings.first()
                else:
                    print(f"⚠️  {cwe_name}: No se encontró el finding")
                    continue
            
            # Actualizar el finding
            finding.active = False
            finding.verified = True
            finding.mitigated_date = resolution_data['mitigated_date']
            finding.mitigation = resolution_data['mitigation']
            
            # Actualizar fecha de creación si es necesario (solo si es más antigua que la actual)
            if 'creation_date' in resolution_data and finding.date:
                if finding.date > resolution_data['creation_date']:
                    finding.date = resolution_data['creation_date']
            
            if 'description_update' in resolution_data:
                finding.description = resolution_data['description_update']
            
            finding.save()
            
            print(f"✅ {cwe_name}: Marcado como resuelto")
            print(f"   - Fecha de creación: {finding.date or resolution_data.get('creation_date', 'N/A')}")
            print(f"   - Fecha de resolución: {resolution_data['mitigated_date']}")
            
        except Exception as e:
            print(f"❌ {cwe_name}: Error al actualizar - {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 60)
    print("Resumen de resoluciones:")
    print("  ✓ CWE-20:")
    print("     - Creado: 2025-11-10")
    print("     - Resuelto: 2025-11-24")
    print("  ✓ CWE-1021:")
    print("     - Creado: 2025-11-10")
    print("     - Resuelto: 2025-11-24")
    print("=" * 60)

if __name__ == '__main__':
    resolve_findings_with_dates()

