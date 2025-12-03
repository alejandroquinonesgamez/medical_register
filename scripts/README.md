# Scripts del Proyecto

Este directorio contiene todos los scripts de utilidad del proyecto.

## Scripts Activos

### Configuración Inicial
- **`setup.sh`** - Script de configuración inicial para Linux/Mac/Git Bash
- **`setup.ps1`** - Script de configuración inicial para Windows/PowerShell
  - Crea directorios de datos
  - Configura archivo `.env` para Docker Compose
  - Verifica Docker
  - Construye imagen de la aplicación

### Gestión de DefectDojo

#### Inicialización
- **`init_defectdojo_internal.py`** - Script ejecutado dentro del contenedor de DefectDojo al arrancar
  - Ejecuta migraciones
  - Crea usuario admin
  - Recolecta archivos estáticos
  - Gestiona findings (llama a `manage_findings.py`)
  
- **`init_defectdojo_empty.py`** - Script para inicializar DefectDojo sin crear findings
  - Usado por `make initDefectDojo` y `.\make.ps1 initDefectDojo`
  - Solo migraciones, admin user y archivos estáticos

#### Gestión de Findings
- **`manage_findings.py`** - ⭐ **Script consolidado** para gestionar todos los findings
  - Crea todos los findings inicialmente como activos
  - Marca findings resueltos con fechas históricas
  - Actualiza descripciones y mitigaciones
  - Reemplaza a los scripts antiguos eliminados

#### Base de Datos
- **`export_defectdojo_db.sh`** - Exporta la base de datos de DefectDojo a un dump SQL
  - Usado por el endpoint `/api/defectdojo/export-dump`
  - También puede ejecutarse manualmente

- **`load_defectdojo_db.sh`** - Carga un dump SQL en la base de datos de DefectDojo
  - Útil para restaurar backups o cargar datos iniciales
  - Referenciado en documentación

- **`reset_defectdojo.sh`** - Reinicializa DefectDojo manualmente
  - Ejecuta migraciones
  - Recolecta archivos estáticos
  - Resetea contraseña del admin
  - Mencionado en README.md

### Generación de Documentación

- **`generate_pdf_report.py`** - Genera PDF del informe de seguridad ASVS
  - Usado por `make pdf_ASVS` y `.\make.ps1 pdf_ASVS`
  - Usado por el endpoint `/api/defectdojo/generate-pdf`
  - Genera PDF con fecha en `docs/informes/`

- **`generate_mermaid_image.py`** - Regenera imágenes PNG desde diagramas Mermaid (.mmd)
  - Convierte archivos `.mmd` a `.png` usando la API de mermaid.ink
  - Útil para actualizar mockups y diagramas

## Uso Recomendado

### Configuración Inicial
```bash
# Linux/Mac/Git Bash
./scripts/setup.sh

# Windows/PowerShell
.\scripts\setup.ps1
```

### Gestión de DefectDojo
```bash
# Usar make/make.ps1 (recomendado)
make update          # Flujo completo con findings
make initDefectDojo  # DefectDojo vacío sin findings

# O directamente
.\make.ps1 update
.\make.ps1 initDefectDojo
```

### Generación de Documentos
```bash
# PDF del informe
make pdf_ASVS

# Regenerar imágenes Mermaid
python scripts/generate_mermaid_image.py docs/mockups/user-manual.mmd
```

## Notas

- Todos los scripts de findings están consolidados en `manage_findings.py`
- Los scripts de setup configuran automáticamente el archivo `.env` para Docker Compose
- Los scripts de base de datos (`export`, `load`, `reset`) son independientes y pueden ejecutarse manualmente cuando sea necesario

