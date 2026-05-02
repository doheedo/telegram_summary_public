from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import dotenv_values


@dataclass(slots=True)
class AppConfig:
    telegram_api_id: int
    telegram_api_hash: str
    telegram_phone: str
    telegram_session_name: str
    bot_token: str
    bot_chat_id: str
    nvidia_api_key: str | None
    nvidia_model_name: str
    groq_api_key: str
    groq_model_name: str
    timezone_name: str
    summary_max_chars: int
    lookback_hours: int
    allowed_chats: list[str]
    nvidia_requests_per_minute: float = 40.0
    groq_requests_per_minute: float = 30.0
    groq_tokens_per_minute: int = 10_000


def load_config(env_file: Path, chats_file: Path) -> AppConfig:
    env = dotenv_values(env_file)
    required = [
        "TG_API_ID",
        "TG_API_HASH",
        "TG_PHONE",
        "TG_SESSION_NAME",
        "BOT_TOKEN",
        "BOT_CHAT_ID",
        "GROQ_API_KEY",
    ]
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise ValueError(f"Missing required settings: {', '.join(missing)}")

    chat_data = yaml.safe_load(chats_file.read_text(encoding="utf-8")) or {}
    allowed_chats = [str(item) for item in chat_data.get("allowed_chats", [])]

    return AppConfig(
        telegram_api_id=int(env["TG_API_ID"]),
        telegram_api_hash=str(env["TG_API_HASH"]),
        telegram_phone=str(env["TG_PHONE"]),
        telegram_session_name=str(env["TG_SESSION_NAME"]),
        bot_token=str(env["BOT_TOKEN"]),
        bot_chat_id=str(env["BOT_CHAT_ID"]),
        nvidia_api_key=str(env["NVIDIA_API_KEY"]) if env.get("NVIDIA_API_KEY") else None,
        nvidia_model_name=str(env.get("NVIDIA_MODEL_NAME", "deepseek-ai/deepseek-v4-pro")),
        groq_api_key=str(env["GROQ_API_KEY"]),
        groq_model_name=str(env.get("GROQ_MODEL_NAME", "llama-3.1-8b-instant")),
        timezone_name=str(env.get("TIMEZONE", "Asia/Seoul")),
        summary_max_chars=int(env.get("SUMMARY_MAX_CHARS", "1000")),
        lookback_hours=int(env.get("LOOKBACK_HOURS", "24")),
        allowed_chats=allowed_chats,
        nvidia_requests_per_minute=float(env.get("NVIDIA_RPM_LIMIT", "40")),
        groq_requests_per_minute=float(env.get("GROQ_RPM_LIMIT", "30")),
        groq_tokens_per_minute=int(env.get("GROQ_TPM_LIMIT", "10000")),
    )
