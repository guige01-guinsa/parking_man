param(
    [string]$BaseUrl = "http://127.0.0.1:8080/parking",
    [string]$ApiKey = "change-me"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-Equal {
    param(
        [Parameter(Mandatory = $true)]$Expected,
        [Parameter(Mandatory = $true)]$Actual,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if ($Expected -ne $Actual) {
        throw "$Message (expected=$Expected, actual=$Actual)"
    }
}

if ($BaseUrl.EndsWith("/")) {
    $BaseUrl = $BaseUrl.TrimEnd("/")
}

$health = Invoke-RestMethod -Method Get -Uri "$BaseUrl/health"
Assert-Equal -Expected $true -Actual $health.ok -Message "proxy health check failed"

$plateOk = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/plates/check?plate=12가3456" -Headers @{ "X-API-Key" = $ApiKey }
Assert-Equal -Expected "OK" -Actual $plateOk.verdict -Message "plate check failed through proxy"

$login = Invoke-WebRequest -Method Get -Uri "$BaseUrl/login" -UseBasicParsing
if ($login.Content -notmatch "action='/parking/login'") {
    throw "login form action is not prefix-aware: expected /parking/login"
}

Write-Host "Proxy verification passed for $BaseUrl"
