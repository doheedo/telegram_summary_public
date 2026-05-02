$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Project virtual environment not found at $python"
}

$botToken = Read-Host "Telegram bot token"

Set-Location $root
& $python -m app.bot_updates --bot-token $botToken

Write-Host ""
Write-Host "If the list is empty, send a message to your bot first and run this again."

