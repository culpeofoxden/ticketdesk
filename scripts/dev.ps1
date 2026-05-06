param(
    [ValidateSet("up", "down", "restart", "ps", "logs", "backend-logs", "frontend-logs", "db-logs", "build-frontend", "smoke")]
    [string]$Command = "ps"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Push-Location $Root
try {
    switch ($Command) {
        "up" { docker compose up --build -d }
        "down" { docker compose down }
        "restart" {
            docker compose down
            docker compose up --build -d
        }
        "ps" { docker compose ps }
        "logs" { docker compose logs --tail=120 }
        "backend-logs" { docker compose logs backend --tail=120 }
        "frontend-logs" { docker compose logs frontend --tail=120 }
        "db-logs" { docker compose logs db --tail=120 }
        "build-frontend" { docker compose exec -T frontend npm run build }
        "smoke" { & "$PSScriptRoot\smoke.ps1" }
    }
}
finally {
    Pop-Location
}
