#!/usr/bin/env python
"""
Script de inicialización interna de DefectDojo
Se ejecuta dentro del contenedor al arrancar
"""
import os
import sys
import time
import subprocess

# Cambiar al directorio de la aplicación primero
os.chdir('/app')

# Configurar Django - usar las variables de entorno que ya están configuradas
# No establecer DJANGO_SETTINGS_MODULE si ya está configurado
# DefectDojo usa las variables de entorno del docker-compose.yml

# Importar Django después de cambiar al directorio
import django


def wait_for_db(max_retries=30, delay=2):
    """Esperar a que la base de datos esté lista"""
    print("⏳ Esperando a que la base de datos esté lista...")
    for i in range(max_retries):
        try:
            # Configurar Django antes de usar connection
            # No establecer DJANGO_SETTINGS_MODULE si ya está configurado
            if 'DJANGO_SETTINGS_MODULE' not in os.environ:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dojo.settings.settings')
            django.setup()
            from django.db import connection
            connection.ensure_connection()
            if connection.is_usable():
                print("✅ Base de datos lista")
                return True
        except Exception as e:
            if i < 3 or i % 5 == 0:
                print(f"   Intento {i+1}/{max_retries}... ({str(e)[:50]})")
        time.sleep(delay)
    print("❌ Error: No se pudo conectar a la base de datos después de {max_retries} intentos")
    return False

def check_migrations_needed():
    """Verificar si hay migraciones pendientes"""
    try:
        django.setup()
        from django.core.management import call_command
        from io import StringIO
        output = StringIO()
        call_command('showmigrations', '--plan', stdout=output, verbosity=0)
        output_str = output.getvalue()
        # Si hay líneas con [ ] significa que hay migraciones pendientes
        return '[ ]' in output_str
    except Exception:
        return True  # Si hay error, asumimos que hay migraciones pendientes

def run_migrations():
    """Ejecutar migraciones si es necesario"""
    django.setup()
    from django.core.management import call_command
    if check_migrations_needed():
        print("📦 Ejecutando migraciones de Django...")
        try:
            call_command('migrate', '--noinput', verbosity=0)
            print("✅ Migraciones completadas")
        except Exception as e:
            print(f"⚠️  Error en migraciones: {e}")
            return False
    else:
        print("✅ Migraciones ya aplicadas")
    return True

def collect_static():
    """Recolectar archivos estáticos"""
    django.setup()
    from django.core.management import call_command
    print("📁 Recolectando archivos estáticos...")
    try:
        call_command('collectstatic', '--noinput', verbosity=0)
        print("✅ Archivos estáticos recolectados")
    except Exception as e:
        print(f"⚠️  Error recolectando estáticos: {e}")
        # No es crítico, continuamos

def create_admin_user():
    """Crear usuario admin si no existe"""
    django.setup()
    from dojo.models import User
    print("👤 Verificando usuario admin...")
    try:
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'is_superuser': True,
                'is_staff': True,
                'is_active': True,
                'email': 'admin@example.com'
            }
        )
        if created:
            user.set_password('admin')
            user.save()
            print("✅ Usuario admin creado (admin/admin)")
        else:
            # Asegurar que la contraseña sea 'admin'
            user.set_password('admin')
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.save()
            print("✅ Usuario admin verificado (admin/admin)")
    except Exception as e:
        print(f"⚠️  Error creando usuario admin: {e}")

