#!/usr/bin/env python3
"""
Script auxiliar para manejar sincronización WSTG desde línea de comandos
Se ejecuta en el contenedor de DefectDojo donde Django está disponible
"""
import sys
import json
import os

# Añadir path de la aplicación
sys.path.insert(0, '/app')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dojo.settings.settings')
import django
django.setup()

from app.wstg_sync import sync_from_tracker, sync_from_defectdojo, get_sync_status

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Uso: python wstg_sync_handler.py <command> [data]"}))
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'sync_from_tracker':
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Se requiere data JSON"}))
            sys.exit(1)
        data = json.loads(sys.argv[2])
        result = sync_from_tracker(data)
        print(json.dumps(result))
        
    elif command == 'sync_from_defectdojo':
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Se requiere data JSON"}))
            sys.exit(1)
        data = json.loads(sys.argv[2])
        result = sync_from_defectdojo(data)
        print(json.dumps(result))
        
    elif command == 'status':
        result = get_sync_status()
        print(json.dumps(result))
        
    else:
        print(json.dumps({"error": f"Comando desconocido: {command}"}))
        sys.exit(1)



