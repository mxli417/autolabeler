[CmdletBinding()]
param(
    [switch]$ConfigOnly,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$trivyImage = "aquasec/trivy:0.75.0"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$cacheMount = "autolabeler_trivy_cache:/root/.cache/"

function Invoke-Docker {
    param([Parameter(Mandatory)][string[]]$Arguments)

    & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "docker $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Scanning Dockerfiles and Compose configuration..."
Invoke-Docker -Arguments @(
    "run", "--rm",
    "--volume", "${repositoryRoot}:/workspace:ro",
    "--volume", $cacheMount,
    $trivyImage,
    "config", "--exit-code", "1", "--severity", "HIGH,CRITICAL",
    "--skip-dirs", "/workspace/.git", "--skip-dirs", "/workspace/.pre-commit-cache",
    "--skip-dirs", "/workspace/.venv", "--skip-dirs", "/workspace/workspace", "/workspace"
)

if ($ConfigOnly) {
    return
}

if (-not $SkipBuild) {
    Write-Host "Building application images..."
    Invoke-Docker -Arguments @("compose", "build", "--pull", "workbench", "ml-backend")
}

foreach ($image in @("autolabeler-workbench:local", "autolabeler-ml-backend:local")) {
    Write-Host "Scanning $image..."
    Invoke-Docker -Arguments @(
        "run", "--rm",
        "--volume", "/var/run/docker.sock:/var/run/docker.sock:ro",
        "--volume", $cacheMount,
        $trivyImage,
        "image", "--exit-code", "1", "--ignore-unfixed", "--no-progress", "--scanners", "vuln",
        "--severity", "HIGH,CRITICAL", $image
    )
}
