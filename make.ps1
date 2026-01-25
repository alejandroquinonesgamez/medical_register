# Script PowerShell equivalente al Makefile
#
# Este script replica la funcionalidad del Makefile para usuarios de Windows/PowerShell.
# Gestiona el despliegue y operación de la aplicación médica en producción.
#
# Características principales:
# - Configuración automática de Docker Compose (incluyendo .env)
# - Gestión de contenedores de la aplicación principal
# - Soluciona problemas con caracteres especiales en rutas mediante COMPOSE_PROJECT_NAME
#
# Uso: .\make.ps1 [comando]
# Ejemplos:
#   .\make.ps1 help          # Mostrar ayuda
#   .\make.ps1 default       # Arrancar aplicación principal
#   .\make.ps1 memory        # Arrancar sin BD (memory)
#   .\make.ps1 db            # Arrancar con BD (sqlite/sqlcipher)
#   .\make.ps1 test          # Ejecutar tests (Python 3)
#   .\make.ps1 default       # Arrancar aplicación principal

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Configurar variables de entorno para Docker Compose
# Esto soluciona problemas con caracteres especiales en rutas
function Initialize-DockerComposeEnv {
    $envFile = Join-Path $PSScriptRoot ".env"
    
    # Si no existe .env, crearlo
    if (-not (Test-Path $envFile)) {
        $envExample = Join-Path $PSScriptRoot "docker-compose.env.example"
        if (Test-Path $envExample) {
            Copy-Item $envExample $envFile
        } else {
            # Crear .env básico
            @"
COMPOSE_PROJECT_NAME=medical_register
COMPOSE_DOCKER_CLI_BUILD=0
DOCKER_BUILDKIT=0
"@ | Out-File -FilePath $envFile -Encoding UTF8
        }
    }
    
    # Cargar variables de entorno desde .env
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^([^#][^=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                if ($key -and $value) {
                    [Environment]::SetEnvironmentVariable($key, $value, "Process")
                }
            }
        }
    }
    
    # Valores por defecto si no están en .env
    if (-not $env:COMPOSE_DOCKER_CLI_BUILD) {
        $env:COMPOSE_DOCKER_CLI_BUILD = "0"
    }
    if (-not $env:DOCKER_BUILDKIT) {
        $env:DOCKER_BUILDKIT = "0"
    }
    if (-not $env:COMPOSE_PROJECT_NAME) {
        $env:COMPOSE_PROJECT_NAME = "medical_register"
    }
}

# Inicializar entorno de Docker Compose al cargar el script
Initialize-DockerComposeEnv

function Test-Requirements {
    Write-Host "Verificando requisitos previos..." -ForegroundColor Cyan
    Write-Host ""
    
    $allOk = $true
    
    # Verificar Docker
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Host "  Docker: " -NoNewline -ForegroundColor Green
            Write-Host $dockerVersion
        } else {
            Write-Host "  Docker: " -NoNewline -ForegroundColor Red
            Write-Host "No instalado"
            $allOk = $false
        }
    } catch {
        Write-Host "  Docker: " -NoNewline -ForegroundColor Red
        Write-Host "No instalado o no disponible"
        $allOk = $false
    }
    
    # Verificar Docker Compose
    try {
        $composeVersion = docker-compose --version 2>$null
        if ($composeVersion) {
            Write-Host "  Docker Compose: " -NoNewline -ForegroundColor Green
            Write-Host $composeVersion
        } else {
            Write-Host "  Docker Compose: " -NoNewline -ForegroundColor Red
            Write-Host "No instalado"
            $allOk = $false
        }
    } catch {
        Write-Host "  Docker Compose: " -NoNewline -ForegroundColor Red
        Write-Host "No instalado o no disponible"
        $allOk = $false
    }
    
    # Verificar que Docker esté corriendo
    try {
        $dockerRunning = docker ps 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Docker Daemon: " -NoNewline -ForegroundColor Green
            Write-Host "Corriendo"
        } else {
            Write-Host "  Docker Daemon: " -NoNewline -ForegroundColor Red
            Write-Host "No esta corriendo"
            $allOk = $false
        }
    } catch {
        Write-Host "  Docker Daemon: " -NoNewline -ForegroundColor Red
        Write-Host "No se pudo verificar"
        $allOk = $false
    }
    
    Write-Host ""
    if ($allOk) {
        Write-Host "Todos los requisitos estan instalados y funcionando" -ForegroundColor Green
        return $true
    } else {
        Write-Host "Algunos requisitos faltan. Por favor, instala Docker y Docker Compose." -ForegroundColor Red
        Write-Host "Visita: https://docs.docker.com/get-docker/" -ForegroundColor Yellow
        return $false
    }
}

