# PalmPay Day 9 — run backend + Flutter tests
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "Installing test dependencies..."
pip install -q pytest httpx

Write-Host "`n=== Backend pytest ==="
$env:PYTHONPATH = (Get-Location).Path
$env:RECOGNITION_LOGS_ENABLED = "false"
python -m pytest tests -v --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== Flutter tests ==="
Push-Location mobile
C:\Users\huzai\flutter\bin\flutter.bat test
$flutterExit = $LASTEXITCODE
Pop-Location
exit $flutterExit
