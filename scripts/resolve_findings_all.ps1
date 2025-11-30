# Script PowerShell para ejecutar el flujo completo de DefectDojo
# Equivalente a: make all

Write-Host "🚀 Iniciando flujo completo de DefectDojo..." -ForegroundColor Cyan
Write-Host ""

Write-Host "Paso 1/2: Arrancando DefectDojo (crea findings como activos)..." -ForegroundColor Yellow
$env:COMPOSE_DOCKER_CLI_BUILD = "0"
$env:DOCKER_BUILDKIT = "0"
docker-compose --profile defectdojo up -d

Write-Host ""
Write-Host "⏳ Esperando 60 segundos a que DefectDojo esté listo..." -ForegroundColor Yellow
Write-Host "   (Esto puede tardar, por favor espera...)" -ForegroundColor Gray
Start-Sleep -Seconds 60

Write-Host ""
Write-Host "Paso 2/2: Marcando findings como resueltos con fechas históricas..." -ForegroundColor Yellow

# Ejecutar el script bash
$bashPath = Get-Command bash -ErrorAction SilentlyContinue
if ($bashPath) {
    & bash scripts/mark_findings_resolved_with_dates.sh
} else {
    Write-Host "⚠️  bash no está disponible. Ejecutando comandos directamente..." -ForegroundColor Yellow
    
    # Verificar si DefectDojo está corriendo
    $defectdojoRunning = docker ps | Select-String "defectdojo"
    if (-not $defectdojoRunning) {
        Write-Host "⚠️  DefectDojo no está corriendo. Iniciando..." -ForegroundColor Yellow
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
        Write-Host "❌ Error: No se encontró el script: $scriptPath" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ Flujo completo finalizado" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Accede a DefectDojo en: http://localhost:8080" -ForegroundColor Cyan
Write-Host "   Engagement: http://localhost:8080/engagement/1/" -ForegroundColor Cyan
Write-Host "   Findings: http://localhost:8080/test/1/findings" -ForegroundColor Cyan

