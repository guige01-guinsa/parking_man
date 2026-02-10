param(
    [string]$ProjectRoot = "C:\parking_management",
    [string]$NginxVersion = "1.28.0"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Wait-Http {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 30
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $resp = Invoke-WebRequest -UseBasicParsing -Method Get -Uri $Url -TimeoutSec 3
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
                return
            }
        } catch {
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "Timeout waiting for $Url"
}

function New-RandomBase64 {
    param([int]$Bytes = 32)
    $buffer = New-Object byte[] $Bytes
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($buffer)
    return [Convert]::ToBase64String($buffer)
}

$pidDir = Join-Path $ProjectRoot "deploy\pids"
New-Item -ItemType Directory -Force -Path $pidDir | Out-Null

$backendDir = Join-Path $ProjectRoot "backend"
$backendLogDir = Join-Path $backendDir "logs"
New-Item -ItemType Directory -Force -Path $backendLogDir | Out-Null
$envFilePath = Join-Path $backendDir ".env.production"
if (-not (Test-Path $envFilePath)) {
    @(
        "PARKING_SECRET_KEY=$(New-RandomBase64 -Bytes 48)"
        "PARKING_API_KEY=$(New-RandomBase64 -Bytes 32)"
        "PARKING_SESSION_MAX_AGE=43200"
        "PARKING_DB_PATH=./app/data/parking.db"
        "PARKING_UPLOAD_DIR=./app/uploads"
        "PARKING_ROOT_PATH=/parking"
        "PARKING_DEFAULT_SITE_CODE=COMMON"
        "PARKING_CONTEXT_SECRET=$(New-RandomBase64 -Bytes 48)"
        "PARKING_CONTEXT_MAX_AGE=300"
        "PARKING_LOCAL_LOGIN_ENABLED=0"
        "PARKING_PORTAL_URL=https://www.ka-part.com/pwa/"
        "PARKING_PORTAL_LOGIN_URL=https://www.ka-part.com/pwa/login.html?next=%2Fparking%2Fadmin2"
    ) | Set-Content -Path $envFilePath -Encoding UTF8
}
$runScript = Join-Path $backendDir "run.ps1"
$pwsh = (Get-Command pwsh.exe -ErrorAction Stop).Source
$backendStdOut = Join-Path $backendLogDir "backend.stdout.log"
$backendStdErr = Join-Path $backendLogDir "backend.stderr.log"

$backendProc = Start-Process -FilePath $pwsh `
    -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $runScript, "-ListenHost", "127.0.0.1", "-Port", "8011", "-EnvFile", ".env.production" `
    -WorkingDirectory $backendDir `
    -RedirectStandardOutput $backendStdOut `
    -RedirectStandardError $backendStdErr `
    -PassThru

Set-Content -Path (Join-Path $pidDir "backend.pid") -Value $backendProc.Id
try {
    Wait-Http -Url "http://127.0.0.1:8011/health" -TimeoutSeconds 60
} catch {
    if (Test-Path $backendStdErr) {
        Get-Content $backendStdErr -Tail 30 | ForEach-Object { Write-Host $_ }
    }
    throw
}

$toolsDir = Join-Path $ProjectRoot "tools"
$nginxRoot = Join-Path $toolsDir "nginx"
New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null

if (-not (Test-Path $nginxRoot)) {
    $zipName = "nginx-$NginxVersion.zip"
    $zipPath = Join-Path $toolsDir $zipName
    $downloadUrl = "https://nginx.org/download/$zipName"
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $toolsDir -Force
    Move-Item -Path (Join-Path $toolsDir "nginx-$NginxVersion") -Destination $nginxRoot -Force
}

$nginxConfSource = Join-Path $ProjectRoot "deploy\nginx\nginx.local.conf"
$nginxConfDest = Join-Path $nginxRoot "conf\nginx.conf"
Copy-Item -Path $nginxConfSource -Destination $nginxConfDest -Force

$nginxExe = Join-Path $nginxRoot "nginx.exe"
$nginxProc = Start-Process -FilePath $nginxExe -ArgumentList "-p", $nginxRoot, "-c", "conf/nginx.conf" -WorkingDirectory $nginxRoot -PassThru
Set-Content -Path (Join-Path $pidDir "nginx.pid") -Value $nginxProc.Id

Wait-Http -Url "http://127.0.0.1:8080/parking/health" -TimeoutSeconds 30

Write-Host "Stack started."
Write-Host "Backend: http://127.0.0.1:8011"
Write-Host "Nginx proxy: http://127.0.0.1:8080/parking"
