#!/usr/bin/env python
"""
Script de inicialización de DefectDojo SIN crear findings
Se ejecuta dentro del contenedor para inicializar DefectDojo vacío
"""
import os
import sys
import time

# Cambiar al directorio de la aplicación primero
os.chdir('/app')

# Configurar Django
import django

def wait_for_db(max_retries=30, delay=2):
    """Esperar a que la base de datos esté lista"""
    print("⏳ Esperando a que la base de datos esté lista...")
    for i in range(max_retries):
        try:
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
    print(f"❌ Error: No se pudo conectar a la base de datos después de {max_retries} intentos")
    return False

def check_migrations_needed():
    """Verificar si hay migraciones pendientes"""
    try:
        django.setup()
        from django.core.management import call_command
        from io import StringIO
        
        output = StringIO()
        call_command('showmigrations', '--list', stdout=output, no_color=True)
        output_str = output.getvalue()
        
        # Si hay alguna migración sin [X], hay migraciones pendientes
        lines = output_str.split('\n')
        for line in lines:
            if line.strip() and not line.strip().startswith('['):
                continue
            if '[ ]' in line:
                return True
        return False
    except Exception as e:
        print(f"⚠️  Error verificando migraciones: {e}")
        return True  # Asumir que hay migraciones pendientes por seguridad

def run_migrations():
    """Ejecutar migraciones de Django"""
    try:
        django.setup()
        from django.core.management import call_command
        
        print("📦 Ejecutando migraciones de Django...")
        call_command('migrate', '--noinput', verbosity=1)
        print("✅ Migraciones completadas")
        return True
    except Exception as e:
        print(f"❌ Error ejecutando migraciones: {e}")
        import traceback
        traceback.print_exc()
        return False

def collect_static():
    """Recolectar archivos estáticos"""
    try:
        django.setup()
        from django.core.management import call_command
        
        print("📁 Recolectando archivos estáticos...")
        call_command('collectstatic', '--noinput', '--clear', verbosity=0)
        print("✅ Archivos estáticos recolectados")
    except Exception as e:
        print(f"⚠️  Error recolectando archivos estáticos: {e}")

def create_admin_user():
    """Crear usuario admin si no existe"""
    try:
        django.setup()
        from dojo.models import User
        
        print("👤 Verificando usuario admin...")
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
            print("✅ Usuario admin creado (usuario: admin, contraseña: admin)")
        else:
            # Actualizar contraseña a admin por si acaso
            user.set_password('admin')
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.save()
            print("✅ Usuario admin verificado (usuario: admin, contraseña: admin)")
    except Exception as e:
        print(f"⚠️  Error creando usuario admin: {e}")

def main():
    """Función principal - Inicialización sin crear findings"""
    print("🔧 Inicializando DefectDojo (vacío - sin findings)...")
    print("")
    
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
        
        print("")
        print("✅ Inicialización completada (sin findings)")
        print("")
        print("ℹ️  DefectDojo está listo pero sin findings creados.")
        print("   Puedes crear findings manualmente o ejecutar 'make update' para")
        print("   crear y actualizar el flujo de findings con fechas históricas.")
        return 0
    except Exception as e:
        print(f"❌ Error en inicialización: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

