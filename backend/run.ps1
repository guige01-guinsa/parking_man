param(
    [string]$ListenHost = "0.0.0.0",
    [int]$Port = 8011,
    [string]$EnvFile = ".env",
    [switch]$Reload,
    [switch]$ForceRestart
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Set-EnvFromFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }

        $parts = $line.Split("=", 2)
        if ($parts.Count -eq 2) {
            [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
        }
    }
}

function Get-ListeningProcess {
    param([int]$LocalPort)

    $conn = Get-NetTCPConnection -LocalPort $LocalPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $conn) {
        return $null
    }

    $proc = Get-CimInstance Win32_Process -Filter ("ProcessId = {0}" -f $conn.OwningProcess) -ErrorAction SilentlyContinue
    if (-not $proc) {
        return [pscustomobject]@{
            ProcessId = $conn.OwningProcess
            CommandLine = $null
        }
    }

    return [pscustomobject]@{
        ProcessId = $proc.ProcessId
        CommandLine = $proc.CommandLine
    }
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $python -m pip install --disable-pip-version-check -r requirements.txt

Set-EnvFromFile -Path ".env.example"
Set-EnvFromFile -Path $EnvFile

if (-not $env:PARKING_DB_PATH) {
    $env:PARKING_DB_PATH = ".\app\data\parking.db"
}
if (-not $env:PARKING_UPLOAD_DIR) {
    $env:PARKING_UPLOAD_DIR = ".\app\uploads"
}
if (-not $env:PARKING_IMPORT_DIR) {
    $env:PARKING_IMPORT_DIR = ".\imports"
}
if (-not $env:PARKING_SECRET_KEY) {
    $env:PARKING_SECRET_KEY = "dev-secret-change-me"
}
if (-not $env:PARKING_OCR_PROVIDER) {
    $env:PARKING_OCR_PROVIDER = "tesseract"
}

$listener = Get-ListeningProcess -LocalPort $Port
if ($listener) {
    if ($ForceRestart) {
        Stop-Process -Id $listener.ProcessId -Force
        Start-Sleep -Seconds 1
    } else {
        try {
            $health = Invoke-RestMethod -Uri ("http://127.0.0.1:{0}/health" -f $Port) -TimeoutSec 2
            if ($health.ok -eq $true) {
                Write-Host ("Parking app is already running on port {0} (PID {1})." -f $Port, $listener.ProcessId)
                Write-Host ("If you want to replace it, run: pwsh -File backend\\run.ps1 -Port {0} -ForceRestart" -f $Port)
                exit 0
            }
        } catch {
        }

        $cmd = $listener.CommandLine
        if (-not $cmd) {
            $cmd = "unknown"
        }
        throw ("Port {0} is already in use by PID {1}. CommandLine: {2}" -f $Port, $listener.ProcessId, $cmd)
    }
}

$uvicornArgs = @(
    "-m", "uvicorn",
    "app.main:app",
    "--host", $ListenHost,
    "--port", "$Port",
    "--proxy-headers",
    "--forwarded-allow-ips=*"
)

if ($Reload) {
    $uvicornArgs += @("--reload", "--reload-dir", "app")
}

& $python @uvicornArgs

