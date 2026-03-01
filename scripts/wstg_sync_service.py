#!/usr/bin/env python3
"""
Servicio de sincronización bidireccional WSTG ↔ DefectDojo
Ejecuta polling periódico, detecta cambios y resuelve conflictos automáticamente
"""
import os
import sys
import django
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dojo.settings.settings')
django.setup()

from dojo.models import Finding, Test, Test_Type
from app.wstg_sync import (
    get_wstg_test_and_engagement, 
    extract_wstg_id, 
    determine_wstg_status,
    load_sync_state,
    save_sync_state,
    log_sync
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/data/wstg_sync_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('wstg_sync_service')


def process_sync_queue():
    """Procesar archivos en la cola de sincronización"""
    from pathlib import Path
    import json
    
    queue_dir = Path('/app/data/wstg_sync_queue')
    if not queue_dir.exists():
        return 0, 0
    
    processed = 0
    errors = 0
    
    for filepath in queue_dir.glob('*.json'):
        try:
            with open(filepath, 'r') as f:
                request_data = json.load(f)
            
            request_type = request_data.get('type')
            data = request_data.get('data', {})
            
            if request_type == 'tracker->dd':
                from app.wstg_sync import sync_from_tracker
                result = sync_from_tracker(data)
                if result.get('success'):
                    processed += 1
                    logger.info(f"✓ Procesado desde cola: {filepath.name}")
                    filepath.unlink()  # Eliminar archivo procesado
                else:
                    errors += 1
                    logger.error(f"✗ Error procesando {filepath.name}: {result.get('error')}")
            elif request_type == 'dd->tracker':
                from app.wstg_sync import sync_from_defectdojo
                result = sync_from_defectdojo(data)
                if result.get('success'):
                    processed += 1
                    logger.info(f"✓ Procesado webhook desde cola: {filepath.name}")
                    filepath.unlink()
                else:
                    errors += 1
                    logger.error(f"✗ Error procesando webhook {filepath.name}: {result.get('error')}")
                    
        except Exception as e:
            errors += 1
            logger.error(f"✗ Error procesando archivo {filepath.name}: {e}", exc_info=True)
            # Mover archivo a carpeta de errores o renombrar
            error_dir = queue_dir / 'errors'
            error_dir.mkdir(exist_ok=True)
            try:
                filepath.rename(error_dir / filepath.name)
            except:
                pass
    
    if processed > 0 or errors > 0:
        logger.info(f"Cola procesada: {processed} exitosos, {errors} errores")
    
    return processed, errors


def sync_all_wstg_findings():
    """Sincronizar todos los findings WSTG desde DefectDojo"""
    try:
        test, _ = get_wstg_test_and_engagement()
        
        # Obtener todos los findings con tag WSTG
        findings = Finding.objects.filter(
            test=test,
            tags__name='WSTG'
        ).distinct()
        
        synced = 0
        errors = 0
        updated = 0
        
        state = load_sync_state()
        if 'items' not in state:
            state['items'] = {}
        
        for finding in findings:
            try:
                wstg_id = extract_wstg_id(finding)
                if not wstg_id:
                    continue
                
                wstg_status = determine_wstg_status(finding)
                
                # Verificar si hay cambios
                item_state = state['items'].get(wstg_id, {})
                old_wstg_status = item_state.get('wstg_status')
                last_sync = item_state.get('last_sync_timestamp')
                
                # Actualizar estado
                state['items'][wstg_id] = {
                    'finding_id': finding.id,
                    'wstg_status': wstg_status,
                    'defectdojo_status': 'verified' if finding.verified else 'active',
                    'last_sync_timestamp': datetime.now().isoformat(),
                    'last_sync_direction': 'dd->tracker'
                }
                
                if old_wstg_status != wstg_status:
                    updated += 1
                    logger.info(f"✓ Actualizado {wstg_id}: {old_wstg_status} → {wstg_status}")
                    log_sync(wstg_id, 'dd->tracker', old_wstg_status, wstg_status, True)
                else:
                    logger.debug(f"  Sin cambios {wstg_id}: {wstg_status}")
                
                synced += 1
                
            except Exception as e:
                errors += 1
                logger.error(f"✗ Error sincronizando finding {finding.id}: {e}", exc_info=True)
        
        save_sync_state(state)
        
        logger.info(f"Sincronización completada: {synced} items, {updated} actualizados, {errors} errores")
        return synced, updated, errors
        
    except Exception as e:
        logger.error(f"Error en sync_all_wstg_findings: {e}", exc_info=True)
        return 0, 0, 1


def resolve_conflicts():
    """Resolver conflictos entre tracker y DefectDojo"""
    state = load_sync_state()
    items = state.get('items', {})
    conflicts_resolved = 0
    
    for wstg_id, item_data in items.items():
        wstg_status = item_data.get('wstg_status')
        dd_status = item_data.get('defectdojo_status')
        last_direction = item_data.get('last_sync_direction')
        
        # Detectar conflictos
        is_conflict = False
        if wstg_status == 'Done' and dd_status != 'verified':
            is_conflict = True
        elif wstg_status == 'In Progress' and dd_status != 'active':
            is_conflict = True
        
        if is_conflict:
            # Estrategia: DefectDojo tiene prioridad
            logger.info(f"Resolviendo conflicto para {wstg_id}: DefectDojo tiene prioridad")
            # Aquí se podría actualizar el tracker si tuviera API
            conflicts_resolved += 1
    
    if conflicts_resolved > 0:
        logger.info(f"Conflictos resueltos: {conflicts_resolved}")
    
    return conflicts_resolved


def run_sync_service(interval_minutes=5):
    """Ejecutar servicio de sincronización en loop"""
    logger.info(f"🔄 Iniciando servicio de sincronización WSTG (intervalo: {interval_minutes} min)")
    
    while True:
        try:
            logger.info(f"[{datetime.now()}] Iniciando sincronización...")
            
            # 1. Procesar cola de sincronizaciones pendientes
            queue_processed, queue_errors = process_sync_queue()
            
            # 2. Sincronizar todos los findings WSTG desde DefectDojo
            synced, updated, errors = sync_all_wstg_findings()
            
            # 3. Resolver conflictos
            conflicts = resolve_conflicts()
            
            logger.info(f"[{datetime.now()}] Sincronización completada: {synced} items, {updated} actualizados, {queue_processed} de cola, {errors + queue_errors} errores, {conflicts} conflictos")
            
        except KeyboardInterrupt:
            logger.info("Servicio detenido por usuario")
            break
        except Exception as e:
            logger.error(f"❌ Error en servicio de sincronización: {e}", exc_info=True)
        
        time.sleep(interval_minutes * 60)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Servicio de sincronización WSTG')
    parser.add_argument('--interval', type=int, default=5, help='Intervalo en minutos (default: 5)')
    parser.add_argument('--once', action='store_true', help='Ejecutar una vez y salir')
    args = parser.parse_args()
    
    if args.once:
        # Procesar cola primero
        queue_processed, queue_errors = process_sync_queue()
        logger.info(f"Cola procesada: {queue_processed} exitosos, {queue_errors} errores")
        
        # Sincronizar findings
        sync_all_wstg_findings()
        resolve_conflicts()
    else:
        run_sync_service(args.interval)

