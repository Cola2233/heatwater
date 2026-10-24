param([string]$Python = "python", [string]$ConfigPath = "config/local.json")
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    & $Python -m scripts.run_pipeline --config $ConfigPath
    if ($LASTEXITCODE -ne 0) { throw "Pipeline failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}
