param(
    [string]$ParkingBaseUrl = "https://parking-man.onrender.com",
    [string]$PortalUrl = "https://www.ka-part.com/pwa/"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-RandomBase64 {
    param([int]$Bytes = 48)
    $buffer = New-Object byte[] $Bytes
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($buffer)
    return [Convert]::ToBase64String($buffer).TrimEnd("=")
}

$parkingApiKey = New-RandomBase64 -Bytes 32
$parkingSecret = New-RandomBase64 -Bytes 48
$parkingContextSecret = New-RandomBase64 -Bytes 48

Write-Host "=== parking_man Render env ==="
Write-Host ("PARKING_API_KEY={0}" -f $parkingApiKey)
Write-Host ("PARKING_SECRET_KEY={0}" -f $parkingSecret)
Write-Host ("PARKING_CONTEXT_SECRET={0}" -f $parkingContextSecret)
Write-Host "PARKING_LOCAL_LOGIN_ENABLED=0"
Write-Host "PARKING_CONTEXT_MAX_AGE=300"
Write-Host "PARKING_DEFAULT_SITE_CODE=COMMON"
Write-Host ("PARKING_PORTAL_URL={0}" -f $PortalUrl)
Write-Host "PARKING_ROOT_PATH="
Write-Host "PARKING_SESSION_MAX_AGE=43200"

Write-Host ""
Write-Host "=== ka-part Render env (gateway mode) ==="
Write-Host "ENABLE_PARKING_EMBED=0"
Write-Host ("PARKING_BASE_URL={0}" -f $ParkingBaseUrl)
Write-Host "PARKING_SSO_PATH=/sso"
Write-Host ("PARKING_CONTEXT_SECRET={0}" -f $parkingContextSecret)
Write-Host "PARKING_CONTEXT_MAX_AGE=300"