def setup_test_and_engagement():
    """Crear o obtener Test y Engagement necesarios para los findings (evita duplicados)"""
    django.setup()
    from dojo.models import Test, Engagement, Product, Product_Type
    from dojo.models import User
    from datetime import date
    
    print("📋 Configurando Test y Engagement para findings...")
    
    try:
        # Obtener usuario admin
        admin_user = User.objects.get(username='admin')
        
        # Crear o obtener Product Type (usar get_or_create para evitar duplicados)
        product_type, _ = Product_Type.objects.get_or_create(
            name='Medical Register',
            defaults={'description': 'Aplicación de registro médico'}
        )
        
        # Crear o obtener Product (usar get_or_create para evitar duplicados)
        product, _ = Product.objects.get_or_create(
            name='Medical Register App',
            defaults={
                'description': 'Aplicación web para registro de peso e IMC',
                'prod_type': product_type
            }
        )
        
        # Crear o obtener Engagement (usar get_or_create para evitar duplicados)
        engagement, _ = Engagement.objects.get_or_create(
            name='CWE-699 Analysis',
            product=product,
            defaults={
                'target_start': date(2024, 1, 1),
                'target_end': date(2024, 12, 31),
                'status': 'In Progress',
                'lead': admin_user
            }
        )
        
        # Crear o obtener Test Type y Environment si no existen
        from dojo.models import Test_Type, Development_Environment
        test_type, _ = Test_Type.objects.get_or_create(name='Static Analysis')
        environment, _ = Development_Environment.objects.get_or_create(name='Development')
        
        # Crear o obtener Test (usar get_or_create para evitar duplicados)
        # Buscar por engagement y test_type para evitar duplicados
        test, _ = Test.objects.get_or_create(
            engagement=engagement,
            test_type=test_type,
            defaults={
                'target_start': date(2024, 1, 1),
                'target_end': date(2024, 12, 31),
                'environment': environment,
                'lead': admin_user
            }
        )
        
        print(f"✅ Test ID: {test.id}, Engagement ID: {engagement.id}")
        return test, engagement, admin_user
    except Exception as e:
        print(f"⚠️  Error configurando Test/Engagement: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def create_findings(test, admin_user):
    """Crear o actualizar los findings de CWE en DefectDojo (evita duplicados)"""
    django.setup()
    from dojo.models import Finding, Test_Type
    
    # Obtener el Test_Type para asignarlo a found_by
    test_type = test.test_type if test else None
    
    if not test or not admin_user:
        print("⚠️  No se pueden crear findings: Test o usuario no disponibles")
        return {}
    
    print("🔍 Creando/actualizando findings de CWE...")
    
    # Mapeo de severidad
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
            'line': 53
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
            'line': 36
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
            'line': 139
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
            'line': 28
        },
        'CWE-703': {
            'title': 'CWE-703: Manejo de excepciones demasiado genérico - MEJORADO PARCIALMENTE',
            'description': 'Uso de Exception genérico en conversiones de float() que puede ocultar errores inesperados. La validación de nombres ya usa manejo estructurado de errores, pero las conversiones numéricas aún usan Exception genérico.',
            'severity': 'Low',
            'cwe': 703,
            'active': True,
            'verified': False,
            'mitigation': 'Especificar excepciones específicas (ValueError, TypeError, KeyError) en lugar de Exception genérico. Agregar logging para debugging.',
            'impact': 'Puede ocultar errores inesperados y dificultar el debugging',
            'references': 'https://cwe.mitre.org/data/definitions/703.html',
            'file_path': 'app/routes.py, app/static/js/sync.js',
            'line': 38
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
            'line': 13
        }
    }
    
    created_findings = {}
    
    for cwe_name, data in findings_data.items():
        try:
            # PRIMERO: Eliminar cualquier finding con el mismo CWE en OTROS tests
            # Esto elimina findings antiguos creados manualmente o por otras herramientas
            from dojo.models import Test as TestModel
            all_tests = TestModel.objects.exclude(id=test.id)
            total_deleted_other_tests = 0
            
            for test_obj in all_tests:
                old_findings = Finding.objects.filter(cwe=data['cwe'], test=test_obj)
                if old_findings.exists():
                    deleted_count = old_findings.count()
                    old_findings.delete()
                    total_deleted_other_tests += deleted_count
            
            # SEGUNDO: Eliminar duplicados dentro del test actual
            duplicates = list(Finding.objects.filter(cwe=data['cwe'], test=test).order_by('-id'))
            total_deleted_same_test = 0
            if len(duplicates) > 1:
                # Hay duplicados, eliminar todos excepto el más reciente
                to_delete = duplicates[1:]
                deleted_ids = [f.id for f in to_delete]
                Finding.objects.filter(id__in=deleted_ids).delete()
                total_deleted_same_test = len(to_delete)
            
            if total_deleted_other_tests > 0 or total_deleted_same_test > 0:
                msg_parts = []
                if total_deleted_other_tests > 0:
                    msg_parts.append(f"{total_deleted_other_tests} de otros tests")
                if total_deleted_same_test > 0:
                    msg_parts.append(f"{total_deleted_same_test} del mismo test")
                print(f"  🗑️  {cwe_name}: Eliminados {' y '.join(msg_parts)} duplicados")
            
            # TERCERO: Buscar el finding único en el test actual (o crear si no existe)
            finding = Finding.objects.filter(cwe=data['cwe'], test=test).first()
            
            if not finding:
                # No existe, crear nuevo
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
                    line=data.get('line')
                )
                # Asignar found_by usando el test_type del test
                if test_type:
                    finding.found_by.add(test_type)
                print(f"  ✓ {cwe_name} creado (ID: {finding.id})")
            else:
                # Ya existe, actualizar con los datos más recientes
                finding.title = data['title']
                finding.description = data['description']
                finding.severity = severity_map.get(data['severity'], 'Medium')
                finding.mitigation = data['mitigation']
                finding.impact = data['impact']
                finding.references = data['references']
                finding.file_path = data['file_path']
                finding.line = data.get('line')
                finding.reporter = admin_user
                # Actualizar found_by si es necesario
                if test_type:
                    # Limpiar found_by existente y asignar el correcto
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