function Show-Help {
    Write-Host ""
    Write-Host "Comandos disponibles:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  default          " -NoNewline -ForegroundColor Yellow
    Write-Host "Arrancar solo la aplicacion principal (por defecto)"
    Write-Host "  memory           " -NoNewline -ForegroundColor Yellow
    Write-Host "Arrancar sin base de datos (memory)"
    Write-Host "  db               " -NoNewline -ForegroundColor Yellow
    Write-Host "Arrancar con base de datos (sqlite/sqlcipher)"
    Write-Host "  test             " -NoNewline -ForegroundColor Yellow
    Write-Host "Ejecutar tests (Python 3)"
    Write-Host "  logs             " -NoNewline -ForegroundColor Yellow
    Write-Host "Ver logs de la aplicacion principal"
    Write-Host "  ps               " -NoNewline -ForegroundColor Yellow
    Write-Host "Ver estado de todos los contenedores"
    Write-Host "  down             " -NoNewline -ForegroundColor Yellow
    Write-Host "Detener todos los servicios"
    Write-Host "  clean-temp       " -NoNewline -ForegroundColor Yellow
    Write-Host "Limpiar archivos temporales del proyecto"
    Write-Host "  fix-containers   " -NoNewline -ForegroundColor Yellow
    Write-Host "Solucionar error ContainerConfig (Raspberry Pi)"
    Write-Host "  clean-all        " -NoNewline -ForegroundColor Yellow
    Write-Host "Limpiar TODO y volver al estado como recien clonado (DESTRUCTIVO)"
    Write-Host "  purge            " -NoNewline -ForegroundColor Yellow
    Write-Host "Detener servicios y limpiar TODO (DESTRUCTIVO: down + clean-all)"
    Write-Host "  check            " -NoNewline -ForegroundColor Yellow
    Write-Host "Verificar requisitos previos (Docker, Docker Compose)"
    Write-Host "  help             " -NoNewline -ForegroundColor Yellow
    Write-Host "Mostrar esta ayuda"
    Write-Host ""
    Write-Host "Ejemplos:" -ForegroundColor Cyan
    Write-Host "  .\make.ps1                # Muestra la ayuda"
    Write-Host "  .\make.ps1 check          # Verifica requisitos"
    Write-Host "  .\make.ps1 default        # Arranca la aplicacion principal"
    Write-Host "  .\make.ps1 memory         # Arranca sin BD (memory)"
    Write-Host "  .\make.ps1 db             # Arranca con BD (sqlite/sqlcipher)"
    Write-Host "  .\make.ps1 test           # Ejecuta tests (Python 3)"
    Write-Host ""
}

function Start-Default {
    Write-Host "Arrancando aplicacion principal..." -ForegroundColor Cyan
    docker-compose up -d --build
    Write-Host ""
    Write-Host "Aplicacion principal arrancada" -ForegroundColor Green
    Write-Host "Accede a la aplicacion en: http://localhost:5001" -ForegroundColor Cyan
}

function Start-Memory {
    Write-Host "Arrancando aplicacion (modo memoria)..." -ForegroundColor Cyan
    $env:STORAGE_BACKEND = "memory"
    docker-compose up -d --build
    Write-Host ""
    Write-Host "Aplicacion principal arrancada (memory)" -ForegroundColor Green
    Write-Host "Accede a la aplicacion en: http://localhost:5001" -ForegroundColor Cyan
}

