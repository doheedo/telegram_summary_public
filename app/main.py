import argparse
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

from app.bot_sender import send_digest
from app.collector import build_chat_batches
from app.config import load_config
from app.reporter import build_digest, split_digest
from app.state import DeliveryState, load_delivery_state, save_delivery_state
from app.summarizer import FallbackSummarizerClient, GroqSummarizerClient, NvidiaSummarizerClient, summarize_chat_batch
from app.telegram_client import create_telegram_client
from app.timezones import load_runtime_timezone

LOGGER = logging.getLogger(__name__)
STATE_PATH = Path("data/delivery_state.json")


def configure_logging(
    *,
    log_file: Path = Path("logs/tel-suma.log"),
    level: int = logging.INFO,
    max_bytes: int = 10_485_760,
    backup_count: int = 5,
) -> None:
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not any(getattr(handler, "_tel_suma_console", False) for handler in root_logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler._tel_suma_console = True
        root_logger.addHandler(console_handler)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    target = str(log_file.resolve())
    if not any(
        isinstance(handler, RotatingFileHandler)
        and getattr(handler, "baseFilename", None) == target
        for handler in root_logger.handlers
    ):
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def bootstrap_login() -> int:
    config = load_config(env_file=Path(".env"), chats_file=Path("config/chats.yaml"))
    client = create_telegram_client(
        session_name=config.telegram_session_name,
        api_id=config.telegram_api_id,
        api_hash=config.telegram_api_hash,
    )
    with client:
        client.start(phone=config.telegram_phone)
        me = client.get_me()
        LOGGER.info("Telethon session is ready for %s", getattr(me, "username", None) or getattr(me, "id", "unknown"))
    return 0


def build_summarizer_client(config):
    clients = []
    if config.nvidia_api_key:
        clients.append(
            NvidiaSummarizerClient(
                api_key=config.nvidia_api_key,
                model_name=config.nvidia_model_name,
                requests_per_minute=config.nvidia_requests_per_minute,
            )
        )
    clients.append(
        GroqSummarizerClient(
            api_key=config.groq_api_key,
            model_name=config.groq_model_name,
            requests_per_minute=config.groq_requests_per_minute,
            tokens_per_minute=config.groq_tokens_per_minute,
        )
    )
    if len(clients) == 1:
        return clients[0]
    return FallbackSummarizerClient(clients)


def run_daily_summary() -> int:
    config = load_config(env_file=Path(".env"), chats_file=Path("config/chats.yaml"))
    now = datetime.now(load_runtime_timezone(config.timezone_name, fallback_for_missing=True))
    report_time_label = now.strftime("%Y-%m-%d %H:%M")
    summarizer_client = build_summarizer_client(config)
    delivery_state = load_delivery_state(STATE_PATH)

    client = create_telegram_client(
        session_name=config.telegram_session_name,
        api_id=config.telegram_api_id,
        api_hash=config.telegram_api_hash,
    )

    summaries = []
    with client:
        client.start(phone=config.telegram_phone)
        batches = build_chat_batches(
            telegram_client=client,
            allowed_chats=config.allowed_chats,
            now=now,
            lookback_hours=config.lookback_hours,
            last_sent_message_ids=delivery_state.last_sent_message_ids,
        )

        delivered_message_ids: dict[int, int] = {}
        for batch in batches:
            try:
                summaries.append(
                    summarize_chat_batch(
                        batch=batch,
                        summary_max_chars=config.summary_max_chars,
                        summarizer_client=summarizer_client,
                    )
                )
                delivered_message_ids[batch.chat_id] = max(message.message_id for message in batch.messages)
            except Exception as exc:  # noqa: BLE001
                # 실패한 채팅은 last_sent_message_ids를 갱신하지 않아 다음 실행에서 다시 시도한다.
                LOGGER.exception("Failed to summarize chat '%s': %s", batch.chat_title, exc)

    digest = build_digest(report_time_label=report_time_label, summaries=summaries)
    for chunk in split_digest(digest):
        send_digest(config.bot_token, config.bot_chat_id, chunk)

    if summaries:
        delivery_state.last_sent_message_ids.update(delivered_message_ids)
        save_delivery_state(STATE_PATH, delivery_state)
    return 0


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="Telegram unread summary runner")
    parser.add_argument(
        "--bootstrap-login",
        action="store_true",
        help="Create or refresh the Telethon session interactively.",
    )
    args = parser.parse_args(argv)

    if args.bootstrap_login:
        return bootstrap_login()

    return run_daily_summary()


if __name__ == "__main__":
    raise SystemExit(main())
