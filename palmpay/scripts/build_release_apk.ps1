# Build release APK for device testing
$ErrorActionPreference = "Stop"
$palmpayRoot = (Resolve-Path $PSScriptRoot\..).Path
$mobileDir = Join-Path $palmpayRoot "mobile"
$apkPath = Join-Path $mobileDir "build\app\outputs\flutter-apk\app-release.apk"

Push-Location $mobileDir
try {
    $apiHost = if ($env:API_HOST) { $env:API_HOST } else { "192.168.18.114" }
    $apiPort = if ($env:API_PORT) { $env:API_PORT } else { "8001" }
    $apiHttps = if ($env:API_HTTPS) { $env:API_HTTPS } else { "false" }
    Write-Host "Building release APK (API_HOST=$apiHost API_PORT=$apiPort API_HTTPS=$apiHttps)..."

    C:\Users\huzai\flutter\bin\flutter.bat build apk --release `
        --dart-define=API_HOST=$apiHost `
        --dart-define=API_PORT=$apiPort `
        --dart-define=API_HTTPS=$apiHttps

    Write-Host ""
    Write-Host "APK built:"
    Write-Host "  $apkPath"
    Write-Host ""
    Write-Host "Install (run from any folder):"
    Write-Host "  .\scripts\install_release_apk.ps1"
}
finally {
    Pop-Location
}
