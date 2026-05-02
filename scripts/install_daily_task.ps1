$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
$runScript = Join-Path $root "scripts\run_daily.ps1"

if (-not (Test-Path $runScript)) {
    throw "Run script not found at $runScript"
}

$taskName = Read-Host "Task name [tel_suma_daily]"
if ([string]::IsNullOrWhiteSpace($taskName)) {
    $taskName = "tel_suma_daily"
}

$startTime = Read-Host "Daily start time [11:30]"
if ([string]::IsNullOrWhiteSpace($startTime)) {
    $startTime = "11:30"
}

$taskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$runScript`""

schtasks /Create /F /SC DAILY /TN $taskName /TR $taskCommand /ST $startTime | Out-Host

Write-Host ""
Write-Host "Created scheduled task '$taskName' at $startTime"
