# Script PowerShell equivalente a: make update
# Levanta aplicacion y DefectDojo, y actualiza flujo de findings

Write-Host "Actualizando aplicacion y flujo de findings..." -ForegroundColor Cyan
Write-Host ""

# Configurar variables de entorno
$env:COMPOSE_DOCKER_CLI_BUILD = "0"
$env:DOCKER_BUILDKIT = "0"

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

# Verificar si bash esta disponible
$bashPath = Get-Command bash -ErrorAction SilentlyContinue
if ($bashPath) {
    & bash scripts/mark_findings_resolved_with_dates.sh
} else {
    Write-Host "   bash no esta disponible. Ejecutando comandos directamente..." -ForegroundColor Yellow
    
    # Verificar si DefectDojo esta corriendo
    $defectdojoRunning = docker ps | Select-String "defectdojo"
    if (-not $defectdojoRunning) {
        Write-Host "   DefectDojo no esta corriendo. Reiniciando..." -ForegroundColor Yellow
        docker-compose --profile defectdojo up -d defectdojo
        Start-Sleep -Seconds 10
    }
    
    # Copiar y ejecutar el script
    $scriptPath = Join-Path $PSScriptRoot "resolve_findings_with_dates.py"
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
