# Script PowerShell para limpiar TODO y volver al estado como recien clonado
# ADVERTENCIA: Este script es DESTRUCTIVO. Elimina todos los datos de Docker, contenedores, imagenes, etc.

Write-Host "ADVERTENCIA" -ForegroundColor Red
Write-Host ""
Write-Host "Este comando eliminara:" -ForegroundColor Yellow
Write-Host "  - Todos los contenedores Docker del proyecto"
Write-Host "  - Todas las imagenes Docker del proyecto"
Write-Host "  - Todos los volumenes Docker del proyecto"
Write-Host "  - Todos los datos de PostgreSQL, Redis y DefectDojo"
Write-Host "  - Todos los dumps SQL generados"
Write-Host "  - El entorno virtual (venv/)"
Write-Host "  - Archivos temporales de desarrollo"
Write-Host ""
Write-Host "El proyecto volvera al estado como recien clonado." -ForegroundColor Yellow
Write-Host ""

$confirmacion = Read-Host "Estas seguro de que deseas continuar? (escribe 'si' para confirmar)"

if ($confirmacion -ne "si") {
    Write-Host ""
    Write-Host "Operacion cancelada." -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "Iniciando limpieza completa..." -ForegroundColor Cyan
Write-Host ""

$count = 0

# Paso 1: Detener y eliminar contenedores Docker
Write-Host "Paso 1/8: Deteniendo y eliminando contenedores Docker..." -ForegroundColor Yellow
if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    $env:COMPOSE_PROJECT_NAME = if ($env:COMPOSE_PROJECT_NAME) { $env:COMPOSE_PROJECT_NAME } else { "medical_register" }
    $env:COMPOSE_DOCKER_CLI_BUILD = if ($env:COMPOSE_DOCKER_CLI_BUILD) { $env:COMPOSE_DOCKER_CLI_BUILD } else { "0" }
    $env:DOCKER_BUILDKIT = if ($env:DOCKER_BUILDKIT) { $env:DOCKER_BUILDKIT } else { "0" }
    
    # Detener y eliminar contenedores
    docker-compose down --volumes --remove-orphans 2>$null
    docker-compose --profile defectdojo down --volumes --remove-orphans 2>$null
    
    Write-Host "  [OK] Contenedores detenidos y eliminados" -ForegroundColor Gray
    $count++
    
    # Eliminar redes huérfanas del proyecto
    Write-Host ""
    Write-Host "   Eliminando redes huerfanas..." -ForegroundColor Gray
    $projectName = if ($env:COMPOSE_PROJECT_NAME) { $env:COMPOSE_PROJECT_NAME } else { "medical_register" }
    $networks = docker network ls --format "{{.Name}}" | Select-String -Pattern "$projectName|defectdojo"
    
    if ($networks) {
        $networks | ForEach-Object {
            docker network rm $_.ToString().Trim() 2>$null
        }
        Write-Host "  [OK] Redes huerfanas eliminadas" -ForegroundColor Gray
    }
}

# Paso 2: Eliminar imagenes del proyecto
Write-Host ""
Write-Host "Paso 2/8: Eliminando imagenes Docker del proyecto..." -ForegroundColor Yellow
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $projectName = if ($env:COMPOSE_PROJECT_NAME) { $env:COMPOSE_PROJECT_NAME } else { "medical_register" }
    
    # Buscar imagenes relacionadas con el proyecto
    $images = docker images --format "{{.Repository}}:{{.Tag}}" | Select-String -Pattern "medical_register|$projectName"
    
    if ($images) {
        $images | ForEach-Object {
            docker rmi -f $_.ToString() 2>$null
        }
        Write-Host "  [OK] Imagenes eliminadas" -ForegroundColor Gray
        $count++
    } else {
        Write-Host "  [INFO] No se encontraron imagenes del proyecto para eliminar" -ForegroundColor Gray
    }
}

# Paso 3: Eliminar datos de PostgreSQL
Write-Host ""
Write-Host "Paso 3/8: Eliminando datos de PostgreSQL..." -ForegroundColor Yellow
if (Test-Path "data\postgres") {
    Remove-Item "data\postgres" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Directorio data/postgres/ eliminado" -ForegroundColor Gray
    $count++
}

# Paso 4: Eliminar datos de Redis
Write-Host ""
Write-Host "Paso 4/8: Eliminando datos de Redis..." -ForegroundColor Yellow
if (Test-Path "data\redis") {
    Remove-Item "data\redis" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Directorio data/redis/ eliminado" -ForegroundColor Gray
    $count++
}

# Paso 5: Eliminar datos de DefectDojo
Write-Host ""
Write-Host "Paso 5/8: Eliminando datos de DefectDojo..." -ForegroundColor Yellow
if (Test-Path "data\defectdojo") {
    Remove-Item "data\defectdojo" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Directorio data/defectdojo/ eliminado" -ForegroundColor Gray
    $count++
}

# Paso 6: Eliminar dumps SQL generados (excepto el inicial)
Write-Host ""
Write-Host "Paso 6/8: Eliminando dumps SQL generados..." -ForegroundColor Yellow
if (Test-Path "data") {
    $dumpFiles = Get-ChildItem -Path "data" -Recurse -Filter "*_db_dump.sql" -ErrorAction SilentlyContinue | 
        Where-Object { $_.Name -ne "defectdojo_db_initial.sql" }
    
    if ($dumpFiles) {
        $dumpFiles | Remove-Item -Force -ErrorAction SilentlyContinue
        $dumpCount = ($dumpFiles | Measure-Object).Count
        Write-Host "  [OK] $dumpCount dumps SQL eliminados" -ForegroundColor Gray
        $count++
    } else {
        Write-Host "  [INFO] No se encontraron dumps SQL para eliminar" -ForegroundColor Gray
    }
}

# Paso 7: Eliminar entorno virtual
Write-Host ""
Write-Host "Paso 7/8: Eliminando entorno virtual..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Remove-Item "venv" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Directorio venv/ eliminado" -ForegroundColor Gray
    $count++
}

# Paso 8: Eliminar .env (se recreara automaticamente)
Write-Host ""
Write-Host "Paso 8/8: Limpiando archivo .env..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Remove-Item ".env" -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Archivo .env eliminado (se recreara automaticamente)" -ForegroundColor Gray
    $count++
}

# Ejecutar limpieza de archivos temporales
Write-Host ""
Write-Host "Ejecutando limpieza de archivos temporales..." -ForegroundColor Yellow
if (Test-Path "scripts\clean_temp.ps1") {
    & "scripts\clean_temp.ps1"
}

Write-Host ""
Write-Host "Limpieza completa finalizada" -ForegroundColor Green
Write-Host ""
Write-Host "El proyecto ha vuelto al estado como recien clonado." -ForegroundColor Cyan
Write-Host ""
Write-Host "Para volver a iniciar el proyecto, ejecuta:" -ForegroundColor Yellow
Write-Host "  .\scripts\setup.ps1  # Windows/PowerShell"
Write-Host "  .\make.ps1           # Luego arranca con make.ps1"

