# Run PalmPay backend with Gunicorn + Uvicorn workers (Day 8 benchmark)
# Usage: .\scripts\run_gunicorn.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Get-Command gunicorn -ErrorAction SilentlyContinue)) {
    Write-Host "Installing gunicorn..."
    pip install gunicorn
}

$env:PYTHONPATH = (Get-Location).Path
gunicorn backend.main:app `
    --worker-class uvicorn.workers.UvicornWorker `
    --workers 4 `
    --bind 0.0.0.0:8001 `
    --timeout 120
