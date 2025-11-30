# Script PowerShell equivalente al Makefile
# Uso: .\make.ps1 [comando]
# Ejemplo: .\make.ps1 update

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Variables de entorno para Docker Compose
$env:COMPOSE_DOCKER_CLI_BUILD = "0"
$env:DOCKER_BUILDKIT = "0"

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
    Write-Host "  initDefectDojo   " -NoNewline -ForegroundColor Yellow
    Write-Host "Iniciar DefectDojo vacio (sin findings)"
    Write-Host "  update           " -NoNewline -ForegroundColor Yellow
    Write-Host "Levantar aplicacion y DefectDojo, y actualizar flujo de findings"
    Write-Host "  logs             " -NoNewline -ForegroundColor Yellow
    Write-Host "Ver logs de la aplicacion principal"
    Write-Host "  logs-defectdojo  " -NoNewline -ForegroundColor Yellow
    Write-Host "Ver logs de DefectDojo"
    Write-Host "  ps               " -NoNewline -ForegroundColor Yellow
    Write-Host "Ver estado de todos los contenedores"
    Write-Host "  down             " -NoNewline -ForegroundColor Yellow
    Write-Host "Detener todos los servicios"
    Write-Host "  pdf_ASVS         " -NoNewline -ForegroundColor Yellow
    Write-Host "Generar PDF del informe de seguridad ASVS con fecha"
    Write-Host "  check            " -NoNewline -ForegroundColor Yellow
    Write-Host "Verificar requisitos previos (Docker, Docker Compose)"
    Write-Host "  help             " -NoNewline -ForegroundColor Yellow
    Write-Host "Mostrar esta ayuda"
    Write-Host ""
    Write-Host "Ejemplos:" -ForegroundColor Cyan
    Write-Host "  .\make.ps1                # Muestra la ayuda"
    Write-Host "  .\make.ps1 check          # Verifica requisitos"
    Write-Host "  .\make.ps1 default        # Arranca la aplicacion principal"
    Write-Host "  .\make.ps1 update         # Despliegue completo y actualizacion"
    Write-Host ""
}

function Start-Default {
    Write-Host "Arrancando aplicacion principal..." -ForegroundColor Cyan
    docker-compose up -d
    Write-Host ""
    Write-Host "Aplicacion principal arrancada" -ForegroundColor Green
    Write-Host "Accede a la aplicacion en: http://localhost:5001" -ForegroundColor Cyan
}

function Start-InitDefectDojo {
    Write-Host "Iniciando DefectDojo vacio (sin findings)..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Nota: Se iniciara DefectDojo pero sin crear findings automaticamente" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Paso 1/2: Arrancando servicios de DefectDojo..." -ForegroundColor Yellow
    $env:DD_SKIP_FINDINGS = "True"
    docker-compose --profile defectdojo up -d
    Write-Host ""
    Write-Host "Esperando 60 segundos a que DefectDojo este listo..." -ForegroundColor Yellow
    Write-Host "   (Esto puede tardar en la primera ejecucion...)" -ForegroundColor Gray
    Start-Sleep -Seconds 60
    Write-Host ""
    Write-Host "Paso 2/2: Inicializando DefectDojo sin crear findings..." -ForegroundColor Yellow
    Write-Host "   (Solo migraciones, admin user y archivos estaticos)" -ForegroundColor Gray
    
    $scriptPath = Join-Path $PSScriptRoot "scripts\init_defectdojo_empty.py"
    if (Test-Path $scriptPath) {
        docker cp $scriptPath defectdojo:/tmp/init_defectdojo_empty.py 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   Reintentando..." -ForegroundColor Gray
            Start-Sleep -Seconds 5
            docker cp $scriptPath defectdojo:/tmp/init_defectdojo_empty.py
        }
        docker-compose --profile defectdojo exec -T defectdojo python3 /tmp/init_defectdojo_empty.py 2>&1
    } else {
        Write-Host "   DefectDojo puede estar ya inicializado (esto es normal)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "DefectDojo vacio iniciado (sin findings creados)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Accede a DefectDojo en: http://localhost:8080" -ForegroundColor Cyan
    Write-Host "   Usuario: admin | Contrasena: admin" -ForegroundColor White
}

