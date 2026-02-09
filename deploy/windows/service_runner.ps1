param(
    [string]$ProjectRoot = "C:\parking_management",
    [int]$Port = 8011
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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
        $kv = $line.Split("=", 2)
        if ($kv.Count -eq 2) {
            [Environment]::SetEnvironmentVariable($kv[0].Trim(), $kv[1].Trim(), "Process")
        }
    }
}

$backendPath = Join-Path $ProjectRoot "backend"
$envFile = Join-Path $backendPath ".env.production"
$python = Join-Path $backendPath ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Python venv missing: $python"
}

Set-EnvFromFile -Path $envFile

if (-not $env:PARKING_DB_PATH) {
    $env:PARKING_DB_PATH = Join-Path $backendPath "app\data\parking.db"
}
if (-not $env:PARKING_UPLOAD_DIR) {
    $env:PARKING_UPLOAD_DIR = Join-Path $backendPath "app\uploads"
}

Set-Location $backendPath
& $python -m uvicorn app.main:app --host 127.0.0.1 --port $Port --proxy-headers --forwarded-allow-ips "127.0.0.1"
