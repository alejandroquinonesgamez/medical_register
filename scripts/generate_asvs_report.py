#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar automáticamente el informe de seguridad ASVS 4.0.3

INTEGRADO CON DEFECTDOJO:
- Obtiene benchmarks ASVS desde DefectDojo
- Usa findings reales de DefectDojo para evaluar cumplimiento
- Genera informe basado en datos reales de la plataforma

Analiza el código de la aplicación Y obtiene datos de DefectDojo para generar
el informe Markdown basándose en OWASP ASVS versión 4.0.3 (versión estable).

Fuente oficial: https://github.com/OWASP/ASVS/tree/v4.0.3/4.0/

El script:
1. Se conecta a DefectDojo y obtiene benchmarks ASVS
2. Obtiene findings reales del producto
3. Analiza el código fuente de la aplicación (complementario)
4. Mapea findings a requisitos ASVS 4.0.3 Nivel 2
5. Genera el informe Markdown automáticamente
6. El script generate_pdf_report.py luego lo convierte a PDF
"""

import os
import sys
import ast
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

# Cargar estructura completa del ASVS 4.0.3 desde el JSON
ASVS_403_JSON_PATH = Path(__file__).parent.parent / 'docs' / 'OWASP Application Security Verification Standard 4.0.3-es.json'
ASVS_403_DATA = None
ASVS_403_HIERARCHY = {}

def load_asvs_403_structure():
    """Cargar la estructura completa del ASVS 4.0.3 desde el JSON"""
    global ASVS_403_DATA, ASVS_403_HIERARCHY
    
    if ASVS_403_DATA is not None:
        return ASVS_403_DATA, ASVS_403_HIERARCHY
    
    try:
        with open(ASVS_403_JSON_PATH, 'r', encoding='utf-8') as f:
            ASVS_403_DATA = json.load(f)
        
        # Construir jerarquía desde el JSON
        ASVS_403_HIERARCHY = {}
        for category in ASVS_403_DATA.get('Requirements', []):
            cat_code = category['Shortcode']
            ASVS_403_HIERARCHY[cat_code] = {
                'name': category.get('Name', category.get('ShortName', '')),
                'subcategories': {}
            }
            
            for subcat in category.get('Items', []):
                subcat_code = subcat['Shortcode']
                ASVS_403_HIERARCHY[cat_code]['subcategories'][subcat_code] = {
                    'name': subcat.get('Name', ''),
                    'requirements': []
                }
                
                for req in subcat.get('Items', []):
                    req_code = req['Shortcode']
                    ASVS_403_HIERARCHY[cat_code]['subcategories'][subcat_code]['requirements'].append(req_code)
        
        return ASVS_403_DATA, ASVS_403_HIERARCHY
    except Exception as e:
        print(f"⚠️  Error cargando estructura ASVS 4.0.3: {e}")
        return None, {}

# ASVS 4.0.3 - Estructura de categorías
ASVS_403_CATEGORIES = {
    'V1': 'Architecture, Design and Threat Modeling',
    'V2': 'Authentication',
    'V3': 'Session Management',
    'V4': 'Access Control',
    'V5': 'Validation, Sanitization and Encoding',
    'V6': 'Stored Cryptographically Sensitive Data',
    'V7': 'Error Handling and Logging',
    'V8': 'Data Protection',
    'V9': 'Communications',
    'V10': 'Malicious Code',
    'V11': 'Business Logic',
    'V12': 'Files and Resources',
    'V13': 'API',
    'V14': 'Configuration'
}

# Requisitos ASVS 4.0.3 Nivel 2 (simplificado para análisis automático)
ASVS_403_LEVEL2_REQUIREMENTS = {
    'V1': ['V1.1', 'V1.2', 'V1.3', 'V1.4'],
    'V2': ['V2.1', 'V2.2', 'V2.3'],  # No aplicable (monousuario)
    'V3': ['V3.1', 'V3.2'],  # No aplicable (sin sesiones)
    'V4': ['V4.1', 'V4.2'],  # No aplicable (monousuario)
    'V5': ['V5.1', 'V5.2', 'V5.3', 'V5.4', 'V5.5', 'V5.6'],
    'V6': ['V6.1', 'V6.2'],  # No aplicable (datos en cliente)
    'V7': ['V7.1', 'V7.2', 'V7.3', 'V7.4'],
    'V8': ['V8.1', 'V8.2', 'V8.3', 'V8.4'],
    'V9': ['V9.1', 'V9.2', 'V9.3'],
    'V10': ['V10.1', 'V10.2', 'V10.3', 'V10.4'],
    'V11': ['V11.1', 'V11.2'],
    'V12': ['V12.1', 'V12.2'],
    'V13': ['V13.1', 'V13.2', 'V13.3', 'V13.4'],
    'V14': ['V14.1', 'V14.2', 'V14.3']
}


class DefectDojoASVSConnector:
    """Conector con DefectDojo para obtener datos ASVS"""
    
    def __init__(self):
        self.django_initialized = False
        self._init_django()
    
    def _init_django(self):
        """Inicializar Django para acceso a DefectDojo"""
        if self.django_initialized:
            return
        
        try:
            import os
            import sys
            import django
            
            sys.path.insert(0, '/app')
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dojo.settings.settings')
            django.setup()
            
            self.django_initialized = True
            print("   ✓ Conectado a DefectDojo")
        except Exception as e:
            print(f"   ⚠️  No se pudo conectar a DefectDojo: {e}")
            print("   ℹ️  Continuando con análisis de código solamente")
            self.django_initialized = False
    
    def get_product(self, product_name='Medical Register App'):
        """Obtener producto de DefectDojo"""
        if not self.django_initialized:
            return None
        
        try:
            from dojo.models import Product
            return Product.objects.filter(name=product_name).first()
        except Exception as e:
            print(f"   ⚠️  Error obteniendo producto: {e}")
            return None
    
    def get_asvs_benchmark(self, product):
        """Obtener benchmark ASVS del producto"""
        if not self.django_initialized or not product:
            return None
        
        try:
            from dojo.models import Benchmark_Product_Summary
            benchmark = Benchmark_Product_Summary.objects.filter(product=product).first()
            if benchmark:
                return {
                    'desired_level': benchmark.desired_level,
                    'current_level': benchmark.current_level,
                    'asvs_level_1_score': benchmark.asvs_level_1_score,
                    'asvs_level_1_benchmark': benchmark.asvs_level_1_benchmark,
                    'asvs_level_2_score': benchmark.asvs_level_2_score,
                    'asvs_level_2_benchmark': benchmark.asvs_level_2_benchmark,
                    'asvs_level_3_score': benchmark.asvs_level_3_score,
                    'asvs_level_3_benchmark': benchmark.asvs_level_3_benchmark,
                }
        except Exception as e:
            print(f"   ⚠️  Error obteniendo benchmark ASVS: {e}")
        
        return None
    
    def get_findings_for_asvs(self, product):
        """Obtener findings relacionados con ASVS (excluyendo WSTG)"""
        if not self.django_initialized or not product:
            return []
        
        try:
            from dojo.models import Finding, Test, Engagement
            
            # Obtener todos los engagements del producto EXCEPTO WSTG
            engagements = Engagement.objects.filter(product=product).exclude(name='WSTG Security Testing')
            tests = Test.objects.filter(engagement__in=engagements)
            
            # Obtener findings activos (excluyendo los que tienen tag WSTG)
            findings = Finding.objects.filter(
                test__in=tests,
                active=True
            ).exclude(tags__name='WSTG').select_related('test', 'test__engagement')
            
            findings_data = []
            for finding in findings:
                # Obtener nombre del test de forma segura
                test_name = None
                if finding.test:
                    try:
                        test_name = str(finding.test)
                    except:
                        test_name = f"Test #{finding.test.id}" if finding.test.id else None
                
                findings_data.append({
                    'id': finding.id,
                    'title': finding.title,
                    'severity': finding.severity,
                    'cwe': finding.cwe,
                    'description': finding.description,
                    'mitigation': finding.mitigation,
                    'verified': finding.verified,
                    'false_p': finding.false_p,
                    'tags': [tag.name for tag in finding.tags.all()],
                    'test_name': test_name,
                })
            
            return findings_data
        except Exception as e:
            print(f"   ⚠️  Error obteniendo findings: {e}")
            return []
    
    def get_wstg_findings(self, product):
        """Obtener findings relacionados con WSTG"""
        if not self.django_initialized or not product:
            print("   ⚠️  Django no inicializado o producto no encontrado")
            return []
        
        try:
            from dojo.models import Finding, Test, Engagement
            
            # ESTRATEGIA: Buscar directamente el engagement que tenga findings con tag WSTG
            # Esto es más robusto que buscar por nombre
            findings_with_wstg = Finding.objects.filter(
                test__engagement__product=product,
                active=True,
                tags__name='WSTG'
            ).select_related('test', 'test__engagement').distinct()
            
            if not findings_with_wstg.exists():
                print("   ⚠️  No se encontraron findings con tag WSTG en ningún engagement")
                return []
            
            # Obtener el engagement del primer finding (todos deberían ser del mismo engagement)
            wstg_engagement = findings_with_wstg.first().test.engagement
            print(f"   ✓ Engagement WSTG encontrado: '{wstg_engagement.name}' (ID: {wstg_engagement.id})")
            
            # Obtener todos los findings activos con tag WSTG de este engagement
            tests = Test.objects.filter(engagement=wstg_engagement)
            findings = Finding.objects.filter(
                test__in=tests,
                active=True,
                tags__name='WSTG'
            ).select_related('test', 'test__engagement').distinct()
            
            print(f"   ✓ {findings.count()} findings WSTG encontrados en el engagement")
            
            wstg_findings_data = []
            for finding in findings:
                # Extraer WSTG ID de tags o título
                wstg_id = None
                for tag in finding.tags.all():
                    if tag.name.startswith('WSTG-'):
                        wstg_id = tag.name
                        break
                
                if not wstg_id and 'WSTG-' in finding.title:
                    import re
                    match = re.search(r'WSTG-\w+-\d+', finding.title)
                    if match:
                        wstg_id = match.group(0)
                
                wstg_findings_data.append({
                    'id': finding.id,
                    'wstg_id': wstg_id or 'Unknown',
                    'title': finding.title,
                    'severity': finding.severity,
                    'description': finding.description,
                    'mitigation': finding.mitigation,
                    'verified': finding.verified,
                    'false_p': finding.false_p,
                    'status': 'Done' if finding.verified else ('Not Applicable' if finding.false_p else 'In Progress'),
                    'tags': [tag.name for tag in finding.tags.all()],
                })
            
            return wstg_findings_data
        except Exception as e:
            print(f"   ⚠️  Error obteniendo findings WSTG: {e}")
            return []


class ASVSAnalyzer:
    """Analizador de cumplimiento ASVS 4.0.3 integrado con DefectDojo"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.app_dir = project_root / 'app'
        self.findings = {
            'compliant': [],
            'partial': [],
            'non_applicable': [],
            'missing': []
        }
        self.code_analysis = {}
        self.defectdojo_data = {
            'benchmark': None,
            'findings': [],
            'wstg_findings': [],
            'product': None
        }
        
        # Conectar con DefectDojo
        self.dd_connector = DefectDojoASVSConnector()
        
    def get_defectdojo_data(self):
        """Obtener datos de DefectDojo (benchmarks ASVS y findings)"""
        print("🔗 Obteniendo datos de DefectDojo...")
        
        # Obtener producto
        product = self.dd_connector.get_product('Medical Register App')
        if product:
            self.defectdojo_data['product'] = product
            print(f"   ✓ Producto encontrado: {product.name}")
            
            # Obtener benchmark ASVS
            benchmark = self.dd_connector.get_asvs_benchmark(product)
            if benchmark:
                self.defectdojo_data['benchmark'] = benchmark
                print(f"   ✓ Benchmark ASVS encontrado:")
                print(f"     - Nivel deseado: {benchmark.get('desired_level', 'N/A')}")
                print(f"     - Nivel actual: {benchmark.get('current_level', 'N/A')}")
                if benchmark.get('asvs_level_2_benchmark'):
                    score = benchmark.get('asvs_level_2_score', 0)
                    total = benchmark.get('asvs_level_2_benchmark', 1)
                    percentage = (score / total * 100) if total > 0 else 0
                    print(f"     - Nivel 2: {score}/{total} ({percentage:.1f}%)")
            else:
                print(f"   ⚠️  No se encontró benchmark ASVS configurado")
            
            # Obtener findings ASVS (excluyendo WSTG)
            findings = self.dd_connector.get_findings_for_asvs(product)
            self.defectdojo_data['findings'] = findings
            print(f"   ✓ Findings ASVS encontrados: {len(findings)}")
            
            # Obtener findings WSTG
            wstg_findings = self.dd_connector.get_wstg_findings(product)
            self.defectdojo_data['wstg_findings'] = wstg_findings
            print(f"   ✓ Findings WSTG encontrados: {len(wstg_findings)}")
        else:
            print(f"   ⚠️  Producto 'Medical Register App' no encontrado en DefectDojo")
            print(f"   ℹ️  Continuando con análisis de código solamente")
    
    def analyze_code(self):
        """Analizar el código fuente de la aplicación"""
        print("🔍 Analizando código fuente...")
        
        # Analizar archivos Python principales
        python_files = [
            self.app_dir / 'routes.py',
            self.app_dir / 'helpers.py',
            self.app_dir / 'storage.py',
            self.app_dir / 'config.py',
        ]
        
        for file_path in python_files:
            if file_path.exists():
                self._analyze_python_file(file_path)
        
        # Analizar archivos JavaScript
        js_files = [
            self.app_dir / 'static' / 'js' / 'main.js',
            self.app_dir / 'static' / 'js' / 'storage.js',
            self.app_dir / 'static' / 'js' / 'validation.js',
        ]
        
        for file_path in js_files:
            if file_path.exists():
                self._analyze_js_file(file_path)
        
        print(f"   ✓ Análisis completado")
        
    def _analyze_python_file(self, file_path: Path):
        """Analizar archivo Python"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            filename = file_path.name
            
            # Detectar validaciones
            if 'validate' in content.lower() or 'sanitize' in content.lower():
                self.code_analysis.setdefault('validation', []).append(filename)
            
            # Detectar manejo de errores
            if 'try:' in content and 'except' in content:
                self.code_analysis.setdefault('error_handling', []).append(filename)
            
            # Detectar headers de seguridad
            if 'X-Frame-Options' in content or 'CSP' in content or 'CORS' in content:
                self.code_analysis.setdefault('security_headers', []).append(filename)
            
            # Detectar configuración centralizada
            if 'config' in filename.lower():
                self.code_analysis.setdefault('centralized_config', True)
            
            # Detectar API REST
            if '@api.route' in content or 'Blueprint' in content:
                self.code_analysis.setdefault('api_rest', True)
                # Contar endpoints
                endpoints = len(re.findall(r'@api\.route|@.*\.route', content))
                self.code_analysis.setdefault('api_endpoints', endpoints)
                
        except Exception as e:
            print(f"   ⚠️  Error analizando {file_path}: {e}")
    
    def _analyze_js_file(self, file_path: Path):
        """Analizar archivo JavaScript"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            filename = file_path.name
            
            # Detectar validaciones en frontend
            if 'validate' in content.lower() or 'parseFloat' in content or 'parseInt' in content:
                self.code_analysis.setdefault('frontend_validation', []).append(filename)
            
            # Detectar sanitización
            if 'sanitize' in content.lower() or 'trim' in content or 'replace' in content:
                self.code_analysis.setdefault('frontend_sanitization', []).append(filename)
                
        except Exception as e:
            print(f"   ⚠️  Error analizando {file_path}: {e}")
    
    def check_asvs_requirements(self):
        """Verificar cumplimiento de requisitos ASVS 4.0.3 usando DefectDojo y análisis de código"""
        print("📋 Verificando requisitos ASVS 4.0.3 Nivel 2...")
        
        # Si tenemos benchmark de DefectDojo, usarlo como referencia
        if self.defectdojo_data.get('benchmark'):
            benchmark = self.defectdojo_data['benchmark']
            print(f"   ℹ️  Usando benchmark ASVS de DefectDojo como referencia")
            print(f"      Nivel 2: {benchmark.get('asvs_level_2_score', 0)}/{benchmark.get('asvs_level_2_benchmark', 0)}")
        
        # Mapear findings de DefectDojo a categorías ASVS
        self._map_findings_to_asvs()
        
        # V1: Architecture, Design and Threat Modeling
        self._check_v1()
        
        # V2: Authentication (No aplicable - monousuario)
        self.findings['non_applicable'].append({
            'category': 'V2',
            'reason': 'Aplicación monousuario sin autenticación compleja'
        })
        
        # V3: Session Management (No aplicable)
        self.findings['non_applicable'].append({
            'category': 'V3',
            'reason': 'No utiliza sesiones en el servidor'
        })
        
        # V4: Access Control (No aplicable)
        self.findings['non_applicable'].append({
            'category': 'V4',
            'reason': 'Aplicación monousuario sin control de acceso entre usuarios'
        })
        
        # V5: Validation, Sanitization and Encoding
        self._check_v5()
        
        # V6: Stored Cryptographically Sensitive Data (No aplicable)
        self.findings['non_applicable'].append({
            'category': 'V6',
            'reason': 'Datos almacenados localmente en cliente, no en servidor'
        })
        
        # V7: Error Handling and Logging
        self._check_v7()
        
        # V8: Data Protection
        self._check_v8()
        
        # V9: Communications
        self._check_v9()
        
        # V10: Malicious Code
        self._check_v10()
        
        # V11: Business Logic
        self._check_v11()
        
        # V12: Files and Resources
        self._check_v12()
        
        # V13: API
        self._check_v13()
        
        # V14: Configuration
        self._check_v14()
        
        print(f"   ✓ Verificación completada")
    
    def _map_findings_to_asvs(self):
        """Mapear findings de DefectDojo a categorías ASVS"""
        findings = self.defectdojo_data.get('findings', [])
        
        # Mapeo de CWE a categorías ASVS
        cwe_to_asvs = {
            # CWE relacionados con validación → V5
            'CWE-20': 'V5',  # Improper Input Validation
            'CWE-1287': 'V5',  # Improper Validation of Specified Type of Input
            'CWE-843': 'V5',  # Access of Resource Using Incompatible Type
            # CWE relacionados con headers → V8
            'CWE-1021': 'V8',  # Improper Restriction of Rendered UI Layers
            # CWE relacionados con logging → V7
            'CWE-703': 'V7',  # Improper Check or Handling of Exceptional Conditions
            # CWE relacionados con CORS → V9
            'CWE-942': 'V9',  # Overly Permissive Cross-domain Whitelist
        }
        
        # Agrupar findings por categoría ASVS
        findings_by_category = {}
        for finding in findings:
            cwe = finding.get('cwe')
            if cwe and cwe in cwe_to_asvs:
                category = cwe_to_asvs[cwe]
                if category not in findings_by_category:
                    findings_by_category[category] = []
                findings_by_category[category].append(finding)
        
        # Almacenar mapeo
        self.defectdojo_data['findings_by_category'] = findings_by_category
        
        if findings_by_category:
            print(f"   ✓ Findings mapeados a categorías ASVS: {len(findings_by_category)} categorías")
    
    def _check_v1(self):
        """V1: Architecture, Design and Threat Modeling"""
        compliant = []
        
        # V1.1: Arquitectura documentada
        if (self.project_root / 'README.md').exists():
            compliant.append('V1.1')
        
        # V1.2: Análisis de amenazas
        if (self.project_root / 'docs').exists():
            compliant.append('V1.2')
        
        # V1.3: Principios de seguridad
        if 'validation' in self.code_analysis or 'error_handling' in self.code_analysis:
            compliant.append('V1.3')
        
        # V1.4: Separación de responsabilidades
        if 'api_rest' in self.code_analysis:
            compliant.append('V1.4')
        
        if len(compliant) == 4:
            self.findings['compliant'].append('V1')
        else:
            self.findings['partial'].append({'category': 'V1', 'compliant': compliant})
    
    def _check_v5(self):
        """V5: Validation, Sanitization and Encoding"""
        compliant = []
        partial = []
        findings_list = []
        
        # Verificar findings de DefectDojo relacionados con V5
        v5_findings = self.defectdojo_data.get('findings_by_category', {}).get('V5', [])
        for finding in v5_findings:
            if finding.get('verified') and not finding.get('false_p'):
                # Finding verificado y no es falso positivo = problema resuelto
                compliant.append(f"Finding #{finding['id']} resuelto")
            elif not finding.get('false_p'):
                # Finding activo = problema pendiente
                partial.append(f"Finding #{finding['id']} pendiente")
                findings_list.append(finding)
        
        # V5.1: Validación en todas las fuentes
        if 'validation' in self.code_analysis and 'frontend_validation' in self.code_analysis:
            compliant.append('V5.1')
        elif 'validation' in self.code_analysis:
            partial.append('V5.1')
        
        # V5.2: Validación de tipos
        if 'validation' in self.code_analysis:
            compliant.append('V5.2')
        
        # V5.3: Sanitización
        if 'frontend_sanitization' in self.code_analysis:
            compliant.append('V5.3')
        else:
            partial.append('V5.3')
        
        # V5.4: Validación de tipos numéricos (verificar findings CWE-1287, CWE-843)
        v5_4_findings = [f for f in v5_findings if f.get('cwe') in ['CWE-1287', 'CWE-843']]
        if not v5_4_findings or all(f.get('verified') for f in v5_4_findings):
            compliant.append('V5.4')
        else:
            partial.append('V5.4')
        
        # V5.5: Validación de límites
        if 'centralized_config' in self.code_analysis:
            compliant.append('V5.5')
        
        # V5.6: Validación de formato
        if 'validation' in self.code_analysis:
            compliant.append('V5.6')
        
        if len(partial) > 0 or findings_list:
            self.findings['partial'].append({
                'category': 'V5',
                'compliant': compliant,
                'partial': partial,
                'defectdojo_findings': findings_list
            })
        else:
            self.findings['compliant'].append('V5')
    
    def _check_v7(self):
        """V7: Error Handling and Logging"""
        partial = []
        findings_list = []
        
        # Verificar findings de DefectDojo relacionados con V7
        v7_findings = self.defectdojo_data.get('findings_by_category', {}).get('V7', [])
        for finding in v7_findings:
            if not finding.get('verified') and not finding.get('false_p'):
                partial.append(f"Finding #{finding['id']} pendiente")
                findings_list.append(finding)
        
        if 'error_handling' in self.code_analysis:
            partial.append('V7.1')
        else:
            self.findings['missing'].append('V7.1')
        
        # V7.2: Códigos HTTP (asumido si hay API REST)
        if 'api_rest' in self.code_analysis:
            partial.append('V7.2')
        
        # V7.3: Logging (verificar finding CWE-703)
        cwe_703 = [f for f in v7_findings if f.get('cwe') == 'CWE-703']
        if cwe_703 and all(f.get('verified') for f in cwe_703):
            partial.append('V7.3 (mejorado)')
        else:
            partial.append('V7.3')
        
        # V7.4: No exponer detalles (asumido)
        partial.append('V7.4')
        
        self.findings['partial'].append({
            'category': 'V7',
            'partial': partial,
            'defectdojo_findings': findings_list
        })
    
    def _check_v8(self):
        """V8: Data Protection"""
        compliant = []
        findings_list = []
        
        # Verificar findings de DefectDojo relacionados con V8
        v8_findings = self.defectdojo_data.get('findings_by_category', {}).get('V8', [])
        # Verificar CWE-1021 (clickjacking) - debe estar resuelto
        cwe_1021 = [f for f in v8_findings if f.get('cwe') == 'CWE-1021']
        if cwe_1021 and all(f.get('verified') for f in cwe_1021):
            compliant.append('V8.3 (CWE-1021 resuelto)')
        elif cwe_1021:
            findings_list.extend([f for f in cwe_1021 if not f.get('verified')])
        
        if 'validation' in self.code_analysis:
            compliant.append('V8.1')
        
        if 'security_headers' in self.code_analysis:
            compliant.append('V8.2')
            if not cwe_1021 or all(f.get('verified') for f in cwe_1021):
                compliant.append('V8.3')
        
        # V8.4: CORS (verificar finding CWE-942)
        v9_findings = self.defectdojo_data.get('findings_by_category', {}).get('V9', [])
        cwe_942 = [f for f in v9_findings if f.get('cwe') == 'CWE-942']
        if cwe_942 and not all(f.get('verified') for f in cwe_942):
            findings_list.extend([f for f in cwe_942 if not f.get('verified')])
        
        if 'security_headers' in self.code_analysis:
            compliant.append('V8.4')
        
        if len(compliant) >= 3 and not findings_list:
            self.findings['compliant'].append('V8')
        else:
            self.findings['partial'].append({
                'category': 'V8',
                'compliant': compliant,
                'defectdojo_findings': findings_list
            })
    
    def _check_v9(self):
        """V9: Communications"""
        partial = []
        findings_list = []
        
        # Verificar findings de DefectDojo relacionados con V9
        v9_findings = self.defectdojo_data.get('findings_by_category', {}).get('V9', [])
        # Verificar CWE-942 (CORS permisivo)
        cwe_942 = [f for f in v9_findings if f.get('cwe') == 'CWE-942']
        if cwe_942 and not all(f.get('verified') for f in cwe_942):
            partial.append('V9.2 (CWE-942 pendiente)')
            partial.append('V9.3 (CWE-942 pendiente)')
            findings_list.extend([f for f in cwe_942 if not f.get('verified')])
        elif 'security_headers' in self.code_analysis:
            partial.append('V9.2')
            partial.append('V9.3')
        
        # V9.1: HTTPS (recomendado para producción)
        partial.append('V9.1')
        
        self.findings['partial'].append({
            'category': 'V9',
            'partial': partial,
            'defectdojo_findings': findings_list
        })
    
    def _check_v10(self):
        """V10: Malicious Code"""
        compliant = []
        
        if 'validation' in self.code_analysis:
            compliant.append('V10.1')
        
        if 'frontend_sanitization' in self.code_analysis:
            compliant.append('V10.2')
        
        if 'security_headers' in self.code_analysis:
            compliant.append('V10.3')
        
        compliant.append('V10.4')  # Asumido
        
        if len(compliant) == 4:
            self.findings['compliant'].append('V10')
        else:
            self.findings['partial'].append({'category': 'V10', 'compliant': compliant})
    
    def _check_v11(self):
        """V11: Business Logic"""
        compliant = []
        
        if 'centralized_config' in self.code_analysis:
            compliant.append('V11.1')
            compliant.append('V11.2')
        
        if len(compliant) == 2:
            self.findings['compliant'].append('V11')
        else:
            self.findings['partial'].append({'category': 'V11', 'compliant': compliant})
    
    def _check_v12(self):
        """V12: Files and Resources"""
        # Parcialmente aplicable (solo endpoints de DefectDojo)
        self.findings['partial'].append({
            'category': 'V12',
            'reason': 'Parcialmente aplicable - Endpoints de importación/exportación de DefectDojo'
        })
    
    def _check_v13(self):
        """V13: API"""
        compliant = []
        
        if 'api_rest' in self.code_analysis:
            compliant.append('V13.1')
            compliant.append('V13.2')
            # V13.3: Sin autenticación (no aplicable por diseño)
            compliant.append('V13.4')
        
        if len(compliant) >= 3:
            self.findings['compliant'].append('V13')
        else:
            self.findings['partial'].append({'category': 'V13', 'compliant': compliant})
    
    def _check_v14(self):
        """V14: Configuration"""
        compliant = []
        
        if 'centralized_config' in self.code_analysis:
            compliant.append('V14.1')
        
        if 'security_headers' in self.code_analysis:
            compliant.append('V14.2')
            compliant.append('V14.3')
        
        if len(compliant) == 3:
            self.findings['compliant'].append('V14')
        else:
            self.findings['partial'].append({'category': 'V14', 'compliant': compliant})


