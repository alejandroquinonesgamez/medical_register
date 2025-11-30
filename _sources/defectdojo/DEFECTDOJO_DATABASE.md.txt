# Gestión de Base de Datos de DefectDojo

Este documento explica cómo exportar e importar la base de datos de DefectDojo para uso en Raspberry Pi o entornos donde no se quiere depender del script de inicialización.

## Dump Inicial del Repositorio

El repositorio incluye un dump inicial de la base de datos en `data/defectdojo_db_initial.sql`. Este dump contiene:

- Base de datos con todas las tablas creadas
- Usuario admin (admin/admin)
- 6 findings de CWE pre-configurados con `found_by` asignado
- Product Type, Product, Engagement y Test configurados
- Sin duplicados

**Para usar el dump inicial:**

```bash
./scripts/load_defectdojo_db.sh
```

O explícitamente:

```bash
./scripts/load_defectdojo_db.sh data/defectdojo_db_initial.sql
```

## Exportar Base de Datos

Para exportar la base de datos actual de DefectDojo a un archivo SQL:

```bash
./scripts/export_defectdojo_db.sh
```

Esto creará un archivo `data/defectdojo_db_dump.sql` con todos los datos.

También puedes especificar una ruta personalizada:

```bash
./scripts/export_defectdojo_db.sh /ruta/personalizada/dump.sql
```

## Importar Base de Datos

Para cargar un dump SQL en DefectDojo:

```bash
./scripts/load_defectdojo_db.sh
```

O especificando la ruta del dump:

```bash
./scripts/load_defectdojo_db.sh /ruta/al/dump.sql
```

**Nota**: Este script reiniciará automáticamente el contenedor de DefectDojo después de cargar el dump.

## Uso en Raspberry Pi

### Opción 1: Usar el dump inicial del repositorio (Más Simple)

1. **Clona el repositorio en tu Raspberry Pi** (el dump inicial ya está incluido)

2. **Carga el dump inicial:**
   ```bash
   ./scripts/load_defectdojo_db.sh
   ```

3. **El script de inicialización detectará que hay datos y no creará findings duplicados.**

### Opción 2: Cargar dump personalizado

1. **Exporta el dump en tu máquina de desarrollo:**
   ```bash
   ./scripts/export_defectdojo_db.sh
   ```

2. **Copia el dump a tu Raspberry Pi:**
   ```bash
   scp data/defectdojo_db_dump.sql usuario@raspberry-pi:/ruta/del/proyecto/data/
   ```

3. **En la Raspberry Pi, carga el dump:**
   ```bash
   ./scripts/load_defectdojo_db.sh data/defectdojo_db_dump.sql
   ```

### Opción 2: Usar el dump como datos iniciales

Si quieres que el dump se cargue automáticamente cuando se inicializa PostgreSQL por primera vez:

1. **Exporta el dump:**
   ```bash
   ./scripts/export_defectdojo_db.sh
   ```

2. **Copia el dump al directorio de inicialización de PostgreSQL:**
   ```bash
   cp data/defectdojo_db_dump.sql data/postgres/init.sql
   ```

3. **Elimina el directorio de datos de PostgreSQL para forzar reinicialización:**
   ```bash
   rm -rf data/postgres/*
   ```

4. **Reinicia los contenedores:**
   ```bash
   make up-defectdojo
   ```

   PostgreSQL cargará automáticamente el dump al inicializarse.

## Comportamiento del Script de Inicialización

El script `init_defectdojo_internal.py` ahora verifica si la base de datos ya contiene datos:

- **Si hay datos**: Salta la creación de findings para evitar duplicados
- **Si está vacía**: Crea los findings normalmente

Esto permite usar el dump sin conflictos con el script de inicialización.

## Estructura del Dump

El dump SQL contiene:
- Todas las tablas de DefectDojo
- Datos de usuarios, productos, engagements, tests
- Todos los findings con sus configuraciones
- Relaciones entre entidades
- Configuraciones del sistema

## Tamaño Típico

Un dump completo de DefectDojo con los 6 findings de ejemplo suele ocupar aproximadamente **1-2 MB**.

## Ventajas de Usar Dump

✅ **Independencia del script**: No necesitas ejecutar el script de inicialización  
✅ **Datos pre-configurados**: Todos los findings y configuraciones ya están listos  
✅ **Portabilidad**: Fácil de mover entre entornos  
✅ **Backup**: Puedes usar el dump como respaldo  
✅ **Raspberry Pi**: Ideal para entornos con recursos limitados  

## Notas Importantes

⚠️ **El dump incluye credenciales**: Asegúrate de proteger el archivo si contiene datos sensibles  
⚠️ **Versión de PostgreSQL**: El dump debe ser compatible con la versión de PostgreSQL en el destino  
⚠️ **Migraciones**: Asegúrate de que las migraciones de Django estén aplicadas antes de cargar el dump  