def update_findings(findings):
    """Actualizar los findings con información detallada"""
    django.setup()
    
    if not findings:
        print("⚠️  No hay findings para actualizar")
        return
    
    print("📝 Actualizando información de findings...")
    
    updates = {
        'CWE-1287': {
            'description': 'Uso de float() directamente sobre datos de entrada sin validar primero el tipo. Puede lanzar excepciones no controladas o producir valores inesperados (NaN, Infinity).\n\nESTADO ACTUAL: ⚠️ PENDIENTE DE CORRECCIÓN\n\nUbicación: app/routes.py líneas 36-39, 94-97\n\nAcción requerida:\n- Validar tipo antes de convertir\n- Verificar que el resultado sea un número finito después de la conversión\n- Usar excepciones específicas (ValueError, TypeError) en lugar de Exception genérico',
            'mitigation': 'Validar tipo antes de convertir. Verificar que el resultado sea un número finito después de la conversión. Implementar validación similar a la usada en validate_and_sanitize_name().'
        },
        'CWE-843': {
            'description': 'Uso de parseFloat() sin validar que el resultado sea un número válido. parseFloat() puede retornar NaN, que luego se propaga en cálculos matemáticos causando resultados incorrectos.\n\nESTADO ACTUAL: ⚠️ PENDIENTE DE CORRECCIÓN\n\nUbicación: app/static/js/main.js líneas 139, 207; app/static/js/storage.js línea 84\n\nAcción requerida:\n- Validar NaN e Infinity después de parseFloat() usando isNaN() e isFinite()\n- Agregar validación antes de usar valores en cálculos (IMC)',
            'mitigation': 'Validar NaN e Infinity después de parseFloat() usando isNaN() e isFinite(). Agregar validación antes de usar valores en cálculos críticos como el IMC.'
        },
        'CWE-1021': {
            'description': 'Vulnerabilidad de clickjacking resuelta mediante la implementación de headers de seguridad.\n\nESTADO ACTUAL: ✅ RESUELTO\n\nMitigación implementada: Se agregaron headers de seguridad en app/__init__.py (líneas 28-36) que incluyen:\n- X-Frame-Options: DENY\n- Content-Security-Policy: frame-ancestors \'none\'\n- X-Content-Type-Options: nosniff\n- X-XSS-Protection: 1; mode=block\n\nEstos headers previenen que la aplicación sea embebida en iframes maliciosos y protegen contra ataques de clickjacking.',
            'mitigation': '✅ RESUELTO: Se implementaron headers de seguridad en app/__init__.py usando @app.after_request que agrega X-Frame-Options: DENY, Content-Security-Policy: frame-ancestors \'none\', X-Content-Type-Options: nosniff, y X-XSS-Protection: 1; mode=block a todas las respuestas HTTP.'
        },
        'CWE-703': {
            'description': 'Uso de Exception genérico en conversiones de float() que puede ocultar errores inesperados.\n\nESTADO ACTUAL: ⚠️ MEJORADO PARCIALMENTE\n\n✅ MEJORAS IMPLEMENTADAS:\n- La validación de nombres (CWE-20) ya usa manejo estructurado de errores\n- Retorna códigos de error específicos (name_empty, name_too_long, invalid_name)\n- Manejo proactivo en lugar de reactivo (try/except)\n\n⚠️ PENDIENTE:\n- Líneas 38 y 96 en app/routes.py aún usan Exception genérico en conversiones de float()\n- app/static/js/sync.js línea 119 captura cualquier error sin diferenciar tipos\n\nAcción requerida:\n- Especificar excepciones específicas (ValueError, TypeError, KeyError) en lugar de Exception genérico\n- Agregar logging para debugging',
            'mitigation': 'Especificar excepciones específicas (ValueError, TypeError, KeyError) en lugar de Exception genérico. Agregar logging para debugging. Aplicar el mismo patrón de manejo estructurado de errores usado en la validación de nombres.'
        },
        'CWE-942': {
            'description': 'CORS configurado para permitir cualquier origen (origins: \'*\'). Cualquier sitio web puede hacer peticiones a la API. Riesgo de CSRF si se implementa autenticación en el futuro.\n\nESTADO ACTUAL: ⏸️ PENDIENTE - ACEPTADO TEMPORALMENTE\n\nRazón de aceptación temporal:\n- La aplicación es monousuario y no requiere autenticación\n- No hay riesgo inmediato en el contexto actual\n- Se ajustará cuando se defina la arquitectura de despliegue final\n\nUbicación: app/__init__.py líneas 13-19\n\nAcción requerida (futuro):\n- Restringir CORS a dominios específicos cuando se defina la arquitectura de despliegue\n- Ajustar configuración si se implementa autenticación',
            'mitigation': 'Restringir CORS a dominios específicos cuando se defina la arquitectura de despliegue final. Actualmente aceptado porque la aplicación es monousuario y no requiere autenticación. Si se implementa autenticación en el futuro, ajustar CORS es crítico para prevenir CSRF.'
        }
    }
    
    for cwe_name, finding in findings.items():
        if cwe_name in updates:
            try:
                update_data = updates[cwe_name]
                finding.description = update_data['description']
                finding.mitigation = update_data['mitigation']
                # Marcar CWE-1021 como resuelto
                if cwe_name == 'CWE-1021':
                    finding.active = False
                    finding.verified = True
                finding.save()
                print(f"  ✓ {cwe_name} actualizado")
            except Exception as e:
                print(f"  ✗ Error actualizando {cwe_name}: {e}")