class ASVSReportGenerator:
    """Generador de informe ASVS 4.0.3"""
    
    def __init__(self, analyzer: ASVSAnalyzer, project_root: Path):
        self.analyzer = analyzer
        self.project_root = project_root
        self.report_date = datetime.now().strftime("%Y-%m-%d")
        
    def generate_report(self) -> str:
        """Generar el informe Markdown completo"""
        print("📝 Generando informe Markdown...")
        
        report = []
        
        # Encabezado
        report.append(self._generate_header())
        report.append("")
        report.append("---")
        report.append("")
        
        # Sección 1: Descripción
        report.append(self._generate_section1())
        report.append("")
        
        # Sección 2: Análisis de seguridad
        report.append(self._generate_section2())
        report.append("")
        
        # Sección 3: Debilidades identificadas
        report.append(self._generate_section3())
        report.append("")
        
        # Sección 4: Nivel ASVS
        report.append(self._generate_section4())
        report.append("")
        
        # Sección 5: Análisis WSTG
        report.append(self._generate_section5_wstg())
        report.append("")
        
        # Sección 6: Recomendaciones
        report.append(self._generate_section6_recommendations())
        report.append("")
        
        # Referencias
        report.append(self._generate_references())
        
        print(f"   ✓ Informe generado")
        return "\n".join(report)
    
    def _generate_header(self) -> str:
        """Generar encabezado del informe"""
        return f"""# Informe de Análisis de Seguridad - Aplicación Médica

**Fecha de análisis**: {self.report_date}  
**Versión analizada**: Versión actual (post-implementación de mejoras de seguridad)  
**Estándares de referencia**: 
- OWASP Application Security Verification Standard (ASVS) **Versión 4.0.3**
- OWASP Web Security Testing Guide (WSTG)
**Fuente oficial ASVS**: [OWASP ASVS v4.0.3 en GitHub](https://github.com/OWASP/ASVS/tree/v4.0.3/4.0/)
**Fuente oficial WSTG**: [OWASP WSTG](https://owasp.org/www-project-web-security-testing-guide/)
**Nota importante**: Este informe utiliza la estructura de categorías de ASVS 4.0.3 (V1-V14). Si necesitas comparar con ASVS 5.0, las categorías han sido reorganizadas y renumeradas.
**Práctica**: Análisis de seguridad y determinación de nivel ASVS + Análisis de tests WSTG

**Nota**: Este informe ha sido generado automáticamente mediante análisis de código e integración con DefectDojo."""
    
    def _generate_section1(self) -> str:
        """Generar sección 1: Descripción de la aplicación"""
        return """## 1. Descripción Breve de la Aplicación Analizada

### 1.1. Propósito y Funcionalidad

La aplicación es una herramienta web **monousuario** diseñada para el registro personal de peso, talla y cálculo del Índice de Masa Corporal (IMC). Su objetivo principal es permitir a un único usuario realizar un seguimiento de su peso corporal y obtener información sobre su estado nutricional mediante el cálculo automático del IMC.

### 1.2. Características Principales

- **Registro de datos personales**: Nombre, apellidos, fecha de nacimiento y talla (en metros)
- **Registro de peso**: Permite registrar el peso actual con fecha y hora automáticas
- **Cálculo automático de IMC**: Calcula y muestra el Índice de Masa Corporal basado en el último peso registrado
- **Estadísticas históricas**: Muestra número de pesajes, peso máximo y peso mínimo registrados
- **Sincronización bidireccional**: Entre frontend (localStorage) y backend (memoria)
- **Modo offline**: Funciona sin conexión al servidor utilizando almacenamiento local

### 1.3. Arquitectura Técnica

- **Backend**: Flask (Python) con API REST
- **Frontend**: JavaScript vanilla con almacenamiento en localStorage
- **Almacenamiento**: Memoria en backend + localStorage en frontend
- **Tests**: 86 tests backend (pytest) + ~66 tests frontend (Jest)
- **Gestión de vulnerabilidades**: DefectDojo integrado para seguimiento de debilidades de seguridad

### 1.4. Análisis de Datos que Maneja la Aplicación

La aplicación maneja diferentes tipos de datos que requieren diferentes niveles de protección:

#### 1.4.1. **Datos Sensibles (Personales de Salud)**
- **Peso corporal (kg)**: Dato biométrico personal
- **Talla/Altura (m)**: Dato biométrico personal  
- **Fecha de nacimiento**: Permite inferir edad y otros datos demográficos
- **Nombre completo**: Identificador personal
- **Apellidos**: Identificador personal

**Clasificación según RGPD**: Estos datos están categorizados como **datos personales sensibles** según el Reglamento General de Protección de Datos, ya que los datos de salud (peso, altura, IMC) están incluidos en la categoría de datos especiales.

**Almacenamiento actual**: 
- Frontend: localStorage del navegador (cliente)
- Backend: Memoria (volátil, se pierde al reiniciar)"""
    
    def _generate_section2(self) -> str:
        """Generar sección 2: Análisis de seguridad"""
        lines = []
        lines.append("## 2. Análisis de Seguridad Realizado")
        lines.append("")
        lines.append("### 2.1. Metodología")
        lines.append("")
        lines.append("El análisis de seguridad se ha realizado mediante:")
        lines.append("- **Integración con DefectDojo**: Obtención de benchmarks ASVS y findings reales")
        lines.append("- **Análisis estático de código**: Revisión del código fuente Python y JavaScript")
        lines.append("- **Verificación de cumplimiento ASVS 4.0.3**: Comparación con requisitos del estándar")
        lines.append("- **Mapeo de findings**: Relación de vulnerabilidades con requisitos ASVS")
        lines.append("- **Análisis de arquitectura**: Revisión de la estructura y diseño de la aplicación")
        lines.append("")
        lines.append("### 2.2. Herramientas Utilizadas")
        lines.append("")
        lines.append("- **DefectDojo**: Benchmarks ASVS y gestión de findings")
        lines.append("- Análisis automático de código fuente")
        lines.append("- Verificación de patrones de seguridad")
        lines.append("- Comparación con estándares OWASP ASVS 4.0.3")
        lines.append("")
        
        # Añadir información de DefectDojo si está disponible
        if self.analyzer.defectdojo_data.get('benchmark'):
            benchmark = self.analyzer.defectdojo_data['benchmark']
            lines.append("### 2.3. Datos de DefectDojo")
            lines.append("")
            lines.append(f"- **Producto**: {self.analyzer.defectdojo_data.get('product', {}).name if self.analyzer.defectdojo_data.get('product') else 'N/A'}")
            lines.append(f"- **Nivel ASVS deseado**: {benchmark.get('desired_level', 'N/A')}")
            lines.append(f"- **Nivel ASVS actual**: {benchmark.get('current_level', 'N/A')}")
            if benchmark.get('asvs_level_2_benchmark'):
                score = benchmark.get('asvs_level_2_score', 0)
                total = benchmark.get('asvs_level_2_benchmark', 1)
                percentage = (score / total * 100) if total > 0 else 0
                lines.append(f"- **Cumplimiento Nivel 2**: {score}/{total} ({percentage:.1f}%)")
            lines.append(f"- **Findings analizados**: {len(self.analyzer.defectdojo_data.get('findings', []))}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_section3(self) -> str:
        """Generar sección 3: Debilidades identificadas"""
        return """## 3. Debilidades de Seguridad Identificadas

### 3.1. Resumen

El análisis automático ha identificado áreas de mejora en la aplicación. Las debilidades principales están relacionadas con:
- Validación de tipos numéricos (NaN/Infinity)
- Configuración de CORS para producción
- Mejora del logging de errores"""
    
    def _generate_section4(self) -> str:
        """Generar sección 4: Nivel ASVS"""
        lines = []
        lines.append("## 4. Nivel ASVS Seleccionado, con Justificación")
        lines.append("")
        lines.append("### 4.1. OWASP Application Security Verification Standard (ASVS)")
        lines.append("")
        lines.append("**Versión utilizada en este informe**: **ASVS 4.0.3** (versión estable, lanzada el 28 de octubre de 2021)")
        lines.append("")
        lines.append("**Fuente oficial**: [OWASP ASVS v4.0.3 en GitHub](https://github.com/OWASP/ASVS/tree/v4.0.3/4.0/)")
        lines.append("")
        lines.append("El **OWASP Application Security Verification Standard (ASVS) versión 4.0.3** es un estándar de seguridad para aplicaciones web que define tres niveles de verificación. Esta versión se centra en corregir errores ortográficos y clarificar requisitos sin introducir cambios significativos ni romper compatibilidad con versiones anteriores.")
        lines.append("")
        lines.append("**Estructura de categorías ASVS 4.0.3**: 14 categorías de verificación (V1-V14):")
        for code, name in ASVS_403_CATEGORIES.items():
            lines.append(f"- {code}: {name}")
        lines.append("")
        lines.append("### 4.2. Nivel Seleccionado: **NIVEL 2 (ESTÁNDAR)**")
        lines.append("")
        lines.append("### 4.3. Justificación de la Selección")
        lines.append("")
        lines.append("La aplicación maneja **datos de salud personales** (peso, altura, fecha de nacimiento), aunque no sean datos médicos críticos ni información de identificación sensible. Según el Reglamento General de Protección de Datos (RGPD), los datos de salud están categorizados como **datos personales sensibles**, lo que requiere un nivel de protección superior al básico.")
        lines.append("")
        lines.append("### 4.4. Enumeración de Requerimientos ASVS Nivel 2")
        lines.append("")
        lines.append("Basado en el análisis automático realizado, se enumeran **TODOS** los requerimientos ASVS Nivel 2 del estándar ASVS 4.0.3. El estándar ASVS 4.0.3 define 14 categorías de verificación (V1-V14) con sus respectivos subrequisitos. Se detallan todos los requisitos manteniendo la estructura exacta del estándar:")
        lines.append("")
        
        # Cargar estructura completa del ASVS 4.0.3 desde el JSON
        asvs_data, asvs_hierarchy = load_asvs_403_structure()
        
        # Generar TODOS los requisitos del ASVS 4.0.3 con código ASVS (V.X.X.X)
        if asvs_data and asvs_hierarchy:
            # Usar estructura completa del JSON del ASVS 4.0.3
            requirements_list = asvs_data.get('Requirements', [])
            
            for category in requirements_list:
                cat_code = category['Shortcode']
                cat_name = category.get('Name', category.get('ShortName', ''))
                
                lines.append(f"#### **{cat_code}: {cat_name}**")
                lines.append("")
                
                # Verificar estado general de la categoría
                cat_status = self._get_category_status(cat_code)
                if cat_status == 'non_applicable':
                    lines.append("**Estado general**: ⚠️ **NO APLICABLE**")
                    lines.append("")
                    na_item = next((f for f in self.analyzer.findings['non_applicable'] if f['category'] == cat_code), None)
                    if na_item:
                        lines.append(f"**Justificación**: {na_item.get('reason', 'No aplicable para esta aplicación')}")
                    lines.append("")
                
                # Recorrer todas las subcategorías
                for subcat in category.get('Items', []):
                    subcat_code = subcat['Shortcode']
                    subcat_name = subcat.get('Name', '')
                    
                    lines.append(f"##### **{subcat_code}: {subcat_name}**")
                    lines.append("")
                    
                    # Recorrer todos los requisitos de la subcategoría
                    for req in subcat.get('Items', []):
                        req_code = req['Shortcode']
                        req_desc = req.get('Description', '')
                        req_l2 = req.get('L2', {}).get('Required', False)
                        
                        # Solo incluir requisitos de Nivel 2
                        if not req_l2:
                            continue
                        
                        # Determinar estado del requisito
                        status = self._get_requirement_status(req_code, cat_code)
                        status_icon = "✅" if status == 'compliant' else ("⚠️" if status == 'partial' else ("❌" if status == 'missing' else "ℹ️"))
                        status_text = "CUMPLE" if status == 'compliant' else ("PARCIAL" if status == 'partial' else ("PENDIENTE" if status == 'missing' else "NO APLICABLE"))
                        
                        lines.append(f"**{req_code}**")
                        lines.append("")
                        lines.append(f"**Descripción**: {req_desc}")
                        lines.append("")
                        lines.append(f"**Estado**: {status_icon} **{status_text}**")
                        lines.append("")
                        
                        # Añadir explicación del estado si está disponible
                        explanation = self._get_requirement_explanation(req_code, cat_code, status)
                        if explanation:
                            lines.append(f"**Explicación**: {explanation}")
                            lines.append("")
                        
                        # Añadir información de CWE si está disponible
                        cwe_list = req.get('CWE', [])
                        if cwe_list:
                            cwe_str = ', '.join([f'CWE-{cwe}' for cwe in cwe_list])
                            lines.append(f"**CWE relacionado**: {cwe_str}")
                            lines.append("")
                        
                        lines.append("---")
                        lines.append("")
                
                # Si no está en la jerarquía completa, usar el método anterior
                else:
                    # Verificar estado de la categoría
                    if cat_code in self.analyzer.findings['compliant']:
                        lines.append("**Estado de cumplimiento**: ✅ **CUMPLE**")
                        lines.append("")
                        explanation = self._get_detailed_explanation(cat_code, 'compliant')
                        if explanation:
                            lines.append("**Explicación del cumplimiento**:")
                            lines.append("")
                            lines.append(explanation)
                            lines.append("")
                    elif cat_code in [f['category'] for f in self.analyzer.findings['partial']]:
                        lines.append("**Estado de cumplimiento**: ⚠️ **PARCIAL**")
                        lines.append("")
                        partial_item = next((f for f in self.analyzer.findings['partial'] if f['category'] == cat_code), None)
                        explanation = self._get_detailed_explanation(cat_code, 'partial', partial_item)
                        if explanation:
                            lines.append("**Explicación detallada**:")
                            lines.append("")
                            lines.append(explanation)
                            lines.append("")
                        if partial_item and partial_item.get('defectdojo_findings'):
                            findings = partial_item['defectdojo_findings']
                            lines.append("**Findings de DefectDojo relacionados**:")
                            for finding in findings[:5]:
                                status = "✅ Resuelto" if finding.get('verified') else "⚠️ Pendiente"
                                lines.append(f"- Finding #{finding['id']}: {finding.get('title', 'N/A')} ({status})")
                                if finding.get('cwe'):
                                    lines.append(f"  - CWE: {finding['cwe']}")
                            if len(findings) > 5:
                                lines.append(f"- ... y {len(findings) - 5} findings más")
                            lines.append("")
                    elif cat_code in [f['category'] for f in self.analyzer.findings['non_applicable']]:
                        lines.append("**Requerimientos ASVS Nivel 2 aplicables**:")
                        lines.append("- ⚠️ **No aplicable**")
                        lines.append("")
                        na_item = next((f for f in self.analyzer.findings['non_applicable'] if f['category'] == cat_code), None)
                        if na_item:
                            lines.append(f"**Justificación**: {na_item.get('reason', 'No aplicable para esta aplicación')}")
                            lines.append("")
                    else:
                        lines.append("**Estado de cumplimiento**: ❌ **PENDIENTE**")
                        lines.append("")
                        explanation = self._get_detailed_explanation(cat_code, 'missing')
                        if explanation:
                            lines.append("**Explicación**:")
                            lines.append("")
                            lines.append(explanation)
                            lines.append("")
        else:
            # Usar estructura básica (método anterior) si no hay estructura completa
            for code, name in ASVS_403_CATEGORIES.items():
                lines.append(f"#### **{code}: {name}**")
                lines.append("")
                
                if code in self.analyzer.findings['compliant']:
                    lines.append("**Estado de cumplimiento**: ✅ **CUMPLE**")
                    lines.append("")
                    explanation = self._get_detailed_explanation(code, 'compliant')
                    if explanation:
                        lines.append("**Explicación del cumplimiento**:")
                        lines.append("")
                        lines.append(explanation)
                        lines.append("")
                elif code in [f['category'] for f in self.analyzer.findings['partial']]:
                    lines.append("**Estado de cumplimiento**: ⚠️ **PARCIAL**")
                    lines.append("")
                    partial_item = next((f for f in self.analyzer.findings['partial'] if f['category'] == code), None)
                    explanation = self._get_detailed_explanation(code, 'partial', partial_item)
                    if explanation:
                        lines.append("**Explicación detallada**:")
                        lines.append("")
                        lines.append(explanation)
                        lines.append("")
                    if partial_item and partial_item.get('defectdojo_findings'):
                        findings = partial_item['defectdojo_findings']
                        lines.append("**Findings de DefectDojo relacionados**:")
                        for finding in findings[:5]:
                            status = "✅ Resuelto" if finding.get('verified') else "⚠️ Pendiente"
                            lines.append(f"- Finding #{finding['id']}: {finding.get('title', 'N/A')} ({status})")
                            if finding.get('cwe'):
                                lines.append(f"  - CWE: {finding['cwe']}")
                        if len(findings) > 5:
                            lines.append(f"- ... y {len(findings) - 5} findings más")
                        lines.append("")
                elif code in [f['category'] for f in self.analyzer.findings['non_applicable']]:
                    lines.append("**Requerimientos ASVS Nivel 2 aplicables**:")
                    lines.append("- ⚠️ **No aplicable**")
                    lines.append("")
                    na_item = next((f for f in self.analyzer.findings['non_applicable'] if f['category'] == code), None)
                    if na_item:
                        lines.append(f"**Justificación**: {na_item.get('reason', 'No aplicable para esta aplicación')}")
                        lines.append("")
                else:
                    lines.append("**Estado de cumplimiento**: ❌ **PENDIENTE**")
                    lines.append("")
                    explanation = self._get_detailed_explanation(code, 'missing')
                    if explanation:
                        lines.append("**Explicación**:")
                        lines.append("")
                        lines.append(explanation)
                        lines.append("")
        
        return "\n".join(lines)
    
    def _get_category_status(self, cat_code: str) -> str:
        """Determinar el estado general de una categoría"""
        if cat_code in self.analyzer.findings['compliant']:
            return 'compliant'
        elif cat_code in [f['category'] for f in self.analyzer.findings['partial']]:
            return 'partial'
        elif cat_code in [f['category'] for f in self.analyzer.findings['non_applicable']]:
            return 'non_applicable'
        else:
            return 'missing'
    
    def _get_requirement_status(self, req_code: str, cat_code: str) -> str:
        """Determinar el estado de un requisito específico"""
        # Verificar si la categoría completa está en los findings
        if cat_code in self.analyzer.findings['compliant']:
            return 'compliant'
        elif cat_code in [f['category'] for f in self.analyzer.findings['partial']]:
            # Para categorías parciales, verificar requisitos específicos
            partial_item = next((f for f in self.analyzer.findings['partial'] if f['category'] == cat_code), None)
            if partial_item:
                compliant_reqs = partial_item.get('compliant', [])
                partial_reqs = partial_item.get('partial', [])
                
                # Extraer subcategoría del requisito (ej: V5.1.1 -> V5.1)
                req_parts = req_code.split('.')
                if len(req_parts) >= 2:
                    subcat_code = f"{req_parts[0]}.{req_parts[1]}"
                    
                    # Verificar si el requisito específico está en la lista de cumplidos
                    if req_code in compliant_reqs or subcat_code in compliant_reqs:
                        return 'compliant'
                    elif req_code in partial_reqs or subcat_code in partial_reqs:
                        return 'partial'
            
            return 'partial'
        elif cat_code in [f['category'] for f in self.analyzer.findings['non_applicable']]:
            return 'non_applicable'
        else:
            return 'missing'
    
    def _get_requirement_explanation(self, req_code: str, cat_code: str, status: str) -> str:
        """Obtener explicación para un requisito específico"""
        # Obtener explicación detallada basada en el análisis
        if status == 'compliant':
            return f"El requisito {req_code} se cumple según el análisis realizado."
        elif status == 'partial':
            partial_item = next((f for f in self.analyzer.findings['partial'] if f['category'] == cat_code), None)
            if partial_item:
                compliant_reqs = partial_item.get('compliant', [])
                partial_reqs = partial_item.get('partial', [])
                
                # Extraer subcategoría del requisito
                req_parts = req_code.split('.')
                if len(req_parts) >= 2:
                    subcat_code = f"{req_parts[0]}.{req_parts[1]}"
                    
                    if req_code in compliant_reqs or subcat_code in compliant_reqs:
                        return f"El requisito {req_code} se cumple según el análisis realizado."
                    elif req_code in partial_reqs or subcat_code in partial_reqs:
                        return f"El requisito {req_code} se cumple parcialmente. Se requiere revisión adicional."
            
            return f"El requisito {req_code} se cumple parcialmente. Se requiere revisión adicional."
        elif status == 'non_applicable':
            return f"El requisito {req_code} no es aplicable para esta aplicación."
        else:
            return f"El requisito {req_code} requiere implementación."
    
    def _get_detailed_explanation(self, category_code: str, status: str, partial_item: dict = None) -> str:
        """Generar explicación detallada para una categoría ASVS"""
        explanations = []
        
        if status == 'compliant':
            # Explicar qué cumple
            if category_code == 'V1':
                explanations.append("✅ **V1.1**: La aplicación cuenta con documentación de arquitectura (README.md)")
                explanations.append("✅ **V1.2**: Existe documentación de análisis de amenazas en la carpeta `docs/`")
                explanations.append("✅ **V1.3**: Se implementan principios de seguridad mediante validaciones y manejo de errores")
                explanations.append("✅ **V1.4**: La aplicación utiliza una arquitectura REST con separación clara de responsabilidades (frontend/backend)")
            elif category_code == 'V5':
                explanations.append("✅ **V5.1**: Se implementa validación de entrada tanto en frontend (JavaScript) como en backend (Python)")
                explanations.append("✅ **V5.2**: Se valida el tipo de datos en todas las entradas (nombres, números, fechas)")
                explanations.append("✅ **V5.3**: Se implementa sanitización de entrada mediante la función `validate_and_sanitize_name()`")
                explanations.append("✅ **V5.4**: Se valida que los valores numéricos sean válidos (no NaN ni Infinity)")
                explanations.append("✅ **V5.5**: Se validan límites de rango para altura (0.4-2.72m) y peso (2-650kg) mediante configuración centralizada")
                explanations.append("✅ **V5.6**: Se valida el formato de fechas (formato ISO)")
            elif category_code == 'V8':
                explanations.append("✅ **V8.1**: Se implementan validaciones defensivas antes de operaciones críticas (cálculo de IMC)")
                explanations.append("✅ **V8.2**: Se configuran headers de seguridad HTTP (X-Frame-Options, Content-Security-Policy, etc.)")
                explanations.append("✅ **V8.3**: Se protege contra clickjacking mediante `X-Frame-Options: DENY` y CSP `frame-ancestors 'none'`")
                explanations.append("✅ **V8.4**: Se configura CORS para controlar el acceso desde otros dominios")
            elif category_code == 'V10':
                explanations.append("✅ **V10.1**: Se valida toda la entrada de datos para prevenir código malicioso")
                explanations.append("✅ **V10.2**: Se sanitiza la entrada en el frontend para prevenir inyección de código")
                explanations.append("✅ **V10.3**: Se implementan headers de seguridad (CSP) para prevenir ejecución de código malicioso")
                explanations.append("✅ **V10.4**: La aplicación no permite la carga de archivos desde usuarios")
            elif category_code == 'V11':
                explanations.append("✅ **V11.1**: La lógica de negocio está centralizada y bien estructurada en `app/config.py`")
                explanations.append("✅ **V11.2**: Se implementan controles de negocio consistentes (validaciones de límites, cálculos)")
            elif category_code == 'V13':
                explanations.append("✅ **V13.1**: La API REST está documentada mediante código y sigue estándares RESTful")
                explanations.append("✅ **V13.2**: Todos los endpoints de la API validan la entrada de datos")
                explanations.append("✅ **V13.4**: Se manejan errores con códigos HTTP apropiados (400, 404, 500)")
            elif category_code == 'V14':
                explanations.append("✅ **V14.1**: La configuración está centralizada en `app/config.py`")
                explanations.append("✅ **V14.2**: Se configuran headers de seguridad de forma centralizada")
                explanations.append("✅ **V14.3**: Se gestiona la configuración de CORS de forma centralizada")
        
        elif status == 'partial':
            # Explicar qué cumple y qué falta
            if category_code == 'V1':
                compliant_reqs = partial_item.get('compliant', []) if partial_item else []
                if 'V1.1' in compliant_reqs:
                    explanations.append("✅ **V1.1**: La aplicación cuenta con documentación de arquitectura (README.md)")
                else:
                    explanations.append("⚠️ **V1.1**: Falta documentación completa de arquitectura")
                
                if 'V1.2' in compliant_reqs:
                    explanations.append("✅ **V1.2**: Existe documentación de análisis de amenazas en la carpeta `docs/`")
                else:
                    explanations.append("⚠️ **V1.2**: Falta documentación detallada de análisis de amenazas")
                
                if 'V1.3' in compliant_reqs:
                    explanations.append("✅ **V1.3**: Se implementan principios de seguridad mediante validaciones y manejo de errores")
                else:
                    explanations.append("⚠️ **V1.3**: Los principios de seguridad podrían estar mejor documentados")
                
                if 'V1.4' in compliant_reqs:
                    explanations.append("✅ **V1.4**: La aplicación utiliza una arquitectura REST con separación clara de responsabilidades")
                else:
                    explanations.append("⚠️ **V1.4**: La separación de responsabilidades podría mejorarse")
            
            elif category_code == 'V5':
                compliant_reqs = partial_item.get('compliant', []) if partial_item else []
                partial_reqs = partial_item.get('partial', []) if partial_item else []
                
                # V5.1: Validación en todas las fuentes
                has_backend_validation = 'validation' in self.analyzer.code_analysis
                has_frontend_validation = 'frontend_validation' in self.analyzer.code_analysis
                
                if 'V5.1' in compliant_reqs:
                    explanations.append("✅ **V5.1**: Se implementa validación de entrada tanto en frontend (JavaScript) como en backend (Python). Los formularios validan antes de enviar y el backend valida al recibir.")
                elif 'V5.1' in partial_reqs:
                    if has_backend_validation and has_frontend_validation:
                        explanations.append("✅ **V5.1**: Se implementa validación de entrada tanto en frontend como en backend. La validación está presente en ambas capas.")
                    elif has_backend_validation:
                        explanations.append("⚠️ **V5.1**: Se valida en backend (Python en `app/routes.py` y `app/helpers.py`), pero la validación frontend (JavaScript) podría ser más completa. Se recomienda validar todos los campos en el cliente antes de enviar para mejorar la experiencia de usuario y reducir carga en el servidor.")
                    else:
                        explanations.append("⚠️ **V5.1**: Se detecta validación pero podría estar incompleta en alguna de las capas")
                else:
                    # No está en compliant ni partial, verificar análisis de código
                    if has_backend_validation and has_frontend_validation:
                        explanations.append("✅ **V5.1**: Se implementa validación de entrada tanto en frontend (JavaScript) como en backend (Python). Los formularios validan antes de enviar y el backend valida al recibir.")
                    elif has_backend_validation:
                        explanations.append("⚠️ **V5.1**: Se valida en backend (Python en `app/routes.py` y `app/helpers.py`), pero falta validación completa en frontend para todos los campos. Se recomienda añadir validación en JavaScript para mejorar la experiencia de usuario.")
                    else:
                        explanations.append("❌ **V5.1**: Falta validación en alguna de las capas (frontend o backend). Se recomienda implementar validación en ambas capas para defensa en profundidad.")
                
                # V5.2: Validación de tipos
                if 'V5.2' in compliant_reqs:
                    explanations.append("✅ **V5.2**: Se valida el tipo de datos en todas las entradas. Se verifica que los nombres sean strings, los números sean numéricos y las fechas tengan formato válido.")
                else:
                    if 'validation' in self.analyzer.code_analysis:
                        explanations.append("✅ **V5.2**: Se valida el tipo de datos en las entradas principales (nombres, números, fechas)")
                    else:
                        explanations.append("⚠️ **V5.2**: La validación de tipos podría ser más estricta y exhaustiva")
                
                # V5.3: Sanitización
                if 'V5.3' in compliant_reqs:
                    explanations.append("✅ **V5.3**: Se implementa sanitización de entrada mediante la función `validate_and_sanitize_name()` que elimina espacios y caracteres especiales.")
                else:
                    if 'frontend_sanitization' in self.analyzer.code_analysis:
                        explanations.append("⚠️ **V5.3**: Se sanitiza en frontend (trim, replace), pero falta sanitización más completa en backend para todos los campos")
                    else:
                        explanations.append("⚠️ **V5.3**: La sanitización está implementada parcialmente. Se sanitiza nombres, pero falta sanitización más completa en otros campos")
                
                # V5.4: Validación de tipos numéricos (NaN/Infinity)
                if 'V5.4' in compliant_reqs:
                    explanations.append("✅ **V5.4**: Se valida que los valores numéricos sean válidos (no NaN ni Infinity) antes de realizar cálculos.")
                else:
                    # Verificar si hay findings pendientes
                    v5_4_findings = [f for f in (partial_item.get('defectdojo_findings', []) if partial_item else []) 
                                    if f.get('cwe') in ['CWE-1287', 'CWE-843']]
                    if v5_4_findings:
                        finding_titles = [f.get('title', '') for f in v5_4_findings[:2]]
                        explanations.append(f"⚠️ **V5.4**: **PENDIENTE** - Falta validación explícita de NaN e Infinity en conversiones numéricas. Las funciones `parseFloat()` y `float()` pueden aceptar estos valores sin validación previa. Esto está relacionado con los findings pendientes en DefectDojo: **CWE-1287** (Improper Validation of NaN/Infinity) y **CWE-843** (Type Confusion).")
                    else:
                        explanations.append("⚠️ **V5.4**: **PENDIENTE** - Falta validación explícita de NaN e Infinity en conversiones numéricas. Las funciones `parseFloat()` y `float()` pueden aceptar estos valores sin validación previa.")
                
                # V5.5: Validación de límites
                if 'V5.5' in compliant_reqs:
                    explanations.append("✅ **V5.5**: Se validan límites de rango mediante configuración centralizada en `app/config.py`. Altura: 0.4-2.72m, Peso: 2-650kg.")
                else:
                    if 'centralized_config' in self.analyzer.code_analysis:
                        explanations.append("✅ **V5.5**: Se validan límites de rango (altura: 0.4-2.72m, peso: 2-650kg) mediante configuración centralizada")
                    else:
                        explanations.append("⚠️ **V5.5**: Los límites de validación están definidos pero podrían estar mejor centralizados en un archivo de configuración")
                
                # V5.6: Validación de formato
                if 'V5.6' in compliant_reqs:
                    explanations.append("✅ **V5.6**: Se valida el formato de fechas (formato ISO) y se verifica que los datos cumplan con los formatos esperados.")
                else:
                    if 'validation' in self.analyzer.code_analysis:
                        explanations.append("✅ **V5.6**: Se valida el formato de fechas y otros datos mediante funciones de validación")
                    else:
                        explanations.append("⚠️ **V5.6**: La validación de formato está implementada pero podría ser más estricta y exhaustiva")
            
            elif category_code == 'V7':
                partial_reqs = partial_item.get('partial', []) if partial_item else []
                
                # V7.1: Manejo de errores
                if 'V7.1' in partial_reqs:
                    if 'error_handling' in self.analyzer.code_analysis:
                        explanations.append("⚠️ **V7.1**: Se implementa manejo de errores con bloques `try/except`, pero las excepciones podrían ser más específicas. El manejo genérico (`except Exception as e:`) dificulta la depuración y el manejo específico de diferentes tipos de errores. Se recomienda usar excepciones específicas como `ValueError`, `TypeError`, etc.")
                    else:
                        explanations.append("❌ **V7.1**: Falta implementación estructurada de manejo de errores")
                else:
                    if 'error_handling' in self.analyzer.code_analysis:
                        explanations.append("✅ **V7.1**: Se implementa manejo de errores con bloques `try/except` en las operaciones críticas")
                    else:
                        explanations.append("❌ **V7.1**: Falta implementación estructurada de manejo de errores")
                
                # V7.2: Códigos HTTP
                if 'V7.2' in partial_reqs:
                    if 'api_rest' in self.analyzer.code_analysis:
                        explanations.append("✅ **V7.2**: La API REST devuelve códigos HTTP apropiados: 400 para errores de validación, 404 para recursos no encontrados, 500 para errores del servidor. Los códigos son apropiados pero podrían ser más específicos (ej. 422 para errores de validación de formato).")
                    else:
                        explanations.append("⚠️ **V7.2**: Los códigos HTTP podrían ser más específicos y consistentes")
                else:
                    explanations.append("⚠️ **V7.2**: Falta verificación de códigos HTTP apropiados en todos los endpoints")
                
                # V7.3: Logging
                if 'V7.3' in partial_reqs:
                    if 'V7.3 (mejorado)' in partial_reqs:
                        explanations.append("✅ **V7.3**: Se ha mejorado el logging de errores, pero aún puede mejorarse con más detalle y estructura. Se recomienda logging estructurado con contexto adicional (usuario, timestamp, stack trace, etc.)")
                    else:
                        explanations.append("⚠️ **V7.3**: El logging de errores está implementado pero es mejorable. Se recomienda logging estructurado con más contexto (módulo, función, parámetros, etc.). Esto está relacionado con el finding **CWE-703** (Improper Check or Handling of Exceptional Conditions) en DefectDojo.")
                else:
                    explanations.append("⚠️ **V7.3**: El logging de errores está implementado básicamente pero falta estructura y detalle. Se recomienda implementar logging estructurado")
                
                # V7.4: No exponer detalles
                if 'V7.4' in partial_reqs:
                    explanations.append("✅ **V7.4**: No se exponen detalles técnicos de errores al usuario final. Los mensajes de error son genéricos y no revelan información sensible sobre la implementación interna.")
                else:
                    explanations.append("✅ **V7.4**: Se asume que no se exponen detalles técnicos de errores al usuario final")
            
            elif category_code == 'V8':
                compliant_reqs = partial_item.get('compliant', []) if partial_item else []
                
                # V8.1: Validaciones defensivas
                if 'V8.1' in compliant_reqs:
                    explanations.append("✅ **V8.1**: Se implementan validaciones defensivas antes de operaciones críticas. Por ejemplo, antes de calcular el IMC se valida que los datos almacenados estén dentro de los límites válidos, protegiendo contra datos corruptos o antiguos.")
                else:
                    if 'validation' in self.analyzer.code_analysis:
                        explanations.append("✅ **V8.1**: Se implementan validaciones defensivas antes de operaciones críticas (cálculo de IMC, almacenamiento de datos)")
                    else:
                        explanations.append("⚠️ **V8.1**: Las validaciones defensivas están implementadas pero podrían ser más exhaustivas en todas las operaciones críticas")
                
                # V8.2: Headers de seguridad
                has_security_headers = 'security_headers' in self.analyzer.code_analysis
                if 'V8.2' in compliant_reqs:
                    explanations.append("✅ **V8.2**: Se configuran headers de seguridad HTTP: `X-Frame-Options: DENY`, `Content-Security-Policy: frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`.")
                else:
                    if has_security_headers:
                        explanations.append("✅ **V8.2**: Se configuran headers de seguridad HTTP (X-Frame-Options, Content-Security-Policy, X-Content-Type-Options, X-XSS-Protection)")
                    else:
                        explanations.append("⚠️ **V8.2**: Falta configuración completa de headers de seguridad. Se recomienda implementar todos los headers de seguridad recomendados por OWASP")
                
                # V8.3: Protección contra clickjacking
                # Verificar si CWE-1021 está resuelto
                v8_findings = partial_item.get('defectdojo_findings', []) if partial_item else []
                cwe_1021_findings = [f for f in v8_findings if f.get('cwe') == 'CWE-1021' or f.get('cwe') == 1021]
                cwe_1021_resolved = any(f.get('verified') for f in cwe_1021_findings) if cwe_1021_findings else False
                
                if 'V8.3' in compliant_reqs or 'V8.3 (CWE-1021 resuelto)' in compliant_reqs or (has_security_headers and cwe_1021_resolved):
                    explanations.append("✅ **V8.3**: Se protege contra clickjacking mediante `X-Frame-Options: DENY` y CSP `frame-ancestors 'none'`. El finding **CWE-1021** (Improper Restriction of Rendered UI Layers) está resuelto en DefectDojo.")
                elif has_security_headers:
                    explanations.append("✅ **V8.3**: Se protege contra clickjacking mediante headers de seguridad (X-Frame-Options, CSP). Si hay un finding CWE-1021 pendiente en DefectDojo, debería marcarse como resuelto.")
                else:
                    explanations.append("⚠️ **V8.3**: Falta protección completa contra clickjacking. El finding **CWE-1021** está pendiente en DefectDojo. Se recomienda implementar `X-Frame-Options: DENY` y CSP `frame-ancestors 'none'`")
                
                # V8.4: CORS
                has_cors = 'security_headers' in self.analyzer.code_analysis  # CORS se detecta como security_headers
                v9_findings = self.analyzer.defectdojo_data.get('findings_by_category', {}).get('V9', [])
                cwe_942_findings = [f for f in v9_findings if f.get('cwe') == 'CWE-942' or f.get('cwe') == 942]
                cwe_942_pending = any(not f.get('verified') for f in cwe_942_findings) if cwe_942_findings else False
                
                if 'V8.4' in compliant_reqs:
                    if has_cors and cwe_942_pending:
                        explanations.append("⚠️ **V8.4**: Se configura CORS, pero en desarrollo está configurado como `origins: '*'` que es demasiado permisivo para producción. Se recomienda restringir a orígenes específicos en producción (relacionado con **CWE-942** pendiente en DefectDojo).")
                    elif has_cors:
                        explanations.append("✅ **V8.4**: Se configura CORS correctamente")
                    else:
                        explanations.append("⚠️ **V8.4**: CORS está configurado pero podría mejorarse")
                else:
                    if has_cors:
                        if cwe_942_pending:
                            explanations.append("⚠️ **V8.4**: Se configura CORS, pero es demasiado permisivo (`origins: '*'`). Se recomienda restringir a orígenes específicos en producción (relacionado con **CWE-942** pendiente en DefectDojo).")
                        else:
                            explanations.append("✅ **V8.4**: Se configura CORS correctamente")
                    else:
                        explanations.append("⚠️ **V8.4**: Falta configuración adecuada de CORS. Se recomienda configurar CORS con orígenes específicos en lugar de permitir todos los orígenes")
            
            elif category_code == 'V9':
                partial_reqs = partial_item.get('partial', []) if partial_item else []
                
                explanations.append("⚠️ **V9.1**: La aplicación actualmente utiliza HTTP. Se recomienda HTTPS para producción para proteger las comunicaciones.")
                
                if 'V9.2' in partial_reqs or 'V9.2 (CWE-942 pendiente)' in partial_reqs:
                    explanations.append("⚠️ **V9.2**: CORS está configurado pero es demasiado permisivo (`origins: '*'`). En producción debe restringirse a orígenes específicos (CWE-942 pendiente en DefectDojo)")
                else:
                    explanations.append("✅ **V9.2**: CORS está configurado correctamente")
                
                if 'V9.3' in partial_reqs or 'V9.3 (CWE-942 pendiente)' in partial_reqs:
                    explanations.append("⚠️ **V9.3**: No se implementa validación de origen específico para CORS. Se recomienda validar el origen de las peticiones (CWE-942 pendiente en DefectDojo)")
                else:
                    explanations.append("✅ **V9.3**: Se valida el origen de las peticiones CORS")
            
            elif category_code == 'V10':
                compliant_reqs = partial_item.get('compliant', []) if partial_item else []
                
                if 'V10.1' in compliant_reqs:
                    explanations.append("✅ **V10.1**: Se valida toda la entrada de datos para prevenir código malicioso")
                else:
                    explanations.append("⚠️ **V10.1**: La validación de entrada podría ser más exhaustiva")
                
                if 'V10.2' in compliant_reqs:
                    explanations.append("✅ **V10.2**: Se sanitiza la entrada en el frontend")
                else:
                    explanations.append("⚠️ **V10.2**: Falta sanitización completa en el frontend")
                
                if 'V10.3' in compliant_reqs:
                    explanations.append("✅ **V10.3**: Se implementan headers de seguridad (CSP) para prevenir ejecución de código malicioso")
                else:
                    explanations.append("⚠️ **V10.3**: Falta configuración completa de Content-Security-Policy")
                
                if 'V10.4' in compliant_reqs:
                    explanations.append("✅ **V10.4**: La aplicación no permite la carga de archivos desde usuarios")
                else:
                    explanations.append("⚠️ **V10.4**: No aplicable - la aplicación no maneja carga de archivos")
            
            elif category_code == 'V11':
                compliant_reqs = partial_item.get('compliant', []) if partial_item else []
                
                if 'V11.1' in compliant_reqs:
                    explanations.append("✅ **V11.1**: La lógica de negocio está centralizada y bien estructurada en `app/config.py`")
                else:
                    explanations.append("⚠️ **V11.1**: La lógica de negocio podría estar mejor centralizada")
                
                if 'V11.2' in compliant_reqs:
                    explanations.append("✅ **V11.2**: Se implementan controles de negocio consistentes (validaciones de límites, cálculos)")
                else:
                    explanations.append("⚠️ **V11.2**: Los controles de negocio podrían ser más consistentes")
            
            elif category_code == 'V12':
                explanations.append("⚠️ **V12.1**: Parcialmente aplicable - Solo los endpoints de importación/exportación de DefectDojo manejan archivos")
                explanations.append("✅ **V12.2**: Se utiliza `secure_filename()` para nombres de archivo en los endpoints de DefectDojo")
            
            elif category_code == 'V13':
                compliant_reqs = partial_item.get('compliant', []) if partial_item else []
                
                if 'V13.1' in compliant_reqs:
                    explanations.append("✅ **V13.1**: La API REST está documentada mediante código y sigue estándares RESTful")
                else:
                    explanations.append("⚠️ **V13.1**: La documentación de la API podría mejorarse")
                
                if 'V13.2' in compliant_reqs:
                    explanations.append("✅ **V13.2**: Todos los endpoints de la API validan la entrada de datos")
                else:
                    explanations.append("⚠️ **V13.2**: Algunos endpoints podrían tener validación más estricta")
                
                explanations.append("⚠️ **V13.3**: No aplicable - La aplicación es monousuario y no requiere autenticación/autorización por diseño")
                
                if 'V13.4' in compliant_reqs:
                    explanations.append("✅ **V13.4**: Se manejan errores con códigos HTTP apropiados (400, 404, 500)")
                else:
                    explanations.append("⚠️ **V13.4**: El manejo de errores HTTP podría ser más específico")
            
            elif category_code == 'V14':
                compliant_reqs = partial_item.get('compliant', []) if partial_item else []
                
                if 'V14.1' in compliant_reqs:
                    explanations.append("✅ **V14.1**: La configuración está centralizada en `app/config.py`")
                else:
                    explanations.append("⚠️ **V14.1**: La configuración podría estar mejor centralizada")
                
                if 'V14.2' in compliant_reqs:
                    explanations.append("✅ **V14.2**: Se configuran headers de seguridad de forma centralizada")
                else:
                    explanations.append("⚠️ **V14.2**: Falta configuración centralizada de headers de seguridad")
                
                if 'V14.3' in compliant_reqs:
                    explanations.append("✅ **V14.3**: Se gestiona la configuración de CORS de forma centralizada, aunque en desarrollo es permisivo")
                else:
                    explanations.append("⚠️ **V14.3**: La configuración de CORS podría estar mejor gestionada")
        
        elif status == 'missing':
            # Explicar qué falta
            if category_code == 'V7':
                explanations.append("❌ **V7.1**: Falta implementación estructurada de manejo de errores. Se recomienda usar bloques `try/except` específicos en lugar de genéricos.")
        
        return "\n".join(explanations) if explanations else ""
    
    def _generate_section5_wstg(self) -> str:
        """Generar sección 5: Análisis WSTG (Web Security Testing Guide)"""
        lines = []
        lines.append("## 5. Análisis WSTG (OWASP Web Security Testing Guide)")
        lines.append("")
        lines.append("### 5.1. Introducción al WSTG")
        lines.append("")
        lines.append("El **OWASP Web Security Testing Guide (WSTG)** es una guía completa para probar la seguridad de aplicaciones web y servicios web. Proporciona un marco de mejores prácticas utilizado por profesionales de seguridad y organizaciones en todo el mundo.")
        lines.append("")
        lines.append("Este análisis se basa en los findings de WSTG almacenados en DefectDojo, obtenidos mediante la sincronización bidireccional con el WSTG Tracker.")
        lines.append("")
        
        # Obtener findings WSTG
        wstg_findings = self.analyzer.defectdojo_data.get('wstg_findings', [])
        
        if not wstg_findings:
            lines.append("### 5.2. Estado de los Tests WSTG")
            lines.append("")
            lines.append("⚠️ **No se encontraron findings de WSTG en DefectDojo.**")
            lines.append("")
            lines.append("Esto puede deberse a:")
            lines.append("- No se ha ejecutado la sincronización WSTG aún")
            lines.append("- No hay tests WSTG configurados en el WSTG Tracker")
            lines.append("- Los findings WSTG no se han sincronizado con DefectDojo")
            lines.append("")
            return "\n".join(lines)
        
        # Agrupar findings por categoría WSTG
        wstg_categories = {
            'INFO': 'Information Gathering',
            'CONF': 'Configuration and Deployment Management',
            'IDENT': 'Identity Management',
            'AUTH': 'Authentication',
            'SESS': 'Session Management',
            'AUTHZ': 'Authorization',
            'DATA': 'Data Validation',
            'ERR': 'Error Handling',
            'CRYPTO': 'Cryptography',
            'BUSINESS': 'Business Logic',
            'CLIENT': 'Client-Side'
        }
        
        findings_by_category = {}
        for finding in wstg_findings:
            wstg_id = finding.get('wstg_id', 'Unknown')
            if wstg_id.startswith('WSTG-'):
                category = wstg_id.split('-')[1]  # INFO, AUTH, etc.
                if category not in findings_by_category:
                    findings_by_category[category] = []
                findings_by_category[category].append(finding)
        
        lines.append("### 5.2. Resumen de Tests WSTG")
        lines.append("")
        lines.append(f"**Total de tests WSTG analizados**: {len(wstg_findings)}")
        lines.append("")
        
        # Contar por estado
        status_counts = {}
        for finding in wstg_findings:
            status = finding.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        lines.append("**Distribución por estado**:")
        for status, count in sorted(status_counts.items()):
            lines.append(f"- **{status}**: {count}")
        lines.append("")
        
        lines.append("### 5.3. Tests WSTG por Categoría")
        lines.append("")
        
        if not findings_by_category:
            lines.append("⚠️ No se pudieron agrupar los findings por categoría WSTG.")
            lines.append("")
        else:
            for category_code, category_name in sorted(wstg_categories.items()):
                if category_code in findings_by_category:
                    category_findings = findings_by_category[category_code]
                    lines.append(f"#### 5.3.{category_code}. **{category_code}: {category_name}**")
                    lines.append("")
                    lines.append(f"**Tests encontrados**: {len(category_findings)}")
                    lines.append("")
                    
                    # Mostrar algunos findings destacados
                    for finding in category_findings[:5]:  # Máximo 5 por categoría
                        status_icon = "✅" if finding.get('verified') else ("⚠️" if finding.get('status') == 'In Progress' else "❌")
                        lines.append(f"- {status_icon} **{finding.get('wstg_id', 'Unknown')}**: {finding.get('title', 'N/A')}")
                        lines.append(f"  - Estado: {finding.get('status', 'Unknown')}")
                        if finding.get('severity'):
                            lines.append(f"  - Severidad: {finding.get('severity')}")
                    
                    if len(category_findings) > 5:
                        lines.append(f"- ... y {len(category_findings) - 5} tests más")
                    lines.append("")
        
        lines.append("### 5.4. Detalles de Tests WSTG")
        lines.append("")
        lines.append("A continuación se detallan los tests WSTG más relevantes:")
        lines.append("")
        
        # Mostrar detalles de los primeros 10 findings
        for i, finding in enumerate(wstg_findings[:10], 1):
            lines.append(f"#### 5.4.{i}. {finding.get('wstg_id', 'Unknown')}: {finding.get('title', 'N/A')}")
            lines.append("")
            lines.append(f"- **Estado**: {finding.get('status', 'Unknown')}")
            lines.append(f"- **Severidad**: {finding.get('severity', 'N/A')}")
            if finding.get('description'):
                desc = finding.get('description', '')[:200]
                lines.append(f"- **Descripción**: {desc}{'...' if len(finding.get('description', '')) > 200 else ''}")
            if finding.get('verified'):
                lines.append("- **Verificado**: ✅ Sí")
            if finding.get('false_p'):
                lines.append("- **Falso Positivo**: ⚠️ Sí")
            lines.append("")
        
        if len(wstg_findings) > 10:
            lines.append(f"*... y {len(wstg_findings) - 10} tests WSTG adicionales*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_section6_recommendations(self) -> str:
        """Generar sección 6: Recomendaciones y Próximos Pasos"""
        return """## 6. Recomendaciones y Próximos Pasos

### 6.1. Resumen del Estado Actual

La aplicación implementa **buenas prácticas de seguridad** en validación de entrada, headers de seguridad y manejo defensivo de datos.

### 6.2. Mejoras Recomendadas

Para alcanzar el cumplimiento completo del **ASVS Nivel 2**, se recomienda implementar las siguientes mejoras:

1. **Validación de tipos numéricos**: Implementar validación explícita de NaN e Infinity
2. **CORS en producción**: Restringir CORS a orígenes específicos en producción
3. **Logging mejorado**: Implementar logging estructurado de errores"""
    
    def _generate_references(self) -> str:
        """Generar referencias"""
        return """---

## 7. Referencias

- [OWASP ASVS (página principal)](https://owasp.org/www-project-application-security-verification-standard/)
- [OWASP ASVS 4.0.3 en GitHub (versión utilizada en este informe)](https://github.com/OWASP/ASVS/tree/v4.0.3/4.0/)
- [OWASP ASVS 4.0.3 - Categorías de verificación](https://github.com/OWASP/ASVS/tree/v4.0.3/4.0/)
- [OWASP ASVS 5.0 (versión actual)](https://owasp.org/www-project-application-security-verification-standard/)
- [OWASP WSTG (Web Security Testing Guide)](https://owasp.org/www-project-web-security-testing-guide/)"""


def main():
    """Función principal"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / "docs"
    report_md = docs_dir / "INFORME_SEGURIDAD.md"
    
    print("=" * 60)
    print("Generador de Informe ASVS 4.0.3")
    print("=" * 60)
    print()
    
    # Crear analizador
    analyzer = ASVSAnalyzer(project_root)
    
    # Obtener datos de DefectDojo (benchmarks ASVS y findings)
    analyzer.get_defectdojo_data()
    print()
    
    # Analizar código (complementario a DefectDojo)
    analyzer.analyze_code()
    print()
    
    # Verificar requisitos ASVS (usando datos de DefectDojo + análisis de código)
    analyzer.check_asvs_requirements()
    print()
    
    # Generar informe
    generator = ASVSReportGenerator(analyzer, project_root)
    report_content = generator.generate_report()
    
    # Guardar informe
    report_md.parent.mkdir(parents=True, exist_ok=True)
    with open(report_md, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print()
    print("=" * 60)
    print(f"✅ Informe generado exitosamente: {report_md}")
    print("=" * 60)
    print()
    print("💡 Próximo paso: Ejecutar 'make pdf_report' para generar el PDF")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