function Start-Db {
    Write-Host "Arrancando aplicacion (modo BD)..." -ForegroundColor Cyan
    $env:STORAGE_BACKEND = "sqlite"
    docker-compose up -d --build
    Write-Host ""
    Write-Host "Aplicacion principal arrancada (db)" -ForegroundColor Green
    Write-Host "Accede a la aplicacion en: http://localhost:5001" -ForegroundColor Cyan
}

function Run-Tests {
    Write-Host "Ejecutando tests (Python 3)..." -ForegroundColor Cyan
    try {
        python3 -m pytest
    } catch {
        python -m pytest
    }
}


function Show-Logs {
    Write-Host "Logs de la aplicacion principal (Ctrl+C para salir)..." -ForegroundColor Cyan
    docker-compose logs -f web
}

function Show-Status {
    Write-Host "Estado de los contenedores:" -ForegroundColor Cyan
    docker-compose ps
}

function Stop-All {
    Write-Host "Deteniendo todos los servicios..." -ForegroundColor Cyan
    docker-compose down 2>$null
    Write-Host ""
    Write-Host "Todos los servicios detenidos" -ForegroundColor Green
}

function Clean-Temp {
    Write-Host "Limpiando archivos temporales..." -ForegroundColor Cyan
    Write-Host ""
    
    $scriptPath = Join-Path $PSScriptRoot "scripts\clean_temp.ps1"
    if (Test-Path $scriptPath) {
        & $scriptPath
    } else {
        Write-Host "Error: No se encontro el script: $scriptPath" -ForegroundColor Red
        exit 1
    }
}

function Clean-All {
    Write-Host "Ejecutando limpieza completa (DESTRUCTIVO)..." -ForegroundColor Yellow
    Write-Host ""
    
    $scriptPath = Join-Path $PSScriptRoot "scripts\clean_all.ps1"
    if (Test-Path $scriptPath) {
        & $scriptPath
    } else {
        Write-Host "Error: No se encontro el script: $scriptPath" -ForegroundColor Red
        exit 1
    }
}

function Fix-Containers {
    Write-Host "Solucionando problemas de contenedores (ContainerConfig error)..." -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Paso 1/3: Deteniendo y eliminando contenedores..." -ForegroundColor Yellow
    docker-compose down -v 2>$null
    Write-Host "   ✓ Contenedores eliminados" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Paso 2/3: Limpiando contenedores huérfanos..." -ForegroundColor Yellow
    docker container prune -f 2>$null
    Write-Host "   ✓ Limpieza completada" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Paso 3/3: Reconstruyendo imágenes..." -ForegroundColor Yellow
    docker-compose build --no-cache web
    Write-Host "   ✓ Imágenes reconstruidas" -ForegroundColor Green
    Write-Host ""
    Write-Host "✅ Problema solucionado. Ahora ejecuta: .\make.ps1 default" -ForegroundColor Green
}

function Purge-All {
    Write-Host "Purgando proyecto (detener servicios + limpieza completa)..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Paso 1/2: Deteniendo todos los servicios..." -ForegroundColor Cyan
    Stop-All
    Write-Host ""
    Write-Host "Paso 2/2: Limpiando todos los datos..." -ForegroundColor Cyan
    Write-Host ""
    Clean-All
    Write-Host ""
    Write-Host "Purge completado" -ForegroundColor Green
}

# Ejecutar el comando solicitado
switch ($Command.ToLower()) {
    "default" {
        Start-Default
    }
    "memory" {
        Start-Memory
    }
    "db" {
        Start-Db
    }
    "test" {
        Run-Tests
    }
    "logs" {
        Show-Logs
    }
    "ps" {
        Show-Status
    }
    "down" {
        Stop-All
    }
    "check" {
        Test-Requirements
    }
    "clean-temp" {
        Clean-Temp
    }
    "cleantemp" {
        Clean-Temp
    }
    "clean-all" {
        Clean-All
    }
    "fix-containers" {
        Fix-Containers
    }
    "cleanall" {
        Clean-All
    }
    "purge" {
        Purge-All
    }
    "help" {
        Show-Help
    }
    "" {
        Show-Help
    }
    default {
        Write-Host "Error: Comando desconocido: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
}

