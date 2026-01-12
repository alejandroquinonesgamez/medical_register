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

### Limpieza
- **`clean_temp.sh`** / **`clean_temp.ps1`** - Limpia archivos temporales
- **`clean_all.sh`** / **`clean_all.ps1`** - Limpia contenedores, imágenes y volúmenes Docker

### Generación de Documentación

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

### Limpieza
```bash
# Limpiar archivos temporales
./scripts/clean_temp.sh

# Limpiar todo (contenedores, imágenes, volúmenes)
./scripts/clean_all.sh
```

### Generación de Documentos
```bash
# Regenerar imágenes Mermaid
python scripts/generate_mermaid_image.py docs/mockups/user-manual.mmd
```

## Notas

- Los scripts de setup configuran automáticamente el archivo `.env` para Docker Compose
- Los scripts de limpieza ayudan a mantener el proyecto organizado

