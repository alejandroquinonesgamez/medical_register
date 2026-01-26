# Script de configuración inicial del proyecto para Windows/PowerShell
#
# Prepara el entorno para usar la aplicación médica. Realiza:
# 1. Crea el directorio de datos necesario
# 2. Configura el archivo .env para Docker Compose (soluciona problemas con caracteres especiales)
# 3. Verifica que Docker y Docker Compose estén instalados
# 4. Construye la imagen de la aplicación
#
# Este script se ejecuta automáticamente al clonar el repositorio
# y debe ejecutarse antes de usar make.ps1 o docker-compose.

$ErrorActionPreference = "Stop"

Write-Host "🚀 Configurando el proyecto Medical Register..." -ForegroundColor Cyan
Write-Host ""

# Obtener la ruta del script y el directorio raíz del proyecto
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Crear directorios de datos si no existen
Write-Host "📁 Creando directorios de datos..." -ForegroundColor Yellow
$dataDirs = @(
    "data"
)

foreach ($dir in $dataDirs) {
    $fullPath = Join-Path $projectRoot $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  ✓ Creado: $dir" -ForegroundColor Gray
    }
}

Write-Host "✅ Directorios creados" -ForegroundColor Green
Write-Host ""

# Configurar archivo .env para Docker Compose (soluciona problemas con caracteres especiales)
Write-Host "⚙️  Configurando Docker Compose..." -ForegroundColor Yellow
$envFile = Join-Path $projectRoot ".env"
$envExample = Join-Path $projectRoot "docker-compose.env.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "  ✓ Archivo .env creado desde docker-compose.env.example" -ForegroundColor Gray
    } else {
        # Crear .env básico
        @"
COMPOSE_PROJECT_NAME=medical_register
COMPOSE_DOCKER_CLI_BUILD=0
DOCKER_BUILDKIT=0
"@ | Out-File -FilePath $envFile -Encoding UTF8
        Write-Host "  ✓ Archivo .env creado con configuración básica" -ForegroundColor Gray
    }
} else {
    Write-Host "  ℹ️  Archivo .env ya existe" -ForegroundColor Gray
}

Write-Host "✅ Docker Compose configurado" -ForegroundColor Green
Write-Host ""

# Verificar Docker
Write-Host "🐳 Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "  ✓ Docker: $dockerVersion" -ForegroundColor Gray
    } else {
        Write-Host "  ❌ Docker no está instalado" -ForegroundColor Red
        Write-Host "     Por favor, instala Docker desde https://www.docker.com/get-started" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "  ❌ Docker no está disponible" -ForegroundColor Red
    Write-Host "     Por favor, instala Docker desde https://www.docker.com/get-started" -ForegroundColor Yellow
    exit 1
}

# Verificar Docker Compose
try {
    $composeVersion = docker-compose --version 2>$null
    if ($composeVersion) {
        Write-Host "  ✓ Docker Compose: $composeVersion" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠️  docker-compose no está disponible (se intentará con 'docker compose')" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  docker-compose no está disponible (se intentará con 'docker compose')" -ForegroundColor Yellow
}

# Verificar que Docker esté corriendo
try {
    $dockerRunning = docker ps 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Docker Daemon está corriendo" -ForegroundColor Gray
    } else {
        Write-Host "  ❌ Docker Daemon no está corriendo" -ForegroundColor Red
        Write-Host "     Por favor, inicia Docker Desktop" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "  ❌ No se pudo verificar el estado de Docker" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker y Docker Compose verificados" -ForegroundColor Green
Write-Host ""

# Construir imagen de la aplicación principal
Write-Host "🔨 Construyendo imagen de la aplicación..." -ForegroundColor Yellow
Set-Location $projectRoot

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

docker-compose build web

Write-Host ""
Write-Host "✅ Configuración completada" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos pasos:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Arrancar la aplicación principal:" -ForegroundColor White
Write-Host "   .\make.ps1 default" -ForegroundColor Gray
Write-Host "   # o: docker-compose up -d" -ForegroundColor DarkGray
Write-Host ""
Write-Host "2. Acceder a la aplicación:" -ForegroundColor White
Write-Host "   - Aplicación Flask: http://localhost:5001" -ForegroundColor Gray
Write-Host ""

