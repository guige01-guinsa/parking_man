param(
    [string]$ListenHost = "0.0.0.0",
    [int]$Port = 8011,
    [string]$EnvFile = ".env",
    [switch]$Reload
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

$uvicornArgs = @(
    "-m", "uvicorn",
    "app.main:app",
    "--host", $ListenHost,
    "--port", "$Port",
    "--proxy-headers",
    "--forwarded-allow-ips", "*"
)

if ($Reload) {
    $uvicornArgs += @("--reload", "--reload-dir", "app")
}

& $python @uvicornArgs

