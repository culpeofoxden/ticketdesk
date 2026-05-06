param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:5173",
    [string]$Email = "admin@example.com",
    [string]$Password = "password"
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message"
}

function Assert-Equal {
    param(
        [object]$Actual,
        [object]$Expected,
        [string]$Message
    )
    if ($Actual -ne $Expected) {
        throw "$Message. Expected '$Expected', got '$Actual'."
    }
}

$ApiUrl = $ApiUrl.TrimEnd("/")
$FrontendUrl = $FrontendUrl.TrimEnd("/")

Write-Step "Checking backend health at $ApiUrl/health"
$health = Invoke-RestMethod -Uri "$ApiUrl/health" -Method Get
Assert-Equal $health.status "ok" "Backend health check failed"

Write-Step "Checking frontend at $FrontendUrl"
$frontend = Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing
Assert-Equal $frontend.StatusCode 200 "Frontend check failed"

Write-Step "Logging in as $Email"
$loginBody = @{
    email = $Email
    password = $Password
} | ConvertTo-Json
$login = Invoke-RestMethod -Uri "$ApiUrl/auth/login" -Method Post -ContentType "application/json" -Body $loginBody
if (-not $login.access_token) {
    throw "Login did not return an access token."
}

$headers = @{
    Authorization = "Bearer $($login.access_token)"
}

Write-Step "Checking current user"
$me = Invoke-RestMethod -Uri "$ApiUrl/auth/me" -Method Get -Headers $headers
Assert-Equal $me.email $Email "Current user check failed"

Write-Step "Checking ticket list"
$tickets = Invoke-RestMethod -Uri "$ApiUrl/tickets" -Method Get -Headers $headers
if ($null -eq $tickets) {
    throw "Ticket list returned null."
}

Write-Host "Smoke checks passed."
