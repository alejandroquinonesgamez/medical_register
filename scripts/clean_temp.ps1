# Script PowerShell para limpiar archivos temporales del proyecto
# Elimina archivos que estan en .gitignore y son generados automaticamente

Write-Host "Limpiando archivos temporales del proyecto..." -ForegroundColor Cyan
Write-Host ""

$count = 0

# Eliminar archivo de cobertura
if (Test-Path .coverage) {
    Remove-Item .coverage -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Eliminado: .coverage" -ForegroundColor Gray
    $count++
}

# Eliminar directorio instance/ (base de datos SQLite)
if (Test-Path instance) {
    Remove-Item instance -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Eliminado: instance/ (base de datos SQLite)" -ForegroundColor Gray
    $count++
}

# Eliminar directorios __pycache__
$pycacheDirs = Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | 
    Where-Object { $_.FullName -notlike "*\venv\*" -and $_.FullName -notlike "*\.git\*" }
if ($pycacheDirs) {
    $pycacheCount = ($pycacheDirs | Measure-Object).Count
    $pycacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Eliminados $pycacheCount directorios __pycache__/" -ForegroundColor Gray
    $count++
}

# Eliminar archivos .pyc y .pyo
$pycFiles = Get-ChildItem -Path . -Recurse -Include *.pyc,*.pyo -ErrorAction SilentlyContinue | 
    Where-Object { $_.FullName -notlike "*\venv\*" -and $_.FullName -notlike "*\.git\*" }
if ($pycFiles) {
    $pycCount = ($pycFiles | Measure-Object).Count
    $pycFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Eliminados $pycCount archivos .pyc/.pyo" -ForegroundColor Gray
    $count++
}

# Eliminar .pytest_cache
if (Test-Path .pytest_cache) {
    Remove-Item .pytest_cache -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Eliminado: .pytest_cache/" -ForegroundColor Gray
    $count++
}

# Eliminar htmlcov
if (Test-Path htmlcov) {
    Remove-Item htmlcov -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Eliminado: htmlcov/" -ForegroundColor Gray
    $count++
}

if ($count -eq 0) {
    Write-Host "  [INFO] No se encontraron archivos temporales para eliminar" -ForegroundColor Yellow
} else {
    Write-Host ""
    $message = "Limpieza completada: $count elementos eliminados"
    Write-Host $message -ForegroundColor Green
}

Write-Host ""