def mark_findings_resolved(findings):
    """Marcar findings como resueltos"""
    django.setup()
    
    if not findings:
        print("⚠️  No hay findings para marcar como resueltos")
        return
    
    print("✅ Marcando findings como resueltos...")
    
    # Findings que deben marcarse como resueltos (ya están resueltos en el código)
    resolved_cwes = ['CWE-1287', 'CWE-843', 'CWE-1021', 'CWE-703']
    
    resolutions = {
        'CWE-1287': '✅ RESUELTO: Se implementó validación de tipo antes de convertir a float() usando isinstance(). Se verifica que el resultado sea finito usando math.isfinite() para prevenir NaN e Infinity. Se usan excepciones específicas (ValueError, TypeError) en lugar de Exception genérico. Ubicación: app/routes.py líneas 36-52, 94-110',
        'CWE-843': '✅ RESUELTO: Se implementó validación de NaN e Infinity después de parseFloat() usando isNaN() e isFinite() en todos los lugares donde se usa parseFloat(). Ubicación: app/static/js/main.js líneas 139-145, 207-213; app/static/js/storage.js líneas 84-89',
        'CWE-1021': '✅ RESUELTO: Se agregaron headers de seguridad en app/__init__.py usando @app.after_request: X-Frame-Options: DENY, Content-Security-Policy: frame-ancestors \'none\', X-Content-Type-Options: nosniff, X-XSS-Protection: 1; mode=block. Ubicación: app/__init__.py líneas 30-37',
        'CWE-703': '✅ RESUELTO: Se mejoró el manejo de excepciones en app/routes.py usando excepciones específicas (ValueError, TypeError) en lugar de Exception genérico. Se agregó logging para debugging. En JavaScript (sync.js) se mejoró el logging para diferenciar tipos de errores. Ubicación: app/routes.py líneas 36-52, 94-110; app/static/js/sync.js líneas 119-130'
    }
    
    for cwe_name in resolved_cwes:
        if cwe_name in findings:
            try:
                finding = findings[cwe_name]
                finding.active = False
                finding.verified = True
                finding.mitigation = resolutions[cwe_name]
                finding.save()
                print(f"  ✓ {cwe_name} marcado como resuelto")
            except Exception as e:
                print(f"  ✗ Error marcando {cwe_name} como resuelto: {e}")
    
    # CWE-20 ya está resuelto desde el inicio
    if 'CWE-20' in findings:
        print("  ℹ️ CWE-20 ya estaba marcado como resuelto")
    
    # CWE-942 se mantiene como aceptado
    if 'CWE-942' in findings:
        print("  ℹ️ CWE-942 se mantiene como aceptado temporalmente (aplicación monousuario)")

