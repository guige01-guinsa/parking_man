param(
    [string]$ProjectRoot = "C:\parking_management"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$pidDir = Join-Path $ProjectRoot "deploy\pids"
$nginxRoot = Join-Path $ProjectRoot "tools\nginx"
$nginxExe = Join-Path $nginxRoot "nginx.exe"
$backendPython = Join-Path $ProjectRoot "backend\.venv\Scripts\python.exe"

function Stop-ByPidFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return
    }
    $pidValue = Get-Content $Path | Select-Object -First 1
    if ($pidValue) {
        Stop-Process -Id ([int]$pidValue) -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $Path -Force -ErrorAction SilentlyContinue
}

if ((Test-Path $nginxExe) -and (Get-Process nginx -ErrorAction SilentlyContinue)) {
    & $nginxExe -p $nginxRoot -c conf/nginx.conf -s quit | Out-Null
    Start-Sleep -Milliseconds 500
    if (Get-Process nginx -ErrorAction SilentlyContinue) {
        & $nginxExe -p $nginxRoot -c conf/nginx.conf -s stop | Out-Null
    }
}

$nginxPidFile = Join-Path $pidDir "nginx.pid"
Stop-ByPidFile -Path $nginxPidFile

# Fallback: kill orphan nginx workers from this project.
Get-Process nginx -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -and $_.Path -ieq $nginxExe } |
    Stop-Process -Force -ErrorAction SilentlyContinue

$backendPidFile = Join-Path $pidDir "backend.pid"
Stop-ByPidFile -Path $backendPidFile

# Fallback: stop backend uvicorn process and wrapper shell if still running.
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ExecutablePath -and $_.ExecutablePath -ieq $backendPython -and $_.CommandLine -like "*uvicorn app.main:app*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Get-CimInstance Win32_Process -Filter "Name='pwsh.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*backend\\run.ps1*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Write-Host "Stack stopped."
