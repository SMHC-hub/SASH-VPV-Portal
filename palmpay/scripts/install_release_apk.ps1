# Install VeinPay release APK via adb
$ErrorActionPreference = "Stop"
$palmpayRoot = (Resolve-Path $PSScriptRoot\..).Path
$apkPath = Join-Path $palmpayRoot "mobile\build\app\outputs\flutter-apk\app-release.apk"
$adb = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"

if (-not (Test-Path $apkPath)) {
    Write-Error "APK not found. Build first:`n  cd `"$palmpayRoot`"`n  `$env:API_HOST=`"192.168.18.114`"`n  .\scripts\build_release_apk.ps1"
}
if (-not (Test-Path $adb)) {
    Write-Error "adb not found at $adb"
}

Write-Host "Installing $apkPath ..."
& $adb install -r $apkPath
