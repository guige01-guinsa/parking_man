param(
    [string]$SiteName = "Default Web Site",
    [string]$ProjectRoot = "C:\parking_management"
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

Import-Module WebAdministration -ErrorAction Stop

$sitePath = "IIS:\Sites\$SiteName"
if (-not (Test-Path $sitePath)) {
    throw "IIS site '$SiteName' not found."
}

$webConfigSource = Join-Path $ProjectRoot "deploy\iis\web.config"
if (-not (Test-Path $webConfigSource)) {
    throw "web.config not found at $webConfigSource"
}

$physicalPath = (Get-ItemProperty $sitePath).physicalPath
if (-not (Test-Path $physicalPath)) {
    throw "IIS site physical path not found: $physicalPath"
}

$webConfigTarget = Join-Path $physicalPath "web.config"
Copy-Item -Path $webConfigSource -Destination $webConfigTarget -Force

Write-Host "Applied reverse proxy web.config to $webConfigTarget"
Write-Host "Ensure IIS URL Rewrite + ARR are installed and Proxy is enabled in ARR."