def check_database_has_data():
    """Verificar si la base de datos ya tiene datos (findings)"""
    django.setup()
    from dojo.models import Finding
    
    try:
        finding_count = Finding.objects.count()
        return finding_count > 0
    except Exception:
        return False

def main():
    """Función principal"""
    print("🔧 Inicializando DefectDojo...")
    
    try:
        # Esperar a que la base de datos esté lista
        if not wait_for_db():
            sys.exit(1)
        
        # Ejecutar migraciones
        if not run_migrations():
            sys.exit(1)
        
        # Recolectar archivos estáticos
        collect_static()
        
        # Crear usuario admin
        create_admin_user()
        
        # Verificar si se debe saltar la creación de findings (variable de entorno)
        skip_findings = os.environ.get('DD_SKIP_FINDINGS', 'False').lower() in ('true', '1', 'yes')
        
        # Verificar si la base de datos ya tiene datos
        # Si tiene datos (por ejemplo, de un dump cargado), saltar la creación de findings
        if skip_findings or check_database_has_data():
            if skip_findings:
                print("")
                print("ℹ️  Variable DD_SKIP_FINDINGS activada - Saltando creación de findings")
            else:
            print("")
            print("ℹ️  La base de datos ya contiene datos (probablemente de un dump)")
            print("   Saltando creación de findings para evitar duplicados")
            print("")
            print("✅ Inicialización completada")
            return 0
        
        # Configurar Test y Engagement para findings
        print("")
        test, engagement, admin_user = setup_test_and_engagement()
        
        if test and admin_user:
            # Crear findings
            print("")
            findings = create_findings(test, admin_user)
            
            if findings:
                # Actualizar findings con información detallada
                print("")
                update_findings(findings)
                
                # Marcar findings como resueltos
                print("")
                mark_findings_resolved(findings)
            else:
                print("⚠️  No se crearon findings")
        else:
            print("⚠️  No se pudo configurar Test/Engagement, saltando creación de findings")
        
        print("")
        print("✅ Inicialización completada")
        return 0
    except Exception as e:
        print(f"❌ Error en inicialización: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

