#!/usr/bin/env python3
"""
Script consolidado para gestionar findings de DefectDojo

Este script gestiona el ciclo de vida completo de los findings relacionados con CWE-699:
1. Crea o actualiza todos los findings (CWE-20, CWE-1287, CWE-843, CWE-1021, CWE-703, CWE-942)
   inicialmente como activos (active=True, verified=False)
2. Crea Product Type "Medical Register", Product "Medical Register App", 
   Engagement "CWE-699 Analysis" y Test Type "CWE-699" si no existen
3. Marca findings resueltos (CWE-20 y CWE-1021) con fechas históricas de mitigación
4. Actualiza descripciones y mitigaciones con el estado actual

Este script es llamado por init_defectdojo_internal.py durante la inicialización,
o puede ejecutarse manualmente para actualizar el flujo de findings.

Los findings se crean en el Test Type "CWE-699" (no "Static Analysis").
"""

import os
import sys
import django
from datetime import date

# Configurar Django
sys.path.insert(0, '/app')
os.chdir('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dojo.settings.settings')
django.setup()

from dojo.models import Finding, Test, Engagement, Product, Product_Type, Test_Type, Development_Environment
from django.contrib.auth.models import User

def get_or_create_test_and_engagement():
    """Obtener o crear Test y Engagement necesarios"""
    try:
        # Obtener usuario admin
        admin_user = User.objects.get(username='admin')
        
        # Crear o obtener Product Type
        product_type, _ = Product_Type.objects.get_or_create(
            name='Medical Register',
            defaults={'description': 'Aplicación de registro médico'}
        )
        
        # Crear o obtener Product
        product, _ = Product.objects.get_or_create(
            name='Medical Register App',
            defaults={
                'description': 'Aplicación web para registro de peso e IMC',
                'prod_type': product_type
            }
        )
        
        # Crear o obtener Engagement
        engagement, _ = Engagement.objects.get_or_create(
            name='CWE-699 Analysis',
            product=product,
            defaults={
                'target_start': date(2025, 11, 1),  # 1 de noviembre de 2025
                'target_end': date(2026, 6, 1),    # 1 de junio de 2026
                'status': 'In Progress',
                'lead': admin_user
            }
        )
        
        # Crear o obtener Test Type y Environment
        test_type, _ = Test_Type.objects.get_or_create(name='CWE-699')
        environment, _ = Development_Environment.objects.get_or_create(name='Development')
        
        # Crear o obtener Test
        test, _ = Test.objects.get_or_create(
            engagement=engagement,
            test_type=test_type,
            defaults={
                'target_start': date(2025, 11, 1),  # 1 de noviembre de 2025
                'target_end': date(2026, 6, 1),     # 1 de junio de 2026
                'environment': environment,
                'lead': admin_user
            }
        )
        
        return test, engagement
    except Exception as e:
        print(f"❌ Error obteniendo Test/Engagement: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def create_all_findings(test, admin_user):
    """Crear todos los findings inicialmente como activos"""
    from django.contrib.auth.models import User
    
    if not admin_user:
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            print("❌ Error: Usuario admin no encontrado")
            return {}
    
    if not test:
        print("❌ Error: Test no disponible")
        return {}
    
    print("🔍 Creando/actualizando findings de CWE...")
    
    severity_map = {
        'Low': 'Low',
        'Medium': 'Medium',
        'High': 'High',
        'Critical': 'Critical'
    }
    
    findings_data = {
        'CWE-20': {
            'title': 'CWE-20: Validación de entrada insuficiente (nombres)',
            'description': 'Vulnerabilidad de validación de entrada en campos de nombre. Se requiere implementar validación robusta con sanitización en backend y frontend.\n\nProblema: Falta validación de longitud, eliminación de caracteres peligrosos, y normalización de espacios.\n\nImpacto: Riesgo de inyección de caracteres peligrosos (XSS potencial) y corrupción de datos almacenados.',
            'severity': 'Medium',
            'cwe': 20,
            'active': True,
            'verified': False,
            'mitigation': 'Implementar validación robusta de nombres con sanitización. Validar longitud (1-100 caracteres), eliminar caracteres peligrosos (< > " \'), normalizar espacios múltiples, y validar caracteres permitidos (letras Unicode, espacios, guiones, apóstrofes). Implementar en backend (app/helpers.py) y frontend (app/static/js/config.js) para defensa en profundidad.',
            'impact': 'Puede causar inyección de caracteres peligrosos (XSS potencial) y corrupción de datos almacenados',
            'references': 'https://cwe.mitre.org/data/definitions/20.html',
            'file_path': 'app/helpers.py, app/routes.py, app/static/js/config.js',
            'line': 53,
            'created_date': date(2025, 11, 10)
        },
        'CWE-1287': {
            'title': 'CWE-1287: Validación de tipo insuficiente',
            'description': 'Uso de float() directamente sobre datos de entrada sin validar primero el tipo. Puede lanzar excepciones no controladas o producir valores inesperados (NaN, Infinity).',
            'severity': 'Medium',
            'cwe': 1287,
            'active': True,
            'verified': False,
            'mitigation': 'Validar tipo antes de convertir. Verificar que el resultado sea un número finito después de la conversión.',
            'impact': 'Puede causar errores en cálculos posteriores (IMC) si se envían valores no numéricos o NaN/Infinity',
            'references': 'https://cwe.mitre.org/data/definitions/1287.html',
            'file_path': 'app/routes.py',
            'line': 36,
            'created_date': date(2025, 11, 10)
        },
        'CWE-843': {
            'title': 'CWE-843: Confusión de tipos (NaN no validado)',
            'description': 'Uso de parseFloat() sin validar que el resultado sea un número válido. parseFloat() puede retornar NaN, que luego se propaga en cálculos matemáticos causando resultados incorrectos.',
            'severity': 'Medium',
            'cwe': 843,
            'active': True,
            'verified': False,
            'mitigation': 'Validar NaN e Infinity después de parseFloat() usando isNaN() e isFinite().',
            'impact': 'Puede causar cálculos incorrectos de IMC y errores en validaciones si se introducen valores inválidos',
            'references': 'https://cwe.mitre.org/data/definitions/843.html',
            'file_path': 'app/static/js/main.js, app/static/js/storage.js',
            'line': 139,
            'created_date': date(2025, 11, 10)
        },
        'CWE-1021': {
            'title': 'CWE-1021: Falta de protección contra clickjacking',
            'description': 'No se implementan headers de seguridad (X-Frame-Options, Content-Security-Policy) para prevenir clickjacking. La aplicación es vulnerable a ataques de clickjacking.\n\nProblema: La aplicación puede ser embebida en iframes maliciosos, permitiendo que los usuarios sean engañados para realizar acciones no deseadas mediante superposición de elementos.\n\nUbicación: app/__init__.py',
            'severity': 'Medium',
            'cwe': 1021,
            'active': True,
            'verified': False,
            'mitigation': 'Agregar headers de seguridad en app/__init__.py después de create_app() usando @app.after_request. Implementar X-Frame-Options: DENY, Content-Security-Policy: frame-ancestors \'none\', X-Content-Type-Options: nosniff, y X-XSS-Protection: 1; mode=block.',
            'impact': 'Vulnerabilidad de seguridad conocida. Permite que la aplicación sea embebida en iframes maliciosos, comprometiendo la confidencialidad e integridad de los datos',
            'references': 'https://cwe.mitre.org/data/definitions/1021.html',
            'file_path': 'app/__init__.py',
            'line': 28,
            'created_date': date(2025, 11, 10)
        },
        'CWE-703': {
            'title': 'CWE-703: Manejo de excepciones demasiado genérico',
            'description': 'Uso de Exception genérico en conversiones de float() que puede ocultar errores inesperados. La validación de nombres ya usa manejo estructurado de errores, pero las conversiones numéricas aún usan Exception genérico.',
            'severity': 'Low',
            'cwe': 703,
            'active': True,
            'verified': False,
            'mitigation': 'Especificar excepciones específicas (ValueError, TypeError, KeyError) en lugar de Exception genérico. Agregar logging para debugging.',
            'impact': 'Puede ocultar errores inesperados y dificultar el debugging',
            'references': 'https://cwe.mitre.org/data/definitions/703.html',
            'file_path': 'app/routes.py, app/static/js/sync.js',
            'line': 38,
            'created_date': date(2025, 11, 10)
        },
        'CWE-942': {
            'title': 'CWE-942: CORS demasiado permisivo',
            'description': 'CORS configurado para permitir cualquier origen (origins: \'*\'). Cualquier sitio web puede hacer peticiones a la API. Riesgo de CSRF si se implementa autenticación en el futuro.',
            'severity': 'Medium',
            'cwe': 942,
            'active': True,
            'verified': False,
            'mitigation': 'Restringir CORS a dominios específicos cuando se defina la arquitectura de despliegue final. Actualmente aceptado porque la aplicación es monousuario y no requiere autenticación.',
            'impact': 'Cualquier sitio web puede hacer peticiones a la API. Riesgo de CSRF si se implementa autenticación sin ajustar CORS',
            'references': 'https://cwe.mitre.org/data/definitions/942.html',
            'file_path': 'app/__init__.py',
            'line': 13,
            'created_date': date(2025, 11, 10)
        }
    }
    
    created_findings = {}
    test_type = test.test_type if test else None
    
    for cwe_name, data in findings_data.items():
        try:
            # Eliminar duplicados
            duplicates = list(Finding.objects.filter(cwe=data['cwe'], test=test).order_by('-id'))
            if len(duplicates) > 1:
                to_delete = duplicates[1:]
                Finding.objects.filter(id__in=[f.id for f in to_delete]).delete()
                print(f"  🗑️  {cwe_name}: Eliminados {len(to_delete)} duplicados")
            
            # Buscar o crear finding
            finding = Finding.objects.filter(cwe=data['cwe'], test=test).first()
            
            if not finding:
                finding = Finding.objects.create(
                    title=data['title'],
                    description=data['description'],
                    severity=severity_map.get(data['severity'], 'Medium'),
                    cwe=data['cwe'],
                    active=data['active'],
                    verified=data['verified'],
                    test=test,
                    reporter=admin_user,
                    mitigation=data['mitigation'],
                    impact=data['impact'],
                    references=data['references'],
                    file_path=data['file_path'],
                    line=data.get('line'),
                    date=data.get('created_date', date.today())
                )
                if test_type:
                    finding.found_by.add(test_type)
                print(f"  ✓ {cwe_name} creado (ID: {finding.id})")
            else:
                # Actualizar
                finding.title = data['title']
                finding.description = data['description']
                finding.severity = severity_map.get(data['severity'], 'Medium')
                finding.mitigation = data['mitigation']
                finding.impact = data['impact']
                finding.references = data['references']
                finding.file_path = data['file_path']
                finding.line = data.get('line')
                finding.reporter = admin_user
                if data.get('created_date') and finding.date:
                    if finding.date > data['created_date']:
                        finding.date = data['created_date']
                if test_type:
                    finding.found_by.clear()
                    finding.found_by.add(test_type)
                finding.save()
                print(f"  🔄 {cwe_name} actualizado (ID: {finding.id})")
            
            created_findings[cwe_name] = finding
        except Exception as e:
            print(f"  ✗ Error procesando {cwe_name}: {e}")
            import traceback
            traceback.print_exc()
    
    return created_findings

def mark_resolved_with_dates(findings):
    """Marcar findings resueltos con fechas históricas"""
    if not findings:
        return
    
    print("")
    print("📅 Marcando findings resueltos con fechas históricas...")
    
    resolutions = {
        'CWE-20': {
            'mitigated_date': date(2025, 11, 24),
            'mitigation': '''✅ RESUELTO (2025-11-24): Se implementó la función validate_and_sanitize_name() en app/helpers.py que valida longitud (1-100 caracteres), elimina caracteres peligrosos (< > " '), y normaliza espacios múltiples. Validación también implementada en frontend (app/static/js/config.js) para defensa en profundidad.

Implementación:
- Backend: app/helpers.py - Función validate_and_sanitize_name()
- Frontend: app/static/js/config.js - Función validateAndSanitizeName()
- Validación en: app/routes.py líneas 69-87

Ubicación: app/helpers.py, app/routes.py, app/static/js/config.js''',
            'description': '''Vulnerabilidad de validación de entrada en campos de nombre - RESUELTA.

ESTADO: ✅ RESUELTO el 2025-11-24

Se implementó validación robusta con sanitización en backend y frontend:
- Validación de longitud (1-100 caracteres)
- Eliminación de caracteres peligrosos (< > " ')
- Normalización de espacios múltiples
- Validación de caracteres permitidos (letras Unicode, espacios, guiones, apóstrofes)
- Defensa en profundidad (validación en backend y frontend)

Ubicación: app/helpers.py, app/routes.py, app/static/js/config.js'''
        },
        'CWE-1021': {
            'mitigated_date': date(2025, 11, 24),
            'mitigation': '''✅ RESUELTO (2025-11-24): Se implementaron headers de seguridad en app/__init__.py usando @app.after_request que agrega los siguientes headers a todas las respuestas HTTP:

- X-Frame-Options: DENY
- Content-Security-Policy: frame-ancestors 'none'
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block

Estos headers previenen que la aplicación sea embebida en iframes maliciosos y protegen contra ataques de clickjacking.

Ubicación: app/__init__.py líneas 28-36''',
            'description': '''Vulnerabilidad de clickjacking - RESUELTA.

ESTADO: ✅ RESUELTO el 2025-11-24

Se implementaron headers de seguridad que previenen la inclusión de la aplicación en iframes maliciosos:
- X-Frame-Options: DENY
- Content-Security-Policy: frame-ancestors 'none'
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block

Ubicación: app/__init__.py líneas 28-36'''
        }
    }
    
    for cwe_name, resolution_data in resolutions.items():
        if cwe_name in findings:
            try:
                finding = findings[cwe_name]
                finding.active = False
                finding.verified = True
                finding.mitigated_date = resolution_data['mitigated_date']
                finding.mitigation = resolution_data['mitigation']
                finding.description = resolution_data['description']
                finding.save()
                print(f"  ✅ {cwe_name}: Marcado como resuelto (fecha: {resolution_data['mitigated_date']})")
            except Exception as e:
                print(f"  ❌ {cwe_name}: Error al marcar como resuelto - {e}")

def main():
    """Función principal"""
    print("=" * 60)
    print("Gestión Consolidada de Findings de DefectDojo")
    print("=" * 60)
    print()
    
    try:
        # Obtener Test y Engagement
        test, engagement = get_or_create_test_and_engagement()
        if not test:
            print("❌ Error: No se pudo obtener Test/Engagement")
            return 1
        
        # Obtener usuario admin
        from django.contrib.auth.models import User
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            print("❌ Error: Usuario admin no encontrado")
            return 1
        
        # Crear todos los findings
        print()
        findings = create_all_findings(test, admin_user)
        
        if not findings:
            print("⚠️  No se crearon findings")
            return 1
        
        # Marcar findings resueltos con fechas
        mark_resolved_with_dates(findings)
        
        print()
        print("=" * 60)
        print("✅ Gestión de findings completada")
        print("=" * 60)
        print()
        print("Resumen:")
        print("  ✓ CWE-20: Resuelto (2025-11-24)")
        print("  ✓ CWE-1021: Resuelto (2025-11-24)")
        print("  ⚠️  CWE-1287: Pendiente")
        print("  ⚠️  CWE-843: Pendiente")
        print("  ⚠️  CWE-703: Pendiente")
        print("  ⏸️  CWE-942: Aceptado temporalmente")
        print()
        
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

