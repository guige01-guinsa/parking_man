param(
    [string]$ProjectRoot = "C:\parking_management"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$pidDir = Join-Path $ProjectRoot "deploy\pids"
$nginxRoot = Join-Path $ProjectRoot "tools\nginx"
$nginxExe = Join-Path $nginxRoot "nginx.exe"

if (Test-Path $nginxExe) {
    & $nginxExe -p $nginxRoot -c conf/nginx.conf -s stop | Out-Null
}

$nginxPidFile = Join-Path $pidDir "nginx.pid"
if (Test-Path $nginxPidFile) {
    $nginxPid = Get-Content $nginxPidFile | Select-Object -First 1
    if ($nginxPid) {
        Stop-Process -Id ([int]$nginxPid) -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $nginxPidFile -Force
}

$backendPidFile = Join-Path $pidDir "backend.pid"
if (Test-Path $backendPidFile) {
    $backendPid = Get-Content $backendPidFile | Select-Object -First 1
    if ($backendPid) {
        Stop-Process -Id ([int]$backendPid) -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $backendPidFile -Force
}

Write-Host "Stack stopped."
