$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Project virtual environment not found at $python"
}

$tgApiId = Read-Host "Telegram API ID"
$tgApiHash = Read-Host "Telegram API Hash"
$tgPhone = Read-Host "Telegram phone number (example: +821012345678)"
$sessionName = Read-Host "Telethon session name [tg_session]"
if ([string]::IsNullOrWhiteSpace($sessionName)) {
    $sessionName = "tg_session"
}

$botToken = Read-Host "Telegram bot token"
$botChatId = Read-Host "Telegram bot personal chat ID"
$nvidiaApiKey = Read-Host "NVIDIA API key (optional, preferred provider)"
$nvidiaModelName = Read-Host "NVIDIA model name [deepseek-ai/deepseek-v4-pro]"
if ([string]::IsNullOrWhiteSpace($nvidiaModelName)) {
    $nvidiaModelName = "deepseek-ai/deepseek-v4-pro"
}
$groqApiKey = Read-Host "Groq API key"
$timezoneName = Read-Host "Timezone [Asia/Seoul]"
if ([string]::IsNullOrWhiteSpace($timezoneName)) {
    $timezoneName = "Asia/Seoul"
}

$summaryMaxChars = Read-Host "Summary max chars [1000]"
if ([string]::IsNullOrWhiteSpace($summaryMaxChars)) {
    $summaryMaxChars = "1000"
}

$lookbackHours = Read-Host "Lookback hours [24]"
if ([string]::IsNullOrWhiteSpace($lookbackHours)) {
    $lookbackHours = "24"
}

$allowedChatsInput = Read-Host "Allowed chats (comma-separated titles or ids)"
$allowedChats = @()
if (-not [string]::IsNullOrWhiteSpace($allowedChatsInput)) {
    $allowedChats = $allowedChatsInput.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}

$argsList = @(
    "-m", "app.setup_files",
    "--env-path", ".env",
    "--chats-path", "config/chats.yaml",
    "--telegram-api-id", $tgApiId,
    "--telegram-api-hash", $tgApiHash,
    "--telegram-phone", $tgPhone,
    "--telegram-session-name", $sessionName,
    "--bot-token", $botToken,
    "--bot-chat-id", $botChatId,
    "--nvidia-api-key", $nvidiaApiKey,
    "--nvidia-model-name", $nvidiaModelName,
    "--groq-api-key", $groqApiKey,
    "--timezone-name", $timezoneName,
    "--summary-max-chars", $summaryMaxChars,
    "--lookback-hours", $lookbackHours
)

foreach ($chat in $allowedChats) {
    $argsList += @("--allowed-chat", $chat)
}

Set-Location $root
& $python @argsList

Write-Host ""
Write-Host "Wrote .env and config/chats.yaml"
Write-Host "Next: .\.venv\Scripts\python.exe -m app.main --bootstrap-login"
