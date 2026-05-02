import argparse
from pathlib import Path


def render_env_file(
    telegram_api_id: str,
    telegram_api_hash: str,
    telegram_phone: str,
    telegram_session_name: str,
    bot_token: str,
    bot_chat_id: str,
    nvidia_api_key: str,
    nvidia_model_name: str,
    groq_api_key: str,
    timezone_name: str,
    summary_max_chars: int,
    lookback_hours: int,
) -> str:
    lines = [
        f"TG_API_ID={telegram_api_id}",
        f"TG_API_HASH={telegram_api_hash}",
        f"TG_PHONE={telegram_phone}",
        f"TG_SESSION_NAME={telegram_session_name}",
        f"BOT_TOKEN={bot_token}",
        f"BOT_CHAT_ID={bot_chat_id}",
        f"NVIDIA_API_KEY={nvidia_api_key}",
        f"NVIDIA_MODEL_NAME={nvidia_model_name}",
        f"GROQ_API_KEY={groq_api_key}",
        "GROQ_MODEL_NAME=llama-3.1-8b-instant",
        f"TIMEZONE={timezone_name}",
        f"SUMMARY_MAX_CHARS={summary_max_chars}",
        f"LOOKBACK_HOURS={lookback_hours}",
    ]
    return "\n".join(lines) + "\n"


def render_allowed_chats_yaml(allowed_chats: list[str]) -> str:
    lines = ["allowed_chats:"]
    lines.extend(f'  - "{chat}"' for chat in allowed_chats)
    return "\n".join(lines) + "\n"


def write_setup_files(
    env_path: Path,
    chats_path: Path,
    telegram_api_id: str,
    telegram_api_hash: str,
    telegram_phone: str,
    telegram_session_name: str,
    bot_token: str,
    bot_chat_id: str,
    nvidia_api_key: str,
    nvidia_model_name: str,
    groq_api_key: str,
    timezone_name: str,
    summary_max_chars: int,
    lookback_hours: int,
    allowed_chats: list[str],
) -> None:
    env_path.write_text(
        render_env_file(
            telegram_api_id=telegram_api_id,
            telegram_api_hash=telegram_api_hash,
            telegram_phone=telegram_phone,
            telegram_session_name=telegram_session_name,
            bot_token=bot_token,
            bot_chat_id=bot_chat_id,
            nvidia_api_key=nvidia_api_key,
            nvidia_model_name=nvidia_model_name,
            groq_api_key=groq_api_key,
            timezone_name=timezone_name,
            summary_max_chars=summary_max_chars,
            lookback_hours=lookback_hours,
        ),
        encoding="utf-8",
    )
    chats_path.parent.mkdir(parents=True, exist_ok=True)
    chats_path.write_text(render_allowed_chats_yaml(allowed_chats), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write .env and chats.yaml for tel_suma")
    parser.add_argument("--env-path", default=".env")
    parser.add_argument("--chats-path", default="config/chats.yaml")
    parser.add_argument("--telegram-api-id", required=True)
    parser.add_argument("--telegram-api-hash", required=True)
    parser.add_argument("--telegram-phone", required=True)
    parser.add_argument("--telegram-session-name", default="tg_session")
    parser.add_argument("--bot-token", required=True)
    parser.add_argument("--bot-chat-id", required=True)
    parser.add_argument("--nvidia-api-key", default="")
    parser.add_argument("--nvidia-model-name", default="deepseek-ai/deepseek-v4-pro")
    parser.add_argument("--groq-api-key", required=True)
    parser.add_argument("--timezone-name", default="Asia/Seoul")
    parser.add_argument("--summary-max-chars", type=int, default=1000)
    parser.add_argument("--lookback-hours", type=int, default=24)
    parser.add_argument("--allowed-chat", action="append", default=[])
    args = parser.parse_args(argv)

    write_setup_files(
        env_path=Path(args.env_path),
        chats_path=Path(args.chats_path),
        telegram_api_id=args.telegram_api_id,
        telegram_api_hash=args.telegram_api_hash,
        telegram_phone=args.telegram_phone,
        telegram_session_name=args.telegram_session_name,
        bot_token=args.bot_token,
        bot_chat_id=args.bot_chat_id,
        nvidia_api_key=args.nvidia_api_key,
        nvidia_model_name=args.nvidia_model_name,
        groq_api_key=args.groq_api_key,
        timezone_name=args.timezone_name,
        summary_max_chars=args.summary_max_chars,
        lookback_hours=args.lookback_hours,
        allowed_chats=args.allowed_chat,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
