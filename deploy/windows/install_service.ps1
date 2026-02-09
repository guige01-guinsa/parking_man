param(
    [string]$ServiceName = "ParkingManagementApi",
    [string]$ProjectRoot = "C:\parking_management",
    [int]$Port = 8011
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script in an elevated PowerShell session."
    }
}

Assert-Admin

$runner = Join-Path $ProjectRoot "deploy\windows\service_runner.ps1"
if (-not (Test-Path $runner)) {
    throw "Service runner not found: $runner"
}

$pwsh = (Get-Command pwsh.exe -ErrorAction Stop).Source
$binPath = "`"$pwsh`" -NoProfile -ExecutionPolicy Bypass -File `"$runner`" -ProjectRoot `"$ProjectRoot`" -Port $Port"

$exists = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($exists) {
    Write-Host "Service already exists: $ServiceName"
} else {
    sc.exe create $ServiceName binPath= $binPath start= auto | Out-Null
    sc.exe description $ServiceName "Parking management FastAPI service" | Out-Null
    Write-Host "Created service: $ServiceName"
}

Start-Service -Name $ServiceName
Write-Host "Service started: $ServiceName"
