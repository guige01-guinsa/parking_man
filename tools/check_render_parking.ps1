param(
    [switch]$Deploy,
    [string]$ServiceName = "parking-man",
    [string]$RepoName = "parking_man",
    [string]$ExpectedCommit = "",
    [int]$TimeoutSec = 600
)

$ErrorActionPreference = "Stop"

if (-not $env:RENDER_API_KEY) {
    throw "RENDER_API_KEY is required."
}

if (-not $ExpectedCommit) {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        $ExpectedCommit = (git rev-parse HEAD).Trim()
    }
}

$headers = @{ Authorization = "Bearer $env:RENDER_API_KEY" }

function Invoke-RenderApi {
    param(
        [string]$Method,
        [string]$Uri,
        [object]$Body = $null
    )
    $args = @{
        Method = $Method
        Uri = $Uri
        Headers = $headers
    }
    if ($null -ne $Body) {
        $args["ContentType"] = "application/json"
        $args["Body"] = ($Body | ConvertTo-Json -Depth 8)
    }
    Invoke-RestMethod @args
}

function Find-ParkingService {
    $items = Invoke-RenderApi -Method Get -Uri "https://api.render.com/v1/services?limit=100"
    $matches = @($items | Where-Object {
        $_.service.name -eq $ServiceName -and $_.service.repo -like "*/$RepoName"
    })
    if ($matches.Count -ne 1) {
        $names = ($items | ForEach-Object { "$($_.service.name) <$($_.service.repo)> [$($_.service.id)]" }) -join "`n"
        throw "Expected exactly one Render service for name '$ServiceName' and repo '$RepoName'.`n$names"
    }
    $matches[0].service
}

function Wait-ForDeploy {
    param(
        [string]$ServiceId,
        [string]$DeployId
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $deploy = Invoke-RenderApi -Method Get -Uri "https://api.render.com/v1/services/$ServiceId/deploys/$DeployId"
        Write-Host ("deploy={0} status={1} commit={2}" -f $deploy.id, $deploy.status, $deploy.commit.id.Substring(0, 7))
        if ($deploy.status -eq "live") {
            return $deploy
        }
        if ($deploy.status -match "failed|canceled|deactivated") {
            throw "Render deploy failed: $($deploy.status)"
        }
        Start-Sleep -Seconds 15
    }
    throw "Render deploy did not become live before timeout."
}

function Test-PublicEndpoint {
    param(
        [string]$BaseUrl,
        [string]$Path,
        [string]$Needle = ""
    )
    $deadline = (Get-Date).AddSeconds([Math]::Min($TimeoutSec, 180))
    $lastError = $null
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl$Path" -TimeoutSec 15
            $headersText = @{
                "x-content-type-options" = $response.Headers["x-content-type-options"]
                "x-frame-options" = $response.Headers["x-frame-options"]
                "referrer-policy" = $response.Headers["referrer-policy"]
            }
            if ($response.StatusCode -ne 200) {
                throw "$Path returned non-200 status: $($response.StatusCode)"
            }
            if ($Needle -and $response.Content -notlike "*$Needle*") {
                throw "$Path response did not contain required marker: $Needle"
            }
            if ($headersText["x-content-type-options"] -ne "nosniff") {
                throw "$Path missing security header: x-content-type-options"
            }
            if ($headersText["x-frame-options"] -ne "DENY") {
                throw "$Path missing security header: x-frame-options"
            }
            Write-Host ("ok {0} {1}" -f $Path, $response.StatusCode)
            return
        } catch {
            $lastError = $_.Exception.Message
            Write-Host ("wait {0}: {1}" -f $Path, $lastError)
            Start-Sleep -Seconds 10
        }
    }
    throw "$Path public check failed: $lastError"
}

$service = Find-ParkingService
Write-Host ("service={0} id={1} repo={2} url={3}" -f $service.name, $service.id, $service.repo, $service.serviceDetails.url)

if ($env:RENDER_SERVICE_ID -and $env:RENDER_SERVICE_ID -ne $service.id) {
    Write-Warning ("Current RENDER_SERVICE_ID={0}, but parking-man service id is {1}. Ignoring RENDER_SERVICE_ID." -f $env:RENDER_SERVICE_ID, $service.id)
}

if ($service.serviceDetails.healthCheckPath -ne "/health") {
    throw "Render health check path is not /health: $($service.serviceDetails.healthCheckPath)"
}
if ($service.serviceDetails.env -ne "docker") {
    throw "Render runtime is not docker: $($service.serviceDetails.env)"
}
if ($service.branch -ne "main") {
    throw "Render branch is not main: $($service.branch)"
}

if ($Deploy) {
    $targetDeploy = Invoke-RenderApi -Method Post -Uri "https://api.render.com/v1/services/$($service.id)/deploys" -Body @{ clearCache = "do_not_clear" }
} else {
    $deploys = Invoke-RenderApi -Method Get -Uri "https://api.render.com/v1/services/$($service.id)/deploys?limit=1"
    $targetDeploy = $deploys[0].deploy
}

if ($ExpectedCommit -and $targetDeploy.commit.id -ne $ExpectedCommit) {
    throw "Render deploy commit does not match expected commit. deploy=$($targetDeploy.commit.id), expected=$ExpectedCommit"
}

$liveDeploy = Wait-ForDeploy -ServiceId $service.id -DeployId $targetDeploy.id
if ($ExpectedCommit -and $liveDeploy.commit.id -ne $ExpectedCommit) {
    throw "Live deploy commit does not match expected commit. live=$($liveDeploy.commit.id), expected=$ExpectedCommit"
}

$baseUrl = $service.serviceDetails.url.TrimEnd("/")
Test-PublicEndpoint -BaseUrl $baseUrl -Path "/health" -Needle '"ok":true'
Test-PublicEndpoint -BaseUrl $baseUrl -Path "/login" -Needle "auth-start-guide"
Test-PublicEndpoint -BaseUrl $baseUrl -Path "/privacy" -Needle "privacy-card"

Write-Host "Render deploy check completed"