function Start-Update {
    Write-Host "Actualizando aplicacion y flujo de findings..." -ForegroundColor Cyan
    Write-Host ""
    
    # Paso 1: Verificar aplicacion principal
    Write-Host "Paso 1/3: Verificando aplicacion principal..." -ForegroundColor Yellow
    $webStatus = docker-compose ps web 2>$null | Select-String "Up"
    if (-not $webStatus) {
        Write-Host "   Arrancando aplicacion principal..." -ForegroundColor Gray
        docker-compose up -d web
        Start-Sleep -Seconds 5
    }
    Write-Host "   Aplicacion principal lista" -ForegroundColor Green
    Write-Host ""
    
    # Paso 2: Verificar DefectDojo
    Write-Host "Paso 2/3: Verificando DefectDojo..." -ForegroundColor Yellow
    $defectdojoStatus = docker-compose --profile defectdojo ps defectdojo 2>$null | Select-String "Up"
    if (-not $defectdojoStatus) {
        Write-Host "   Arrancando DefectDojo..." -ForegroundColor Gray
        docker-compose --profile defectdojo up -d
        Write-Host "   Esperando 60 segundos..." -ForegroundColor Gray
        Start-Sleep -Seconds 60
    }
    Write-Host "   DefectDojo listo" -ForegroundColor Green
    Write-Host ""
    
    # Paso 3: Actualizar flujo de findings
    Write-Host "Paso 3/3: Actualizando flujo de findings con fechas historicas..." -ForegroundColor Yellow
    
    $bashPath = Get-Command bash -ErrorAction SilentlyContinue
    if ($bashPath) {
        & bash scripts/mark_findings_resolved_with_dates.sh
    } else {
        Write-Host "   bash no esta disponible. Ejecutando comandos directamente..." -ForegroundColor Yellow
        
        $defectdojoRunning = docker ps | Select-String "defectdojo"
        if (-not $defectdojoRunning) {
            Write-Host "   DefectDojo no esta corriendo. Reiniciando..." -ForegroundColor Yellow
            docker-compose --profile defectdojo up -d defectdojo
            Start-Sleep -Seconds 10
        }
        
        $scriptPath = Join-Path $PSScriptRoot "scripts\resolve_findings_with_dates.py"
        if (Test-Path $scriptPath) {
            Write-Host "   Copiando script al contenedor..." -ForegroundColor Gray
            docker cp $scriptPath defectdojo:/tmp/resolve_findings_with_dates.py
            
            Write-Host "   Ejecutando script en DefectDojo..." -ForegroundColor Gray
            docker-compose --profile defectdojo exec -T defectdojo python3 /tmp/resolve_findings_with_dates.py
        } else {
            Write-Host "   Error: No se encontro el script: $scriptPath" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host ""
    Write-Host "Actualizacion completada" -ForegroundColor Green
    Write-Host ""
    Write-Host "Accede a:" -ForegroundColor Cyan
    Write-Host "   Aplicacion: http://localhost:5001" -ForegroundColor White
    Write-Host "   DefectDojo: http://localhost:8080/engagement/1/" -ForegroundColor White
}

function Show-Logs {
    Write-Host "Logs de la aplicacion principal (Ctrl+C para salir)..." -ForegroundColor Cyan
    docker-compose logs -f web
}

function Show-LogsDefectDojo {
    Write-Host "Logs de DefectDojo (Ctrl+C para salir)..." -ForegroundColor Cyan
    docker-compose --profile defectdojo logs -f defectdojo
}

function Show-Status {
    Write-Host "Estado de los contenedores:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "=== Aplicacion Principal ===" -ForegroundColor Yellow
    docker-compose ps
    Write-Host ""
    Write-Host "=== DefectDojo ===" -ForegroundColor Yellow
    docker-compose --profile defectdojo ps
}

function Stop-All {
    Write-Host "Deteniendo todos los servicios..." -ForegroundColor Cyan
    docker-compose down 2>$null
    docker-compose --profile defectdojo down 2>$null
    Write-Host ""
    Write-Host "Todos los servicios detenidos" -ForegroundColor Green
}

function Generate-PDFReport {
    Write-Host "Generando PDF del informe de seguridad ASVS..." -ForegroundColor Cyan
    Write-Host ""
    
    # Obtener el directorio del proyecto (donde está make.ps1)
    $projectRoot = Split-Path -Parent $MyInvocation.PSCommandPath
    if (-not $projectRoot) {
        $projectRoot = $PSScriptRoot
    }
    
    $scriptPath = Join-Path $projectRoot "scripts\generate_pdf_report.py"
    if (Test-Path $scriptPath) {
        python $scriptPath
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "PDF generado exitosamente en: docs/informes/" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "Error al generar el PDF" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Error: No se encontro el script: $scriptPath" -ForegroundColor Red
        exit 1
    }
}

# Ejecutar el comando solicitado
switch ($Command.ToLower()) {
    "default" {
        Start-Default
    }
    "initdefectdojo" {
        Start-InitDefectDojo
    }
    "update" {
        Start-Update
    }
    "logs" {
        Show-Logs
    }
    "logs-defectdojo" {
        Show-LogsDefectDojo
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
    "pdf_asvs" {
        Generate-PDFReport
    }
    "pdf_ASVS" {
        Generate-PDFReport
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

